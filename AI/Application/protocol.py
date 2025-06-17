import json

# Game mode actions
LEARNING_SHAPE = "LEARNING_SHAPE"
TEST_SHAPE = "TEST_SHAPE"
LEARNING_COLOR = "LEARNING_COLOR"
TEST_COLOR = "TEST_COLOR"

# Hardware actions
SET_LED = "SET_LED"
MOVE_SERVO = "MOVE_SERVO"
RAINBOW_LED = "RAINBOW_LED"

def create_command(action, payload=None):
    return json.dumps({
        'action': action,
        'payload': payload
    }).encode()

def parse_command(data):
    return json.loads(data.decode())
