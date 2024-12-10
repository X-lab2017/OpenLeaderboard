import pandas as pd
import requests
from time import sleep
import os

# 从环境变量中获取数据库信息
TOKEN = os.getenv('GITHUB_TOKEN')

# GitHub API认证令牌和URL
URL = "https://api.github.com/graphql"
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
}

# 结果保存文件路径
OUTPUT_FILE = "dashboard/developer/data/user_api_info.csv"
FAILED_USER_FILE = 'dashboard/developer/data/failed_user_github_api.csv'


def get_existing_usernames():
    """检查并读取已存在的用户数据"""
    if pd.io.common.file_exists(OUTPUT_FILE):
        existing_data = pd.read_csv(OUTPUT_FILE)
        return existing_data['actor_login'].tolist()
    else:
        # 创建一个空文件并写入标题行
        columns = ["actor_login", "actor_id", "followers", "following", "totalRepositories", "totalRepositoriesContributedTo",
                   "totalStarredRepositories", "totalGists", "tatal_repo_stars", "total_forks", "totalCommitContributions",
                   "totalPullRequestContributions", "totalIssueContributions", "totalRepositoryContributions",
                   "totalPullRequestReviewContributions", "totalRepositoriesWithContributedIssues",
                   "totalRepositoriesWithContributedPullRequests", "totalRepositoriesWithContributedCommits",
                   "repositoryDiscussions", "pullRequests", "issues", "organizations"]
        pd.DataFrame(columns=columns).to_csv(OUTPUT_FILE, index=False)
        return []


def get_user_data(username):
    """获取用户数据"""
    query = f"""
    {{
        user(login: "{username}") {{
            login
            databaseId
            followers {{ totalCount }}
            following {{ totalCount }}
            repositories(first: 100) {{
                totalCount
                nodes {{
                    name
                    stargazerCount
                    forkCount
                }}
            }}
            repositoriesContributedTo(first: 100) {{
                totalCount
                nodes {{
                    name
                    owner {{ login }}
                }}
            }}
            starredRepositories(first: 100) {{ totalCount }}
            gists {{ totalCount }}
            contributionsCollection {{
                totalCommitContributions
                totalPullRequestContributions
                totalIssueContributions
                totalRepositoryContributions
                totalPullRequestReviewContributions
                totalRepositoriesWithContributedIssues
                totalRepositoriesWithContributedPullRequests
                totalRepositoriesWithContributedCommits
            }}
            repositoryDiscussions(first: 100) {{ totalCount }}
            pullRequests(first: 100) {{ totalCount }}
            issues(first: 100) {{ totalCount }}
            organizations(first: 100) {{ totalCount }}
        }}
    }}
    """
    try:
        response = requests.post(URL, json={"query": query}, headers=HEADERS, timeout=30)
        response.raise_for_status()  # 会抛出异常，如果响应码不是200
        return response.json().get("data", {}).get("user", None)
    except requests.exceptions.RequestException as e:
        print(f"请求 {username} 的数据失败: {e}")
        return None


def save_user_info(user_info):
    """保存用户数据"""
    if user_info:
        with open(OUTPUT_FILE, mode="a", newline='', encoding='utf-8') as f:
            pd.DataFrame([user_info]).to_csv(f, index=False, header=False)


def get_data_from_graph_ql(usernames):
    failed_user = []
    existing_usernames = get_existing_usernames()

    for username in usernames:
        if username in existing_usernames:
            # print(f"{username} 已存在，跳过处理")
            continue

        data = get_user_data(username)
        if data:
            repos = data.get("repositories", {}).get("nodes", [])
            user_info = {
                "actor_login": data.get("login", ""),
                "actor_id": data.get("databaseId", ""),
                "followers": data.get("followers", {}).get("totalCount", 0),
                "following": data.get("following", {}).get("totalCount", 0),
                "totalRepositories": data.get("repositories", {}).get("totalCount", 0),
                "totalRepositoriesContributedTo": data.get("repositoriesContributedTo", {}).get("totalCount", 0),
                "totalStarredRepositories": data.get("starredRepositories", {}).get("totalCount", 0),
                "totalGists": data.get("gists", {}).get("totalCount", 0),
                "tatal_repo_stars": sum(repo.get("stargazerCount", 0) for repo in repos),
                "total_forks": sum(repo.get("forkCount", 0) for repo in repos),
                "totalCommitContributions": data.get("contributionsCollection", {}).get("totalCommitContributions", 0),
                "totalPullRequestContributions": data.get("contributionsCollection", {}).get("totalPullRequestContributions", 0),
                "totalIssueContributions": data.get("contributionsCollection", {}).get("totalIssueContributions", 0),
                "totalRepositoryContributions": data.get("contributionsCollection", {}).get("totalRepositoryContributions", 0),
                "totalPullRequestReviewContributions": data.get("contributionsCollection", {}).get("totalPullRequestReviewContributions", 0),
                "totalRepositoriesWithContributedIssues": data.get("contributionsCollection", {}).get("totalRepositoriesWithContributedIssues", 0),
                "totalRepositoriesWithContributedPullRequests": data.get("contributionsCollection", {}).get("totalRepositoriesWithContributedPullRequests", 0),
                "totalRepositoriesWithContributedCommits": data.get("contributionsCollection", {}).get("totalRepositoriesWithContributedCommits", 0),
                "repositoryDiscussions": data.get("repositoryDiscussions", {}).get("totalCount", 0),
                "pullRequests": data.get("pullRequests", {}).get("totalCount", 0),
                "issues": data.get("issues", {}).get("totalCount", 0),
                "organizations": data.get("organizations", {}).get("totalCount", 0),
            }

            save_user_info(user_info)
            # logging.info(f"获取 {username} 的数据成功")
        else:
            failed_user.append(username)
            print(f"获取 {username} 的数据失败")

    if failed_user:
        failed_df = pd.DataFrame(failed_user, columns=['actor_login'])
        failed_df.to_csv(FAILED_USER_FILE, index=False)

    print("用户数据已保存到 user_api_info.csv 文件")

