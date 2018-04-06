import socket
import select
import signal
import sys
import datetime
import threading


class ClientThread(threading.Thread):
    # The client information
    buffer_size = 2048
    ip = ""
    port = 0
    sock = None
    id = 0

    # An event that tells the thread to stop
    stopper = None

    def __init__(self, client_socket, client_address, stopper, id):
        super().__init__()
        self.ip = client_address[0]
        self.port = client_address[1]
        self.sock = client_socket
        self.stopper = stopper
        self.id = id

    def upper(self, message, client):
        return message.upper()

    def lower(self, message, client):
        return message.lower()

    def who_am_i(self, message, client):
        return "IP=" + self.ip + " port=" + str(self.port)

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

    def run(self):
        while not self.stopper.is_set():
            print("pwet", self.stopper.is_set())
            try:
                data = self.sock.recv(self.buffer_size).decode("utf-8")
                if data:
                    # Send message
                    print("IP=" + self.ip + " PORT=" + str(self.port) + " MESSAGE=" + data)
                    msg = self.pars_cmd(data, self.sock)
                    self.sock.send(msg.encode("utf-8"))
                else:
                    # Close leaving client
                    print("Client " +
                          str(self.id) +
                          " disconnected. Number of connected clients = "
                          + str(threading.active_count() - 2))
                    self.sock.close()
                    break
            except socket.error as err:
                # close if error
                self.sock.close()
        print("I exit")
        self.sock.close()
        sys.exit()


class SignalHandler:
    # The stop event that's shared by this handler and threads.
    stopper = None

    def __init__(self, stopper):
        self.stopper = stopper

    def __call__(self, signum, frame):
        print("LOLOLOLOLOL" + str(self.stopper.is_set()))
        self.stopper.set()
        print("LOLOLOLOLOL" + str(self.stopper.is_set()))
        sys.exit(0)


class Server:
    server_port = 21350
    server_socket = None
    threads = []

    def serve(self):
        stopper = threading.Event()
        handler = SignalHandler(stopper)
        signal.signal(signal.SIGINT, handler)
        connected_client = 0

        while not stopper.is_set():
            if self.server_socket:
                (client_socket, client_address) = self.server_socket.accept()
                new_thread = ClientThread(client_socket, client_address, stopper, connected_client)
                self.threads.append({
                    "id": connected_client,
                    "thread": new_thread
                })
                new_thread.start()
                print("Client " + str(connected_client) + " connected. Number of connected clients = " + str(threading.active_count() - 1))
                connected_client += 1

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


def main():
    Server().serve()


if __name__ == "__main__":
    main()
