import socket
import threading
import json
import os


# Server configuration
HOST = '127.0.0.1'  # Server's IP address
PORT = 12345  # Server's port


# Create a socket
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:

    # Connect to the server
    client_socket.connect((HOST, PORT))
    print(f"Connected to {HOST}:{PORT}")

    # Function to receive and display messages
    def receive_messages():
        while True:
            try:
                message = client_socket.recv(1024).decode('utf-8')
                if not message:
                    break
                message_json = json.loads(message)
                message_type = message_json.get("type")
                
                if message_type == "connect_ack":
                    # Display a connection acknowledgment message
                    print("You connected to the room.")
                
                elif message_type == "notification":
                    # Display a notification about someone else joining the room
                    join_message = message_json["payload"]["message"]
                    print(join_message)

                elif message_type == "message":
                    sender_name = message_json["payload"]["sender"]
                    message_text = message_json["payload"]["text"]
                    print(f"\n{sender_name}: {message_text}")

            except (json.JSONDecodeError, KeyError):
                # Handle JSON decoding errors or missing keys
                pass
            except:
                break  # Exit the loop when the server disconnects

    # Start the message reception thread
    receive_thread = threading.Thread(target=receive_messages)
    receive_thread.daemon = True  # Thread will exit when the main program exits
    receive_thread.start()

    while True:
        message = input()

        if message.lower() == 'exit':
            break

        if message.lower() == 'connect':
            room = input("Enter room: ")
            name = input("Enter name: ")
            message_json = {
                'type': 'connect',
                'payload': {
                    'name': name,
                    'room': room
                }
            }
            client_socket.sendall(json.dumps(message_json).encode('utf-8'))

        elif message.startswith('upload'):
            file_path = message.split(' ')[1]
            if os.path.exists(file_path):
                message_json = {
                    "type": "file_command",
                    "payload": {
                        "command": f"upload: {file_path}"
                    }
                }
                client_socket.send(json.dumps(message_json).encode('utf-8'))
            else:
                print(f"File {file_path} doesn't exist.")
        elif message.startswith('download'):
            message_json = {
                "type": "file_command",
                "payload": {
                    "command": message
                }
            }
            client_socket.send(json.dumps(message_json).encode('utf-8'))
        else:
            # Send regular messages to the server
            message_json = {
                'type': 'message',
                'payload': {
                    'text': message
                }
            }
            client_socket.sendall(json.dumps(message_json).encode('utf-8'))

    parting_message = 'exit'
    client_socket.sendall(parting_message.encode('utf-8'))  # Use sendall to ensure the entire message is sent

    # Close the client socket when done
    client_socket.close()
