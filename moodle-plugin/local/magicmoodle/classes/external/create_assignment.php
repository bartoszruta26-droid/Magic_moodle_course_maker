<?php
namespace local_magicmoodle\external;

defined('MOODLE_INTERNAL') || die();

use context_course;
use invalid_parameter_exception;

require_once($CFG->libdir . '/externallib.php');
require_once($CFG->dirroot . '/course/modlib.php');
require_once($CFG->dirroot . '/mod/assign/lib.php');
require_once($CFG->dirroot . '/mod/assign/locallib.php');

class create_assignment extends \external_api {
    public static function execute_parameters() {
        return new \external_function_parameters([
            'courseid' => new \external_value(PARAM_INT, 'Course id'),
            'sectionnum' => new \external_value(PARAM_INT, 'Zero-based section number'),
            'name' => new \external_value(PARAM_TEXT, 'Assignment name'),
            'intro' => new \external_value(PARAM_RAW, 'Assignment description HTML', VALUE_DEFAULT, ''),
            'allowsubmissionsfromdate' => new \external_value(PARAM_INT, 'Submission start timestamp', VALUE_DEFAULT, 0),
            'duedate' => new \external_value(PARAM_INT, 'Due timestamp', VALUE_DEFAULT, 0),
            'cutoffdate' => new \external_value(PARAM_INT, 'Final submission cutoff timestamp', VALUE_DEFAULT, 0),
            'grade' => new \external_value(PARAM_FLOAT, 'Maximum grade', VALUE_DEFAULT, 100),
            'submissiontype' => new \external_value(PARAM_ALPHANUMEXT, 'onlinetext, file, or both', VALUE_DEFAULT, 'both'),
            'maxfiles' => new \external_value(PARAM_INT, 'Maximum submitted files', VALUE_DEFAULT, 5),
            'maxbytes' => new \external_value(PARAM_INT, 'Maximum bytes per submitted file', VALUE_DEFAULT, 10485760),
            'submissiondrafts' => new \external_value(PARAM_BOOL, 'Require submit button', VALUE_DEFAULT, false),
            'requiresubmissionstatement' => new \external_value(PARAM_BOOL, 'Require submission statement', VALUE_DEFAULT, false),
            'completionenabled' => new \external_value(PARAM_BOOL, 'Enable completion on submission', VALUE_DEFAULT, false),
        ]);
    }

