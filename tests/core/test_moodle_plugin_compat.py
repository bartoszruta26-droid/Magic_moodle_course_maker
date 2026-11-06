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



def test_all_create_endpoints_reject_source_identity_conflicts():
    endpoints = (
        "create_activity.php",
        "create_assignment.php",
        "create_book.php",
        "create_glossary.php",
        "create_quiz.php",
        "create_resource.php",
    )
    for filename in endpoints:
        source = (PLUGIN / "classes" / "external" / filename).read_text(encoding="utf-8")
        assert "different source idnumber" in source
        assert "different name" in source
        assert "another course section" in source


def test_every_mutating_endpoint_uses_a_delegated_transaction():
    endpoints = (
        "update_section.php",
        "create_activity.php",
        "create_assignment.php",
        "create_book.php",
        "create_glossary.php",
        "create_quiz.php",
        "create_resource.php",
    )
    for filename in endpoints:
        source = (PLUGIN / "classes" / "external" / filename).read_text(encoding="utf-8")
        assert "start_delegated_transaction()" in source
        assert "allow_commit()" in source
        assert "rollback($exception)" in source


def test_resource_draft_files_are_cleaned_up_after_failed_or_successful_creation():
    source = (PLUGIN / "classes" / "external" / "create_resource.php").read_text(encoding="utf-8")
    assert "$draftitemid = null;" in source
    assert "finally {" in source
    assert "delete_area_files($usercontext->id, 'user', 'draft', $draftitemid)" in source


def test_section_update_rebuilds_course_cache_inside_transaction():
    source = (PLUGIN / "classes" / "external" / "update_section.php").read_text(encoding="utf-8")
    assert "rebuild_course_cache($course->id, true);" in source
    assert source.index("start_delegated_transaction()") < source.index("rebuild_course_cache")
    assert source.index("rebuild_course_cache") < source.index("allow_commit()")



def test_create_endpoints_serialize_writes_by_source_identity():
    endpoints = (
        "create_activity.php",
        "create_assignment.php",
        "create_book.php",
        "create_glossary.php",
        "create_quiz.php",
        "create_resource.php",
    )
    for filename in endpoints:
        source = (PLUGIN / "classes" / "external" / filename).read_text(encoding="utf-8")
        assert "lock_config::get_lock_factory('local_magicmoodle')" in source
        assert "get_lock($lockkey, 30)" in source
        assert "$lock->release();" in source
        assert "hash('sha256'" in source
