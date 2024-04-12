# UPPER = constants
# lower = variables
import base64
import json
import socket
import threading
from tkinter import font
from tkinter import scrolledtext
import tkinter
from PIL import Image, ImageTk

HEADER = 256  # byte size of header
SIZE = 16384  # byte size of packages
PORT = 8080

# FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "D"
REQUEST_FILE = "R"
SET_NICKNAME = "N"
ICON = "files/classical-greek-temple.jpg"
BACKGROUND = "files/lighthousealexandria.jpg"
THEME = "#E8E8E8"
DEFAULT_SIZE = (600, 400)
DOWNLOAD_PATH = "downloaded"
bookshelf = []
chat_users = []
my_nickname = None


try:
    HOST_NAME = socket.gethostname()
    SERVER = socket.gethostbyname(HOST_NAME)  # host local IP address
except socket.gaierror:
    HOST_NAME = socket.gethostname()
    SERVER = HOST_NAME.split(".")[0].replace("-", ".")  # host local IP address

ADDRESS = (SERVER, PORT)
connected = False
send_flag = False

server_chat = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
server_download = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)


def send(command=None, data=None, nickname=None, filename=None):
    try:
        # Send a command with optional data over the socket.
        message = {
            "command": command,
            "data": data,
            "nickname": nickname,
            "filename": filename,
        }
        message = json.dumps(message).encode()
        message_length = len(message)  # length of encoded message
        # print('\nlungime mesaj full = ' + str(message_length))
        # encoded length
        send_length = str(message_length).encode()  # encoded length
        # pad length
        padded_send_length = send_length + b" " * (HEADER - len(send_length))
        # send padded length
        server_chat.send(padded_send_length)
        server_download.send(padded_send_length)
        for i in range(0, message_length, SIZE):
            # print('Lungime chunk = ' + str(len(message[i:i + SIZE])) + '\n')
            chunk = message[i : i + SIZE]
            server_chat.send(chunk)
            server_download.send(chunk)
    except OSError:
        return


def receive(server):
    global bookshelf
    try:
        message_length = server.recv(HEADER).decode()
        # print(f'Expected message of length = {message_length}')
        if message_length:
            message_length = int(message_length)
            full_message = ""
            while len(full_message) < message_length:
                remainder = message_length - len(full_message)
                if remainder < SIZE:
                    message = server.recv(remainder)
                    full_message += message.decode()
                else:
                    message = server.recv(SIZE)
                    full_message += message.decode()
                # print('\nlungime mesaj full primit = ' + str(len(full_message)))
            # Parse the received JSON message
            try:
                full_message = json.loads(full_message)
                is_bookshelf = full_message.get("is_bookshelf")
                is_file = full_message.get("is_file")
                filename = full_message.get("filename")
                data = full_message.get("data")
                # Handle the command
                if is_bookshelf:
                    bookshelf = data
                elif is_file:
                    try:
                        file = open(f"{DOWNLOAD_PATH}/{filename}", "xb")
                        data = base64.b64decode(data.encode())
                        file.write(data)
                        file.close()
                    except FileExistsError:
                        print("The file already exists!\n")
                else:
                    return data
            except json.JSONDecodeError:
                # Handle invalid JSON
                print("Error decoding JSON message: parsing failed!")
            except TypeError:
                # Handle invalid JSON
                print("Error decoding JSON message: wrong type!")
    except OSError:
        return


def write():
    global connected, send_flag
    while connected:
        if send_flag:
            text = chat_in.get("1.0", "end")
            chat_in.delete("1.0", "end")
            send_flag = False
        else:
            continue
        if text == "" or text.isspace():
            continue
        else:
            chat_out.config(state="normal")
            chat_out.insert("end", f"You({my_nickname}): {text}")
            chat_out.yview("end")
            chat_out.config(state="disabled")
            send(command=None, data=text)
            # print('\nMessage sent\n')
    server_chat.close()


def read(server):
    global connected
    while connected:
        try:
            received = receive(server)
            if received is None or received.isspace():
                continue
            else:
                print(received)
                chat_out.config(state="normal")
                chat_out.insert("end", received)
                chat_out.yview("end")
                chat_out.config(state="disabled")
        except OSError:
            pass
    server.close()


