# QUIEF Hippolyte - 50171350

import socket
import select
import signal
import sys
import datetime


def remove_client(clients, client):
    idx = -1
    for index, item in enumerate(clients):
        if item.socket == client.socket:
            idx = index
    if idx != -1:
        del clients[idx]


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


class Omok:
    ROW = 10
    COL = 10
    turn = 0
    count = 0
    win = 0

    def print_board(self):
        print("   ", end="")
        for j in range(0, self.COL):
            print("%2d" % j, end="")

        print()
        print("  ", end="")
        for j in range(0, 2 * self.COL + 3):
            print("-", end="")

        print()
        for i in range(0, self.ROW):
            print("%d |" % i, end="")
            for j in range(0, self.COL):
                c = self.board[i][j]
                if c == 0:
                    print(" +", end="")
                elif c == 1:
                    print(" 0", end="")
                elif c == 2:
                    print(" @", end="")
                else:
                    print("ERROR", end="")
            print(" |")

        print("  ", end="")
        for j in range(0, 2 * self.COL + 3):
            print("-", end="")

        print()

    def check_win(self, x, y):
        last_stone = self.board[x][y]
        start_x, start_y, end_x, end_y = x, y, x, y

        # check x
        while (start_x - 1 >= 0 and
               self.board[start_x - 1][y] == last_stone):
            start_x -= 1
        while (end_x + 1 < self.ROW and
               self.board[(end_x + 1)][y] == last_stone):
            end_x += 1
        if end_x - start_x + 1 >= 5:
            return last_stone

        # check y
        start_x, start_y, end_x, end_y = x, y, x, y
        while (start_y - 1 >= 0 and
               self.board[x][start_y - 1] == last_stone):
            start_y -= 1
        while (end_y + 1 < self.COL and
               self.board[x][end_y + 1] == last_stone):
            end_y += 1
        if end_y - start_y + 1 >= 5:
            return last_stone

        # check diag 1
        start_x, start_y, end_x, end_y = x, y, x, y
        while (start_x - 1 >= 0 and start_y - 1 >= 0 and
               self.board[start_x - 1][start_y - 1] == last_stone):
            start_x -= 1
            start_y -= 1
        while (end_x + 1 < self.ROW and end_y + 1 < self.COL and
               self.board[end_x + 1][end_y + 1] == last_stone):
            end_x += 1
            end_y += 1
        if end_y - start_y + 1 >= 5:
            return last_stone

        # check diag 2
        start_x, start_y, end_x, end_y = x, y, x, y
        while (start_x - 1 >= 0 and end_y + 1 < self.COL and
               self.board[start_x - 1][end_y + 1] == last_stone):
            start_x -= 1
            end_y += 1
        while (end_x + 1 < self.ROW and start_y - 1 >= 0 and
               self.board[end_x + 1][start_y - 1] == last_stone):
            end_x += 1
            start_y -= 1
        if end_y - start_y + 1 >= 5:
            return last_stone
        return 0

    def play(self, x, y):
        if x < 0 or y < 0 or x >= self.ROW or y >= self.COL:
            return "error, out of bound!"
        elif self.board[x][y] != 0:
            return "error, already used!"

        if self.turn == 0:
            self.board[x][y] = 1
        else:
            self.board[x][y] = 2

        # os.system("clear")
        self.print_board()

        win = self.check_win(x, y)
        if win != 0:
            return "player %d wins!" % win

        self.count += 1
        if self.count == self.ROW * self.COL:
            return
        self.turn = (self.turn + 1) % 2

    def reset(self):
        pass

    def __init__(self):
        self.board = [[0 for row in range(self.ROW)] for col in range(self.COL)]
        x, y = None, None


class Game:
    players = []

    def set_player_1(self, client):
        self.players[0] = client

    def set_player_2(self, client):
        self.players[1] = client

    def __init__(self):
        self.game = Omok()
        self.players.append(None)
        self.players.append(None)


