# FILE: src/analysis/analysis.py

import ast
import json
import logging
import os
import subprocess
from pathlib import Path
from typing import Any

import coverage

from src.app.logger import NullLogger
from src.utils.workspace_helper import WorkspaceHelper


class TestAnalysisManager:
    def __init__(
        self,
        project_root: str | Path,
        tests_path: str | Path,
        workspace_helper: WorkspaceHelper,
        logger: logging.Logger | None = None,
    ):
        self.project_root = Path(project_root).resolve()
        self.tests_path = (self.project_root / tests_path).resolve()
        self.workspace_helper: WorkspaceHelper = workspace_helper
        self.coverage_data: dict[str, Any] = {}
        self.logger = logger or NullLogger()

    def _write_coverage_config(self, sandbox: Path, coverage_data_file: Path) -> Path:
        config_content = f"""[run]
    parallel = false
    data_file = {coverage_data_file}
    branch = true
    source = {self.project_root}
    omit =
        {self.tests_path}/*
        */migrations/*
        */venv/*
        */.venv/*
        {sandbox}/*
    """
        config_file = sandbox / ".coveragerc"
        config_file.write_text(config_content.strip(), encoding="utf-8")
        return config_file

    def run_coverage(
        self, test_code, test_function_name, file_path, test_filename="test_generated.py"
    ):
        sandbox = self.workspace_helper.sandbox_dir
        sandbox.mkdir(parents=True, exist_ok=True)

        for old in sandbox.glob(".coverage*"):
            old.unlink(missing_ok=True)
        for old in sandbox.glob("*.cover"):
            old.unlink(missing_ok=True)
        for old in sandbox.glob(test_filename + "*"):
            old.unlink(missing_ok=True)

        test_file = sandbox / test_filename
        test_file.write_text(test_code, encoding="utf-8")

        coverage_data_file = sandbox / ".coverage"
        config_file = self._write_coverage_config(sandbox, coverage_data_file)

        env = self.workspace_helper.build_env()
        existing_pp = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = (
            f"{self.project_root}{os.pathsep}{existing_pp}"
            if existing_pp
            else str(self.project_root)
        )
        env["COVERAGE_FILE"] = str(coverage_data_file)
        env.pop("COVERAGE_PROCESS_START", None)

        cmd = [
            self.workspace_helper._venv_python,
            "-m",
            "coverage",
            "run",
            f"--rcfile={config_file}",
            "-m",
            "pytest",
            str(test_file),
            "-v",
            "--tb=short",
            "--no-header",
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
                cwd=str(self.project_root),
                env=env,
            )
            retcode = result.returncode

            if result.stdout:
                self.logger.debug(f"[COVERAGE] stdout: {result.stdout}")
            if result.stderr:
                self.logger.warning(f"[COVERAGE] stderr: {result.stderr}")

        except subprocess.TimeoutExpired:
            self.logger.error("Test execution timed out")
            return -1

        coverage_file = self._find_coverage_file(sandbox)
        if not coverage_file:
            self.logger.error("[COVERAGE] .coverage файл не найден")
            return retcode

        cov = coverage.Coverage(
            data_file=str(coverage_file),
            config_file=str(config_file),
        )
        cov.load()

        file_path_obj = Path(file_path).resolve()
        self._generate_reports(cov, file_path_obj)
        self._process_annotate_file(file_path_obj, test_function_name)
        return retcode

    def _find_coverage_file(self, sandbox: Path) -> Path | None:
        exact = sandbox / ".coverage"
        if exact.exists():
            return exact

        candidates = list(sandbox.glob(".coverage.*"))
        if len(candidates) == 1:
            return candidates[0]
        if len(candidates) > 1:
            return max(candidates, key=lambda f: f.stat().st_mtime)

        return None

    def _generate_reports(self, cov: coverage.Coverage, file_path) -> None:
        sandbox_dir = self.workspace_helper.sandbox_dir

        original_dir = os.getcwd()
        try:
            os.chdir(sandbox_dir)

            try:
                os.chdir(sandbox_dir)
                cov.annotate(
                    morfs=[str(file_path)],
                    directory=str(sandbox_dir),
                )
            except Exception as exc:
                self.logger.warning(f"[COVERAGE] annotate() не удался: {exc}")
        finally:
            os.chdir(original_dir)

    def _find_function_bounds(
        self, file_path: Path, class_name: str | None, func_name: str
    ) -> tuple[int, int] | None:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source = f.read()

            tree = ast.parse(source)

            for node in ast.walk(tree):
                if class_name and isinstance(node, ast.ClassDef) and node.name == class_name:
                    for item in node.body:
                        if (
                            isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
                            and item.name == func_name
                        ):
                            start_line = item.lineno
                            end_line = item.end_lineno
                            return (start_line, end_line)

                elif (
                    not class_name
                    and isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and node.name == func_name
                ):
                    start_line = node.lineno
                    end_line = node.end_lineno
                    return (start_line, end_line)

            return None

        except Exception as exc:
            self.logger.warning(f"Ошибка при парсинге AST для {file_path}: {exc}")
            return None

    def _process_annotate_file(self, file_path: str, test_function_name: str) -> None:
        import difflib

        file_path = Path(file_path)
        test_function_name = str(test_function_name)

        pattern = f"*_{file_path.stem}.py,cover"
        annotate_files = list(self.workspace_helper.sandbox_dir.glob(pattern))

        if not annotate_files:
            self.logger.warning(f"Annotate файл не найден для {file_path.name}")
            return

        if "." in test_function_name:
            class_name, func_name = test_function_name.split(".")
        else:
            class_name, func_name = None, test_function_name

        bounds = self._find_function_bounds(file_path, class_name, func_name)

        if not bounds:
            self.logger.warning(f"Не удалось найти функцию {test_function_name} через AST")
            return

        start_line, end_line = bounds
        self.logger.debug(f"Функция {test_function_name} найдена: строки {start_line}-{end_line}")

        try:
            original_lines = file_path.read_text(encoding="utf-8").splitlines()
            original_fragment = "\n".join(original_lines[start_line - 1 : end_line])
        except Exception as exc:
            self.logger.warning(f"Не удалось прочитать оригинальный файл {file_path}: {exc}")
            original_fragment = ""

        best_file = None
        best_score = -1.0

        for annotate_file in annotate_files:
            try:
                lines = annotate_file.read_text(encoding="utf-8").splitlines()
            except Exception as exc:
                self.logger.warning(f"Не удалось прочитать {annotate_file}: {exc}")
                continue

            fragment_lines = lines[start_line - 1 : end_line]

            cleaned_lines = []
            for line in fragment_lines:
                if line and line[0] in (">", "!", "-", " "):
                    cleaned_lines.append(line[2:] if len(line) > 2 else "")
                else:
                    cleaned_lines.append(line)

            cleaned_fragment = "\n".join(cleaned_lines)

            score = difflib.SequenceMatcher(
                None,
                original_fragment,
                cleaned_fragment,
            ).ratio()

            self.logger.debug(f"[COVERAGE] {annotate_file.name}: similarity={score:.3f}")

            if score > best_score:
                best_score = score
                best_file = annotate_file

        if best_file is None:
            self.logger.warning(f"Не удалось выбрать annotate файл для {file_path.name}")
            return

        self.logger.debug(
            f"[COVERAGE] Выбран annotate файл: {best_file.name} (score={best_score:.3f})"
        )

        lines = best_file.read_text(encoding="utf-8").splitlines(keepends=True)
        function_lines = lines[start_line - 1 : end_line]

        if not function_lines:
            self.logger.warning(f"Не удалось извлечь строки {start_line}-{end_line} из {best_file}")
            best_file.unlink()
            return

        annotated_body = "".join(function_lines)

        total = 0
        covered = 0
        missing = []

        for i, line in enumerate(function_lines, start=start_line):
            clean_line = line[2:] if line and line[0] in ">!- " else line

            stripped = clean_line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if i == start_line and (
                stripped.startswith("def ") or stripped.startswith("async def ")
            ):
                continue

            total += 1
            if line.startswith(">"):
                covered += 1
            elif line.startswith("!"):
                missing.append(i)

        coverage_pct = (covered / total * 100) if total > 0 else 0

        self.logger.info(
            f"Функция {test_function_name}: покрытие {coverage_pct:.1f}% "
            f"({covered}/{total} строк)"
        )

        self.coverage_data[test_function_name] = {
            "coverage_percent": coverage_pct,
            "covered_lines": covered,
            "total_lines": total,
            "missing_lines": missing,
            "annotate_file": str(best_file),
            "annotated_body": annotated_body,
            "function_start": start_line,
            "function_end": end_line,
        }

        for annotate_file in annotate_files:
            try:
                annotate_file.unlink()
            except Exception:
                pass
