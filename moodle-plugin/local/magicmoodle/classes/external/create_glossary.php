<?php
namespace local_magicmoodle\external;

defined('MOODLE_INTERNAL') || die();

use context_course;
use invalid_parameter_exception;

require_once($CFG->libdir . '/externallib.php');
require_once($CFG->dirroot . '/course/modlib.php');
require_once($CFG->dirroot . '/mod/glossary/lib.php');
require_once($CFG->dirroot . '/mod/glossary/classes/external.php');

class create_glossary extends \external_api {
    public static function execute_parameters() {
        return new \external_function_parameters([
            'courseid' => new \external_value(PARAM_INT, 'Course id'),
            'sectionnum' => new \external_value(PARAM_INT, 'Zero-based section number'),
            'name' => new \external_value(PARAM_TEXT, 'Glossary name'),
            'intro' => new \external_value(PARAM_RAW, 'Glossary introduction HTML', VALUE_DEFAULT, ''),
            'entries' => new \external_multiple_structure(
                new \external_single_structure([
                    'term' => new \external_value(PARAM_TEXT, 'Glossary term'),
                    'definition' => new \external_value(PARAM_RAW, 'Term definition HTML'),
                ]),
                'Glossary entries'
            ),
            'idnumber' => new \external_value(PARAM_ALPHANUMEXT, 'Stable source identifier', VALUE_DEFAULT, ''),
        ]);
    }

