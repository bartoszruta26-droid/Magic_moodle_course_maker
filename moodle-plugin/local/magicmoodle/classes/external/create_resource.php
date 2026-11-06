<?php
namespace local_magicmoodle\external;

defined('MOODLE_INTERNAL') || die();

use context_course;
use context_user;
use invalid_parameter_exception;

require_once($CFG->libdir . '/externallib.php');
require_once($CFG->dirroot . '/course/modlib.php');
require_once($CFG->libdir . '/resourcelib.php');
require_once($CFG->dirroot . '/mod/resource/lib.php');
require_once($CFG->dirroot . '/mod/resource/locallib.php');

class create_resource extends \external_api {
    public static function execute_parameters() {
        return new \external_function_parameters([
            'courseid' => new \external_value(PARAM_INT, 'Course id'),
            'sectionnum' => new \external_value(PARAM_INT, 'Zero-based section number'),
            'name' => new \external_value(PARAM_TEXT, 'Resource activity name'),
            'filename' => new \external_value(PARAM_FILE, 'File name'),
            'contentbase64' => new \external_value(PARAM_RAW, 'Base64 encoded file content'),
            'intro' => new \external_value(PARAM_RAW, 'Resource introduction HTML', VALUE_DEFAULT, ''),
            'previousfilename' => new \external_value(PARAM_FILE, 'Previously managed file name', VALUE_DEFAULT, ''),
            'previoussha256' => new \external_value(PARAM_ALPHANUMEXT, 'Previous managed file SHA-256', VALUE_DEFAULT, ''),
            'syncfields' => new \external_multiple_structure(
                new \external_value(PARAM_ALPHANUMEXT, 'Explicitly source-managed setting'),
                'Settings to synchronize', VALUE_DEFAULT, ['name', 'file']
            ),
            'idnumber' => new \external_value(PARAM_ALPHANUMEXT, 'Stable source identifier', VALUE_DEFAULT, ''),
        ]);
    }

