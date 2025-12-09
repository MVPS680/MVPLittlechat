import socket
import threading
import time
import os
import requests

# 版本信息
CURRENT_VERSION = "3.0.0"

# Gitee配置
GITEE_OWNER = "MVPS680"
GITEE_REPO = "MVPLittlechat"
GITEE_TOKEN = "f19052b74c6322d54137ff8caa114093"

def compare_versions(current_ver, latest_ver):
    """比较版本号，返回版本差异信息
    返回值：
    - -1: 当前版本高于最新版本
    - 0: 当前版本等于最新版本
    - 1: 当前版本低于最新版本一个版本
    - 2: 当前版本低于最新版本两个或更多版本，或主版本号落后
    """
    try:
        # 解析版本号为列表
        current = list(map(int, current_ver.split(".")))
        latest = list(map(int, latest_ver.split(".")))
        
        # 确保版本号列表长度相同，不足的补0
        max_len = max(len(current), len(latest))
        current = current + [0] * (max_len - len(current))
        latest = latest + [0] * (max_len - len(latest))
        
        # 比较每个部分
        for i in range(max_len):
            if current[i] < latest[i]:
                # 当前版本低于最新版本，计算差异
                if i == 0:  # 主版本号差异
                    # 只要主版本号落后任意个版本，就强制更新
                    return 2  # 主版本号差异，强制更新
                elif i == 1:  # 次版本号差异
                    if latest[i] - current[i] >= 2:
                        return 2  # 次版本号差异2个或以上，强制更新
                    elif latest[i] - current[i] >= 1:
                        return 1  # 次版本号差异1个，可选更新
                else:  # 修订号差异
                    return 1  # 修订号差异，可选更新
            elif current[i] > latest[i]:
                return -1  # 当前版本高于最新版本
        
        return 0  # 版本相同
    except Exception:
        # 版本号格式错误，默认不需要更新
        return 0

def download_latest_release(download_url, latest_version, file_name=None):
    """下载最新版本"""
    try:
        # 设置请求头，包含Token认证
        headers = {
            "Authorization": f"token {GITEE_TOKEN}"
        }
        
        # 获取文件大小
        response = requests.get(download_url, headers=headers, stream=True, timeout=10)
        response.raise_for_status()
        
        total_size = int(response.headers.get("content-length", 0))
        
        # 如果没有提供文件名，生成默认文件名
        if not file_name:
            file_name = f"{GITEE_REPO}_server_v{latest_version}.zip"
        
        # 开始下载
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 开始下载更新: {file_name}")
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 文件大小: {total_size / 1024:.2f} KB")
        
        downloaded_size = 0
        with open(file_name, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded_size += len(chunk)
                    
                    # 显示下载进度
                    if total_size > 0:
                        progress = (downloaded_size / total_size) * 100
                        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 下载进度: {progress:.1f}% ({downloaded_size / 1024:.2f} KB / {total_size / 1024:.2f} KB)", end="\r")
        
        print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] ✅ 下载完成: {file_name}")
        
    except requests.exceptions.RequestException as e:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ❌ 下载失败: 网络请求错误 - {str(e)}")
    except Exception as e:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ❌ 下载失败: {str(e)}")

