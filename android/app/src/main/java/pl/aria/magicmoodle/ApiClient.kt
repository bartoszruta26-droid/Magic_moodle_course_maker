package pl.aria.magicmoodle

import java.net.HttpURLConnection
import java.net.URLEncoder
import java.net.URL
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.booleanOrNull
import kotlinx.serialization.json.intOrNull
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import kotlinx.serialization.json.contentOrNull
import kotlinx.serialization.json.put

data class CourseSummary(
    val id: String,
    val name: String,
    val shortName: String,
    val sections: Int?,
    val activities: Int?,
    val loadError: Boolean,
)

data class CourseSection(
    val id: String,
    val name: String,
    val activityCount: Int,
)

data class CourseDetails(
    val id: String,
    val name: String,
    val shortName: String,
    val description: String,
    val sections: List<CourseSection>,
    val activityCount: Int,
)

data class ValidationFinding(
    val severity: String,
    val code: String,
    val path: String,
    val message: String,
)

data class CourseValidation(
    val ok: Boolean,
    val errors: List<ValidationFinding>,
    val warnings: List<ValidationFinding>,
)

data class CourseDraft(
    val draftId: String,
    val courseId: String,
    val revision: Int,
)

data class DraftPreview(
    val draft: CourseDraft,
    val fullName: String,
    val shortName: String,
    val description: String,
    val sections: List<CourseSection>,
    val validation: CourseValidation,
)

class ApiException(
    val statusCode: Int?,
    override val message: String,
) : Exception(message)

class ApiClient(
    private val baseUrl: String,
    private val bearerToken: String = "",
) {
    suspend fun listCourses(): List<CourseSummary> = withContext(Dispatchers.IO) {
        listCoursesBlocking()
    }

    suspend fun getCourseDetails(courseId: String): CourseDetails = withContext(Dispatchers.IO) {
        parseCourseDetailsJson(requestJson("/courses/${encodePathSegment(courseId)}", "GET").toString())
    }

    suspend fun validateCourse(courseId: String): CourseValidation = withContext(Dispatchers.IO) {
        parseCourseValidationJson(
            requestJson("/courses/${encodePathSegment(courseId)}/validation", "POST").toString(),
        )
    }

    suspend fun createDraft(courseId: String): CourseDraft = withContext(Dispatchers.IO) {
        parseCourseDraftJson(
            requestJson(
                "/courses/${encodePathSegment(courseId)}/drafts",
                "POST",
                buildJsonObject {},
            ).toString(),
        )
    }

    suspend fun previewDraft(draftId: String): DraftPreview = withContext(Dispatchers.IO) {
        parseDraftPreviewJson(
            requestJson("/drafts/${encodePathSegment(draftId)}/preview", "GET").toString(),
        )
    }

    suspend fun updateDraft(
        draftId: String,
        expectedRevision: Int,
        fullName: String,
        shortName: String,
        description: String,
        sectionNames: Map<String, String>,
    ): CourseDraft = withContext(Dispatchers.IO) {
        val changes = buildJsonObject {
            put("full_name", JsonPrimitive(fullName))
            put("short_name", JsonPrimitive(shortName))
            put("description", JsonPrimitive(description))
            put(
                "section_names",
                buildJsonObject {
                    sectionNames.forEach { (id, name) -> put(id, JsonPrimitive(name)) }
                },
            )
        }
        val payload = buildJsonObject {
            put("expected_revision", JsonPrimitive(expectedRevision))
            put("changes", changes)
        }
        parseCourseDraftJson(
            requestJson(
                "/drafts/${encodePathSegment(draftId)}/update",
                "POST",
                payload,
            ).toString(),
        )
    }

    internal fun listCoursesBlocking(): List<CourseSummary> =
        parseCourseListJson(requestJson("/courses", "GET").toString())

    private fun requestJson(path: String, method: String, body: JsonObject? = null): JsonObject {
        val endpoint = baseUrl.trimEnd('/') + path
        val connection = URL(endpoint).openConnection() as HttpURLConnection
        try {
            connection.requestMethod = method
            connection.connectTimeout = 10_000
            connection.readTimeout = 15_000
            connection.setRequestProperty("Accept", "application/json")
            if (bearerToken.isNotBlank()) {
                connection.setRequestProperty("Authorization", "Bearer $bearerToken")
            }
            if (body != null) {
                connection.doOutput = true
                connection.setRequestProperty("Content-Type", "application/json; charset=utf-8")
                connection.outputStream.use { output ->
                    output.write(body.toString().toByteArray(Charsets.UTF_8))
                }
            }

            val status = connection.responseCode
            val stream = if (status in 200..299) connection.inputStream else connection.errorStream
            val responseBody = stream?.bufferedReader(Charsets.UTF_8)?.use { it.readText() }.orEmpty()
            if (status !in 200..299) {
                throw ApiException(status, apiErrorMessage(responseBody, status))
            }
            return try {
                Json.parseToJsonElement(responseBody).jsonObject
            } catch (error: Exception) {
                throw ApiException(status, "API zwróciło nieprawidłowy format danych.")
            }
        } catch (error: ApiException) {
            throw error
        } catch (error: Exception) {
            throw ApiException(null, "Nie udało się połączyć z API: ${error.message ?: "błąd sieci"}.")
        } finally {
            connection.disconnect()
        }
    }
}

