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

    @Test(expected = ApiException::class)
    fun rejectsResponseWithoutDataArray() {
        parseCourseListJson("""{"meta":{"api_version":"1"}}""")
    }
}
