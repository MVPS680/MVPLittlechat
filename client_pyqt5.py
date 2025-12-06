import sys
import socket
import threading
import time
import requests
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QFrame, QListWidget,
    QListWidgetItem, QMenu, QAction, QMessageBox, QProgressDialog
)
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QThread, pyqtSlot
from PyQt5.QtGui import QFont, QColor, QTextCharFormat, QTextCursor

# 应用版本信息
<<<<<<< HEAD
CURRENT_VERSION = "2.3.0"
=======
CURRENT_VERSION = "2.2.1"
>>>>>>> 2d24d323418f153d54fa4847084755382db36c5c
# Gitee仓库信息
GITEE_OWNER = "MVPS680"
GITEE_REPO = "MVPLittlechat"
GITEE_TOKEN = "f19052b74c6322d54137ff8caa114093"

class Communicate(QObject):
    message_received = pyqtSignal(str)
    user_list_updated = pyqtSignal(list)
    profile_received = pyqtSignal(str, str, str, str)
    error_message = pyqtSignal(str)
    notification = pyqtSignal(str, str, str)  # 用于发送通知弹窗，参数：标题、内容、类型
    show_reconnect_dialog_signal = pyqtSignal()  # 用于触发重连对话框的显示

class ChatClient(QMainWindow):
    def __init__(self):
        super().__init__()
        self.comm = Communicate()
        self.client_socket = None
        self.nickname = ""
        self.connected = False
        self.online_users = []
        self.is_muted = False  # 跟踪用户是否被禁言
        self.showing_reconnect_dialog = False  # 跟踪是否已经显示了重连对话框
        self.initUI()
        self.setup_signals()
        # 启动时自动检查更新
        self.check_for_updates()

    def initUI(self):
        self.setWindowTitle(f"LittleChat v{CURRENT_VERSION} -MVP")
<<<<<<< HEAD
        # 放大窗口大小1.5倍
        self.setGeometry(100, 100, 1200, 900)
        self.setMinimumSize(900, 600)
=======
        self.setGeometry(100, 100, 800, 600)
        self.setMinimumSize(600, 400)
>>>>>>> 2d24d323418f153d54fa4847084755382db36c5c

        # 主窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # 连接界面
        self.connect_frame = QFrame()
