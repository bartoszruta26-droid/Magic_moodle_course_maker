<?php
defined('MOODLE_INTERNAL') || die();

use local_magicmoodle\external\create_assignment;
use local_magicmoodle\external\create_book;
use local_magicmoodle\external\create_glossary;
use local_magicmoodle\external\create_quiz;
use local_magicmoodle\external\create_resource;

/**
 * Integration tests for in-place synchronization against a real Moodle 4.1 database.
 *
 * @package    local_magicmoodle
 * @category   test
 */
final class local_magicmoodle_sync_external_test extends advanced_testcase {
    protected function setUp(): void {
        parent::setUp();
        $this->resetAfterTest();
        $this->setAdminUser();
    }

    /**
     * Create a course with a section available to module endpoints.
     *
     * @return stdClass
     */
    private function create_sync_course(): stdClass {
        return $this->getDataGenerator()->create_course(['numsections' => 2]);
    }

    public function test_book_chapter_sync_preserves_chapter_and_module_ids(): void {
        global $DB;

        $course = $this->create_sync_course();
        $chapters = [
            ['sourceid' => 'chapter-intro', 'title' => 'Start', 'content' => '<p>Pierwsza treść</p>', 'subchapter' => false],
            ['sourceid' => 'chapter-main', 'title' => 'Rozdział główny', 'content' => '<p>Druga treść</p>', 'subchapter' => false],
        ];

        $created = create_book::execute(
            $course->id, 1, 'Podręcznik', $chapters, [], 1, 'it-book-001'
        );
        $this->assertTrue($created['created']);
        $this->assertCount(2, $created['chapterids']);

        $updatedchapters = [
            ['sourceid' => 'chapter-intro', 'title' => 'Wprowadzenie', 'content' => '<p>Treść po zmianie</p>', 'subchapter' => false],
            ['sourceid' => 'chapter-main', 'title' => 'Rozdział główny', 'content' => '<p>Druga treść</p>', 'subchapter' => false],
        ];
        $updated = create_book::execute(
            $course->id, 1, 'Podręcznik po zmianie', $updatedchapters, $created['chapterids'], 1, 'it-book-001'
        );

        $this->assertFalse($updated['created']);
        $this->assertTrue($updated['updated']);
        $this->assertSame($created['cmid'], $updated['cmid']);
        $this->assertSame($created['instanceid'], $updated['instanceid']);
        $this->assertSame($created['chapterids'], $updated['chapterids']);
        $this->assertSame(2, $updated['chapters_updated']);

        $chapter = $DB->get_record('book_chapters', ['id' => $created['chapterids'][0]['chapterid']], '*', MUST_EXIST);
        $this->assertSame('Wprowadzenie', $chapter->title);
        $this->assertSame('<p>Treść po zmianie</p>', $chapter->content);
    }

