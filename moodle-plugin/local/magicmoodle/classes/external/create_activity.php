<?php
namespace local_magicmoodle\external;

defined('MOODLE_INTERNAL') || die();

use context_course;
use invalid_parameter_exception;

require_once($CFG->libdir . '/externallib.php');
require_once($CFG->dirroot . '/course/modlib.php');

class create_activity extends \external_api {
    public static function execute_parameters() {
        return new \external_function_parameters([
            'courseid' => new \external_value(PARAM_INT, 'Course id'),
            'sectionnum' => new \external_value(PARAM_INT, 'Zero-based section number'),
            'modname' => new \external_value(PARAM_ALPHANUMEXT, 'Supported module: page, label or url'),
            'name' => new \external_value(PARAM_TEXT, 'Activity name'),
            'content' => new \external_value(PARAM_RAW, 'HTML content', VALUE_DEFAULT, ''),
            'externalurl' => new \external_value(PARAM_URL, 'Target URL for URL activity', VALUE_DEFAULT, ''),
            'idnumber' => new \external_value(PARAM_ALPHANUMEXT, 'Stable source identifier', VALUE_DEFAULT, ''),
        ]);
    }

    public static function execute($courseid, $sectionnum, $modname, $name, $content = '', $externalurl = '', $idnumber = '') {
        global $DB;

        $params = self::validate_parameters(self::execute_parameters(), [
            'courseid' => $courseid,
            'sectionnum' => $sectionnum,
            'idnumber' => $idnumber,
            'modname' => $modname,
            'name' => $name,
            'content' => $content,
            'externalurl' => $externalurl,
        ]);
        if (strlen($params['idnumber']) > 100) {
            throw new \invalid_parameter_exception('Activity idnumber must not exceed 100 characters.');
        }

        $course = get_course($params['courseid']);
        $context = context_course::instance($course->id);
        self::validate_context($context);
        require_capability('moodle/course:manageactivities', $context);

        if (!in_array($params['modname'], ['page', 'label', 'url'], true)) {
            throw new invalid_parameter_exception('Only page, label and url modules are supported.');
        }
        if ($params['sectionnum'] < 0 || trim($params['name']) === '') {
            throw new invalid_parameter_exception('Invalid section number or empty activity name.');
        }
        if ($params['modname'] === 'url') {
            $parts = parse_url($params['externalurl']);
            if (!is_array($parts) || empty($parts['scheme'])
                    || !in_array(strtolower($parts['scheme']), ['http', 'https'], true)
                    || empty($parts['host']) || isset($parts['user']) || isset($parts['pass'])) {
                throw new invalid_parameter_exception('URL activity requires an absolute HTTP or HTTPS URL.');
            }
        }

        $section = $DB->get_record('course_sections', [
            'course' => $course->id,
            'section' => $params['sectionnum'],
        ], '*', MUST_EXIST);

        // Idempotency: same module type/name/section is reused, never duplicated.
        // Serialize all writes for this module type within the course to avoid check-then-create races.
        $lockkey = 'activity_' . hash('sha256', $course->id . '|' . $params['modname']);
        $lockfactory = \core\lock\lock_config::get_lock_factory('local_magicmoodle');
        $lock = $lockfactory->get_lock($lockkey, 30);
        if (!$lock) {
            throw new \moodle_exception('locktimeout', 'error');
        }
        try {
            $modinfo = get_fast_modinfo($course);
            if ($params['idnumber'] !== '') {
                foreach ($modinfo->get_cms() as $candidate) {
                    if (empty($candidate->deletioninprogress)
                            && $candidate->modname === $params['modname']
                            && $candidate->idnumber === $params['idnumber']
                            && (int)$candidate->sectionnum !== (int)$params['sectionnum']) {
                        throw new invalid_parameter_exception('This source idnumber already exists in another course section. Move/update the existing activity explicitly instead of creating a duplicate.');
                    }
                }
            }
            foreach ($modinfo->get_cms() as $existing) {
                if (empty($existing->deletioninprogress)
                        && $existing->modname === $params['modname']
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
    
                    // Re-publishing a source activity is an update, not a no-op.
                    // Keep the existing course-module and module-instance identifiers.
                    $transaction = $DB->start_delegated_transaction();
                    try {
                        $moduleid = $DB->get_field('modules', 'id', ['name' => $params['modname']], MUST_EXIST);
                        $safecontent = clean_text($params['content'], FORMAT_HTML);
                        $moduleinfo = new \\stdClass();
                        $moduleinfo->modulename = $params['modname'];
                        $moduleinfo->module = $moduleid;
                        $moduleinfo->course = $course->id;
                        $moduleinfo->section = $section->section;
                        $moduleinfo->instance = (int)$existing->instance;
                        $moduleinfo->coursemodule = (int)$existing->id;
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
                        $moduleinfo->cmidnumber = $params['idnumber'] !== ''
                            ? $params['idnumber'] : (string)$existing->idnumber;

                        if ($params['modname'] === 'page') {
                            $moduleinfo->content = $safecontent;
                            $moduleinfo->contentformat = FORMAT_HTML;
                            $moduleinfo->display = RESOURCELIB_DISPLAY_AUTO;
                            $moduleinfo->displayoptions = serialize(['printheading' => 1, 'printintro' => 0]);
                            $moduleinfo->printheading = 1;
                            $moduleinfo->printintro = 0;
                            $moduleinfo->printlastmodified = 0;
                        } else if ($params['modname'] === 'label') {
                            $moduleinfo->intro = $safecontent;
                            $moduleinfo->introformat = FORMAT_HTML;
                        } else {
                            $moduleinfo->externalurl = $params['externalurl'];
                            $moduleinfo->parameters = '';
                            $moduleinfo->popupwidth = 800;
                            $moduleinfo->popupheight = 600;
                            $moduleinfo->display = RESOURCELIB_DISPLAY_AUTO;
                            $moduleinfo->displayoptions = serialize(['printheading' => 1, 'printintro' => 0]);
                            $moduleinfo->printheading = 1;
                            $moduleinfo->printintro = 0;
                        }

                        $coursemodule = $DB->get_record('course_modules', [
                            'id' => $existing->id,
                            'course' => $course->id,
                        ], '*', MUST_EXIST);
                        update_moduleinfo($coursemodule, $moduleinfo, $course);
                        if ($params['idnumber'] !== '' && empty($existing->idnumber)) {
                            $DB->set_field('course_modules', 'idnumber', $params['idnumber'], ['id' => $existing->id]);
                        }
                        rebuild_course_cache($course->id, true);
                        $transaction->allow_commit();
                    } catch (\\Throwable $exception) {
                        $transaction->rollback($exception);
                    }
                    return [
                        'cmid' => (int)$existing->id,
                        'instanceid' => (int)$existing->instance,
                        'modname' => $params['modname'],
                        'name' => $params['name'],
                        'created' => false,
                    ];
                }
            }
    
            $moduleid = $DB->get_field('modules', 'id', ['name' => $params['modname']], MUST_EXIST);
            $safecontent = clean_text($params['content'], FORMAT_HTML);
    
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
            $moduleinfo->cmidnumber = $params['idnumber'];
    
            if ($params['modname'] === 'page') {
                $moduleinfo->content = $safecontent;
                $moduleinfo->contentformat = FORMAT_HTML;
                $moduleinfo->display = RESOURCELIB_DISPLAY_AUTO;
                $moduleinfo->displayoptions = serialize(['printheading' => 1, 'printintro' => 0]);
                $moduleinfo->printheading = 1;
                $moduleinfo->printintro = 0;
                $moduleinfo->printlastmodified = 0;
            } else if ($params['modname'] === 'label') {
                $moduleinfo->intro = $safecontent;
                $moduleinfo->introformat = FORMAT_HTML;
            } else {
                $moduleinfo->externalurl = $params['externalurl'];
                $moduleinfo->parameters = '';
                $moduleinfo->popupwidth = 800;
                $moduleinfo->popupheight = 600;
                $moduleinfo->display = RESOURCELIB_DISPLAY_AUTO;
                $moduleinfo->displayoptions = serialize(['printheading' => 1, 'printintro' => 0]);
                $moduleinfo->printheading = 1;
                $moduleinfo->printintro = 0;
            }
    
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
                'modname' => $params['modname'],
                'name' => $params['name'],
                'created' => true,
            ];
        } finally {
            $lock->release();
        }
    }

    public static function execute_returns() {
        return new \external_single_structure([
            'cmid' => new \external_value(PARAM_INT, 'Course module id'),
            'instanceid' => new \external_value(PARAM_INT, 'Module instance id'),
            'modname' => new \external_value(PARAM_TEXT, 'Module name'),
            'name' => new \external_value(PARAM_TEXT, 'Activity name'),
            'created' => new \external_value(PARAM_BOOL, 'Whether a new activity was created'),
        ]);
    }
}
