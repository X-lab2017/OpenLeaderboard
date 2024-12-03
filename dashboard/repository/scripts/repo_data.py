import os
import pandas as pd
import requests
import re
from datetime import datetime, timedelta
from clickhouse_driver import Client

# 下载并聚合数据
def down_data_and_aggregate(url, org_repo_platform_df, metrics_list):
    """下载数据并聚合到一个DataFrame"""
    all_data = pd.DataFrame()  # 初始化空的DataFrame

    for index, row in org_repo_platform_df.iterrows():
        org_repo = row['repo_name']
        platform = row['platform']

        # 遍历每个指标
        for metric in metrics_list:
            cur_url = f"{url}{platform}/{org_repo}/{metric}"
            response = requests.get(cur_url, timeout=30)

            if response.status_code == 200:
                data = response.json()
                filtered_data = {k: v for k, v in data.items() if re.match(r"^\d{4}-\d{2}$", k)}

                metric_name = metric.split('.')[0]  # 使用指标名去除扩展名
                df = pd.DataFrame(list(filtered_data.items()), columns=['t_month', metric_name])
                df['org_repo'] = org_repo
                all_data = pd.concat([all_data, df], axis=0)  # 聚合数据
            else:
                print(f"Error: {cur_url} - HTTP Status Code: {response.status_code}")

    # 聚合数据，按 "org_repo" 和 "t_month" 进行透视
    all_data = all_data.pivot_table(index=['org_repo', 't_month'], 
                                    values=[metric.split('.')[0] for metric in metrics_list],
                                    aggfunc='first').reset_index()

    return all_data

# 获取每个项目最新一个月的数据
def get_latest_data(all_data):
    """获取每个项目最新一个月的数据"""
    all_data['t_month'] = pd.to_datetime(all_data['t_month'], format='%Y-%m')
    latest_data = all_data.sort_values('t_month').groupby('org_repo').tail(1)
    latest_data['t_month'] = latest_data['t_month'].dt.strftime('%Y-%m')
    return latest_data

# 下载近六个月的数据并聚合到一个DataFrame
def down_data_and_aggregate_contributor(url, org_repo_platform_df, metric):
    """下载近六个月的数据并聚合到一个DataFrame"""
    all_data = pd.DataFrame()  # 初始化空的DataFrame以聚合所有数据

    # 计算近六个月的月份
    current_date = datetime.now()
    recent_six_months = [(current_date - timedelta(days=30 * i)).strftime("%Y-%m") for i in range(6)]

    # 遍历每个仓库和平台
    for index, row in org_repo_platform_df.iterrows():
        org_repo = row['repo_name']
        platform = row['platform']
        
        # 构建URL
        cur_url = f"{url}{platform}/{org_repo}/{metric}"
        response = requests.get(cur_url)
        
        if response.status_code == 200:
            data = response.json()
            
            # 只保留日期为"yyyy-mm"格式并且属于近六个月的数据
            filtered_data = {k: v for k, v in data.items() if re.match(r"^\d{4}-\d{2}$", k) and k in recent_six_months}
            
            # 创建DataFrame并整合数据
            rows = []
            for month, contributors in filtered_data.items():
                for contributor, value in contributors:
                    rows.append([org_repo, month, contributor, value])

            df = pd.DataFrame(rows, columns=['org_repo', 't_month', 'contributor', 'value'])
            all_data = pd.concat([all_data, df], axis=0)  # 聚合数据
        else:
            print(f"Error: {cur_url} - HTTP Status Code: {response.status_code}")

    return all_data

# 年度数据下载与聚合
def down_data_and_aggregate_yearly(url, org_repo_platform_df, metrics_dict):
    """下载数据并按项目求和后聚合到一个DataFrame"""
    all_data = pd.DataFrame()  # 初始化空的DataFrame以聚合所有数据

    # 遍历每个仓库、平台和所需的指标
    for index, row in org_repo_platform_df.iterrows():
        org_repo = row['repo_name']
        platform = row['platform']
        
        repo_data = {'org_repo': org_repo, 'stars': 0, 'forks': 0, 'participants': 0, 'merged_PRs': 0}
        
        for metric, metric_name in metrics_dict.items():
            cur_url = f"{url}{platform}/{org_repo}/{metric}"
            response = requests.get(cur_url)
            
            if response.status_code == 200:
                data = response.json()
                # 只保留年份格式为 "yyyy" 的数据
                filtered_data = {k: v for k, v in data.items() if re.match(r"^\d{4}$", k)}
                
                # 计算当前指标的总和，并存储在repo_data字典中
                repo_data[metric_name] = sum(filtered_data.values())
            else:
                print(f"Error: {cur_url} - HTTP Status Code: {response.status_code}")

        # 将当前项目的数据添加到总体数据中
        all_data = pd.concat([all_data, pd.DataFrame([repo_data])], ignore_index=True)

    return all_data

