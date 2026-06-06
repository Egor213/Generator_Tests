from typing import Dict, List, Set

def deep_nested_six(
    matrix: List[List[int]],
    thresholds: List[int],
    exclude_values: Set[int],
    factor: float
) -> Dict[str, List[int]]:
    result: Dict[str, List[int]] = {"rows": [], "cols": []}
    for i, row in enumerate(matrix):                     # 1
        row_threshold = thresholds[i % len(thresholds)]
        for j, val in enumerate(row):                    # 2
            if val > row_threshold:                      # 3
                if val not in exclude_values:            # 4
                    for k in range(j, j + 2):            # 5
                        if k < len(row):                 # 6
                            result["rows"].append(i)
                            result["cols"].append(k)
                            row[k] = int(row[k] * factor)
    return result
