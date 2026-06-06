from typing import Any


def find_deep_nested_key(
    data: dict[str, Any],
    target_key: str,
    max_depth: int = 3
) -> Any | None:
    stack = [(data, 0)]
    while stack:                       
        obj, depth = stack.pop()
        if depth > max_depth:
            continue
        if isinstance(obj, dict):
            for k, v in obj.items():                     
                if k == target_key:                     
                    return v
                if isinstance(v, (dict, list)):
                    stack.append((v, depth + 1))        
        elif isinstance(obj, list):
            for idx, item in enumerate(obj):           
                if isinstance(item, (dict, list)):
                    stack.append((item, depth + 1))
    return None