def main():
    global server_chat, server_download, chat_users
    server_chat = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
    server_chat.connect(ADDRESS)
    server_download = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
    server_download.connect(ADDRESS)
    receive(server_chat)
    chat_users = receive(server_chat)
    global connected
    connected = True
    # Threads
    read_thread = threading.Thread(target=read, args=(server_chat,))
    read_thread.start()
    read_thread = threading.Thread(target=read, args=(server_download,))
    read_thread.start()
    write_thread = threading.Thread(target=write)
    write_thread.start()
    # print(f'Threads open: {threading.active_count()-1}')
    print(f"\nAvailable files for download: {bookshelf}")
    print(f"Online chat users: {chat_users}\n")
    list_box.delete("0", "end")
    for book in bookshelf:
        list_box.insert("end", book)
    chat_out.config(state="normal")
    if not chat_users:
        chat_out.insert("end", "None at the moment\n")
    else:
        for user in chat_users:
            chat_out.insert("end", f'"{user}"\n')
    chat_out.insert("end", "\n")
    chat_out.config(state="disabled")


# # # GUI

# General
root = tkinter.Tk()
root.title("Alexandria")
root.geometry(f"{DEFAULT_SIZE[0]}x{DEFAULT_SIZE[1]}")


def prepare_image(name):
    old_extension = name.split(".")[-1]
    new_extension = "png"
    img = Image.open(name)
    prepared = name[: (len(name) - len(old_extension))] + new_extension
    img.save(prepared)
    return prepared


icon_image = prepare_image(ICON)
icon = tkinter.PhotoImage(file=icon_image)
root.iconphoto(True, icon)

# Background
background_image = prepare_image(BACKGROUND)

# Frames
# Main Frame
welcome_frame = tkinter.Frame(root)
welcome_frame.pack(fill=tkinter.BOTH, expand=True)
# Chat Frame
chat_frame = tkinter.Frame(root)
chat_frame.config(background=THEME)
chat_frame.place(x=0, y=0, relwidth=1, relheight=1)
# Request Frame
request_frame = tkinter.Frame(root)
request_frame.config(background=THEME)
request_frame.place(x=0, y=0, relwidth=1, relheight=1)
# Show Main Frame first
previous_frame = welcome_frame
welcome_frame.tkraise()

# # # Create Widgets

# # Labels

# Background Label of Welcome Frame
welcome_background_label = tkinter.Label(welcome_frame)
welcome_background_label.place(
    x=0, y=0, relwidth=1, relheight=1
)  # Place the label to cover the whole frame
# Background Label of Chat Frame
# chat_background_label = tkinter.Label(chat_frame)
# chat_background_label.place(x=0, y=0, relwidth=1, relheight=1)  # Place the label to cover the whole frame


# Welcome Frame Label

welcome_label = tkinter.Label(
    welcome_frame,
    text="Welcome to the\nVirtual Math Library of\nALEXANDRIA",
    font=font.Font(family="Bodoni 72 Oldstyle", size=22, weight="bold", slant="italic"),
    background=THEME,
    foreground="black",
    borderwidth=1,
    relief="raised",
)
welcome_label.place(relx=0.6, rely=0.1, relwidth=0.35, relheight=0.15)

# Chat Label

chat_label = tkinter.Label(
    chat_frame,
    text="CHAT",
    font=font.Font(family="Bodoni 72 Oldstyle", size=22, weight="bold", slant="italic"),
    background=THEME,
    foreground="black",
    borderwidth=1,
    relief="raised",
)
chat_label.place(relx=0.78, rely=0.06, relwidth=0.15, relheight=0.15)


# # Buttons


# Join Button
def command_join_button():
    chat_out.config(state="normal")
    chat_out.delete("1.0", "end")
    chat_out.config(state="disabled")

    def cleanup():
        global my_nickname, chat_users
        my_nickname = entry.get()
        nickname_popup.destroy()
        chat_out.config(state="normal")
        chat_out.insert(
            "end",
            f'Welcome, you joined the chat as "{my_nickname}"\n'
            f"The other chat members currently online are:\n",
        )
        chat_out.config(state="disabled")
        chat_frame.tkraise()
        if not connected:
            main()
            # print(f'Current number of open threads = {threading.active_count()-1}')
        send(command=SET_NICKNAME, nickname=my_nickname)

    nickname_popup = tkinter.Toplevel(root)
    nickname_popup.geometry("250x150")
    nickname_popup.resizable(False, False)
    nickname_popup.rowconfigure(0, weight=3)
    nickname_popup.rowconfigure(1, weight=1)
    nickname_popup.rowconfigure(2, weight=1)
    nickname_popup.columnconfigure(0, weight=1)
    nickname_popup.grab_set()
    label = tkinter.Label(
        nickname_popup,
        text="Choose a nickname: ",
        font=font.Font(
            family="Bodoni 72 Oldstyle", weight="bold", slant="italic", size=22
        ),
        background=THEME,
        foreground="black",
        borderwidth=1,
        relief="raised",
    )
    label.grid(row=0, column=0, sticky="wens", padx=5, pady=2)
    entry = tkinter.Entry(
        nickname_popup,
        font=font.Font(
            family="Bodoni 72 Oldstyle", weight="bold", slant="italic", size=20
        ),
        background=THEME,
        foreground="black",
        borderwidth=1,
        relief="raised",
        justify="center",
    )
    entry.grid(row=1, column=0, sticky="wens", padx=5, pady=2)
    button = tkinter.Button(
        nickname_popup,
        text="Ok",
        command=cleanup,
        font=font.Font(
            family="Bodoni 72 Oldstyle", weight="bold", slant="italic", size=18
        ),
        background=THEME,
        foreground="black",
        borderwidth=1,
        relief="raised",
    )
    button.grid(row=2, column=0, sticky="wens", padx=5, pady=2)


