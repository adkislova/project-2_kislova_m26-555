import json
import os


def load_metadata(filepath):
    """Loads metadata from a JSON file"""

    json_data = {}

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = f.read().strip()
            if not data:
                json_data = {}
            else:
                json_data = json.loads(data)

    except FileNotFoundError:
        print(f"Файл не найден по пути: {filepath}")
    except json.JSONDecodeError:
        print(f"Файл метаданных повреждён (не является корректным JSON): {filepath}")
        return {}

    if not isinstance(json_data, dict):
        print(f"Ошибка: некорректный формат метаданных в файле: {filepath}")
        return {}
    return json_data


def save_metadata(filepath, data):
    """Saves metadata to a JSON file"""

    try:
        payload = json.dumps(data, ensure_ascii=False)
        encoded = payload.encode("utf-8")
    except UnicodeEncodeError:
        print("Ошибка сохранения метаданных: некорректные символы в данных.")
        return

    with open(filepath, "wb") as f:
        f.write(encoded)


def load_table_data(table_name):
    """Loads table data; a missing data file is treated as an empty table."""

    base_dir = os.path.dirname(os.path.abspath(__file__))
    filepath = os.path.join(base_dir, "data", f"{table_name}.json")
    filepath = os.path.abspath(filepath)
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = f.read().strip()
            json_data = json.loads(data) if data else {}
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        print(f"Файл данных повреждён (не является корректным JSON): {filepath}")
        print("Таблица считается пустой; следующая запись перезапишет файл.")
        return {}

    if not isinstance(json_data, dict):
        print(f"Ошибка: некорректный формат данных в файле: {filepath}")
        return {}
    return json_data


def save_table_data(table_name, data):
    """Saves table data to a JSON file"""

    base_dir = os.path.dirname(os.path.abspath(__file__))
    filepath = os.path.join(base_dir, "data", f"{table_name}.json")
    filepath = os.path.abspath(filepath)

    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    try:
        payload = json.dumps(data, ensure_ascii=False, indent=2)
        encoded = payload.encode("utf-8")
    except UnicodeEncodeError:
        print("Ошибка сохранения: некорректные символы в данных (кодировка ввода).")
        return

    with open(filepath, "wb") as f:
        f.write(encoded)

