<?php
namespace local_magicmoodle\external;

defined('MOODLE_INTERNAL') || die();

use context_course;
use invalid_parameter_exception;

require_once($CFG->libdir . '/externallib.php');
require_once($CFG->dirroot . '/course/modlib.php');
require_once($CFG->dirroot . '/mod/book/locallib.php');

class create_book extends \external_api {
    public static function execute_parameters() {
        return new \external_function_parameters([
            'courseid' => new \external_value(PARAM_INT, 'Course id'),
            'sectionnum' => new \external_value(PARAM_INT, 'Zero-based section number'),
            'name' => new \external_value(PARAM_TEXT, 'Book activity name'),
            'chapters' => new \external_multiple_structure(
                new \external_single_structure([
                    'sourceid' => new \external_value(PARAM_ALPHANUMEXT, 'Stable source chapter identifier'),
                    'title' => new \external_value(PARAM_TEXT, 'Chapter title'),
                    'content' => new \external_value(PARAM_RAW, 'Chapter HTML content'),
                    'subchapter' => new \external_value(PARAM_BOOL, 'Whether this is a subchapter', VALUE_DEFAULT, false),
                    'files' => new \external_multiple_structure(
                        new \external_single_structure([
                            'filepath' => new \external_value(PARAM_RAW, 'Chapter asset filepath'),
                            'filename' => new \external_value(PARAM_FILE, 'Chapter asset filename'),
                            'contentbase64' => new \external_value(PARAM_RAW, 'Base64-encoded chapter asset'),
                        ]),
                        'Chapter assets', VALUE_OPTIONAL
                    ),
                ]),
                'Book chapters'
            ),
            'chapterids' => new \external_multiple_structure(
                new \external_single_structure([
                    'sourceid' => new \external_value(PARAM_ALPHANUMEXT, 'Stable source chapter identifier'),
                    'chapterid' => new \external_value(PARAM_INT, 'Existing Moodle chapter id'),
                ]),
                'Previously persisted source-to-chapter mappings',
                VALUE_DEFAULT,
                []
            ),
            'numbering' => new \external_value(PARAM_INT, 'Book numbering: 0 none, 1 numbers, 2 bullets, 3 indented', VALUE_DEFAULT, 1),
            'idnumber' => new \external_value(PARAM_ALPHANUMEXT, 'Stable source identifier', VALUE_DEFAULT, ''),
        ]);
    }