def check_for_updates():
    """检查Gitee仓库是否有新的发行版"""
    try:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 🔍 正在检查更新...")
        
        # 构建API请求URL
        url = f"https://gitee.com/api/v5/repos/{GITEE_OWNER}/{GITEE_REPO}/releases/latest"
        
        # 设置请求头，包含Token认证
        headers = {
            "Authorization": f"token {GITEE_TOKEN}",
            "Content-Type": "application/json"
        }
        
        # 发送请求
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # 解析响应
        latest_release = response.json()
        latest_version = latest_release.get("tag_name", "").lstrip("v")
        
        # 获取assets
        assets = latest_release.get("assets", [])
        release_notes = latest_release.get("body", "")
        
        # 比较版本
        version_diff = compare_versions(CURRENT_VERSION, latest_version)
        if version_diff == 2:
            # 当前版本落后最新版本两个或更多版本，强制更新
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ⚠️  您的版本已落后最新版本两个或更多版本，为了保证正常使用，请立即更新！")
            print(f"当前版本：{CURRENT_VERSION}")
            print(f"最新版本：{latest_version}")
            print(f"\n更新日志：")
            print(release_notes)
            
            # 强制更新询问用户
            choice = input("是否立即下载更新？(y/n): ").strip().lower()
            if choice == 'y':
                # 查找zip文件附件
                zip_assets = [asset for asset in assets if asset.get("name", "").lower().endswith(".zip")]
                
                # 查找带有server字段的py文件
                server_py_assets = []
                for asset in assets:
                    asset_name = asset.get("name", "").lower()
                    if "server" in asset_name and asset_name.endswith(".py"):
                        server_py_assets.append(asset)
                
                if not zip_assets and not server_py_assets:
                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ❌ 未找到可下载的更新文件！")
                    return
                
                # 让用户选择下载类型
                print("\n可下载的更新文件：")
                option_count = 1
                if zip_assets:
                    print(f"{option_count}. 完整更新包 - {zip_assets[0].get('name')}")
                    option_count += 1
                if server_py_assets:
                    print(f"{option_count}. 服务器Python文件 - {server_py_assets[0].get('name')}")
                
                # 设置默认选项为1（完整更新包）
                download_choice = input("请选择下载类型 (1-完整更新包, 2-服务器Python文件, 直接回车默认完整更新包): ").strip()
                
                # 默认选择完整更新包
                if download_choice == "" or download_choice == "1":
                    if zip_assets:
                        download_url = zip_assets[0].get("browser_download_url", "")
                        file_name = zip_assets[0].get("name", f"{GITEE_REPO}_v{latest_version}.zip")
                    else:
                        # 如果没有zip文件，退而求其次选择服务器Python文件
                        if server_py_assets:
                            download_url = server_py_assets[0].get("browser_download_url", "")
                            file_name = server_py_assets[0].get("name", f"{GITEE_REPO}_server_v{latest_version}.py")
                        else:
                            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ❌ 未找到可下载的更新文件！")
                            return
                elif download_choice == "2":
                    if server_py_assets:
                        download_url = server_py_assets[0].get("browser_download_url", "")
                        file_name = server_py_assets[0].get("name", f"{GITEE_REPO}_server_v{latest_version}.py")
                    else:
                        # 如果没有服务器Python文件，退而求其次选择完整更新包
                        if zip_assets:
                            download_url = zip_assets[0].get("browser_download_url", "")
                            file_name = zip_assets[0].get("name", f"{GITEE_REPO}_v{latest_version}.zip")
                        else:
                            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ❌ 未找到可下载的更新文件！")
                            return
                else:
                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ⚠️  无效选择，默认下载完整更新包")
                    if zip_assets:
                        download_url = zip_assets[0].get("browser_download_url", "")
                        file_name = zip_assets[0].get("name", f"{GITEE_REPO}_v{latest_version}.zip")
                    elif server_py_assets:
                        download_url = server_py_assets[0].get("browser_download_url", "")
                        file_name = server_py_assets[0].get("name", f"{GITEE_REPO}_server_v{latest_version}.py")
                    else:
                        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ❌ 未找到可下载的更新文件！")
                        return
                
                # 确保URL格式正确
                if download_url and not (download_url.startswith("http://") or download_url.startswith("https://")):
                    download_url = f"https://gitee.com{download_url}"
                
                if download_url:
                    download_latest_release(download_url, latest_version, file_name)
                else:
                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ❌ 获取下载链接失败！")
        elif version_diff == 1:
            # 当前版本落后最新版本一个版本，可选更新
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 🎉 发现新版本！")
            print(f"当前版本：{CURRENT_VERSION}")
            print(f"最新版本：{latest_version}")
            print(f"\n更新日志：")
            print(release_notes)
            
            # 询问用户是否更新
            choice = input("是否下载更新？(y/n): ").strip().lower()
            if choice == 'y':
                # 查找zip文件附件
                zip_assets = [asset for asset in assets if asset.get("name", "").lower().endswith(".zip")]
                
                # 查找带有server字段的py文件
                server_py_assets = []
                for asset in assets:
                    asset_name = asset.get("name", "").lower()
                    if "server" in asset_name and asset_name.endswith(".py"):
                        server_py_assets.append(asset)
                
                if not zip_assets and not server_py_assets:
                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ❌ 未找到可下载的更新文件！")
                    return
                
                # 让用户选择下载类型
                print("\n可下载的更新文件：")
                option_count = 1
                if zip_assets:
                    print(f"{option_count}. 完整更新包 - {zip_assets[0].get('name')}")
                    option_count += 1
                if server_py_assets:
                    print(f"{option_count}. 服务器Python文件 - {server_py_assets[0].get('name')}")
                
                # 设置默认选项为1（完整更新包）
                download_choice = input("请选择下载类型 (1-完整更新包, 2-服务器Python文件, 直接回车默认完整更新包): ").strip()
                
                # 默认选择完整更新包
                if download_choice == "" or download_choice == "1":
                    if zip_assets:
                        download_url = zip_assets[0].get("browser_download_url", "")
                        file_name = zip_assets[0].get("name", f"{GITEE_REPO}_v{latest_version}.zip")
                    else:
                        # 如果没有zip文件，退而求其次选择服务器Python文件
                        if server_py_assets:
                            download_url = server_py_assets[0].get("browser_download_url", "")
                            file_name = server_py_assets[0].get("name", f"{GITEE_REPO}_server_v{latest_version}.py")
                        else:
                            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ❌ 未找到可下载的更新文件！")
                            return
                elif download_choice == "2":
                    if server_py_assets:
                        download_url = server_py_assets[0].get("browser_download_url", "")
                        file_name = server_py_assets[0].get("name", f"{GITEE_REPO}_server_v{latest_version}.py")
                    else:
                        # 如果没有服务器Python文件，退而求其次选择完整更新包
                        if zip_assets:
                            download_url = zip_assets[0].get("browser_download_url", "")
                            file_name = zip_assets[0].get("name", f"{GITEE_REPO}_v{latest_version}.zip")
                        else:
                            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ❌ 未找到可下载的更新文件！")
                            return
                else:
                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ⚠️  无效选择，默认下载完整更新包")
                    if zip_assets:
                        download_url = zip_assets[0].get("browser_download_url", "")
                        file_name = zip_assets[0].get("name", f"{GITEE_REPO}_v{latest_version}.zip")
                    elif server_py_assets:
                        download_url = server_py_assets[0].get("browser_download_url", "")
                        file_name = server_py_assets[0].get("name", f"{GITEE_REPO}_server_v{latest_version}.py")
                    else:
                        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ❌ 未找到可下载的更新文件！")
                        return
                
                # 确保URL格式正确
                if download_url and not (download_url.startswith("http://") or download_url.startswith("https://")):
                    download_url = f"https://gitee.com{download_url}"
                
                if download_url:
                    download_latest_release(download_url, latest_version, file_name)
                else:
                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ❌ 获取下载链接失败！")
        elif version_diff == 0:
            # 当前版本等于最新版本
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ✅ 当前已是最新版本！")
            print(f"当前版本：{CURRENT_VERSION}")
        else:
            # 当前版本高于最新版本
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ✅ 当前版本已高于最新发布版本！")
            print(f"当前版本：{CURRENT_VERSION}")
            
    except requests.exceptions.RequestException as e:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ❌ 检查更新失败：网络请求错误 - {str(e)}")
    except Exception as e:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ❌ 检查更新失败：{str(e)}")

