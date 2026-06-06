from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.orchestrator.post_processor import PostProcessResult, PostProcessor
from src.utils.import_cleaner import ImportCleaner


class TestPostProcessorReview:

    @pytest.fixture
    def mock_llm_client(self):
        return MagicMock()

    @pytest.fixture
    def mock_prompt_engine(self):
        return MagicMock()

    @pytest.fixture
    def mock_text_parser(self):
        return MagicMock()

    @pytest.fixture
    def mock_logger(self):
        return MagicMock()

    @pytest.fixture
    def post_processor(self, mock_llm_client, mock_prompt_engine, mock_text_parser, mock_logger):
        return PostProcessor(llm_client=mock_llm_client, prompt_engine=mock_prompt_engine, text_parser=mock_text_parser, logger=mock_logger)

    @pytest.mark.asyncio
    async def test_review_successful_modification(self, post_processor, mock_prompt_engine, mock_llm_client, mock_text_parser, mock_logger):
        """
        Успешная пост-обработка: LLM вернула валидный код, проверки безопасности пройдены,
        результат изменён.
        """
        test_code = 'def test_example():\n    assert True\n'
        source_code = 'def foo():\n    return 1\n'
        reviewed_code = 'def test_example():\n    assert True\n\ndef test_new():\n    assert False\n'
        mock_prompt_engine.render.return_value = 'prompt'
        mock_llm_client.send_prompt = AsyncMock(return_value=MagicMock(content=reviewed_code))
        mock_text_parser.extract_code.return_value = reviewed_code
        with patch.object(post_processor.import_cleaner, 'clean_unused_imports', return_value=reviewed_code):
            result = await post_processor.review(test_code, source_code)
        assert isinstance(result, PostProcessResult)
        assert result.reviewed_code == reviewed_code
        assert result.was_modified is True
        mock_logger.info.assert_any_call('Запуск пост-обработки тестов через LLM...')

    @pytest.mark.asyncio
    async def test_review_llm_returns_none(self, post_processor, mock_prompt_engine, mock_llm_client, mock_text_parser, mock_logger):
        """
        LLM вернула None через извлечение кода — используется оригинальный код.
        """
        test_code = 'def test_example():\n    assert True\n'
        source_code = 'def foo():\n    return 1\n'
        mock_prompt_engine.render.return_value = 'prompt'
        mock_llm_client.send_prompt = AsyncMock(return_value=MagicMock(content='irrelevant'))
        mock_text_parser.extract_code.return_value = None
        result = await post_processor.review(test_code, source_code)
        assert isinstance(result, PostProcessResult)
        assert result.was_modified is False
        mock_logger.warning.assert_any_call('Не удалось извлечь код из ответа LLM, используется оригинал')

    @pytest.mark.asyncio
    async def test_review_llm_raises_exception(self, post_processor, mock_prompt_engine, mock_llm_client, mock_logger):
        """
        LLM выбросила исключение — используется оригинальный код.
        """
        test_code = 'def test_example():\n    assert True\n'
        source_code = 'def foo():\n    return 1\n'
        mock_prompt_engine.render.return_value = 'prompt'
        mock_llm_client.send_prompt = AsyncMock(side_effect=RuntimeError('Network error'))
        result = await post_processor.review(test_code, source_code)
        assert isinstance(result, PostProcessResult)
        assert result.was_modified is False
        mock_logger.error.assert_any_call('Ошибка пост-обработки: Network error')
        mock_logger.info.assert_any_call('Используется оригинальный код без изменений')

    @pytest.mark.asyncio
    async def test_review_no_change_after_review(self, post_processor, mock_prompt_engine, mock_llm_client, mock_text_parser, mock_logger):
        """
        LLM вернула код, идентичный оригиналу — изменений нет.
        """
        test_code = 'def test_example():\n    assert True\n'
        source_code = 'def foo():\n    return 1\n'
        reviewed_code = 'def test_example():\n    assert True\n'
        mock_prompt_engine.render.return_value = 'prompt'
        mock_llm_client.send_prompt = AsyncMock(return_value=MagicMock(content=reviewed_code))
        mock_text_parser.extract_code.return_value = reviewed_code
        with patch.object(post_processor.import_cleaner, 'clean_unused_imports', return_value=reviewed_code):
            result = await post_processor.review(test_code, source_code)
        assert isinstance(result, PostProcessResult)
        assert result.reviewed_code == reviewed_code
        assert result.was_modified is False
        mock_logger.info.assert_any_call('Пост-обработка: LLM не внесла изменений, код чистый')