    public static function execute($courseid, $sectionnum, $name, $chapters, $chapterids = [], $numbering = 1, $idnumber = '') {
        global $DB, $CFG, $USER;

        $params = self::validate_parameters(self::execute_parameters(), [
            'courseid' => $courseid,
            'sectionnum' => $sectionnum,
            'idnumber' => $idnumber,
            'name' => $name,
            'chapters' => $chapters,
            'chapterids' => $chapterids,
            'numbering' => $numbering,
        ]);
        if (strlen($params['idnumber']) > 100) {
            throw new invalid_parameter_exception('Activity idnumber must not exceed 100 characters.');
        }

        $course = get_course($params['courseid']);
        $context = context_course::instance($course->id);
        self::validate_context($context);
        require_capability('moodle/course:manageactivities', $context);
        require_capability('mod/book:addinstance', $context);

        if ($params['sectionnum'] < 0 || trim($params['name']) === '' || \core_text::strlen($params['name']) > 255) {
            throw new invalid_parameter_exception('Invalid section number or empty book name.');
        }
        if (!in_array($params['numbering'], [0, 1, 2, 3], true)) {
            throw new invalid_parameter_exception('Unsupported book numbering mode.');
        }
        if (empty($params['chapters']) || count($params['chapters']) > 200) {
            throw new invalid_parameter_exception('A book must contain between 1 and 200 chapters.');
        }

        $totalsize = 0;
        $assetstotalsize = 0;
        $seensourceids = [];
        foreach ($params['chapters'] as $index => $chapter) {
            $sourceid = trim($chapter['sourceid']);
            $totalsize += strlen($chapter['content']);
            if ($sourceid === '' || isset($seensourceids[$sourceid])) {
                throw new invalid_parameter_exception('Book chapter source ids must be non-empty and unique.');
            }
            $seensourceids[$sourceid] = true;
            if ($totalsize > 5 * 1024 * 1024) {
                throw new invalid_parameter_exception('Combined chapter content exceeds the 5 MiB limit.');
            }
            if (trim($chapter['title']) === '' || \core_text::strlen($chapter['title']) > 255) {
                throw new invalid_parameter_exception('Chapter titles must contain 1 to 255 characters.');
            }
            if ($index === 0 && !empty($chapter['subchapter'])) {
                throw new invalid_parameter_exception('The first book chapter cannot be a subchapter.');
            }
            if (isset($chapter['files']) && count($chapter['files']) > 100) {
                throw new invalid_parameter_exception('A Book chapter cannot contain more than 100 files.');
            }
            $seenfiles = [];
            foreach (($chapter['files'] ?? []) as $file) {
                $filepath = $file['filepath'];
                $filename = $file['filename'];
                if (!preg_match('#^/assets(?:/[^/\\\\\x00]+)*/$#uD', $filepath)
                        || strpos($filepath, '\\') !== false
                        || $filename === '' || $filename === '.' || $filename === '..'
                        || strpos($filename, '/') !== false || strpos($filename, '\\') !== false
                        || strpos($filename, "\0") !== false
                        || preg_match('/[%]|[\x00-\x1F]/', $filepath . $filename)) {
                    throw new invalid_parameter_exception('Invalid Book chapter asset path or filename.');
                }
                foreach (explode('/', trim($filepath, '/')) as $segment) {
                    if ($segment === '' || $segment === '.' || $segment === '..') {
                        throw new invalid_parameter_exception('Invalid Book chapter asset path segment.');
                    }
                }
                $filekey = $filepath . $filename;
                if (isset($seenfiles[$filekey])) {
                    throw new invalid_parameter_exception('Duplicate Book chapter asset path.');
                }
                $seenfiles[$filekey] = true;
                $decoded = base64_decode($file['contentbase64'], true);
                if ($decoded === false || strlen($decoded) > 2 * 1024 * 1024) {
                    throw new invalid_parameter_exception('Invalid base64 or Book asset exceeds 2 MiB.');
                }
                $assetstotalsize += strlen($decoded);
                if ($assetstotalsize + $totalsize > 5 * 1024 * 1024) {
                    throw new invalid_parameter_exception('Combined Book chapter content and assets exceed the 5 MiB activity limit.');
                }
            }
        }

        $mapping = [];
        $seenchapterids = [];
        foreach ($params['chapterids'] as $mappingitem) {
            $sourceid = trim($mappingitem['sourceid']);
            $chapterid = (int)$mappingitem['chapterid'];
            if ($sourceid === '' || $chapterid < 1 || isset($mapping[$sourceid]) || isset($seenchapterids[$chapterid])) {
                throw new invalid_parameter_exception('Invalid or duplicate Book source-to-chapter mapping.');
            }
            $mapping[$sourceid] = $chapterid;
            $seenchapterids[$chapterid] = true;
        }

        $section = $DB->get_record('course_sections', [
            'course' => $course->id,
            'section' => $params['sectionnum'],
        ], '*', MUST_EXIST);

        $lockkey = 'activity_' . hash('sha256', $course->id . '|book');
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
                            && $candidate->modname === 'book'
                            && $candidate->idnumber === $params['idnumber']
                            && (int)$candidate->sectionnum !== (int)$params['sectionnum']) {
                        throw new invalid_parameter_exception('This source idnumber already exists in another course section. Move/update the existing activity explicitly instead of creating a duplicate.');
                    }
                }
            }

            $existing = null;
            foreach ($modinfo->get_cms() as $candidate) {
                if (empty($candidate->deletioninprogress) && $candidate->modname === 'book'
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
                        'module' => $DB->get_field('modules', 'id', ['name' => 'book'], MUST_EXIST),
                    ], '*', MUST_EXIST);
                    $book = $DB->get_record('book', ['id' => $existing->instance], '*', MUST_EXIST);
                    if (empty($mapping) && $DB->record_exists('book_chapters', ['bookid' => $book->id])) {
                        throw new invalid_parameter_exception(
                            'This existing Book has chapters but no source-id mapping manifest. '
                            . 'Refusing to create duplicates; reconcile the legacy chapters first.'
                        );
                    }
                    list($cm, $modulecontext, $module, $moduleinfo, $courseSection) =
                        get_moduleinfo_data($cm, $course);
                    $cm->modname = 'book';
                    $moduleinfo->name = trim($params['name']);
                    $moduleinfo->numbering = $params['numbering'];
                    if ($params['idnumber'] !== '') {
                        $moduleinfo->cmidnumber = $params['idnumber'];
                    }
                    update_moduleinfo($cm, $moduleinfo, $course);
                    $cmid = (int)$existing->id;
                    $instanceid = (int)$existing->instance;
                    $created = false;
                } else {
                    if (!empty($mapping)) {
                        throw new invalid_parameter_exception('Book chapter mappings were supplied but the target Book does not exist. Refusing to attach old chapter ids to a new Book.');
                    }
                    $moduleid = $DB->get_field('modules', 'id', ['name' => 'book'], MUST_EXIST);
                    $moduleinfo = new \stdClass();
                    $moduleinfo->modulename = 'book';
                    $moduleinfo->module = $moduleid;
                    $moduleinfo->course = $course->id;
                    $moduleinfo->section = $section->section;
                    $moduleinfo->name = trim($params['name']);
                    $moduleinfo->intro = '';
                    $moduleinfo->introformat = FORMAT_HTML;
                    $moduleinfo->numbering = $params['numbering'];
                    $moduleinfo->navstyle = 1;
                    $moduleinfo->customtitles = 0;
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
                    $createdmodule = add_moduleinfo($moduleinfo, $course);
                    $cmid = (int)$createdmodule->coursemodule;
                    $instanceid = (int)$createdmodule->instance;
                    $book = $DB->get_record('book', ['id' => $instanceid], '*', MUST_EXIST);
                    $modulecontext = \context_module::instance($cmid);
                    $created = true;
                }

                $modulecontext = \context_module::instance($cmid);
                require_capability('mod/book:edit', $modulecontext);

                foreach ($mapping as $sourceid => $chapterid) {
                    $DB->get_record('book_chapters', [
                        'id' => $chapterid,
                        'bookid' => $book->id,
                    ], '*', MUST_EXIST);
                }

                $fs = get_file_storage();
                // File API blobs are not rolled back with SQL. Keep complete snapshots
                // until the delegated transaction commits, then compensate on failure.
                $filesnapshots = [];
                $createdfilekeys = [];
                $resultmapping = $mapping;
                $createdcount = 0;
                $updatedcount = 0;
                $now = time();
                foreach ($params['chapters'] as $index => $chapterdata) {
                    $sourceid = trim($chapterdata['sourceid']);
                    if (isset($mapping[$sourceid])) {
                        $chapterid = $mapping[$sourceid];
                        $chapter = $DB->get_record('book_chapters', [
                            'id' => $chapterid,
                            'bookid' => $book->id,
                        ], '*', MUST_EXIST);
                        $chapter->pagenum = $index + 1;
                        $chapter->subchapter = empty($chapterdata['subchapter']) ? 0 : 1;
                        $chapter->title = trim($chapterdata['title']);
                        $chapter->content = clean_text($chapterdata['content'], FORMAT_HTML);
                        $chapter->contentformat = FORMAT_HTML;
                        $chapter->timemodified = $now;
                        $DB->update_record('book_chapters', $chapter);
                        \mod_book\event\chapter_updated::create_from_chapter($book, $modulecontext, $chapter)->trigger();
                        $updatedcount++;
                    } else {
                        $chapter = new \stdClass();
                        $chapter->bookid = $book->id;
                        $chapter->pagenum = $index + 1;
                        $chapter->subchapter = empty($chapterdata['subchapter']) ? 0 : 1;
                        $chapter->title = trim($chapterdata['title']);
                        $chapter->content = clean_text($chapterdata['content'], FORMAT_HTML);
                        $chapter->contentformat = FORMAT_HTML;
                        $chapter->hidden = 0;
                        $chapter->timecreated = $now;
                        $chapter->timemodified = $now;
                        $chapter->importsrc = '';
                        $chapter->id = $DB->insert_record('book_chapters', $chapter);
                        \mod_book\event\chapter_created::create_from_chapter($book, $modulecontext, $chapter)->trigger();
                        $resultmapping[$sourceid] = (int)$chapter->id;
                        $createdcount++;
                    }

                    // Omitted files preserve manual/legacy assets; [] explicitly clears them.
                    if (array_key_exists('files', $chapterdata)) {
                        $chapterid = (int)$resultmapping[$sourceid];
                        $existingfiles = $fs->get_area_files(
                            $modulecontext->id, 'mod_book', 'chapter', $chapterid, 'id', false
                        );
                        foreach ($existingfiles as $existingfile) {
                            $filesnapshots[] = [
                                'record' => [
                                    'contextid' => $existingfile->get_contextid(),
                                    'component' => $existingfile->get_component(),
                                    'filearea' => $existingfile->get_filearea(),
                                    'itemid' => $existingfile->get_itemid(),
                                    'filepath' => $existingfile->get_filepath(),
                                    'filename' => $existingfile->get_filename(),
                                    'userid' => $existingfile->get_userid(),
                                    'license' => $existingfile->get_license(),
                                    'author' => $existingfile->get_author(),
                                    'source' => $existingfile->get_source(),
                                    'sortorder' => $existingfile->get_sortorder(),
                                    'timecreated' => $existingfile->get_timecreated(),
                                    'timemodified' => $existingfile->get_timemodified(),
                                ],
                                'content' => $existingfile->get_content(),
                            ];
                            $existingfile->delete();
                        }
                        foreach ($chapterdata['files'] as $file) {
                            $filerecord = [
                                'contextid' => $modulecontext->id,
                                'component' => 'mod_book',
                                'filearea' => 'chapter',
                                'itemid' => $chapterid,
                                'filepath' => $file['filepath'],
                                'filename' => $file['filename'],
                                'userid' => $USER->id,
                            ];
                            $fs->create_file_from_string(
                                $filerecord, base64_decode($file['contentbase64'], true)
                            );
                            $createdfilekeys[] = $filerecord;
                        }
                    }
                }

                book_preload_chapters($book);
                rebuild_course_cache($course->id, true);
                $transaction->allow_commit();
            } catch (\Throwable $exception) {
                try {
                    $transaction->rollback($exception);
                } catch (\Throwable $rollbackexception) {
                    // The delegated rollback rethrows the original exception.
                }
                $compensationerrors = [];
                foreach (array_reverse($createdfilekeys) as $filekey) {
                    try {
                        $newfile = $fs->get_file(
                            $filekey['contextid'], $filekey['component'], $filekey['filearea'],
                            $filekey['itemid'], $filekey['filepath'], $filekey['filename']
                        );
                        if ($newfile) {
                            $newfile->delete();
                        }
                    } catch (\Throwable $compensationexception) {
                        $compensationerrors[] = $compensationexception->getMessage();
                    }
                }
                foreach ($filesnapshots as $snapshot) {
                    try {
                        $fs->create_file_from_string($snapshot['record'], $snapshot['content']);
                    } catch (\Throwable $compensationexception) {
                        $compensationerrors[] = $compensationexception->getMessage();
                    }
                }
                if (!empty($compensationerrors)) {
                    throw new \moodle_exception(
                        'Book synchronization failed and File API compensation was incomplete: '
                        . implode('; ', $compensationerrors),
                        'error'
                    );
                }
                throw $exception;
            }

            return [
                'cmid' => $cmid,
                'instanceid' => $instanceid,
                'modname' => 'book',
                'name' => $params['name'],
                'created' => $created,
                'updated' => !$created,
                'chaptercount' => count($params['chapters']),
                'chapters_created' => $createdcount,
                'chapters_updated' => $updatedcount,
                'chapterids' => array_map(
                    static function($sourceid, $chapterid) {
                        return ['sourceid' => $sourceid, 'chapterid' => (int)$chapterid];
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
            'instanceid' => new \external_value(PARAM_INT, 'Book instance id'),
            'modname' => new \external_value(PARAM_TEXT, 'Module name'),
            'name' => new \external_value(PARAM_TEXT, 'Book name'),
            'created' => new \external_value(PARAM_BOOL, 'Whether a new book was created'),
            'updated' => new \external_value(PARAM_BOOL, 'Whether an existing book was updated'),
            'chaptercount' => new \external_value(PARAM_INT, 'Number of source chapters'),
            'chapters_created' => new \external_value(PARAM_INT, 'Number of new chapters'),
            'chapters_updated' => new \external_value(PARAM_INT, 'Number of updated chapters'),
            'chapterids' => new \external_multiple_structure(
                new \external_single_structure([
                    'sourceid' => new \external_value(PARAM_ALPHANUMEXT, 'Stable source chapter identifier'),
                    'chapterid' => new \external_value(PARAM_INT, 'Moodle Book chapter id'),
                ])
            ),
        ]);
    }
}
