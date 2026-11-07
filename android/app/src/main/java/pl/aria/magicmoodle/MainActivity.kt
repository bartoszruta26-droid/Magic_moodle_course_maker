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
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.Card
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
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

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
    var settingsVisible by rememberSaveable { mutableStateOf(initialServerUrl.isBlank()) }
    var statusMessage by rememberSaveable {
        mutableStateOf("Oczekiwanie na konfigurację usługi API.")
    }

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
                    .padding(20.dp)
                    .verticalScroll(rememberScrollState()),
                verticalArrangement = Arrangement.spacedBy(16.dp),
            ) {
                Text(
                    text = "Mobilna pracownia kursów",
                    style = MaterialTheme.typography.headlineSmall,
                )
                Text(
                    text = "Przegląd kursów, kontrola jakości materiałów i statusy publikacji.",
                    style = MaterialTheme.typography.bodyLarge,
                )

                if (settingsVisible) {
                    Card(modifier = Modifier.fillMaxWidth()) {
                        Column(
                            modifier = Modifier.padding(16.dp),
                            verticalArrangement = Arrangement.spacedBy(12.dp),
                        ) {
                            Text(
                                text = "Połączenie z API",
                                style = MaterialTheme.typography.titleMedium,
                            )
                            OutlinedTextField(
                                value = serverUrl,
                                onValueChange = { serverUrl = it },
                                modifier = Modifier.fillMaxWidth(),
                                label = { Text("Adres bazowy API") },
                                placeholder = { Text("https://serwer.example/api/v1") },
                                supportingText = {
                                    Text("Wymagany adres HTTP lub HTTPS bez danych logowania.")
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
                                },
                                enabled = ApiUrlValidator.isValid(serverUrl),
                                modifier = Modifier.fillMaxWidth(),
                            ) {
                                Text("Zapisz konfigurację")
                            }
                        }
                    }
                } else {
                    Card(modifier = Modifier.fillMaxWidth()) {
                        Column(
                            modifier = Modifier.padding(16.dp),
                            verticalArrangement = Arrangement.spacedBy(8.dp),
                        ) {
                            Text(
                                text = "Skonfigurowany serwer",
                                style = MaterialTheme.typography.titleMedium,
                            )
                            Text(
                                text = savedServerUrl,
                                style = MaterialTheme.typography.bodyMedium,
                            )
                            Text(
                                text = "Po wdrożeniu API lista kursów zostanie pobrana z serwera. " +
                                    "Ten etap dostarcza konfigurację klienta, bez pozorowania danych.",
                                style = MaterialTheme.typography.bodyMedium,
                            )
                            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                TextButton(onClick = { settingsVisible = true }) {
                                    Text("Zmień adres")
                                }
                                TextButton(
                                    onClick = {
                                        statusMessage =
                                            "Połączenie sieciowe zostanie włączone po wdrożeniu API."
                                    },
                                ) {
                                    Text("Status integracji")
                                }
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
