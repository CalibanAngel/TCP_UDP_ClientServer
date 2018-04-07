# QUIEF Hippolyte - 50171350

import socket
import select
import signal
import sys
import datetime
import threading

threads = {}


class ClientThread(threading.Thread):
    # The client information
    buffer_size = 2048
    ip = ""
    port = 0
    sock = None
    id = 0
    lock = None

    # An event that tells the thread to stop
    stopper = None

    def __init__(self, client_socket, client_address, stopper, id, lock):
        super().__init__()
        self.ip = client_address[0]
        self.port = client_address[1]
        self.sock = client_socket
        self.stopper = stopper
        self.id = id
        self.lock = lock

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

    def shutdown(self):
        self.sock.shutdown(socket.SHUT_RDWR)

    def run(self):
        # Get the threads
        global threads
        while not self.stopper.is_set():  # Continue until receive stopper event
            try:
                data = self.sock.recv(self.buffer_size).decode("utf-8")
                if data:
                    # Send message
                    msg = self.pars_cmd(data, self.sock)
                    self.sock.send(msg.encode("utf-8"))
                else:
                    # Close leaving client and print
                    self.sock.close()
                    # Delete the thread from the threads array
                    self.lock.acquire()
                    try:
                        if threads and threads[self.id]:
                            print("Client " +
                                  str(threads[self.id]["id"]) +
                                  " disconnected. Number of connected clients = "
                                  + str(len(threads) - 1))
                            del threads[self.id]
                    finally:
                        self.lock.release()
                    break
            except socket.error as err:
                # close if error
                self.sock.close()
                # Delete the thread from the threads array
                self.lock.acquire()
                try:
                    if threads and threads[self.id]:
                        del threads[self.id]
                finally:
                    self.lock.release()
        self.sock.close()
        sys.exit()


class SignalHandler:
    # The stop event that's shared by this handler and threads.
    stopper = None

    def __init__(self, stopper, lock):
        self.stopper = stopper
        self.lock = lock

    def __call__(self, signum, frame):
        # Get the threads
        global threads
        print("Shutting down server")
        self.stopper.set()  # Send the event
        self.lock.acquire()
        try:
            # Shutdown each thread
            for idx, obj in threads.items():
                obj["thread"].shutdown()
        finally:
            self.lock.release()
        sys.exit(0)


class Server:
    server_port = 21350
    server_socket = None

    def serve(self):
        # Get the threads
        global threads
        stopper = threading.Event()  # Create event to handle ctrl-c
        lock = threading.Lock()  # Create mutex to access threads
        handler = SignalHandler(stopper, lock)  # Handle ctrl-c
        signal.signal(signal.SIGINT, handler)
        connected_client = 0  # Total of client who connect

        while not stopper.is_set():
            if self.server_socket:
                (client_socket, client_address) = self.server_socket.accept()  # Accept a new connection
                # print('Connection requested from', client_address)
                connected_client += 1
                new_thread = ClientThread(client_socket, client_address, stopper, connected_client, lock)  # Create thread
                lock.acquire()  # Lock the access to threads
                try:
                    # Add the thread to the threads array
                    threads[connected_client] = {
                        "id": connected_client,
                        "thread": new_thread
                    }
                finally:
                    lock.release()  # Release access to threads
                # Start the thread
                new_thread.start()
                print("Client " +
                      str(connected_client) +
                      " connected. Number of connected clients = " +
                      str(threading.active_count() - 1))

    def __init__(self):
        # Init the server socket
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
