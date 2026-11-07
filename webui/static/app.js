const $ = (id) => document.getElementById(id);
let courses = [];
let selected = null;
let apiToken = "";

async function request(url, options = {}) {
  const headers = {"Accept": "application/json", ...(options.headers || {})};
  if (apiToken) headers.Authorization = "Bearer " + apiToken;
  let body;
  if (options.payload !== undefined) {
    headers["Content-Type"] = "application/json";
    body = JSON.stringify(options.payload);
  }
  const response = await fetch(url, {
    method: options.method || "GET",
    headers,
    body,
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "Błąd żądania");
  return data;
}

function renderCourses() {
  const query = $("search").value.trim().toLocaleLowerCase("pl");
  const visible = courses.filter(c => (c.name + " " + c.short_name).toLocaleLowerCase("pl").includes(query));
  $("list-count").textContent = visible.length;
  $("courses").replaceChildren();
  if (!visible.length) {
    const empty = document.createElement("div");
    empty.className = "empty";
    empty.textContent = "Brak kursów pasujących do wyszukiwania.";
    $("courses").append(empty);
    return;
  }
  for (const course of visible) {
    const button = document.createElement("button");
    button.className = "course-item" + (selected === course.id ? " selected" : "");
    const name = document.createElement("strong");
    name.textContent = course.name;
    const meta = document.createElement("small");
    meta.textContent = [course.short_name, course.sections + " sekcji", course.activities + " aktywności"].filter(Boolean).join(" · ");
    button.append(name, meta);
    button.addEventListener("click", () => selectCourse(course.id));
    $("courses").append(button);
  }
}

function renderFindings(title, items, type) {
  if (!items.length) return null;
  const wrapper = document.createElement("div");
  const heading = document.createElement("h3");
  heading.className = "findings-title";
  heading.textContent = title + " (" + items.length + ")";
  wrapper.append(heading);
  for (const item of items) {
    const row = document.createElement("div");
    row.className = "finding " + type;
    const strong = document.createElement("strong");
    strong.textContent = item.code + " · " + item.path;
    const p = document.createElement("p");
    p.textContent = item.message;
    row.append(strong, p);
    wrapper.append(row);
  }
  return wrapper;
}

function field(labelText, value, name, multiline = false) {
  const wrapper = document.createElement("label");
  wrapper.className = "editor-field";
  const label = document.createElement("span");
  label.textContent = labelText;
  const input = document.createElement(multiline ? "textarea" : "input");
  input.name = name;
  input.value = value || "";
  if (!multiline) input.type = "text";
  else input.rows = 4;
  wrapper.append(label, input);
  return wrapper;
}

function renderDraftEditor(preview) {
  const draft = preview.draft;
  const course = preview.course;
  const editor = document.createElement("section");
  editor.className = "draft-editor";
  const header = document.createElement("div");
  header.className = "draft-heading";
  const title = document.createElement("h3");
  title.textContent = "Wersja robocza";
  const revision = document.createElement("span");
  revision.className = "tag";
  revision.textContent = "REWIZJA " + draft.revision;
  const historyButton = document.createElement("button");
  historyButton.className = "secondary-button";
  historyButton.textContent = "Historia";
  historyButton.addEventListener("click", () => loadDraftHistory(draft));
  header.append(title, revision, historyButton);
  editor.append(header);

  const form = document.createElement("form");
  form.className = "draft-form";
  form.append(
    field("Nazwa kursu", course.course.full_name, "full_name"),
    field("Nazwa skrócona", course.course.short_name, "short_name"),
    field("Opis", course.course.description, "description", true),
  );

  const sectionHeading = document.createElement("h4");
  sectionHeading.textContent = "Sekcje i aktywności";
  form.append(sectionHeading);
  for (const section of course.sections) {
    const group = document.createElement("fieldset");
    group.className = "editor-group";
    const legend = document.createElement("legend");
    legend.textContent = "Sekcja: " + section.id;
    group.append(legend, field("Nazwa sekcji", section.name, "section:" + section.id));
    for (const activity of section.activities) {
      group.append(field(
        "Aktywność · " + activity.type + " · " + activity.ref,
        activity.name,
        "activity:" + section.id + "|" + activity.ref,
      ));
    }
    form.append(group);
  }

  const actions = document.createElement("div");
  actions.className = "editor-actions";
  const save = document.createElement("button");
  save.type = "submit";
  save.className = "primary-button";
  save.textContent = "Zapisz wersję roboczą";
  const status = document.createElement("span");
  status.className = "editor-status";
  status.setAttribute("role", "status");
  actions.append(save, status);
  form.append(actions);

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    save.disabled = true;
    status.textContent = "Zapisywanie…";
    const changes = {};
    const sectionNames = {};
    const activityNames = {};
    for (const [key, value] of new FormData(form).entries()) {
      if (key === "full_name" || key === "short_name" || key === "description") {
        changes[key] = value;
      } else if (key.startsWith("section:")) {
        sectionNames[key.slice("section:".length)] = value;
      } else if (key.startsWith("activity:")) {
        activityNames[key.slice("activity:".length)] = value;
      }
    }
    if (Object.keys(sectionNames).length) changes.section_names = sectionNames;
    if (Object.keys(activityNames).length) changes.activity_names = activityNames;
    try {
      await request("/api/drafts/" + encodeURIComponent(draft.draft_id), {
        method: "PATCH",
        payload: {expected_revision: draft.revision, changes},
      });
      const updated = await request("/api/drafts/" + encodeURIComponent(draft.draft_id) + "/preview");
      $("detail").replaceChildren();
      renderDraftEditor(updated.data);
    } catch (error) {
      status.textContent = error.message;
      save.disabled = false;
    }
  });

  editor.append(form);
  const validation = document.createElement("div");
  validation.className = "draft-validation";
  const state = document.createElement("div");
  state.className = "status-line " + (preview.validation.ok ? "ok" : "bad");
  state.textContent = preview.validation.ok
    ? "✓ Podgląd wersji roboczej przeszedł walidację."
    : "! Podgląd wersji roboczej zawiera błędy.";
  validation.append(state);
  const errors = renderFindings("Błędy podglądu", preview.validation.errors, "error");
  const warnings = renderFindings("Ostrzeżenia podglądu", preview.validation.warnings, "warning");
  if (errors) validation.append(errors);
  if (warnings) validation.append(warnings);
  editor.append(validation);
  $("detail").append(editor);
}

