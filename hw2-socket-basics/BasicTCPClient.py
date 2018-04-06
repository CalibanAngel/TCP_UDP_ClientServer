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
    menu = """<Menu>
1) convert text to UPPER-case
2) convert text to LOWER-case
3) get my IP address and port number
4) get server time
5) exit\n"""

    def prompt(self):
        while True:
            try:
                cmd = input(self.menu + "Input option: ")
                msg = ""
                if len(cmd.split()) == 1 and cmd in ["1", "2", "3", "4", "5"]:
                    # check if only option
                    if cmd in ["1", "2"]:
                        # check if sentence is need
                        msg = input("Input Sentence: ")
                    message = cmd + " " + msg
                    if cmd == "5":
                        # check if exist
                        print("Bye bye~")
                        break

                    start_time = time.time()  # start time
                    self.client_socket.send(message.encode("utf-8"))
                    modified_message = self.client_socket.recv(2048)
                    elapsed_time = time.time() - start_time  # get the response time
                    print("Reply from server:", modified_message.decode("utf-8"))
                    print("Response time: ", str(int(elapsed_time * 1000)) + " ms\n")
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

    def __init__(self, server_name, server_port):
        self.server_name = server_name
        self.server_port = server_port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((self.server_name, self.server_port))
        print("The client is running on port", self.client_socket.getsockname()[1])


def parsing():
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
    client = Client(args.serverName, args.serverPort)
    client.prompt()


if __name__ == "__main__":
    main()
