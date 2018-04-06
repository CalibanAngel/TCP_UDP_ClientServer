import socket
import select
import signal
import sys
import datetime


class Server:
    server_port = 21350
    server_socket = None
    buffer_size = 2048

    def upper(self, message, client):
        return message.upper()

    def lower(self, message, client):
        return message.lower()

    def who_am_i(self, message, client):
        return "IP=" + client[0] + " port=" + str(client[1])

    def what_time_is_it(self, message, client):
        return str(datetime.datetime.now())

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
            "1": self.upper,
            "2": self.lower,
            "3": self.who_am_i,
            "4": self.what_time_is_it,
            "5": self.exit,
        }
        if cmd not in cmd_list:
            return "Invalid command"
        func = cmd_list[cmd]
        return func(msg, client)

    def serve(self):
        inputs = [self.server_socket]
        self.outputs = []
        while True:
            try:
                (input_ready, output_ready, except_ready) = select.select(inputs, self.outputs, [], 1 * 60)  # select
            except select.error:
                break
            except socket.error:
                break

            for intr in input_ready:
                try:
                    (data, client_address) = intr.recvfrom(self.buffer_size)
                    if data:
                        # Send message
                        msg = self.pars_cmd(data.decode("utf-8"), client_address)
                        intr.sendto(msg.encode("utf-8"), client_address)
                    else:
                        # Close leaving client
                        intr.close()
                except socket.error as err:
                    pass

    def signal_handler(self, signum, frame):
        # Handle CTRL-c
        print("Shutting down server")
        self.server_socket.close()
        sys.exit()

    def __init__(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.server_socket.bind(('', self.server_port))
        except socket.error as msg:
            print("Bind failed.", str(msg), file=sys.stderr)
            sys.exit()
        # self.server_socket.listen(1)
        print("The server is ready to receive on port", self.server_port)
        signal.signal(signal.SIGINT, self.signal_handler)  # Handle CTRL-c


def main():
    Server().serve()


if __name__ == "__main__":
    main()
