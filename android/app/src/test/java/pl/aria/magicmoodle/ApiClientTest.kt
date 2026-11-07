package pl.aria.magicmoodle

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class ApiClientTest {
    @Test
    fun parsesCourseListResponse() {
        val courses = parseCourseListJson(
            """
            {
              "data": [
                {
                  "id": "med10",
                  "name": "Kurs MED.10",
                  "short_name": "MED10",
                  "sections": 12,
                  "activities": 48,
                  "load_error": false
                }
              ],
              "meta": { "api_version": "1" }
            }
            """.trimIndent(),
        )

        assertEquals(1, courses.size)
        assertEquals("med10", courses.first().id)
        assertEquals("Kurs MED.10", courses.first().name)
        assertEquals(12, courses.first().sections)
        assertEquals(48, courses.first().activities)
        assertFalse(courses.first().loadError)
    }

    @Test
    fun preservesMalformedCourseFlagAndNullableCounts() {
        val courses = parseCourseListJson(
            """{"data":[{"id":"broken","name":"broken","load_error":true}],"meta":{"api_version":"1"}}""",
        )

        assertTrue(courses.single().loadError)
        assertEquals(null, courses.single().sections)
        assertEquals(null, courses.single().activities)
    }


    @Test
    fun parsesCourseDetailsResponse() {
        val details = parseCourseDetailsJson(
            """
            {
              "data": {
                "id": "med10",
                "name": "Kurs MED.10",
                "short_name": "MED10",
                "description": "Opis kursu",
                "sections": [
                  {"id": "intro", "name": "Wprowadzenie", "activity_count": 3}
                ],
                "statistics": {"section_count": 1, "activity_count": 3}
              },
              "meta": {"api_version": "1"}
            }
            """.trimIndent(),
        )

        assertEquals("med10", details.id)
        assertEquals("Opis kursu", details.description)
        assertEquals("Wprowadzenie", details.sections.single().name)
        assertEquals(3, details.activityCount)
    }

    @Test
    fun parsesValidationErrorsAndWarnings() {
        val report = parseCourseValidationJson(
            """
            {
              "data": {
                "ok": false,
                "errors": [
                  {"severity": "error", "code": "MISSING_NAME", "path": "course.yaml", "message": "Brak nazwy"}
                ],
                "warnings": [
                  {"severity": "warning", "code": "NO_TAGS", "path": "tags.yaml", "message": "Brak tagów"}
                ]
              },
              "meta": {"api_version": "1"}
            }
            """.trimIndent(),
        )

        assertFalse(report.ok)
        assertEquals("MISSING_NAME", report.errors.single().code)
        assertEquals("NO_TAGS", report.warnings.single().code)
    }

    @Test(expected = ApiException::class)
    fun rejectsResponseWithoutDataArray() {
        parseCourseListJson("""{"meta":{"api_version":"1"}}""")
    }
}
