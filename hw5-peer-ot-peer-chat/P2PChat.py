import argparse
import socket
import sys
import select
import threading
import signal
import pickle
from enum import Enum

parser = argparse.ArgumentParser(description="Peer-to-peer chat")
server_t = None
ui_t = None


def parsing():
    parser.add_argument("nodeId",
                        help="your id on the server, must be a number 1 and 4",
                        type=int)
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


def find_client_by_id(clients, node_id):
    for key, client in enumerate(clients):
        if client.node.port == nodes[node_id].port:
            return key, client
    return -1, None


def count_handled_client(clients):
    handled = 0
    for client in clients:
        if client.client_type == ClientType.HANDLED:
            handled += 1
    return handled


def count_init_client(clients):
    init = 0
    for client in clients:
        if client.client_type == ClientType.INIT:
            init += 1
    return init


class ClientType(Enum):
    HANDLED = 1
    INIT = 2


class Node:
    def set_nickname(self, nickname):
        self.nickname = nickname

    def set_ip(self, ip):
        self.ip = ip

    def __init__(self, port):
        self.ip = None
        self.nickname = ""
        self.port = port


nodes = {
    "1": Node(21350),
    "2": Node(31350),
    "3": Node(41350),
    "4": Node(51350)
}


class Packet:
    def serialize(self):
        return pickle.dumps({
            "cmd": self.cmd,
            "sender": self.sender,
            "data": self.data,
            "id": self.id,
            "creator": self.creator
        })

    def __init__(self, cmd, sender, data, id, creator):
        self.cmd = str(cmd)
        self.sender = sender
        self.data = data
        self.id = id
        self.creator = creator


class Client:
    def __init__(self, node, client_type):
        self.node = node
        self.client_type = client_type


class Server(threading.Thread):
    buffer_size = 1024
    last_packets = []
    clients = []
    packet_id = 0

    def kill(self):
        self.broadcast(nodes[self.node_id].nickname, "EXIT")
        print("EXIT")
        self.running = False
        self.server_socket.close()

    def send(self, message, cmd, node):
        if self.server_socket.fileno() == -1:
            return
        packet = Packet(cmd, self.node_id, message, self.packet_id, self.node_id)
        self.packet_id += 1
        self.server_socket.sendto(packet.serialize(), (node.ip, node.port))

    def broadcast(self, message, cmd):
        if self.server_socket.fileno() == -1:
            return
        packet = Packet(cmd, self.node_id, message, self.packet_id, self.node_id)
        self.packet_id += 1
        for client in self.clients:
            self.server_socket.sendto(packet.serialize(), (client.node.ip, client.node.port))

    def transfer_packet(self, packet):
        packet.sender = self.node_id
        for client in self.clients:
            self.server_socket.sendto(packet.serialize(), (client.node.ip, client.node.port))

    def is_new_packet(self, packet):
        if len(self.last_packets) == 0:
            return True
        for old in self.last_packets:
            if old.id == packet.id and old.creator == packet.creator:
                return False
            return True

    def receive_from(self, sock):
        (data, client_address) = sock.recvfrom(self.buffer_size)
        packet = None
        if data:
            packet = pickle.loads(data)
            packet = Packet(packet["cmd"], packet["sender"], packet["data"], packet["id"], packet["creator"])
        # print("[packet]: ", packet["cmd"], packet["sender"], packet["data"], packet["creator"])
        return packet

    def exit(self, packet):
        (id, client) = find_client_by_id(self.clients, packet.creator)
        if id == -1 or not client:
            return
        print("[server]: " + packet.data + " disconnected")
        del self.clients[id]
        self.init_connection()

    def accept_connection(self, packet):
        node = nodes[packet.creator]
        node.set_nickname(packet.data)
        self.clients.append(Client(node, ClientType.INIT))
        print("[server]: connection establish with " + node.nickname)

    def refused_connection(self, packet):
        print("[server]: connection refused by " + packet.data)

    def receive_message(self, packet):
        # print("receive_message")
        if self.is_new_packet(packet):
            self.last_packets.append(packet)
            print(packet.data)
            self.transfer_packet(packet)

    def handle_connection(self, packet):
        if count_handled_client(self.clients) < 2:
            # print("handle connection", packet.sender)
            nodes[packet.creator].set_nickname(packet.data)
            self.clients.append(Client(nodes[packet.creator], ClientType.HANDLED))
            self.send(self.nickname, "CONNECT", nodes[packet.creator])
            print("[server]: connection establish with " + packet.data)
            return
        self.send(self.nickname, "NOT_CONNECT", nodes[packet.creator])
        print("[server]: connection refused to " + packet.data)

    def parse_cmd(self, packet):
        if not packet:
            return None
        cmd_list = {
            "EXIT": self.exit,
            "CONNECT": self.accept_connection,
            "ASK_CONNECT": self.handle_connection,
            "NOT_CONNECT": self.refused_connection,
            "MSG": self.receive_message
        }
        if packet.cmd not in cmd_list:
            return
        func = cmd_list[packet.cmd]
        return func(packet)

    def init_connection(self):
        for node_id, node in nodes.items():
            if node_id != self.node_id and count_init_client(self.clients) < 2 and node.ip and node.port:
                # print("init connection", node_id)
                self.send(self.nickname, "ASK_CONNECT", node)

    def run(self):
        self.init_connection()
        while not self.stopper.is_set() or self.running:
            try:
                packet = self.receive_from(self.server_socket)
                if packet:
                    self.parse_cmd(packet)
                # elif not packet:
                #     print("test")
                #     self.kill()
            except:
                self.kill()
                break
        sys.exit(0)

    def __init__(self, nickname, server_name, node_id, stopper):
        super().__init__()
        self.stopper = stopper
        self.running = True
        self.nickname = nickname
        self.server_name = server_name
        self.node_id = str(node_id)

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.server_socket.bind(('', nodes[self.node_id].port))
        except socket.error as msg:
            print("Bind failed.", str(msg), file=sys.stderr)
            sys.exit()
        print("The server is ready to receive on port", nodes[self.node_id].port)


