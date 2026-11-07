package pl.aria.magicmoodle

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.launch

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val preferences = getSharedPreferences("magic_moodle_settings", MODE_PRIVATE)
        val initialUrl = preferences.getString("api_base_url", "").orEmpty()

        setContent {
            MagicMoodleApp(
                initialServerUrl = initialUrl,
                onSaveServerUrl = { value ->
                    preferences.edit().putString("api_base_url", value).apply()
                },
            )
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun MagicMoodleApp(
    initialServerUrl: String,
    onSaveServerUrl: (String) -> Unit,
) {
    var serverUrl by rememberSaveable { mutableStateOf(initialServerUrl) }
    var savedServerUrl by rememberSaveable { mutableStateOf(initialServerUrl) }
    var apiToken by remember { mutableStateOf("") }
    var settingsVisible by rememberSaveable { mutableStateOf(initialServerUrl.isBlank()) }
    var statusMessage by rememberSaveable {
        mutableStateOf("Oczekiwanie na konfigurację usługi API.")
    }
    var courses by remember { mutableStateOf<List<CourseSummary>>(emptyList()) }
    var isLoading by remember { mutableStateOf(false) }
    var errorMessage by remember { mutableStateOf<String?>(null) }
    val scope = rememberCoroutineScope()

    MaterialTheme {
        Scaffold(
            topBar = {
                TopAppBar(
                    title = { Text("Magic Moodle") },
                    actions = {
                        TextButton(onClick = { settingsVisible = !settingsVisible }) {
                            Text(if (settingsVisible) "Kursy" else "Ustawienia")
                        }
                    },
                )
            },
        ) { contentPadding ->
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(contentPadding)
                    .padding(20.dp),
                verticalArrangement = Arrangement.spacedBy(16.dp),
            ) {
                Text(
                    text = "Mobilna pracownia kursów",
                    style = MaterialTheme.typography.headlineSmall,
                )

                if (settingsVisible) {
                    Card(modifier = Modifier.fillMaxWidth()) {
                        Column(
                            modifier = Modifier.padding(16.dp),
                            verticalArrangement = Arrangement.spacedBy(12.dp),
                        ) {
                            Text(
                                text = "Połączenie z API v1",
                                style = MaterialTheme.typography.titleMedium,
                            )
                            OutlinedTextField(
                                value = serverUrl,
                                onValueChange = { serverUrl = it },
                                modifier = Modifier.fillMaxWidth(),
                                label = { Text("Adres bazowy API") },
                                placeholder = { Text("https://serwer.example/api/v1") },
                                supportingText = {
                                    Text("Adres HTTPS z prefiksem /api/v1.")
                                },
                                singleLine = true,
                            )
                            OutlinedTextField(
                                value = apiToken,
                                onValueChange = { apiToken = it },
                                modifier = Modifier.fillMaxWidth(),
                                label = { Text("Token Bearer (opcjonalny)") },
                                visualTransformation = PasswordVisualTransformation(),
                                supportingText = {
                                    Text("Token pozostaje w pamięci bieżącej sesji i nie jest zapisywany.")
                                },
                                singleLine = true,
                            )
                            Button(
                                onClick = {
                                    val normalized = serverUrl.trim().trimEnd('/')
                                    onSaveServerUrl(normalized)
                                    savedServerUrl = normalized
                                    serverUrl = normalized
                                    settingsVisible = false
                                    statusMessage = "Zapisano adres usługi API."
                                    errorMessage = null
                                },
                                enabled = ApiUrlValidator.isValid(serverUrl),
                                modifier = Modifier.fillMaxWidth(),
                            ) {
                                Text("Zapisz konfigurację")
                            }
                        }
                    }
                } else {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                    ) {
                        Column(modifier = Modifier.weight(1f)) {
                            Text("Serwer", style = MaterialTheme.typography.titleSmall)
                            Text(savedServerUrl, style = MaterialTheme.typography.bodySmall)
                        }
                        TextButton(onClick = { settingsVisible = true }) {
                            Text("Zmień")
                        }
                    }
                    Button(
                        onClick = {
                            scope.launch {
                                isLoading = true
                                errorMessage = null
                                try {
                                    courses = ApiClient(savedServerUrl, apiToken).listCourses()
                                    statusMessage = "Pobrano kursów: ${courses.size}"
                                } catch (error: ApiException) {
                                    courses = emptyList()
                                    errorMessage = error.message
                                    statusMessage = "Błąd połączenia z API."
                                } finally {
                                    isLoading = false
                                }
                            }
                        },
                        enabled = ApiUrlValidator.isValid(savedServerUrl) && !isLoading,
                        modifier = Modifier.fillMaxWidth(),
                    ) {
                        Text(if (isLoading) "Pobieranie…" else "Pobierz kursy")
                    }

                    errorMessage?.let { message ->
                        Text(
                            text = message,
                            color = MaterialTheme.colorScheme.error,
                            style = MaterialTheme.typography.bodyMedium,
                        )
                    }

                    if (isLoading) {
                        CircularProgressIndicator()
                    } else if (courses.isEmpty() && errorMessage == null) {
                        Text(
                            text = "Brak pobranych kursów. Wybierz „Pobierz kursy”, aby odczytać dane z API.",
                            style = MaterialTheme.typography.bodyMedium,
                        )
                    } else {
                        LazyColumn(
                            modifier = Modifier.weight(1f),
                            verticalArrangement = Arrangement.spacedBy(8.dp),
                        ) {
                            items(courses, key = { it.id }) { course ->
                                CourseCard(course)
                            }
                        }
                    }
                }

                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    text = statusMessage,
                    style = MaterialTheme.typography.bodySmall,
                )
            }
        }
    }
}

@Composable
private fun CourseCard(course: CourseSummary) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(6.dp),
        ) {
            Text(course.name, style = MaterialTheme.typography.titleMedium)
            Text(course.shortName, style = MaterialTheme.typography.bodySmall)
            Text(
                text = "${course.sections ?: "—"} sekcji · ${course.activities ?: "—"} aktywności",
                style = MaterialTheme.typography.bodyMedium,
            )
            if (course.loadError) {
                Text(
                    "Kurs wymaga kontroli — wystąpił błąd odczytu.",
                    color = MaterialTheme.colorScheme.error,
                )
            }
        }
    }
}
