import json


def load_metadata(filepath):
    """Loads metadata from a JSON file"""

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = f.read().strip()
            if not data:
                json_data = {}
            else:
                json_data = json.loads(data)

    except FileNotFoundError:
        print(f"Файл не найден по пути: {filepath}")
    return json_data


def save_metadata(filepath, data):
    """Saves metadata to a JSON file"""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f)