<<<<<<< HEAD
        self.connect_frame.setObjectName("connectFrame")
        self.connect_frame.setStyleSheet("background-color: #F0F2F5;")
        connect_layout = QVBoxLayout(self.connect_frame)
        connect_layout.setAlignment(Qt.AlignCenter)
        connect_layout.setContentsMargins(20, 20, 20, 20)
        connect_layout.setSpacing(20)

        # 标题
        title_label = QLabel("连接到聊天服务器")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 36px;
                font-weight: bold;
                color: #333;
                font-family: 'Microsoft YaHei', SimSun, sans-serif;
            }
        """)
        connect_layout.addWidget(title_label)

        # 连接表单容器
        form_container = QFrame()
        form_container.setObjectName("formContainer")
        form_container.setStyleSheet("""
            QFrame#formContainer {
                background-color: white;
                border-radius: 15px;
                border: 2px solid #E0E0E0;
            }
        """)
        form_layout = QVBoxLayout(form_container)
        form_layout.setContentsMargins(30, 30, 30, 30)
        form_layout.setSpacing(20)

        # IP地址输入
        ip_layout = QHBoxLayout()
        ip_layout.setSpacing(10)
        ip_label = QLabel("服务器IP地址:")
        ip_label.setStyleSheet("""
            QLabel {
                font-size: 21px;
                font-weight: bold;
                color: #555;
                font-family: 'Microsoft YaHei', SimSun, sans-serif;
                min-width: 150px;
                text-align: right;
            }
        """)
        self.ip_entry = QLineEdit()
        self.ip_entry.setText("127.0.0.1")
        self.ip_entry.setStyleSheet("""
            QLineEdit {
                background-color: #F5F5F5;
                border: none;
                border-radius: 12px;
                padding: 15px 22px;
                font-size: 21px;
                font-family: 'Microsoft YaHei', SimSun, sans-serif;
            }
            QLineEdit:focus {
                background-color: white;
                border: 1px solid #2196F3;
                outline: none;
            }
        """)
        ip_layout.addWidget(ip_label)
        ip_layout.addWidget(self.ip_entry)
        form_layout.addLayout(ip_layout)

        # 端口输入
        port_layout = QHBoxLayout()
        port_layout.setSpacing(10)
        port_label = QLabel("服务器端口:")
        port_label.setStyleSheet("""
            QLabel {
                font-size: 21px;
                font-weight: bold;
                color: #555;
                font-family: 'Microsoft YaHei', SimSun, sans-serif;
                min-width: 150px;
                text-align: right;
            }
        """)
        self.port_entry = QLineEdit()
        self.port_entry.setText("7891")
        self.port_entry.setStyleSheet("""
            QLineEdit {
                background-color: #F5F5F5;
                border: none;
                border-radius: 12px;
                padding: 15px 22px;
                font-size: 21px;
                font-family: 'Microsoft YaHei', SimSun, sans-serif;
            }
            QLineEdit:focus {
                background-color: white;
                border: 1px solid #2196F3;
                outline: none;
            }
        """)
        port_layout.addWidget(port_label)
        port_layout.addWidget(self.port_entry)
        form_layout.addLayout(port_layout)

        # 昵称输入
        nick_layout = QHBoxLayout()
        nick_layout.setSpacing(10)
        nick_label = QLabel("您的昵称:")
        nick_label.setStyleSheet("""
            QLabel {
                font-size: 21px;
                font-weight: bold;
                color: #555;
                font-family: 'Microsoft YaHei', SimSun, sans-serif;
                min-width: 150px;
                text-align: right;
            }
        """)
        self.nick_entry = QLineEdit()
        self.nick_entry.setStyleSheet("""
            QLineEdit {
                background-color: #F5F5F5;
                border: none;
                border-radius: 12px;
                padding: 15px 22px;
                font-size: 21px;
                font-family: 'Microsoft YaHei', SimSun, sans-serif;
            }
            QLineEdit:focus {
                background-color: white;
                border: 1px solid #2196F3;
                outline: none;
            }
        """)
        nick_layout.addWidget(nick_label)
        nick_layout.addWidget(self.nick_entry)
        form_layout.addLayout(nick_layout)

        # 状态标签
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("""
            QLabel {
                color: red;
                font-size: 21px;
                font-family: 'Microsoft YaHei', SimSun, sans-serif;
                text-align: center;
            }
        """)
        form_layout.addWidget(self.status_label)

        # 按钮容器
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        button_layout.setAlignment(Qt.AlignCenter)

        # 连接按钮
        self.connect_button = QPushButton("连接服务器")
        self.connect_button.setObjectName("connectButton")
        self.connect_button.clicked.connect(self.connect_to_server)
        self.connect_button.setStyleSheet("""
            QPushButton#connectButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 30px;
                padding: 18px 45px;
                font-size: 24px;
                font-weight: bold;
                font-family: 'Microsoft YaHei', SimSun, sans-serif;
            }
            QPushButton#connectButton:hover {
                background-color: #1976D2;
            }
            QPushButton#connectButton:pressed {
                background-color: #1565C0;
            }
        """)
        button_layout.addWidget(self.connect_button)

        # 检查更新按钮
        self.check_update_button = QPushButton("检查更新")
        self.check_update_button.setObjectName("checkUpdateButton")
        self.check_update_button.clicked.connect(self.check_for_updates)
        self.check_update_button.setStyleSheet("""
            QPushButton#checkUpdateButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 30px;
                padding: 18px 45px;
                font-size: 24px;
                font-weight: bold;
                font-family: 'Microsoft YaHei', SimSun, sans-serif;
            }
            QPushButton#checkUpdateButton:hover {
                background-color: #45a049;
            }
        """)
        button_layout.addWidget(self.check_update_button)

        form_layout.addLayout(button_layout)
        connect_layout.addWidget(form_container)
        
        # 作者信息
        self.author_label = QLabel("作者: MVP")
        self.author_label.setStyleSheet("color: #666; font-size: 21px; font-family: 'Microsoft YaHei', SimSun, sans-serif;")
=======
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
        
        # 检查更新按钮
        self.check_update_button = QPushButton("检查更新")
        self.check_update_button.setFixedWidth(150)
        self.check_update_button.clicked.connect(self.check_for_updates)
        connect_layout.addWidget(self.check_update_button)
        
        # 作者信息
        self.author_label = QLabel("作者: MVP")
        self.author_label.setStyleSheet("color: gray; font-size: 14px;")
>>>>>>> 2d24d323418f153d54fa4847084755382db36c5c
        self.author_label.setAlignment(Qt.AlignCenter)
        connect_layout.addWidget(self.author_label)

        # 聊天界面
        self.chat_frame = QFrame()
<<<<<<< HEAD
        self.chat_frame.setObjectName("chatFrame")
        chat_layout = QHBoxLayout(self.chat_frame)
        chat_layout.setContentsMargins(0, 0, 0, 0)

        # 左侧聊天区域
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(10, 10, 10, 10)
        left_layout.setSpacing(10)

        # 聊天记录 - 使用更现代化的设计
        self.chat_text = QTextEdit()
        self.chat_text.setReadOnly(True)
        self.chat_text.setObjectName("chatText")
        self.chat_text.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.chat_text.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.chat_text.setStyleSheet("""
            QTextEdit#chatText {
                background-color: #F5F5F5;
                border: 1px solid #E0E0E0;
                border-radius: 15px;
                padding: 15px;
                font-family: 'Microsoft YaHei', SimSun, sans-serif;
                font-size: 21px;
            }
            QTextEdit#chatText::scroll-bar:vertical {
                width: 12px;
                background: transparent;
            }
            QTextEdit#chatText::handle:vertical {
                background-color: rgba(0, 0, 0, 0.2);
                border-radius: 6px;
                min-height: 30px;
            }
            QTextEdit#chatText::handle:vertical:hover {
                background-color: rgba(0, 0, 0, 0.3);
            }
        """)
        left_layout.addWidget(self.chat_text)

        # 消息输入区域 - 现代化设计
        input_container = QFrame()
        input_container.setObjectName("inputContainer")
        input_container.setStyleSheet("""
            QFrame#inputContainer {
                background-color: white;
                border-radius: 10px;
                border: 1px solid #E0E0E0;
            }
        """)
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(10, 10, 10, 10)
        input_layout.setSpacing(10)

        self.message_entry = QLineEdit()
        self.message_entry.setObjectName("messageEntry")
        self.message_entry.setPlaceholderText("输入消息... (按Enter发送, @用户名可以@指定用户)")
        self.message_entry.returnPressed.connect(self.send_message)
        self.message_entry.setStyleSheet("""
            QLineEdit#messageEntry {
                background-color: #F5F5F5;
                border: none;
                border-radius: 30px;
                padding: 15px 22px;
                font-size: 21px;
                font-family: 'Microsoft YaHei', SimSun, sans-serif;
            }
            QLineEdit#messageEntry:focus {
                background-color: white;
                border: 1px solid #2196F3;
                outline: none;
            }
        """)
        input_layout.addWidget(self.message_entry)

        self.send_button = QPushButton("发送")
        self.send_button.setObjectName("sendButton")
        self.send_button.clicked.connect(self.send_message)
        self.send_button.setStyleSheet("""
            QPushButton#sendButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 30px;
                padding: 15px 30px;
                font-size: 21px;
                font-weight: bold;
                font-family: 'Microsoft YaHei', SimSun, sans-serif;
            }
            QPushButton#sendButton:hover {
                background-color: #1976D2;
            }
            QPushButton#sendButton:pressed {
                background-color: #1565C0;
            }
        """)
        input_layout.addWidget(self.send_button)

        left_layout.addWidget(input_container)

        # 右侧用户列表 - 现代化设计
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(10, 10, 10, 10)
        right_layout.setSpacing(10)
        
        # 用户列表容器
        users_container = QFrame()
        users_container.setObjectName("usersContainer")
        users_container.setStyleSheet("""
            QFrame#usersContainer {
                background-color: white;
                border-radius: 10px;
                border: 1px solid #E0E0E0;
            }
        """)
        users_inner_layout = QVBoxLayout(users_container)
        users_inner_layout.setContentsMargins(10, 10, 10, 10)
        users_inner_layout.setSpacing(10)
        
        users_label = QLabel("在线用户")
        users_label.setAlignment(Qt.AlignCenter)
        users_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #333;
                font-family: 'Microsoft YaHei', SimSun, sans-serif;
            }
        """)
        users_inner_layout.addWidget(users_label)

        self.users_list = QListWidget()
        self.users_list.setObjectName("usersList")
        self.users_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.users_list.customContextMenuRequested.connect(self.show_context_menu)
        self.users_list.doubleClicked.connect(self.add_mention)
        self.users_list.setStyleSheet("""
            QListWidget#usersList {
                background-color: #F5F5F5;
                border: none;
                border-radius: 12px;
                padding: 8px;
                font-size: 21px;
                font-family: 'Microsoft YaHei', SimSun, sans-serif;
            }
            QListWidget#usersList::item {
                padding: 12px 15px;
                border-radius: 9px;
                margin-bottom: 5px;
            }
            QListWidget#usersList::item:hover {
                background-color: rgba(33, 150, 243, 0.1);
            }
            QListWidget#usersList::item:selected {
                background-color: rgba(33, 150, 243, 0.2);
                color: #2196F3;
            }
        """)
        users_inner_layout.addWidget(self.users_list)
        
        # 添加检查更新按钮
        self.check_update_button = QPushButton("检查更新")
        self.check_update_button.setObjectName("checkUpdateButton")
        self.check_update_button.clicked.connect(self.check_for_updates)
        self.check_update_button.setStyleSheet("""
            QPushButton#checkUpdateButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 12px;
                padding: 12px 22px;
                font-size: 19px;
                font-family: 'Microsoft YaHei', SimSun, sans-serif;
            }
            QPushButton#checkUpdateButton:hover {
                background-color: #45a049;
            }
        """)
        users_inner_layout.addWidget(self.check_update_button)
        
        # 作者信息
        self.author_label_chat = QLabel("作者: MVP")
        self.author_label_chat.setAlignment(Qt.AlignCenter)
        self.author_label_chat.setStyleSheet("color: #666; font-size: 18px; font-family: 'Microsoft YaHei', SimSun, sans-serif;")
        users_inner_layout.addWidget(self.author_label_chat)
        
        right_layout.addWidget(users_container)
