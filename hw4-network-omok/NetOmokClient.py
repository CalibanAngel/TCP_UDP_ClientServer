import socket
import argparse
import sys
import time


parser = argparse.ArgumentParser(description="Simple TCP client")


class Client:
    server_name = "nsl2.cau.ac.kr"
    server_port = 21350
    port_list = [21350, 31350, 41350, 51350]
    client_socket = None
    is_close = False

    def send(self, message):
        self.client_socket.send(message.encode("utf-8"))

    def receive(self):
        modified_message = self.client_socket.recv(2048)
        print("Reply from server:", modified_message.decode("utf-8"))

    def pars(self):
        inp = input("$> ")
        inp = inp.split(" ")
        cmd = ""
        msg = ""

        if len(inp) and len(inp[0]):
            if inp[0][0] == '\\':
                cmd = inp[0]
                msg = " ".join(inp[1:])
            elif inp[0][0] != '\\':
                cmd = '\msg'
                msg = " ".join(inp)

            if cmd == "\quit":
                # check if exist
                print("Bye bye~")
                self.is_close = True
        return cmd, msg

    def prompt(self):
        while self.is_close != True:
            try:
                cmd, msg = self.pars()

                if len(cmd):
                    self.send(cmd + " " + msg)
                    # ["\list", "\w", "\board", "\play", "\ss", "\gg", "\quite"]:
                else:
                    print("Please, enter a number between 1 and 5\n", file=sys.stderr)
            except KeyboardInterrupt:
                # CTRL-c catch
                print("Cyaa~~")
                self.client_socket.close()
                sys.exit()
        # close if exit
        self.client_socket.close()
        sys.exit()

    def __init__(self, server_name, server_port, nickname):
        self.nickname = nickname
        self.server_name = server_name
        self.server_port = server_port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((self.server_name, self.server_port))
        self.send("\\welcome " + self.nickname)
        print("The client is running on port", self.client_socket.getsockname()[1])


def parsing():
    parser.add_argument("nickname",
                        help="your name on the server",
                        type=str)
    parser.add_argument("--serverName",
                        help="the name of the server you want to connect",
                        type=str,
                        default="nsl2.cau.ac.kr")
    parser.add_argument("--serverPort",
                        help="the port of the server you want to connect",
                        type=int,
                        default=21350)


def main():
    parsing()
    args = parser.parse_args()
    client = Client(args.serverName, args.serverPort, args.nickname)
    client.prompt()


if __name__ == "__main__":
    main()
