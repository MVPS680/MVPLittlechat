import requests

# 应用版本信息
CURRENT_VERSION = "1.0.0"
# Gitee仓库信息
GITEE_OWNER = "MVPS680"
GITEE_REPO = "MVPLittlechat"
GITEE_TOKEN = "d5e8dbf0042d38a266870e0150b63989"

# 测试Gitee API调用
def test_api():
    try:
        url = f"https://gitee.com/api/v5/repos/{GITEE_OWNER}/{GITEE_REPO}/releases/latest"
        headers = {
            "Authorization": f"token {GITEE_TOKEN}",
            "Content-Type": "application/json"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        print("API调用成功！")
        data = response.json()
        print(f"标签名: {data.get('tag_name', 'N/A')}")
        print(f"Zipball URL: {data.get('zipball_url', 'N/A')}")
        
        # 测试修复后的URL处理逻辑
        download_url = ""
        assets = data.get("assets", [])
        if assets:
            download_url = assets[0].get("browser_download_url", "")
        
        if not download_url:
            download_url = data.get("zipball_url", "")
            
        if download_url and not (download_url.startswith("http://") or download_url.startswith("https://")):
            download_url = f"https://gitee.com{download_url}"
        
        print(f"处理后的下载链接: {download_url}")
        
    except Exception as e:
        print(f"错误: {str(e)}")

if __name__ == "__main__":
    test_api()