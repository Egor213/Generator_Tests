# File path: Generator_Tests/src/llm/clients/llm_client.py
import logging

from src.entity.llm import LLMProvider, LLMResponse, Message
from src.factories.invoker_factory import create_invoker
from src.llm.invoker import LLMInvoker
from src.managers.config import Config
from src.utils.usage_tracker import LLMUsageTracker

logger = logging.getLogger(__name__)


class LLMClient:
    def __init__(
        self,
        config: Config,
    ):
        self.config = config
        self.provider = LLMProvider(config.ai.llm_provider.lower())
        self.invoker: LLMInvoker = create_invoker(self.provider, config)
        self.usage_tracker = LLMUsageTracker()

    def _build_payload(self, messages: list[Message]) -> dict:
        model = self.config.ai.model or self._get_default_model()
        return {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": self.config.ai.temperature,
        }

    def _get_default_model(self) -> str:
        base_models = {
            LLMProvider.OPENAI: "gpt-4o-mini",
        }
        return base_models.get(self.provider, "default")

    def _get_messages(self, prompt: str | list[Message]):
        if isinstance(prompt, str):
            messages = [Message(role="user", content=prompt)]
        else:
            messages = prompt
        return messages

    async def send_prompt(self, prompt: str | list[Message]) -> LLMResponse:
        messages = self._get_messages(prompt)
        payload = self._build_payload(messages)
        logger.debug("Запрос отправлен")

        response = await self.invoker.invoke_with_retry(payload)
        self.usage_tracker.record(response.usage, response.model)
        return response

    def print_usage_report(self) -> None:
        print(self.usage_tracker.report())

    async def close(self) -> None:
        await self.invoker.close()