# 保存数据到ClickHouse
def save_to_clickhouse(client, table_name, df, columns):
    """将数据保存到ClickHouse"""
    # 确保日期字段为字符串
    if 't_month' in df.columns:
        df['t_month'] = df['t_month'].astype(str)
    
    # 清空目标表
    client.execute(f"TRUNCATE TABLE {table_name}")
    
    # 显式将 NaN 转换为 None（NULL）
    df = df.applymap(lambda x: None if pd.isna(x) else x)

    # 转换为记录字典列表并插入
    records = df.to_dict('records')
    client.execute(f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES", records)
    print(f"数据已成功保存到表 {table_name}")

# 从ClickHouse查询数据
def query_clickhouse(client, table_name):
    """从ClickHouse查询数据"""
    query = f"SELECT * FROM {table_name}"
    result = client.execute(query)
    return pd.DataFrame(result, columns=['org_repo', 't_month', 'contributor', 'value'])

# 从ClickHouse加载repo_name和platform列
def load_org_repo_platform_from_clickhouse(client, table_name):
    """从ClickHouse查询repo_name和platform列"""
    query = f"SELECT repo_name, platform FROM {table_name}"
    result = client.execute(query)
    return pd.DataFrame(result, columns=['repo_name', 'platform'])


if __name__ == '__main__':
    url = "https://oss.x-lab.info/open_digger/"  # 基础API URL
    platform_project_mapping_table = 'platform_project_mapping'  # 存储repo_name和platform信息的表名

    # 获取从 GitHub 或其他平台的凭证
    dashboard_host = os.getenv('DASHBOARD_DB_HOST')
    dashboard_user = os.getenv('DASHBOARD_DB_USER')
    dashboard_password = os.getenv('DASHBOARD_DB_PASSWORD')

    # 连接到ClickHouse
    target_client = Client(
        host=dashboard_host,  # 目标服务器地址
        port=9000,  # ClickHouse 默认端口
        user=dashboard_user,  # 目标服务器用户名
        password=dashboard_password,  # 目标服务器密码
        database='opensource',  # 目标数据库名称
        send_receive_timeout=600
    )

    # 从ClickHouse表加载repo_name和platform列
    org_repo_platform_df = load_org_repo_platform_from_clickhouse(target_client, platform_project_mapping_table)

    # -------------------- code_change_data Metric Set -------------------- (code change data)
    metrics_list_1 = ["code_change_lines_add.json", "code_change_lines_remove.json", "code_change_lines_sum.json"]
    all_data_1 = down_data_and_aggregate(url, org_repo_platform_df, metrics_list_1)
    aggregated_table_1 = "REPO_code_change_data"
    save_to_clickhouse(target_client, aggregated_table_1, all_data_1, ['org_repo', 't_month', 'code_change_lines_add', 'code_change_lines_remove', 'code_change_lines_sum'])

    # -------------------- issues_data Metric Set -------------------- (issue data)
    metrics_list_2 = ["issues_new.json", "issues_closed.json", "issue_comments.json"]
    all_data_2 = down_data_and_aggregate(url, org_repo_platform_df, metrics_list_2)
    aggregated_table_2 = "REPO_issues_data"
    save_to_clickhouse(target_client, aggregated_table_2, all_data_2, ['org_repo', 't_month', 'issues_new', 'issues_closed', 'issue_comments'])

    # -------------------- pr_data Metric Set -------------------- (pull request data)
    metrics_list_3 = ["change_requests.json", "change_requests_accepted.json"]
    all_data_3 = down_data_and_aggregate(url, org_repo_platform_df, metrics_list_3)
    aggregated_table_3 = "REPO_pr_data"
    save_to_clickhouse(target_client, aggregated_table_3, all_data_3, ['org_repo', 't_month', 'change_requests', 'change_requests_accepted'])

    # -------------------- aggregated_data Metric Set -------------------- (activity & attention)
    metrics_list_4 = ["activity.json", "openrank.json", "attention.json"]
    all_data_4 = down_data_and_aggregate(url, org_repo_platform_df, metrics_list_4)
    aggregated_table_4 = "REPO_aggregated_data"
    save_to_clickhouse(target_client, aggregated_table_4, all_data_4, ['org_repo', 't_month', 'activity', 'openrank', 'attention'])

    # -------------------- activity_details Metric Set -------------------- (monthly activity details)
    metric_monthly = "activity_details.json"
    all_data_monthly = down_data_and_aggregate_contributor(url, org_repo_platform_df, metric_monthly)
    aggregated_table_monthly = "REPO_activity_details"
    save_to_clickhouse(target_client, aggregated_table_monthly, all_data_monthly, ['org_repo', 't_month', 'contributor', 'value'])

    # -------------------- starfork_participant_data Metric Set -------------------- (yearly star/fork/participant data)
    metrics_dict_yearly = {
        "stars.json": "stars",
        "technical_fork.json": "forks",
        "participants.json": "participants",
        "change_requests_accepted.json": "merged_PRs"
    }
    all_data_yearly = down_data_and_aggregate_yearly(url, org_repo_platform_df, metrics_dict_yearly)
    aggregated_table_yearly = "REPO_starfork_participant_data"
    save_to_clickhouse(target_client, aggregated_table_yearly, all_data_yearly, ['org_repo', 'stars', 'forks', 'participants', 'merged_PRs'])

    # -------------------- latest_month_data Metric Set -------------------- (latest month data)
    latest_data_4 = get_latest_data(all_data_4)
    latest_table_4 = "REPO_latest_month_data"
    save_to_clickhouse(target_client, latest_table_4, latest_data_4, ['org_repo', 't_month', 'activity', 'openrank', 'attention'])