class Client:
    nickname = "toto"

    def display(self):
        return str(self.nickname) + " " + str(self.address[0]) + " " + str(self.address[1])

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
    game = None

    def send(self, message, sock, cmd):
        sock.send((cmd + " " + message).encode("utf-8"))

    def broadcast(self, message, cmd):
        for sock in self.outputs:
            sock.send((cmd + " " + message).encode("utf-8"))

    def chat(self, message, client, cmd):
        message = "[" + client.nickname + "]: " + message
        self.broadcast(message, cmd)

    def welcome(self, message, client, cmd):
        client.set_nickname(message)
        message = client.nickname + " has join the room"
        self.send("welcome " + client.nickname + " to net-omok chat room at " + "IP SOCKET" + ". You are " + str(client.id + 1) + "th user",
                  client.socket, cmd)
        self.broadcast(message, cmd)

    def nickname(self, message, client, cmd):
        old_nick = client.nickname
        client.set_nickname(message)
        self.broadcast(old_nick + " is now named " + client.nickname, cmd)

    def list(self, message, client, cmd):
        msg = ""
        for idx, item in enumerate(self.clients):
            msg += str(idx) + ") " + item.display() + "\n"
        self.send(msg, client.socket, cmd)

    def whisper(self, message, client, cmd):
        msg = message.split(" ", 1)
        w_client = find_client_by_nickname(self.clients, msg[0])
        self.send("[whisper from" + client.nickname + "]: " + msg[1], w_client.socket, cmd)
        self.send("[whisper to" + w_client.nickname + "]: " + msg[1], client.socket, cmd)

    def board(self, message, client, cmd):  # TODO
        pass

    def ask_play(self, message, client, cmd):
        if self.game:
            self.send("A game is currently running, wait until it finish to create a new one", client.socket, cmd)
        self.game = Game()
        w_client = find_client_by_nickname(self.clients, message)
        self.game.set_player_1(client)
        self.broadcast(client.nickname + " asked to play to " + w_client.nickname, cmd)
        self.send(client.nickname + " wants to play with you, agree? [y/n]", w_client.socket, cmd)

    def join(self, message, client, cmd):
        if message in ["y", "n"] and self.game.players[0]:
            if message == "y":
                self.broadcast(client.nickname + " accepted to play with " + self.game.players[0].nickname, cmd)
                self.game.set_player_2(client)
            elif message == "n":
                self.broadcast(self.game.players[0].nickname + " refused to play with " + client.nickname, cmd)
                self.game = None
        else:
            self.send(self.game.players[0].nickname + " wants to play with you, agree? [y/n]", client.socket, "\play")

    def surrender(self, message, client, cmd):
        player_2 = None
        if client.nickname == self.game.players[0].nickname:
            player_2 = self.game.players[1]
        else:
            player_2 = self.game.players[0]
        self.game = Game()
        self.broadcast(client.nickname + " surrender ! " + player_2.nickname + " won the game !", cmd)

    def play(self, message, client, cmd):  # TODO
        pass

    def exit(self, message, client, cmd):
        self.broadcast(client.nickname + " just leave", cmd)
        self.send("Cyaa~", client.socket, cmd)
        remove_client(self.clients, client)

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
            "\join": self.join,
            "\ss": self.play,
            "\gg": self.surrender,
            "\quit": self.exit,
        }
        if cmd not in cmd_list:
            return "Invalid command"
        func = cmd_list[cmd]
        return func(msg, client, cmd)

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
                            self.pars_cmd(data, client)
                            # intr.send((msg + "\n").encode("utf-8"))
                        else:
                            # Close leaving client
                            intr.close()
                            self.inputs.remove(intr)  # Remove client form input and output and clients
                            self.outputs.remove(intr)
                            print("Client " +
                                  str(client.nickname) +
                                  " disconnected. Number of connected clients = "
                                  + str(len(self.outputs)))
                            remove_client(self.clients, client)
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
            client = find_client_by_socket(self.clients, outp)
            print("Client " +
                  str(client.nickname) +
                  " disconnected. Number of connected clients = "
                  + str(len(self.clients) - 1))
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
