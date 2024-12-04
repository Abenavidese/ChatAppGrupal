import ssl
import socket
import threading
import tkinter as tk
from tkinter import simpledialog, scrolledtext
import time

host = 'localhost'
port = 55555

# Variables globales
secure_client = None
connected = False
nickname = None

# Crear y configurar el socket seguro
def create_secure_client():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    context = ssl.create_default_context(cafile="cert.pem")
    secure_client = context.wrap_socket(client, server_hostname=host)
    return secure_client

# Intentar conectar al servidor con reintentos
def connect_to_server():
    global secure_client, connected
    while not connected:
        try:
            secure_client = create_secure_client()
            secure_client.connect((host, port))
            connected = True
            chat_box_insert("Connected to the server!")
            secure_client.send(nickname.encode('ascii'))  # Enviar el nickname al servidor
            threading.Thread(target=receive_messages, daemon=True).start()
        except Exception as e:
            connected = False
            chat_box_insert("Server disconnected. Retrying in 5 seconds...")
            time.sleep(5)

# Insertar texto en el chatbox
def chat_box_insert(message):
    chat_box.config(state=tk.NORMAL)
    chat_box.insert(tk.END, f"{message}\n")
    chat_box.config(state=tk.DISABLED)
    chat_box.yview(tk.END)

# Función para recibir mensajes del servidor
def receive_messages():
    global connected
    while connected:
        try:
            message = secure_client.recv(1024).decode('ascii')
            if not message:
                raise ConnectionResetError("Empty message received.")
            if message == 'NICK':  # Si el servidor solicita el apodo
                secure_client.send(nickname.encode('ascii'))
            else:
                chat_box_insert(message)
        except Exception as e:
            connected = False
            chat_box_insert("Lost connection to the server.")
            connect_to_server()
            break

# Función para enviar mensajes al servidor
def send_message(event=None):
    global connected
    message = message_entry.get()
    if connected and message:
        try:
            secure_client.send(message.encode('ascii'))
            message_entry.delete(0, tk.END)
        except Exception as e:
            chat_box_insert("Failed to send message. Please try again.")
    else:
        chat_box_insert("You are not connected to the server.")

# Preguntar por el nickname
def ask_nickname():
    return simpledialog.askstring("Nickname", "Choose a nickname:") or "Anonymous"

# Interfaz gráfica
root = tk.Tk()
root.title("Chat Cliente")
root.geometry("500x500")
root.configure(bg="#2C3E50")

nickname = ask_nickname()

chat_box_label = tk.Label(root, text=f"Nickname: {nickname}", bg="#2C3E50", fg="#ECF0F1")
chat_box_label.pack(pady=10)

chat_box = scrolledtext.ScrolledText(root, width=50, height=20, state='disabled', bg="#34495E", fg="#ECF0F1")
chat_box.pack(pady=10)

message_entry = tk.Entry(root, width=40, bg="#ECF0F1", font=("Arial", 10))
message_entry.pack(side=tk.LEFT, padx=(20, 10), pady=10)
message_entry.bind("<Return>", send_message)

send_button = tk.Button(root, text="Enviar", command=send_message, bg="#3498DB", fg="#ECF0F1")
send_button.pack(side=tk.LEFT, padx=(0, 20), pady=10)

# Conectar al servidor
threading.Thread(target=connect_to_server, daemon=True).start()

root.mainloop()