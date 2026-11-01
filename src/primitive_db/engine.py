import re
import shlex
from pathlib import Path

from prettytable import PrettyTable

from primitive_db.core import (
    convert_value,
    create_table,
    delete,
    drop_table,
    insert,
    list_tables,
    select,
    update,
)
from primitive_db.parser import parse_set_clause, parse_where_clause
from primitive_db.utils import (
    load_metadata,
    load_table_data,
    save_metadata,
    save_table_data,
)

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "db_meta.json"

NO_MATCHES_MESSAGE = "Записи, удовлетворяющие условию, не найдены."

INSERT_COMMAND_RE = re.compile(r"\s*insert\s+into\s+(\w+)\s+values\s*\((.*)\)\s*$")


def _parse_values(raw_values):
    """Splits the raw '(...)' payload of an INSERT command into separate values."""

    parts = []
    buffer = ""
    quote_char = None
    for char in raw_values:
        if quote_char:
            buffer += char
            if char == quote_char:
                quote_char = None
        elif char in ('"', "'"):
            quote_char = char
            buffer += char
        elif char == ",":
            parts.append(buffer.strip())
            buffer = ""
        else:
            buffer += char
    parts.append(buffer.strip())
    return parts


def _load_table(data, table_name):
    """Loads table data for an existing table, prints an error otherwise."""

    if table_name not in data:
        print(f"Таблица '{table_name}' не существует.")
        return None
    return load_table_data(table_name)


def _print_select_result(headers, data):
    """Displays the SELECT result in a nice format using PrettyTable."""

    if not data:
        print("Нет данных для отображения.")
        return

    table = PrettyTable()
    table.field_names = headers

    ordered_ids = sorted(data, key=lambda key: int(key) if str(key).isdigit() else 0)
    for record_id in ordered_ids:
        record = data[record_id]
        table.add_row([record_id] + [record.get(col, "") for col in headers[1:]])

    print(table)


def _convert_set_values(schema, set_clause):
    """Converts SET values to their column types, prints errors and returns None."""

    converted_set = {}
    for field, raw_value in set_clause.items():
        converted_set[field] = convert_value(schema[field], raw_value, column=field)
        if converted_set[field] is None:
            return None
    return converted_set