=======
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
        
        # 添加检查更新按钮
        self.check_update_button = QPushButton("检查更新")
        self.check_update_button.clicked.connect(self.check_for_updates)
        right_layout.addWidget(self.check_update_button)
        
        # 作者信息
        self.author_label_chat = QLabel("作者: MVP")
        self.author_label_chat.setStyleSheet("color: gray; font-size: 12px;")
        self.author_label_chat.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(self.author_label_chat)
>>>>>>> 2d24d323418f153d54fa4847084755382db36c5c

        # 添加分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)
<<<<<<< HEAD
        separator.setStyleSheet("background-color: #E0E0E0;")
=======
>>>>>>> 2d24d323418f153d54fa4847084755382db36c5c

        # 组装聊天界面
        chat_layout.addLayout(left_layout, 3)
        chat_layout.addWidget(separator)
        chat_layout.addLayout(right_layout, 1)
<<<<<<< HEAD
        
        # 设置整体背景色
        self.chat_frame.setStyleSheet("background-color: #F0F2F5;")
=======
>>>>>>> 2d24d323418f153d54fa4847084755382db36c5c

        # 初始显示连接界面
        main_layout.addWidget(self.connect_frame)
        # 确保聊天界面初始是隐藏的，并且没有被添加到布局中
        self.chat_frame.hide()

    def setup_signals(self):
        self.comm.message_received.connect(self.display_message)
        self.comm.user_list_updated.connect(self.update_user_list)
        self.comm.profile_received.connect(self.show_user_profile)
        self.comm.error_message.connect(self.show_error_message)
        self.comm.notification.connect(self.show_notification)
        self.comm.show_reconnect_dialog_signal.connect(self.show_reconnect_dialog)

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
                self.setWindowTitle(f"LittleChat v{CURRENT_VERSION} -MVP 当前用户：{self.nickname}")
                self.message_entry.setFocus()

                # 启动接收消息线程
                receive_thread = threading.Thread(target=self.receive_messages, daemon=True)
                receive_thread.start()