def load_config():
    """加载配置文件，若不存在则生成默认配置"""
    config_file = "LittleChat.serverset"
    default_config = {
        "server_port": "7891",
        "max_user": "5",
        "max_attempts": "5",
        "wait_time": "1",
        "socket_timeout": "1",
        "admin_prefix": "ADMIN：",
        "log_level": "info",
        "message_size_limit": "1024"
    }
    
    # 检查配置文件是否存在
    if not os.path.exists(config_file):
        # 生成默认配置文件
        with open(config_file, "w", encoding="utf-8") as f:
            f.write("# LittleChat服务器配置文件\n")
            f.write("# 编辑此文件修改服务器设置\n")
            f.write("# 支持完整注释行和行末注释\n\n")
            
            # 为每个配置项添加注释
            for key, value in default_config.items():
                if key == "server_port":
                    f.write("# 服务器绑定的端口号\n")
                    f.write(f"{key}={value} # 默认端口：7891\n\n")
                elif key == "max_user":
                    f.write("# 最大允许连接的用户数\n")
                    f.write(f"{key}={value} # 默认最大用户数：5\n\n")
                elif key == "max_attempts":
                    f.write("# 端口绑定失败后的最大重试次数\n")
                    f.write(f"{key}={value} # 默认重试次数：5\n\n")
                elif key == "wait_time":
                    f.write("# 端口绑定失败后重试的等待时间（秒）\n")
                    f.write(f"{key}={value} # 默认等待时间：1秒\n\n")
                elif key == "socket_timeout":
                    f.write("# 服务器socket的超时时间（秒）\n")
                    f.write(f"{key}={value} # 默认超时时间：1秒\n\n")
                elif key == "admin_prefix":
                    f.write("# 管理员昵称前缀\n")
                    f.write(f"{key}={value} # 默认前缀：ADMIN：\n\n")
                elif key == "log_level":
                    f.write("# 日志级别（info/warn/error）\n")
                    f.write(f"{key}={value} # 默认日志级别：info\n\n")
                elif key == "message_size_limit":
                    f.write("# 单个消息的最大长度（字节）\n")
                    f.write(f"{key}={value} # 默认消息大小：1024字节\n\n")
                else:
                    f.write(f"# {key}配置\n")
                    f.write(f"{key}={value}\n\n")
        return default_config
    
    # 读取配置文件
    config = {}
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                # 跳过空行
                if not line:
                    continue
                # 跳过完整的注释行
                if line.startswith("#"):
                    continue
                # 处理行末注释
                if "#" in line:
                    # 只保留#之前的部分
                    line = line.split("#", 1)[0].strip()
                # 解析键值对
                if "=" in line:
                    key, value = line.split("=", 1)
                    config[key.strip()] = value.strip()
    except Exception as e:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 配置文件读取错误: {e}")
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 使用默认配置")
        return default_config
    
    # 确保所有必要的配置项都存在
    for key, value in default_config.items():
        if key not in config:
            config[key] = value
    
    return config

