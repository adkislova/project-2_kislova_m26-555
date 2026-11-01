from primitive_db.constants import VALID_TYPES
from primitive_db.decorators import confirm_action, handle_db_errors, log_time
from primitive_db.utils import load_table_data, save_table_data


@handle_db_errors
def create_table(metadata, table_name, columns):
    """Creates a new table"""

    if not table_name.isidentifier():
        raise ValueError(f"некорректное имя таблицы: '{table_name}'")

    if table_name in metadata:
        raise ValueError(f"таблица {table_name} уже существует")

    cols = {}
    for col in columns:
        if ":" not in col or len(col.split(":")) != 2:
            raise ValueError(f"некорректное определение столбца: '{col}'")

        key, value = map(str.strip, col.split(":"))
        if not key or not value:
            raise ValueError(f"в столбце '{col}' нет названия или типа")
        if value not in VALID_TYPES:
            raise ValueError(f"тип '{value}' не поддерживается (int, str, bool)")

        cols[key] = value

    id_type = cols.pop("ID", "int")
    cols = {"ID": id_type, **cols}

    metadata[table_name] = cols

    display_cols = ", ".join(f"{key}:{value}" for key, value in cols.items())
    print(f"Таблица {table_name} успешно создана со столбцами: {display_cols}.")

    save_table_data(table_name, {})

    return metadata


@handle_db_errors
@confirm_action("удаление таблицы")
def drop_table(metadata, table_name):
    """Drops an existing table"""

    if table_name not in metadata:
        raise KeyError(table_name)

    del metadata[table_name]
    print(f"Таблица {table_name} успешно удалена.")

    return metadata


@handle_db_errors
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
    """Converts a value to the column type, raises ValueError on mismatch."""

    error_prefix = "некорректное значение"
    column_part = f" для столбца '{column}'" if column else ""

    if not isinstance(value, str):
        is_plain_int = isinstance(value, int) and not isinstance(value, bool)
        if expected_type == "int" and is_plain_int:
            return value
        if expected_type == "bool" and isinstance(value, int):
            return bool(value)
        raise ValueError(
            f"{error_prefix} {value!r}{column_part} (ожидается {expected_type})"
        )

    value = _strip_quotes(value)

    if expected_type == "int":
        try:
            return int(value)
        except ValueError:
            raise ValueError(
                f"{error_prefix} '{value}'{column_part} (ожидается int)"
            ) from None
    if expected_type == "bool":
        lowered = value.lower()
        if lowered in ("true", "1"):
            return True
        if lowered in ("false", "0"):
            return False
        raise ValueError(
            f"{error_prefix} '{value}'{column_part} (ожидается true/false)"
        )
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


@handle_db_errors
@log_time
def insert(metadata, table_name, values):
    """Creates a new record in the table, returns the table data (None on error)"""

    if table_name not in metadata:
        raise KeyError(table_name)

    table_schema = metadata[table_name]
    data_cols = [col for col in table_schema if col != "ID"]

    if len(values) != len(data_cols):
        expected = ", ".join(data_cols)
        raise ValueError(
            f"получено {len(values)} значений, ожидалось {len(data_cols)} "
            f"(столбцы: {expected}); все поля обязательны"
        )

    new_record = {
        col: convert_value(table_schema[col], raw_value, column=col)
        for col, raw_value in zip(data_cols, values)
    }

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


@handle_db_errors
@log_time
def select(table_data, where_clause=None):
    """Returns all records or only those matching the WHERE clause"""

    if where_clause is None:
        return table_data

    return {
        record_id: record
        for record_id, record in table_data.items()
        if _matches(record_id, record, where_clause)
    }


@handle_db_errors
def update(table_data, set_clause, where_clause):
    """Updates records matching the WHERE clause, returns the table data"""

    update_data = {record_id: dict(record) for record_id, record in table_data.items()}

    for record_id, record in update_data.items():
        if _matches(record_id, record, where_clause):
            for field, new_value in set_clause.items():
                record[field] = new_value

    return update_data


@handle_db_errors
@confirm_action("удаление записей")
def delete(table_data, where_clause):
    """Deletes records matching the WHERE clause, returns the remaining data"""

    return {
        record_id: record
        for record_id, record in table_data.items()
        if not _matches(record_id, record, where_clause)
    }
