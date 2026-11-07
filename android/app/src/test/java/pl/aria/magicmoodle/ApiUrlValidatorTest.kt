package pl.aria.magicmoodle

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class ApiUrlValidatorTest {
    @Test
    fun acceptsHttpAndHttpsBaseUrls() {
        assertTrue(ApiUrlValidator.isValid("https://moodle.example/api/v1"))
        assertTrue(ApiUrlValidator.isValid("http://10.0.2.2:8765/api/v1"))
    }

    @Test
    fun rejectsUnsupportedOrMalformedUrls() {
        assertFalse(ApiUrlValidator.isValid("ftp://moodle.example"))
        assertFalse(ApiUrlValidator.isValid("https:///api/v1"))
        assertFalse(ApiUrlValidator.isValid("moodle.example/api/v1"))
        assertFalse(ApiUrlValidator.isValid("https://user:password@moodle.example"))
        assertFalse(ApiUrlValidator.isValid("https://moodle.example/api/v1?token=secret"))
    }
}
