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
        'description' => 'Create a Book activity and its chapters in a course section.',
        'type' => 'write',
        'ajax' => false,
        'capabilities' => 'moodle/course:manageactivities',
    ],
    'local_magicmoodle_create_activity' => [
        'classname' => '\\local_magicmoodle\\external\\create_activity',
        'description' => 'Create a Page, Label or URL activity in a course section.',
        'type' => 'write',
        'ajax' => false,
        'capabilities' => 'moodle/course:manageactivities',
    ],
];
