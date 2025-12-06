import socket
import tkinter as tk
import threading

def start_client():
    root = tk.Tk()
    root.title("局域网聊天客户端")
    root.geometry("400x400")
    root.resizable(False, False)
    
    client_socket = None
    
    # 创建连接框架
    def create_connection_frame():
        connection_frame = tk.Frame(root, padx=20, pady=20)
        connection_frame.pack(fill=tk.BOTH, expand=True)
        
        # IP地址输入
        ip_label = tk.Label(connection_frame, text="服务器IP地址:")
        ip_label.pack(pady=5)
        ip_entry = tk.Entry(connection_frame, width=30)
        ip_entry.pack(pady=5)
        ip_entry.insert(0, "127.0.0.1")  # 默认本地IP
        
        # 端口输入
        port_label = tk.Label(connection_frame, text="服务器端口:")
        port_label.pack(pady=5)
        port_entry = tk.Entry(connection_frame, width=30)
        port_entry.pack(pady=5)
        port_entry.insert(0, "7891")  # 默认端口7891
        
        # 状态标签
        status_label = tk.Label(connection_frame, text="", fg="red")
        status_label.pack(pady=10)
        
        def connect_to_server():
            nonlocal client_socket
            ip = ip_entry.get()
            port = port_entry.get()
            
            try:
                port = int(port)
                if port < 1 or port > 65535:
                    raise ValueError("端口号无效")
                
                client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client_socket.connect((ip, port))
                status_label.config(text="连接成功！", fg="green")
                connection_frame.pack_forget()
                create_nickname_frame()
            except ValueError as e:
                status_label.config(text=f"错误: {e}", fg="red")
            except ConnectionRefusedError:
                status_label.config(text="无法连接到服务器：不存在的服务器", fg="red")
            except socket.gaierror:
                status_label.config(text="错误: 无效的IP地址", fg="red")
            except Exception as e:
                status_label.config(text="无法连接到服务器：不存在的服务器", fg="red")
        
        connect_button = tk.Button(connection_frame, text="连接服务器", command=connect_to_server)
        connect_button.pack(pady=10)
    
    # 创建昵称框架
    def create_nickname_frame():
        nickname_frame = tk.Frame(root, padx=20, pady=20)
        nickname_frame.pack(fill=tk.BOTH, expand=True)
        
        nickname_label = tk.Label(nickname_frame, text="请输入您的昵称:")
        nickname_label.pack(pady=10)
        
        nickname_entry = tk.Entry(nickname_frame, width=30)
        nickname_entry.pack(pady=5)
        
        def send_nickname():
            nickname = nickname_entry.get().strip()
            if not nickname:
                status_label.config(text="昵称不能为空", fg="red")
                return
            
            try:
                client_socket.send(nickname.encode('utf-8'))
                nickname_frame.pack_forget()
                setup_chat_interface(nickname)
            except Exception as e:
                status_label.config(text=f"发送失败: {str(e)}", fg="red")
        
        status_label = tk.Label(nickname_frame, text="", fg="red")
        status_label.pack(pady=10)
        
        send_button = tk.Button(nickname_frame, text="确定", command=send_nickname)
        send_button.pack(pady=10)
    
    # 创建聊天界面
    def setup_chat_interface(nickname):
        chat_frame = tk.Frame(root)
        chat_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 聊天记录区域
        output_text = tk.Text(chat_frame, height=15, width=50)
        output_text.pack(pady=5, fill=tk.BOTH, expand=True)
        output_text.config(state=tk.DISABLED)  # 设置为只读
        
        # 消息输入区域
        input_frame = tk.Frame(chat_frame)
        input_frame.pack(fill=tk.X, pady=5)
        
        input_entry = tk.Entry(input_frame, width=40)
        input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        def send_message():
            message = input_entry.get().strip()
            if not message:
                return
            
            try:
                client_socket.send(message.encode('utf-8'))
                # 在聊天记录中显示自己发送的消息
                output_text.config(state=tk.NORMAL)
                output_text.insert(tk.END, f"我: {message}\n")
                output_text.config(state=tk.DISABLED)
                output_text.see(tk.END)  # 自动滚动到底部
                input_entry.delete(0, tk.END)
            except Exception as e:
                output_text.config(state=tk.NORMAL)
                output_text.insert(tk.END, f"系统: 发送失败 - {str(e)}\n", "error")
                output_text.config(state=tk.DISABLED)
                output_text.see(tk.END)
        
        send_button = tk.Button(input_frame, text="发送", command=send_message)
        send_button.pack(side=tk.RIGHT, padx=5)
        
        # 绑定回车键发送消息
        input_entry.bind('<Return>', lambda event: send_message())
        
        # 配置文本标签样式
        output_text.tag_configure("error", foreground="red")
        output_text.tag_configure("system", foreground="blue")
        
        def receive_messages():
            while True:
                try:
                    message = client_socket.recv(1024).decode('utf-8')
                    if not message:
                        break
                    output_text.config(state=tk.NORMAL)
                    output_text.insert(tk.END, message + "\n")
                    output_text.config(state=tk.DISABLED)
                    output_text.see(tk.END)
                except ConnectionResetError:
                    output_text.config(state=tk.NORMAL)
                    output_text.insert(tk.END, "系统: 与服务器断开连接\n", "error")
                    output_text.config(state=tk.DISABLED)
                    output_text.see(tk.END)
                    break
                except Exception as e:
                    output_text.config(state=tk.NORMAL)
                    output_text.insert(tk.END, f"系统: 接收错误 - {str(e)}\n", "error")
                    output_text.config(state=tk.DISABLED)
                    output_text.see(tk.END)
                    break
        
        receive_thread = threading.Thread(target=receive_messages, daemon=True)
        receive_thread.start()
    
    # 启动连接界面
    create_connection_frame()
    root.mainloop()
    
    # 关闭连接
    if client_socket:
        try:
            client_socket.close()
        except:
            pass

if __name__ == "__main__":
    start_client()