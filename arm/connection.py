import socket
import json

BUFFER = 1024

class Connection():

    def __init__(self, arm_host, arm_port):
        self.arm_host = arm_host
        self.arm_port = arm_port
        self.acc_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.acc_socket.bind((self.arm_host, self.arm_port))
        self.conn_socket, self.camera_addr = None, None

    def wait_camera_connection(self):
        self.acc_socket.listen(1)
        self.conn_socket, self.camera_addr = self.acc_socket.accept()

    def receive_data(self):
        received = ""
        while "\n" not in received:
            data = self.conn_socket.recv(BUFFER)
            if not data:
                raise ConnectionError("camera disconnected unexpectedly")
            received += data.decode('utf-8')
        
        received = received.strip() # remove '\n' at the end
        return json.loads(received)
    
    def close(self):
        if self.conn_socket:
            self.conn_socket.close();


