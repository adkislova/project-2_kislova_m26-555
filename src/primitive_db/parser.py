import re

_CONDITION_RE = re.compile(r"(\w+)\s*=\s*(.+)$")


def parse_where_clause(where_string):
    """Parses a WHERE clause like 'age = 28 AND name = "Sergei"' into a dict."""

    if not where_string or not where_string.strip():
        print("Ошибка: условие WHERE не задано. Попробуйте снова.")
        return None

    result = {}
    conditions = re.split(
        r"\s+AND\s+(?=\w+\s*=)", where_string.strip(), flags=re.IGNORECASE
    )

    for condition in conditions:
        match = _CONDITION_RE.match(condition.lstrip())
        if not match:
            print(
                f"Ошибка: Неверный формат условия: {condition.strip()}."
                " Попробуйте снова."
            )
            return None

        field_name = match.group(1)
        result[field_name] = _parse_value(match.group(2))

    return result


def parse_set_clause(set_string):
    """Parses a SET clause like 'age = 29, name = "Sergei"' into a dict."""

    if not set_string or not set_string.strip():
        print("Ошибка: условие SET не задано. Попробуйте снова.")
        return None

    result = {}
    fields = re.split(r",(?=\s*\w+\s*=)", set_string)

    for field in fields:
        match = _CONDITION_RE.match(field.strip())
        if not match:
            print(
                f"Ошибка: Неверный формат поля SET: {field.strip()}."
                " Попробуйте снова."
            )
            return None

        field_name = match.group(1)
        result[field_name] = _parse_value(match.group(2))

    return result


def _parse_value(value_str):
    """Converts a raw value to int, bool or str (quoted or bare words)."""

    if len(value_str) >= 2 and value_str[0] == value_str[-1] and value_str[0] in "\"'":
        return value_str[1:-1]

    lowered = value_str.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False

    try:
        return int(value_str)
    except ValueError:
        return value_str