join_chat_button = tkinter.Button(
    welcome_frame,
    text="Join the Chat",
    font=font.Font(family="Bodoni 72 Oldstyle", size=14, slant="italic"),
    background="#E3E3E3",
    foreground="black",
    borderwidth=0.05,
    relief="raised",
    highlightthickness=0,
    command=command_join_button,
)
join_chat_button.place(relx=0.68, rely=0.33, relwidth=0.01, relheight=0.01)


# Request Button
def command_request_file():
    global previous_frame
    previous_frame = welcome_frame
    request_frame.tkraise()
    main()
    # print(f'open threads = {threading.active_count()-1}')


request_file_button = tkinter.Button(
    welcome_frame,
    text="Request a file",
    font=font.Font(family="Bodoni 72 Oldstyle", size=14, slant="italic"),
    background="#E3E3E3",
    foreground="black",
    borderwidth=0.05,
    relief="raised",
    highlightthickness=0,
    command=lambda: command_request_file(),
)
request_file_button.place(relx=0.68, rely=0.43, relwidth=0.01, relheight=0.01)


# Return Home Button (from Chat Frame)
def command_disconnect_chat():
    global connected
    send(command=DISCONNECT_MESSAGE)
    connected = False
    welcome_frame.tkraise()
    return


chat_return_button = tkinter.Button(
    chat_frame,
    text="Disconnect",
    font=font.Font(family="Bodoni 72 Oldstyle", size=14, slant="italic"),
    background="#E3E3E3",
    foreground="black",
    borderwidth=0.05,
    relief="raised",
    highlightthickness=0,
    command=command_disconnect_chat,
)
chat_return_button.place(relx=0.78, rely=0.4, relwidth=0.15, relheight=0.05)


# Send Message Button
def click_send():
    global send_flag
    send_flag = True
    return


send_button = tkinter.Button(
    chat_frame,
    text="Send",
    font=font.Font(family="Bodoni 72 Oldstyle", size=14, slant="italic"),
    background="#E3E3E3",
    foreground="black",
    borderwidth=0.05,
    relief="raised",
    highlightthickness=0,
    command=lambda: click_send(),
)
send_button.place(relx=0.78, rely=0.85, relwidth=0.15, relheight=0.05)


# Request Chat button
def command_request_file_chat():
    global previous_frame
    previous_frame = chat_frame
    request_frame.tkraise()


chat_request_file_button = tkinter.Button(
    chat_frame,
    text="Request a file",
    font=font.Font(family="Bodoni 72 Oldstyle", size=14, slant="italic"),
    background="#E3E3E3",
    foreground="black",
    borderwidth=0.05,
    relief="raised",
    highlightthickness=0,
    command=lambda: command_request_file_chat(),
)
chat_request_file_button.place(relx=0.78, rely=0.53, relwidth=0.15, relheight=0.05)


# Return Home Button (from Request Frame)
def command_request_return():
    if previous_frame == welcome_frame:
        global connected
        send(command=DISCONNECT_MESSAGE)
        connected = False
        previous_frame.tkraise()
    elif previous_frame == chat_frame:
        previous_frame.tkraise()


request_return_button = tkinter.Button(
    request_frame,
    text="Quit",
    font=font.Font(family="Bodoni 72 Oldstyle", size=14, slant="italic"),
    background="#E3E3E3",
    foreground="black",
    borderwidth=0.05,
    relief="raised",
    highlightthickness=0,
    command=lambda: command_request_return(),
)
request_return_button.place(relx=0.78, rely=0.4, relwidth=0.15, relheight=0.05)


# Download Button
def command_download_button():
    selected_index = list_box.curselection()
    if selected_index:
        selected_book = list_box.get(selected_index[0])
        send(command=REQUEST_FILE, filename=selected_book)


