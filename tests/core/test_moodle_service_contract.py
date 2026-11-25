"""Static contract checks between the Python REST client and Moodle plugin services."""

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[2]
CLIENT = (ROOT / "magic_moodle" / "moodle_api.py").read_text(encoding="utf-8")
SERVICES = (ROOT / "moodle-plugin" / "local" / "magicmoodle" / "db" / "services.php").read_text(
    encoding="utf-8"
)
EXTERNAL = ROOT / "moodle-plugin" / "local" / "magicmoodle" / "classes" / "external"

ADAPTERS = {
    "create_activity": ("local_magicmoodle_create_activity", "create_activity.php"),
    "update_section": ("local_magicmoodle_update_section", "update_section.php"),
    "create_book": ("local_magicmoodle_create_book", "create_book.php"),
    "create_assignment": ("local_magicmoodle_create_assignment", "create_assignment.php"),
    "create_quiz": ("local_magicmoodle_create_quiz", "create_quiz.php"),
    "create_resource": ("local_magicmoodle_create_resource", "create_resource.php"),
    "create_glossary": ("local_magicmoodle_create_glossary", "create_glossary.php"),
}


def _python_adapter_block(method_name: str) -> str:
    match = re.search(
        rf"^    def {re.escape(method_name)}\(.*?(?=^    def |\Z)",
        CLIENT,
        flags=re.MULTILINE | re.DOTALL,
    )
    assert match, f"Missing MoodleClient.{method_name} adapter"
    return match.group(0)


def _php_parameter_names(source: str) -> set[str]:
    start = source.index("public static function execute_parameters()")
    end = source.index("public static function execute(", start)
    signature = source[start:end]
    return set(re.findall(r"'([a-z][a-z0-9_]*)'\s*=>\s*new \\external_", signature))


def _python_payload_names(block: str) -> set[str]:
    return set(re.findall(r"""["']([a-z][a-z0-9_]*)["']\s*:""", block))


def test_every_python_adapter_is_registered_to_the_matching_plugin_class():
    for method, (function_name, filename) in ADAPTERS.items():
        assert f'"{function_name}"' in CLIENT, f"{method} does not call {function_name}"
        assert f"'{function_name}'" in SERVICES, f"{function_name} is absent from db/services.php"
        php = (EXTERNAL / filename).read_text(encoding="utf-8")
        class_name = filename.removesuffix(".php")
        assert f"class {class_name} extends \\external_api" in php
        assert f"\\\\external\\\\{class_name}" in SERVICES


def test_python_adapter_payload_keys_are_declared_by_moodle_php_contract():
    for method, (_, filename) in ADAPTERS.items():
        python_keys = _python_payload_names(_python_adapter_block(method))
        php = (EXTERNAL / filename).read_text(encoding="utf-8")
        php_keys = _php_parameter_names(php)
        assert python_keys, f"{method} payload extraction returned no keys"
        undeclared = sorted(python_keys - php_keys)
        assert not undeclared, (
            f"{method} sends parameters not declared by {filename}: {undeclared}"
        )


def test_plugin_external_service_registration_is_complete_for_all_adapters():
    for function_name, filename in ADAPTERS.values():
        php = (EXTERNAL / filename).read_text(encoding="utf-8")
        assert "public static function execute_parameters()" in php
        assert "public static function execute(" in php
        assert "public static function execute_returns()" in php
        assert function_name in SERVICES