    public static function execute(
        $courseid, $sectionnum, $name, $intro = '', $allowsubmissionsfromdate = 0,
        $duedate = 0, $cutoffdate = 0, $grade = 100, $submissiontype = 'both',
        $maxfiles = 5, $maxbytes = 10485760, $submissiondrafts = false,
        $requiresubmissionstatement = false, $completionenabled = false
    ) {
        global $CFG, $DB;

        $params = self::validate_parameters(self::execute_parameters(), [
            'courseid' => $courseid,
            'sectionnum' => $sectionnum,
            'name' => $name,
            'intro' => $intro,
            'allowsubmissionsfromdate' => $allowsubmissionsfromdate,
            'duedate' => $duedate,
            'cutoffdate' => $cutoffdate,
            'grade' => $grade,
            'submissiontype' => $submissiontype,
            'maxfiles' => $maxfiles,
            'maxbytes' => $maxbytes,
            'submissiondrafts' => $submissiondrafts,
            'requiresubmissionstatement' => $requiresubmissionstatement,
            'completionenabled' => $completionenabled,
        ]);

        $course = get_course($params['courseid']);
        $coursecontext = context_course::instance($course->id);
        self::validate_context($coursecontext);
        require_capability('moodle/course:manageactivities', $coursecontext);
        require_capability('mod/assign:addinstance', $coursecontext);

        if ($params['sectionnum'] < 0 || trim($params['name']) === ''
                || \core_text::strlen($params['name']) > 255) {
            throw new invalid_parameter_exception('Invalid section number or assignment name.');
        }
        if (!in_array($params['submissiontype'], ['onlinetext', 'file', 'both'], true)) {
            throw new invalid_parameter_exception('submissiontype must be onlinetext, file, or both.');
        }
        if ($params['maxfiles'] < 1 || $params['maxfiles'] > 20
                || $params['maxbytes'] < 1 || $params['maxbytes'] > 104857600) {
            throw new invalid_parameter_exception('File submission limits are outside supported bounds.');
        }
        if ($params['grade'] <= 0 || $params['grade'] > 10000) {
            throw new invalid_parameter_exception('Assignment grade must be greater than zero and at most 10000.');
        }
        $from = $params['allowsubmissionsfromdate'];
        $due = $params['duedate'];
        $cutoff = $params['cutoffdate'];
        if (($from < 0) || ($due < 0) || ($cutoff < 0)
                || ($due > 0 && $from > 0 && $due <= $from)
                || ($cutoff > 0 && $due > 0 && $cutoff < $due)
                || ($cutoff > 0 && $from > 0 && $cutoff < $from)) {
            throw new invalid_parameter_exception('Assignment dates are invalid or out of order.');
        }

        $section = $DB->get_record('course_sections', [
            'course' => $course->id,
            'section' => $params['sectionnum'],
        ], '*', MUST_EXIST);

        $modinfo = get_fast_modinfo($course);
        foreach ($modinfo->get_cms() as $existing) {
            if (empty($existing->deletioninprogress) && $existing->modname === 'assign'
                    && (int)$existing->sectionnum === (int)$params['sectionnum']
                    && $existing->name === $params['name']) {
                return [
                    'cmid' => (int)$existing->id,
                    'instanceid' => (int)$existing->instance,
                    'modname' => 'assign',
                    'name' => $params['name'],
                    'created' => false,
                ];
            }
        }

        $moduleid = $DB->get_field('modules', 'id', ['name' => 'assign'], MUST_EXIST);
        $moduleinfo = new \stdClass();
        $moduleinfo->modulename = 'assign';
        $moduleinfo->module = $moduleid;
        $moduleinfo->course = $course->id;
        $moduleinfo->section = $section->section;
        $moduleinfo->name = trim($params['name']);
        $moduleinfo->intro = clean_text($params['intro'], FORMAT_HTML);
        $moduleinfo->introformat = FORMAT_HTML;
        $moduleinfo->alwaysshowdescription = 1;
        $moduleinfo->activity = '';
        $moduleinfo->activityformat = FORMAT_HTML;
        $moduleinfo->submissionattachments = 0;
        $moduleinfo->submissiondrafts = $params['submissiondrafts'] ? 1 : 0;
        $moduleinfo->requiresubmissionstatement = $params['requiresubmissionstatement'] ? 1 : 0;
        $moduleinfo->sendnotifications = 0;
        $moduleinfo->sendlatenotifications = 0;
        $moduleinfo->sendstudentnotifications = 1;
        $moduleinfo->allowsubmissionsfromdate = $from;
        $moduleinfo->duedate = $due;
        $moduleinfo->cutoffdate = $cutoff;
        $moduleinfo->gradingduedate = 0;
        $moduleinfo->grade = $params['grade'];
        $moduleinfo->completionsubmit = $params['completionenabled'] ? 1 : 0;
        $moduleinfo->teamsubmission = 0;
        $moduleinfo->requireallteammemberssubmit = 0;
        $moduleinfo->teamsubmissiongroupingid = 0;
        $moduleinfo->blindmarking = 0;
        $moduleinfo->hidegrader = 0;
        $moduleinfo->attemptreopenmethod = 'none';
        $moduleinfo->maxattempts = 1;
        $moduleinfo->preventsubmissionnotingroup = 0;
        $moduleinfo->markingworkflow = 0;
        $moduleinfo->markingallocation = 0;
        $moduleinfo->visible = 1;
        $moduleinfo->groupmode = 0;
        $moduleinfo->groupingid = 0;
        $moduleinfo->availability = null;
        $moduleinfo->completion = $params['completionenabled']
            ? COMPLETION_TRACKING_AUTOMATIC : COMPLETION_TRACKING_NONE;
        $moduleinfo->completionview = 0;
        $moduleinfo->completionexpected = 0;
        $moduleinfo->showdescription = 0;
        $moduleinfo->visibleoncoursepage = 1;
        $moduleinfo->cmidnumber = '';

        $moduleinfo->assignsubmission_onlinetext_enabled =
            in_array($params['submissiontype'], ['onlinetext', 'both'], true) ? 1 : 0;
        $moduleinfo->assignsubmission_onlinetext_wordlimit = 0;
        $moduleinfo->assignsubmission_onlinetext_wordlimit_enabled = 0;
        $moduleinfo->assignsubmission_file_enabled =
            in_array($params['submissiontype'], ['file', 'both'], true) ? 1 : 0;
        $moduleinfo->assignsubmission_file_maxfiles = $params['maxfiles'];
        $moduleinfo->assignsubmission_file_maxsizebytes = $params['maxbytes'];
        $moduleinfo->assignsubmission_file_filetypes = '';

        $moduleinfo->assignfeedback_comments_enabled = 1;
        $moduleinfo->assignfeedback_comments_commentinline = 0;
        $moduleinfo->assignfeedback_editpdf_enabled = 0;

        $transaction = $DB->start_delegated_transaction();
        try {
            $created = add_moduleinfo($moduleinfo, $course);
            $transaction->allow_commit();
        } catch (\Throwable $exception) {
            $transaction->rollback($exception);
        }

        return [
            'cmid' => (int)$created->coursemodule,
            'instanceid' => (int)$created->instance,
            'modname' => 'assign',
            'name' => $params['name'],
            'created' => true,
        ];
    }

    public static function execute_returns() {
        return new \external_single_structure([
            'cmid' => new \external_value(PARAM_INT, 'Course module id'),
            'instanceid' => new \external_value(PARAM_INT, 'Assignment instance id'),
            'modname' => new \external_value(PARAM_TEXT, 'Module name'),
            'name' => new \external_value(PARAM_TEXT, 'Assignment name'),
            'created' => new \external_value(PARAM_BOOL, 'Whether a new assignment was created'),
        ]);
    }
}
