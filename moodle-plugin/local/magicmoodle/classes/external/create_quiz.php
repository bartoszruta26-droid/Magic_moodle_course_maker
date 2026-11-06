<?php
namespace local_magicmoodle\external;

defined('MOODLE_INTERNAL') || die();

use context_course;
use invalid_parameter_exception;

require_once($CFG->libdir . '/externallib.php');
require_once($CFG->dirroot . '/course/modlib.php');
require_once($CFG->libdir . '/questionlib.php');
require_once($CFG->dirroot . '/mod/quiz/lib.php');
require_once($CFG->dirroot . '/mod/quiz/locallib.php');
require_once($CFG->dirroot . '/question/format.php');
require_once($CFG->dirroot . '/question/format/gift/format.php');

class create_quiz extends \external_api {
    public static function execute_parameters() {
        return new \external_function_parameters([
            'courseid' => new \external_value(PARAM_INT, 'Course id'),
            'sectionnum' => new \external_value(PARAM_INT, 'Zero-based section number'),
            'name' => new \external_value(PARAM_TEXT, 'Quiz name'),
            'intro' => new \external_value(PARAM_RAW, 'Quiz introduction HTML', VALUE_DEFAULT, ''),
            'gift' => new \external_value(PARAM_RAW, 'GIFT source text'),
            'timelimit' => new \external_value(PARAM_INT, 'Time limit in seconds', VALUE_DEFAULT, 0),
            'attempts' => new \external_value(PARAM_INT, 'Allowed attempts; zero means unlimited', VALUE_DEFAULT, 1),
            'grade' => new \external_value(PARAM_FLOAT, 'Maximum quiz grade', VALUE_DEFAULT, 10),
            'passingpercent' => new \external_value(PARAM_FLOAT, 'Passing threshold as percent', VALUE_DEFAULT, 0),
            'shuffleanswers' => new \external_value(PARAM_BOOL, 'Shuffle answers', VALUE_DEFAULT, true),
            'questionsperpage' => new \external_value(PARAM_INT, 'Questions per page', VALUE_DEFAULT, 1),
        ]);
    }

