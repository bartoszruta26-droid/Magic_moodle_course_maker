<?php
namespace local_magicmoodle\external;

defined('MOODLE_INTERNAL') || die();

use context_course;
use invalid_parameter_exception;

require_once($CFG->libdir . '/externallib.php');
require_once($CFG->dirroot . '/course/modlib.php');

class create_book extends \external_api {
    public static function execute_parameters() {
        return new \external_function_parameters([
            'courseid' => new \external_value(PARAM_INT, 'Course id'),
            'sectionnum' => new \external_value(PARAM_INT, 'Zero-based section number'),
            'idnumber' => new \external_value(PARAM_ALPHANUMEXT, 'Stable source identifier', VALUE_DEFAULT, ''),
            'name' => new \external_value(PARAM_TEXT, 'Book activity name'),
            'chapters' => new \external_multiple_structure(
                new \external_single_structure([
                    'title' => new \external_value(PARAM_TEXT, 'Chapter title'),
                    'content' => new \external_value(PARAM_RAW, 'Chapter HTML content'),
                    'subchapter' => new \external_value(PARAM_BOOL, 'Whether this is a subchapter', VALUE_DEFAULT, false),
                ]),
                'Book chapters'
            ),
            'numbering' => new \external_value(PARAM_INT, 'Book numbering: 0 none, 1 numbers, 2 bullets, 3 indented', VALUE_DEFAULT, 1),
        ]);
    }

    public static function execute($courseid, $sectionnum, $name, $chapters, $numbering = 1, $idnumber = '') {
        global $DB;

        $params = self::validate_parameters(self::execute_parameters(), [
            'courseid' => $courseid,
            'sectionnum' => $sectionnum,
            'idnumber' => $idnumber,
            'name' => $name,
            'chapters' => $chapters,
            'numbering' => $numbering,
        ]);
        if (strlen($params['idnumber']) > 100) {
            throw new \\invalid_parameter_exception('Activity idnumber must not exceed 100 characters.');
        }

        $course = get_course($params['courseid']);
        $context = context_course::instance($course->id);
        self::validate_context($context);
        require_capability('moodle/course:manageactivities', $context);

        if ($params['sectionnum'] < 0 || trim($params['name']) === '') {
            throw new invalid_parameter_exception('Invalid section number or empty book name.');
        }
        if (!in_array($params['numbering'], [0, 1, 2, 3], true)) {
            throw new invalid_parameter_exception('Unsupported book numbering mode.');
        }
        if (empty($params['chapters']) || count($params['chapters']) > 200) {
            throw new invalid_parameter_exception('A book must contain between 1 and 200 chapters.');
        }
        $totalsize = 0;
        foreach ($params['chapters'] as $index => $chapter) {
            $totalsize += strlen($chapter['content']);
            if ($totalsize > 5 * 1024 * 1024) {
                throw new invalid_parameter_exception('Combined chapter content exceeds the 5 MiB limit.');
            }
            if (trim($chapter['title']) === '' || \core_text::strlen($chapter['title']) > 255) {
                throw new invalid_parameter_exception('Chapter titles must contain 1 to 255 characters.');
            }
            if ($index === 0 && !empty($chapter['subchapter'])) {
                throw new invalid_parameter_exception('The first book chapter cannot be a subchapter.');
            }
        }

        $section = $DB->get_record('course_sections', [
            'course' => $course->id,
            'section' => $params['sectionnum'],
        ], '*', MUST_EXIST);

        $modinfo = get_fast_modinfo($course);
        foreach ($modinfo->get_cms() as $existing) {
            if (empty($existing->deletioninprogress) && $existing->modname === 'book'
                    && (int)$existing->sectionnum === (int)$params['sectionnum']
                    && ($existing->name === $params['name'] || ($params['idnumber'] !== '' && $existing->idnumber === $params['idnumber']))) {
                if ($params['idnumber'] !== '' && empty($existing->idnumber)) {
                    $DB->set_field('course_modules', 'idnumber', $params['idnumber'], ['id' => $existing->id]);
                }
                return [
                    'cmid' => (int)$existing->id,
                    'instanceid' => (int)$existing->instance,
                    'modname' => 'book',
                    'name' => $params['name'],
                    'created' => false,
                    'chaptercount' => (int)$DB->count_records('book_chapters', ['bookid' => $existing->instance]),
                ];
            }
        }

        $moduleid = $DB->get_field('modules', 'id', ['name' => 'book'], MUST_EXIST);
        $moduleinfo = new \stdClass();
        $moduleinfo->modulename = 'book';
        $moduleinfo->module = $moduleid;
        $moduleinfo->course = $course->id;
        $moduleinfo->section = $section->section;
        $moduleinfo->name = $params['name'];
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

        $transaction = $DB->start_delegated_transaction();
        try {
            $created = add_moduleinfo($moduleinfo, $course);
            $book = $DB->get_record('book', ['id' => $created->instance], '*', MUST_EXIST);
            $modulecontext = \context_module::instance($created->coursemodule);
            require_capability('mod/book:edit', $modulecontext);
            $now = time();

            foreach ($params['chapters'] as $index => $chapterdata) {
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
            }

            require_once($CFG->dirroot . '/mod/book/locallib.php');
            book_preload_chapters($book);
            $transaction->allow_commit();
        } catch (\Throwable $exception) {
            $transaction->rollback($exception);
        }

        return [
            'cmid' => (int)$created->coursemodule,
            'instanceid' => (int)$created->instance,
            'modname' => 'book',
            'name' => $params['name'],
            'created' => true,
            'chaptercount' => count($params['chapters']),
        ];
    }

    public static function execute_returns() {
        return new \external_single_structure([
            'cmid' => new \external_value(PARAM_INT, 'Course module id'),
            'instanceid' => new \external_value(PARAM_INT, 'Book instance id'),
            'modname' => new \external_value(PARAM_TEXT, 'Module name'),
            'name' => new \external_value(PARAM_TEXT, 'Book name'),
            'created' => new \external_value(PARAM_BOOL, 'Whether a new book was created'),
            'chaptercount' => new \external_value(PARAM_INT, 'Number of chapters'),
        ]);
    }
}
