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
            'completionenabled' => new \external_value(PARAM_BOOL, 'Enable activity completion', VALUE_DEFAULT, false),
            'completiontype' => new \external_value(PARAM_ALPHANUMEXT, 'Completion condition: grade or view', VALUE_DEFAULT, 'grade'),
            'questioncount' => new \external_value(PARAM_INT, 'Expected number of GIFT questions', VALUE_DEFAULT, 0),
            'previousgiftsha256' => new \external_value(PARAM_ALPHANUMEXT, 'Previous GIFT SHA-256', VALUE_DEFAULT, ''),
            'syncfields' => new \external_multiple_structure(
                new \external_value(PARAM_ALPHANUMEXT, 'Explicitly source-managed setting'),
                'Settings to synchronize', VALUE_DEFAULT, ['name']
            ),
            'idnumber' => new \external_value(PARAM_ALPHANUMEXT, 'Stable source identifier', VALUE_DEFAULT, ''),
        ]);
    }

    public static function execute(
        $courseid, $sectionnum, $name, $intro, $gift, $timelimit = 0,
        $attempts = 1, $grade = 10, $passingpercent = 0, $shuffleanswers = true,
        $questionsperpage = 1, $completionenabled = false, $completiontype = 'grade', $questioncount = 0, $previousgiftsha256 = '', $syncfields = ['name'], $idnumber = ''
    ) {
        global $CFG, $DB;

        $params = self::validate_parameters(self::execute_parameters(), [
            'courseid' => $courseid,
            'sectionnum' => $sectionnum,
            'idnumber' => $idnumber,
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
            'questioncount' => $questioncount,
            'previousgiftsha256' => $previousgiftsha256,
            'syncfields' => $syncfields,
        ]);

        $allowedfields = [
            'name', 'intro', 'timelimit', 'attempts', 'grade', 'passingpercent',
            'shuffleanswers', 'questionsperpage', 'completion',
        ];
        $syncfields = array_values(array_unique($params['syncfields']));
        foreach ($syncfields as $field) {
            if (!in_array($field, $allowedfields, true)) {
                throw new invalid_parameter_exception('Unsupported Quiz synchronization field: ' . $field);
            }
        }
        if (!in_array('name', $syncfields, true)) {
            $syncfields[] = 'name';
        }
        if ($params['questioncount'] < 1 || $params['questioncount'] > 250) {
            throw new invalid_parameter_exception('Quiz question count must be between 1 and 250.');
        }
        if ($params['previousgiftsha256'] !== ''
                && !preg_match('/^[a-f0-9]{64}$/', $params['previousgiftsha256'])) {
            throw new invalid_parameter_exception('Previous GIFT SHA-256 must be a lowercase hexadecimal digest.');
        }
        if (strlen($params['idnumber']) > 100) {
            throw new \invalid_parameter_exception('Activity idnumber must not exceed 100 characters.');
        }

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
        // Serialize all writes for this module type within the course to avoid check-then-create races.
        $lockkey = 'activity_' . hash('sha256', $course->id . '|' . 'quiz');
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
                            && $candidate->modname === 'quiz'
                            && $candidate->idnumber === $params['idnumber']
                            && (int)$candidate->sectionnum !== (int)$params['sectionnum']) {
                        throw new invalid_parameter_exception('This source idnumber already exists in another course section. Move/update the existing activity explicitly instead of creating a duplicate.');
                    }
                }
            }
            foreach ($modinfo->get_cms() as $existing) {
                if (empty($existing->deletioninprogress) && $existing->modname === 'quiz'
                        && (int)$existing->sectionnum === (int)$params['sectionnum']
                        && ($existing->name === $params['name'] || ($params['idnumber'] !== '' && $existing->idnumber === $params['idnumber']))) {
                    if ($params['idnumber'] !== '' && $existing->name === $params['name']
                            && !empty($existing->idnumber) && $existing->idnumber !== $params['idnumber']) {
                        throw new invalid_parameter_exception('An activity with this name already has a different source idnumber. Refusing to reuse it.');
                    }

                    $quiz = $DB->get_record('quiz', ['id' => $existing->instance], '*', MUST_EXIST);
                    $questioncount = (int)$DB->count_records('quiz_slots', ['quizid' => $quiz->id]);
                    if ($questioncount !== $params['questioncount']) {
                        throw new invalid_parameter_exception(
                            'The existing quiz question count differs from the source. '
                            . 'Question-bank synchronization is not enabled; refusing to alter slots or question identities.'
                        );
                    }
                    if ($questioncount > 0) {
                        if ($params['previousgiftsha256'] === '') {
                            throw new invalid_parameter_exception(
                                'This existing quiz has questions but no prior GIFT digest in the publish manifest. '
                                . 'Refusing to assume that its question content matches the source.'
                            );
                        }
                        $currentgifthash = hash('sha256', $params['gift']);
                        if (!hash_equals($params['previousgiftsha256'], $currentgifthash)) {
                            throw new invalid_parameter_exception(
                                'GIFT question content changed. Quiz question-version synchronization is not enabled; '
                                . 'existing questions and attempts were left untouched.'
                            );
                        }
                    }

                    $transaction = $DB->start_delegated_transaction();
                    try {
                        $cm = $DB->get_record('course_modules', [
                            'id' => $existing->id,
                            'course' => $course->id,
                            'module' => $DB->get_field('modules', 'id', ['name' => 'quiz'], MUST_EXIST),
                        ], '*', MUST_EXIST);
                        list($cm, $modulecontext, $module, $moduleinfo, $courseSection) =
                            get_moduleinfo_data($cm, $course);
                        $cm->modname = 'quiz';
                        $moduleinfo->quizpassword = $moduleinfo->quizpassword ?? '';
                        $attemptcount = (int)$DB->count_records('quiz_attempts', [
                            'quiz' => $quiz->id,
                            'preview' => 0,
                        ]);

                        if (in_array('name', $syncfields, true)) {
                            $moduleinfo->name = trim($params['name']);
                        }
                        if (in_array('intro', $syncfields, true)) {
                            $moduleinfo->intro = clean_text($params['intro'], FORMAT_HTML);
                            $moduleinfo->introformat = FORMAT_HTML;
                        }
                        foreach (['timelimit', 'attempts', 'shuffleanswers', 'questionsperpage'] as $field) {
                            if (in_array($field, $syncfields, true)) {
                                $moduleinfo->$field = $params[$field];
                            }
                        }
                        if (in_array('grade', $syncfields, true)) {
                            if ($attemptcount > 0 && (float)$quiz->grade !== (float)$params['grade']) {
                                throw new invalid_parameter_exception(
                                    'Quiz maximum grade cannot be changed after student attempts exist; grade history is protected.'
                                );
                            }
                            $moduleinfo->grade = $params['grade'];
                        }
                        if (in_array('completion', $syncfields, true)) {
                            $moduleinfo->completion = $params['completionenabled']
                                ? COMPLETION_TRACKING_AUTOMATIC : COMPLETION_TRACKING_NONE;
                            $moduleinfo->completionview = ($params['completionenabled'] && $params['completiontype'] === 'view') ? 1 : 0;
                            $moduleinfo->completionusegrade = ($params['completionenabled'] && $params['completiontype'] === 'grade') ? 1 : 0;
                            $moduleinfo->completionpassgrade = $moduleinfo->completionusegrade;
                        }
                        update_moduleinfo($cm, $moduleinfo, $course);

                        if (in_array('passingpercent', $syncfields, true)) {
                            require_once($CFG->libdir . '/gradelib.php');
                            $gradeitem = \grade_item::fetch([
                                'itemtype' => 'mod',
                                'itemmodule' => 'quiz',
                                'iteminstance' => $quiz->id,
                                'itemnumber' => 0,
                            ]);
                            if ($gradeitem) {
                                $effectivegrade = in_array('grade', $syncfields, true)
                                    ? (float)$params['grade'] : (float)$quiz->grade;
                                $newgradepass = $effectivegrade * (float)$params['passingpercent'] / 100;
                                if ($attemptcount > 0 && (float)$gradeitem->gradepass !== $newgradepass) {
                                    throw new invalid_parameter_exception(
                                        'Quiz passing grade cannot be changed after student attempts exist; grade history is protected.'
                                    );
                                }
                                $gradeitem->gradepass = $newgradepass;
                                $gradeitem->update();
                            }
                        }
                        if ($params['idnumber'] !== '' && empty($existing->idnumber)) {
                            $DB->set_field('course_modules', 'idnumber', $params['idnumber'], ['id' => $existing->id]);
                        }
                        rebuild_course_cache($course->id, true);
                        $transaction->allow_commit();
                    } catch (\Throwable $exception) {
                        $transaction->rollback($exception);
                    }

                    return [
                        'cmid' => (int)$existing->id,
                        'instanceid' => (int)$existing->instance,
                        'modname' => 'quiz',
                        'name' => $params['name'],
                        'created' => false,
                        'updated' => true,
                        'questioncount' => $questioncount,
                        'categoryid' => 0,
                        'giftsha256' => hash('sha256', $params['gift']),
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
            $moduleinfo->cmidnumber = $params['idnumber'];
    
            $tempdir = make_temp_directory('local_magicmoodle');
            $giftfile = tempnam($tempdir, 'gift');
            $giftbytes = $giftfile === false ? false : file_put_contents($giftfile, $params['gift']);
            if ($giftfile === false || $giftbytes !== strlen($params['gift'])) {
                if ($giftfile && is_file($giftfile)) {
                    unlink($giftfile);
                }
                throw new \moodle_exception('cannotcreatetempfile', 'error');
            }
    
            $transaction = null;
            try {
                $transaction = $DB->start_delegated_transaction();
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
                if ($transaction !== null) {
                    $transaction->rollback($exception);
                }
                throw $exception;
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
                'updated' => false,
                'questioncount' => count($format->questionids),
                'categoryid' => (int)$category->id,
                'giftsha256' => hash('sha256', $params['gift']),
            ];
        } finally {
            $lock->release();
        }
    }

    public static function execute_returns() {
        return new \external_single_structure([
            'cmid' => new \external_value(PARAM_INT, 'Course module id'),
            'instanceid' => new \external_value(PARAM_INT, 'Quiz instance id'),
            'modname' => new \external_value(PARAM_TEXT, 'Module name'),
            'name' => new \external_value(PARAM_TEXT, 'Quiz name'),
            'created' => new \external_value(PARAM_BOOL, 'Whether a new quiz was created'),
            'updated' => new \external_value(PARAM_BOOL, 'Whether an existing quiz was updated'),
            'questioncount' => new \external_value(PARAM_INT, 'Number of quiz questions'),
            'categoryid' => new \external_value(PARAM_INT, 'Question category id'),
            'giftsha256' => new \external_value(PARAM_ALPHANUMEXT, 'Source GIFT SHA-256'),
        ]);
    }
}