async function loadDrafts(courseId) {
  try {
    const result = await request("/api/courses/" + encodeURIComponent(courseId) + "/drafts");
    const panel = document.createElement("section");
    panel.className = "draft-history";
    const heading = document.createElement("h3");
    heading.textContent = "Zapisane wersje robocze";
    panel.append(heading);
    if (!result.data.length) {
      const empty = document.createElement("p");
      empty.className = "empty";
      empty.textContent = "Ten kurs nie ma jeszcze zapisanych wersji roboczych.";
      panel.append(empty);
    }
    for (const draft of result.data) {
      const row = document.createElement("div");
      row.className = "history-row";
      const details = document.createElement("div");
      const label = document.createElement("strong");
      label.textContent = "Rewizja " + draft.revision;
      const date = document.createElement("small");
      date.textContent = new Date(draft.updated_at).toLocaleString("pl-PL");
      details.append(label, date);
      const actions = document.createElement("div");
      actions.className = "history-actions";
      const open = document.createElement("button");
      open.className = "secondary-button";
      open.textContent = "Otwórz";
      open.addEventListener("click", async () => {
        try {
          const preview = await request("/api/drafts/" + encodeURIComponent(draft.draft_id) + "/preview");
          $("detail").replaceChildren();
          renderDraftEditor(preview.data);
        } catch (error) {
          showDraftError(error.message);
        }
      });
      const history = document.createElement("button");
      history.className = "secondary-button";
      history.textContent = "Historia";
      history.addEventListener("click", () => loadDraftHistory(draft));
      actions.append(open, history);
      row.append(details, actions);
      panel.append(row);
    }
    $("detail").replaceChildren(panel);
  } catch (error) {
    showDraftError(error.message);
  }
}

async function loadDraftHistory(draft) {
  try {
    const result = await request("/api/drafts/" + encodeURIComponent(draft.draft_id) + "/history");
    const panel = document.createElement("section");
    panel.className = "draft-history";
    const heading = document.createElement("h3");
    heading.textContent = "Historia wersji roboczej";
    panel.append(heading);
    const back = document.createElement("button");
    back.className = "secondary-button";
    back.textContent = "Otwórz bieżącą rewizję";
    back.addEventListener("click", async () => {
      const preview = await request("/api/drafts/" + encodeURIComponent(draft.draft_id) + "/preview");
      $("detail").replaceChildren();
      renderDraftEditor(preview.data);
    });
    panel.append(back);
    for (const revision of result.data) {
      const row = document.createElement("div");
      row.className = "history-row";
      const details = document.createElement("div");
      const label = document.createElement("strong");
      label.textContent = "Rewizja " + revision.revision;
      const changes = document.createElement("small");
      changes.textContent = Object.keys(revision.changes || {}).join(", ") || "Wersja początkowa";
      details.append(label, changes);
      const actions = document.createElement("div");
      actions.className = "history-actions";
      if (revision.revision !== draft.revision) {
        const restore = document.createElement("button");
        restore.className = "secondary-button";
        restore.textContent = "Przywróć";
        restore.addEventListener("click", async () => {
          restore.disabled = true;
          try {
            await request("/api/drafts/" + encodeURIComponent(draft.draft_id) + "/restore", {
              method: "POST",
              payload: {expected_revision: draft.revision, target_revision: revision.revision},
            });
            const preview = await request("/api/drafts/" + encodeURIComponent(draft.draft_id) + "/preview");
            $("detail").replaceChildren();
            renderDraftEditor(preview.data);
          } catch (error) {
            restore.disabled = false;
            showDraftError(error.message);
          }
        });
        actions.append(restore);
      }
      row.append(details, actions);
      panel.append(row);
    }
    $("detail").replaceChildren(panel);
  } catch (error) {
    showDraftError(error.message);
  }
}

