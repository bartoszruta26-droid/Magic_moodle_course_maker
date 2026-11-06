const $ = (id) => document.getElementById(id);
let courses = [];
let selected = null;

async function request(url) {
  const response = await fetch(url, {headers: {"Accept": "application/json"}});
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "Błąd żądania");
  return data;
}

function renderCourses() {
  const query = $("search").value.trim().toLocaleLowerCase("pl");
  const visible = courses.filter(c => (c.name + " " + c.short_name).toLocaleLowerCase("pl").includes(query));
  $("list-count").textContent = visible.length;
  $("courses").innerHTML = "";
  if (!visible.length) {
    $("courses").innerHTML = '<div class="empty">Brak kursów pasujących do wyszukiwania.</div>';
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
  if (!items.length) return "";
  const heading = document.createElement("h3");
  heading.className = "findings-title";
  heading.textContent = title + " (" + items.length + ")";
  const wrapper = document.createElement("div");
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

async function selectCourse(id) {
  selected = id;
  renderCourses();
  $("detail").innerHTML = '<div class="empty">Trwa walidacja projektu…</div>';
  try {
    const result = await request("/api/courses/" + encodeURIComponent(id) + "/validate");
    const course = result.course;
    const box = document.createElement("div");
    const title = document.createElement("h2");
    title.textContent = course.name;
    title.style.fontFamily = "Manrope";
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
    box.append(renderFindings("Błędy", result.errors, "error"));
    box.append(renderFindings("Ostrzeżenia", result.warnings, "warning"));
    if (!result.errors.length && !result.warnings.length) {
      const clean = document.createElement("p"); clean.className = "empty"; clean.textContent = "Nie wykryto problemów.";
      box.append(clean);
    }
    $("detail").replaceChildren(box);
  } catch (error) {
    $("detail").textContent = "Nie udało się zweryfikować kursu: " + error.message;
  }
}

async function init() {
  try {
    const [health, result] = await Promise.all([request("/api/health"), request("/api/courses")]);
    $("api-status").textContent = "Połączono";
    courses = result.courses;
    $("course-count").textContent = courses.length;
    $("section-count").textContent = courses.reduce((n,c) => n + (Number(c.sections) || 0), 0);
    $("activity-count").textContent = courses.reduce((n,c) => n + (Number(c.activities) || 0), 0);
    $("search").addEventListener("input", renderCourses);
    renderCourses();
    if (courses.length) selectCourse(courses[0].id);
    else $("courses").innerHTML = '<div class="empty">Nie znaleziono projektów. Umieść kurs w katalogu courses/.</div>';
  } catch (error) {
    $("api-status").textContent = "Brak połączenia";
    $("courses").textContent = error.message;
  }
}
init();
