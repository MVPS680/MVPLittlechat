import socket
import threading
import time

class ChatServer:
    def __init__(self, port=7891):
        self.port = port
        self.server_socket = None
        self.client_sockets = []
        self.client_nicknames = {}
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
            
            # 线程安全地添加客户端
            with self.lock:
                self.client_sockets.append(client_socket)
                self.client_nicknames[client_socket] = nickname
            
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 客户端 {client_address} 已连接，昵称为: {nickname}")
            
            # 广播新用户加入消息
            self.broadcast_message(f"系统: {nickname} 加入了聊天室", exclude_socket=client_socket)
            
            # 处理客户端消息
            while True:
                message = client_socket.recv(1024).decode('utf-8')
                if not message:
                    break
                
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
            
            # 关闭客户端连接
            try:
                client_socket.close()
            except:
                pass
            
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 客户端 {client_address} 已断开连接")
            # 广播用户离开消息
            self.broadcast_message(f"系统: {nickname} 离开了聊天室")
    
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
    
    def start(self):
        """启动服务器"""
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
                    print("" * 20 + "聊天服务器启动成功")
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
                                print("-" * 60)
                            elif command == 'status':
                                print("-" * 60)
                                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 🔍 服务器状态: {'运行中' if self.running else '已关闭'}")
                                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 🚪 监听端口: {self.port}")
                                with self.lock:
                                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 👥 在线客户端: {len(self.client_sockets)}")
                                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 🕒 运行时长: {self._get_running_time()}")
                                print("-" * 60)
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