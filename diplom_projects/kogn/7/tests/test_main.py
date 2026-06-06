from typing import Dict, List, Set

from main import seven_level_transformer
import pytest


class TestSevenLevelTransformer:
    """Тесты для функции seven_level_transformer."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "matrix,thresholds,exclude_values,factor,min_factor,expected",
        [
            (
                [[10, 20, 30], [5, 15, 25]],
                [15, 10],
                {20},
                2.0,
                0.5,
                {"rows": [0, 1, 1, 1], "cols": [2, 1, 2, 2]},
            ),
            (
                [[1, 2], [3, 4]],
                [5],
                set(),
                1.0,
                0.5,
                {"rows": [], "cols": []},
            ),
            (
                [[100, 200], [300, 400]],
                [50, 250],
                {300},
                0.6,
                0.5,
                {"rows": [0, 0, 0, 1], "cols": [0, 1, 1, 1]},
            ),
            (
                [[10]],
                [5],
                set(),
                0.4,
                0.5,
                {"rows": [], "cols": []},
            ),
            (
                [[10, 20, 30, 40]],
                [15],
                {25, 35},
                3.0,
                0.5,
                {"rows": [0, 0, 0, 0, 0, 0], "cols": [1, 2, 3, 2, 3, 3]},
            ),
        ],
    )
    async def test_seven_level_transformer_variants(
        self,
        matrix: List[List[int]],
        thresholds: List[int],
        exclude_values: Set[int],
        factor: float,
        min_factor: float,
        expected: Dict[str, List[int]],
    ) -> None:
        """Проверяет корректность преобразования матрицы с разными входными данными."""
        result = seven_level_transformer(
            matrix=[row[:] for row in matrix],
            thresholds=thresholds,
            exclude_values=exclude_values,
            factor=factor,
            min_factor=min_factor,
        )
        assert result == expected

    @pytest.mark.asyncio
    async def test_seven_level_transformer_empty_matrix(self) -> None:
        """Проверяет обработку пустой матрицы."""
        result = seven_level_transformer(
            matrix=[],
            thresholds=[10],
            exclude_values=set(),
            factor=2.0,
            min_factor=0.5,
        )
        assert result == {"rows": [], "cols": []}

    @pytest.mark.asyncio
    async def test_seven_level_transformer_factor_equal_min_factor(self) -> None:
        """Проверяет, что при factor == min_factor изменения не применяются."""
        matrix = [[10, 20]]
        result = seven_level_transformer(
            matrix=[row[:] for row in matrix],
            thresholds=[5],
            exclude_values=set(),
            factor=0.5,
            min_factor=0.5,
        )
        assert result == {"rows": [], "cols": []}

    @pytest.mark.asyncio
    async def test_seven_level_transformer_exclude_values_blocks_all(self) -> None:
        """Проверяет, что exclude_values блокирует все подходящие значения."""
        matrix = [[100, 200]]
        result = seven_level_transformer(
            matrix=[row[:] for row in matrix],
            thresholds=[50],
            exclude_values={100, 200},
            factor=2.0,
            min_factor=0.5,
        )
        assert result == {"rows": [], "cols": []}

    @pytest.mark.asyncio
    async def test_seven_level_transformer_modifies_matrix_in_place(self) -> None:
        """Проверяет, что функция модифицирует переданную матрицу."""
        matrix = [[10, 20, 30]]
        seven_level_transformer(
            matrix=matrix,
            thresholds=[15],
            exclude_values=set(),
            factor=2.0,
            min_factor=0.5,
        )
        assert matrix == [[10, 40, 120]]
