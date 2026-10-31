def create_table(metadata, table_name, columns):
    """Creates a new table"""

    if table_name in metadata:
        print(f"Таблица {table_name} уже существует. ")
        return metadata

    cols = {}
    for col in columns:
        if ":" not in col:
            print(f"Некорректное значение: {col}. Попробуйте снова.")
            return metadata

        key_value = col.split(":")

        if len(key_value) != 2:
            print(f"Некорректное значение: {key_value}. Попробуйте снова.")
            return metadata

        key, value = map(str.strip, key_value)

        if not key or not value:
            print("Отсутствует название колонки или тип данных. Попробуйте еще раз.")
            return metadata
        elif value not in ["int", "str", "bool"]:
            print(f"Некорректное значение: {value}. Попробуйте снова.")
            return metadata

        cols[key] = value

    if "ID" not in cols:
        cols = {"ID": "int", **cols}

    metadata[table_name] = cols

    display_cols = ", ".join(f"{key}:{value}" for key, value in cols.items())
    print(f"Таблица {table_name} успешно создана со столбцами: {display_cols}.")

    return metadata


def drop_table(metadata, table_name):
    """Drops an existing table"""

    if table_name in metadata:
        del metadata[table_name]
        print(f"Таблица {table_name} успешно удалена.")
    else:
        print(f"Таблица {table_name} не существует. ")

    return metadata


def list_tables(metadata):
    """Print the list of existing tables"""

    result = ", ".join(metadata.keys())
    print(f" - {result}")
