<?php
defined('MOODLE_INTERNAL') || die();

$functions = [
    'local_magicmoodle_update_section' => [
        'classname' => '\\local_magicmoodle\\external\\update_section',
        'description' => 'Update a course section name.',
        'type' => 'write',
        'ajax' => false,
        'capabilities' => 'moodle/course:update',
    ],
    'local_magicmoodle_create_book' => [
        'classname' => '\\local_magicmoodle\\external\\create_book',
        'description' => 'Create or update a Book activity and synchronize source-mapped chapters in a course section.',
        'type' => 'write',
        'ajax' => false,
        'capabilities' => 'moodle/course:manageactivities',
    ],
    'local_magicmoodle_create_glossary' => [
        'classname' => '\\local_magicmoodle\\external\\create_glossary',
        'description' => 'Create or update a Glossary activity and synchronize source-mapped term definitions.',
        'type' => 'write',
        'ajax' => false,
        'capabilities' => 'moodle/course:manageactivities, mod/glossary:addinstance, mod/glossary:write',
    ],
    'local_magicmoodle_create_resource' => [
        'classname' => '\\local_magicmoodle\\external\\create_resource',
        'description' => 'Create or update a Resource activity using manifest-bound file identity and Moodle File API.',
        'type' => 'write',
        'ajax' => false,
        'capabilities' => 'moodle/course:manageactivities, mod/resource:addinstance',
    ],
    'local_magicmoodle_create_assignment' => [
        'classname' => '\\local_magicmoodle\\external\\create_assignment',
        'description' => 'Create or update an Assignment while protecting existing submissions and unmanaged settings.',
        'type' => 'write',
        'ajax' => false,
        'capabilities' => 'moodle/course:manageactivities, mod/assign:addinstance',
    ],
    'local_magicmoodle_create_quiz' => [
        'classname' => '\\local_magicmoodle\\external\\create_quiz',
        'description' => 'Create or update Quiz settings while preserving question slots, attempts and grade history; GIFT import is used only for new quizzes.',
        'type' => 'write',
        'ajax' => false,
        'capabilities' => 'moodle/course:manageactivities, mod/quiz:addinstance, moodle/question:add',
    ],
    'local_magicmoodle_create_activity' => [
        'classname' => '\\local_magicmoodle\\external\\create_activity',
        'description' => 'Create a Page, Label or URL activity in a course section.',
        'type' => 'write',
        'ajax' => false,
        'capabilities' => 'moodle/course:manageactivities',
    ],
];
