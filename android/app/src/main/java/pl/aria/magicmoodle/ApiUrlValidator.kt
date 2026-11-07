package pl.aria.magicmoodle

import java.net.URI

object ApiUrlValidator {
    fun isValid(value: String): Boolean {
        return runCatching {
            val uri = URI(value.trim())
            (uri.scheme == "https" || uri.scheme == "http") &&
                !uri.host.isNullOrBlank() &&
                uri.userInfo == null &&
                uri.query == null &&
                uri.fragment == null
        }.getOrDefault(false)
    }
}
