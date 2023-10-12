import socket
import threading
import json
import os

# Server configuration
HOST = '127.0.0.1'  # Loopback address for localhost
PORT = 12345  # Port to listen on

previous_message=''

# Create a socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Bind the socket to the specified address and port
server_socket.bind((HOST, PORT))

# Listen for incoming connections
server_socket.listen()
print(f"Server is listening on {HOST}:{PORT}")

# Store client information in a dictionary
clients = {}  # {client_socket: {"name": name, "room": room}}

# Function to handle a client's messages
def handle_client(client_socket, client_address):
    print(f"Accepted connection from {client_address}")
    while True:
        try:
            message = client_socket.recv(1024).decode('utf-8')
            if not message:
                break
            message_json = json.loads(message)
            message_type = message_json.get("type")
            
            if message_type == "connect":
                name = message_json["payload"]["name"]
                room = message_json["payload"]["room"]
                clients[client_socket] = {"name": name, "room": room}
                
                # Notify the client of successful connection
                connect_ack_message = {
                    "type": "connect_ack",
                    "payload": {
                        "message": "Connected to the room."
                    }
                }
                client_socket.sendall(json.dumps(connect_ack_message).encode('utf-8'))
                # Notify other clients in the room about the new user
                notification_message = {
                    "type": "notification",
                    "payload": {
                        "message": f"{name} has joined the room."
                    }
                }
                broadcast_message_to_room(notification_message, room)

            elif message_type == "message":
                sender_name = clients[client_socket]["name"]
                room = clients[client_socket]["room"]
                text = message_json["payload"]["text"]
                
                # Broadcast the message to all clients in the same room
                message_to_broadcast = {
                    "type": "message",
                    "payload": {
                        "sender": sender_name,
                        "room": room,
                        "text": text
                    }
                }
                broadcast_message_to_room(message_to_broadcast, room)
            elif message_type == 'file_command':
                command = message_json['payload']['command']
                file_path = command.split(' ')[1]
                if command.startswith('upload'):
                    handle_uploads(name,room,message_json, file_path)
                elif command.startswith('download'):
                    handle_downloads(name,room,message_json, file_path)
            
                
        except (json.JSONDecodeError, KeyError):
            # Handle JSON decoding errors or missing keys
            pass
        except:
            break  # Exit the loop when the client disconnects
    
    # Remove the client from the dictionary
    if client_socket in clients:
        del clients[client_socket]
    
    client_socket.close()

# Function to broadcast a message to all clients in a specific room
def broadcast_message_to_room(message, room):
    # Display the message in the format: [Room Name]: [Sender's Name]: [Message Text]
    if message['type'] == 'notification':
        formatted_message = f"{room}: {message['payload']['message']}"
    elif message['type'] == 'message':
        formatted_message = f"{room}: {message['payload']['sender']}: {message['payload']['text']}"
    print(formatted_message)

    for client_socket, client_info in clients.items():
        if client_info["room"] == room:
            client_socket.sendall(json.dumps(message).encode('utf-8'))


def handle_downloads(name, room, message_json, file_path):
    server_media_path = os.path.join('SERVER_MEDIA', room, file_path)

    if os.path.exists(server_media_path):
        with open(server_media_path, 'rb') as file:
            file_data = file.read()

        client_socket.send(file_data)

        client_media_folder = os.path.join('CLIENT_MEDIA', name)
        os.makedirs(client_media_folder, exist_ok=True)
        client_file_path = os.path.join(client_media_folder, file_path)

        with open(client_file_path, 'wb') as client_file:
            client_file.write(file_data)

        # Notify the client that the file was downloaded successfully
        client_socket.send(json.dumps({
            "type": "notification",
            "payload": {
                "message": f"File {file_path} downloaded."
            }
        }).encode('utf-8'))
    else:
        client_socket.send(json.dumps({
            "type": "notification",
            "payload": {
                "message": f"The {file_path} doesn't exist."
            }
        }).encode('utf-8'))

def handle_uploads(name, room, message_json, file_path):
    if os.path.exists(file_path):
        room_folder = os.path.join('SERVER_MEDIA', room)
        os.makedirs(room_folder, exist_ok=True)  #

        with open(file_path, 'rb') as file:
            file_data = file.read()
            file_name = os.path.basename(file_path)
            server_media_path = os.path.join(room_folder, file_name)
            with open(server_media_path, 'wb') as server_file:
                server_file.write(file_data)


        for msg_socket, msg_details in clients.items():
            msg_room = msg_details.get("room")
            if msg_room == room:
                msg_socket.send(json.dumps({
                    "type": "notification",
                    "payload": {
                        "message": f"User {name} uploaded {file_name}."
                    }
                }).encode('utf-8'))
    else:

        client_socket.send(json.dumps({
            "type": "notification",
            "payload": {
                "message": f"File {file_path} doesn't exist."
            }
        }).encode('utf-8'))

while True:
    client_socket, client_address = server_socket.accept()
    clients[client_socket] = {"name": None, "room": None}
    
    # Start a thread to handle the client
    client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
    client_thread.start()
