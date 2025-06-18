import json

LEARNING_SHAPE = "LEARNING_SHAPE"
SET_LED_COLOR = "SET_LED_COLOR"


def create_command(action, payload=None):
    return json.dumps({
        'action': action,
        'payload': payload
    }).encode()

def parse_command(data):
    return json.loads(data.decode())
