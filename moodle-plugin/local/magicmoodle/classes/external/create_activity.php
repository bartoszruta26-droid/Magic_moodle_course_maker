<?php
namespace local_magicmoodle\external;

defined('MOODLE_INTERNAL') || die();

require_once($CFG->libdir . '/externallib.php');
require_once($CFG->dirroot . '/course/modlib.php');

use context_course;
use core_external\external_api;
use core_external\external_function_parameters;
use core_external\external_single_structure;
use core_external\external_value;
use invalid_parameter_exception;

class create_activity extends external_api {
    public static function execute_parameters() {
        return new external_function_parameters([
            'courseid' => new external_value(PARAM_INT, 'Course id'),
            'sectionnum' => new external_value(PARAM_INT, 'Zero-based section number'),
            'modname' => new external_value(PARAM_ALPHANUMEXT, 'Supported module: page or label'),
            'name' => new external_value(PARAM_TEXT, 'Activity name'),
            'content' => new external_value(PARAM_RAW, 'HTML content'),
        ]);
    }

    public static function execute($courseid, $sectionnum, $modname, $name, $content) {
        global $DB;

        $params = self::validate_parameters(self::execute_parameters(), [
            'courseid' => $courseid,
            'sectionnum' => $sectionnum,
            'modname' => $modname,
            'name' => $name,
            'content' => $content,
        ]);
        $course = get_course($params['courseid']);
        $context = context_course::instance($course->id);
        self::validate_context($context);
        require_capability('moodle/course:manageactivities', $context);

        if (!in_array($params['modname'], ['page', 'label'], true)) {
            throw new invalid_parameter_exception('Only page and label modules are supported.');
        }
        if ($params['sectionnum'] < 0 || trim($params['name']) === '') {
            throw new invalid_parameter_exception('Invalid section number or empty activity name.');
        }
        $section = $DB->get_record('course_sections', [
            'course' => $course->id,
            'section' => $params['sectionnum'],
        ], '*', MUST_EXIST);

        // Idempotency: an identical module name/type in the same section is not duplicated.
        $modinfo = get_fast_modinfo($course);
        foreach ($modinfo->get_cms() as $existing) {
            if (empty($existing->deletioninprogress)
                    && $existing->modname === $params['modname']
                    && (int)$existing->sectionnum === (int)$params['sectionnum']
                    && $existing->name === $params['name']) {
                return [
                    'cmid' => (int)$existing->id,
                    'instanceid' => (int)$existing->instance,
                    'modname' => $params['modname'],
                    'name' => $params['name'],
                    'created' => false,
                ];
            }
        }

        $moduleid = $DB->get_field('modules', 'id', ['name' => $params['modname']], MUST_EXIST);\n        $safecontent = clean_text($params['content'], FORMAT_HTML);

        $moduleinfo = new \stdClass();
        $moduleinfo->modulename = $params['modname'];
        $moduleinfo->module = $moduleid;
        $moduleinfo->course = $course->id;
        $moduleinfo->section = $section->section;
        $moduleinfo->name = $params['name'];
        $moduleinfo->intro = '';
        $moduleinfo->introformat = FORMAT_HTML;
        $moduleinfo->visible = 1;
        $moduleinfo->groupmode = 0;
        $moduleinfo->groupingid = 0;
        $moduleinfo->availability = null;
        $moduleinfo->completion = COMPLETION_TRACKING_NONE;
        $moduleinfo->completionview = 0;
        $moduleinfo->completionexpected = 0;
        $moduleinfo->showdescription = 0;
        $moduleinfo->visibleoncoursepage = 1;
        $moduleinfo->cmidnumber = '';

        if ($params['modname'] === 'page') {
            $moduleinfo->content = $safecontent;
            $moduleinfo->contentformat = FORMAT_HTML;
            $moduleinfo->display = RESOURCELIB_DISPLAY_AUTO;
            $moduleinfo->displayoptions = serialize(['printheading' => 1, 'printintro' => 0]);
            $moduleinfo->printheading = 1;
            $moduleinfo->printintro = 0;
            $moduleinfo->printlastmodified = 0;
        } else {
            $moduleinfo->intro = $safecontent;
            $moduleinfo->introformat = FORMAT_HTML;
        }

        $created = add_moduleinfo($moduleinfo, $course);
        return [
            'cmid' => (int)$created->coursemodule,
            'instanceid' => (int)$created->instance,
            'modname' => $params['modname'],
            'name' => $params['name'],
            'created' => true,
        ];
    }

    public static function execute_returns() {
        return new external_single_structure([
            'cmid' => new external_value(PARAM_INT, 'Course module id'),
            'instanceid' => new external_value(PARAM_INT, 'Module instance id'),
            'modname' => new external_value(PARAM_TEXT, 'Module name'),
            'name' => new external_value(PARAM_TEXT, 'Activity name'),
            'created' => new external_value(PARAM_BOOL, 'Whether a new activity was created'),
        ]);
    }
}