    public function test_book_chapter_files_are_created_and_replaced_without_affecting_other_chapters(): void {
        global $USER;

        $course = $this->create_sync_course();
        $firstbytes = "\x89PNG\r\n\x1a\nfirst";
        $secondbytes = "\x89PNG\r\n\x1a\nsecond";
        $created = create_book::execute(
            $course->id,
            1,
            'Podręcznik z grafikami',
            [
                [
                    'sourceid' => 'chapter-one',
                    'title' => 'Pierwszy',
                    'content' => '<p><img src="@@PLUGINFILE@@/assets/first.png"></p>',
                    'subchapter' => false,
                    'files' => [[
                        'filepath' => '/assets/',
                        'filename' => 'first.png',
                        'contentbase64' => base64_encode($firstbytes),
                    ]],
                ],
                [
                    'sourceid' => 'chapter-two',
                    'title' => 'Drugi',
                    'content' => '<p><img src="@@PLUGINFILE@@/assets/second.png"></p>',
                    'subchapter' => false,
                    'files' => [[
                        'filepath' => '/assets/',
                        'filename' => 'second.png',
                        'contentbase64' => base64_encode($secondbytes),
                    ]],
                ],
            ],
            [],
            1,
            'it-book-assets-001'
        );

        $context = context_module::instance($created['cmid']);
        $fs = get_file_storage();
        $firstchapterid = $created['chapterids'][0]['chapterid'];
        $secondchapterid = $created['chapterids'][1]['chapterid'];
        $firstfile = $fs->get_file($context->id, 'mod_book', 'chapter', $firstchapterid, '/assets/', 'first.png');
        $secondfile = $fs->get_file($context->id, 'mod_book', 'chapter', $secondchapterid, '/assets/', 'second.png');
        $this->assertNotFalse($firstfile);
        $this->assertNotFalse($secondfile);
        $this->assertSame($firstbytes, $firstfile->get_content());
        $this->assertSame($secondbytes, $secondfile->get_content());

        $replacementbytes = "\x89PNG\r\n\x1a\nreplacement";
        $updated = create_book::execute(
            $course->id,
            1,
            'Podręcznik z grafikami',
            [
                [
                    'sourceid' => 'chapter-one',
                    'title' => 'Pierwszy po zmianie',
                    'content' => '<p><img src="@@PLUGINFILE@@/assets/replacement.png"></p>',
                    'subchapter' => false,
                    'files' => [[
                        'filepath' => '/assets/',
                        'filename' => 'replacement.png',
                        'contentbase64' => base64_encode($replacementbytes),
                    ]],
                ],
                [
                    'sourceid' => 'chapter-two',
                    'title' => 'Drugi',
                    'content' => '<p><img src="@@PLUGINFILE@@/assets/second.png"></p>',
                    'subchapter' => false,
                    'files' => [[
                        'filepath' => '/assets/',
                        'filename' => 'second.png',
                        'contentbase64' => base64_encode($secondbytes),
                    ]],
                ],
            ],
            $created['chapterids'],
            1,
            'it-book-assets-001'
        );

        $this->assertTrue($updated['updated']);
        $this->assertSame($created['chapterids'], $updated['chapterids']);
        $this->assertFalse($fs->file_exists($context->id, 'mod_book', 'chapter', $firstchapterid, '/assets/', 'first.png'));
        $replacement = $fs->get_file($context->id, 'mod_book', 'chapter', $firstchapterid, '/assets/', 'replacement.png');
        $preserved = $fs->get_file($context->id, 'mod_book', 'chapter', $secondchapterid, '/assets/', 'second.png');
        $this->assertNotFalse($replacement);
        $this->assertNotFalse($preserved);
        $this->assertSame($replacementbytes, $replacement->get_content());
        $this->assertSame($secondbytes, $preserved->get_content());
    }

    public function test_book_rejects_invalid_asset_paths_and_base64_before_writing(): void {
        $course = $this->create_sync_course();
        $invalidcases = [
            ['filepath' => '/assets/../outside/', 'filename' => 'bad.bin', 'contentbase64' => base64_encode('x')],
            ['filepath' => '/assets/', 'filename' => 'bad.bin', 'contentbase64' => '%%%not-base64%%%'],
        ];
        foreach ($invalidcases as $index => $file) {
            try {
                create_book::execute(
                    $course->id,
                    1,
                    'Nieprawidłowe zasoby ' . $index,
                    [[
                        'sourceid' => 'chapter-invalid-' . $index,
                        'title' => 'Rozdział',
                        'content' => '<p>Treść</p>',
                        'subchapter' => false,
                        'files' => [$file],
                    ]],
                    [],
                    1,
                    'it-book-invalid-' . $index
                );
                $this->fail('Expected invalid Book asset payload to be rejected.');
            } catch (invalid_parameter_exception $exception) {
                $this->assertNotEmpty($exception->getMessage());
            }
        }
    }

