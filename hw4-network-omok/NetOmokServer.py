# QUIEF Hippolyte - 50171350

import socket
import select
import signal
import sys
import datetime


def find_client_by_nickname(clients, nickname):
    client = None
    for index, item in enumerate(clients):
        if item.nickname == nickname:
            client = item
    return client


def find_client_by_socket(clients, c_socket):
    client = None
    for index, item in enumerate(clients):
        if item.socket == c_socket:
            client = item
    return client


class Client:
    nickname = "toto"

    def set_nickname(self, nickname):
        self.nickname = nickname

    def __init__(self, c_socket, c_address, c_id):
        self.socket = c_socket
        self.address = c_address
        self.id = c_id


class Server:
    server_port = 21350
    server_socket = None
    buffer_size = 2048
    outputs = []
    inputs = []
    clients = []

    def chat(self, message, client):
        message = client.nickname + " " + message
        for sock in self.outputs:
            sock.send(message.encode("utf-8"))
        return ""

    def welcome(self, message, client):
        client.set_nickname(message)
        message = client.nickname + " has join the room"
        for sock in self.outputs:
            sock.send(message.encode("utf-8"))
        return "welcome " + client.nickname + " to net-omok chat room at " + "IP SOCKET" + ". You are " + str(client.id) + "th user"

    def nickname(self, message, client):
        old_nick = client.nickname
        client.set_nickname(message)
        return old_nick + " is now named " + client.nickname

    def list(self, message, client):
        pass

    def whisper(self, message, client):
        pass

    def board(self, message, client):
        pass

    def ask_play(self, message, client):
        pass

    def surrender(self, message, client):
        pass

    def play(self, message, client):
        pass

    def exit(self, message, client):
        return "Cyaa~"

    def pars_cmd(self, data, client):
        tmp = data.lstrip().split(' ', 1)
        cmd = tmp[0]
        msg = ""
        if len(tmp) >= 2:
            msg = tmp[1]
        # dictionary of server cmd --> no switch/case in Python :)
        cmd_list = {
            "\msg": self.chat,
            "\welcome": self.welcome,
            "\\nickname": self.nickname,
            "\list": self.list,
            "\w": self.whisper,
            "\\board": self.board,
            "\play": self.ask_play,
            "\ss": self.play,
            "\gg": self.surrender,
            "\quit": self.exit,
        }
        if cmd not in cmd_list:
            return "Invalid command"
        func = cmd_list[cmd]
        return func(msg, client)

    def handle_new_client(self, intr, connected_client):
        (client_socket, client_address) = self.server_socket.accept()
        # print('Connection requested from', client_address)
        self.inputs.append(client_socket)
        self.outputs.append(client_socket)

        self.clients.append(Client(client_socket, client_address, connected_client))

    def serve(self):
        self.inputs = [self.server_socket]
        self.outputs = []
        connected_client = 0

        while True:
            try:
                (input_ready, output_ready, except_ready) = select.select(self.inputs, self.outputs, [], 1 * 10)  # select
            except select.error:
                break
            except socket.error:
                break

            for intr in input_ready:
                if intr == self.server_socket:
                    # Handle new client
                    self.handle_new_client(intr, connected_client)
                    connected_client += 1
                else:
                    # Handle other client
                    try:
                        data = intr.recv(self.buffer_size).decode("utf-8")
                        client = find_client_by_socket(self.clients, intr)
                        if data:
                            # Send message
                            msg = self.pars_cmd(data, client)
                            intr.send(msg.encode("utf-8"))
                        else:
                            # Close leaving client
                            intr.close()
                            self.inputs.remove(intr)  # Remove client form input and output and clients
                            self.outputs.remove(intr)
                            print("Client " +
                                  str(client.nickname) +
                                  " disconnected. Number of connected clients = "
                                  + str(len(self.outputs)))
                            # del self.clients[intr]  # TODO
                    except socket.error as err:
                        # close if error
                        self.inputs.remove(intr)
                        self.outputs.remove(intr)

    def signal_handler(self, signum, frame):
        # Handle CTRL-c
        print("Shutting down server")
        self.server_socket.close()
        for outp in self.outputs:
            # close every client
            print("Client " +
                  str(self.clients[outp]["id"]) +
                  " disconnected. Number of connected clients = "
                  + str(len(self.clients) - 1))
            del self.clients[outp]
            outp.close()
        sys.exit(0)

    def __init__(self):
        # init the server socket
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.server_socket.bind(('', self.server_port))
        except socket.error as msg:
            print("Bind failed.", str(msg), file=sys.stderr)
            sys.exit()
        self.server_socket.listen(1)
        print("The server is ready to receive on port", self.server_port)
        # Handle ctrl-c
        signal.signal(signal.SIGINT, self.signal_handler)


def main():
    Server().serve()


if __name__ == "__main__":
    main()
