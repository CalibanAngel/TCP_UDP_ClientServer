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
        board = "   "
        for j in range(0, self.COL):
            board += ("%2d" % j)

        board += "\n"
        board += "  "
        for j in range(0, 2 * self.COL + 3):
            board += "-"

        board += "\n"
        for i in range(0, self.ROW):
            board += ("%d |" % i)
            for j in range(0, self.COL):
                c = self.board[i][j]
                if c == 0:
                    board += " +"
                elif c == 1:
                    board += " 0"
                elif c == 2:
                    board += " @"
                else:
                    board += "ERROR"
            board += " |\n"

        board += "  "
        for j in range(0, 2 * self.COL + 3):
            board += "-"

        board += "\n"
        return board

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

    def play(self, x, y, player_name):
        if x < 0 or y < 0 or x >= self.ROW or y >= self.COL:
            return "[server]: error, out of bound!"
        elif self.board[x][y] != 0:
            return "[server]: error, already used!"

        if self.turn == 0:
            self.board[x][y] = 1
        else:
            self.board[x][y] = 2

        win = self.check_win(x, y)
        if win != 0:
            return ""  # player_name win

        self.count += 1
        if self.count == self.ROW * self.COL:
            return ""  # can play
        self.turn = (self.turn + 1) % 2
        return ""

    def is_win(self):
        return self.win

    def reset(self):
        pass

    def __init__(self):
        self.board = [[0 for row in range(self.ROW)] for col in range(self.COL)]