<<<<<<< HEAD
                
                # 显示系统消息：你加入了聊天室
                self.add_bubble_message("系统: 你加入了聊天室")
=======
>>>>>>> 2d24d323418f153d54fa4847084755382db36c5c

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
                elif message.startswith("MUTED:"):
                    # 处理被禁言消息
                    mute_message = message.split(":", 1)[1]
                    # 使用信号来触发GUI操作，确保在主线程中执行
                    self.comm.message_received.emit(mute_message)
                    # 发送信号显示禁言提示，确保在主线程中执行
                    self.comm.notification.emit("禁言通知", "您已被管理员禁言，无法发送消息", "info")
                    # 设置禁言状态并禁用输入框
                    self.is_muted = True
                    self.message_entry.setDisabled(True)
                    self.send_button.setDisabled(True)
                elif message.startswith("UNMUTED:"):
                    # 处理解禁消息
                    unmute_message = message.split(":", 1)[1]
                    # 使用信号来触发GUI操作，确保在主线程中执行
                    self.comm.message_received.emit(unmute_message)
                    # 发送信号显示解禁提示，确保在主线程中执行
                    self.comm.notification.emit("解禁通知", "您已被管理员解禁，可以发送消息", "info")
                    # 取消禁言状态并启用输入框
                    self.is_muted = False
                    self.message_entry.setEnabled(True)
                    self.send_button.setEnabled(True)
                elif message.startswith("OP:"):
                    # 处理设为管理员消息
                    op_message = message.split(":", 1)[1]
                    # 使用信号来触发GUI操作，确保在主线程中执行
                    self.comm.message_received.emit(op_message)
                    # 发送信号显示设为管理员提示，确保在主线程中执行
                    self.comm.notification.emit("管理员通知", "您已被设为管理员，获得管理权限", "info")
                elif message.startswith("UNOP:"):
                    # 处理撤销管理员消息
                    unop_message = message.split(":", 1)[1]
                    # 使用信号来触发GUI操作，确保在主线程中执行
                    self.comm.message_received.emit(unop_message)
                    # 发送信号显示撤销管理员提示，确保在主线程中执行
                    self.comm.notification.emit("管理员通知", "您的管理员权限已被撤销", "info")
                else:
                    # 普通消息，显示在聊天记录中
                    self.comm.message_received.emit(message)
            except ConnectionResetError:
                self.comm.message_received.emit("系统: 与服务器断开连接")
                self.connected = False
                # 发送信号显示重连对话框，确保在主线程中执行
                self.comm.show_reconnect_dialog_signal.emit()
                break
            except Exception as e:
                self.comm.message_received.emit(f"系统: 接收错误 - {str(e)}")
                self.connected = False
                # 发送信号显示重连对话框，确保在主线程中执行
                self.comm.show_reconnect_dialog_signal.emit()
                break

