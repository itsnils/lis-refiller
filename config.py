import json

def load(filepath='/home/pi/Refiller/config.json'):
    with open(filepath, "r") as f:
        return json.load(f)

def save(data, filepath='/home/pi/Refiller/config.json'):
    with open(filepath, "w") as f:
        json.dump(data, f, indent=4)

