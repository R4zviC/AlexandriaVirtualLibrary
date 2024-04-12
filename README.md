Virtual library of mathematics related contents made up from a server and clients.

The server is unique and allows multiple connections through TCP, with threaded handling of each client via two sockets: one for downloading files from the library, the other for exchanging chats with other clients connected to the server.

The clients can run on different PCs or local networks and connect to the server knowing its IP address. The information exchange between client and server is mediated by a friendly GUI on the client side.

# Setup and Running Instructions

## Prerequisites

Before you begin, ensure you have Python installed on your machine. This project is tested on Python 3.9. It might work with other versions but compatibility is not guaranteed.

## Clone the Repository

First, clone the repository to your local machine using Git:

```
git clone https://github.com/R4zviC/AlexandriaVirtualLibrary.git
cd AlexandriaVirtualLibrary
```

## Setup the Python Environment

To set up the Python virtual environment and install all required dependencies, follow these steps:

Unix-like Systems (Linux, macOS)

```
# Run the setup script (bash)
bash setup_environment.sh
```

Windows

```
# Run the setup script (batch)
setup_environment.bat
```

This will create a virtual environment in the venv directory within your project folder and install all necessary packages as listed in requirements.txt.

## Activate the Environment

Make sure to activate the virtual environment before running the application.

Unix-like Systems

```
source venv/bin/activate
```

Windows

```
.\venv\Scripts\activate
```

## Run the Application

### Start the Server

To start the server component of the chat application, run:

```
python3 server.py  # Use python server.py on Windows if python3 alias is not set
```

### Start the Client

Open another terminal session, activate the environment as shown above, and run:

```
python3 client.py  # Use python client.py on Windows if python3 alias is not set
```

### Using the Application

Once both the server and the client are running:

The server will listen on the configured port and accept incoming connections.
On the client side, follow the on-screen prompts to connect to the server, send messages, and use the chat functionalities.
Exiting the Application
To exit, you can simply close the client window or use the exit option within the client's interface. To stop the server, use Ctrl+C in the terminal where the server is running.

# Notes

If you encounter any issues with running the scripts, ensure they have executable permissions (chmod +x setup_environment.sh on Unix-like systems).
