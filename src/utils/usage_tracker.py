from dataclasses import dataclass
from typing import Dict, List


@dataclass
class CallRecord:
    call_id: int
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    model: str


class LLMUsageTracker:
    def __init__(self):
        self._calls: List[CallRecord] = []
        self._last_id = 0

    def record(self, usage: Dict[str, int], model: str) -> int:
        self._last_id += 1
        record = CallRecord(
            call_id=self._last_id,
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
            model=model,
        )
        self._calls.append(record)
        return self._last_id

    @property
    def total_prompt_tokens(self) -> int:
        return sum(c.prompt_tokens for c in self._calls)

    @property
    def total_completion_tokens(self) -> int:
        return sum(c.completion_tokens for c in self._calls)

    @property
    def total_tokens(self) -> int:
        return sum(c.total_tokens for c in self._calls)

    @property
    def total_calls(self) -> int:
        return len(self._calls)

    def report(self) -> str:
        lines = []
        lines.append("=" * 60)
        lines.append("LLM USAGE REPORT")
        lines.append("=" * 60)
        for call in self._calls:
            lines.append(
                f"Call #{call.call_id}: {call.prompt_tokens} prompt + "
                f"{call.completion_tokens} completion = {call.total_tokens} tokens "
                f"(model: {call.model})"
            )
        lines.append("-" * 60)
        lines.append(
            f"SUMMARY: {self.total_calls} calls, "
            f"{self.total_prompt_tokens} prompt tokens, "
            f"{self.total_completion_tokens} completion tokens, "
            f"{self.total_tokens} total tokens"
        )
        lines.append("=" * 60)
        return "\n".join(lines)