class UI:
    def kill(self):
        self.running = False
        self.server.kill()

    def connect(self):
        self.server.init_connection()

    def run(self):
        while not self.stopper.is_set() or self.running:
            line = input()
            print("jacky", line)

            if line:
                print("jacky", line)
                if line.split()[0] == "\quit":
                    self.kill()
                    break
                elif line.split()[0] == "\connect":
                    self.connect()
                else:
                    self.server.broadcast("[" + self.nickname + "]: " + line, "MSG")
        print("ui exit")
        sys.exit(0)

    def __init__(self, nickname, server, stopper):
        self.stopper = stopper
        self.running = True
        self.nickname = nickname
        self.server = server
        self.run()


class SignalHandler:
    # The stop event that's shared by this handler and threads.
    stopper = None

    def __init__(self, stopper, lock):
        self.stopper = stopper
        self.lock = lock

    def __call__(self, signum, frame):
        # Get the threads
        global server_t
        global ui_t

        self.stopper.set()  # Send the event
        print("signal", ui_t)
        if ui_t:
            ui_t.kill()
        else:
            sys.exit()
        print("Shutting down server")


def main():
    global server_t
    global ui_t

    stopper = threading.Event()  # Create event to handle ctrl-c
    lock = threading.Lock()  # Create mutex to access threads
    handler = SignalHandler(stopper, lock)  # Handle ctrl-c
    signal.signal(signal.SIGINT, handler)

    parsing()
    args = parser.parse_args()
    for node_id, node in nodes.items():
        node.set_ip(args.serverName)
    nodes[str(args.nodeId)].set_nickname(args.nickname)
    server_t = Server(args.nickname, args.serverName, args.nodeId, stopper)
    ui_t = UI(args.nickname, server_t, stopper)
    print("tmp", ui_t)

    server_t.start()
    server_t.join()
    return 0


if __name__ == "__main__":
    main()
