# src/managers/prompt_engine.py
import logging
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

logger = logging.getLogger(__name__)


class PromptEngine:
    def __init__(self, templates_dir: str = None):
        if templates_dir is None:
            templates_dir = Path(__file__).parent.parent / "prompts"
        else:
            templates_dir = Path(templates_dir)

        if not templates_dir.exists():
            raise FileNotFoundError(f"Папка с шаблонами не найдена: {templates_dir}")

        self.env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        logger.debug(f"PromptEngine инициализирован: {templates_dir}")

    def render(self, template_name: str, **kwargs) -> str:
        """Рендерит шаблон с переданными параметрами"""
        template = self._load_template(template_name)
        return template.render(**kwargs)

    def _load_template(self, template_name: str):
        """Загружает шаблон по имени"""
        try:
            template = self.env.get_template(template_name)
            logger.debug(f"Шаблон '{template_name}' загружен")
            return template
        except Exception as e:
            raise ValueError(f"Ошибка загрузки шаблона {template_name}: {e}")
