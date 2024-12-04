import ssl
import socket
import threading

host = 'localhost'
port = 55555

# Crear y configurar el socket
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((host, port))
server.listen()

context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain(certfile="cert.pem", keyfile="key.pem")
secure_server = context.wrap_socket(server, server_side=True)

clients = []
nicknames = []
first_message_flag = {}  # Diccionario para rastrear si es el primer mensaje de cada cliente

def broadcast(message):
    for client in clients[:]:
        try:
            client.send(message)
        except (ssl.SSLEOFError, ConnectionResetError):
            clients.remove(client)
            client.close()

def handle(client):
    while True:
        try:
            # Intenta recibir un mensaje del cliente
            message = client.recv(1024).decode('ascii')
            if not message:
                # Si el cliente se desconectó de manera correcta, se cierra la conexión
                raise ConnectionResetError("Client disconnected.")
            
            index = clients.index(client)  # Obtener el índice del cliente
            nickname = nicknames[index]  # Obtener el nickname del cliente

            # Añadir el nombre del remitente al mensaje
            full_message = f"{nickname}: {message}"

            # Si es el primer mensaje, no se retransmite
            if first_message_flag.get(client, False):
                first_message_flag[client] = False
                continue

            # Retransmitir el mensaje a todos los clientes
            broadcast(full_message.encode('ascii'))

        except (ssl.SSLEOFError, ConnectionResetError) as e:
            # Si ocurre un error, eliminar el cliente de la lista de clientes y notificar a los demás
            try:
                index = clients.index(client)
                clients.remove(client)
                nickname = nicknames.pop(index)
                client.close()
                broadcast(f'{nickname} left the chat!'.encode('ascii'))
                # Mostrar en el servidor que el usuario se desconectó
                print(f"{nickname} se ha desconectado")
            except ValueError:
                # Si ya no está en la lista de clientes, simplemente termina la ejecución
                pass
            break
        except Exception as e:
            print(f"Error al recibir mensaje: {e}")
            break


def receive():
    while True:
        client, address = secure_server.accept()
        print(f"Connection established with {str(address)}")

        client.send('NICK'.encode('ascii'))
        nickname = client.recv(1024).decode('ascii')
        nicknames.append(nickname)
        clients.append(client)

        # Marcar que este cliente ha enviado su primer mensaje (el nickname)
        first_message_flag[client] = True

        print(f"Nickname of the client is {nickname}")
        # Mostrar en el servidor que el usuario se ha conectado
        print(f"Conexión establecida con {nickname}")
        
        # Anunciar la llegada del nuevo cliente sin enviar su primer mensaje
        broadcast(f"{nickname} joined the chat!".encode('ascii'))
        client.send('Connected to the server!'.encode('ascii'))

        thread = threading.Thread(target=handle, args=(client,))
        thread.start()

print("Secure server is listening...")
receive()
