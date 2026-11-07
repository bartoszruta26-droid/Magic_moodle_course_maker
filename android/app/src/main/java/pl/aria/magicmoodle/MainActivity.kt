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
    var selectedDetails by remember { mutableStateOf<CourseDetails?>(null) }
    var selectedValidation by remember { mutableStateOf<CourseValidation?>(null) }
    var detailsLoading by remember { mutableStateOf(false) }
    var draftPreview by remember { mutableStateOf<DraftPreview?>(null) }
    var draftEditorVisible by remember { mutableStateOf(false) }
    var draftLoading by remember { mutableStateOf(false) }
    var draftSaving by remember { mutableStateOf(false) }
    var draftFullName by remember { mutableStateOf("") }
    var draftShortName by remember { mutableStateOf("") }
    var draftDescription by remember { mutableStateOf("") }
    var draftSectionNames by remember { mutableStateOf<Map<String, String>>(emptyMap()) }
    val scope = rememberCoroutineScope()

    fun openDraftEditor(courseId: String) {
        scope.launch {
            draftLoading = true
            errorMessage = null
            try {
                val client = ApiClient(savedServerUrl, apiToken)
                val existing = draftPreview?.takeIf { it.draft.courseId == courseId }
                val preview = if (existing == null) {
                    val created = client.createDraft(courseId)
                    client.previewDraft(created.draftId)
                } else {
                    client.previewDraft(existing.draft.draftId)
                }
                draftPreview = preview
                draftFullName = preview.fullName
                draftShortName = preview.shortName
                draftDescription = preview.description
                draftSectionNames = preview.sections.associate { it.id to it.name }
                draftEditorVisible = true
                statusMessage = "Otwarto wersję roboczą, rewizja ${preview.draft.revision}."
            } catch (error: ApiException) {
                errorMessage = error.message
                statusMessage = "Nie udało się otworzyć wersji roboczej."
            } finally {
                draftLoading = false
            }
        }
    }

    fun saveDraft() {
        val current = draftPreview ?: return
        scope.launch {
            draftSaving = true
            errorMessage = null
            try {
                val client = ApiClient(savedServerUrl, apiToken)
                val updated = client.updateDraft(
                    draftId = current.draft.draftId,
                    expectedRevision = current.draft.revision,
                    fullName = draftFullName,
                    shortName = draftShortName,
                    description = draftDescription,
                    sectionNames = draftSectionNames,
                )
                val preview = client.previewDraft(updated.draftId)
                draftPreview = preview
                draftEditorVisible = false
                statusMessage = "Zapisano wersję roboczą, rewizja ${preview.draft.revision}. "
                    + "Walidacja: ${if (preview.validation.ok) "poprawna" else "wymaga poprawy"}."
            } catch (error: ApiException) {
                errorMessage = error.message
                statusMessage = "Nie udało się zapisać wersji roboczej."
            } finally {
                draftSaving = false
            }
        }
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
                                label = { Text("Token Bearer (wymagany do edycji)") },
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
                                    selectedDetails = null
                                    selectedValidation = null
                                    draftPreview = null
                                    draftEditorVisible = false
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

                    if (isLoading || detailsLoading || draftLoading || draftSaving) {
                        CircularProgressIndicator()
                    }
                    selectedDetails?.let { details ->
                        CourseDetailsCard(
                            details = details,
                            validation = selectedValidation,
                            onEditDraft = { openDraftEditor(details.id) },
                        )
                    }
                    if (draftEditorVisible && draftPreview != null) {
                        CourseDraftEditorCard(
                            preview = draftPreview!!,
                            fullName = draftFullName,
                            onFullNameChange = { draftFullName = it },
                            shortName = draftShortName,
                            onShortNameChange = { draftShortName = it },
                            description = draftDescription,
                            onDescriptionChange = { draftDescription = it },
                            sectionNames = draftSectionNames,
                            onSectionNameChange = { id, value ->
                                draftSectionNames = draftSectionNames + (id to value)
                            },
                            saving = draftSaving,
                            onSave = { saveDraft() },
                            onCancel = { draftEditorVisible = false },
                        )
                    } else {
                        draftPreview?.let { DraftPreviewCard(it) }
                    }

                    if (!isLoading && courses.isEmpty() && errorMessage == null) {
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
                                CourseCard(course) {
                                    scope.launch {
                                        detailsLoading = true
                                        errorMessage = null
                                        selectedDetails = null
                                        selectedValidation = null
                                        draftPreview = null
                                        draftEditorVisible = false
                                        try {
                                            val client = ApiClient(savedServerUrl, apiToken)
                                            selectedDetails = client.getCourseDetails(course.id)
                                            selectedValidation = client.validateCourse(course.id)
                                            statusMessage = "Pobrano szczegóły i raport walidacji."
                                        } catch (error: ApiException) {
                                            errorMessage = error.message
                                            statusMessage = "Nie udało się pobrać szczegółów kursu."
                                        } finally {
                                            detailsLoading = false
                                        }
                                    }
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

@Composable
private fun CourseCard(course: CourseSummary, onOpen: () -> Unit) {
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
            TextButton(onClick = onOpen) {
                Text("Szczegóły i walidacja")
            }
        }
    }
}

@Composable
private fun CourseDetailsCard(
    details: CourseDetails,
    validation: CourseValidation?,
    onEditDraft: () -> Unit,
) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(6.dp),
        ) {
            Text(details.name, style = MaterialTheme.typography.titleMedium)
            if (details.description.isNotBlank()) {
                Text(details.description, style = MaterialTheme.typography.bodyMedium)
            }
            Text(
                "Sekcje: ${details.sections.size} · Aktywności: ${details.activityCount}",
                style = MaterialTheme.typography.bodySmall,
            )
            details.sections.take(8).forEach { section ->
                Text("• ${section.name} — ${section.activityCount} aktywności")
            }
            if (details.sections.size > 8) {
                Text("Pozostałe sekcje: ${details.sections.size - 8}")
            }
            validation?.let { report ->
                Text(
                    if (report.ok) "Walidacja: poprawna" else "Walidacja: wymaga poprawy",
                    color = if (report.ok) MaterialTheme.colorScheme.primary
                    else MaterialTheme.colorScheme.error,
                    style = MaterialTheme.typography.titleSmall,
                )
                Text("Błędy: ${report.errors.size} · Ostrzeżenia: ${report.warnings.size}")
                (report.errors + report.warnings).take(8).forEach { finding ->
                    Text(
                        "[${finding.severity}] ${finding.code}: ${finding.message}",
                        style = MaterialTheme.typography.bodySmall,
                    )
                }
                val remaining = report.errors.size + report.warnings.size - 8
                if (remaining > 0) Text("Pozostałe uwagi: $remaining")
            }
            Button(onClick = onEditDraft, modifier = Modifier.fillMaxWidth()) {
                Text("Utwórz / edytuj wersję roboczą")
            }
        }
    }
}

