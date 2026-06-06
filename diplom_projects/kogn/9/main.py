from typing import Dict, List, Any

def nine_level_enhanced_processor(
    queue: List[Dict[str, Any]],
    priority_map: Dict[str, int],
    default_priority: int = 1,
    max_depth: int = 3
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Обрабатывает очередь задач с расширенной логикой в else-ветках.
    Содержит 9 уровней вложенности.
    Возвращает словарь с категориями обработанных задач.
    """
    import copy
    processed = []
    low_priority_fallback = []
    unmapped_normalized = []
    non_list_converted = []
    non_dict_wrapped = []
    error_handled = []

    while queue:                                                      # уровень 1
        task = queue.pop(0)
        temp = copy.deepcopy(task)
        for field_name, field_value in task.items():                  # уровень 2
            if field_name in priority_map:                            # уровень 3 (if)
                p = priority_map[field_name]
                if p >= 5:                                            # уровень 4 (if)
                    if isinstance(field_value, list):                 # уровень 5 (if)
                        for sub_item in field_value:                  # уровень 6
                            if isinstance(sub_item, dict):            # уровень 7 (if)
                                try:                                  # уровень 8 (try)
                                    # Уровень 9 (if/else внутри try)
                                    if sub_item.get("active", False):
                                        sub_item["priority"] = p
                                        temp.setdefault("subtasks", []).append(sub_item)
                                    else:
                                        sub_item["priority"] = p - 2
                                        sub_item["reason"] = "inactive"
                                        temp.setdefault("inactive_subtasks", []).append(sub_item)
                                except (KeyError, TypeError) as e:    # уровень 8 (except)
                                    # Логика обработки ошибок – без увеличения глубины
                                    sub_item["error"] = str(e)
                                    error_handled.append(sub_item)
                            else:                                     # анти-уровень 7 – не-словарь
                                wrapped = {"value": sub_item, "priority": p, "type": "wrapped"}
                                temp.setdefault("wrapped_items", []).append(wrapped)
                                non_dict_wrapped.append(wrapped)
                    else:                                             # анти-уровень 5 – поле не список
                        # Преобразуем одиночное значение в список
                        converted_list = [field_value]
                        temp[field_name] = converted_list
                        non_list_converted.append({field_name: converted_list})
                else:                                                 # анти-уровень 4 – низкий приоритет
                    # Дополнительная проверка для увеличения глубины (уровень 5 в этой ветке)
                    if p < 1:                                         # уровень 5 в этой альтернативной ветке
                        adjusted = default_priority
                    else:
                        adjusted = p
                    # Внутри можно добавить ещё проверку (уровень 6), но не обязательно
                    temp["adjusted_priority"] = adjusted
                    low_priority_fallback.append({field_name: adjusted})
            else:                                                     # анти-уровень 3 – поле отсутствует в priority_map
                # Нормализация поля
                normalized_value = {
                    "original": field_value,
                    "assigned_priority": default_priority,
                    "defaulted": True
                }
                temp[field_name] = normalized_value
                unmapped_normalized.append({field_name: normalized_value})

        processed.append(temp)

    return {
        "processed_tasks": processed,
        "low_priority_adjustments": low_priority_fallback,
        "unmapped_fields": unmapped_normalized,
        "non_list_converted": non_list_converted,
        "non_dict_wrapped": non_dict_wrapped,
        "error_handled": error_handled
    }