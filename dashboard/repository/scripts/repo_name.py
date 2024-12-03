import os
import requests
import pandas as pd
from datetime import datetime
from clickhouse_driver import Client

# 获取最新的年月，如果最新月没有数据，则回退到上一个月
def get_latest_month():
    today = datetime.today()
    year = today.year
    month = today.month
    return year, month

# 获取数据
def fetch_data(year, month, index, region):
    url = f'https://xlab-open-source.oss-cn-beijing.aliyuncs.com/open_leaderboard/{index}/repo/{region}/{year}{month}.json'
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data['data']
    except requests.exceptions.RequestException as e:
        print(f"获取数据时出错: {e}")
        return []

# 查询 ClickHouse 数据
def query_clickhouse(client, project_names, batch_size=100):
    all_results = []

    for i in range(0, len(project_names), batch_size):
        batch_names = project_names[i:i + batch_size]
        query = """
            SELECT lower(CAST(platform AS String)), repo_name
            FROM export_repo
            WHERE repo_name IN %(batch_names)s
        """
        try:
            batch_result = client.execute(query, {'batch_names': batch_names})
            all_results.extend(batch_result)
        except Exception as e:
            print(f"查询失败: {e}")
            continue

    df_result = pd.DataFrame(all_results, columns=['platform', 'repo_name'])
    df_result = (
        df_result.sort_values(by='platform', ascending=False)
        .drop_duplicates(subset=['repo_name'], keep='first')
    )
    return df_result

# 保存到 ClickHouse
def save_to_clickhouse(client, table_name, df):
    client.execute(f"TRUNCATE TABLE {table_name}")
    client.execute(
        f"INSERT INTO {table_name} (platform, repo_name) VALUES",
        df.to_dict('records')
    )
    print(f"数据已成功保存到表 {table_name}")

# 主程序
if __name__ == "__main__":
    # Step 1: 获取数据
    year, month = get_latest_month()
    data = None
    while data is None or len(data) == 0:
        month_str = str(month).zfill(2)
        indices = ['activity', 'open_rank']
        regions = ['chinese', 'global']
        all_data = []

        for index in indices:
            for region in regions:
                temp_data = fetch_data(year, month_str, index, region)
                if temp_data:
                    all_data.extend(temp_data[:300])

        if all_data:
            data = all_data
        else:
            if month == 1:
                month = 12
                year -= 1
            else:
                month -= 1

    # Step 2: 提取项目名称并去重
    project_names = list({item['item']['name'] for item in data})

    # Step 3: 连接 ClickHouse 数据库
    # 读取数据的 ClickHouse
    source_client = Client(
        host=os.environ.get('xlabDB_HOST'),
        port=9000,
        user=os.environ.get('xlabDB_USER'),
        password=os.environ.get('xlabDB_PASSWORD'),
        database='opensource',
        send_receive_timeout=600
    )

    # 保存数据的 ClickHouse
    target_client = Client(
        host=os.environ.get('dashboardDB_HOST'),
        port=9000,
        user=os.environ.get('dashboardDB_USER'),
        password=os.environ.get('dashboardDB_PASSWORD'),
        database='opensource',
        send_receive_timeout=600
    )

    # Step 4: 查询并处理 ClickHouse 数据
    df_result = query_clickhouse(source_client, project_names)

    # Step 5: 保存结果到 ClickHouse
    table_name = "platform_project_mapping"
    save_to_clickhouse(target_client, table_name, df_result)
