from primitive_db.utils import load_table_data, save_table_data


def create_table(metadata, table_name, columns):
    """Creates a new table"""

    if not table_name.isidentifier():
        print(f"Некорректное имя таблицы: '{table_name}'. Попробуйте снова.")
        return metadata

    if table_name in metadata:
        print(f"Таблица {table_name} уже существует.")
        return metadata

    cols = {}
    for col in columns:
        if ":" not in col:
            print(f"Некорректное значение: {col}. Попробуйте снова.")
            return metadata

        key_value = col.split(":")

        if len(key_value) != 2:
            print(f"Некорректное значение: {col}. Попробуйте снова.")
            return metadata

        key, value = map(str.strip, key_value)

        if not key or not value:
            print("Отсутствует название колонки или тип данных. Попробуйте еще раз.")
            return metadata
        elif value not in ["int", "str", "bool"]:
            print(f"Некорректный тип данных: {value}. Доступны: int, str, bool.")
            return metadata

        cols[key] = value

    id_type = cols.pop("ID", "int")
    cols = {"ID": id_type, **cols}

    metadata[table_name] = cols

    display_cols = ", ".join(f"{key}:{value}" for key, value in cols.items())
    print(f"Таблица {table_name} успешно создана со столбцами: {display_cols}.")

    save_table_data(table_name, {})

    return metadata


def drop_table(metadata, table_name):
    """Drops an existing table"""

    if table_name in metadata:
        del metadata[table_name]
        print(f"Таблица {table_name} успешно удалена.")
    else:
        print(f"Таблица {table_name} не существует.")

    return metadata


def list_tables(metadata):
    """Print the list of existing tables"""

    result = ", ".join(metadata.keys())
    print(f" - {result}")


def _strip_quotes(value):
    """Removes surrounding single/double quotes from a raw value"""

    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
        return value[1:-1]
    return value


def convert_value(expected_type, value, column=None):
    """Converts a value to the column type, prints an error and returns None."""

    error_prefix = "Ошибка: некорректное значение"
    column_part = f" для столбца '{column}'" if column else ""

    if not isinstance(value, str):
        is_plain_int = isinstance(value, int) and not isinstance(value, bool)
        if expected_type == "int" and is_plain_int:
            return value
        if expected_type == "bool" and isinstance(value, bool):
            return value
        print(f"{error_prefix} {value!r}{column_part} (ожидается {expected_type}).")
        return None

    value = _strip_quotes(value)

    if expected_type == "int":
        try:
            return int(value)
        except ValueError:
            print(f"{error_prefix} '{value}'{column_part} (ожидается int).")
            return None
    if expected_type == "bool":
        lowered = value.lower()
        if lowered in ("true", "1"):
            return True
        if lowered in ("false", "0"):
            return False
        print(f"{error_prefix} '{value}'{column_part} (ожидается true/false).")
        return None
    return value


def _matches(record_id, record, where_clause):
    """Checks whether a record satisfies the WHERE clause (ID is the record key)"""

    for field, expected_value in where_clause.items():
        if field == "ID":
            try:
                actual_value = int(record_id)
            except ValueError:
                return False
        elif field in record:
            actual_value = record[field]
        else:
            return False

        if isinstance(actual_value, str) and isinstance(expected_value, str):
            if actual_value.strip() != expected_value.strip():
                return False
        elif actual_value != expected_value:
            return False

    return True


def insert(metadata, table_name, values):
    """Creates a new record in the table, returns the table data (None on error)"""

    if table_name not in metadata:
        print(f"Таблица '{table_name}' не существует.")
        return None

    table_schema = metadata[table_name]
    data_cols = [col for col in table_schema if col != "ID"]

    if len(values) != len(data_cols):
        expected = ", ".join(data_cols)
        print(
            f"Некорректное количество значений: получено {len(values)}, "
            f"ожидалось {len(data_cols)} (столбцы: {expected}). Все поля обязательны."
        )
        return None

    new_record = {}
    for col, raw_value in zip(data_cols, values):
        converted = convert_value(table_schema[col], raw_value, column=col)
        if converted is None:
            return None
        new_record[col] = converted

    table_data = load_table_data(table_name)

    existing_ids = []
    for key in table_data:
        try:
            existing_ids.append(int(key))
        except ValueError:
            continue
    new_id = max(existing_ids) + 1 if existing_ids else 1

    table_data[str(new_id)] = new_record
    print(f'Запись с ID={new_id} успешно добавлена в таблицу "{table_name}".')

    return table_data


def select(table_data, where_clause=None):
    """Returns all records or only those matching the WHERE clause"""

    if where_clause is None:
        return table_data

    return {
        record_id: record
        for record_id, record in table_data.items()
        if _matches(record_id, record, where_clause)
    }


def update(table_data, set_clause, where_clause):
    """Updates records matching the WHERE clause, returns the table data"""

    update_data = {record_id: dict(record) for record_id, record in table_data.items()}

    for record_id, record in update_data.items():
        if _matches(record_id, record, where_clause):
            for field, new_value in set_clause.items():
                record[field] = new_value

    return update_data


def delete(table_data, where_clause):
    """Deletes records matching the WHERE clause, returns the remaining data"""

    return {
        record_id: record
        for record_id, record in table_data.items()
        if not _matches(record_id, record, where_clause)
    }