class Game:
    players = []
    turn_time = 10

    def is_player_turn(self, client):
        player_id = -1
        for index, item in enumerate(self.players):
            if item.socket == client.socket:
                player_id = index
        return player_id == self.game.turn

    def get_player_turn(self):
        return self.players[self.game.turn]

    def is_player(self, client):
        if client.nickname == self.players[0].nickname or client.nickname == self.players[1].nickname:
            return True
        return False

    def how_long_game(self):
        return datetime.datetime.now() - self.time

    def get_other_player(self, client):
        if client.nickname == self.players[0].nickname:
            return self.players[1]
        elif client.nickname == self.players[1].nickname:
            return self.players[0]
        return None

    def set_player_1(self, client):
        self.players[0] = client

    def set_player_2(self, client):
        self.players[1] = client

    def __init__(self):
        self.game = Omok()
        self.time = datetime.datetime.now()
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

    # send message to sock user
    def send(self, message, sock, cmd):
        sock.send((cmd + " " + message).encode("utf-8"))

    # send message to all user
    def broadcast(self, message):
        for sock in self.outputs:
            sock.send(("\msg" + " " + message).encode("utf-8"))

    # chat
    def chat(self, message, client, cmd):
        message = "[" + client.nickname + "]: " + message
        self.broadcast(message)

    # use when a user is connect for the first time
    def welcome(self, message, client, cmd):
        client.set_nickname(message)
        message = "[server]: " + client.nickname + " has join the room"
        self.send("[server]: welcome %s to net-omok chat room at %s %s. You are %s th user" % (client.nickname, str(client.address[0]), str(client.address[1]), str(client.id + 1)),
                  client.socket, cmd)
        self.help(message, client, '\help')
        self.broadcast(message)

    # change the nickname
    def nickname(self, message, client, cmd):
        old_nick = client.nickname
        client.set_nickname(message)
        self.broadcast("[server]: " + old_nick + " is now named " + client.nickname)

    # get the list of all users
    def list(self, message, client, cmd):
        msg = "[server]: \n"
        for idx, item in enumerate(self.clients):
            msg += str(idx) + ") " + item.display() + "\n"
        self.send(msg, client.socket, cmd)

    # send a private message
    def whisper(self, message, client, cmd):
        msg = message.split(" ", 1)
        w_client = find_client_by_nickname(self.clients, msg[0])
        if not w_client:  # check if user exist
            self.send("[server]: Cannot find user " + message + ". Use < \list > to see the users", client.socket, "\msg")
            return
        self.send("[whisper from" + client.nickname + "]: " + msg[1], w_client.socket, cmd)
        self.send("[whisper to" + w_client.nickname + "]: " + msg[1], client.socket, cmd)

    # send the board to a specific user
    def board(self, message, client, cmd):
        self.send(self.game.game.print_board(), client.socket, cmd)
        self.send("it's " + self.game.get_player_turn(client).nickname + " turn", client.socket, cmd)

    # send the board to every users
    def board_broadcast(self, client):
        self.broadcast(self.game.game.print_board())
        self.broadcast("[server]: it's " + self.game.get_player_turn(client).nickname + " turn")

    # ask a user to play a game
    def ask_play(self, message, client, cmd):
        if self.game:  # check if a game is not start
            self.send("[server]: Cannot make play request", client.socket, "\msg")
            return
        w_client = find_client_by_nickname(self.clients, message)
        if not w_client:  # check if user exist
            self.send("[server]: Cannot find user " + message + ". Use < \list > to see the users", client.socket, "\msg")
            return
        self.game = Game()  # create a new game
        self.game.set_player_1(client)  # set the first user of the game
        self.broadcast("[server]: " + client.nickname + " asked to play to " + w_client.nickname)
        self.send("[server]: " + client.nickname + " wants to play with you, agree? [y/n]", w_client.socket, cmd)

    # answer of the asked-to-play user
    def join(self, message, client, cmd):
        if message in ["y", "n"] and self.game.players[0]:
            if message == "y":
                self.broadcast("[server]: " + client.nickname + " accepted to play with " + self.game.players[0].nickname)
                self.game.set_player_2(client)  # set the second user of the game
                self.board_broadcast(client)  # send board to every user
            elif message == "n":
                self.broadcast("[server]: " + self.game.players[0].nickname + " refused to play with " + client.nickname)
                self.game = None  # destroy the game
        else:  # if answer different from y or n
            self.send("[server]: " + self.game.players[0].nickname + " wants to play with you, agree? [y/n]", client.socket, "\play")

    # surrender the game
    def surrender(self, message, client, cmd):
        if not self.game.is_player(client):  # check if the user is a player
            self.send("[server]: you are not a player during this game", client.socket, cmd)
            return
        player_2 = self.game.get_other_player(client)  # get the other player
        self.game = None  # destroy the game
        self.broadcast("[server]: " + client.nickname + " surrender ! " + player_2.nickname + " won the game !")

    # play a stone
    def play(self, message, client, cmd):
        if not self.game:  # check if the game exist
            self.send("[server]: there is not game started, start one with < \play <nickname> >", client.socket, cmd)
            return
        if not self.game.is_player(client):  # check if the user is a player
            self.send("[server]: you are not a player during this game", client.socket, cmd)
            return
        if not self.game.is_player_turn(client):  # check if the player can play
            self.send("[server]: it's not your turn to play", client.socket, cmd)  # try to play when it's not your turn
            return

        cord = message.split()
        if len(cord) != 2:  # check if coordinates are giver
            self.send("[help]: \ss <x> <y> with <x> and <y> are number", client.socket, cmd)  # wrong command
            return
        try:  # check if coordinates are number
            x = int(cord[0])
            y = int(cord[1])
        except ValueError:
            self.send("[help]: \ss <x> <y> with <x> and <y> are number", client.socket, cmd)  # wrong command
            return

        msg = self.game.game.play(x, y, client.nickname)
        if len(msg):  # check if can play
            self.send(msg, client.socket, cmd)  # print if error
            return

        self.broadcast("[server]: " + client.nickname + " played on (" + cord[0] + ", " + cord[1] + ")")
        self.board_broadcast(client)  # send to every users the play
        if self.game.game.is_win():
            player_2 = self.game.get_other_player(client)
            self.broadcast("[server]: " + client.nickname + " win ! Don't cry " + player_2.nickname + ", you will won next time ;)\n End of the game, you can now start a new one")
            self.game = None

    # help command
    def help(self, message, client, cmd):
        msg = """
HELP:
    \help => show the list of command
    \\nickname <username> => changer nickname
    \list => show list of user
    \w <username> <msg> => send private message to <username>
    \\board => print the board
    \play <username> => ask <username> to play
    \ss <x> <y> => if you are playing, put a stone on (<x>, <y>)
    \gg => if you are playing, you surrender
    \quit => close the client
        """
        self.send(msg, client.socket, cmd)

    def exit(self, message, client, cmd):
        self.inputs.remove(client.socket)
        self.outputs.remove(client.socket)
        remove_client(self.clients, client)
        self.broadcast("[server]: " + client.nickname + " just leave")
        self.send("Cyaa~", client.socket, cmd)
        client.socket.close()


    # parse received command
    def pars_cmd(self, data, client):
        tmp = data.lstrip().split(' ', 1)
        cmd = tmp[0]
        msg = ""
        if len(tmp) >= 2:
            msg = tmp[1]
        # dictionary of server cmd --> no switch/case in Python :)
        cmd_list = {
            "\help": self.help,
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
            return "Invalid command, use < \help > for more detail"
        func = cmd_list[cmd]
        return func(msg, client, cmd)

    # handle new connection
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
            if self.game:  # timer of the game
                if self.game.how_long_game().total_seconds() >= self.game.turn_time and not self.game.players[1]:
                    self.game = None
                    self.broadcast("[server]: You can now start a new game")
                if self.game.how_long_game().total_seconds() >= self.game.turn_time and self.game.players[1]:
                    player = self.game.get_player_turn()
                    player_2 = self.game.get_other_player()
                    self.broadcast("[server]: " + player.nickname + " took to much to play, so he looses the game. " + player_2.nickname + " win !")
                    self.game = None
                    self.broadcast("[server]: You can now start a new game")

            try:
                (input_ready, output_ready, except_ready) = select.select(self.inputs, self.outputs, [], 1 * 1)  # select
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
                        else:
                            # Close leaving client
                            self.send("Server shutting down", intr, '\quit')
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
        for outp in self.outputs:
            # close every client
            client = find_client_by_socket(self.clients, outp)
            print("Client " +
                  str(client.nickname) +
                  " disconnected. Number of connected clients = "
                  + str(len(self.clients) - 1))
            outp.close()
        self.server_socket.close()
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
