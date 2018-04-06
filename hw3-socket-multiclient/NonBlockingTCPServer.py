import socket
import select
import signal
import sys
import datetime


class Server:
    server_port = 21350
    server_socket = None
    buffer_size = 2048
    outputs = []
    clients = {}

    def upper(self, message, client):
        return message.upper()

    def lower(self, message, client):
        return message.lower()

    def who_am_i(self, message, client):
        return "IP=" + self.clients[client]["address"][0] + " port=" + str(self.clients[client]["address"][1])

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
        connected_client = 0
        while True:
            try:
                (input_ready, output_ready, except_ready) = select.select(inputs, self.outputs, [], 1 * 10)  # select
            except select.error:
                break
            except socket.error:
                break

            for intr in input_ready:
                if intr == self.server_socket:
                    # Handle new client
                    (client_socket, client_address) = self.server_socket.accept()
                    print('Connection requested from', client_address)
                    connected_client += 1
                    inputs.append(client_socket)
                    self.outputs.append(client_socket)
                    self.clients[client_socket] = {
                        "id": connected_client,
                        "address": client_address
                    }
                    print("Client " +
                          str(self.clients[client_socket]["id"]) +
                          " connected. Number of connected clients = " +
                          str(len(self.outputs)))
                else:
                    # Handle other client
                    try:
                        data = intr.recv(self.buffer_size).decode("utf-8")
                        if data:
                            # Send message
                            msg = self.pars_cmd(data, intr)
                            intr.send(msg.encode("utf-8"))
                        else:
                            # Close leaving client
                            intr.close()
                            inputs.remove(intr)
                            self.outputs.remove(intr)
                            print("Client " +
                                  str(self.clients[intr]["id"]) +
                                  " disconnected. Number of connected clients = "
                                  + str(len(self.outputs)))
                    except socket.error as err:
                        # close if error
                        inputs.remove(intr)
                        self.outputs.remove(intr)

    def signal_handler(self, signum, frame):
        # Handle CTRL-c
        print("Shutting down server")
        self.server_socket.close()
        for outp in self.outputs:
            # close every client
            outp.close()
        sys.exit()

    def __init__(self):
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
