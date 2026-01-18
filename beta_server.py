import socket
import threading
import time
import os
import requests
from flask import Flask, render_template_string, jsonify, request

# 版本信息
CURRENT_VERSION = "3.2.0"

# Gitee配置
GITEE_OWNER = "MVPS680"
GITEE_REPO = "MVPLittlechat"

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
        # 设置请求头，不包含Token认证
        headers = {
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
        
        print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] [成功] 下载完成: {file_name}")
        
    except requests.exceptions.RequestException as e:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [错误] 下载失败: 网络请求错误 - {str(e)}")
    except Exception as e:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [错误] 下载失败: {str(e)}")

def check_for_updates():
    """检查Gitee仓库是否有新的发行版"""
    try:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [信息] 正在检查更新...")
        
        # 构建API请求URL
        url = f"https://gitee.com/api/v5/repos/{GITEE_OWNER}/{GITEE_REPO}/releases/latest"
        
        # 设置请求头，不包含Token认证
        headers = {
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
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [警告] 您的版本已落后最新版本两个或更多版本，为了保证正常使用，请立即更新！")
            print(f"当前版本：{CURRENT_VERSION}")
            print(f"最新版本：{latest_version}")
            print(f"\n更新日志：")
            print(release_notes)
            
            # 强制更新询问用户
            choice = input("是否立即下载更新？: ").strip().lower()
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
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [信息] 发现新版本！")
            print(f"当前版本：{CURRENT_VERSION}")
            print(f"最新版本：{latest_version}")
            print(f"\n更新日志：")
            print(release_notes)
            
            # 询问用户是否更新
            choice = input("是否下载更新？: ").strip().lower()
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
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [成功] 当前已是最新版本！")
            print(f"当前版本：{CURRENT_VERSION}")
        else:
            # 当前版本高于最新版本
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [成功] 当前版本已高于最新发布版本！")
            print(f"当前版本：{CURRENT_VERSION}")
            
    except requests.exceptions.RequestException as e:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [错误] 检查更新失败：网络请求错误 - {str(e)}")
    except Exception as e:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [错误] 检查更新失败：{str(e)}")

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
        "message_size_limit": "1024",
        "web_port": "5000",
        "web_enabled": "true"
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
                    f.write("# 日志级别\n")
                    f.write(f"{key}={value} # 默认日志级别：info\n\n")
                elif key == "message_size_limit":
                    f.write("# 单个消息的最大长度（字节）\n")
                    f.write(f"{key}={value} # 默认消息大小：1024字节\n\n")
                elif key == "web_port":
                    f.write("# Web管理界面端口号\n")
                    f.write(f"{key}={value} # 默认Web端口：5000\n\n")
                elif key == "web_enabled":
                    f.write("# 是否启用Web管理界面\n")
                    f.write(f"{key}={value} # 默认启用：true\n\n")
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


# Flask Web UI 模板
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MVPLittleChat 服务器管理</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css" rel="stylesheet">
    <style>
        :root {
            --primary-color: #4a90e2;
            --secondary-color: #357abd;
            --success-color: #28a745;
            --danger-color: #dc3545;
            --warning-color: #ffc107;
            --info-color: #17a2b8;
            --dark-bg: #1a1a2e;
            --light-bg: #16213e;
            --card-bg: #0f3460;
            --text-color: #eaeaea;
            --border-radius: 8px;
        }
        
        body {
            background: linear-gradient(135deg, var(--dark-bg) 0%, var(--light-bg) 100%);
            color: var(--text-color);
            min-height: 100vh;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        
        .navbar {
            background: linear-gradient(90deg, var(--primary-color) 0%, var(--secondary-color) 100%);
            box-shadow: 0 2px 10px rgba(0,0,0,0.3);
        }
        
        .navbar-brand {
            font-weight: bold;
            font-size: 1.5rem;
        }
        
        .card {
            background: var(--card-bg);
            border: none;
            border-radius: var(--border-radius);
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
            margin-bottom: 20px;
        }
        
        .card-header {
            background: rgba(74, 144, 226, 0.2);
            border-bottom: 1px solid rgba(255,255,255,0.1);
            font-weight: bold;
            padding: 15px 20px;
        }
        
        .card-body {
            padding: 20px;
        }
        
        .stat-card {
            text-align: center;
            padding: 20px;
            transition: transform 0.3s ease;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
        }
        
        .stat-value {
            font-size: 2.5rem;
            font-weight: bold;
            margin: 10px 0;
        }
        
        .stat-label {
            color: #aaa;
            font-size: 0.9rem;
        }
        
        .stat-icon {
            font-size: 3rem;
            margin-bottom: 10px;
        }
        
        .table {
            background: transparent;
            color: var(--text-color);
        }
        
        .table thead th {
            background: rgba(74, 144, 226, 0.2);
            border-color: rgba(255,255,255,0.1);
            color: var(--text-color);
        }
        
        .table tbody tr {
            border-color: rgba(255,255,255,0.05);
            transition: background 0.3s ease;
        }
        
        .table tbody tr:hover {
            background: rgba(255,255,255,0.05);
        }
        
        .btn {
            border-radius: var(--border-radius);
            padding: 8px 16px;
            font-weight: 500;
            transition: all 0.3s ease;
        }
        
        .btn-primary {
            background: var(--primary-color);
            border-color: var(--primary-color);
        }
        
        .btn-primary:hover {
            background: var(--secondary-color);
            border-color: var(--secondary-color);
        }
        
        .badge {
            padding: 6px 12px;
            border-radius: var(--border-radius);
        }
        
        .badge-admin {
            background: var(--warning-color);
            color: #000;
        }
        
        .badge-muted {
            background: var(--danger-color);
        }
        
        .badge-normal {
            background: var(--success-color);
        }
        
        .modal-content {
            background: var(--card-bg);
            border: none;
            border-radius: var(--border-radius);
        }
        
        .modal-header {
            background: rgba(74, 144, 226, 0.2);
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        
        .modal-footer {
            border-top: 1px solid rgba(255,255,255,0.1);
        }
        
        .form-control, .form-select {
            background: rgba(255,255,255,0.1);
            border: 1px solid rgba(255,255,255,0.2);
            color: var(--text-color);
            border-radius: var(--border-radius);
        }
        
        .form-control:focus, .form-select:focus {
            background: rgba(255,255,255,0.15);
            border-color: var(--primary-color);
            color: var(--text-color);
            box-shadow: 0 0 0 0.2rem rgba(74, 144, 226, 0.25);
        }
        
        .form-control::placeholder {
            color: rgba(255,255,255,0.5);
        }
        
        .nav-tabs {
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        
        .nav-tabs .nav-link {
            color: var(--text-color);
            border: none;
            padding: 10px 20px;
            transition: all 0.3s ease;
        }
        
        .nav-tabs .nav-link:hover {
            background: rgba(255,255,255,0.05);
            color: var(--primary-color);
        }
        
        .nav-tabs .nav-link.active {
            background: rgba(74, 144, 226, 0.2);
            color: var(--primary-color);
            border-bottom: 2px solid var(--primary-color);
        }
        
        .alert {
            border-radius: var(--border-radius);
            border: none;
        }
        
        .loading-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.7);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 9999;
        }
        
        .spinner-border {
            width: 3rem;
            height: 3rem;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .status-online {
            animation: pulse 2s infinite;
        }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark">
        <div class="container-fluid">
            <a class="navbar-brand" href="#">
                <i class="bi bi-chat-dots-fill me-2"></i>MVPLittleChat
            </a>
            <span class="navbar-text ms-auto">
                <i class="bi bi-circle-fill status-online text-success me-2"></i>
                服务器运行中
            </span>
        </div>
    </nav>

    <div class="container-fluid mt-4">
        <ul class="nav nav-tabs mb-4" id="serverTabs" role="tablist">
            <li class="nav-item" role="presentation">
                <button class="nav-link active" id="dashboard-tab" data-bs-toggle="tab" data-bs-target="#dashboard" type="button" role="tab">
                    <i class="bi bi-speedometer2 me-2"></i>仪表盘
                </button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link" id="users-tab" data-bs-toggle="tab" data-bs-target="#users" type="button" role="tab">
                    <i class="bi bi-people me-2"></i>用户管理
                </button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link" id="banned-tab" data-bs-toggle="tab" data-bs-target="#banned" type="button" role="tab">
                    <i class="bi bi-shield-x me-2"></i>封禁管理
                </button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link" id="muted-tab" data-bs-toggle="tab" data-bs-target="#muted" type="button" role="tab">
                    <i class="bi bi-megaphone-fill me-2"></i>禁言管理
                </button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link" id="config-tab" data-bs-toggle="tab" data-bs-target="#config" type="button" role="tab">
                    <i class="bi bi-gear me-2"></i>服务器配置
                </button>
            </li>
        </ul>

        <div class="tab-content" id="serverTabsContent">
            <!-- 仪表盘 -->
            <div class="tab-pane fade show active" id="dashboard" role="tabpanel">
                <div class="row">
                    <div class="col-md-3">
                        <div class="card stat-card">
                            <i class="bi bi-people-fill stat-icon text-primary"></i>
                            <div class="stat-value" id="onlineUsers">0</div>
                            <div class="stat-label">在线用户</div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card stat-card">
                            <i class="bi bi-shield-fill-check stat-icon text-success"></i>
                            <div class="stat-value" id="adminCount">0</div>
                            <div class="stat-label">管理员</div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card stat-card">
                            <i class="bi bi-clock-fill stat-icon text-warning"></i>
                            <div class="stat-value" id="uptime">0s</div>
                            <div class="stat-label">运行时间</div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card stat-card">
                            <i class="bi bi-tag-fill stat-icon text-info"></i>
                            <div class="stat-value" id="version">v{{ version }}</div>
                            <div class="stat-label">版本</div>
                        </div>
                    </div>
                </div>

                <div class="row mt-4">
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header">
                                <i class="bi bi-info-circle me-2"></i>服务器信息
                            </div>
                            <div class="card-body">
                                <table class="table table-sm">
                                    <tr>
                                        <td><strong>监听地址:</strong></td>
                                        <td>0.0.0.0</td>
                                    </tr>
                                    <tr>
                                        <td><strong>聊天端口:</strong></td>
                                        <td>{{ chat_port }}</td>
                                    </tr>
                                    <tr>
                                        <td><strong>Web端口:</strong></td>
                                        <td>{{ web_port }}</td>
                                    </tr>
                                    <tr>
                                        <td><strong>最大连接数:</strong></td>
                                        <td>{{ max_user }}</td>
                                    </tr>
                                    <tr>
                                        <td><strong>服务器IP:</strong></td>
                                        <td>{{ server_ip }}</td>
                                    </tr>
                                </table>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header">
                                <i class="bi bi-bell me-2"></i>快速操作
                            </div>
                            <div class="card-body">
                                <div class="d-grid gap-2">
                                    <button class="btn btn-primary" onclick="refreshData()">
                                        <i class="bi bi-arrow-clockwise me-2"></i>刷新数据
                                    </button>
                                    <button class="btn btn-warning" onclick="showKickAllModal()">
                                        <i class="bi bi-person-x me-2"></i>踢出所有用户
                                    </button>
                                    <button class="btn btn-danger" onclick="showStopServerModal()">
                                        <i class="bi bi-power me-2"></i>停止服务器
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- 用户管理 -->
            <div class="tab-pane fade" id="users" role="tabpanel">
                <div class="card">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <span><i class="bi bi-people me-2"></i>在线用户列表</span>
                        <button class="btn btn-sm btn-primary" onclick="refreshData()">
                            <i class="bi bi-arrow-clockwise"></i> 刷新
                        </button>
                    </div>
                    <div class="card-body">
                        <div class="table-responsive">
                            <table class="table table-hover" id="usersTable">
                                <thead>
                                    <tr>
                                        <th>昵称</th>
                                        <th>IP地址</th>
                                        <th>加入时间</th>
                                        <th>状态</th>
                                        <th>操作</th>
                                    </tr>
                                </thead>
                                <tbody id="usersTableBody">
                                    <!-- 动态填充 -->
                                </tbody>
                            </table>
                        </div>
                        <div id="noUsers" class="text-center py-4" style="display: none;">
                            <i class="bi bi-people" style="font-size: 3rem; color: #666;"></i>
                            <p class="mt-2">暂无在线用户</p>
                        </div>
                    </div>
                </div>
            </div>

            <!-- 封禁管理 -->
            <div class="tab-pane fade" id="banned" role="tabpanel">
                <div class="card">
                    <div class="card-header">
                        <i class="bi bi-shield-x me-2"></i>封禁IP列表
                    </div>
                    <div class="card-body">
                        <div class="table-responsive">
                            <table class="table table-hover" id="bannedTable">
                                <thead>
                                    <tr>
                                        <th>IP地址</th>
                                        <th>操作</th>
                                    </tr>
                                </thead>
                                <tbody id="bannedTableBody">
                                    <!-- 动态填充 -->
                                </tbody>
                            </table>
                        </div>
                        <div id="noBanned" class="text-center py-4" style="display: none;">
                            <i class="bi bi-shield-check" style="font-size: 3rem; color: #666;"></i>
                            <p class="mt-2">暂无封禁IP</p>
                        </div>
                    </div>
                </div>
            </div>

            <!-- 禁言管理 -->
            <div class="tab-pane fade" id="muted" role="tabpanel">
                <div class="card">
                    <div class="card-header">
                        <i class="bi bi-megaphone-fill me-2"></i>禁言用户列表
                    </div>
                    <div class="card-body">
                        <div class="table-responsive">
                            <table class="table table-hover" id="mutedTable">
                                <thead>
                                    <tr>
                                        <th>用户名</th>
                                        <th>禁言时长（分钟）</th>
                                        <th>剩余时间</th>
                                        <th>操作</th>
                                    </tr>
                                </thead>
                                <tbody id="mutedTableBody">
                                    <!-- 动态填充 -->
                                </tbody>
                            </table>
                        </div>
                        <div id="noMuted" class="text-center py-4" style="display: none;">
                            <i class="bi bi-megaphone" style="font-size: 3rem; color: #666;"></i>
                            <p class="mt-2">暂无禁言用户</p>
                        </div>
                    </div>
                </div>
            </div>

            <!-- 服务器配置 -->
            <div class="tab-pane fade" id="config" role="tabpanel">
                <div class="card">
                    <div class="card-header">
                        <i class="bi bi-gear me-2"></i>服务器配置
                    </div>
                    <div class="card-body">
                        <form id="configForm">
                            <div class="mb-3">
                                <label for="serverPort" class="form-label">聊天服务器端口</label>
                                <input type="number" class="form-control" id="serverPort" value="{{ chat_port }}">
                            </div>
                            <div class="mb-3">
                                <label for="maxUser" class="form-label">最大连接数</label>
                                <input type="number" class="form-control" id="maxUser" value="{{ max_user }}">
                            </div>
                            <div class="mb-3">
                                <label for="messageSizeLimit" class="form-label">消息大小限制（字节）</label>
                                <input type="number" class="form-control" id="messageSizeLimit" value="{{ message_size_limit }}">
                            </div>
                            <div class="mb-3">
                                <label for="adminPrefix" class="form-label">管理员前缀</label>
                                <input type="text" class="form-control" id="adminPrefix" value="{{ admin_prefix }}">
                            </div>
                            <button type="button" class="btn btn-primary" onclick="saveConfig()">
                                <i class="bi bi-save me-2"></i>保存配置
                            </button>
                        </form>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- 用户操作模态框 -->
    <div class="modal fade" id="userActionModal" tabindex="-1">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">用户操作</h5>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <p>对用户 <strong id="actionUsername"></strong> 执行操作：</p>
                    <div class="d-grid gap-2">
                        <button class="btn btn-warning" onclick="performAction('kick')">
                            <i class="bi bi-person-x me-2"></i>踢出用户
                        </button>
                        <button class="btn btn-danger" onclick="performAction('ban')">
                            <i class="bi bi-shield-x me-2"></i>封禁IP
                        </button>
                        <button class="btn btn-info" onclick="showMuteModal()">
                            <i class="bi bi-megaphone-fill me-2"></i>禁言
                        </button>
                        <button class="btn btn-success" id="opBtn" onclick="performAction('op')">
                            <i class="bi bi-person-check me-2"></i>设为管理员
                        </button>
                        <button class="btn btn-secondary" id="unopBtn" onclick="performAction('unop')" style="display: none;">
                            <i class="bi bi-person-dash me-2"></i>撤销管理员
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- 禁言模态框 -->
    <div class="modal fade" id="muteModal" tabindex="-1">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">禁言用户</h5>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <div class="mb-3">
                        <label for="muteDuration" class="form-label">禁言时长（分钟）</label>
                        <input type="number" class="form-control" id="muteDuration" min="1" value="10">
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                    <button type="button" class="btn btn-primary" onclick="performMute()">确认禁言</button>
                </div>
            </div>
        </div>
    </div>

    <!-- 停止服务器确认模态框 -->
    <div class="modal fade" id="stopServerModal" tabindex="-1">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title text-danger">确认停止服务器</h5>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <p>您确定要停止服务器吗？此操作将断开所有用户连接。</p>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                    <button type="button" class="btn btn-danger" onclick="stopServer()">确认停止</button>
                </div>
            </div>
        </div>
    </div>

    <!-- 踢出所有用户确认模态框 -->
    <div class="modal fade" id="kickAllModal" tabindex="-1">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title text-warning">确认踢出所有用户</h5>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <p>您确定要踢出所有在线用户吗？</p>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                    <button type="button" class="btn btn-warning" onclick="kickAllUsers()">确认踢出</button>
                </div>
            </div>
        </div>
    </div>

    <!-- 加载遮罩 -->
    <div class="loading-overlay" id="loadingOverlay" style="display: none;">
        <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">加载中...</span>
        </div>
    </div>

    <!-- 提示消息 -->
    <div class="position-fixed bottom-0 end-0 p-3" style="z-index: 11">
        <div id="toast" class="toast align-items-center text-white bg-success border-0" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body" id="toastMessage"></div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        let currentActionUser = null;
        let userActionModal = null;
        let muteModal = null;
        let stopServerModal = null;
        let kickAllModal = null;
        let toast = null;

        document.addEventListener('DOMContentLoaded', function() {
            userActionModal = new bootstrap.Modal(document.getElementById('userActionModal'));
            muteModal = new bootstrap.Modal(document.getElementById('muteModal'));
            stopServerModal = new bootstrap.Modal(document.getElementById('stopServerModal'));
            kickAllModal = new bootstrap.Modal(document.getElementById('kickAllModal'));
            toast = new bootstrap.Toast(document.getElementById('toast'));
            
            // 初始加载数据
            refreshData();
            
            // 每5秒自动刷新数据
            setInterval(refreshData, 5000);
        });

        function showLoading() {
            document.getElementById('loadingOverlay').style.display = 'flex';
        }

        function hideLoading() {
            document.getElementById('loadingOverlay').style.display = 'none';
        }

        function showToast(message, type = 'success') {
            const toastEl = document.getElementById('toast');
            const toastMessage = document.getElementById('toastMessage');
            toastMessage.textContent = message;
            toastEl.className = `toast align-items-center text-white bg-${type} border-0`;
            toast.show();
        }

        async function refreshData() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                
                // 更新仪表盘
                document.getElementById('onlineUsers').textContent = data.online_users;
                document.getElementById('adminCount').textContent = data.admin_count;
                document.getElementById('uptime').textContent = data.uptime;
                
                // 更新用户列表
                const usersTableBody = document.getElementById('usersTableBody');
                const noUsers = document.getElementById('noUsers');
                
                if (data.users.length === 0) {
                    usersTableBody.innerHTML = '';
                    noUsers.style.display = 'block';
                } else {
                    noUsers.style.display = 'none';
                    usersTableBody.innerHTML = data.users.map(user => `
                        <tr>
                            <td>
                                <strong>${user.nickname}</strong>
                                ${user.is_admin ? '<span class="badge badge-admin ms-2">管理员</span>' : ''}
                                ${user.is_muted ? '<span class="badge badge-muted ms-2">禁言中</span>' : ''}
                            </td>
                            <td>${user.ip_address}</td>
                            <td>${user.join_time}</td>
                            <td>
                                <span class="badge ${user.is_admin ? 'badge-admin' : 'badge-normal'}">
                                    ${user.is_admin ? '管理员' : '普通用户'}
                                </span>
                            </td>
                            <td>
                                <button class="btn btn-sm btn-primary" onclick="showUserAction('${user.nickname}', ${user.is_admin})">
                                    <i class="bi bi-gear"></i> 管理
                                </button>
                            </td>
                        </tr>
                    `).join('');
                }
                
                // 更新封禁列表
                const bannedTableBody = document.getElementById('bannedTableBody');
                const noBanned = document.getElementById('noBanned');
                
                if (data.banned_ips.length === 0) {
                    bannedTableBody.innerHTML = '';
                    noBanned.style.display = 'block';
                } else {
                    noBanned.style.display = 'none';
                    bannedTableBody.innerHTML = data.banned_ips.map(ip => `
                        <tr>
                            <td>${ip}</td>
                            <td>
                                <button class="btn btn-sm btn-success" onclick="unbanIP('${ip}')">
                                    <i class="bi bi-shield-check"></i> 解封
                                </button>
                            </td>
                        </tr>
                    `).join('');
                }
                
                // 更新禁言列表
                const mutedTableBody = document.getElementById('mutedTableBody');
                const noMuted = document.getElementById('noMuted');
                
                if (data.muted_users.length === 0) {
                    mutedTableBody.innerHTML = '';
                    noMuted.style.display = 'block';
                } else {
                    noMuted.style.display = 'none';
                    mutedTableBody.innerHTML = data.muted_users.map(user => `
                        <tr>
                            <td>${user.nickname}</td>
                            <td>${user.duration} 分钟</td>
                            <td>${user.remaining_time}</td>
                            <td>
                                <button class="btn btn-sm btn-success" onclick="unmuteUser('${user.nickname}')">
                                    <i class="bi bi-megaphone"></i> 解禁
                                </button>
                            </td>
                        </tr>
                    `).join('');
                }
            } catch (error) {
                console.error('刷新数据失败:', error);
            }
        }

        function showUserAction(username, isAdmin) {
            currentActionUser = username;
            document.getElementById('actionUsername').textContent = username;
            
            const opBtn = document.getElementById('opBtn');
            const unopBtn = document.getElementById('unopBtn');
            
            if (isAdmin) {
                opBtn.style.display = 'none';
                unopBtn.style.display = 'block';
            } else {
                opBtn.style.display = 'block';
                unopBtn.style.display = 'none';
            }
            
            userActionModal.show();
        }

        function showMuteModal() {
            userActionModal.hide();
            muteModal.show();
        }

        async function performAction(action) {
            if (!currentActionUser) return;
            
            showLoading();
            
            try {
                const response = await fetch('/api/action', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        action: action,
                        username: currentActionUser
                    })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    showToast(result.message, 'success');
                    await refreshData();
                } else {
                    showToast(result.message, 'danger');
                }
            } catch (error) {
                console.error('操作失败:', error);
                showToast('操作失败', 'danger');
            } finally {
                hideLoading();
                userActionModal.hide();
            }
        }

        async function performMute() {
            if (!currentActionUser) return;
            
            const duration = document.getElementById('muteDuration').value;
            
            showLoading();
            
            try {
                const response = await fetch('/api/action', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        action: 'mute',
                        username: currentActionUser,
                        duration: parseInt(duration)
                    })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    showToast(result.message, 'success');
                    await refreshData();
                } else {
                    showToast(result.message, 'danger');
                }
            } catch (error) {
                console.error('禁言失败:', error);
                showToast('操作失败', 'danger');
            } finally {
                hideLoading();
                muteModal.hide();
            }
        }

        async function unbanIP(ip) {
            if (!confirm(`确定要解封IP ${ip} 吗？`)) return;
            
            showLoading();
            
            try {
                const response = await fetch('/api/unban', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ ip: ip })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    showToast(result.message, 'success');
                    await refreshData();
                } else {
                    showToast(result.message, 'danger');
                }
            } catch (error) {
                console.error('解封失败:', error);
                showToast('操作失败', 'danger');
            } finally {
                hideLoading();
            }
        }

        async function unmuteUser(username) {
            if (!confirm(`确定要解除 ${username} 的禁言吗？`)) return;
            
            showLoading();
            
            try {
                const response = await fetch('/api/unmute', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ username: username })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    showToast(result.message, 'success');
                    await refreshData();
                } else {
                    showToast(result.message, 'danger');
                }
            } catch (error) {
                console.error('解禁失败:', error);
                showToast('操作失败', 'danger');
            } finally {
                hideLoading();
            }
        }

        function showKickAllModal() {
            kickAllModal.show();
        }

        async function kickAllUsers() {
            showLoading();
            
            try {
                const response = await fetch('/api/kickall', {
                    method: 'POST'
                });
                
                const result = await response.json();
                
                if (result.success) {
                    showToast(result.message, 'success');
                    await refreshData();
                } else {
                    showToast(result.message, 'danger');
                }
            } catch (error) {
                console.error('踢出所有用户失败:', error);
                showToast('操作失败', 'danger');
            } finally {
                hideLoading();
                kickAllModal.hide();
            }
        }

        function showStopServerModal() {
            stopServerModal.show();
        }

        async function stopServer() {
            showLoading();
            
            try {
                const response = await fetch('/api/stop', {
                    method: 'POST'
                });
                
                const result = await response.json();
                
                if (result.success) {
                    showToast('服务器正在关闭...', 'warning');
                    setTimeout(() => {
                        location.reload();
                    }, 3000);
                } else {
                    showToast(result.message, 'danger');
                }
            } catch (error) {
                showToast('操作失败', 'danger');
            }
            
            hideLoading();
            stopServerModal.hide();
        }

        async function saveConfig() {
            showLoading();
            
            const config = {
                server_port: document.getElementById('serverPort').value,
                max_user: document.getElementById('maxUser').value,
                message_size_limit: document.getElementById('messageSizeLimit').value,
                admin_prefix: document.getElementById('adminPrefix').value
            };
            
            try {
                const response = await fetch('/api/config', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(config)
                });
                
                const result = await response.json();
                
                if (result.success) {
                    showToast('配置保存成功，请重启服务器生效', 'success');
                } else {
                    showToast(result.message, 'danger');
                }
            } catch (error) {
                console.error('保存配置失败:', error);
                showToast('保存失败', 'danger');
            } finally {
                hideLoading();
            }
        }
    </script>
