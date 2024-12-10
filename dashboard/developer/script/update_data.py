import get_data
import get_data_github_api
import pandas as pd

#获取并保存数据
def fetch_and_save_data(query, user_logins, data_name, csv_path, columns):
    data = get_data.query_clickhouse(user_logins, query, columns)
    data.to_csv(csv_path, index=False, encoding='utf-8')
    get_data.save_to_clickhouse(data_name, data)

# 一、从 openleaderboard api 获取上个月 top 300 的user_list
user_list = get_data.get_openleaderboard_user_list()
user_list.to_csv('dashboard/developer/data/user_list.csv', index=False, encoding='utf-8')
get_data.save_to_clickhouse('user_list', user_list)
user_logins = user_list['actor_login']

# 二、从 opendigger api 获取活跃度和 openrank
user_openrank_activity_by_month = get_data.get_all_user_opendigger_data(user_logins)
user_openrank_activity_by_month.to_csv('dashboard/developer/data/user_openrank_activity_by_month.csv', index=False, encoding='utf-8')
get_data.save_to_clickhouse('user_openrank_activity_by_month', user_openrank_activity_by_month)

# 三、从 github graphql api 获取数据
get_data_github_api.get_data_from_graph_ql(user_logins)
user_api_info = pd.read_csv("dashboard/developer/data/user_api_info.csv")  
get_data.save_to_clickhouse('user_api_info', user_api_info)

# 四、从 clickhouse 获取数据

# 1. 开发者近期事件列表 user_latest_events_list
query_events_list = """
SELECT actor_login, repo_name, CAST(`type` AS String) AS type, action, created_at
FROM (
         SELECT actor_login,
                repo_name,
                `type`,
                action,
                created_at,
                ROW_NUMBER() OVER (PARTITION BY actor_id ORDER BY created_at DESC) AS row_num
         FROM events
         WHERE platform = 1
           AND created_at > now() - INTERVAL 6 MONTH 
           AND actor_login IN ('{user_batch_list}')
         ) AS ActorRecentEvents
WHERE row_num <= 30
ORDER BY actor_login, row_num;
"""
fetch_and_save_data(query_events_list, user_logins, 'user_latest_events_list', 
                     'dashboard/developer/data/user_latest_events_list.csv', 
                     ['actor_login', 'repo_name', 'type', 'action', 'created_at'])

# 2. 开发者近期活跃仓库列表 user_top10_repo_list
query_repo_list = """
SELECT actor_login, repo_name, event_count
FROM (
         SELECT actor_login,
                repo_name,
                COUNT(*)                                                            AS event_count,
                ROW_NUMBER() OVER (PARTITION BY actor_login ORDER BY COUNT(*) DESC) AS row_num
         FROM events
         WHERE created_at > NOW() - INTERVAL 6 MONTH
           AND platform = 1
           AND actor_login IN ('{user_batch_list}')
         GROUP BY actor_login, repo_name
         ) AS ranked
WHERE row_num <= 10
ORDER BY actor_login, row_num;
"""
fetch_and_save_data(query_repo_list, user_logins, 'user_top10_repo_list', 
                     'dashboard/developer/data/user_top10_repo_list.csv', 
                     ['actor_login', 'repo_name', 'event_count'])

# 3. 开发者 issue 情况 user_issue_info_by_month
query_issue = '''
SELECT actor_login,
       date_trunc('month', created_at) AS month,
       COUNT(CASE
                 WHEN action IN ('opened', 'reopened') THEN 1
                 ELSE NULL
           END)                        AS opened_count,
       COUNT(CASE
                 WHEN action = 'closed' THEN 1
                 ELSE NULL
           END)                        AS closed_count,
       COUNT(CASE
                 WHEN action IN ('opened', 'reopened') THEN 1
                 ELSE NULL
           END) - COUNT(CASE
                            WHEN action = 'closed' THEN 1
                            ELSE NULL
           END)                        AS waited_count
FROM opensource.events
WHERE type = 7
  AND platform = 1
  AND actor_login IN ('{user_batch_list}')
GROUP BY actor_login, month
ORDER BY actor_login, month;
'''
fetch_and_save_data(query_issue, user_logins, 'user_issue_info_by_month', 
                     'dashboard/developer/data/user_issue_info_by_month.csv', 
                     ['actor_login', 'month', 'opened_count', 'closed_count', 'waited_count'])

# 4. 开发者 pr 情况 user_pr_info_by_month
query_pr = '''
SELECT actor_login,
       date_trunc('month', created_at) AS month,
       COUNT(CASE
                 WHEN action IN ('opened', 'reopened') THEN 1
                 ELSE NULL
           END)                        AS opened_count,
       COUNT(CASE
                 WHEN pull_merged_at IS NOT NULL THEN 1
                 ELSE NULL
           END)                        AS merged_count,
       COUNT(CASE
                 WHEN pull_merged_at IS NULL AND action = 'closed' THEN 1
                 ELSE NULL
           END)                        AS closed_count
FROM opensource.events
WHERE type = 10
  and platform = 1
  AND actor_login IN ('{user_batch_list}')
GROUP BY actor_login, month
ORDER BY actor_login, month;
'''
fetch_and_save_data(query_pr, user_logins, 'user_pr_info_by_month', 
                     'dashboard/developer/data/user_pr_info_by_month.csv', 
                     ['actor_login', 'month', 'opened_count', 'merged_count', 'closed_count'])

# 5. 开发者 fork 仓库数 user_fork_count
query_fork = '''
SELECT actor_login, count(*) as fork_count
FROM events
WHERE type = 4
  and platform = 1
  AND actor_login IN ('{user_batch_list}')
GROUP BY actor_login
'''
fetch_and_save_data(query_fork, user_logins, 'user_fork_count', 
                     'dashboard/developer/data/user_fork_count.csv', 
                     ['actor_login', 'fork_count'])

# 6. 开发者 merge pr 数 user_pr_merge_count
query_merge_pr = '''
SELECT actor_login, count(*) as pr_merged_count
FROM opensource.events
WHERE type = 10
  and pull_merged_at IS NOT NULL
  and platform = 1
  AND actor_login IN ('{user_batch_list}')
GROUP BY actor_login
'''
fetch_and_save_data(query_merge_pr, user_logins, 'user_pr_merge_count', 
                     'dashboard/developer/data/user_pr_merge_count.csv', 
                     ['actor_login', 'pr_merged_count'])