class TestPostProcessorUnchangedResult:
    """Тесты для метода PostProcessor._unchanged_result."""

    @pytest.fixture
    def post_processor(self):
        """Фикстура: минимальный экземпляр PostProcessor для вызова метода."""
        # Создаём объект, не проверяя его инициализацию — только для вызова _unchanged_result.
        processor = PostProcessor.__new__(PostProcessor)
        processor.import_cleaner = MagicMock(spec=ImportCleaner)
        return processor

    @pytest.mark.parametrize(
        "test_code,cleaned_code,expected_modified",
        [
            ("import os\nprint('hello')", "import os\nprint('hello')", False),
            ("import os\nimport sys\nprint('hello')", "import os\nprint('hello')", True),
            ("", "", False),
            ("   \n  ", "   \n  ", False),
            ("import json", "import json", False),
            ("import json\nimport typing", "import json", True),
        ],
    )
    def test_unchanged_result_return_value(
        self,
        post_processor,
        test_code,
        cleaned_code,
        expected_modified,
    ):
        """Проверяет, что метод возвращает корректный PostProcessResult."""
        post_processor.import_cleaner.clean_unused_imports.return_value = cleaned_code

        result = post_processor._unchanged_result(test_code)

        assert isinstance(result, PostProcessResult)
        assert result.reviewed_code == cleaned_code
        assert result.was_modified == expected_modified

    @pytest.mark.parametrize(
        "test_code",
        [
            "import os\nprint('hello')",
            "",
            "import json\nimport sys\nimport typing",
        ],
    )
    def test_unchanged_result_calls_cleaner(
        self,
        post_processor,
        test_code,
    ):
        """Проверяет, что метод вызывает clean_unused_imports с переданным кодом."""
        post_processor.import_cleaner.clean_unused_imports.return_value = test_code

        post_processor._unchanged_result(test_code)

        post_processor.import_cleaner.clean_unused_imports.assert_called_once_with(test_code)

    def test_unchanged_result_strip_comparison(self, post_processor):
        """Проверяет, что сравнение использует strip() для обоих значений."""
        post_processor.import_cleaner.clean_unused_imports.return_value = "  x = 1  "

        result = post_processor._unchanged_result("x = 1")

        # "  x = 1  ".strip() == "x = 1".strip() => was_modified=False
        assert result.was_modified is False