</body>
</html>
"""


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
        self.web_port = int(config.get("web_port", "5000"))
        self.web_enabled = config.get("web_enabled", "true").lower() == "true"
        
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
        
        # Flask 应用
        self.app = Flask(__name__)
        self.app.secret_key = 'mvplittlechat-secret-key-2024'
        self.setup_flask_routes()
    
    def setup_flask_routes(self):
        """设置Flask路由"""
        
        @self.app.route('/')
        def index():
            """主页 - Web管理界面"""
            return render_template_string(
                HTML_TEMPLATE,
                version=CURRENT_VERSION,
                chat_port=self.port,
                web_port=self.web_port,
                max_user=self.max_user,
                server_ip=socket.gethostbyname(socket.gethostname()),
                message_size_limit=self.message_size_limit,
                admin_prefix=self.admin_prefix
            )
        
        @self.app.route('/api/status')
        def api_status():
            """获取服务器状态API"""
            with self.lock:
                users = []
                for sock, nickname in self.client_nicknames.items():
                    profile = self.client_profiles.get(sock, {})
                    users.append({
                        'nickname': nickname,
                        'ip_address': profile.get('ip_address', '未知'),
                        'join_time': profile.get('join_time', '未知'),
                        'is_admin': nickname in self.admins,
                        'is_muted': nickname in self.muted_users
                    })
                
                banned_ips = list(self.banned_ips)
                
                muted_users = []
                current_time = time.time()
                for nickname, (mute_time, duration) in self.muted_users.items():
                    remaining_seconds = int(duration * 60 - (current_time - mute_time))
                    if remaining_seconds > 0:
                        remaining_minutes = remaining_seconds // 60
                        remaining_seconds = remaining_seconds % 60
                        muted_users.append({
                            'nickname': nickname,
                            'duration': duration,
                            'remaining_time': f"{remaining_minutes}分{remaining_seconds}秒"
                        })
            
            return jsonify({
                'success': True,
                'online_users': len(self.client_sockets),
                'admin_count': len(self.admins),
                'uptime': self._get_running_time(),
                'users': users,
                'banned_ips': banned_ips,
                'muted_users': muted_users
            })
        
        @self.app.route('/api/action', methods=['POST'])
        def api_action():
            """执行用户操作API"""
            data = request.get_json()
            action = data.get('action')
            username = data.get('username')
            
            if not action or not username:
                return jsonify({'success': False, 'message': '参数错误'})
            
            try:
                if action == 'kick':
                    self.kick_user(username)
                    return jsonify({'success': True, 'message': f'已踢出用户 {username}'})
                
                elif action == 'ban':
                    target_ip = None
                    with self.lock:
                        for sock, n in self.client_nicknames.items():
                            if n == username:
                                if sock in self.client_profiles:
                                    target_ip = self.client_profiles[sock]['ip_address']
                                break
                    
                    if target_ip:
                        with self.lock:
                            self.banned_ips.add(target_ip)
                        self.kick_user(username)
                        self.broadcast_message(f"系统: 用户 {username} 的IP {target_ip} 已被管理员封禁")
                        return jsonify({'success': True, 'message': f'已封禁IP {target_ip}（用户：{username}）'})
                    else:
                        return jsonify({'success': False, 'message': '找不到用户或其IP地址'})
                
                elif action == 'op':
                    target_socket = None
                    with self.lock:
                        for sock, n in self.client_nicknames.items():
                            if n == username:
                                target_socket = sock
                                break
                        self.admins.add(username)
                    
                    broadcast_msg = f"系统: {username} 已成为管理员"
                    self.broadcast_message(broadcast_msg)
                    if target_socket:
                        try:
                            target_socket.send(f"OP:{broadcast_msg}".encode('utf-8'))
                        except:
                            pass
                    self.broadcast_user_list()
                    return jsonify({'success': True, 'message': f'已将 {username} 设为管理员'})
                
                elif action == 'unop':
                    is_admin = False
                    target_socket = None
                    with self.lock:
                        for sock, n in self.client_nicknames.items():
                            if n == username:
                                target_socket = sock
                                break
                        if username in self.admins:
                            self.admins.remove(username)
                            is_admin = True
                    
                    if is_admin:
                        broadcast_msg = f"系统: {username} 已被撤销管理员权限"
                        self.broadcast_message(broadcast_msg)
                        if target_socket:
                            try:
                                target_socket.send(f"UNOP:{broadcast_msg}".encode('utf-8'))
                            except:
                                pass
                        self.broadcast_user_list()
                        return jsonify({'success': True, 'message': f'已撤销 {username} 的管理员权限'})
                    else:
                        return jsonify({'success': False, 'message': '该用户不是管理员'})
                
                elif action == 'mute':
                    duration = data.get('duration', 10)
                    target_socket = None
                    with self.lock:
                        for sock, n in self.client_nicknames.items():
                            if n == username:
                                target_socket = sock
                                break
                        self.muted_users[username] = (time.time(), duration)
                    
                    broadcast_msg = f"系统: {username} 已被管理员禁言 {duration} 分钟"
                    self.broadcast_message(broadcast_msg)
                    if target_socket:
                        try:
                            target_socket.send(f"MUTED:{broadcast_msg}".encode('utf-8'))
                        except:
                            pass
                    return jsonify({'success': True, 'message': f'已禁言 {username} {duration} 分钟'})
                
                else:
                    return jsonify({'success': False, 'message': '不支持的操作'})
            
            except Exception as e:
                return jsonify({'success': False, 'message': f'操作失败: {str(e)}'})
        
        @self.app.route('/api/unban', methods=['POST'])
        def api_unban():
            """解封IP API"""
            data = request.get_json()
            ip = data.get('ip')
            
            if not ip:
                return jsonify({'success': False, 'message': '参数错误'})
            
            is_banned = False
            with self.lock:
                if ip in self.banned_ips:
                    self.banned_ips.remove(ip)
                    is_banned = True
            
            if is_banned:
                self.broadcast_message(f"系统: IP {ip} 已被管理员解除封禁")
                return jsonify({'success': True, 'message': f'已解除IP {ip} 的封禁'})
            else:
                return jsonify({'success': False, 'message': '该IP未被封禁'})
        
        @self.app.route('/api/unmute', methods=['POST'])
        def api_unmute():
            """解除禁言API"""
            data = request.get_json()
            username = data.get('username')
            
            if not username:
                return jsonify({'success': False, 'message': '参数错误'})
            
            target_socket = None
            is_muted = False
            
            with self.lock:
                for sock, n in self.client_nicknames.items():
                    if n == username:
                        target_socket = sock
                        break
                if username in self.muted_users:
                    del self.muted_users[username]
                    is_muted = True
            
            if is_muted:
                broadcast_msg = f"系统: {username} 已被管理员解除禁言"
                self.broadcast_message(broadcast_msg)
                if target_socket:
                    try:
                        target_socket.send(f"UNMUTED:{broadcast_msg}".encode('utf-8'))
                    except:
                        pass
                return jsonify({'success': True, 'message': f'已解除 {username} 的禁言'})
            else:
                return jsonify({'success': False, 'message': '该用户未被禁言'})
        
        @self.app.route('/api/kickall', methods=['POST'])
        def api_kickall():
            """踢出所有用户API"""
            with self.lock:
                users_to_kick = list(self.client_nicknames.values())
            
            for username in users_to_kick:
                self.kick_user(username)
            
            return jsonify({'success': True, 'message': f'已踢出所有用户（共{len(users_to_kick)}人）'})
        
        @self.app.route('/api/stop', methods=['POST'])
        def api_stop():
            """停止服务器API"""
            self.running = False
            return jsonify({'success': True, 'message': '服务器正在关闭'})
        
        @self.app.route('/api/config', methods=['POST'])
        def api_config():
            """保存配置API"""
            try:
                data = request.get_json()
                config_file = "LittleChat.serverset"
                
                # 读取现有配置
                config = load_config()
                
                # 更新配置
                config['server_port'] = str(data.get('server_port', config['server_port']))
                config['max_user'] = str(data.get('max_user', config['max_user']))
                config['message_size_limit'] = str(data.get('message_size_limit', config['message_size_limit']))
                config['admin_prefix'] = str(data.get('admin_prefix', config['admin_prefix']))
                
                # 保存配置文件
                with open(config_file, "w", encoding="utf-8") as f:
                    f.write("# LittleChat服务器配置文件\n")
                    f.write("# 编辑此文件修改服务器设置\n")
                    f.write("# 支持完整注释行和行末注释\n\n")
                    
                    for key, value in config.items():
                        if key == "server_port":
                            f.write(f"{key}={value}\n\n")
                        elif key == "max_user":
                            f.write(f"{key}={value}\n\n")
                        elif key == "message_size_limit":
                            f.write(f"{key}={value}\n\n")
                        elif key == "admin_prefix":
                            f.write(f"{key}={value}\n\n")
                        else:
                            f.write(f"{key}={value}\n\n")
                
                return jsonify({'success': True, 'message': '配置保存成功'})
            
            except Exception as e:
                return jsonify({'success': False, 'message': f'保存失败: {str(e)}'})
    
    def run_web_server(self):
        """在独立线程中运行Flask Web服务器"""
        try:
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [Web] Web管理界面启动中...")
            self.app.run(host='0.0.0.0', port=self.web_port, debug=False, use_reloader=False)
        except Exception as e:
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [错误] Web服务器启动失败: {str(e)}")
    
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
                                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [成功] 管理员 {nickname} 已将 {target_nickname} 设为管理员")
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
                                        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [成功] 管理员 {nickname} 已撤销 {target_nickname} 的管理员权限")
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
                                        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [成功] 管理员 {nickname} 已封禁IP {target_ip}（用户：{target_nickname}）")
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
                                            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [成功] 管理员 {nickname} 已解除IP {target_ip} 的封禁")
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
                                                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [成功] 管理员 {nickname} 已禁言 {actual_target} {duration} 分钟")
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
                                            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [成功] 管理员 {nickname} 已解除 {target_nickname} 的禁言")
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
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [成功] 已踢出用户: {target_nickname}")
                # 广播踢出消息
                self.broadcast_message(f"系统: {target_nickname} 已被管理员踢出聊天室")
            except Exception as e:
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [错误] 踢出用户 {target_nickname} 时发生错误: {str(e)}")
        else:
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [错误] 用户 {target_nickname} 不存在或已离线")
    
    def start(self):
        """启动服务器"""
        print("=" * 60)
        print("" * 20 + "聊天服务器启动中...")
        print("=" * 60)
        
        # 检查更新
        check_for_updates()
        
        # 启动 Web 服务器
        if self.web_enabled:
            web_thread = threading.Thread(target=self.run_web_server)
            web_thread.daemon = True
            web_thread.start()
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [Web] Web管理界面启动中...")
        
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
                    if self.web_enabled:
                        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [Web] Web管理界面: http://localhost:{self.web_port}")
                    print("=" * 60)
                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 等待客户端连接...")
                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 提示: 输入 'quit'、'exit' 或 'stop' 可关闭服务器")
                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 提示: 服务端目录下的LittleChat.serverset文件是服务器配置文件，试试改一改它吧！")
                    if self.web_enabled:
                        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 提示: 访问 http://localhost:{self.web_port} 使用Web管理界面")
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
                                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [警告] 收到退出命令，正在关闭服务器...")
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
                                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [信息] 服务器版本: v{CURRENT_VERSION}")
                                print("-" * 60)
                            elif command == 'status':
                                print("-" * 60)
                                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [信息] 服务器状态: {'运行中' if self.running else '已关闭'}")
                                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [信息] 监听端口: {self.port}")
                                with self.lock:
                                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [信息] 在线客户端: {len(self.client_sockets)}")
                                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [信息] 运行时长: {self._get_running_time()}")
                                if self.web_enabled:
                                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [Web] Web管理界面: http://localhost:{self.web_port}")
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
                                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [成功] 已将 {target_nickname} 设置为管理员")
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
                                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [错误] 命令格式错误: op <用户名>")
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
                                        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [成功] 已撤销 {target_nickname} 的管理员权限")
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
                                        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [错误] {target_nickname} 不是管理员")
                                else:
                                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [错误] 命令格式错误: unop <用户名>")
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
                                        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [成功] 已封禁IP {target_ip}（用户：{target_nickname}）")
                                        # 踢出该用户（如果在线）
                                        self.kick_user(target_nickname)
                                        # 通知所有用户
                                        self.broadcast_message(f"系统: 用户 {target_nickname} 的IP {target_ip} 已被封禁")
                                    else:
                                        # 用户不在线或找不到IP
                                        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [错误] 找不到用户 {target_nickname} 或其IP地址")
                                else:
                                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [错误] 命令格式错误: ban <用户名>")
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
                                                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [成功] 已解除IP {target_ip} 的封禁")
                                                # 通知所有用户
                                                if target_user != target_ip:
                                                    self.broadcast_message(f"系统: 用户 {target_user} 的IP {target_ip} 已被管理员解除封禁")
                                                else:
                                                    self.broadcast_message(f"系统: IP {target_ip} 已被管理员解除封禁")
                                            else:
                                                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [错误] IP {target_ip} 未被封禁")
                                    else:
                                        # 无法找到目标IP
                                        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [错误] 找不到目标 {target} 或其IP地址")
                                else:
                                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [错误] 命令格式错误: unban <用户名或IP>")
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
                                            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [成功] 已禁言 {target_nickname} {duration} 分钟")
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
                                            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [错误] 禁言时长必须大于0")
                                    except ValueError:
                                        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [错误] 命令格式错误: shutup <用户名> <时间（分钟）>")
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
                                            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [成功] 已解除 {target_nickname} 的禁言")
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
                                            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [错误] {target_nickname} 未被禁言")
                                else:
                                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [错误] 命令格式错误: unshutup <用户名>")
                            elif command.startswith('kick '):
                                # 处理kick命令
                                parts = command.split(' ', 1)
                                if len(parts) == 2:
                                    target_nickname = parts[1].strip()
                                    self.kick_user(target_nickname)
                                else:
                                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [错误] 命令格式错误: kick <用户名>")
                            elif command:
                                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [错误] 未知命令: {command}")
                                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [提示] 输入 'help' 查看可用命令")
                        except EOFError:
                            # 处理Ctrl+D输入
                            print("\n" + "=" * 60)
                            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [警告] 收到EOF信号，正在关闭服务器...")
                            self.running = False
                            break
                        except KeyboardInterrupt:
                            # 处理Ctrl+C输入
                            print("\n" + "=" * 60)
                            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ⚠️  收到中断信号，正在关闭服务器...")
                            self.running = False
                            break
                        except Exception as e:
                            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [错误] 命令处理错误: {str(e)}")
                
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
                        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [警告] 收到中断信号，正在关闭服务器...")
                        self.running = False
                        break
                    except Exception as e:
                        if not self.running:
                            break
                        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [错误] 接受客户端连接时发生错误: {str(e)}")
                        if not self.running:
                            break
        except Exception as e:
            print("=" * 60)
            print("" * 20 + "[错误] 服务器启动失败")
            print("=" * 60)
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [错误] 错误原因: {str(e)}")
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [提示] 建议: 检查端口是否被占用或权限是否足够")
            self.running = False
        finally:
            self.stop()
    
    def stop(self):
        """停止服务器"""
        if not self.running:
            return
        
        print("-" * 60)
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [信息] 正在关闭服务器...")
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
        print("" * 20 + "[成功] 服务器已关闭")
        print("=" * 60)
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [信息] 服务器状态: 已关闭")
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [信息] 已断开客户端数: {client_count}")
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [信息] 运行时长: {self._get_running_time()}")
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