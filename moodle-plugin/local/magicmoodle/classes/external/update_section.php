<?php
namespace local_magicmoodle\external;

defined('MOODLE_INTERNAL') || die();

use context_course;
use invalid_parameter_exception;

require_once($CFG->libdir . '/externallib.php');

class update_section extends \external_api {
    public static function execute_parameters() {
        return new \external_function_parameters([
            'courseid' => new \external_value(PARAM_INT, 'Course id'),
            'sectionnum' => new \external_value(PARAM_INT, 'Zero-based section number'),
            'name' => new \external_value(PARAM_TEXT, 'Section name'),
        ]);
    }

    public static function execute($courseid, $sectionnum, $name) {
        global $DB;

        $params = self::validate_parameters(self::execute_parameters(), [
            'courseid' => $courseid,
            'sectionnum' => $sectionnum,
            'name' => $name,
        ]);
        $course = get_course($params['courseid']);
        $context = context_course::instance($course->id);
        self::validate_context($context);
        require_capability('moodle/course:update', $context);

        if ($params['sectionnum'] < 0 || trim($params['name']) === '') {
            throw new invalid_parameter_exception('Invalid section number or empty name.');
        }
        $section = $DB->get_record('course_sections', [
            'course' => $course->id,
            'section' => $params['sectionnum'],
        ], '*', MUST_EXIST);
        $section->name = $params['name'];
        $DB->update_record('course_sections', $section);
        rebuild_course_cache($course->id, true);

        return [
            'courseid' => (int)$course->id,
            'sectionnum' => (int)$params['sectionnum'],
            'updated' => true,
        ];
    }

    public static function execute_returns() {
        return new \external_single_structure([
            'courseid' => new \external_value(PARAM_INT, 'Course id'),
            'sectionnum' => new \external_value(PARAM_INT, 'Section number'),
            'updated' => new \external_value(PARAM_BOOL, 'Whether section was updated'),
        ]);
    }
}