    public static function execute($courseid, $sectionnum, $name, $filename, $contentbase64, $intro = '', $previousfilename = '', $previoussha256 = '', $syncfields = ['name', 'file'], $idnumber = '') {
        global $CFG, $DB, $USER;

        $params = self::validate_parameters(self::execute_parameters(), [
            'courseid' => $courseid,
            'sectionnum' => $sectionnum,
            'idnumber' => $idnumber,
            'name' => $name,
            'filename' => $filename,
            'contentbase64' => $contentbase64,
            'intro' => $intro,
            'previousfilename' => $previousfilename,
            'previoussha256' => $previoussha256,
            'syncfields' => $syncfields,
        ]);

        $allowedfields = ['name', 'intro', 'file'];
        $syncfields = array_values(array_unique($params['syncfields']));
        foreach ($syncfields as $field) {
            if (!in_array($field, $allowedfields, true)) {
                throw new invalid_parameter_exception('Unsupported Resource synchronization field: ' . $field);
            }
        }
        if (!in_array('name', $syncfields, true) || !in_array('file', $syncfields, true)) {
            throw new invalid_parameter_exception('Resource synchronization requires name and file fields.');
        }
        if ($params['previoussha256'] !== ''
                && !preg_match('/^[a-f0-9]{64}$/', $params['previoussha256'])) {
            throw new invalid_parameter_exception('Previous Resource SHA-256 must be a lowercase hexadecimal digest.');
        }
        if (strlen($params['idnumber']) > 100) {
            throw new \invalid_parameter_exception('Activity idnumber must not exceed 100 characters.');
        }

        $course = get_course($params['courseid']);
        $coursecontext = context_course::instance($course->id);
        self::validate_context($coursecontext);
        require_capability('moodle/course:manageactivities', $coursecontext);
        require_capability('mod/resource:addinstance', $coursecontext);

        $filename = clean_param($params['filename'], PARAM_FILE);
        if ($params['sectionnum'] < 0 || trim($params['name']) === ''
                || \core_text::strlen($params['name']) > 255
                || $filename === '' || $filename === '.' || $filename === '..'
                || strpos($filename, '/') !== false || strpos($filename, '\\') !== false) {
            throw new invalid_parameter_exception('Invalid resource section, name or filename.');
        }
        if (!is_string($params['contentbase64']) || strlen($params['contentbase64']) > 7 * 1024 * 1024) {
            throw new invalid_parameter_exception('Encoded resource content exceeds the 5 MiB upload limit.');
        }
        $filecontent = base64_decode($params['contentbase64'], true);
        if ($filecontent === false || strlen($filecontent) < 1 || strlen($filecontent) > 5 * 1024 * 1024) {
            throw new invalid_parameter_exception('Resource content must be valid base64 containing 1 byte to 5 MiB.');
        }
        $siteuploadlimit = (int)$CFG->maxbytes;
        $courseuploadlimit = (int)$course->maxbytes;
        $effectiveuploadlimit = ($courseuploadlimit > 0)
            ? min($siteuploadlimit, $courseuploadlimit) : $siteuploadlimit;
        if ($effectiveuploadlimit > 0 && strlen($filecontent) > $effectiveuploadlimit) {
            throw new invalid_parameter_exception('Resource file exceeds the Moodle site or course upload limit.');
        }

        $section = $DB->get_record('course_sections', [
            'course' => $course->id,
            'section' => $params['sectionnum'],
        ], '*', MUST_EXIST);

        // Serialize all writes for this module type within the course to avoid check-then-create races.
        $lockkey = 'activity_' . hash('sha256', $course->id . '|' . 'resource');
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
                            && $candidate->modname === 'resource'
                            && $candidate->idnumber === $params['idnumber']
                            && (int)$candidate->sectionnum !== (int)$params['sectionnum']) {
                        throw new invalid_parameter_exception('This source idnumber already exists in another course section. Move/update the existing activity explicitly instead of creating a duplicate.');
                    }
                }
            }
            foreach ($modinfo->get_cms() as $existing) {
                if (empty($existing->deletioninprogress) && $existing->modname === 'resource'
                        && (int)$existing->sectionnum === (int)$params['sectionnum']
                        && ($existing->name === $params['name'] || ($params['idnumber'] !== '' && $existing->idnumber === $params['idnumber']))) {
                    if ($params['idnumber'] !== '' && $existing->name === $params['name']
                            && !empty($existing->idnumber) && $existing->idnumber !== $params['idnumber']) {
                        throw new invalid_parameter_exception('An activity with this name already has a different source idnumber. Refusing to reuse it.');
                    }

                    $transaction = $DB->start_delegated_transaction();
                    $draftitemid = null;
                    $fs = get_file_storage();
                    $usercontext = context_user::instance($USER->id);
                    try {
                        $cm = $DB->get_record('course_modules', [
                            'id' => $existing->id,
                            'course' => $course->id,
                            'module' => $DB->get_field('modules', 'id', ['name' => 'resource'], MUST_EXIST),
                        ], '*', MUST_EXIST);
                        list($cm, $modulecontext, $module, $moduleinfo, $courseSection) =
                            get_moduleinfo_data($cm, $course);
                        $modulecontext = \context_module::instance($existing->id);
                        $existingfiles = $fs->get_area_files(
                            $modulecontext->id, 'mod_resource', 'content', 0, 'id', false
                        );
                        $oldfile = null;
                        if ($params['previousfilename'] !== '') {
                            if ($params['previoussha256'] === '') {
                                throw new invalid_parameter_exception('A prior Resource file mapping without a digest cannot be updated safely.');
                            }
                            $oldfile = $fs->get_file(
                                $modulecontext->id, 'mod_resource', 'content', 0, '/', $params['previousfilename']
                            );
                            if (!$oldfile) {
                                throw new invalid_parameter_exception('The previously managed Resource file is missing. Refusing to overwrite an unknown file.');
                            }
                            $remotehash = hash('sha256', $oldfile->get_content());
                            if (!hash_equals($params['previoussha256'], $remotehash)) {
                                throw new invalid_parameter_exception('The previously managed Resource file changed in Moodle since the last publication. Resolve this content conflict before synchronizing.');
                            }
                        } else if (!empty($existingfiles)) {
                            throw new invalid_parameter_exception(
                                'This existing Resource has files but no manifest mapping. Refusing to replace an unmanaged file.'
                            );
                        }

                        $contenthash = hash('sha256', $filecontent);
                        $contentchanged = !$oldfile
                            || $params['previousfilename'] !== $filename
                            || !hash_equals($remotehash, $contenthash);
                        if ($contentchanged) {
                            $draftitemid = file_get_unused_draft_itemid();
                            $fileoptions = [
                                'subdirs' => true,
                                'maxfiles' => -1,
                                'maxbytes' => $effectiveuploadlimit,
                            ];
                            file_prepare_draft_area(
                                $draftitemid, $modulecontext->id, 'mod_resource', 'content', 0, $fileoptions
                            );
                            if ($params['previousfilename'] !== '') {
                                $draftold = $fs->get_file(
                                    $usercontext->id, 'user', 'draft', $draftitemid, '/', $params['previousfilename']
                                );
                                if (!$draftold) {
                                    throw new invalid_parameter_exception('The managed Resource file was not copied to the draft area.');
                                }
                                $draftold->delete();
                            }
                            if ($fs->get_file($usercontext->id, 'user', 'draft', $draftitemid, '/', $filename)) {
                                throw new invalid_parameter_exception(
                                    'The new Resource filename already belongs to another file in this activity. Refusing to overwrite it.'
                                );
                            }
                            $fs->create_file_from_string([
                                'contextid' => $usercontext->id,
                                'component' => 'user',
                                'filearea' => 'draft',
                                'itemid' => $draftitemid,
                                'filepath' => '/',
                                'filename' => $filename,
                                'userid' => $USER->id,
                            ], $filecontent);
                            $moduleinfo->files = $draftitemid;
                            $moduleinfo->mainfile = $filename;
                        } else {
                            $moduleinfo->files = IGNORE_FILE_MERGE;
                        }

                        $moduleinfo->name = trim($params['name']);
                        if (in_array('intro', $syncfields, true)) {
                            $moduleinfo->intro = clean_text($params['intro'], FORMAT_HTML);
                            $moduleinfo->introformat = FORMAT_HTML;
                        }
                        if ($params['idnumber'] !== '' && empty($existing->idnumber)) {
                            $moduleinfo->cmidnumber = $params['idnumber'];
                        }
                        update_moduleinfo($cm, $moduleinfo, $course);
                        file_set_sortorder(
                            $modulecontext->id, 'mod_resource', 'content', 0, '/', $filename, 1
                        );
                        rebuild_course_cache($course->id, true);
                        $transaction->allow_commit();
                    } catch (\Throwable $exception) {
                        $transaction->rollback($exception);
                    } finally {
                        if ($draftitemid !== null) {
                            $fs->delete_area_files($usercontext->id, 'user', 'draft', $draftitemid);
                        }
                    }

                    $storedfile = $fs->get_file(
                        $modulecontext->id, 'mod_resource', 'content', 0, '/', $filename
                    );
                    if (!$storedfile) {
                        throw new \moodle_exception('filenotfound', 'error', '', $filename);
                    }
                    return [
                        'cmid' => (int)$existing->id,
                        'instanceid' => (int)$existing->instance,
                        'modname' => 'resource',
                        'name' => $params['name'],
                        'filename' => $filename,
                        'filesize' => (int)$storedfile->get_filesize(),
                        'sha256' => hash('sha256', $storedfile->get_content()),
                        'created' => false,
                        'updated' => true,
                    ];
                }
            }

            $moduleid = $DB->get_field('modules', 'id', ['name' => 'resource'], MUST_EXIST);
            $draftitemid = null;
            $usercontext = context_user::instance($USER->id);
            $fs = get_file_storage();
            $transaction = $DB->start_delegated_transaction();
            try {
                $draftitemid = file_get_unused_draft_itemid();
                $fs->create_file_from_string([
                    'contextid' => $usercontext->id,
                    'component' => 'user',
                    'filearea' => 'draft',
                    'itemid' => $draftitemid,
                    'filepath' => '/',
                    'filename' => $filename,
                    'userid' => $USER->id,
                ], $filecontent);
    
                $moduleinfo = new \stdClass();
                $moduleinfo->modulename = 'resource';
                $moduleinfo->module = $moduleid;
                $moduleinfo->course = $course->id;
                $moduleinfo->section = $section->section;
                $moduleinfo->name = trim($params['name']);
                $moduleinfo->intro = clean_text($params['intro'], FORMAT_HTML);
                $moduleinfo->introformat = FORMAT_HTML;
                $moduleinfo->files = $draftitemid;
                $moduleinfo->display = RESOURCELIB_DISPLAY_AUTO;
                $moduleinfo->popupwidth = 800;
                $moduleinfo->popupheight = 600;
                $moduleinfo->printintro = 1;
                $moduleinfo->showsize = 1;
                $moduleinfo->showtype = 1;
                $moduleinfo->showdate = 0;
                $moduleinfo->filterfiles = 1;
                $moduleinfo->revision = 1;
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
    
                $created = add_moduleinfo($moduleinfo, $course);
                $transaction->allow_commit();
            } catch (\Throwable $exception) {
                $transaction->rollback($exception);
            } finally {
                if ($draftitemid !== null) {
                    $fs->delete_area_files($usercontext->id, 'user', 'draft', $draftitemid);
                }
            }
    
            $modulecontext = \context_module::instance($created->coursemodule);
            $storedfiles = $fs->get_area_files($modulecontext->id, 'mod_resource', 'content', 0, 'sortorder', false);
            $storedsize = 0;
            foreach ($storedfiles as $storedfile) {
                $storedsize += $storedfile->get_filesize();
            }
    
            return [
                'cmid' => (int)$created->coursemodule,
                'instanceid' => (int)$created->instance,
                'modname' => 'resource',
                'name' => $params['name'],
                'filename' => $filename,
                'filesize' => (int)$fs->get_file(
                    $modulecontext->id, 'mod_resource', 'content', 0, '/', $filename
                )->get_filesize(),
                'sha256' => hash('sha256', $filecontent),
                'created' => true,
                'updated' => false,
            ];
        } finally {
            $lock->release();
        }
    }

    public static function execute_returns() {
        return new \external_single_structure([
            'cmid' => new \external_value(PARAM_INT, 'Course module id'),
            'instanceid' => new \external_value(PARAM_INT, 'Resource instance id'),
            'modname' => new \external_value(PARAM_TEXT, 'Module name'),
            'name' => new \external_value(PARAM_TEXT, 'Resource name'),
            'filename' => new \external_value(PARAM_FILE, 'Stored filename'),
            'filesize' => new \external_value(PARAM_INT, 'Stored file size in bytes'),
            'sha256' => new \external_value(PARAM_ALPHANUMEXT, 'Managed file SHA-256'),
            'created' => new \external_value(PARAM_BOOL, 'Whether a new resource was created'),
            'updated' => new \external_value(PARAM_BOOL, 'Whether an existing resource was updated'),
        ]);
    }
}