@Composable
private fun CourseDraftEditorCard(
    preview: DraftPreview,
    fullName: String,
    onFullNameChange: (String) -> Unit,
    shortName: String,
    onShortNameChange: (String) -> Unit,
    description: String,
    onDescriptionChange: (String) -> Unit,
    sectionNames: Map<String, String>,
    onSectionNameChange: (String, String) -> Unit,
    saving: Boolean,
    onSave: () -> Unit,
    onCancel: () -> Unit,
) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp),
        ) {
            Text(
                "Wersja robocza · rewizja ${preview.draft.revision}",
                style = MaterialTheme.typography.titleMedium,
            )
            OutlinedTextField(
                value = fullName,
                onValueChange = onFullNameChange,
                modifier = Modifier.fillMaxWidth(),
                label = { Text("Nazwa kursu") },
                singleLine = true,
            )
            OutlinedTextField(
                value = shortName,
                onValueChange = onShortNameChange,
                modifier = Modifier.fillMaxWidth(),
                label = { Text("Nazwa skrócona") },
                singleLine = true,
            )
            OutlinedTextField(
                value = description,
                onValueChange = onDescriptionChange,
                modifier = Modifier.fillMaxWidth(),
                label = { Text("Opis kursu") },
                minLines = 3,
            )
            Text("Nazwy sekcji", style = MaterialTheme.typography.titleSmall)
            preview.sections.forEach { section ->
                OutlinedTextField(
                    value = sectionNames[section.id] ?: section.name,
                    onValueChange = { onSectionNameChange(section.id, it) },
                    modifier = Modifier.fillMaxWidth(),
                    label = { Text(section.id) },
                    singleLine = true,
                )
            }
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Button(onClick = onSave, enabled = !saving) {
                    Text(if (saving) "Zapisywanie…" else "Zapisz wersję")
                }
                TextButton(onClick = onCancel, enabled = !saving) {
                    Text("Anuluj")
                }
            }
        }
    }
}

@Composable
private fun DraftPreviewCard(preview: DraftPreview) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(6.dp),
        ) {
            Text("Podgląd zapisanej wersji roboczej", style = MaterialTheme.typography.titleSmall)
            Text("Rewizja: ${preview.draft.revision}")
            Text(preview.fullName)
            Text(
                if (preview.validation.ok) "Walidacja: poprawna" else "Walidacja: wymaga poprawy",
                color = if (preview.validation.ok) MaterialTheme.colorScheme.primary
                else MaterialTheme.colorScheme.error,
            )
            Text(
                "Błędy: ${preview.validation.errors.size} · Ostrzeżenia: ${preview.validation.warnings.size}",
                style = MaterialTheme.typography.bodySmall,
            )
        }
    }
}