class TestPostProcessorSendReview:
    """Тесты для метода PostProcessor._send_review."""

    @pytest.fixture
    def mock_llm_client(self):
        return AsyncMock()

    @pytest.fixture
    def mock_prompt_engine(self):
        return MagicMock()

    @pytest.fixture
    def mock_text_parser(self):
        return MagicMock()

    @pytest.fixture
    def post_processor(self, mock_llm_client, mock_prompt_engine, mock_text_parser):
        return PostProcessor(
            llm_client=mock_llm_client,
            prompt_engine=mock_prompt_engine,
            text_parser=mock_text_parser,
        )

    @pytest.mark.asyncio
    async def test_send_review_successful_extraction(
        self,
        post_processor,
        mock_prompt_engine,
        mock_llm_client,
        mock_text_parser,
    ):
        """Успешное извлечение кода из ответа LLM."""
        test_code = "def test_example(): pass"
        source_code = "def foo(): return 1"
        prompt = "rendered prompt"
        response_content = "```python\ndef test_example(): return 2\n```"
        extracted = "def test_example(): return 2"

        mock_prompt_engine.render.return_value = prompt
        mock_llm_client.send_prompt.return_value.content = response_content
        mock_text_parser.extract_code.return_value = extracted

        result = await post_processor._send_review(test_code, source_code)

        mock_prompt_engine.render.assert_called_once_with(
            template_name="post_review.j2",
            test_code=test_code,
            source_code=source_code,
        )
        mock_llm_client.send_prompt.assert_called_once_with(prompt)
        mock_text_parser.extract_code.assert_called_once_with(response_content)
        assert result == extracted

    @pytest.mark.asyncio
    async def test_send_review_extracted_too_short_returns_none(
        self,
        post_processor,
        mock_prompt_engine,
        mock_llm_client,
        mock_text_parser,
    ):
        """Извлечённый код короче 10 символов — возвращается None."""
        test_code = "def test_example(): pass"
        source_code = "def foo(): return 1"
        prompt = "rendered prompt"
        response_content = "some output"
        extracted = "short"

        mock_prompt_engine.render.return_value = prompt
        mock_llm_client.send_prompt.return_value.content = response_content
        mock_text_parser.extract_code.return_value = extracted

        result = await post_processor._send_review(test_code, source_code)

        mock_text_parser.extract_code.assert_called_once_with(response_content)
        assert result is None

    @pytest.mark.asyncio
    async def test_send_review_extracted_empty_returns_none(
        self,
        post_processor,
        mock_prompt_engine,
        mock_llm_client,
        mock_text_parser,
    ):
        """Пустое извлечённое значение — возвращается None."""
        test_code = "def test_example(): pass"
        source_code = "def foo(): return 1"
        prompt = "rendered prompt"
        response_content = "some output"
        extracted = ""

        mock_prompt_engine.render.return_value = prompt
        mock_llm_client.send_prompt.return_value.content = response_content
        mock_text_parser.extract_code.return_value = extracted

        result = await post_processor._send_review(test_code, source_code)

        mock_text_parser.extract_code.assert_called_once_with(response_content)
        assert result is None

    @pytest.mark.asyncio
    async def test_send_review_extracted_none_returns_none(
        self,
        post_processor,
        mock_prompt_engine,
        mock_llm_client,
        mock_text_parser,
    ):
        """extract_code вернул None — возвращается None."""
        test_code = "def test_example(): pass"
        source_code = "def foo(): return 1"
        prompt = "rendered prompt"
        response_content = "some output"

        mock_prompt_engine.render.return_value = prompt
        mock_llm_client.send_prompt.return_value.content = response_content
        mock_text_parser.extract_code.return_value = None

        result = await post_processor._send_review(test_code, source_code)

        mock_text_parser.extract_code.assert_called_once_with(response_content)
        assert result is None

    @pytest.mark.asyncio
    async def test_send_review_extraction_exception_logs_warning_and_returns_none(
        self,
        post_processor,
        mock_prompt_engine,
        mock_llm_client,
        mock_text_parser,
    ):
        """Исключение при извлечении кода — предупреждение в лог и None."""
        test_code = "def test_example(): pass"
        source_code = "def foo(): return 1"
        prompt = "rendered prompt"
        response_content = "some output"
        error = ValueError("parse error")

        mock_prompt_engine.render.return_value = prompt
        mock_llm_client.send_prompt.return_value.content = response_content
        mock_text_parser.extract_code.side_effect = error

        with patch.object(post_processor.logger, "warning") as mock_warning:
            result = await post_processor._send_review(test_code, source_code)

            mock_text_parser.extract_code.assert_called_once_with(response_content)
            assert result is None
            # Проверка вызова логгера с предупреждением
            assert mock_warning.called
            assert "Не удалось извлечь код из ответа" in str(mock_warning.call_args_list)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "response_content,extracted,expected",
        [
            (
                "```python\ndef test_one(): pass\n```",
                "def test_one(): pass",
                "def test_one(): pass",
            ),
            (
                "```\npython\ndef test_two(): pass\n```",
                "def test_two(): pass",
                "def test_two(): pass",
            ),
            (
                "plain code without backticks",
                "plain code without backticks",
                "plain code without backticks",
            ),
        ],
    )
    async def test_send_review_various_response_formats(
        self,
        post_processor,
        mock_prompt_engine,
        mock_llm_client,
        mock_text_parser,
        response_content,
        extracted,
        expected,
    ):
        """Проверка разных форматов ответа LLM через параметризацию."""
        test_code = "def test_example(): pass"
        source_code = "def foo(): return 1"
        prompt = "rendered prompt"

        mock_prompt_engine.render.return_value = prompt
        mock_llm_client.send_prompt.return_value.content = response_content
        mock_text_parser.extract_code.return_value = extracted

        result = await post_processor._send_review(test_code, source_code)

        mock_text_parser.extract_code.assert_called_once_with(response_content)
        assert result == expected


