<?php
namespace local_magicmoodle\external;

defined('MOODLE_INTERNAL') || die();

use context_course;
use context_user;
use invalid_parameter_exception;

require_once($CFG->libdir . '/externallib.php');
require_once($CFG->dirroot . '/course/modlib.php');
require_once($CFG->libdir . '/resourcelib.php');
require_once($CFG->dirroot . '/mod/resource/lib.php');
require_once($CFG->dirroot . '/mod/resource/locallib.php');

class create_resource extends \external_api {
    public static function execute_parameters() {
        return new \external_function_parameters([
            'courseid' => new \external_value(PARAM_INT, 'Course id'),
            'sectionnum' => new \external_value(PARAM_INT, 'Zero-based section number'),
            'name' => new \external_value(PARAM_TEXT, 'Resource activity name'),
            'filename' => new \external_value(PARAM_FILE, 'File name'),
            'contentbase64' => new \external_value(PARAM_RAW, 'Base64 encoded file content'),
            'intro' => new \external_value(PARAM_RAW, 'Resource introduction HTML', VALUE_DEFAULT, ''),
            'idnumber' => new \external_value(PARAM_ALPHANUMEXT, 'Stable source identifier', VALUE_DEFAULT, ''),
        ]);
    }

    public static function execute($courseid, $sectionnum, $name, $filename, $contentbase64, $intro = '', $idnumber = '') {
        global $CFG, $DB, $USER;

        $params = self::validate_parameters(self::execute_parameters(), [
            'courseid' => $courseid,
            'sectionnum' => $sectionnum,
            'idnumber' => $idnumber,
            'name' => $name,
            'filename' => $filename,
            'contentbase64' => $contentbase64,
            'intro' => $intro,
        ]);

        if (strlen($params['idnumber']) > 100) {
            throw new \invalid_parameter_exception('Activity idnumber must not exceed 100 characters.');
        }

        $course = get_course($params['courseid']);
        $coursecontext = context_course::instance($course->id);
        self::validate_context($coursecontext);
        require_capability('moodle/course:manageactivities', $coursecontext);
        require_capability('mod/resource:addinstance', $coursecontext);

        $filename = clean_param($params['filename'], PARAM_FILE);
        if ($params['sectionnum'] < 0 || trim($params['name']) === ''
                || \core_text::strlen($params['name']) > 255
                || $filename === '' || $filename === '.' || $filename === '..'
                || strpos($filename, '/') !== false || strpos($filename, '\\') !== false) {
            throw new invalid_parameter_exception('Invalid resource section, name or filename.');
        }
        if (!is_string($params['contentbase64']) || strlen($params['contentbase64']) > 7 * 1024 * 1024) {
            throw new invalid_parameter_exception('Encoded resource content exceeds the 5 MiB upload limit.');
        }
        $filecontent = base64_decode($params['contentbase64'], true);
        if ($filecontent === false || strlen($filecontent) < 1 || strlen($filecontent) > 5 * 1024 * 1024) {
            throw new invalid_parameter_exception('Resource content must be valid base64 containing 1 byte to 5 MiB.');
        }
        $siteuploadlimit = (int)$CFG->maxbytes;
        $courseuploadlimit = (int)$course->maxbytes;
        $effectiveuploadlimit = ($courseuploadlimit > 0)
            ? min($siteuploadlimit, $courseuploadlimit) : $siteuploadlimit;
        if ($effectiveuploadlimit > 0 && strlen($filecontent) > $effectiveuploadlimit) {
            throw new invalid_parameter_exception('Resource file exceeds the Moodle site or course upload limit.');
        }

        $section = $DB->get_record('course_sections', [
            'course' => $course->id,
            'section' => $params['sectionnum'],
        ], '*', MUST_EXIST);

        $modinfo = get_fast_modinfo($course);
        foreach ($modinfo->get_cms() as $existing) {
            if (empty($existing->deletioninprogress) && $existing->modname === 'resource'
                    && (int)$existing->sectionnum === (int)$params['sectionnum']
                    && ($existing->name === $params['name'] || ($params['idnumber'] !== '' && $existing->idnumber === $params['idnumber']))) {
                if ($params['idnumber'] !== ''
                        && $existing->name === $params['name']
                        && !empty($existing->idnumber)
                        && $existing->idnumber !== $params['idnumber']) {
                    throw new invalid_parameter_exception('An activity with this name already has a different source idnumber. Refusing to reuse it.');
                }
                if ($params['idnumber'] !== ''
                        && $existing->idnumber === $params['idnumber']
                        && $existing->name !== $params['name']) {
                    throw new invalid_parameter_exception('This source idnumber already belongs to an activity with a different name. An explicit update is required.');
                }

                if ($params['idnumber'] !== '' && empty($existing->idnumber)) {
                    $DB->set_field('course_modules', 'idnumber', $params['idnumber'], ['id' => $existing->id]);
                }
                return [
                    'cmid' => (int)$existing->id,
                    'instanceid' => (int)$existing->instance,
                    'modname' => 'resource',
                    'name' => $params['name'],
                    'filename' => $filename,
                    'filesize' => (int)$DB->get_field('files', 'filesize', [
                        'contextid' => \context_module::instance($existing->id)->id,
                        'component' => 'mod_resource',
                        'filearea' => 'content',
                        'itemid' => 0,
                        'filename' => $filename,
                    ]),
                    'created' => false,
                ];
            }
        }

        $moduleid = $DB->get_field('modules', 'id', ['name' => 'resource'], MUST_EXIST);
        $draftitemid = null;
        $usercontext = context_user::instance($USER->id);
        $fs = get_file_storage();
        $transaction = $DB->start_delegated_transaction();
        try {
            $draftitemid = file_get_unused_draft_itemid();
        $fs->create_file_from_string([
            'contextid' => $usercontext->id,
            'component' => 'user',
            'filearea' => 'draft',
            'itemid' => $draftitemid,
            'filepath' => '/',
            'filename' => $filename,
            'userid' => $USER->id,
        ], $filecontent);

        $moduleinfo = new \stdClass();
        $moduleinfo->modulename = 'resource';
        $moduleinfo->module = $moduleid;
        $moduleinfo->course = $course->id;
        $moduleinfo->section = $section->section;
        $moduleinfo->name = trim($params['name']);
        $moduleinfo->intro = clean_text($params['intro'], FORMAT_HTML);
        $moduleinfo->introformat = FORMAT_HTML;
        $moduleinfo->files = $draftitemid;
        $moduleinfo->display = RESOURCELIB_DISPLAY_AUTO;
        $moduleinfo->popupwidth = 800;
        $moduleinfo->popupheight = 600;
        $moduleinfo->printintro = 1;
        $moduleinfo->showsize = 1;
        $moduleinfo->showtype = 1;
        $moduleinfo->showdate = 0;
        $moduleinfo->filterfiles = 1;
        $moduleinfo->revision = 1;
        $moduleinfo->visible = 1;
        $moduleinfo->groupmode = 0;
        $moduleinfo->groupingid = 0;
        $moduleinfo->availability = null;
        $moduleinfo->completion = COMPLETION_TRACKING_NONE;
        $moduleinfo->completionview = 0;
        $moduleinfo->completionexpected = 0;
        $moduleinfo->showdescription = 0;
        $moduleinfo->visibleoncoursepage = 1;
        $moduleinfo->cmidnumber = $params['idnumber'];

            $created = add_moduleinfo($moduleinfo, $course);
            $transaction->allow_commit();
        } catch (\Throwable $exception) {
            $transaction->rollback($exception);
        } finally {
            if ($draftitemid !== null) {
                $fs->delete_area_files($usercontext->id, 'user', 'draft', $draftitemid);
            }
        }

        $modulecontext = \context_module::instance($created->coursemodule);
        $storedfiles = $fs->get_area_files($modulecontext->id, 'mod_resource', 'content', 0, 'sortorder', false);
        $storedsize = 0;
        foreach ($storedfiles as $storedfile) {
            $storedsize += $storedfile->get_filesize();
        }

        return [
            'cmid' => (int)$created->coursemodule,
            'instanceid' => (int)$created->instance,
            'modname' => 'resource',
            'name' => $params['name'],
            'filename' => $filename,
            'filesize' => $storedsize,
            'created' => true,
        ];
    }

    public static function execute_returns() {
        return new \external_single_structure([
            'cmid' => new \external_value(PARAM_INT, 'Course module id'),
            'instanceid' => new \external_value(PARAM_INT, 'Resource instance id'),
            'modname' => new \external_value(PARAM_TEXT, 'Module name'),
            'name' => new \external_value(PARAM_TEXT, 'Resource name'),
            'filename' => new \external_value(PARAM_FILE, 'Stored filename'),
            'filesize' => new \external_value(PARAM_INT, 'Stored file size in bytes'),
            'created' => new \external_value(PARAM_BOOL, 'Whether a new resource was created'),
        ]);
    }
}
