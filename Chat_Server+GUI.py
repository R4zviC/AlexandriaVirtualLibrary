# UPPER = constants
# lower = variables
import base64
import json
import os
import re
import socket
import subprocess
import getpass
import threading

HEADER = 256  # byte size of header
SIZE = 16384  # byte size of packages
PORT = 8080

# Setting up the server
try:
    HOST_NAME = socket.gethostname()
    SERVER = socket.gethostbyname(HOST_NAME)  # host local IP address
except socket.gaierror:
    HOST_NAME = socket.gethostname()
    SERVER = HOST_NAME.split('.')[0].replace('-', '.')  # host local IP address

ADDRESS = (SERVER, PORT)  # address info = pair (host address, port)
# FORMAT = 'utf-8'
DISCONNECT_MESSAGE = 'D'
REQUEST_FILE = 'R'
SET_NICKNAME = 'N'
LIBRARY_PATH = 'files/Library'

server_chat = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)

shelf_path = 'files/Library'
bookshelf = os.listdir(shelf_path)
print(f'\nAvailable files for download: {bookshelf}\n')
list_connections = []


def broadcast(message):
    for i in list_connections:
        if i['nickname'] is not None:
            thread = threading.Thread(target=send, args=(i['client_chat'], 0, 0, None, message))
            thread.start()


def bind():
    success = False
    while success is False:
        try:
            server_chat.bind(ADDRESS)
            success = True
            print('Server successfully bound...')
        except OSError:
            command_1 = f'lsof -i:{PORT}'
            child_process = subprocess.run(command_1, shell=True, capture_output=True)
            result = child_process.stdout.decode()
            if re.search(getpass.getuser(), result) and re.search('python', result, re.IGNORECASE):
                pid = result.split()[10]
                command_2 = f'kill {pid}'
                subprocess.run(command_2, shell=True)
                continue
            elif result == '':
                continue
            else:
                print(f'The port {PORT} is used by unknown process!'
                      '\nKill it manually only if appropriate!'
                      '\nPress Enter when done')
                if input() == '':
                    continue


# custom thread
class CustomThread(threading.Thread):
    # constructor
    def __init__(self, client, address):
        # execute the base constructor
        threading.Thread.__init__(self)
        self.client = client
        self.client_chat = None
        self.client_download = None
        self.address = address
        # set a default value
        self.is_free = True
        self.full_message = ''

    # override the run function
    def run(self):
        self.handle()

    # function executed in the new thread
    def handle(self):
        global bookshelf
        nickname = None
        print(f'\nNew connection established: {self.address}')
        print(f'Active connections: {threading.active_count() - 1}')
        socket_type = None
        index = None
        for i in list_connections:
            if i['client_chat'] == self.client:
                self.client_chat = self.client
                i['availability_chat'] = self.is_free
                socket_type = 'c'
                index = list_connections.index(i)
                break
            elif i['client_download'] == self.client:
                self.client_download = self.client
                i['availability_download'] = self.is_free
                socket_type = 'd'
                index = list_connections.index(i)
                break
        online_chat_users = []
        other_connected = []
        count_chat = 1
        count_other = 1
        for i in list_connections:
            if list_connections.index(i) != index:
                if i['nickname'] is None:
                    other_connected.append(f'#{count_other}: {i['nickname']}')
                    count_other += 1
                else:
                    online_chat_users.append(f'#{count_chat}: {i['nickname']}')
                    count_chat += 1
        print(f'Type of socket: for {socket_type}')
        print(f'Currently active chat users: {online_chat_users}')
        print(f'Currently active other users: {other_connected}\n')
        if socket_type == 'c':
            send(self.client, 1, 0, filename=None, data=bookshelf)
            send(self.client, 0, 0, filename=None, data=online_chat_users)
        connected = True
        while connected:
            self.full_message = receive(self.client)
            try:
                self.full_message = json.loads(self.full_message)
                command = self.full_message.get("command")
                data = self.full_message.get("data")
                # Handle the command
                if command == SET_NICKNAME:
                    if socket_type == 'c':
                        nickname = self.full_message.get("nickname")
                        for i in list_connections:
                            if i['client_chat'] == self.client or i['client_download'] == self.client:
                                i['nickname'] = nickname
                                break
                        broadcast(f'!!{nickname} joined the chat!!\n')
                        print(f'{self.address} joined the chat as "{nickname}"\n')
                    else:
                        pass
                elif command == REQUEST_FILE:
                    if socket_type == 'd':
                        file_name = self.full_message.get("filename")
                        # Process file request
                        print(f"{self.address} sent file request for: {file_name}\n")
                        try:
                            file_path = LIBRARY_PATH + '/' + file_name
                            file = open(file_path, 'rb')
                            file_read = file.read()
                            file_read = base64.b64encode(file_read).decode()
                            # send(self.client, 0, 1, data=file_read, filename=file_name)
                            threading.Thread(target=send, args=(self.client, 0, 1, file_name, file_read)).start()
                            file.close()
                        except FileNotFoundError:
                            print('File not found!')
                            # send(self.client, 0, 0, data='The file you requested was not found!\n')
                            threading.Thread(target=send, args=(self.client, 0, 0, file_name, 'The file you requested '
                                                                                              'was'
                                                                                              'not found!\n')).start()
                    else:
                        pass
                elif command == DISCONNECT_MESSAGE:
                    # Disconnect
                    print(f"{self.address} sent disconnection request\n")
                    while True:
                        if self.is_free:
                            connected = False
                            break
                        else:
                            continue
                elif command is None:
                    if socket_type == 'c':
                        # Chat
                        chat_message = data
                        print(f'{self.address} chats: {chat_message}')
                        broadcast(nickname + ': ' + chat_message)  # broadcast to chat
                    else:
                        pass
                else:
                    pass
            except json.JSONDecodeError:
                # Handle invalid JSON
                print("Error decoding JSON message: parsing failed!")
                break
            except TypeError:
                # Handle invalid JSON
                print("Error decoding JSON message: wrong type!")
                break
        disconnect(self.client, self.address, socket_type)


