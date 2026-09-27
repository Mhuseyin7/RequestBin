import copy
from typing import Any

def _path_get(value: Any, path: str) -> Any:
    current = value
    for key in path.split("."):
        if not isinstance(current, dict) or key not in current: return None
        current = current[key]
    return current
def _path_set(value: dict, path: str, item: Any) -> None:
    keys = path.split("."); current = value
    for key in keys[:-1]: current = current.setdefault(key, {})
    current[keys[-1]] = item
def matches(condition: dict, headers: dict[str, str], body: Any) -> bool:
    if not condition: return True
    source = headers if condition.get("source") == "header" else body
    return _path_get(source, condition.get("path", "")) == condition.get("equals")
def apply(body: Any, headers: dict[str, str], transforms: list[dict]) -> tuple[Any, dict[str, str]]:
    body, headers = copy.deepcopy(body), copy.deepcopy(headers)
    for item in transforms:
        operation = item.get("op")
        if operation == "add_header": headers[str(item["name"])] = str(item["value"])
        elif operation == "remove_header": headers.pop(str(item["name"]), None)
        elif operation == "set_field" and isinstance(body, dict): _path_set(body, str(item["path"]), item.get("value"))
        elif operation == "rename_field" and isinstance(body, dict):
            value = _path_get(body, str(item["from"]));
            if value is not None: _path_set(body, str(item["to"]), value)
    return body, headers