<<<<<<< HEAD
    def add_bubble_message(self, message, is_self=False):
        """添加气泡消息到聊天记录"""
        if is_self:
            # 自己发送的消息，右对齐气泡，浅蓝背景
            html = f"""<div style="display: flex; justify-content: flex-end; margin: 18px 0;">
                        <div style="max-width: 75%;">
                            <div style="text-align: right; margin-bottom: 6px; font-size: 21px; color: #000000; margin-right: 12px; font-weight: 500;">我</div>
                            <div style="position: relative; background-color: #E3F2FD;
                                       color: #000000; padding: 21px 27px; border-radius: 30px 30px 6px 30px;
                                       word-wrap: break-word;
                                       font-size: 24px; line-height: 1.5; max-width: 100%;
                                       border: 1px solid #BBDEFB;">
                                {message}
                                <div style="position: absolute; bottom: 0; right: -12px; width: 0; height: 0;
                                           border-top: 12px solid transparent;
                                           border-bottom: 12px solid transparent;
                                           border-left: 12px solid #E3F2FD;"></div>
                            </div>
                        </div>
                      </div>"""
        elif ":" in message and not message.startswith("系统:"):
            # 他人发送的消息，左对齐气泡，浅灰背景
            sender, msg_content = message.split(":", 1)
            sender = sender.strip()
            msg_content = msg_content.strip()
            html = f"""<div style="display: flex; justify-content: flex-start; margin: 18px 0;">
                        <div style="max-width: 75%;">
                            <div style="text-align: left; margin-bottom: 6px; font-size: 21px; color: #000000; margin-left: 12px; font-weight: 500;">{sender}</div>
                            <div style="position: relative; background-color: #F9FAFB;
                                       color: #000000; padding: 21px 27px; border-radius: 30px 30px 30px 6px;
                                       word-wrap: break-word;
                                       font-size: 24px; line-height: 1.5; max-width: 100%;
                                       border: 1px solid #E5E7EB;">
                                {msg_content}
                                <div style="position: absolute; bottom: 0; left: -12px; width: 0; height: 0;
                                           border-top: 12px solid transparent;
                                           border-bottom: 12px solid transparent;
                                           border-right: 12px solid #F9FAFB;"></div>
                            </div>
                        </div>
                      </div>"""
        else:
            # 系统消息，居中显示，浅色背景
            html = f"""<div style="display: flex; justify-content: center; margin: 15px 0;">
                        <div style="background-color: #F3F4F6; color: #000000; padding: 18px 30px; border-radius: 30px;
                                   font-size: 21px; line-height: 1.5; font-weight: 500; max-width: 80%;
                                   text-align: center; border: 1px solid #E5E7EB;">
                            {message}
                        </div>
                      </div>"""
        
        # 确保聊天记录初始状态干净
        if self.chat_text.toPlainText().strip() == "":
            self.chat_text.clear()
        
        # 插入完整的HTML消息块，使用<div>包裹每条消息，确保样式独立
        full_html = f"<div style='display: block; width: 100%;'>{html}</div>"
        self.chat_text.insertHtml(full_html)
        
        # 插入一个换行符，确保消息之间完全分隔
        self.chat_text.insertHtml("<br/>")
        
        # 自动滚动到聊天记录底部
        self.chat_text.ensureCursorVisible()
        self.chat_text.moveCursor(QTextCursor.End)
    
    def display_message(self, message):
        # 显示气泡消息
        self.add_bubble_message(message)
        
        # 检查是否有@自己的消息
        if f"@{self.nickname}" in message and not message.startswith("我:"):
            # 提取发送者昵称
            if ":" in message:
                sender = message.split(":", 1)[0].strip()
                # 弹出通知弹窗
                QMessageBox.information(self, "@提及通知", f"{sender} 在聊天中提到了你")