function showDraftError(message) {
  const error = document.createElement("div");
  error.className = "status-line bad";
  error.textContent = message;
  $("detail").append(error);
}

async function createDraft(courseId, button) {
  button.disabled = true;
  button.textContent = "Tworzenie…";
  try {
    const created = await request("/api/courses/" + encodeURIComponent(courseId) + "/drafts", {
      method: "POST",
      payload: {},
    });
    const preview = await request("/api/drafts/" + encodeURIComponent(created.data.draft_id) + "/preview");
    renderDraftEditor(preview.data);
  } catch (error) {
    const message = document.createElement("div");
    message.className = "status-line bad";
    message.textContent = "Nie udało się utworzyć wersji roboczej: " + error.message;
    $("detail").append(message);
    button.disabled = false;
    button.textContent = "Utwórz wersję roboczą";
  }
}

async function selectCourse(id) {
  selected = id;
  renderCourses();
  $("detail").textContent = "Trwa walidacja projektu…";
  try {
    const result = await request("/api/courses/" + encodeURIComponent(id) + "/validate");
    const course = result.course;
    const box = document.createElement("div");
    const title = document.createElement("h2");
    title.textContent = course.name;
    const subtitle = document.createElement("p");
    subtitle.className = "sub";
    subtitle.textContent = course.short_name;
    box.append(title, subtitle);
    const summary = document.createElement("div");
    summary.className = "course-summary";
    for (const [label, value] of [["Sekcje", course.sections], ["Aktywności", course.activities], ["Typy aktywności", Object.keys(course.activity_types).length]]) {
      const cell = document.createElement("div"); cell.className = "summary-cell";
      const small = document.createElement("small"); small.textContent = label;
      const strong = document.createElement("strong"); strong.textContent = value;
      cell.append(small, strong); summary.append(cell);
    }
    box.append(summary);
    const status = document.createElement("div");
    status.className = "status-line " + (result.ok ? "ok" : "bad");
    status.textContent = result.ok ? "✓ Walidacja zakończona — brak błędów." : "! Walidacja wykryła błędy wymagające poprawy.";
    box.append(status);
    const types = document.createElement("p"); types.className = "sub";
    types.textContent = "Rodzaje aktywności: " + Object.entries(course.activity_types).map(([k,v]) => k + ": " + v).join(" · ");
    box.append(types);
    const errors = renderFindings("Błędy", result.errors, "error");
    const warnings = renderFindings("Ostrzeżenia", result.warnings, "warning");
    if (errors) box.append(errors);
    if (warnings) box.append(warnings);
    if (!result.errors.length && !result.warnings.length) {
      const clean = document.createElement("p"); clean.className = "empty"; clean.textContent = "Nie wykryto problemów.";
      box.append(clean);
    }
    const editButton = document.createElement("button");
    editButton.className = "primary-button";
    editButton.textContent = "Utwórz wersję roboczą";
    editButton.addEventListener("click", () => createDraft(id, editButton));
    box.append(editButton);
    const draftsButton = document.createElement("button");
    draftsButton.className = "secondary-button";
    draftsButton.textContent = "Zapisane wersje robocze";
    draftsButton.addEventListener("click", () => loadDrafts(id));
    box.append(draftsButton);
    $("detail").replaceChildren(box);
  } catch (error) {
    $("detail").textContent = "Nie udało się zweryfikować kursu: " + error.message;
  }
}

async function init() {
  $("apply-token").addEventListener("click", () => {
    apiToken = $("api-token").value.trim();
    $("token-status").textContent = apiToken ? "Token ustawiony w pamięci tej karty." : "Brak tokenu.";
    if (selected) selectCourse(selected);
  });
  try {
    await request("/api/health");
    const result = await request("/api/courses");
    $("api-status").textContent = "Połączono";
    courses = result.courses;
    $("course-count").textContent = courses.length;
    $("section-count").textContent = courses.reduce((n,c) => n + (Number(c.sections) || 0), 0);
    $("activity-count").textContent = courses.reduce((n,c) => n + (Number(c.activities) || 0), 0);
    $("search").addEventListener("input", renderCourses);
    renderCourses();
    if (courses.length) selectCourse(courses[0].id);
    else {
      const empty = document.createElement("div");
      empty.className = "empty";
      empty.textContent = "Nie znaleziono projektów. Umieść kurs w katalogu courses/.";
      $("courses").replaceChildren(empty);
    }
  } catch (error) {
    $("api-status").textContent = "Brak połączenia";
    $("courses").textContent = error.message;
  }
}
init();