def run():
    """Runs the CLI loop to process user commands."""

    while True:
        data = load_metadata(DB_PATH)

        try:
            user_input = input(">>> Введите команду: ")
            args = shlex.split(user_input)
        except ValueError as error:
            print(f"Ошибка разбора команды: {error}. Попробуйте снова.")
            continue
        except (EOFError, KeyboardInterrupt):
            print("\nВыход из программы")
            break

        if not args:
            continue

        match args:

            case ["create_table", table_name, *columns]:
                if not columns:
                    print("Укажите хотя бы один столбец.")
                    continue
                metadata = create_table(data, table_name, columns)
                save_metadata(DB_PATH, metadata)

            case ["drop_table", table_name]:
                metadata = drop_table(data, table_name)
                save_metadata(DB_PATH, metadata)

            case ["list_tables"]:
                list_tables(data)

            case ["insert", "into", table_name, *_]:
                payload = INSERT_COMMAND_RE.match(user_input)
                if payload is None:
                    print(
                        "Некорректный синтаксис. Формат: "
                        "insert into <таблица> values (<значение1>, <значение2>, ...)"
                    )
                    continue

                new_data = insert(data, table_name, _parse_values(payload.group(2)))
                if new_data is not None:
                    save_table_data(table_name, new_data)

            case ["select", "from", table_name]:
                table_data = _load_table(data, table_name)
                if table_data is None:
                    continue
                _print_select_result(list(data[table_name]), select(table_data))

            case ["select", "from", table_name, "where", *where_parts]:
                if not where_parts:
                    print(
                        "Укажите условие: select from <таблица>"
                        " where <столбец> = <значение>"
                    )
                    continue
                table_data = _load_table(data, table_name)
                if table_data is None:
                    continue
                where_clause = parse_where_clause(" ".join(where_parts))
                if where_clause is None:
                    continue
                _print_select_result(
                    list(data[table_name]), select(table_data, where_clause)
                )

            case ["update", table_name, "set", *rest]:
                table_data = _load_table(data, table_name)
                if table_data is None:
                    continue
                if "where" not in rest:
                    print("Ошибка: после set должно быть условие where.")
                    continue

                idx = rest.index("where")
                set_clause = parse_set_clause(" ".join(rest[:idx]))
                where_clause = parse_where_clause(" ".join(rest[idx + 1:]))
                if set_clause is None or where_clause is None:
                    continue

                invalid_columns = [
                    field
                    for field in set_clause
                    if field == "ID" or field not in data[table_name]
                ]
                if invalid_columns:
                    bad_columns = ", ".join(invalid_columns)
                    print(f"Некорректные столбцы для update: {bad_columns}.")
                    continue

                converted_set = _convert_set_values(data[table_name], set_clause)
                if converted_set is None:
                    continue

                matched_data = select(table_data, where_clause)
                updated_data = update(table_data, converted_set, where_clause)
                changed_ids = [
                    record_id
                    for record_id, record in updated_data.items()
                    if record != table_data.get(record_id)
                ]
                if not matched_data:
                    print(NO_MATCHES_MESSAGE)
                    continue
                if not changed_ids:
                    matched_ids = ", ".join(matched_data)
                    print(
                        f"Записи найдены (ID: {matched_ids}),"
                        " но значения уже соответствуют новым."
                    )
                    continue

                save_table_data(table_name, updated_data)
                for record_id in changed_ids:
                    print(
                        f'Запись с ID={record_id} в таблице "{table_name}"'
                        " успешно обновлена."
                    )

            case ["delete", "from", table_name, "where", *where_parts]:
                if not where_parts:
                    print(
                        "Укажите условие: delete from <таблица>"
                        " where <столбец> = <значение>"
                    )
                    continue
                table_data = _load_table(data, table_name)
                if table_data is None:
                    continue
                where_clause = parse_where_clause(" ".join(where_parts))
                if where_clause is None:
                    continue
                remaining_data = delete(table_data, where_clause)
                deleted_ids = [
                    record_id
                    for record_id in table_data
                    if record_id not in remaining_data
                ]
                if not deleted_ids:
                    print(NO_MATCHES_MESSAGE)
                    continue

                save_table_data(table_name, remaining_data)
                for record_id in deleted_ids:
                    print(
                        f'Запись с ID={record_id} успешно удалена'
                        f' из таблицы "{table_name}".'
                    )

            case ["info", table_name]:
                table_data = _load_table(data, table_name)
                if table_data is None:
                    continue
                columns_info = ", ".join(
                    f"{key}:{value}" for key, value in data[table_name].items()
                )
                print(f"Таблица: {table_name}")
                print(f"Столбцы: {columns_info}")
                print(f"Количество записей: {len(table_data)}")

            case ["help"]:
                print_help()

            case ["exit"]:
                print("Выход из программы")
                break

            case _:
                known_commands = (
                    "insert", "select", "update", "delete", "info",
                    "create_table", "drop_table", "list_tables",
                )
                if args[0] in known_commands:
                    print(
                        f"Некорректный синтаксис команды '{args[0]}'."
                        " Попробуйте снова."
                    )
                else:
                    print(f"Функции {args[0]} нет. Попробуйте снова.")


def print_help():
    """Prints the help message for the current mode"""

    print("\n***Процесс работы с таблицей***")
    print("Функции:")
    print(
        "<command> create_table <имя_таблицы> <столбец1:тип> <столбец2:тип> .."
        " - создать таблицу"
    )
    print("<command> list_tables - показать список всех таблиц")
    print("<command> drop_table <имя_таблицы> - удалить таблицу")

    print("\n***Операции с данными***")
    print("Функции:")
    print(
        "<command> insert into <имя_таблицы> values (<значение1>, <значение2>, ...)"
        " - создать запись."
    )
    print(
        "<command> select from <имя_таблицы> where <столбец> = <значение>"
        " - прочитать записи по условию."
    )
    print("<command> select from <имя_таблицы> - прочитать все записи.")
    print(
        "<command> update <имя_таблицы> set <столбец1> = <новое_значение1>"
        " where <столбец_условия> = <значение_условия> - обновить запись."
    )
    print(
        "<command> delete from <имя_таблицы> where <столбец> = <значение>"
        " - удалить запись."
    )
    print("<command> info <имя_таблицы> - вывести информацию о таблице.")

    print("\nОбщие команды:")
    print("<command> exit - выход из программы")
    print("<command> help - справочная информация\n")
