import json

LEARNING_SHAPE = "LEARNING_SHAPE" 

def create_command(action, payload=None):
    return json.dumps({
        'action': action,
        'payload': payload
    }).encode()

def parse_command(data):
    return json.loads(data.decode())
