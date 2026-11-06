from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PLUGIN = ROOT / "moodle-plugin" / "local" / "magicmoodle"


def test_plugin_declares_moodle_41_minimum_version():
    version = (PLUGIN / "version.php").read_text(encoding="utf-8")
    assert "$plugin->requires = 2022112800;" in version


def test_external_services_use_moodle_41_legacy_api():
    for filename in ("update_section.php", "create_activity.php"):
        source = (PLUGIN / "classes" / "external" / filename).read_text(encoding="utf-8")
        assert "require_once($CFG->libdir . '/externallib.php');" in source
        assert "extends \\external_api" in source
        assert "core_external\\" not in source
        assert "new \\external_function_parameters" in source
        assert "new \\external_single_structure" in source
        assert "new \\external_value" in source
