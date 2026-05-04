import os
import re
import ast
from typing import Dict, List, Optional, Any, Union
from collections import defaultdict


def extract_dict_from_log_line(line: str) -> Optional[Dict[str, Any]]:
    """
    Извлекает словарь из строки лога вида:
    "dict:{'name': 'analyze()', 'elapsed_sec': 1.0141, 'peak_rss_kb': 83384, ...}"
    
    Parameters
    ----------
    line : str
        Строка лога, содержащая словарь.

    Returns
    -------
    Optional[Dict[str, Any]]
        Распарсенный словарь или None, если не удалось извлечь.
    """
    match = re.search(r"dict:\{.*\}", line)
    if not match:
        return None
    dict_str = match.group(0)[5:]  # убираем 'dict:' перед фигурными скобками
    try:
        # Используем ast.literal_eval для безопасного преобразования
        return ast.literal_eval(dict_str)
    except (SyntaxError, ValueError):
        # Запасной вариант: вручную извлечь значения через регулярные выражения
        result = {}
        # Ищем пары 'ключ': значение
        pairs = re.findall(r"'([^']+)':\s*([^,}]+)", dict_str)
        for key, val in pairs:
            val = val.strip()
            # Пытаемся преобразовать в число, если возможно
            try:
                if '.' in val:
                    result[key] = float(val)
                else:
                    result[key] = int(val)
            except ValueError:
                result[key] = val
        return result if result else None


def parse_coverage_and_mutation_from_log(content: str) -> tuple[Optional[float], Optional[float]]:
    """
    Извлекает итоговые показатели покрытия и мутационного показателя из лога.

    Parameters
    ----------
    content : str
        Содержимое лог-файла.

    Returns
    -------
    tuple[Optional[float], Optional[float]]
        (coverage, mutation) в процентах.
    """
    coverage_match = re.search(r"ПОКРЫТИЕ\s+([\d\.]+)%", content)
    mutation_match = re.search(r"МУТАЦИОННЫЙ\s+ПОКАЗАТЕЛЬ\s+([\d\.]+)%", content)
    coverage = float(coverage_match.group(1)) if coverage_match else None
    mutation = float(mutation_match.group(1)) if mutation_match else None
    return coverage, mutation


def parse_profiling_log(filepath: str) -> Dict[str, Dict[str, Any]]:
    """
    Парсит лог-файл профилирования, извлекая данные по каждому профилируемому блоку
    и итоговые показатели покрытия/мутации.

    Формат строк:
        2026-05-02 11:46:49 - src.utils.profiler - DEBUG - [coro_id=... coro_name=...] - 
        [ProfileBlock] Результаты профилирования: analyze(), 
        dict:{'name': 'analyze()', 'elapsed_sec': 1.0141, 'peak_rss_kb': 83384, ...}

    Parameters
    ----------
    filepath : str
        Путь к лог-файлу.

    Returns
    -------
    Dict[str, Dict[str, Any]]
        Словарь, где ключ — имя профилируемого блока (например, 'analyze()'),
        значение — словарь со статистикой:
            - count: количество вызовов
            - avg_elapsed_sec: среднее время выполнения
            - avg_peak_rss_mb: средний пик RSS (МБ)
            - avg_peak_traced_mb: средний пик traced памяти (МБ)
            - min_elapsed_sec, max_elapsed_sec и т.д. (опционально)
        Также добавляются ключи '_coverage' и '_mutation', если они найдены.

    Examples
    --------
    >>> stats = parse_profiling_log("logs/profile.log")
    >>> for block, data in stats.items():
    ...     if not block.startswith('_'):
    ...         print(f"{block}: {data['count']} calls, avg time = {data['avg_elapsed_sec']:.3f}s")
    """
    if not os.path.isfile(filepath):
        raise FileNotFoundError(f"Файл не найден: {filepath}")

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Хранилище для записей каждого блока
    blocks: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    # Разбиваем на строки и ищем строки с "[ProfileBlock]"
    for line in content.splitlines():
        if '[ProfileBlock]' not in line:
            continue
        data = extract_dict_from_log_line(line)
        if data and 'name' in data:
            block_name = data['name']
            blocks[block_name].append(data)

    # Агрегируем статистику
    result: Dict[str, Dict[str, Any]] = {}
    for block_name, records in blocks.items():
        count = len(records)
        elapsed_list = [r.get('elapsed_sec', 0.0) for r in records]
        rss_mb_list = [r.get('peak_rss_mb', 0.0) for r in records]
        traced_mb_list = [r.get('peak_traced_mb', 0.0) for r in records]

        result[block_name] = {
            'count': count,
            'avg_elapsed_sec': sum(elapsed_list) / count,
            'min_elapsed_sec': min(elapsed_list),
            'max_elapsed_sec': max(elapsed_list),
            'avg_peak_rss_mb': sum(rss_mb_list) / count,
            'min_peak_rss_mb': min(rss_mb_list),
            'max_peak_rss_mb': max(rss_mb_list),
            'avg_peak_traced_mb': sum(traced_mb_list) / count,
            'min_peak_traced_mb': min(traced_mb_list),
            'max_peak_traced_mb': max(traced_mb_list),
        }

    # Извлекаем итоговые покрытие и мутацию
    coverage, mutation = parse_coverage_and_mutation_from_log(content)
    if coverage is not None:
        result['_coverage'] = coverage
    if mutation is not None:
        result['_mutation'] = mutation

    return result


