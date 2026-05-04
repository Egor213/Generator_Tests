import re
from typing import Dict, List, Optional, Any

def parse_run_block(block: str) -> Optional[Dict[str, Any]]:
    """Парсит один блок запуска, возвращает словарь с метриками или None."""
    # Поиск покрытия и мутантов
    coverage_match = re.search(r"Покрытие\s+([\d\.]+)%", block)
    mutation_match = re.search(r"Мутанты\s+([\d\.]+)%", block)
    if not coverage_match or not mutation_match:
        return None

    coverage = float(coverage_match.group(1))
    mutation = float(mutation_match.group(1))

    # Поиск LLM SUMMARY
    summary_match = re.search(
        r"SUMMARY:\s+(\d+)\s+calls,\s+(\d+)\s+prompt\s+tokens,\s+(\d+)\s+completion\s+tokens,\s+(\d+)\s+total\s+tokens",
        block,
    )
    if not summary_match:
        return {"coverage": coverage, "mutation": mutation}  # без LLM статистики

    calls = int(summary_match.group(1))
    total_tokens = int(summary_match.group(4))

    # Поиск пикового токена среди Call строк внутри блока
    peak_tokens = 0
    for call_match in re.finditer(
        r"Call\s+#\d+:\s+\d+\s+prompt\s+\+\s+\d+\s+completion\s+=\s+(\d+)\s+tokens",
        block,
    ):
        tokens = int(call_match.group(1))
        if tokens > peak_tokens:
            peak_tokens = tokens

    return {
        "coverage": coverage,
        "mutation": mutation,
        "llm_calls": calls,
        "llm_total_tokens": total_tokens,
        "llm_peak_tokens": peak_tokens,
    }


def parse_all_runs(log_text: str) -> List[Dict[str, Any]]:
    """Парсит весь лог, содержащий несколько запусков. Возвращает список метрик по каждому запуску."""
    # Разделяем на блоки, начиная с "Запуск X:" до следующего "Запуск Y:" или конца текста
    pattern = r"(Запуск\s+\d+:.*?)(?=(Запуск\s+\d+:)|$)"
    matches = re.findall(pattern, log_text, re.DOTALL)
    runs = []
    for match in matches:
        block = match[0].strip()
        metrics = parse_run_block(block)
        if metrics:
            runs.append(metrics)
    return runs


def compute_averages(runs: List[Dict[str, Any]]) -> Dict[str, float]:
    """Считает средние значения по всем запускам."""
    if not runs:
        return {}
    n = len(runs)
    avg_coverage = sum(r["coverage"] for r in runs) / n
    avg_mutation = sum(r["mutation"] for r in runs) / n

    # Для LLM метрик считаем только по тем запускам, где они есть
    runs_with_llm = [r for r in runs if "llm_calls" in r]
    if runs_with_llm:
        m = len(runs_with_llm)
        avg_calls = sum(r["llm_calls"] for r in runs_with_llm) / m
        avg_total_tokens = sum(r["llm_total_tokens"] for r in runs_with_llm) / m
        avg_peak_tokens = sum(r["llm_peak_tokens"] for r in runs_with_llm) / m
    else:
        avg_calls = avg_total_tokens = avg_peak_tokens = 0.0

    return {
        "avg_coverage": avg_coverage,
        "avg_mutation": avg_mutation,
        "avg_llm_calls": avg_calls,
        "avg_llm_total_tokens": avg_total_tokens,
        "avg_llm_peak_tokens": avg_peak_tokens,
    }
    
if __name__ == "__main__":
    with open("./logs/profile_log_cogn_5.log", "r", encoding="utf-8") as f:
        content = f.read()

    runs = parse_all_runs(content)

    print("Информация по каждому запуску:")
    for i, run in enumerate(runs, 1):
        print(f"Запуск {i}: покрытие {run['coverage']}%, мутанты {run['mutation']}%", end="")
        if "llm_calls" in run:
            print(f", LLM вызовы={run['llm_calls']}, общие токены={run['llm_total_tokens']}, пик={run['llm_peak_tokens']}")
        else:
            print()

    avg = compute_averages(runs)
    print("\nСредние значения по всем запускам:")
    print(f"Среднее покрытие: {avg['avg_coverage']:.2f}%")
    print(f"Средний мутационный показатель: {avg['avg_mutation']:.2f}%")
    if avg['avg_llm_calls'] > 0:
        print(f"Среднее количество вызовов LLM: {avg['avg_llm_calls']:.1f}")
        print(f"Среднее общее количество токенов: {avg['avg_llm_total_tokens']:.0f}")
        print(f"Средний пик токенов за вызов: {avg['avg_llm_peak_tokens']:.0f}")