    public function test_book_update_rolls_back_all_chapters_after_mid_operation_database_failure(): void {
        global $DB;

        if ($DB->get_dbfamily() !== 'mysql') {
            $this->markTestSkipped('The rollback fault-injection test requires MySQL/MariaDB triggers.');
        }

        $course = $this->create_sync_course();
        $chapters = [
            ['sourceid' => 'chapter-one', 'title' => 'Pierwszy', 'content' => '<p>Stara 1</p>', 'subchapter' => false],
            ['sourceid' => 'chapter-two', 'title' => 'Drugi', 'content' => '<p>Stara 2</p>', 'subchapter' => false],
        ];
        $created = create_book::execute(
            $course->id, 1, 'Książka rollback', $chapters, [], 1, 'it-book-rollback'
        );

        $prefix = $DB->get_prefix();
        $table = $prefix . 'book_chapters';
        $trigger = 'local_mm_book_rollback_test';
        $DB->execute("DROP TRIGGER IF EXISTS {$trigger}");
        // Moodle's database abstraction rejects multi-statement SQL. Use a
        // single-statement trigger; the NOT NULL constraint raises an error
        // only when the second chapter receives the sentinel title.
        $DB->execute(
            "CREATE TRIGGER {$trigger} BEFORE UPDATE ON {$table} FOR EACH ROW "
            . "SET NEW.title = IF(NEW.title = 'FAIL_ROLLBACK', NULL, NEW.title)"
        );

        try {
            $changed = [
                ['sourceid' => 'chapter-one', 'title' => 'Pierwszy po zmianie', 'content' => '<p>Nowa 1</p>', 'subchapter' => false],
                ['sourceid' => 'chapter-two', 'title' => 'FAIL_ROLLBACK', 'content' => '<p>Nowa 2</p>', 'subchapter' => false],
            ];
            try {
                create_book::execute(
                    $course->id, 1, 'Książka rollback', $changed, $created['chapterids'], 1, 'it-book-rollback'
                );
                $this->fail('Expected the injected database failure to abort the transaction.');
            } catch (\Throwable $exception) {
                $this->assertStringContainsString('cannot be null', strtolower($exception->getMessage()));
            }
        } finally {
            $DB->execute("DROP TRIGGER IF EXISTS {$trigger}");
        }

        $first = $DB->get_record('book_chapters', ['id' => $created['chapterids'][0]['chapterid']], '*', MUST_EXIST);
        $second = $DB->get_record('book_chapters', ['id' => $created['chapterids'][1]['chapterid']], '*', MUST_EXIST);
        $this->assertSame('Pierwszy', $first->title);
        $this->assertSame('<p>Stara 1</p>', $first->content);
        $this->assertSame('Drugi', $second->title);
        $this->assertSame('<p>Stara 2</p>', $second->content);
    }

    public function test_glossary_sync_preserves_entry_ids_and_updates_terms(): void {
        global $DB;

        $course = $this->create_sync_course();
        $entries = [
            ['sourceid' => 'term-one', 'term' => 'Masaż', 'definition' => '<p>Definicja pierwsza</p>'],
            ['sourceid' => 'term-two', 'term' => 'Rehabilitacja', 'definition' => '<p>Definicja druga</p>'],
        ];
        $created = create_glossary::execute(
            $course->id, 1, 'Słownik', '<p>Opis</p>', $entries, [], 'it-glossary-001'
        );
        $this->assertTrue($created['created']);
        $this->assertCount(2, $created['entryids']);

        $updated = create_glossary::execute(
            $course->id,
            1,
            'Słownik po zmianie',
            '<p>Nowy opis</p>',
            [
                ['sourceid' => 'term-one', 'term' => 'Masaż leczniczy', 'definition' => '<p>Nowa definicja</p>'],
                ['sourceid' => 'term-two', 'term' => 'Rehabilitacja', 'definition' => '<p>Definicja druga</p>'],
            ],
            $created['entryids'],
            'it-glossary-001'
        );

        $this->assertFalse($updated['created']);
        $this->assertTrue($updated['updated']);
        $this->assertSame($created['cmid'], $updated['cmid']);
        $this->assertSame($created['instanceid'], $updated['instanceid']);
        $this->assertSame($created['entryids'], $updated['entryids']);
        $this->assertSame(2, $updated['entries_updated']);

        $entry = $DB->get_record('glossary_entries', ['id' => $created['entryids'][0]['entryid']], '*', MUST_EXIST);
        $this->assertSame('Masaż leczniczy', $entry->concept);
        $this->assertSame('<p>Nowa definicja</p>', $entry->definition);
    }

    public function test_assignment_sync_preserves_instance_and_existing_submission_records(): void {
        global $DB;

        $course = $this->create_sync_course();
        $created = create_assignment::execute(
            $course->id, 1, 'Zadanie', '<p>Opis</p>', 0, 0, 0, 100, 'both',
            3, 10485760, false, false, false,
            ['name', 'intro', 'duedate', 'grade'], 'it-assignment-001'
        );
        $this->assertTrue($created['created']);

        $updated = create_assignment::execute(
            $course->id, 1, 'Zadanie po zmianie', '<p>Nowy opis</p>', 0, 2000000000, 0, 100, 'both',
            3, 10485760, false, false, false,
            ['name', 'intro', 'duedate', 'grade'], 'it-assignment-001'
        );
        $this->assertFalse($updated['created']);
        $this->assertTrue($updated['updated']);
        $this->assertSame($created['cmid'], $updated['cmid']);
        $this->assertSame($created['instanceid'], $updated['instanceid']);

        $assignment = $DB->get_record('assign', ['id' => $created['instanceid']], '*', MUST_EXIST);
        $this->assertSame('Zadanie po zmianie', $assignment->name);
        $this->assertSame(2000000000, (int)$assignment->duedate);
        $this->assertSame(0, $DB->count_records('assign_submission', ['assignment' => $assignment->id]));
    }