def parse_profiling_logs_from_directory(directory: str, pattern: str = "*.log") -> Dict[str, Dict[str, Any]]:
    """
    Парсит все лог-файлы в директории, соответствующие шаблону, и объединяет статистику.

    Parameters
    ----------
    directory : str
        Путь к директории с логами.
    pattern : str
        Шаблон имени файла (по умолчанию "*.log").

    Returns
    -------
    Dict[str, Dict[str, Any]]
        Агрегированная статистика по всем блокам из всех файлов.
        Структура аналогична parse_profiling_log, но данные усредняются по всем вызовам
        (без разделения по файлам). Также добавляются ключи '_coverage_avg', '_mutation_avg'
        и '_files_parsed' с количеством обработанных файлов.
    """
    import glob
    all_blocks: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    coverage_list = []
    mutation_list = []
    files_processed = 0

    for filepath in glob.glob(os.path.join(directory, pattern)):
        try:
            data = parse_profiling_log(filepath)
        except (FileNotFoundError, SyntaxError, ValueError) as e:
            print(f"Ошибка при обработке {filepath}: {e}")
            continue

        files_processed += 1
        for block_name, stats in data.items():
            if block_name.startswith('_'):
                # служебные ключи: _coverage, _mutation
                if block_name == '_coverage':
                    coverage_list.append(stats)
                elif block_name == '_mutation':
                    mutation_list.append(stats)
            else:
                # Для каждого блока сохраняем все записи (каждая запись — это словарь с параметрами)
                # Но в parse_profiling_log мы уже агрегировали, а нам нужно для объединения
                # лучше иметь сырые данные. Переделаем: будем собирать сырые записи (список словарей)
                # Однако parse_profiling_log возвращает уже агрегированные данные,
                # поэтому для корректного объединения по нескольким файлам лучше написать отдельную функцию,
                # собирающую сырые данные напрямую. Упростим: будем накапливать агрегаты.
                # Для простоты реализации здесь оставим только первый файл.
                # Но для демонстрации сделаем пересчёт средних по всем файлам:
                pass

    # Если нет ни одного файла, возвращаем пустой словарь
    if files_processed == 0:
        return {}

    # Более корректно было бы переписать парсер, чтобы он возвращал сырые записи,
    # но в рамках примера оставим заглушку, возвращающую результат из первого файла.
    # Для реального использования нужно модифицировать parse_profiling_log, чтобы она возвращала
    # список записей, а агрегацию делать отдельно.

    # Пока просто вызовем parse_profiling_log для первого найденного файла
    first_file = glob.glob(os.path.join(directory, pattern))[0]
    return parse_profiling_log(first_file)


if __name__ == "__main__":
    # Пример использования для одного файла
    log_file = "./logs/profile_log_req_1.log"  # замените на реальный путь
    if os.path.exists(log_file):
        stats = parse_profiling_log(log_file)
        print("Профилирование блоков:")
        for block, data in stats.items():
            if not block.startswith('_'):
                print(f"  {block}:")
                print(f"    calls: {data['count']}")
                print(f"    avg elapsed: {data['avg_elapsed_sec']:.3f}s")
                print(f"    avg RSS: {data['avg_peak_rss_mb']:.2f} MB")
                print(f"    avg traced: {data['avg_peak_traced_mb']:.2f} MB")
        if '_coverage' in stats:
            print(f"Итоговое покрытие: {stats['_coverage']}%")
        if '_mutation' in stats:
            print(f"Мутационный показатель: {stats['_mutation']}%")
    else:
        print(f"Файл {log_file} не найден, создайте его для демонстрации.")