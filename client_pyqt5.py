import sys
import socket
import threading
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QFrame, QListWidget,
    QListWidgetItem, QMenu, QAction, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QObject
from PyQt5.QtGui import QFont, QColor, QTextCharFormat, QTextCursor

class Communicate(QObject):
    message_received = pyqtSignal(str)
    user_list_updated = pyqtSignal(list)
    profile_received = pyqtSignal(str, str, str, str)
    error_message = pyqtSignal(str)

class ChatClient(QMainWindow):
    def __init__(self):
        super().__init__()
        self.comm = Communicate()
        self.client_socket = None
        self.nickname = ""
        self.connected = False
        self.online_users = []
        self.initUI()
        self.setup_signals()

    def initUI(self):
        self.setWindowTitle("LittleChat -MVP")
        self.setGeometry(100, 100, 800, 600)
        self.setMinimumSize(600, 400)

        # 主窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # 连接界面
        self.connect_frame = QFrame()
        connect_layout = QVBoxLayout(self.connect_frame)
        connect_layout.setAlignment(Qt.AlignCenter)

        title_label = QLabel("连接到聊天服务器")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        connect_layout.addWidget(title_label)

        # IP地址输入
        ip_layout = QHBoxLayout()
        ip_label = QLabel("服务器IP地址:")
        self.ip_entry = QLineEdit()
        self.ip_entry.setText("127.0.0.1")
        self.ip_entry.setFixedWidth(200)
        ip_layout.addWidget(ip_label)
        ip_layout.addWidget(self.ip_entry)
        connect_layout.addLayout(ip_layout)

        # 端口输入
        port_layout = QHBoxLayout()
        port_label = QLabel("服务器端口:")
        self.port_entry = QLineEdit()
        self.port_entry.setText("7891")
        self.port_entry.setFixedWidth(200)
        port_layout.addWidget(port_label)
        port_layout.addWidget(self.port_entry)
        connect_layout.addLayout(port_layout)

        # 昵称输入
        nick_layout = QHBoxLayout()
        nick_label = QLabel("您的昵称:")
        self.nick_entry = QLineEdit()
        self.nick_entry.setFixedWidth(200)
        nick_layout.addWidget(nick_label)
        nick_layout.addWidget(self.nick_entry)
        connect_layout.addLayout(nick_layout)

        # 连接按钮
        self.connect_button = QPushButton("连接服务器")
        self.connect_button.setFixedWidth(150)
        self.connect_button.clicked.connect(self.connect_to_server)
        connect_layout.addWidget(self.connect_button)

        # 状态标签
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: red;")
        connect_layout.addWidget(self.status_label)

        # 聊天界面
        self.chat_frame = QFrame()
        chat_layout = QHBoxLayout(self.chat_frame)

        # 左侧聊天区域
        left_layout = QVBoxLayout()

        # 聊天记录
        self.chat_text = QTextEdit()
        self.chat_text.setReadOnly(True)
        self.chat_text.setFont(QFont("SimSun", 10))
        left_layout.addWidget(self.chat_text)

        # 消息输入区域
        input_layout = QHBoxLayout()
        self.message_entry = QLineEdit()
        self.message_entry.setPlaceholderText("输入消息... (按Enter发送, @用户名可以@指定用户)")
        self.message_entry.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.message_entry)

        self.send_button = QPushButton("发送")
        self.send_button.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_button)

        left_layout.addLayout(input_layout)

        # 右侧用户列表
        right_layout = QVBoxLayout()
        users_label = QLabel("在线用户")
        users_label.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(users_label)

        self.users_list = QListWidget()
        self.users_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.users_list.customContextMenuRequested.connect(self.show_context_menu)
        self.users_list.doubleClicked.connect(self.add_mention)
        right_layout.addWidget(self.users_list)

        # 添加分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)

        # 组装聊天界面
        chat_layout.addLayout(left_layout, 3)
        chat_layout.addWidget(separator)
        chat_layout.addLayout(right_layout, 1)

        # 初始显示连接界面
        main_layout.addWidget(self.connect_frame)
        # 确保聊天界面初始是隐藏的，并且没有被添加到布局中
        self.chat_frame.hide()

    def setup_signals(self):
        self.comm.message_received.connect(self.display_message)
        self.comm.user_list_updated.connect(self.update_user_list)
        self.comm.profile_received.connect(self.show_user_profile)
        self.comm.error_message.connect(self.show_error_message)

    def connect_to_server(self):
        ip = self.ip_entry.text().strip()
        port = self.port_entry.text().strip()
        nickname = self.nick_entry.text().strip()

        if not ip or not port or not nickname:
            self.status_label.setText("所有字段都必须填写!")
            return

        try:
            port = int(port)
            if port < 1 or port > 65535:
                raise ValueError
        except ValueError:
            self.status_label.setText("端口号必须是1-65535之间的整数!")
            return

        self.nickname = nickname

        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((ip, port))
            # 只发送昵称
            self.client_socket.send(nickname.encode('utf-8'))
            
            # 接收服务器的响应
            response = self.client_socket.recv(1024).decode('utf-8')
            
            if response.startswith("ERROR:"):
                # 昵称冲突或其他错误
                self.status_label.setText(response[6:])
                self.client_socket.close()
                return
            elif response.startswith("SUCCESS:"):
                # 连接成功
                self.connected = True

                # 切换到聊天界面
                main_layout = self.centralWidget().layout()
                # 移除连接界面
                main_layout.removeWidget(self.connect_frame)
                self.connect_frame.hide()
                # 添加聊天界面
                main_layout.addWidget(self.chat_frame)
                self.chat_frame.show()
                # 设置窗口标题
                self.setWindowTitle(f"LittleChat-MVP 当前用户：{self.nickname}")
                self.message_entry.setFocus()

                # 启动接收消息线程
                receive_thread = threading.Thread(target=self.receive_messages, daemon=True)
                receive_thread.start()

        except ConnectionRefusedError:
            self.status_label.setText("无法连接到服务器：服务器未启动")
        except socket.gaierror:
            self.status_label.setText("无效的IP地址")
        except Exception as e:
            self.status_label.setText(f"连接失败：{str(e)}")
        finally:
            if not self.connected and self.client_socket:
                self.client_socket.close()

    def receive_messages(self):
        while self.connected:
            try:
                message = self.client_socket.recv(1024).decode('utf-8')
                if not message:
                    break
                
                # 检查是否是用户列表更新消息
                if message.startswith("USERS_LIST:"):
                    # 解析用户列表
                    users_part = message.split(":", 1)[1]
                    users = users_part.split(",") if users_part else []
                    self.comm.user_list_updated.emit(users)
                elif message.startswith("PROFILE:"):
                    # 处理用户profile响应
                    profile_part = message.split(":", 1)[1]
                    profile_data = profile_part.split("|")
                    if len(profile_data) == 4:
                        nickname, ip_address, join_time, os_version = profile_data
                        # 使用信号来触发GUI操作，确保在主线程中执行
                        self.comm.profile_received.emit(nickname, ip_address, join_time, os_version)
                elif message.startswith("PROFILE_ERROR:"):
                    # 处理profile错误
                    error_message = message.split(":", 1)[1]
                    # 使用信号来触发GUI操作，确保在主线程中执行
                    self.comm.error_message.emit(error_message)
                elif message.startswith("KICKED:"):
                    # 处理被踢出消息
                    kick_message = message.split(":", 1)[1]
                    # 使用信号来触发GUI操作，确保在主线程中执行
                    self.comm.error_message.emit(kick_message)
                    # 关闭连接
                    self.connected = False
                    self.client_socket.close()
                    # 切换回连接界面
                    self.chat_frame.hide()
                    self.connect_frame.show()
                else:
                    # 普通消息，显示在聊天记录中
                    self.comm.message_received.emit(message)
            except ConnectionResetError:
                self.comm.message_received.emit("系统: 与服务器断开连接")
                self.connected = False
                break
            except Exception as e:
                self.comm.message_received.emit(f"系统: 接收错误 - {str(e)}")
                break

    def display_message(self, message):
        self.chat_text.append(message)
        # 检查是否有@自己的消息
        if f"@{self.nickname}" in message:
            self.highlight_mention(message)
            # 只在收到其他用户的消息且@自己时弹出弹窗，自己发送的消息不弹出
            if not message.startswith("我:"):
                # 提取发送者昵称
                if ":" in message:
                    sender = message.split(":", 1)[0]
                    # 弹出通知弹窗
                    QMessageBox.information(self, "@提及通知", f"{sender} 在聊天中提到了你")

    def highlight_mention(self, message):
        # 高亮显示@自己的消息
        cursor = self.chat_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.movePosition(QTextCursor.StartOfLine, QTextCursor.KeepAnchor)
        cursor.movePosition(QTextCursor.End, QTextCursor.KeepAnchor)
        format = QTextCharFormat()
        format.setBackground(QColor(255, 255, 150))
        cursor.setCharFormat(format)

    def send_message(self):
        message = self.message_entry.text().strip()
        if not message or not self.connected:
            return

        try:
            # 检查是否是管理员命令
            if message.startswith('/'):
                # 提取命令和参数
                parts = message[1:].split(' ', 1)
                command = parts[0].lower()
                
                # 管理员命令处理
                if command == 'kick':
                    if len(parts) == 2:
                        target_nickname = parts[1].strip()
                        # 防止管理员自己踢自己
                        if target_nickname != self.nickname:
                            # 发送命令给服务器
                            admin_command = f"ADMIN_COMMAND:{command}:{target_nickname}"
                            self.client_socket.send(admin_command.encode('utf-8'))
                            self.chat_text.append(f"我: {message}")
                            self.message_entry.clear()
                        else:
                            self.chat_text.append("系统: 您不能对自己执行此操作")
                            self.message_entry.clear()
                    else:
                        self.chat_text.append("系统: 命令格式错误: /kick <用户名>")
                        self.message_entry.clear()
                elif command == 'unop':
                    if len(parts) == 2:
                        target_nickname = parts[1].strip()
                        # 防止管理员自己撤销自己的权限
                        if target_nickname != self.nickname:
                            # 发送命令给服务器
                            admin_command = f"ADMIN_COMMAND:{command}:{target_nickname}"
                            self.client_socket.send(admin_command.encode('utf-8'))
                            self.chat_text.append(f"我: {message}")
                            self.message_entry.clear()
                        else:
                            self.chat_text.append("系统: 您不能撤销自己的管理员权限")
                            self.message_entry.clear()
                    else:
                        self.chat_text.append("系统: 命令格式错误: /unop <用户名>")
                        self.message_entry.clear()
                elif command == 'ban':
                    if len(parts) == 2:
                        target_nickname = parts[1].strip()
                        # 防止管理员自己封禁自己
                        if target_nickname != self.nickname:
                            # 发送命令给服务器
                            admin_command = f"ADMIN_COMMAND:{command}:{target_nickname}"
                            self.client_socket.send(admin_command.encode('utf-8'))
                            self.chat_text.append(f"我: {message}")
                            self.message_entry.clear()
                        else:
                            self.chat_text.append("系统: 您不能封禁自己")
                            self.message_entry.clear()
                    else:
                        self.chat_text.append("系统: 命令格式错误: /ban <用户名>")
                        self.message_entry.clear()
                elif command == 'unban':
                    if len(parts) == 2:
                        target_nickname = parts[1].strip()
                        # 发送命令给服务器
                        admin_command = f"ADMIN_COMMAND:{command}:{target_nickname}"
                        self.client_socket.send(admin_command.encode('utf-8'))
                        self.chat_text.append(f"我: {message}")
                        self.message_entry.clear()
                    else:
                        self.chat_text.append("系统: 命令格式错误: /unban <用户名>")
                        self.message_entry.clear()
                elif command == 'shutup':
                    if len(parts) == 2:
                        # 提取目标用户和禁言时长
                        target_parts = parts[1].split(' ', 1)
                        if len(target_parts) == 2:
                            target_nickname = target_parts[0].strip()
                            duration = target_parts[1].strip()
                            # 防止管理员自己禁言自己
                            if target_nickname != self.nickname:
                                # 发送命令给服务器
                                admin_command = f"ADMIN_COMMAND:{command}:{target_nickname} {duration}"
                                self.client_socket.send(admin_command.encode('utf-8'))
                                self.chat_text.append(f"我: {message}")
                                self.message_entry.clear()
                            else:
                                self.chat_text.append("系统: 您不能禁言自己")
                                self.message_entry.clear()
                        else:
                            self.chat_text.append("系统: 命令格式错误: /shutup <用户名> <时间（分钟）>")
                            self.message_entry.clear()
                    else:
                        self.chat_text.append("系统: 命令格式错误: /shutup <用户名> <时间（分钟）>")
                        self.message_entry.clear()
                elif command == 'unshutup':
                    if len(parts) == 2:
                        target_nickname = parts[1].strip()
                        # 防止管理员自己解除自己的禁言
                        if target_nickname != self.nickname:
                            # 发送命令给服务器
                            admin_command = f"ADMIN_COMMAND:{command}:{target_nickname}"
                            self.client_socket.send(admin_command.encode('utf-8'))
                            self.chat_text.append(f"我: {message}")
                            self.message_entry.clear()
                        else:
                            self.chat_text.append("系统: 您不能解除自己的禁言")
                            self.message_entry.clear()
                    else:
                        self.chat_text.append("系统: 命令格式错误: /unshutup <用户名>")
                        self.message_entry.clear()
                else:
                    # 不支持的命令
                    self.chat_text.append(f"系统: 不支持的命令: {command}")
                    self.message_entry.clear()
            else:
                # 普通消息
                self.client_socket.send(message.encode('utf-8'))
                # 在聊天记录中显示自己发送的消息
                self.chat_text.append(f"我: {message}")
                self.message_entry.clear()
        except Exception as e:
            self.chat_text.append(f"系统: 发送失败 - {str(e)}")

    def show_context_menu(self, pos):
        # 获取右键点击的项目
        item = self.users_list.itemAt(pos)
        if item:
            # 选中右键点击的项目
            self.users_list.setCurrentItem(item)
        
        # 显示右键菜单
        menu = QMenu(self)
        mention_action = QAction("@提及", self)
        mention_action.triggered.connect(self.add_mention)
        menu.addAction(mention_action)
        
        # 添加查看资料选项
        profile_action = QAction("查看资料", self)
        profile_action.triggered.connect(self.request_user_profile)
        menu.addAction(profile_action)
        
        # 执行菜单
        menu.exec_(self.users_list.mapToGlobal(pos))

    def add_mention(self):
        # 在输入框中添加@用户名
        selected_items = self.users_list.selectedItems()
        if selected_items:
            user = selected_items[0].text()
            current_text = self.message_entry.text()
            if current_text:
                self.message_entry.setText(f"{current_text} @{user} ")
            else:
                self.message_entry.setText(f"@{user} ")
            self.message_entry.setFocus()

    def request_user_profile(self):
        # 请求选中用户的profile
        print("request_user_profile called")
        selected_items = self.users_list.selectedItems()
        print(f"selected_items: {selected_items}")
        print(f"connected: {self.connected}")
        if selected_items and self.connected:
            user = selected_items[0].text()
            print(f"requesting profile for: {user}")
            # 发送profile请求给服务器
            request_message = f"PROFILE_REQUEST:{user}"
            self.client_socket.send(request_message.encode('utf-8'))
            print(f"sent profile request: {request_message}")
        else:
            print("not requesting profile: no selection or not connected")

    def show_user_profile(self, nickname, ip_address, join_time, os_version):
        # 显示用户profile信息
        profile_text = f"用户资料\n\n昵称: {nickname}\nIP地址: {ip_address}\n加入时间: {join_time}\n操作系统: {os_version}"
        QMessageBox.information(self, f"{nickname} 的资料", profile_text)

    def show_error_message(self, error_text):
        # 显示错误消息
        QMessageBox.warning(self, "错误", error_text)

    def update_user_list(self, users):
        # 更新在线用户列表
        self.users_list.clear()
        for user in users:
            item = QListWidgetItem(user)
            self.users_list.addItem(item)

    def closeEvent(self, event):
        # 关闭窗口时断开连接
        if self.connected:
            self.connected = False
            try:
                self.client_socket.close()
            except:
                pass
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ChatClient()
    window.show()
    sys.exit(app.exec_())