def disconnect(client, address, socket_type):
    try:
        if socket_type == 'c':
            nickname = None
            for i in list_connections:
                if i['client_chat'] == client:
                    nickname = i['nickname']
                    break
            if nickname is not None:
                broadcast(f'!!{nickname} left the chat!!\n')
            client.close()
            print(f'{address} disconnected')
            print(f'Active connections: {threading.active_count() - 2}\n')
        elif socket_type == 'd':
            for i in list_connections:
                if i['client_download'] == client:
                    list_connections.remove(i)
                    break
            client.close()
            print(f'{address} disconnected')
            print(f'Active connections: {threading.active_count() - 2}\n')
    except ValueError as error:
        print(f'ERROR1: {error}')
        client.close()
        print(f'{address} disconnected')
        print(f'Active connections: {threading.active_count() - 2}\n')


def intercept():
    server_chat.listen()
    print(f'Server listening on: {SERVER}')
    while True:
        try:
            client_chat, address_chat = server_chat.accept()
            client_download, address_download = server_chat.accept()
            dictionary = {
                'client_chat': client_chat,
                'client_download': client_download,
                'address_chat': address_chat,
                'address_download': address_download,
                'nickname': None,
                'availability_chat': None,
                'availability_download': None
            }
            list_connections.append(dictionary)
            thread_chat = CustomThread(client_chat, address_chat)
            thread_chat.start()
            thread_download = CustomThread(client_download, address_download)
            thread_download.start()
        except KeyboardInterrupt as error:
            print(f'ERROR2: {error}')
            break


def receive(client):
    try:
        message_length = client.recv(HEADER).decode()
        # print(f'Expected message of length = {message_length}')
        if message_length:
            message_length = int(message_length)
            full_message = ''
            while len(full_message) < message_length:
                remainder = message_length - len(full_message)
                if remainder < SIZE:
                    message = client.recv(remainder)
                    full_message += message.decode()
                else:
                    message = client.recv(SIZE)
                    full_message += message.decode()
            # print('\nlungime mesaj full primit = ' + str(len(full_message)))
            return full_message
    except ConnectionResetError as error:
        print(f'ERROR3: {error}')
        # client.close()
    except OSError as error:
        print(f'ERROR4: {error}')
        # client.close()


def send(client, is_bookshelf=0, is_file=0, filename=None, data=None):
    # Send a message with optional data over the socket.
    available = None
    index = None
    socket_type = None
    while True:
        for i in list_connections:
            if i['client_chat'] == client:
                available = i['availability_chat']
                index = list_connections.index(i)
                socket_type = 'c'
                break
            elif i['client_download'] == client:
                available = i['availability_download']
                index = list_connections.index(i)
                socket_type = 'd'
                break
        if available:
            # print(f'{address} is now available: {available} for {socket_type} >>>\n')
            try:
                if socket_type == 'c':
                    (list_connections[index])['availability_chat'] = False
                elif socket_type == 'd':
                    (list_connections[index])['availability_download'] = False
                message = {"is_bookshelf": is_bookshelf, "is_file": is_file, "filename": filename, "data": data}
                message = (json.dumps(message)).encode()
                message_length = len(message)  # length of encoded message
                # print('\nlungime mesaj full = ' + str(message_length))
                send_length = str(message_length).encode()  # encoded length
                padded_send_length = send_length + b" " * (HEADER - len(send_length))  # pad length
                client.send(padded_send_length)  # send padded length
                for i in range(0, message_length, SIZE):
                    # print('Lungime chunk = ' + str(len(message[i:i + SIZE])) + '\n')
                    chunk = message[i:i + SIZE]
                    client.send(chunk)
                # print(f'Sending the message of type {socket_type} to {address} finished <<<\n')
                if socket_type == 'c':
                    (list_connections[index])['availability_chat'] = True
                elif socket_type == 'd':
                    (list_connections[index])['availability_download'] = True
                break
            except BrokenPipeError as error:
                print(f'ERROR5: {error}')
            except ValueError as error:
                print(f'ERROR6: {error}')
                break
            except IndexError as error:
                print(f'ERROR7: {error}')
                break
            except OSError as error:
                print(f'ERROR8: {error}')
                break
        else:
            continue


def main():
    print('Binding the server...')
    bind()
    print('Establishing new connections...')
    intercept()


main()
