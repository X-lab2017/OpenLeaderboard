import pandas as pd
from clickhouse_driver import Client
from datetime import datetime, timedelta
import requests
import time
import os

xlabDB_host = os.getenv('DB_HOST')
xlabDB_user = os.getenv('DB_USER')
xlabDB_password = os.getenv('DB_PASSWORD')

dashboard_host = os.getenv('DASHBOARDS_DB_HOST')
dashboard_user = os.getenv('DASHBOARDS_DB_USER')
# 访问 clickhouse 数据库
source_client = Client(
    host=xlabDB_host,
    port=9000,  # ClickHouse 默认端口为 9000
    user= xlabDB_user,
    password= xlabDB_password,
    database='opensource'  # 数据库名称
)

target_client = Client(
    host=dashboard_host,
    port=9000,
    user=dashboard_user,
    database='opensource',
)

# 获取上个月的月份
def get_last_month():
    # 获取当前日期
    today = datetime.today()
    # 计算上个月
    first_day_of_current_month = today.replace(day=1)
    last_month = first_day_of_current_month - timedelta(days=1)
    return last_month.strftime("%Y%m")



def query_clickhouse(user_list,query_template, columns,client = source_client, batch_size=150):

    result = []
    
    # 分批处理用户列表
    for i in range(0, len(user_list), batch_size):
        batch = user_list[i:i + batch_size]
        user_batch_list = "', '".join(batch)
        
        # 创建查询语句
        query = query_template.format(user_batch_list=user_batch_list)
        
        # 执行查询并获取结果
        result_batch = client.execute(query)
        
        result.extend(result_batch)
        
        print(f'已查询 {i + batch_size}/{len(user_list)} 位用户数据')
    
    return pd.DataFrame(result, columns=columns)

def save_to_clickhouse(table_name, data,client=target_client):

    columns = data.columns.tolist()

    # 确保日期字段为字符串
    if 'created_at' in columns:
        data['created_at'] = data['created_at'].astype(str)

    # 清空表中的数据
    client.execute(f"TRUNCATE TABLE {table_name}")
    print(f"表 {table_name} 的数据已被清空")
    
    # 显式将 NaN 转换为 None（NULL）
    data = data.applymap(lambda x: None if pd.isna(x) else x)

    # 转换为记录字典列表并插入
    records = data.to_dict('records')

    try:
        # 执行插入操作
        client.execute(f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES", records)
        print(f"数据已成功保存到表 {table_name}")
    except Exception as e:
        print(f"插入失败: {e}")
        print(f"错误的 SQL 查询: INSERT INTO {table_name} ({', '.join(columns)}) VALUES")


# 从 从openleaderboard api 获取数据
# 定义函数，用于从 openleaderboard oss api 获取数据
def fetch_openleaderboard_data(region, metric, month = None):
    # 如果没有传入月份，使用上个月的月份
    if month is None:
        month = get_last_month()
    
    # 构建 URL，metric 是替换的指标
    url = f"https://oss.x-lab.info/open_leaderboard/{metric}/actor/{region}/{month}.json"
    print("请求的URL：", url)
    response = requests.get(url)

    # 检查请求是否成功
    if response.status_code == 200:
        data = response.json().get("data", [])[:300]  # 获取前300项
        # 提取actor_login,  value
        return [
            {
                "actor_login": item["item"]["name"],
                "value": item["value"] # 提取value字段
            } for item in data
        ]
    else:
        print("请求失败，状态码：", response.status_code, response.text)
        return []

def get_openleaderboard_user_list():

    # 定义指标变量
    metrics = ["activity", "open_rank"]

    # 定义地区变量
    regions = ["chinese", "global"]

    # 存储所有结果的 DataFrame
    combined_df = pd.DataFrame()

    # 获取每个指标的每个地区的数据
    for metric in metrics:
        for region in regions:
            # 获取数据
            data = fetch_openleaderboard_data(region, metric)
            
            if data:  # 确保数据不为空
                # 将数据转换为DataFrame
                df = pd.DataFrame(data)
                
                # 动态命名value列
                value_column_name = f"{metric}_{region}_value"
                df[value_column_name] = df["value"].astype(str)
                df = df.drop(columns=["value"])

                # 按actor_login列合并
                if combined_df.empty:
                    combined_df = df
                else:
                    # 使用'actor_login'列进行合并
                    combined_df = pd.merge(combined_df, df[['actor_login', value_column_name]], on='actor_login', how='outer')


    combined_df = combined_df.fillna('') 

    return combined_df

# 从 opendigger 获取数据
# 获取用户的 opendigger 指标数据


def get_opendigger_data(actor_login, metric, retries=3, delay=5):
    # 根据 metric 参数决定请求的 URL
    url = f'https://oss.x-lab.info/open_digger/github/{actor_login}/{metric}.json'
    
    # 重试机制，只对请求异常进行重试
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=30)

            # 如果请求成功，但状态码非 200
            if response.status_code != 200:
                # print(f"Error: Received status code {response.status_code} for {url}, not retrying.")
                return []  # 如果状态码不为 200，直接返回空数据

            # 如果请求成功且状态码为 200
            data = response.json()  # 尝试解析 JSON
            result = []
            for key, value in data.items():
                if len(key) == 7:  # 确保键是日期格式（例如：2020-01）
                    result.append({'actor_login': actor_login, 'month': key, metric: value})
            return result

        except requests.exceptions.RequestException as e:
            # 捕获网络请求相关的异常，如连接错误、超时等
            print(f"RequestException: {e}, retrying... ({attempt + 1}/{retries})")
            time.sleep(delay)  # 等待一段时间后重试

        except ValueError as e:
            # 捕获 JSON 解码错误
            print(f"JSON Decode Error: {e} for {url}")
            return []

    # 如果重试都失败了，返回空数据
    print(f"Failed to fetch data after {retries} attempts for {url}")
    return []




# 获取所有用户的 opendigger 指标数据
def get_all_user_opendigger_data(user_list):
    opendigger_failed_user = []
    activity_data = []
    openrank_data = []

    for actor_login in user_list:
        # 获取用户的活动数据
        activities = get_opendigger_data(actor_login, 'activity')
        activity_data.extend(activities)

        # 获取用户的 OpenRank 数据
        openranks = get_opendigger_data(actor_login, 'openrank')
        openrank_data.extend(openranks)

        if activities == [] and openranks == []:
            opendigger_failed_user.append(actor_login)
    
    # 转换为 DataFrame
    activity_df = pd.DataFrame(activity_data).astype(str)
    openrank_df = pd.DataFrame(openrank_data).astype(str)

    opendigger_failed_user = pd.DataFrame(opendigger_failed_user, columns=['actor_login'])

    opendigger_failed_user.to_csv('dashboard/developer/data/failed_user_opendigger.csv', index=False)

    # 按照 actor_login 和 month 进行外连接
    combined_df = pd.merge(activity_df, openrank_df, on=['actor_login', 'month'], how='outer')
    combined_df = combined_df.fillna('') 
    
    return combined_df