=======
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
>>>>>>> 2d24d323418f153d54fa4847084755382db36c5c

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
<<<<<<< HEAD
                            self.add_bubble_message(message, is_self=True)
                            self.message_entry.clear()
                        else:
                            self.add_bubble_message("系统: 您不能对自己执行此操作")
                            self.message_entry.clear()
                    else:
                        self.add_bubble_message("系统: 命令格式错误: /kick <用户名>")
=======
                            self.chat_text.append(f"我: {message}")
                            self.message_entry.clear()
                        else:
                            self.chat_text.append("系统: 您不能对自己执行此操作")
                            self.message_entry.clear()
                    else:
                        self.chat_text.append("系统: 命令格式错误: /kick <用户名>")
>>>>>>> 2d24d323418f153d54fa4847084755382db36c5c
                        self.message_entry.clear()
                elif command == 'unop':
                    if len(parts) == 2:
                        target_nickname = parts[1].strip()
                        # 防止管理员自己撤销自己的权限
                        if target_nickname != self.nickname:
                            # 发送命令给服务器
                            admin_command = f"ADMIN_COMMAND:{command}:{target_nickname}"
                            self.client_socket.send(admin_command.encode('utf-8'))
<<<<<<< HEAD
                            self.add_bubble_message(message, is_self=True)
                            self.message_entry.clear()
                        else:
                            self.add_bubble_message("系统: 您不能撤销自己的管理员权限")
                            self.message_entry.clear()
                    else:
                        self.add_bubble_message("系统: 命令格式错误: /unop <用户名>")
=======
                            self.chat_text.append(f"我: {message}")
                            self.message_entry.clear()
                        else:
                            self.chat_text.append("系统: 您不能撤销自己的管理员权限")
                            self.message_entry.clear()
                    else:
                        self.chat_text.append("系统: 命令格式错误: /unop <用户名>")
>>>>>>> 2d24d323418f153d54fa4847084755382db36c5c
                        self.message_entry.clear()
                elif command == 'ban':
                    if len(parts) == 2:
                        target_nickname = parts[1].strip()
                        # 防止管理员自己封禁自己
                        if target_nickname != self.nickname:
                            # 发送命令给服务器
                            admin_command = f"ADMIN_COMMAND:{command}:{target_nickname}"
                            self.client_socket.send(admin_command.encode('utf-8'))
<<<<<<< HEAD
                            self.add_bubble_message(message, is_self=True)
                            self.message_entry.clear()
                        else:
                            self.add_bubble_message("系统: 您不能封禁自己")
                            self.message_entry.clear()
                    else:
                        self.add_bubble_message("系统: 命令格式错误: /ban <用户名>")
=======
                            self.chat_text.append(f"我: {message}")
                            self.message_entry.clear()
                        else:
                            self.chat_text.append("系统: 您不能封禁自己")
                            self.message_entry.clear()
                    else:
                        self.chat_text.append("系统: 命令格式错误: /ban <用户名>")
>>>>>>> 2d24d323418f153d54fa4847084755382db36c5c
                        self.message_entry.clear()
                elif command == 'unban':
                    if len(parts) == 2:
                        target_nickname = parts[1].strip()
                        # 发送命令给服务器
                        admin_command = f"ADMIN_COMMAND:{command}:{target_nickname}"
                        self.client_socket.send(admin_command.encode('utf-8'))
<<<<<<< HEAD
                        self.add_bubble_message(message, is_self=True)
                        self.message_entry.clear()
                    else:
                        self.add_bubble_message("系统: 命令格式错误: /unban <用户名>")
=======
                        self.chat_text.append(f"我: {message}")
                        self.message_entry.clear()
                    else:
                        self.chat_text.append("系统: 命令格式错误: /unban <用户名>")
>>>>>>> 2d24d323418f153d54fa4847084755382db36c5c
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
<<<<<<< HEAD
                                self.add_bubble_message(message, is_self=True)
                                self.message_entry.clear()
                            else:
                                self.add_bubble_message("系统: 您不能禁言自己")
                                self.message_entry.clear()
                        else:
                            self.add_bubble_message("系统: 命令格式错误: /shutup <用户名> <时间（分钟）>")
                            self.message_entry.clear()
                    else:
                        self.add_bubble_message("系统: 命令格式错误: /shutup <用户名> <时间（分钟）>")