class ChatServer:
    def __init__(self):
        # 加载配置
        config = load_config()
        self.port = int(config["server_port"])
        self.max_user = int(config["max_user"])
        self.max_attempts = int(config["max_attempts"])
        self.wait_time = int(config["wait_time"])
        self.socket_timeout = int(config["socket_timeout"])
        self.admin_prefix = config["admin_prefix"]
        self.log_level = config["log_level"]
        self.message_size_limit = int(config["message_size_limit"])
        
        self.server_socket = None
        self.client_sockets = []
        self.client_nicknames = {}
        self.client_profiles = {}
        self.admins = set()  # 管理员列表
        self.banned_users = set()  # 封禁的用户名列表（保留兼容，实际使用IP封禁）
        self.banned_ips = set()  # 封禁的IP地址列表
        self.muted_users = {}  # 禁言的用户名和禁言时长，格式: {nickname: (mute_time, duration)}
        self.lock = threading.Lock()  # 线程锁，保护客户端列表
        self.running = False
        self.start_time = None  # 服务器启动时间
    
    def _get_running_time(self):
        """计算服务器运行时间"""
        if not self.start_time:
            return "0秒"
        end_time = time.time()
        running_time = int(end_time - self.start_time)
        
        # 格式化运行时间
        days = running_time // (24 * 3600)
        hours = (running_time % (24 * 3600)) // 3600
        minutes = (running_time % 3600) // 60
        seconds = running_time % 60
        
        if days > 0:
            return f"{days}天{hours}小时{minutes}分钟{seconds}秒"
        elif hours > 0:
            return f"{hours}小时{minutes}分钟{seconds}秒"
        elif minutes > 0:
            return f"{minutes}分钟{seconds}秒"
        else:
            return f"{seconds}秒"
    
    def handle_client(self, client_socket, client_address):
        """处理单个客户端连接"""
        nickname = "未知用户"
        try:
            # 接收客户端昵称
            nickname_data = client_socket.recv(1024).decode('utf-8')
            if nickname_data:
                nickname = nickname_data.strip()
            
            # 检查用户IP是否被封禁
            with self.lock:
                # 先检查IP是否被封禁
                if client_address[0] in self.banned_ips:
                    # IP已被封禁，发送错误消息并关闭连接
                    error_message = "ERROR:您的IP已被封禁，无法连接"
                    client_socket.send(error_message.encode('utf-8'))
                    client_socket.close()
                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 被封禁IP {client_address[0]} 尝试连接，使用昵称: {nickname}")
                    return
                # 保留用户名封禁检查，兼容旧逻辑
                if nickname in self.banned_users:
                    # 用户已被封禁，发送错误消息并关闭连接
                    error_message = "ERROR:您已被封禁，无法连接"
                    client_socket.send(error_message.encode('utf-8'))
                    client_socket.close()
                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 被封禁用户 {nickname} 尝试连接")
                    return
                
                # 检查昵称是否已被使用
                if nickname in self.client_nicknames.values():
                    # 昵称已存在，发送错误消息并关闭连接
                    error_message = "ERROR:昵称已被使用，请选择其他昵称"
                    client_socket.send(error_message.encode('utf-8'))
                    client_socket.close()
                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 客户端 {client_address} 尝试使用已存在的昵称: {nickname}")
                    return
                
                # 昵称可用，线程安全地添加客户端
                self.client_sockets.append(client_socket)
                self.client_nicknames[client_socket] = nickname
                # 存储用户profile信息
                self.client_profiles[client_socket] = {
                    'nickname': nickname,
                    'ip_address': client_address[0],
                    'join_time': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'os_version': '未知'  # 暂时无法获取客户端操作系统
                }
            
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 客户端 {client_address} 已连接，昵称为: {nickname}")
            
            # 发送成功消息给客户端
            success_message = "SUCCESS:连接成功"
            client_socket.send(success_message.encode('utf-8'))
            
            # 广播新用户加入消息
            self.broadcast_message(f"系统: {nickname} 加入了聊天室", exclude_socket=client_socket)
            # 广播更新后的在线用户列表
            self.broadcast_user_list()
            
            # 处理客户端消息
            while True:
                message = client_socket.recv(self.message_size_limit).decode('utf-8')
                if not message:
                    break
                
                if message.startswith("PROFILE_REQUEST:"):
                    # 处理用户profile请求
                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 收到PROFILE_REQUEST: {message}")
                    requested_nickname = message.split(":", 1)[1]
                    profile_data = None
                    
                    with self.lock:
                        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] client_profiles: {self.client_profiles}")
                        # 查找请求的用户profile
                        for sock, prof in self.client_profiles.items():
                            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] checking profile: {prof['nickname']} vs {requested_nickname}")
                            if prof['nickname'] == requested_nickname:
                                profile_data = prof
                                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] found profile: {profile_data}")
                                break
                    
                    if profile_data:
                        # 构造profile响应
                        profile_message = f"PROFILE:{profile_data['nickname']}|{profile_data['ip_address']}|{profile_data['join_time']}|{profile_data['os_version']}"
                        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] sending profile: {profile_message}")
                        client_socket.send(profile_message.encode('utf-8'))
                    else:
                        # 用户不存在
                        error_message = "PROFILE_ERROR:用户不存在"
                        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] sending profile error: {error_message}")
                        client_socket.send(error_message.encode('utf-8'))
                elif message.startswith("ADMIN_COMMAND:"):
                    # 处理管理员命令
                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 收到ADMIN_COMMAND: {message}")
                    # 格式: ADMIN_COMMAND:command:target
                    parts = message.split(":", 2)
                    if len(parts) == 3:
                        admin_command = parts[1].lower()
                        target_nickname = parts[2].strip()
                        
                        # 检查发送者是否是管理员
                        with self.lock:
                            is_admin = nickname in self.admins
                        
                        if is_admin:
                            # 执行管理员命令
                            if admin_command == 'kick':
                                # 防止管理员自己踢自己
                                if target_nickname != nickname:
                                    self.kick_user(target_nickname)
                                else:
                                    # 发送错误消息给管理员
                                    error_message = "ERROR:您不能对自己执行此操作"
                                    client_socket.send(error_message.encode('utf-8'))
                                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 管理员 {nickname} 尝试踢自己")
                            elif admin_command == 'op':
                                # 防止管理员自己给自己设为管理员
                                if target_nickname != nickname:
                                    # 查找目标用户的socket
                                    target_socket = None
                                    with self.lock:
                                        for sock, n in self.client_nicknames.items():
                                            if n == target_nickname:
                                                target_socket = sock
                                                break
                                        self.admins.add(target_nickname)
                                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ✅ 管理员 {nickname} 已将 {target_nickname} 设为管理员")
                                    # 通知所有用户
                                    broadcast_msg = f"系统: {target_nickname} 已被管理员设为管理员"
                                    self.broadcast_message(broadcast_msg)
                                    # 向被设为管理员的用户发送特定消息，触发客户端弹窗
                                    if target_socket:
                                        try:
                                            target_socket.send(f"OP:{broadcast_msg}".encode('utf-8'))
                                        except:
                                            pass
                                    # 更新所有客户端的用户列表，显示管理员标识
                                    self.broadcast_user_list()
                                else:
                                    # 发送错误消息给管理员
                                    error_message = "ERROR:您已经是管理员"
                                    client_socket.send(error_message.encode('utf-8'))
                                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 管理员 {nickname} 尝试给自己设为管理员")
                            elif admin_command == 'unop':
                                # 防止管理员自己撤销自己的权限
                                if target_nickname != nickname:
                                    is_admin = False
                                    target_socket = None
                                    with self.lock:
                                        # 查找目标用户的socket
                                        for sock, n in self.client_nicknames.items():
                                            if n == target_nickname:
                                                target_socket = sock
                                                break
                                        if target_nickname in self.admins:
                                            self.admins.remove(target_nickname)
                                            is_admin = True
                                    
                                    if is_admin:
                                        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ✅ 管理员 {nickname} 已撤销 {target_nickname} 的管理员权限")
                                        # 通知所有用户 - 移出锁范围，避免死锁
                                        broadcast_msg = f"系统: {target_nickname} 已被管理员撤销管理员权限"
                                        self.broadcast_message(broadcast_msg)
                                        # 向被撤销管理员权限的用户发送特定消息，触发客户端弹窗
                                        if target_socket:
                                            try:
                                                target_socket.send(f"UNOP:{broadcast_msg}".encode('utf-8'))
                                            except:
                                                pass
                                        # 更新所有客户端的用户列表，恢复原昵称显示
                                        self.broadcast_user_list()
                                    else:
                                        error_message = "ERROR:该用户不是管理员"
                                        client_socket.send(error_message.encode('utf-8'))
                                        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 管理员 {nickname} 尝试撤销非管理员 {target_nickname} 的权限")
                                else:
                                    # 发送错误消息给管理员
                                    error_message = "ERROR:您不能撤销自己的管理员权限"
                                    client_socket.send(error_message.encode('utf-8'))
                                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 管理员 {nickname} 尝试撤销自己的权限")
                            elif admin_command == 'ban':
                                # 防止管理员自己封禁自己
                                if target_nickname != nickname:
                                    # 查找目标用户的IP地址
                                    target_ip = None
                                    with self.lock:
                                        for sock, n in self.client_nicknames.items():
                                            if n == target_nickname:
                                                # 找到目标用户，获取其IP地址
                                                if sock in self.client_profiles:
                                                    target_ip = self.client_profiles[sock]['ip_address']
                                                break
                                    
                                    if target_ip:
                                        # 封禁目标用户的IP
                                        with self.lock:
                                            self.banned_ips.add(target_ip)
                                        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ✅ 管理员 {nickname} 已封禁IP {target_ip}（用户：{target_nickname}）")
                                        # 踢出该用户（如果在线）
                                        self.kick_user(target_nickname)
                                        # 通知所有用户
                                        self.broadcast_message(f"系统: 用户 {target_nickname} 的IP {target_ip} 已被管理员封禁")
                                    else:
                                        # 用户不在线或找不到IP
                                        error_message = f"ERROR:找不到用户 {target_nickname} 或其IP地址"
                                        client_socket.send(error_message.encode('utf-8'))
                                        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 管理员 {nickname} 尝试封禁不存在的用户 {target_nickname}")
                                else:
                                    # 发送错误消息给管理员
                                    error_message = "ERROR:您不能封禁自己"
                                    client_socket.send(error_message.encode('utf-8'))
                                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 管理员 {nickname} 尝试封禁自己")
                            elif admin_command == 'unban':
                                # 支持两种方式解除封禁：直接使用IP地址，或通过用户名查找IP
                                target_ip = None
                                target_user = target_nickname  # 保存原始目标名称
                                
                                # 检查目标是否是IP地址格式
                                import re
                                ip_pattern = r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$'
                                if re.match(ip_pattern, target_nickname):
                                    # 直接使用IP地址
                                    target_ip = target_nickname
                                else:
                                    # 尝试通过用户名查找IP地址
                                    with self.lock:
                                        for sock, n in self.client_nicknames.items():
                                            if n == target_nickname:
                                                # 找到目标用户，获取其IP地址
                                                if sock in self.client_profiles:
                                                    target_ip = self.client_profiles[sock]['ip_address']
                                                break
                                
                                if target_ip:
                                    with self.lock:
                                        if target_ip in self.banned_ips:
                                            self.banned_ips.remove(target_ip)
                                            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ✅ 管理员 {nickname} 已解除IP {target_ip} 的封禁")
                                            # 通知所有用户
                                            if target_user != target_ip:
                                                self.broadcast_message(f"系统: 用户 {target_user} 的IP {target_ip} 已被管理员解除封禁")
                                            else:
                                                self.broadcast_message(f"系统: IP {target_ip} 已被管理员解除封禁")
                                        else:
                                            error_message = f"ERROR:该IP {target_ip} 未被封禁"
                                            client_socket.send(error_message.encode('utf-8'))
                                            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 管理员 {nickname} 尝试解除未封禁IP {target_ip} 的封禁")
                                else:
                                    # 无法找到目标IP
                                    error_message = f"ERROR:找不到目标 {target_nickname} 或其IP地址"
                                    client_socket.send(error_message.encode('utf-8'))
                                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 管理员 {nickname} 尝试解除不存在的目标 {target_nickname} 的封禁")
                            elif admin_command == 'shutup':
                                # 提取禁言时长
                                duration_part = target_nickname.split(' ', 1)
                                if len(duration_part) == 2:
                                    actual_target = duration_part[0]
                                    try:
                                        duration = int(duration_part[1])
                                        if duration > 0:
                                            # 防止管理员自己禁言自己
                                            if actual_target != nickname:
                                                # 查找目标用户的socket
                                                target_socket = None
                                                with self.lock:
                                                    for sock, n in self.client_nicknames.items():
                                                        if n == actual_target:
                                                            target_socket = sock
                                                            break
                                                    self.muted_users[actual_target] = (time.time(), duration)
                                                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ✅ 管理员 {nickname} 已禁言 {actual_target} {duration} 分钟")
                                                # 通知所有用户
                                                broadcast_msg = f"系统: {actual_target} 已被管理员禁言 {duration} 分钟"
                                                self.broadcast_message(broadcast_msg)
                                                # 向被禁言的用户发送特定消息，触发客户端弹窗
                                                if target_socket:
                                                    try:
                                                        target_socket.send(f"MUTED:{broadcast_msg}".encode('utf-8'))
                                                    except:
                                                        pass
                                            else:
                                                error_message = "ERROR:您不能禁言自己"
                                                client_socket.send(error_message.encode('utf-8'))
                                                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 管理员 {nickname} 尝试禁言自己")
                                        else:
                                            error_message = "ERROR:禁言时长必须大于0"
                                            client_socket.send(error_message.encode('utf-8'))
                                            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 管理员 {nickname} 尝试使用无效的禁言时长")
                                    except ValueError:
                                        error_message = "ERROR:命令格式错误: /shutup <用户名> <时间（分钟）>"
                                        client_socket.send(error_message.encode('utf-8'))
                                        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 管理员 {nickname} 尝试使用错误的命令格式")
                                else:
                                    error_message = "ERROR:命令格式错误: /shutup <用户名> <时间（分钟）>"
                                    client_socket.send(error_message.encode('utf-8'))
                                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 管理员 {nickname} 尝试使用错误的命令格式")
                            elif admin_command == 'unshutup':
                                # 防止管理员自己解除自己的禁言
                                if target_nickname != nickname:
                                    # 查找目标用户的socket
                                    target_socket = None
                                    with self.lock:
                                        for sock, n in self.client_nicknames.items():
                                            if n == target_nickname:
                                                target_socket = sock
                                                break
                                        if target_nickname in self.muted_users:
                                            del self.muted_users[target_nickname]
                                            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ✅ 管理员 {nickname} 已解除 {target_nickname} 的禁言")
                                            # 通知所有用户
                                            broadcast_msg = f"系统: {target_nickname} 已被管理员解除禁言"
                                            self.broadcast_message(broadcast_msg)
                                            # 向被解禁的用户发送特定消息，触发客户端弹窗
                                            if target_socket:
                                                try:
                                                    target_socket.send(f"UNMUTED:{broadcast_msg}".encode('utf-8'))
                                                except:
                                                    pass
                                        else:
                                            error_message = "ERROR:该用户未被禁言"
                                            client_socket.send(error_message.encode('utf-8'))
                                            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 管理员 {nickname} 尝试解除未禁言用户 {target_nickname} 的禁言")
                                else:
                                    error_message = "ERROR:您不能解除自己的禁言"
                                    client_socket.send(error_message.encode('utf-8'))
                                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 管理员 {nickname} 尝试解除自己的禁言")
                            else:
                                # 不支持的命令
                                error_message = f"ERROR:不支持的命令: {admin_command}"
                                client_socket.send(error_message.encode('utf-8'))
                                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 管理员 {nickname} 尝试执行不支持的命令: {admin_command}")
                        else:
                            # 发送错误消息给非管理员用户
                            error_message = "ERROR:您没有权限执行此命令"
                            client_socket.send(error_message.encode('utf-8'))
                            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 非管理员用户 {nickname} 尝试执行管理员命令")
                else:
                    # 检查用户是否被禁言
                    is_muted = False
                    mute_duration = 0
                    mute_expired = False
                    with self.lock:
                        if nickname in self.muted_users:
                            mute_time, duration = self.muted_users[nickname]
                            # 检查禁言是否已过期（分钟转换为秒）
                            if time.time() - mute_time < duration * 60:
                                is_muted = True
                                mute_duration = duration
                            else:
                                # 禁言已过期，自动解除禁言
                                del self.muted_users[nickname]
                                mute_expired = True
                    
                    # 移出锁范围，避免死锁
                    if mute_expired:
                        self.broadcast_message(f"系统: {nickname} 禁言已过期")
                    
                    if is_muted:
                        # 用户被禁言，发送错误消息
                        error_message = f"ERROR:您已被禁言 {mute_duration} 分钟，无法发送消息"
                        client_socket.send(error_message.encode('utf-8'))
                        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 被禁言用户 {nickname} 尝试发送消息")
                    else:
                        # 普通消息，广播给其他用户
                        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 收到 {nickname} 的消息: {message}")
                        self.broadcast_message(f"{nickname}: {message}", exclude_socket=client_socket)
                
        except ConnectionResetError:
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 客户端 {client_address} 强制断开连接")
        except UnicodeDecodeError:
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 客户端 {client_address} 发送了无效的UTF-8数据")
        except Exception as e:
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 处理客户端 {client_address} 时发生错误: {str(e)}")
        finally:
            # 线程安全地移除客户端
            with self.lock:
                if client_socket in self.client_sockets:
                    self.client_sockets.remove(client_socket)
                    if client_socket in self.client_nicknames:
                        del self.client_nicknames[client_socket]
                    if client_socket in self.client_profiles:
                        del self.client_profiles[client_socket]
            
            # 关闭客户端连接
            try:
                client_socket.close()
            except:
                pass
            
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 客户端 {client_address} 已断开连接")
            # 广播用户离开消息
            self.broadcast_message(f"系统: {nickname} 离开了聊天室")
            # 广播更新后的在线用户列表
            self.broadcast_user_list()
    
    def broadcast_message(self, message, exclude_socket=None):
        """广播消息给所有客户端，可选排除特定客户端"""
        with self.lock:
            # 创建客户端列表副本，避免在迭代时修改列表
            clients_copy = self.client_sockets.copy()
        
        for client in clients_copy:
            if client == exclude_socket:
                continue
            
            try:
                client.send(message.encode('utf-8'))
            except BrokenPipeError:
                # 处理客户端断开但未从列表中移除的情况
                with self.lock:
                    if client in self.client_sockets:
                        self.client_sockets.remove(client)
                        if client in self.client_nicknames:
                            del self.client_nicknames[client]
                try:
                    client.close()
                except:
                    pass
            except Exception as e:
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 广播消息失败: {str(e)}")
    
    def broadcast_user_list(self):
        """广播在线用户列表给所有客户端"""
        with self.lock:
            # 获取当前在线用户昵称列表，并为管理员添加前缀
            users = []
            for sock, nickname in self.client_nicknames.items():
                if nickname in self.admins:
                    # 管理员昵称前添加配置的前缀
                    users.append(f"{self.admin_prefix}{nickname}")
                else:
                    # 普通用户使用原昵称
                    users.append(nickname)
        
        # 构造用户列表消息，使用特殊格式以便客户端解析
        user_list_message = f"USERS_LIST:{','.join(users)}"
        self.broadcast_message(user_list_message)
    
    def kick_user(self, target_nickname):
        """踢出指定用户"""
        target_socket = None
        
        with self.lock:
            # 查找目标用户的socket
            for sock, nickname in self.client_nicknames.items():
                if nickname == target_nickname:
                    target_socket = sock
                    break
        
        if target_socket:
            try:
                # 发送踢出消息给目标用户
                target_socket.send("KICKED:你已被管理员踢出聊天室".encode('utf-8'))
                # 关闭连接
                target_socket.close()
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ✅ 已踢出用户: {target_nickname}")
                # 广播踢出消息
                self.broadcast_message(f"系统: {target_nickname} 已被管理员踢出聊天室")
            except Exception as e:
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ❌ 踢出用户 {target_nickname} 时发生错误: {str(e)}")
        else:
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ❌ 用户 {target_nickname} 不存在或已离线")
    
    def start(self):
        """启动服务器"""
        print("=" * 60)
        print("" * 20 + "聊天服务器启动中...")
        print("=" * 60)
        
        # 检查更新
        check_for_updates()
        try:
            bind_attempts = 0
            bind_success = False
            
            while bind_attempts < self.max_attempts and not bind_success:
                try:
                    # 创建套接字
                    self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    
                    # 关键：确保在bind之前设置SO_REUSEADDR选项
                    # 对于Windows，这个选项必须在bind之前设置才有效
                    # 特别是打包为exe后，这个设置至关重要
                    self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 已设置 SO_REUSEADDR 选项，允许端口复用")
                    
                    bind_attempts += 1
                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 尝试绑定到端口 {self.port}... (尝试 {bind_attempts}/{self.max_attempts})")
                    
                    # 绑定地址和端口
                    self.server_socket.bind(('0.0.0.0', self.port))
                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 成功绑定到端口 {self.port}")
                    
                    # 开始监听连接
                    self.server_socket.listen(self.max_user)
                    self.running = True
                    self.start_time = time.time()  # 记录服务器启动时间
                    
                    # 服务器启动成功提示
                    print("=" * 60)
                    print("" * 20 + f"聊天服务器启动成功 v{CURRENT_VERSION}  作者：MVP请勿做商业用途或非法活动")
                    print("=" * 60)
                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 服务器状态: 运行中")
                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 监听地址: 0.0.0.0")
                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 监听端口: {self.port}")
                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 服务器IP: {socket.gethostbyname(socket.gethostname())}")
                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 最大连接数: {self.max_user}")
                    print("=" * 60)
                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 等待客户端连接...")
                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 提示: 输入 'quit'、'exit' 或 'stop' 可关闭服务器")
                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 提示: 服务端目录下的LittleChat.serverset文件是服务器配置文件，试试改一改它吧！")
                    print("=" * 60)
                    
                    bind_success = True
                except OSError as e:
                    if hasattr(e, 'winerror') and e.winerror == 10048:
                        # Windows特定错误：地址已被占用
                        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 警告: 端口 {self.port} 被占用 - {e.strerror}")
                        if bind_attempts < self.max_attempts:
                            # 等待一段时间后重试
                            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 等待 {self.wait_time} 秒后重试...")
                            time.sleep(self.wait_time)
                            # 关闭当前套接字，准备下一次尝试
                            try:
                                self.server_socket.close()
                            except:
                                pass
                        else:
                            # 达到最大尝试次数，抛出异常
                            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 错误: 经过 {self.max_attempts} 次尝试后仍无法绑定到端口 {self.port}")
                            raise
                    else:
                        # 其他OSError，直接抛出
                        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 错误: 绑定端口时发生其他错误 - {e.strerror}")
                        raise
                
                # 启动命令监听线程
                def command_listener():
                    """监听用户输入的命令"""
                    while self.running:
                        try:
                            command = input("MVPLittleChat> ").strip().lower()
                            if command in ['quit', 'exit', 'stop']:
                                print("\n" + "=" * 60)
                                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ⚠️  收到退出命令，正在关闭服务器...")
                                self.running = False
                                break
                            elif command in ['help', '?']:
                                print("-" * 60)
                                print("可用命令:")
                                print("  quit, exit, stop  - 关闭服务器")
                                print("  help, ?          - 显示帮助信息")
                                print("  status           - 显示服务器状态")
                                print("  version          - 显示当前版本号")
                                print("  op <用户名>       - 将指定用户设置为管理员")
                                print("  unop <用户名>     - 撤销指定用户的管理员权限")
                                print("  kick <用户名>     - 踢出指定用户")
                                print("  ban <用户名>      - 封禁指定用户的IP")
                                print("  unban <用户名或IP>    - 解除指定IP的封禁")
                                print("  shutup <用户名> <时间> - 禁言指定时长（分钟）")
                                print("  unshutup <用户名> - 解除指定用户的禁言")
                                print("-" * 60)
                            elif command == 'version':
                                print("-" * 60)
                                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 🔍 服务器版本: v{CURRENT_VERSION}")
                                print("-" * 60)
                            elif command == 'status':
                                print("-" * 60)
                                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 🔍 服务器状态: {'运行中' if self.running else '已关闭'}")
                                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 🚪 监听端口: {self.port}")
                                with self.lock:
                                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 👥 在线客户端: {len(self.client_sockets)}")
                                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 🕒 运行时长: {self._get_running_time()}")
                                print("-" * 60)
                            elif command.startswith('op '):
                                # 处理op命令
                                parts = command.split(' ', 1)
                                if len(parts) == 2:
                                    target_nickname = parts[1].strip()
                                    # 查找目标用户的socket
                                    target_socket = None
                                    with self.lock:
                                        for sock, n in self.client_nicknames.items():
                                            if n == target_nickname:
                                                target_socket = sock
                                                break
                                        self.admins.add(target_nickname)
                                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ✅ 已将 {target_nickname} 设置为管理员")
                                    # 通知所有用户
                                    broadcast_msg = f"系统: {target_nickname} 已成为管理员"
                                    self.broadcast_message(broadcast_msg)
                                    # 向被设为管理员的用户发送特定消息，触发客户端弹窗
                                    if target_socket:
                                        try:
                                            target_socket.send(f"OP:{broadcast_msg}".encode('utf-8'))
                                        except:
                                            pass
                                    # 更新所有客户端的用户列表，显示管理员标识
                                    self.broadcast_user_list()
                                else:
                                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ❌ 命令格式错误: op <用户名>")
                            elif command.startswith('unop '):
                                # 处理unop命令
                                parts = command.split(' ', 1)
                                if len(parts) == 2:
                                    target_nickname = parts[1].strip()
                                    is_admin = False
                                    target_socket = None
                                    with self.lock:
                                        # 查找目标用户的socket
                                        for sock, n in self.client_nicknames.items():
                                            if n == target_nickname:
                                                target_socket = sock
                                                break
                                        if target_nickname in self.admins:
                                            self.admins.remove(target_nickname)
                                            is_admin = True
                                    
                                    if is_admin:
                                        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ✅ 已撤销 {target_nickname} 的管理员权限")
                                        # 通知所有用户
                                        broadcast_msg = f"系统: {target_nickname} 已被撤销管理员权限"
                                        self.broadcast_message(broadcast_msg)
                                        # 向被撤销管理员权限的用户发送特定消息，触发客户端弹窗
                                        if target_socket:
                                            try:
                                                target_socket.send(f"UNOP:{broadcast_msg}".encode('utf-8'))
                                            except:
                                                pass
                                        # 更新所有客户端的用户列表，恢复原昵称显示
                                        self.broadcast_user_list()
                                    else:
                                        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ❌ {target_nickname} 不是管理员")
                                else:
                                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ❌ 命令格式错误: unop <用户名>")
                            elif command.startswith('ban '):
                                # 处理ban命令
                                parts = command.split(' ', 1)
                                if len(parts) == 2:
                                    target_nickname = parts[1].strip()
                                    # 查找目标用户的IP地址
                                    target_ip = None
                                    with self.lock:
                                        for sock, n in self.client_nicknames.items():
                                            if n == target_nickname:
                                                # 找到目标用户，获取其IP地址
                                                if sock in self.client_profiles:
                                                    target_ip = self.client_profiles[sock]['ip_address']
                                                break
                                    
                                    if target_ip:
                                        # 封禁目标用户的IP
                                        with self.lock:
                                            self.banned_ips.add(target_ip)
                                        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ✅ 已封禁IP {target_ip}（用户：{target_nickname}）")
                                        # 踢出该用户（如果在线）
                                        self.kick_user(target_nickname)
                                        # 通知所有用户
                                        self.broadcast_message(f"系统: 用户 {target_nickname} 的IP {target_ip} 已被封禁")
                                    else:
                                        # 用户不在线或找不到IP
                                        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ❌ 找不到用户 {target_nickname} 或其IP地址")
                                else:
                                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ❌ 命令格式错误: ban <用户名>")
                            elif command.startswith('unban '):
                                # 处理unban命令
                                parts = command.split(' ', 1)
                                if len(parts) == 2:
                                    target = parts[1].strip()
                                    target_ip = None
                                    target_user = target  # 保存原始目标名称
                                    
                                    # 检查目标是否是IP地址格式
                                    import re
                                    ip_pattern = r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$'
                                    if re.match(ip_pattern, target):
                                        # 直接使用IP地址
                                        target_ip = target
                                    else:
                                        # 尝试通过用户名查找IP地址
                                        with self.lock:
                                            for sock, n in self.client_nicknames.items():
                                                if n == target:
                                                    # 找到目标用户，获取其IP地址
                                                    if sock in self.client_profiles:
                                                        target_ip = self.client_profiles[sock]['ip_address']
                                                    break
                                    
                                    if target_ip:
                                        with self.lock:
                                            if target_ip in self.banned_ips:
                                                self.banned_ips.remove(target_ip)
                                                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ✅ 已解除IP {target_ip} 的封禁")
                                                # 通知所有用户
                                                if target_user != target_ip:
                                                    self.broadcast_message(f"系统: 用户 {target_user} 的IP {target_ip} 已被解除封禁")
                                                else:
                                                    self.broadcast_message(f"系统: IP {target_ip} 已被解除封禁")
                                            else:
                                                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ❌ IP {target_ip} 未被封禁")
                                    else:
                                        # 无法找到目标IP
                                        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ❌ 找不到目标 {target} 或其IP地址")
                                else:
                                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ❌ 命令格式错误: unban <用户名或IP>")
                            elif command.startswith('shutup '):
                                # 处理shutup命令
                                parts = command.split(' ', 2)
                                if len(parts) == 3:
                                    target_nickname = parts[1].strip()
                                    try:
                                        duration = int(parts[2].strip())
                                        if duration > 0:
                                            # 查找目标用户的socket
                                            target_socket = None
                                            with self.lock:
                                                for sock, n in self.client_nicknames.items():
                                                    if n == target_nickname:
                                                        target_socket = sock
                                                        break
                                                self.muted_users[target_nickname] = (time.time(), duration)
                                            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ✅ 已禁言 {target_nickname} {duration} 分钟")
                                            # 通知所有用户
                                            broadcast_msg = f"系统: {target_nickname} 已被禁言 {duration} 分钟"
                                            self.broadcast_message(broadcast_msg)
                                            # 向被禁言的用户发送特定消息，触发客户端弹窗
                                            if target_socket:
                                                try:
                                                    target_socket.send(f"MUTED:{broadcast_msg}".encode('utf-8'))
                                                except:
                                                    pass
                                        else:
                                            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ❌ 禁言时长必须大于0")
                                    except ValueError:
                                        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ❌ 命令格式错误: shutup <用户名> <时间（分钟）>")
                                else:
                                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ❌ 命令格式错误: shutup <用户名> <时间（分钟）>")
                            elif command.startswith('unshutup '):
                                # 处理unshutup命令
                                parts = command.split(' ', 1)
                                if len(parts) == 2:
                                    target_nickname = parts[1].strip()
                                    target_socket = None
                                    with self.lock:
                                        # 查找目标用户的socket
                                        for sock, n in self.client_nicknames.items():
                                            if n == target_nickname:
                                                target_socket = sock
                                                break
                                        if target_nickname in self.muted_users:
                                            del self.muted_users[target_nickname]
                                            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ✅ 已解除 {target_nickname} 的禁言")
                                            # 通知所有用户
                                            broadcast_msg = f"系统: {target_nickname} 已被解除禁言"
                                            self.broadcast_message(broadcast_msg)
                                            # 向被解禁的用户发送特定消息，触发客户端弹窗
                                            if target_socket:
                                                try:
                                                    target_socket.send(f"UNMUTED:{broadcast_msg}".encode('utf-8'))
                                                except:
                                                    pass
                                        else:
                                            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ❌ {target_nickname} 未被禁言")
                                else:
                                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ❌ 命令格式错误: unshutup <用户名>")
                            elif command.startswith('kick '):
                                # 处理kick命令
                                parts = command.split(' ', 1)
                                if len(parts) == 2:
                                    target_nickname = parts[1].strip()
                                    self.kick_user(target_nickname)
                                else:
                                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ❌ 命令格式错误: kick <用户名>")
                            elif command:
                                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ❓ 未知命令: {command}")
                                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 💡 提示: 输入 'help' 查看可用命令")
                        except EOFError:
                            # 处理Ctrl+D输入
                            print("\n" + "=" * 60)
                            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ⚠️  收到EOF信号，正在关闭服务器...")
                            self.running = False
                            break
                        except KeyboardInterrupt:
                            # 处理Ctrl+C输入
                            print("\n" + "=" * 60)
                            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ⚠️  收到中断信号，正在关闭服务器...")
                            self.running = False
                            break
                        except Exception as e:
                            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ❌ 命令处理错误: {str(e)}")
                
                # 创建并启动命令监听线程
                command_thread = threading.Thread(target=command_listener)
                command_thread.daemon = True  # 设置为守护线程
                command_thread.start()
                
                while self.running:
                    try:
                        # 设置超时，定期检查running状态
                        self.server_socket.settimeout(self.socket_timeout)  # 从配置文件读取超时时间
                        client_socket, client_address = self.server_socket.accept()
                        # 为每个客户端创建一个新线程
                        client_thread = threading.Thread(target=self.handle_client, args=(client_socket, client_address))
                        client_thread.daemon = True  # 设置为守护线程，服务器关闭时自动退出
                        client_thread.start()
                    except socket.timeout:
                        # 超时异常，继续循环检查running状态
                        continue
                    except KeyboardInterrupt:
                        print("\n" + "=" * 60)
                        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ⚠️  收到中断信号，正在关闭服务器...")
                        self.running = False
                        break
                    except Exception as e:
                        if not self.running:
                            break
                        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ❌ 接受客户端连接时发生错误: {str(e)}")
                        if not self.running:
                            break
        except Exception as e:
            print("=" * 60)
            print("" * 20 + "❌ 服务器启动失败 ❌")
            print("=" * 60)
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 🔍 错误原因: {str(e)}")
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 💡 建议: 检查端口是否被占用或权限是否足够")
            self.running = False
        finally:
            self.stop()
    
    def stop(self):
        """停止服务器"""
        if not self.running:
            return
        
        print("-" * 60)
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 🔄 正在关闭服务器...")
        self.running = False
        
        # 关闭所有客户端连接
        with self.lock:
            client_count = len(self.client_sockets)
            clients_copy = self.client_sockets.copy()
            self.client_sockets.clear()
            self.client_nicknames.clear()
        
        for client in clients_copy:
            try:
                client.close()
            except:
                pass
        
        # 关闭服务器套接字
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        
        print("=" * 60)
        print("" * 20 + "✅ 服务器已关闭 ✅")
        print("=" * 60)
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 🔍 服务器状态: 已关闭")
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 📊 已断开客户端数: {client_count}")
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 🕒 运行时长: {self._get_running_time()}")
        print("=" * 60)


def start_server():
    """启动聊天服务器"""
    server = ChatServer()
    server.start()


if __name__ == "__main__":
    try:
        start_server()
    except KeyboardInterrupt:
        print("\n服务器已被用户中断")
    except Exception as e:
        print(f"服务器发生未处理的异常: {str(e)}")