package pl.aria.magicmoodle

import java.net.HttpURLConnection
import java.net.URL
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.booleanOrNull
import kotlinx.serialization.json.intOrNull
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import kotlinx.serialization.json.contentOrNull

data class CourseSummary(
    val id: String,
    val name: String,
    val shortName: String,
    val sections: Int?,
    val activities: Int?,
    val loadError: Boolean,
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

    internal fun listCoursesBlocking(): List<CourseSummary> {
        val endpoint = baseUrl.trimEnd('/') + "/courses"
        val connection = URL(endpoint).openConnection() as HttpURLConnection
        try {
            connection.requestMethod = "GET"
            connection.connectTimeout = 10_000
            connection.readTimeout = 15_000
            connection.setRequestProperty("Accept", "application/json")
            if (bearerToken.isNotBlank()) {
                connection.setRequestProperty("Authorization", "Bearer $bearerToken")
            }

            val status = connection.responseCode
            val stream = if (status in 200..299) connection.inputStream else connection.errorStream
            val responseBody = stream?.bufferedReader(Charsets.UTF_8)?.use { it.readText() }.orEmpty()
            if (status !in 200..299) {
                throw ApiException(status, apiErrorMessage(responseBody, status))
            }
            return parseCourseListJson(responseBody)
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
    try {
        val root = Json.parseToJsonElement(body).jsonObject
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
    } catch (error: ApiException) {
        throw error
    } catch (error: Exception) {
        throw ApiException(null, "API zwróciło nieprawidłowy format danych.")
    }
}

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