=======
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
>>>>>>> 2d24d323418f153d54fa4847084755382db36c5c
                        self.message_entry.clear()
                elif command == 'unshutup':
                    if len(parts) == 2:
                        target_nickname = parts[1].strip()
                        # 防止管理员自己解除自己的禁言
                        if target_nickname != self.nickname:
                            # 发送命令给服务器
                            admin_command = f"ADMIN_COMMAND:{command}:{target_nickname}"
                            self.client_socket.send(admin_command.encode('utf-8'))
<<<<<<< HEAD
                            self.add_bubble_message(message, is_self=True)
                            self.message_entry.clear()
                        else:
                            self.add_bubble_message("系统: 您不能解除自己的禁言")
                            self.message_entry.clear()
                    else:
                        self.add_bubble_message("系统: 命令格式错误: /unshutup <用户名>")
                        self.message_entry.clear()
                else:
                    # 不支持的命令
                    self.add_bubble_message(f"系统: 不支持的命令: {command}")
=======
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
>>>>>>> 2d24d323418f153d54fa4847084755382db36c5c
                    self.message_entry.clear()
            else:
                # 普通消息
                self.client_socket.send(message.encode('utf-8'))
<<<<<<< HEAD
                # 在聊天记录中显示自己发送的消息（气泡样式）
                self.add_bubble_message(message, is_self=True)
                self.message_entry.clear()
        except Exception as e:
            self.add_bubble_message(f"系统: 发送失败 - {str(e)}")
=======
                # 在聊天记录中显示自己发送的消息
                self.chat_text.append(f"我: {message}")
                self.message_entry.clear()
        except Exception as e:
            self.chat_text.append(f"系统: 发送失败 - {str(e)}")
