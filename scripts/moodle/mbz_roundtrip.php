<?php
/**
 * Creates and verifies a small Moodle 4.1 course used for an MBZ backup/restore round trip.
 *
 * Run from the Moodle root:
 *   MOODLE_ROOT=/path/to/moodle php /path/to/mbz_roundtrip.php create
 *   MOODLE_ROOT=/path/to/moodle MBZ_COURSE_ID=123 php /path/to/mbz_roundtrip.php verify
 */

define('CLI_SCRIPT', true);

$moodleroot = getenv('MOODLE_ROOT');
if (!$moodleroot || !is_file($moodleroot . '/config.php')) {
    fwrite(STDERR, "MOODLE_ROOT must point to the Moodle installation root.\n");
    exit(2);
}

require($moodleroot . '/config.php');
require_once($CFG->dirroot . '/course/lib.php');
require_once($CFG->dirroot . '/course/modlib.php');

global $DB, $USER;

$mode = $argv[1] ?? '';
$sentinel = 'MBZ_ROUNDTRIP_SENTINEL_2026';

if ($mode === 'create') {
    $admin = get_admin();
    $USER = $admin;
    require_once($CFG->libdir . '/resourcelib.php');
    if (!$admin) {
        throw new RuntimeException('Moodle administrator account is missing.');
    }
    $template = $DB->get_record('course', ['id' => SITEID], '*', MUST_EXIST);
    unset($template->id);
    $template->fullname = 'MBZ round-trip fixture';
    $template->shortname = 'MBZRT-' . time();
    $template->idnumber = 'MBZRT-' . bin2hex(random_bytes(4));
    $template->category = 1;
    $template->format = 'topics';
    $template->numsections = 1;
    $template->visible = 1;
    $course = create_course($template);

    $moduleinfo = new stdClass();
    $moduleinfo->modulename = 'page';
    $moduleinfo->module = $DB->get_field('modules', 'id', ['name' => 'page'], MUST_EXIST);
    $moduleinfo->course = $course->id;
    $moduleinfo->section = 1;
    $moduleinfo->name = 'MBZ round-trip page';
    $moduleinfo->intro = '<p>Fixture activity for Moodle backup and restore.</p>';
    $moduleinfo->introformat = FORMAT_HTML;
    $moduleinfo->content = '<p>' . $sentinel . '</p><p><a href="@@PLUGINFILE@@/fixture.txt">Fixture file</a></p>';
    $moduleinfo->contentformat = FORMAT_HTML;
    $moduleinfo->revision = 1;
    $moduleinfo->display = RESOURCELIB_DISPLAY_AUTO;
    $moduleinfo->popupwidth = 620;
    $moduleinfo->popupheight = 450;
    $moduleinfo->printintro = 0;
    $moduleinfo->printlastmodified = 0;
    $moduleinfo->visible = 1;
    $moduleinfo->visibleoncoursepage = 1;
    $moduleinfo->groupmode = 0;
    $moduleinfo->groupingid = 0;
    $moduleinfo->completion = COMPLETION_DISABLED;
    $moduleinfo->completionview = 0;
    $moduleinfo->completionexpected = 0;
    $cm = add_moduleinfo($moduleinfo, $course);

    $context = context_module::instance($cm->coursemodule);
    get_file_storage()->create_file_from_string([
        'contextid' => $context->id,
        'component' => 'mod_page',
        'filearea' => 'content',
        'itemid' => 0,
        'filepath' => '/',
        'filename' => 'fixture.txt',
        'userid' => $admin->id,
    ], "MBZ round-trip file payload\n");

    echo "MBZ_FIXTURE_COURSE_ID={$course->id}\n";
    echo "MBZ_FIXTURE_COURSE_SHORTNAME={$course->shortname}\n";
    exit(0);
}

if ($mode === 'verify') {
    $courseid = (int)(getenv('MBZ_COURSE_ID') ?: 0);
    if ($courseid <= SITEID) {
        fwrite(STDERR, "MBZ_COURSE_ID must identify the restored non-site course.\n");
        exit(2);
    }
    $course = $DB->get_record('course', ['id' => $courseid], '*', MUST_EXIST);
    $cm = $DB->get_record_sql(
        "SELECT cm.* FROM {course_modules} cm
           JOIN {modules} m ON m.id = cm.module
          WHERE cm.course = ? AND m.name = 'page'
          ORDER BY cm.id DESC
          LIMIT 1",
        [$courseid]
    );
    if (!$cm) {
        throw new RuntimeException('Restored fixture Page activity was not found.');
    }
    $page = $DB->get_record('page', ['id' => $cm->instance], '*', MUST_EXIST);
    if (strpos($page->content, $sentinel) === false) {
        throw new RuntimeException('Restored Page content does not contain the fixture sentinel.');
    }
    $context = context_module::instance($cm->id);
    $file = get_file_storage()->get_file($context->id, 'mod_page', 'content', 0, '/', 'fixture.txt');
    if (!$file || $file->get_content() !== "MBZ round-trip file payload\n") {
        throw new RuntimeException('Restored Page file is missing or its bytes changed.');
    }
    echo "MBZ_ROUNDTRIP_VERIFIED courseid={$course->id} pagecmid={$cm->id} filebytes=" . $file->get_filesize() . "\n";
    exit(0);
}

fwrite(STDERR, "Usage: php mbz_roundtrip.php create|verify\n");
exit(2);
