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
                    'sourceid' => new \external_value(PARAM_ALPHANUMEXT, 'Stable source entry identifier'),
                    'term' => new \external_value(PARAM_TEXT, 'Glossary term'),
                    'definition' => new \external_value(PARAM_RAW, 'Term definition HTML'),
                ]),
                'Glossary entries'
            ),
            'entryids' => new \external_multiple_structure(
                new \external_single_structure([
                    'sourceid' => new \external_value(PARAM_ALPHANUMEXT, 'Stable source entry identifier'),
                    'entryid' => new \external_value(PARAM_INT, 'Existing Moodle glossary entry id'),
                ]),
                'Previously persisted source-to-entry mappings',
                VALUE_DEFAULT,
                []
            ),
            'idnumber' => new \external_value(PARAM_ALPHANUMEXT, 'Stable source identifier', VALUE_DEFAULT, ''),
        ]);
    }

    public static function execute($courseid, $sectionnum, $name, $intro, $entries, $entryids = [], $idnumber = '') {
        global $DB, $CFG;

        $params = self::validate_parameters(self::execute_parameters(), [
            'courseid' => $courseid,
            'sectionnum' => $sectionnum,
            'idnumber' => $idnumber,
            'name' => $name,
            'intro' => $intro,
            'entries' => $entries,
            'entryids' => $entryids,
        ]);

        if (strlen($params['idnumber']) > 100) {
            throw new invalid_parameter_exception('Activity idnumber must not exceed 100 characters.');
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
        foreach ($params['entries'] as $entry) {
            $sourceid = trim($entry['sourceid']);
            $term = trim($entry['term']);
            $definition = $entry['definition'];
            if ($sourceid === '' || $term === '' || \core_text::strlen($term) > 255 || trim($definition) === '') {
                throw new invalid_parameter_exception('Glossary source ids, terms and definitions must be non-empty; terms are limited to 255 characters.');
            }
            if (isset($seen[$sourceid])) {
                throw new invalid_parameter_exception('Duplicate glossary source id: ' . $sourceid);
            }
            $seen[$sourceid] = true;
            $totalsize += strlen($term) + strlen($definition);
            if (strlen($definition) > 100000 || $totalsize > 5 * 1024 * 1024) {
                throw new invalid_parameter_exception('Glossary definitions exceed the supported size limits.');
            }
        }

        $mapping = [];
        $seenentryids = [];
        foreach ($params['entryids'] as $mappingitem) {
            $sourceid = trim($mappingitem['sourceid']);
            $entryid = (int)$mappingitem['entryid'];
            if ($sourceid === '' || $entryid < 1 || isset($mapping[$sourceid]) || isset($seenentryids[$entryid])) {
                throw new invalid_parameter_exception('Invalid or duplicate glossary source-to-entry mapping.');
            }
            $mapping[$sourceid] = $entryid;
            $seenentryids[$entryid] = true;
        }

        $section = $DB->get_record('course_sections', [
            'course' => $course->id,
            'section' => $params['sectionnum'],
        ], '*', MUST_EXIST);

        $lockkey = 'activity_' . hash('sha256', $course->id . '|glossary');
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

            $existing = null;
            foreach ($modinfo->get_cms() as $candidate) {
                if (empty($candidate->deletioninprogress) && $candidate->modname === 'glossary'
                        && (int)$candidate->sectionnum === (int)$params['sectionnum']
                        && ($candidate->name === $params['name']
                            || ($params['idnumber'] !== '' && $candidate->idnumber === $params['idnumber']))) {
                    if ($params['idnumber'] !== '' && $candidate->name === $params['name']
                            && !empty($candidate->idnumber) && $candidate->idnumber !== $params['idnumber']) {
                        throw new invalid_parameter_exception('An activity with this name already has a different source idnumber. Refusing to reuse it.');
                    }
                    $existing = $candidate;
                    break;
                }
            }

            $transaction = $DB->start_delegated_transaction();
            try {
                if ($existing) {
                    $cm = $DB->get_record('course_modules', [
                        'id' => $existing->id,
                        'course' => $course->id,
                        'module' => $DB->get_field('modules', 'id', ['name' => 'glossary'], MUST_EXIST),
                    ], '*', MUST_EXIST);
                    $glossary = $DB->get_record('glossary', ['id' => $existing->instance], '*', MUST_EXIST);
                    if (empty($mapping) && $DB->record_exists('glossary_entries', ['glossaryid' => $glossary->id])) {
                        throw new invalid_parameter_exception(
                            'This existing glossary has entries but no source-id mapping manifest. '
                            . 'Refusing to create duplicates; reconcile the legacy entries first.'
                        );
                    }
                    list($cm, $modulecontext, $module, $moduleinfo, $courseSection) =
                        get_moduleinfo_data($cm, $course);
                    $moduleinfo->name = trim($params['name']);
                    $moduleinfo->intro = clean_text($params['intro'], FORMAT_HTML);
                    $moduleinfo->introformat = FORMAT_HTML;
                    if ($params['idnumber'] !== '') {
                        $moduleinfo->cmidnumber = $params['idnumber'];
                    }
                    update_moduleinfo($cm, $moduleinfo, $course);
                    $cmid = (int)$existing->id;
                    $instanceid = (int)$existing->instance;
                    $created = false;
                } else {
                    if (!empty($mapping)) {
                        throw new invalid_parameter_exception('Glossary entry mappings were supplied but the target glossary does not exist. Refusing to attach old entry ids to a new glossary.');
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
                    $createdmodule = add_moduleinfo($moduleinfo, $course);
                    $cmid = (int)$createdmodule->coursemodule;
                    $instanceid = (int)$createdmodule->instance;
                    $glossary = $DB->get_record('glossary', ['id' => $instanceid], '*', MUST_EXIST);
                    $modulecontext = \context_module::instance($cmid);
                    $created = true;
                }

                $modulecontext = \context_module::instance($cmid);
                require_capability('mod/glossary:write', $modulecontext);

                // Validate every persisted mapping before changing any entry. Stale ids fail closed.
                foreach ($mapping as $sourceid => $entryid) {
                    $DB->get_record('glossary_entries', [
                        'id' => $entryid,
                        'glossaryid' => $glossary->id,
                    ], '*', MUST_EXIST);
                }

                $resultmapping = $mapping;
                $createdcount = 0;
                $updatedcount = 0;
                foreach ($params['entries'] as $entry) {
                    $sourceid = trim($entry['sourceid']);
                    $term = trim($entry['term']);
                    $definition = clean_text($entry['definition'], FORMAT_HTML);
                    if (isset($mapping[$sourceid])) {
                        $entryid = $mapping[$sourceid];
                        $entryrecord = $DB->get_record('glossary_entries', [
                            'id' => $entryid,
                            'glossaryid' => $glossary->id,
                        ], '*', MUST_EXIST);
                        $fs = get_file_storage();
                        $hasattachments = !empty($fs->get_area_files(
                            $modulecontext->id, 'mod_glossary', 'attachment', $entryid, 'id', false
                        )) || !empty($fs->get_area_files(
                            $modulecontext->id, 'mod_glossary', 'inlineattachment', $entryid, 'id', false
                        ));
                        if ($hasattachments) {
                            throw new invalid_parameter_exception(
                                'A mapped glossary entry contains attachments or inline files. '
                                . 'File-preserving glossary editor synchronization is required before updating this entry.'
                            );
                        }
                        $aliases = $DB->get_fieldset_select(
                            'glossary_alias', 'alias', 'entryid = ?', [$entryid]
                        );
                        $categories = $DB->get_fieldset_select(
                            'glossary_entries_categories', 'categoryid', 'entryid = ?', [$entryid]
                        );
                        $options = [
                            ['name' => 'aliases', 'value' => implode(', ', $aliases)],
                        ];
                        if (!empty($categories)) {
                            $options[] = ['name' => 'categories', 'value' => implode(',', $categories)];
                        }
                        if (!empty($glossary->usedynalink)) {
                            $options[] = ['name' => 'usedynalink', 'value' => (int)$entryrecord->usedynalink];
                            $options[] = ['name' => 'casesensitive', 'value' => (int)$entryrecord->casesensitive];
                            $options[] = ['name' => 'fullmatch', 'value' => (int)$entryrecord->fullmatch];
                        }
                        \mod_glossary\external\update_entry::execute(
                            $entryid, $term, $definition, FORMAT_HTML, $options
                        );
                        $updatedcount++;
                    } else {
                        $added = \mod_glossary_external::add_entry(
                            $glossary->id, $term, $definition, FORMAT_HTML, []
                        );
                        $added = \external_api::clean_returnvalue(
                            \mod_glossary_external::add_entry_returns(), $added
                        );
                        $entryid = (int)$added['entryid'];
                        if ($entryid < 1) {
                            throw new \moodle_exception('invalidrecord', 'error', '', 'Glossary entry id missing');
                        }
                        $resultmapping[$sourceid] = $entryid;
                        $createdcount++;
                    }
                }

                rebuild_course_cache($course->id, true);
                $transaction->allow_commit();
            } catch (\Throwable $exception) {
                $transaction->rollback($exception);
            }

            return [
                'cmid' => $cmid,
                'instanceid' => $instanceid,
                'modname' => 'glossary',
                'name' => $params['name'],
                'created' => $created,
                'updated' => !$created,
                'entrycount' => count($params['entries']),
                'entries_created' => $createdcount,
                'entries_updated' => $updatedcount,
                'entryids' => array_map(
                    static function($sourceid, $entryid) {
                        return ['sourceid' => $sourceid, 'entryid' => (int)$entryid];
                    },
                    array_keys($resultmapping),
                    array_values($resultmapping)
                ),
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
            'updated' => new \external_value(PARAM_BOOL, 'Whether an existing glossary was updated'),
            'entrycount' => new \external_value(PARAM_INT, 'Number of source glossary entries'),
            'entries_created' => new \external_value(PARAM_INT, 'Number of new entries'),
            'entries_updated' => new \external_value(PARAM_INT, 'Number of updated entries'),
            'entryids' => new \external_multiple_structure(
                new \external_single_structure([
                    'sourceid' => new \external_value(PARAM_ALPHANUMEXT, 'Stable source entry identifier'),
                    'entryid' => new \external_value(PARAM_INT, 'Moodle glossary entry id'),
                ])
            ),
        ]);
    }
}
