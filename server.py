import socket
import threading
import time

class ChatServer:
    def __init__(self, port=7891):
        self.port = port
        self.server_socket = None
        self.client_sockets = []
        self.client_nicknames = {}
        self.client_profiles = {}
        self.admins = set()  # 管理员列表
        self.banned_users = set()  # 封禁的用户名列表
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
            
            # 检查用户是否被封禁
            with self.lock:
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
                message = client_socket.recv(1024).decode('utf-8')
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
                                    with self.lock:
                                        self.banned_users.add(target_nickname)
                                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ✅ 管理员 {nickname} 已封禁 {target_nickname}")
                                    # 踢出该用户（如果在线）
                                    self.kick_user(target_nickname)
                                    # 通知所有用户
                                    self.broadcast_message(f"系统: {target_nickname} 已被管理员封禁")
                                else:
                                    # 发送错误消息给管理员
                                    error_message = "ERROR:您不能封禁自己"
                                    client_socket.send(error_message.encode('utf-8'))
                                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 管理员 {nickname} 尝试封禁自己")
                            elif admin_command == 'unban':
                                with self.lock:
                                    if target_nickname in self.banned_users:
                                        self.banned_users.remove(target_nickname)
                                        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ✅ 管理员 {nickname} 已解除 {target_nickname} 的封禁")
                                        # 通知所有用户
                                        self.broadcast_message(f"系统: {target_nickname} 已被管理员解除封禁")
                                    else:
                                        error_message = "ERROR:该用户未被封禁"
                                        client_socket.send(error_message.encode('utf-8'))
                                        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 管理员 {nickname} 尝试解除未封禁用户 {target_nickname} 的封禁")
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
            # 获取当前在线用户昵称列表
            users = list(self.client_nicknames.values())
        
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
        try:
            bind_attempts = 0
            max_attempts = 5
            bind_success = False
            
            while bind_attempts < max_attempts and not bind_success:
                try:
                    # 创建套接字
                    self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    
                    # 关键：确保在bind之前设置SO_REUSEADDR选项
                    # 对于Windows，这个选项必须在bind之前设置才有效
                    # 特别是打包为exe后，这个设置至关重要
                    self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 已设置 SO_REUSEADDR 选项，允许端口复用")
                    
                    bind_attempts += 1
                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 尝试绑定到端口 {self.port}... (尝试 {bind_attempts}/{max_attempts})")
                    
                    # 绑定地址和端口
                    self.server_socket.bind(('0.0.0.0', self.port))
                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 成功绑定到端口 {self.port}")
                    
                    # 开始监听连接
                    self.server_socket.listen(5)
                    self.running = True
                    self.start_time = time.time()  # 记录服务器启动时间
                    
                    # 服务器启动成功提示
                    print("=" * 60)
                    print("" * 20 + "聊天服务器启动成功  作者：MVP请勿做商业用途或非法活动")
                    print("=" * 60)
                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 服务器状态: 运行中")
                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 监听地址: 0.0.0.0")
                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 监听端口: {self.port}")
                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 服务器IP: {socket.gethostbyname(socket.gethostname())}")
                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 最大连接数: 5")
                    print("=" * 60)
                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 等待客户端连接...")
                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 提示: 输入 'quit'、'exit' 或 'stop' 可关闭服务器")
                    print("-" * 60)
                    
                    bind_success = True
                except OSError as e:
                    if hasattr(e, 'winerror') and e.winerror == 10048:
                        # Windows特定错误：地址已被占用
                        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 警告: 端口 {self.port} 被占用 - {e.strerror}")
                        if bind_attempts < max_attempts:
                            # 等待一段时间后重试
                            wait_time = 1  # 秒
                            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 等待 {wait_time} 秒后重试...")
                            time.sleep(wait_time)
                            # 关闭当前套接字，准备下一次尝试
                            try:
                                self.server_socket.close()
                            except:
                                pass
                        else:
                            # 达到最大尝试次数，抛出异常
                            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 错误: 经过 {max_attempts} 次尝试后仍无法绑定到端口 {self.port}")
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
                            command = input().strip().lower()
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
                                print("  op <用户名>       - 将指定用户设置为管理员")
                                print("  unop <用户名>     - 撤销指定用户的管理员权限")
                                print("  kick <用户名>     - 踢出指定用户")
                                print("  ban <用户名>      - 封禁指定用户")
                                print("  unban <用户名>    - 解除指定用户的封禁")
                                print("  shutup <用户名> <时间> - 禁言指定时长（分钟）")
                                print("  unshutup <用户名> - 解除指定用户的禁言")
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
                                    else:
                                        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ❌ {target_nickname} 不是管理员")
                                else:
                                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ❌ 命令格式错误: unop <用户名>")
                            elif command.startswith('ban '):
                                # 处理ban命令
                                parts = command.split(' ', 1)
                                if len(parts) == 2:
                                    target_nickname = parts[1].strip()
                                    with self.lock:
                                        self.banned_users.add(target_nickname)
                                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ✅ 已封禁 {target_nickname}")
                                    # 踢出该用户（如果在线）
                                    self.kick_user(target_nickname)
                                    # 通知所有用户
                                    self.broadcast_message(f"系统: {target_nickname} 已被封禁")
                                else:
                                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ❌ 命令格式错误: ban <用户名>")
                            elif command.startswith('unban '):
                                # 处理unban命令
                                parts = command.split(' ', 1)
                                if len(parts) == 2:
                                    target_nickname = parts[1].strip()
                                    with self.lock:
                                        if target_nickname in self.banned_users:
                                            self.banned_users.remove(target_nickname)
                                            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ✅ 已解除 {target_nickname} 的封禁")
                                            # 通知所有用户
                                            self.broadcast_message(f"系统: {target_nickname} 已被解除封禁")
                                        else:
                                            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ❌ {target_nickname} 未被封禁")
                                else:
                                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ❌ 命令格式错误: unban <用户名>")
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
                        self.server_socket.settimeout(1)  # 1秒超时
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
    server = ChatServer(port=7891)
    server.start()


if __name__ == "__main__":
    try:
        start_server()
    except KeyboardInterrupt:
        print("\n服务器已被用户中断")
    except Exception as e:
        print(f"服务器发生未处理的异常: {str(e)}")