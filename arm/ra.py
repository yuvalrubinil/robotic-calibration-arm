from connection import Connection
import json

cc = Connection("0.0.0.0", 65432)
cc.wait_camera_connection()
_json = cc.receive_data()

with open('output.txt', 'w') as output_file:
    output_file.write(json.dumps(_json))
