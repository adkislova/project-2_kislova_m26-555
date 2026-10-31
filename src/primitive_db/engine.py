import shlex
from pathlib import Path

from primitive_db.core import create_table, drop_table, list_tables
from primitive_db.utils import load_metadata, save_metadata

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "db_meta.json"


def engine():
    print("Первая попытка запустить проект!")
    print("\n***")
    print("\n<command> exit - выйти из программы")
    print("\n<command> help - справочная информация")
    print("\nВведите команду: help")
    print("\n<command> exit - выйти из программы")
    print("\n<command> help - справочная информация")
    print("\nВведите команду: _")


def run():
    """Runs the CLI loop to process user comands"""

    while True:
        data = load_metadata(DB_PATH)
        user_input = input("Введите команду: ")
        args = shlex.split(user_input)

        if not args:
            continue

        match args:
            case ["create_table", table_name, *columns]:

                if ":" in table_name:
                    print("Укажите название таблицы.")
                    continue
                if not columns:
                    print("Укажите хотя бы один столбец.")
                    continue
                metadata = create_table(data, args[1], args[2:])
                save_metadata(DB_PATH, metadata)
            case ["drop_table", table_name]:
                metadata = drop_table(data, args[1])
                save_metadata(DB_PATH, metadata)
            case ["help"]:
                print_help()
            case ["list_tables"]:
                list_tables(data)
            case ["exit"]:
                print("Выход из программы")
                break
            case _:

                if args[0] == "create_table" or args[0] == "drop_table":
                    print("Укажите название таблицы")
                else:
                    print(f"Функции {args[0]} нет. Попробуйте снова.")
                continue


def print_help():
    """Prints the help message for the current mode."""

    print("\n***Процесс работы с таблицей***")
    print("Функции:")
    print("<command> create_table <имя_таблицы> <столбец1:тип> .. - создать таблицу")
    print("<command> list_tables - показать список всех таблиц")
    print("<command> drop_table <имя_таблицы> - удалить таблицу")

    print("\nОбщие команды:")
    print("<command> exit - выход из программы")
    print("<command> help - справочная информация\n")
