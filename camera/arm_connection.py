import socket
import json


class ArmConnection():

    def __init__(self, arm_host, arm_port):
        self.arm_host = arm_host
        self.arm_port = arm_port
        self.conn_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect_arm(self):
        self.conn_socket.connect((self.arm_host, self.arm_port))

    def send(self, _json):
        str_json = json.dumps(_json) + '\n' # \n to mark the end of json
        data = str_json.encode('utf-8')
        self.conn_socket.sendall(data)

    def close(self):
        self.conn_socket.close();