class TestPostProcessorIsSafeModification:
    @pytest.fixture
    def mock_post_processor(self):
        llm_client = MagicMock()
        prompt_engine = MagicMock()
        text_parser = MagicMock()
        logger = MagicMock()
        return PostProcessor(
            llm_client=llm_client,
            prompt_engine=prompt_engine,
            text_parser=text_parser,
            logger=logger,
        )

    @pytest.mark.parametrize(
        "original,reviewed,expected",
        [
            ("", "", True),
            ("\n", "", True),
            ("   ", "", True),
            ("def test_one():\n    pass", "", False),
            ("def test_one():\n    pass", "def test_one():\n    pass", True),
            ("def test_one():\n    pass", "def test_one():", False),
            ("def test_one():\n    pass\n\ndef test_two():\n    pass", "def test_one():\n    pass", False),
            ("def test_one():\n    pass\n\ndef test_two():\n    pass\n\ndef test_three():\n    pass", "def test_one():\n    pass", False),
            ("def test_one():\n    pass\n\ndef test_two():\n    pass\n\ndef test_three():\n    pass", "def test_one():\n    pass\n\ndef test_two():\n    pass", True),
            ("def test_one():\n    pass\n\ndef test_two():\n    pass\n\ndef test_three():\n    pass", "def test_one():\n    pass\n\ndef test_two():", False),
        ],
    )
    def test_is_safe_modification(self, mock_post_processor, original, reviewed, expected):
        """
        Проверка корректности вычисления безопасности модификации
        на основе отношения удалённых строк к исходным.
        """
        result = mock_post_processor._is_safe_modification(original, reviewed)
        assert result is expected

    def test_is_safe_modification_logs_warning_on_excessive_removal(self, mock_post_processor):
        """
        Проверка логирования при превышении порога удаления строк.
        """
        original = "def test_one():\n    pass\n\ndef test_two():\n    pass\n\ndef test_three():\n    pass"
        reviewed = ""
        result = mock_post_processor._is_safe_modification(original, reviewed)
        assert result is False
        mock_post_processor.logger.debug.assert_called()