    public static function execute($courseid, $sectionnum, $name, $intro, $entries, $idnumber = '') {
        global $DB;

        $params = self::validate_parameters(self::execute_parameters(), [
            'courseid' => $courseid,
            'sectionnum' => $sectionnum,
            'idnumber' => $idnumber,
            'name' => $name,
            'intro' => $intro,
            'entries' => $entries,
        ]);

        if (strlen($params['idnumber']) > 100) {
            throw new \invalid_parameter_exception('Activity idnumber must not exceed 100 characters.');
        }

        $course = get_course($params['courseid']);
        $coursecontext = context_course::instance($course->id);
        self::validate_context($coursecontext);
        require_capability('moodle/course:manageactivities', $coursecontext);
        require_capability('mod/glossary:addinstance', $coursecontext);

        if ($params['sectionnum'] < 0 || trim($params['name']) === ''
                || \core_text::strlen($params['name']) > 255) {
            throw new invalid_parameter_exception('Invalid section number or glossary name.');
        }
        if (empty($params['entries']) || count($params['entries']) > 500) {
            throw new invalid_parameter_exception('A glossary must contain between 1 and 500 entries.');
        }
        $seen = [];
        $totalsize = 0;
        foreach ($params['entries'] as $index => $entry) {
            $term = trim($entry['term']);
            $definition = $entry['definition'];
            if ($term === '' || \core_text::strlen($term) > 255 || trim($definition) === '') {
                throw new invalid_parameter_exception('Glossary terms and definitions must be non-empty; terms are limited to 255 characters.');
            }
            $key = \core_text::strtolower($term);
            if (isset($seen[$key])) {
                throw new invalid_parameter_exception('Duplicate glossary term: ' . $term);
            }
            $seen[$key] = true;
            $totalsize += strlen($term) + strlen($definition);
            if (strlen($definition) > 100000 || $totalsize > 5 * 1024 * 1024) {
                throw new invalid_parameter_exception('Glossary definitions exceed the supported size limits.');
            }
        }

        $section = $DB->get_record('course_sections', [
            'course' => $course->id,
            'section' => $params['sectionnum'],
        ], '*', MUST_EXIST);

        $identity = $params['idnumber'] !== '' ? $params['idnumber'] : $params['name'];
        $lockkey = 'activity_' . hash('sha256', $course->id . '|' . 'glossary' . '|' . $identity);
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
                            && $candidate->modname === 'glossary'
                            && $candidate->idnumber === $params['idnumber']
                            && (int)$candidate->sectionnum !== (int)$params['sectionnum']) {
                        throw new invalid_parameter_exception('This source idnumber already exists in another course section. Move/update the existing activity explicitly instead of creating a duplicate.');
                    }
                }
            }
            foreach ($modinfo->get_cms() as $existing) {
                if (empty($existing->deletioninprogress) && $existing->modname === 'glossary'
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
                        'modname' => 'glossary',
                        'name' => $params['name'],
                        'created' => false,
                        'entrycount' => (int)$DB->count_records('glossary_entries', ['glossaryid' => $existing->instance]),
                    ];
                }
            }
    
            $moduleid = $DB->get_field('modules', 'id', ['name' => 'glossary'], MUST_EXIST);
            $moduleinfo = new \stdClass();
            $moduleinfo->modulename = 'glossary';
            $moduleinfo->module = $moduleid;
            $moduleinfo->course = $course->id;
            $moduleinfo->section = $section->section;
            $moduleinfo->name = trim($params['name']);
            $moduleinfo->intro = clean_text($params['intro'], FORMAT_HTML);
            $moduleinfo->introformat = FORMAT_HTML;
            $moduleinfo->globalglossary = 0;
            $moduleinfo->mainglossary = 0;
            $moduleinfo->defaultapproval = 1;
            $moduleinfo->editalways = 0;
            $moduleinfo->allowduplicatedentries = 0;
            $moduleinfo->allowcomments = 0;
            $moduleinfo->usedynalink = 0;
            $moduleinfo->displayformat = 'dictionary';
            $moduleinfo->approvaldisplayformat = 'default';
            $moduleinfo->entbypage = 50;
            $moduleinfo->showalphabet = 1;
            $moduleinfo->showall = 1;
            $moduleinfo->showspecial = 1;
            $moduleinfo->allowprintview = 1;
            $moduleinfo->rsstype = 0;
            $moduleinfo->rssarticles = 0;
            $moduleinfo->assessed = 0;
            $moduleinfo->assesstimestart = 0;
            $moduleinfo->assesstimefinish = 0;
            $moduleinfo->scale = 0;
            $moduleinfo->visible = 1;
            $moduleinfo->groupmode = 0;
            $moduleinfo->groupingid = 0;
            $moduleinfo->availability = null;
            $moduleinfo->completion = COMPLETION_TRACKING_NONE;
            $moduleinfo->completionview = 0;
            $moduleinfo->completionexpected = 0;
            $moduleinfo->completionentries = 0;
            $moduleinfo->completionentriesenabled = 0;
            $moduleinfo->showdescription = 0;
            $moduleinfo->visibleoncoursepage = 1;
            $moduleinfo->cmidnumber = $params['idnumber'];
    
            $transaction = $DB->start_delegated_transaction();
            try {
                $created = add_moduleinfo($moduleinfo, $course);
                $glossary = $DB->get_record('glossary', ['id' => $created->instance], '*', MUST_EXIST);
                $modulecontext = \context_module::instance($created->coursemodule);
                require_capability('mod/glossary:write', $modulecontext);
    
                foreach ($params['entries'] as $entry) {
                    \mod_glossary_external::add_entry(
                        (int)$glossary->id,
                        trim($entry['term']),
                        clean_text($entry['definition'], FORMAT_HTML),
                        FORMAT_HTML,
                        []
                    );
                }
                $transaction->allow_commit();
            } catch (\Throwable $exception) {
                $transaction->rollback($exception);
            }
    
            return [
                'cmid' => (int)$created->coursemodule,
                'instanceid' => (int)$created->instance,
                'modname' => 'glossary',
                'name' => $params['name'],
                'created' => true,
                'entrycount' => count($params['entries']),
            ];
        } finally {
            $lock->release();
        }
    }

    public static function execute_returns() {
        return new \external_single_structure([
            'cmid' => new \external_value(PARAM_INT, 'Course module id'),
            'instanceid' => new \external_value(PARAM_INT, 'Glossary instance id'),
            'modname' => new \external_value(PARAM_TEXT, 'Module name'),
            'name' => new \external_value(PARAM_TEXT, 'Glossary name'),
            'created' => new \external_value(PARAM_BOOL, 'Whether a new glossary was created'),
            'entrycount' => new \external_value(PARAM_INT, 'Number of glossary entries'),
        ]);
    }
}