    public static function execute(
        $courseid, $sectionnum, $name, $intro, $gift, $timelimit = 0,
        $attempts = 1, $grade = 10, $passingpercent = 0, $shuffleanswers = true,
        $questionsperpage = 1, $completionenabled = false, $completiontype = 'grade'
    ) {
        global $CFG, $DB;

        $params = self::validate_parameters(self::execute_parameters(), [
            'courseid' => $courseid,
            'sectionnum' => $sectionnum,
            'name' => $name,
            'intro' => $intro,
            'gift' => $gift,
            'timelimit' => $timelimit,
            'attempts' => $attempts,
            'grade' => $grade,
            'passingpercent' => $passingpercent,
            'shuffleanswers' => $shuffleanswers,
            'questionsperpage' => $questionsperpage,
            'completionenabled' => $completionenabled,
            'completiontype' => $completiontype,
        ]);

        $course = get_course($params['courseid']);
        $coursecontext = context_course::instance($course->id);
        self::validate_context($coursecontext);
        require_capability('moodle/course:manageactivities', $coursecontext);
        require_capability('mod/quiz:addinstance', $coursecontext);
        require_capability('moodle/question:add', $coursecontext);
        if (!has_any_capability(['moodle/question:usemine', 'moodle/question:useall'], $coursecontext)) {
            throw new invalid_parameter_exception('The service account must be allowed to use questions in the course context.');
        }

        if ($params['sectionnum'] < 0 || trim($params['name']) === ''
                || \core_text::strlen($params['name']) > 255) {
            throw new invalid_parameter_exception('Invalid section number or quiz name.');
        }
        if (!is_string($params['gift']) || trim($params['gift']) === ''
                || strlen($params['gift']) > 2 * 1024 * 1024) {
            throw new invalid_parameter_exception('GIFT source must contain 1 byte to 2 MiB.');
        }
        if ($params['timelimit'] < 0 || $params['timelimit'] > 86400
                || $params['attempts'] < 0 || $params['attempts'] > 10
                || $params['grade'] <= 0 || $params['grade'] > 1000
                || $params['passingpercent'] < 0 || $params['passingpercent'] > 100
                || $params['questionsperpage'] < 0 || $params['questionsperpage'] > 50
                || !in_array($params['completiontype'], ['grade', 'view'], true)
                || ($params['completionenabled'] && $params['completiontype'] === 'grade' && $params['passingpercent'] <= 0)) {
            throw new invalid_parameter_exception('Quiz settings are outside supported limits.');
        }

        $section = $DB->get_record('course_sections', [
            'course' => $course->id,
            'section' => $params['sectionnum'],
        ], '*', MUST_EXIST);

        // Reuse an existing quiz with the same name and section; never re-import questions.
        $modinfo = get_fast_modinfo($course);
        foreach ($modinfo->get_cms() as $existing) {
            if (empty($existing->deletioninprogress) && $existing->modname === 'quiz'
                    && (int)$existing->sectionnum === (int)$params['sectionnum']
                    && $existing->name === $params['name']) {
                return [
                    'cmid' => (int)$existing->id,
                    'instanceid' => (int)$existing->instance,
                    'modname' => 'quiz',
                    'name' => $params['name'],
                    'created' => false,
                    'questioncount' => (int)$DB->count_records('quiz_slots', ['quizid' => $existing->instance]),
                    'categoryid' => 0,
                ];
            }
        }

        $moduleid = $DB->get_field('modules', 'id', ['name' => 'quiz'], MUST_EXIST);
        $moduleinfo = new \stdClass();
        $moduleinfo->modulename = 'quiz';
        $moduleinfo->module = $moduleid;
        $moduleinfo->course = $course->id;
        $moduleinfo->section = $section->section;
        $moduleinfo->name = trim($params['name']);
        $moduleinfo->intro = clean_text($params['intro'], FORMAT_HTML);
        $moduleinfo->introformat = FORMAT_HTML;
        $moduleinfo->timeopen = 0;
        $moduleinfo->timeclose = 0;
        $moduleinfo->timelimit = $params['timelimit'];
        $moduleinfo->overduehandling = 'autosubmit';
        $moduleinfo->graceperiod = 0;
        $moduleinfo->grade = $params['grade'];
        $moduleinfo->attempts = $params['attempts'];
        $moduleinfo->grademethod = 1;
        $moduleinfo->questionsperpage = $params['questionsperpage'];
        $moduleinfo->navmethod = 'free';
        $moduleinfo->shuffleanswers = $params['shuffleanswers'] ? 1 : 0;
        $moduleinfo->preferredbehaviour = 'deferredfeedback';
        $moduleinfo->canredoquestions = 0;
        $moduleinfo->attemptonlast = 0;
        $moduleinfo->quizpassword = '';
        $moduleinfo->decimalpoints = 2;
        $moduleinfo->questiondecimalpoints = -1;
        $moduleinfo->showuserpicture = 0;
        $moduleinfo->browsersecurity = '-';
        $moduleinfo->feedbackboundarycount = -1;

        // Review settings: no answers during the attempt; show review after closing.
        foreach (['attempt', 'correctness', 'marks', 'specificfeedback',
                'generalfeedback', 'rightanswer', 'overallfeedback'] as $field) {
            $moduleinfo->{$field . 'during'} = 0;
            $moduleinfo->{$field . 'immediately'} = 0;
            $moduleinfo->{$field . 'open'} = 0;
            $moduleinfo->{$field . 'closed'} = 1;
        }

        $moduleinfo->visible = 1;
        $moduleinfo->groupmode = 0;
        $moduleinfo->groupingid = 0;
        $moduleinfo->availability = null;
        $moduleinfo->completion = $params['completionenabled']
            ? COMPLETION_TRACKING_AUTOMATIC : COMPLETION_TRACKING_NONE;
        $moduleinfo->completionview = ($params['completionenabled'] && $params['completiontype'] === 'view') ? 1 : 0;
        $moduleinfo->completionusegrade = ($params['completionenabled'] && $params['completiontype'] === 'grade') ? 1 : 0;
        $moduleinfo->completionpassgrade = $moduleinfo->completionusegrade;
        $moduleinfo->completionexpected = 0;
        $moduleinfo->showdescription = 0;
        $moduleinfo->visibleoncoursepage = 1;
        $moduleinfo->cmidnumber = '';

        $tempdir = make_temp_directory('local_magicmoodle');
        $giftfile = tempnam($tempdir, 'gift');
        if ($giftfile === false || file_put_contents($giftfile, $params['gift']) === false) {
            if ($giftfile && is_file($giftfile)) {
                unlink($giftfile);
            }
            throw new \moodle_exception('cannotcreatetempfile', 'error');
        }

        $transaction = $DB->start_delegated_transaction();
        try {
            $created = add_moduleinfo($moduleinfo, $course);
            $quiz = $DB->get_record('quiz', ['id' => $created->instance], '*', MUST_EXIST);

            $category = question_make_default_categories([$coursecontext]);
            if (!$category) {
                throw new \moodle_exception('cannotfinddefaultcategory', 'question');
            }

            $format = new \qformat_gift();
            $format->setCategory($category);
            $format->setCourse($course);
            $format->setFilename($giftfile);
            $format->setRealfilename('questions.gift');
            $format->setStoponerror(true);
            $format->set_display_progress(false);

            ob_start();
            try {
                $imported = $format->importprocess();
            } finally {
                ob_end_clean();
            }
            if (!$imported || $format->importerrors > 0 || empty($format->questionids)) {
                throw new \moodle_exception('importparseerror', 'question');
            }
            if (count($format->questionids) > 250) {
                throw new invalid_parameter_exception('A single quiz is limited to 250 imported questions.');
            }

            foreach ($format->questionids as $questionid) {
                quiz_add_quiz_question((int)$questionid, $quiz);
            }
            quiz_update_sumgrades($quiz);
            quiz_set_grade((float)$params['grade'], $quiz);

            if ($params['passingpercent'] > 0) {
                require_once($CFG->libdir . '/gradelib.php');
                $gradeitem = \grade_item::fetch([
                    'itemtype' => 'mod',
                    'itemmodule' => 'quiz',
                    'iteminstance' => $quiz->id,
                    'itemnumber' => 0,
                ]);
                if ($gradeitem) {
                    $gradeitem->gradepass = (float)$params['grade'] * (float)$params['passingpercent'] / 100;
                    $gradeitem->update();
                }
            }

            $transaction->allow_commit();
        } catch (\Throwable $exception) {
            $transaction->rollback($exception);
        } finally {
            if (is_file($giftfile)) {
                unlink($giftfile);
            }
        }

        return [
            'cmid' => (int)$created->coursemodule,
            'instanceid' => (int)$created->instance,
            'modname' => 'quiz',
            'name' => $params['name'],
            'created' => true,
            'questioncount' => count($format->questionids),
            'categoryid' => (int)$category->id,
        ];
    }

    public static function execute_returns() {
        return new \external_single_structure([
            'cmid' => new \external_value(PARAM_INT, 'Course module id'),
            'instanceid' => new \external_value(PARAM_INT, 'Quiz instance id'),
            'modname' => new \external_value(PARAM_TEXT, 'Module name'),
            'name' => new \external_value(PARAM_TEXT, 'Quiz name'),
            'created' => new \external_value(PARAM_BOOL, 'Whether a new quiz was created'),
            'questioncount' => new \external_value(PARAM_INT, 'Number of quiz questions'),
            'categoryid' => new \external_value(PARAM_INT, 'Question category id'),
        ]);
    }
}