class TestPreservesTestCoverage:
    """Тесты для метода PostProcessor._preserves_test_coverage."""

    @pytest.fixture
    def post_processor(self):
        llm_client = MagicMock()
        prompt_engine = MagicMock()
        text_parser = MagicMock()
        logger = MagicMock()
        return PostProcessor(
            llm_client=llm_client,
            prompt_engine=prompt_engine,
            text_parser=text_parser,
            logger=logger,
        )

    @pytest.mark.parametrize(
        "original_tests,reviewed_tests,expected",
        [
            (set(), set(), True),
            (set(), {"test_a"}, True),
            ({"test_a"}, {"test_a"}, True),
            ({"test_a", "test_b"}, {"test_a", "test_b"}, True),
            ({"test_a", "test_b", "test_c"}, {"test_a", "test_b", "test_c"}, True),
        ],
    )
    def test_no_removal_returns_true(self, post_processor, original_tests, reviewed_tests, expected):
        """
        Проверяет, что при отсутствии удалённых тестов метод возвращает True.
        """
        result = post_processor._preserves_test_coverage(original_tests, reviewed_tests)
        assert result is expected

    @pytest.mark.parametrize(
        "original_tests,reviewed_tests",
        [
            ({"test_a", "test_b", "test_c", "test_d", "test_e", "test_f", "test_g", "test_h", "test_i", "test_j"},
             {"test_a", "test_b", "test_c", "test_d", "test_e", "test_f"}),
            ({"test_1", "test_2", "test_3", "test_4", "test_5", "test_6", "test_7", "test_8", "test_9", "test_10"},
             {"test_1", "test_2", "test_3", "test_4", "test_5", "test_6"}),
        ],
    )
    def test_high_removal_ratio_returns_false(self, post_processor, original_tests, reviewed_tests):
        """
        Проверяет, что при превышении порога удаления тестов метод возвращает False.
        """
        result = post_processor._preserves_test_coverage(original_tests, reviewed_tests)
        assert result is False

    @pytest.mark.parametrize(
        "original_tests,reviewed_tests",
        [
            ({"test_a", "test_b", "test_c", "test_d"}, {"test_a", "test_b", "test_c"}),
            ({"test_1", "test_2", "test_3", "test_4", "test_5", "test_6", "test_7"}, {"test_1", "test_2", "test_3", "test_4", "test_5"}),
        ],
    )
    def test_low_removal_ratio_returns_true(self, post_processor, original_tests, reviewed_tests):
        """
        Проверяет, что при удалении тестов в пределах допустимого порога метод возвращает True.
        """
        result = post_processor._preserves_test_coverage(original_tests, reviewed_tests)
        assert result is True

    def test_logger_debug_called_on_excessive_removal(self, post_processor):
        """
        Проверяет, что при превышении лимита удаления вызывается logger.debug с ожидаемым сообщением.
        """
        original_tests = {"test_a", "test_b", "test_c", "test_d", "test_e", "test_f", "test_g", "test_h", "test_i", "test_j"}
        reviewed_tests = {"test_a", "test_b", "test_c", "test_d", "test_e", "test_f"}

        post_processor._preserves_test_coverage(original_tests, reviewed_tests)

        post_processor.logger.debug.assert_called()
        call_args = post_processor.logger.debug.call_args[0][0]
        assert "Удалено тестов" in call_args
        assert "4/10" in call_args


class TestPostProcessorExtractTestNames:
    """Тесты для статического метода PostProcessor._extract_test_names."""

    @pytest.mark.parametrize(
        "code,expected",
        [
            ("", set()),
            ("def not_a_test(): pass", set()),
            ("def test_foo(): pass", {"test_foo"}),
            ("async def test_bar(): pass", {"test_bar"}),
            ("def test_one(): pass\ndef test_two(): pass", {"test_one", "test_two"}),
            ("async def test_async_baz(): pass", {"test_async_baz"}),
            ("def test_a(): pass\n    def nested(): pass", {"test_a"}),
            ("class TestSuite:\n    def test_method(self): pass", {"test_method"}),
            ("def test_123(): pass\ndef test_abc(): pass", {"test_123", "test_abc"}),
            ("def test_with_underscore_long_name(): pass", {"test_with_underscore_long_name"}),
            ("async def test_mixed(): pass\ndef test_plain(): pass", {"test_mixed", "test_plain"}),
            ("# def test_commented(): pass", {"test_commented"}),
            ("'def test_in_string(): pass'", {"test_in_string"}),
            ("def test_(): pass", set()),
            ("async def test_(): pass", set()),
            ("def test_9(): pass", {"test_9"}),
        ],
    )
    def test_extract_test_names_variants(self, code, expected):
        """Проверяет извлечение имён тестовых функций для разных шаблонов кода."""
        result = PostProcessor._extract_test_names(code)
        assert result == expected

    def test_no_false_positives(self):
        """Убеждается, что не-async/не-def конструкции не распознаются как тесты."""
        code = (
            "def testing(): pass\n"
            "def test(): pass\n"
            "def test_this(): pass\n"
            "async def not_a_test(): pass\n"
            "def test_1(): pass  # real\n"
            "class Test:\n"
            "    def helper(self): pass\n"
        )
        result = PostProcessor._extract_test_names(code)
        assert result == {"test_this", "test_1"}