>>>>>>> 2d24d323418f153d54fa4847084755382db36c5c

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
    
    def show_notification(self, title, content, notification_type):
        # 显示通知消息，在主线程中执行
        if notification_type == "info":
            QMessageBox.information(self, title, content)
        elif notification_type == "warning":
            QMessageBox.warning(self, title, content)
        elif notification_type == "error":
            QMessageBox.critical(self, title, content)
        else:
            QMessageBox.information(self, title, content)

    def update_user_list(self, users):
        # 更新在线用户列表
        self.users_list.clear()
        for user in users:
            item = QListWidgetItem(user)
            self.users_list.addItem(item)

    def show_reconnect_dialog(self):
        # 如果已经显示了重连对话框，直接返回，避免重复显示
        if self.showing_reconnect_dialog:
            return
        
        # 设置标志位，表示正在显示重连对话框
        self.showing_reconnect_dialog = True
        
        try:
            # 显示重连对话框
            reply = QMessageBox.question(self, "连接断开", 
                                        f"服务器连接已断开（{self.ip_entry.text()}:{self.port_entry.text()}）是否重连或返回主界面？",
                                        QMessageBox.Retry | QMessageBox.Cancel, 
                                        QMessageBox.Retry)
            if reply == QMessageBox.Retry:
                # 用户选择重连，尝试5次
                self.reconnect_to_server()
            else:
                # 用户选择返回主界面
                self.return_to_main()
        finally:
            # 无论如何，都要重置标志位，表示重连对话框已经关闭
            self.showing_reconnect_dialog = False
    
    def reconnect_to_server(self):
        # 尝试重连服务器，最多5次
        max_retries = 5
        retry_count = 0
        success = False
        
        while retry_count < max_retries and not success:
            retry_count += 1
            self.comm.message_received.emit(f"系统: 尝试第 {retry_count} 次重连...")
            
            try:
                # 关闭旧连接（如果存在）
                if self.client_socket:
                    try:
                        self.client_socket.close()
                    except:
                        pass
                
                # 创建新连接
                self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.client_socket.connect((self.ip_entry.text(), int(self.port_entry.text())))
                # 发送昵称
                self.client_socket.send(self.nickname.encode('utf-8'))
                
                # 接收服务器响应
                response = self.client_socket.recv(1024).decode('utf-8')
                
                if response.startswith("ERROR:"):
                    # 昵称冲突或其他错误
                    self.comm.message_received.emit(f"系统: 重连失败 - {response[6:]}")
                elif response.startswith("SUCCESS:"):
                    # 重连成功
                    self.connected = True
                    success = True
                    self.comm.message_received.emit("系统: 重连成功！")
                    
                    # 启动接收消息线程
                    receive_thread = threading.Thread(target=self.receive_messages, daemon=True)
                    receive_thread.start()
                
                # 如果成功，退出循环
                if success:
                    break
            except Exception as e:
                self.comm.message_received.emit(f"系统: 重连失败 - {str(e)}")
            
            # 等待1秒后重试
            if not success and retry_count < max_retries:
                time.sleep(1)
        
        # 如果重连失败，显示失败信息并返回主界面
        if not success:
            self.comm.message_received.emit(f"系统: 经过 {max_retries} 次尝试，重连失败，返回主界面")
            self.return_to_main()
    
    def return_to_main(self):
        # 返回主界面（连接界面）
        self.connected = False
        # 关闭旧连接
        if self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass
        
        # 切换回连接界面
        main_layout = self.centralWidget().layout()
        # 移除聊天界面
        main_layout.removeWidget(self.chat_frame)
        self.chat_frame.hide()
        # 添加连接界面
        main_layout.addWidget(self.connect_frame)
        self.connect_frame.show()
        # 重置窗口标题
        self.setWindowTitle("LittleChat -MVP")
    
    def check_for_updates(self):
        """检查Gitee仓库是否有新的发行版"""
        try:
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
            
            # 获取下载链接，优先使用assets中的下载链接
            download_url = ""
            assets = latest_release.get("assets", [])
            if assets:
                # 优先使用第一个asset的浏览器下载链接
                download_url = assets[0].get("browser_download_url", "")
            
            # 如果没有assets，使用zipball_url
            if not download_url:
                download_url = latest_release.get("zipball_url", "")
                
            # 确保URL有协议前缀
            if download_url and not (download_url.startswith("http://") or download_url.startswith("https://")):
                download_url = f"https://gitee.com{download_url}"
            
            release_notes = latest_release.get("body", "")
            
            # 验证下载URL
            if not download_url:
                QMessageBox.warning(self, "检查更新", "获取下载链接失败，请稍后再试！")
                return
            
            # 比较版本
            if self.compare_versions(CURRENT_VERSION, latest_version):
                # 有新版本
                self.on_update_available(latest_version, download_url, release_notes)
            else:
                QMessageBox.information(self, "检查更新", f"程序版本：{CURRENT_VERSION} \n当前已是最新版本！")
                
        except requests.exceptions.RequestException as e:
            QMessageBox.critical(self, "检查更新失败", f"网络请求错误：{str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "检查更新失败", f"解析错误：{str(e)}")
    
    def compare_versions(self, current_ver, latest_ver):
        """比较版本号，返回是否需要更新"""
        try:
            # 解析版本号为列表
            current = list(map(int, current_ver.split(".")))
            latest = list(map(int, latest_ver.split(".")))
            
            # 比较每个部分
            for i in range(max(len(current), len(latest))):
                curr = current[i] if i < len(current) else 0
                lat = latest[i] if i < len(latest) else 0
                
                if lat > curr:
                    return True
                elif lat < curr:
                    return False
            
            return False
        except Exception:
            # 版本号格式错误，默认不需要更新
            return False
    
    def on_update_available(self, latest_version, download_url, release_notes):
        """处理更新可用事件"""
        msg = QMessageBox()
        msg.setWindowTitle("发现新版本")
        msg.setText(f"当前版本：{CURRENT_VERSION}\n最新版本：{latest_version}\n\n更新日志：\n{release_notes}")
        msg.setIcon(QMessageBox.Information)
        
        # 添加按钮
        update_button = msg.addButton("立即更新", QMessageBox.AcceptRole)
        later_button = msg.addButton("稍后更新", QMessageBox.RejectRole)
        ignore_button = msg.addButton("忽略此版本", QMessageBox.ActionRole)
        
        msg.exec_()
        
        if msg.clickedButton() == update_button:
            # 开始下载
            self.download_latest_release(download_url, latest_version)
    
    def download_latest_release(self, download_url, latest_version):
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
            
            # 创建进度对话框
            progress = QProgressDialog("正在下载更新...", "取消", 0, total_size, self)
            progress.setWindowTitle("下载更新")
            progress.setWindowModality(Qt.WindowModal)
            progress.show()
            
            # 设置文件名
            file_name = f"{GITEE_REPO}_v{latest_version}.zip"
            
            # 开始下载
            downloaded_size = 0
            with open(file_name, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        
                        # 更新进度
                        progress.setValue(downloaded_size)
                        
                        # 检查是否取消
                        if progress.wasCanceled():
                            # 删除未完成的文件
                            import os
                            os.remove(file_name)
                            QMessageBox.information(self, "下载取消", "更新下载已取消")
                            return
            
            progress.close()
            QMessageBox.information(self, "下载完成", f"最新版本已下载完成：{file_name}")
            
        except requests.exceptions.RequestException as e:
            QMessageBox.critical(self, "下载失败", f"网络请求错误：{str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "下载失败", f"下载错误：{str(e)}")
    
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