    public function test_resource_sync_replaces_only_the_manifest_managed_file(): void {
        global $DB, $USER;

        $course = $this->create_sync_course();
        $firstcontent = 'pierwsza wersja pliku';
        $created = create_resource::execute(
            $course->id, 1, 'Dokument', 'source.txt', base64_encode($firstcontent), '',
            '', '', ['name', 'file'], 'it-resource-001'
        );
        $this->assertTrue($created['created']);

        $context = context_module::instance($created['cmid']);
        $fs = get_file_storage();
        $fs->create_file_from_string([
            'contextid' => $context->id,
            'component' => 'mod_resource',
            'filearea' => 'content',
            'itemid' => 0,
            'filepath' => '/',
            'filename' => 'manual-extra.txt',
            'userid' => $USER->id,
        ], 'plik ręczny');

        $secondcontent = 'druga wersja pliku';
        $updated = create_resource::execute(
            $course->id, 1, 'Dokument po zmianie', 'source.txt', base64_encode($secondcontent), '',
            'source.txt', $created['sha256'], ['name', 'file'], 'it-resource-001'
        );
        $this->assertFalse($updated['created']);
        $this->assertTrue($updated['updated']);
        $this->assertSame($created['cmid'], $updated['cmid']);
        $this->assertSame($created['instanceid'], $updated['instanceid']);

        $managed = $fs->get_file($context->id, 'mod_resource', 'content', 0, '/', 'source.txt');
        $manual = $fs->get_file($context->id, 'mod_resource', 'content', 0, '/', 'manual-extra.txt');
        $this->assertNotFalse($managed);
        $this->assertNotFalse($manual);
        $this->assertSame($secondcontent, $managed->get_content());
        $this->assertSame('plik ręczny', $manual->get_content());
    }

    public function test_quiz_settings_sync_preserves_question_slots_and_attempts(): void {
        global $DB;

        $course = $this->create_sync_course();
        $gift = "::sync-question:: Czy synchronizacja zachowuje pytania? {TRUE}";
        $created = create_quiz::execute(
            $course->id, 1, 'Quiz', '<p>Opis</p>', $gift, 0, 2, 10, 0,
            true, 1, false, 'grade', 1, '', ['name', 'intro'], 'it-quiz-001'
        );
        $this->assertTrue($created['created']);
        $slotsbefore = $DB->get_records('quiz_slots', ['quizid' => $created['instanceid']], 'slot ASC');
        $student = $this->getDataGenerator()->create_and_enrol($course, 'student');
        $this->setUser($student);
        $quizgenerator = $this->getDataGenerator()->get_plugin_generator('mod_quiz');
        $attempt = $quizgenerator->create_attempt($created['instanceid'], $student->id);
        $this->assertNotEmpty($attempt->id);
        $this->assertSame((int)$student->id, (int)$attempt->userid);
        $this->assertSame(0, (int)$attempt->preview);
        $this->setAdminUser();

        $updated = create_quiz::execute(
            $course->id, 1, 'Quiz po zmianie', '<p>Nowy opis</p>', $gift, 600, 2, 10, 0,
            false, 1, false, 'grade', 1, $created['giftsha256'], ['name', 'intro', 'timelimit', 'shuffleanswers'],
            'it-quiz-001'
        );
        $this->assertFalse($updated['created']);
        $this->assertTrue($updated['updated']);
        $this->assertSame($created['cmid'], $updated['cmid']);
        $this->assertSame($created['instanceid'], $updated['instanceid']);
        $slotidsafter = array_keys($DB->get_records('quiz_slots', ['quizid' => $created['instanceid']], 'slot ASC'));
        $this->assertSame(array_keys($slotsbefore), $slotidsafter);
        $this->assertSame(1, $DB->count_records('quiz_attempts', ['quiz' => $created['instanceid'], 'preview' => 0]));
    }
}