internal fun parseCourseListJson(body: String): List<CourseSummary> {
    val root = parseRoot(body)
    val data = root["data"]?.jsonArray
        ?: throw ApiException(null, "Odpowiedź API nie zawiera listy kursów.")
    return data.map { element ->
        val item = element.jsonObject
        CourseSummary(
            id = item.string("id"),
            name = item.string("name"),
            shortName = item.string("short_name"),
            sections = item.intOrNull("sections"),
            activities = item.intOrNull("activities"),
            loadError = item.booleanOrNull("load_error") ?: false,
        )
    }
}

internal fun parseCourseDetailsJson(body: String): CourseDetails {
    val data = parseRoot(body)["data"]?.jsonObject
        ?: throw ApiException(null, "Odpowiedź API nie zawiera szczegółów kursu.")
    val sections = parseSections(data["sections"]?.jsonArray.orEmpty())
    val statistics = data["statistics"]?.jsonObject
    return CourseDetails(
        id = data.string("id"),
        name = data.string("name"),
        shortName = data.string("short_name"),
        description = data.string("description"),
        sections = sections,
        activityCount = statistics?.intOrNull("activity_count") ?: 0,
    )
}

internal fun parseCourseValidationJson(body: String): CourseValidation {
    val data = parseRoot(body)["data"]?.jsonObject
        ?: throw ApiException(null, "Odpowiedź API nie zawiera raportu walidacji.")
    return parseValidationObject(data)
}

internal fun parseCourseDraftJson(body: String): CourseDraft {
    val data = parseRoot(body)["data"]?.jsonObject
        ?: throw ApiException(null, "Odpowiedź API nie zawiera wersji roboczej.")
    return CourseDraft(
        draftId = data.string("draft_id"),
        courseId = data.string("course_id"),
        revision = data.intOrNull("revision")
            ?: throw ApiException(null, "Wersja robocza nie zawiera numeru rewizji."),
    )
}

internal fun parseDraftPreviewJson(body: String): DraftPreview {
    val data = parseRoot(body)["data"]?.jsonObject
        ?: throw ApiException(null, "Odpowiedź API nie zawiera podglądu wersji roboczej.")
    val draftData = data["draft"]?.jsonObject
        ?: throw ApiException(null, "Podgląd nie zawiera metadanych wersji roboczej.")
    val course = data["course"]?.jsonObject
        ?: throw ApiException(null, "Podgląd nie zawiera kursu.")
    val courseData = course["course"]?.jsonObject
        ?: throw ApiException(null, "Podgląd nie zawiera metadanych kursu.")
    val validation = data["validation"]?.jsonObject
        ?: throw ApiException(null, "Podgląd nie zawiera walidacji.")
    return DraftPreview(
        draft = CourseDraft(
            draftId = draftData.string("draft_id"),
            courseId = draftData.string("course_id"),
            revision = draftData.intOrNull("revision")
                ?: throw ApiException(null, "Wersja robocza nie zawiera numeru rewizji."),
        ),
        fullName = courseData.string("full_name"),
        shortName = courseData.string("short_name"),
        description = courseData.string("description"),
        sections = parseSections(course["sections"]?.jsonArray.orEmpty()),
        validation = parseValidationObject(validation),
    )
}

private fun parseSections(items: kotlinx.serialization.json.JsonArray): List<CourseSection> =
    items.map { element ->
        val section = element.jsonObject
        CourseSection(
            id = section.string("id"),
            name = section.string("name"),
            activityCount = section.intOrNull("activity_count") ?: 0,
        )
    }

private fun parseValidationObject(data: JsonObject): CourseValidation =
    CourseValidation(
        ok = data.booleanOrNull("ok") ?: false,
        errors = data["errors"]?.jsonArray.orEmpty().map { parseFinding(it.jsonObject) },
        warnings = data["warnings"]?.jsonArray.orEmpty().map { parseFinding(it.jsonObject) },
    )

private fun parseFinding(item: JsonObject) = ValidationFinding(
    severity = item.string("severity"),
    code = item.string("code"),
    path = item.string("path"),
    message = item.string("message"),
)

private fun parseRoot(body: String): JsonObject {
    return try {
        Json.parseToJsonElement(body).jsonObject
    } catch (error: Exception) {
        throw ApiException(null, "API zwróciło nieprawidłowy format danych.")
    }
}

private fun encodePathSegment(value: String): String =
    URLEncoder.encode(value, Charsets.UTF_8.name()).replace("+", "%20")

private fun JsonObject.string(name: String): String =
    this[name]?.jsonPrimitive?.contentOrNull.orEmpty()

private fun JsonObject.intOrNull(name: String): Int? =
    this[name]?.jsonPrimitive?.intOrNull

private fun JsonObject.booleanOrNull(name: String): Boolean? =
    this[name]?.jsonPrimitive?.booleanOrNull

private fun apiErrorMessage(body: String, status: Int): String {
    return runCatching {
        val root = Json.parseToJsonElement(body).jsonObject
        root["error"]?.jsonObject?.get("message")?.jsonPrimitive?.contentOrNull
    }.getOrNull() ?: "Serwer API zwrócił HTTP $status."
}
