"""Guard the existing knowledge/service boundary without importing application UI."""
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def imports(path):
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            yield from (alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if node.level:
                package = path.parent.relative_to(ROOT).parts
                base = package[:len(package) - node.level + 1]
                module = ".".join((*base, *module.split("."))).rstrip(".")
            yield module
            yield from (f"{module}.{alias.name}" for alias in node.names)


def test_application_does_not_import_rvdb_producer_internals():
    violations = []
    for directory in ("ui", "controllers", "services", "models", "config"):
        for path in (ROOT / directory).rglob("*.py"):
            for module in imports(path):
                if module.split(".")[0] in {"engine", "validator", "rvdb"}:
                    violations.append((str(path.relative_to(ROOT)), module))
    assert not violations, violations


def test_raw_consumer_is_confined_to_adapter_and_composition_root():
    allowed = {"ui/main_window.py", "services/rvdb/__init__.py",
               "services/rvdb/consumer.py", "services/rvdb/service.py"}
    violations = []
    for directory in ("ui", "controllers", "services"):
        for path in (ROOT / directory).rglob("*.py"):
            relative = path.relative_to(ROOT).as_posix()
            if relative in allowed:
                continue
            for module in imports(path):
                if module == "services.rvdb.consumer" or module.endswith(".RVDBConsumer"):
                    violations.append((relative, module))
    assert not violations, violations


def test_presentation_resolution_does_not_import_execution_or_writers():
    forbidden = {"subprocess", "services.retroarch", "config.writer",
                 "config.ConfigWriter", "services.presentation.native_deployment",
                 "services.presentation.native_shader_deployment"}
    for name in ("resolver", "effective_resolver", "composer", "automation", "recommendation_resolver"):
        path = ROOT / "services" / "presentation" / f"{name}.py"
        for module in imports(path):
            assert not any(module == prefix or module.startswith(prefix + ".")
                           for prefix in forbidden), (path, module)


def test_application_workflows_do_not_import_ui_or_qt():
    for name in ('controllers/game_launch_controller.py', 'services/settings/service.py',
                 'services/library/presentation_studio.py', 'services/library/library_service.py'):
        for module in imports(ROOT / name):
            assert module.split('.')[0] not in {'ui', 'PyQt6', 'PySide6'}, (name, module)


def test_game_details_does_not_prepare_or_execute_runtime_resources():
    forbidden = {'config', 'models.launch_profile', 'services.retroarch.launcher',
                 'services.retroarch.archive_runtime', 'subprocess'}
    for module in imports(ROOT / 'ui/library/details/game_details.py'):
        assert not any(module == value or module.startswith(value + '.') for value in forbidden), module