download_button = tkinter.Button(
    request_frame,
    text="Download",
    font=font.Font(family="Bodoni 72 Oldstyle", size=14, slant="italic"),
    background="#E3E3E3",
    foreground="black",
    borderwidth=0.05,
    relief="raised",
    highlightthickness=0,
    command=command_download_button,
)
download_button.place(relx=0.78, rely=0.3, relwidth=0.15, relheight=0.05)

# # Chat Scrolled Text
chat_out = tkinter.scrolledtext.ScrolledText(
    chat_frame,
    font=font.Font(family="Bodoni 72 Oldstyle", size=16, slant="italic"),
    background="#E3E3E3",
    foreground="black",
    borderwidth=0.5,
    relief="raised",
    border=True,
    highlightthickness=0,
    highlightcolor="black",
)
chat_out.place(relx=0.01, rely=0.01, relwidth=0.7, relheight=0.8)
chat_out.config(state="disabled")

# # Chat Text Input
chat_in = tkinter.Text(
    chat_frame,
    font=font.Font(family="Bodoni 72 Oldstyle", size=16, slant="italic"),
    background=THEME,
    foreground="black",
    borderwidth=0.5,
    relief="raised",
    border=True,
    highlightthickness=0,
    highlightcolor="black",
    insertofftime=500,
    insertbackground="black",
)
chat_in.place(relx=0.01, rely=0.85, relwidth=0.7, relheight=0.1)

# # Request List Box
list_box = tkinter.Listbox(
    request_frame,
    font=font.Font(family="Bodoni 72 Oldstyle", size=16, slant="italic"),
    background="#E3E3E3",
    foreground="black",
    borderwidth=0.5,
    relief="raised",
    border=True,
    highlightthickness=0,
    highlightcolor="black",
)
list_box.config(relief="raised")
scroll_bar = tkinter.Scrollbar(list_box)
list_box.place(relx=0.01, rely=0.01, relwidth=0.7, relheight=0.8)
scroll_bar.pack(side="right", fill="both")


def on_double_click(e):
    selected_index = list_box.curselection()
    if selected_index:
        selected_book = list_box.get(selected_index[0])
        send(command=REQUEST_FILE, filename=selected_book)


# # # Update widgets and image

# Avoid garbage collection by referencing the new PhotoImage object outside the scope of the Function
new_background = None


# Function
def update(e):
    global new_background  # Avoid garbage collection
    # Resize image
    updated_image = Image.open(background_image)

    def resize_image():
        resized_im = updated_image.resize((e.width, e.height), Image.LANCZOS)
        return resized_im

    resized = resize_image()
    new_background = ImageTk.PhotoImage(resized)
    welcome_background_label.config(image=new_background)
    # Resize and reposition the buttons and label + resize text
    button_width = 0.2 * e.width
    button_height = 0.06 * e.height
    label_height = 0.04 * e.height
    label_width = 0.04 * e.width
    join_chat_button.place_configure(width=button_width, height=button_height)
    request_file_button.place_configure(width=button_width, height=button_height)
    welcome_label.place_configure(height=label_height, width=label_width)
    send_button.place_configure(height=label_height, width=label_width)
    chat_return_button.place_configure(height=label_height, width=label_width)
    request_return_button.place_configure(height=label_height, width=label_width)
    chat_request_file_button.place_configure(height=label_height, width=label_width)
    chat_label.place_configure(height=label_height, width=label_width)
    chat_in.place_configure(height=label_height, width=label_width)
    chat_out.place_configure(height=label_height, width=label_width)
    download_button.place_configure(height=label_height, width=label_width)
    list_box.place_configure(height=label_height, width=label_width)
    # Resize the font size of the widgets
    font_size = int(0.035 * min(e.width, e.height))
    _font_ = ("Bodoni 72 Oldstyle", font_size, "italic")
    welcome_label.config(font=_font_)
    chat_label.config(font=_font_)
    join_chat_button.config(font=_font_)
    request_file_button.config(font=_font_)
    send_button.config(font=_font_)
    chat_return_button.config(font=_font_)
    request_return_button.config(font=_font_)
    chat_request_file_button.config(font=_font_)
    download_button.config(font=_font_)
    # list_box.config(font=_font_)
    # chat_in.config(font=_font_)
    # chat_out.config(font=_font_)


# Bind
welcome_frame.bind("<Configure>", update)
list_box.bind("<Double-1>", on_double_click)


# Close GUI Protocol
def stop():
    global connected
    try:
        send(command=DISCONNECT_MESSAGE)
        connected = False
    except OSError:
        pass
    root.destroy()
    exit(0)


root.protocol("WM_DELETE_WINDOW", stop)

# Loop
welcome_frame.mainloop()
