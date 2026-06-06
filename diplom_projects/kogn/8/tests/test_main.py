from main import eight_level_analyzer


class TestEightLevelAnalyzer:
    """Тесты для функции eight_level_analyzer."""

    def test_eight_level_analyzer_empty_template(self) -> None:
        """Пустой path_template должен вернуть начальный счётчик без изменений."""
        result = eight_level_analyzer({'a': 1}, [], [])
        assert result == {'hits': 0, 'misses': 0}

    def test_eight_level_analyzer_empty_flags(self) -> None:
        """Пустой flags не должен увеличивать hits/misses при совпадении ключа."""
        result = eight_level_analyzer({'k': {0: 'v0'}}, ['k'], [])
        assert result == {'hits': 0, 'misses': 0}

    def test_eight_level_analyzer_flag_false_skips_hit(self) -> None:
        """Если flags[step_idx] == False, совпадение ключа не должно давать hit/miss."""
        result = eight_level_analyzer({'k': {0: 'v0'}}, ['k'], [False])
        assert result == {'hits': 0, 'misses': 0}

    def test_eight_level_analyzer_non_dict_non_list_breaks(self) -> None:
        """Если current не dict/list, цикл должен прерваться и вернуть текущий счётчик."""
        result = eight_level_analyzer({'a': 42}, ['a', 'b'], [True, True])
        assert result == {'hits': 0, 'misses': 1}

    def test_eight_level_analyzer_multiple_hits(self) -> None:
        """Сценарий с несколькими уровнями, где возможны несколько hits."""
        config = {'level0': {0: {0: 'hit0', 1: 'hit1', 2: 'hit2'}}}
        result = eight_level_analyzer(config, ['level0', 0], [True, True])
        assert result == {'hits': 1, 'misses': 0}

    def test_eight_level_analyzer_override_current_on_hit(self) -> None:
        """При hit значение current[key] должно замениться на sub_val."""
        config = {'k': {0: {0: 'new_value'}}}
        eight_level_analyzer(config, ['k'], [True])
        assert config['k'][0] == 'new_value'

    def test_eight_level_analyzer_no_override_on_miss(self) -> None:
        """При miss (sub_val is None) current[key] остаётся без изменений."""
        config = {'k': {0: {0: None}}}
        original = config['k'][0].copy()
        eight_level_analyzer(config, ['k'], [True])
        assert config['k'][0] is None
