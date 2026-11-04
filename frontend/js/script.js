"use strict";

/* API ENDPOINTS */

const API_BASE = "http://localhost:8080";

const TOPICS_API = `${API_BASE}/api/topics`;
const ANALYZE_API = `${API_BASE}/api/analyze`;
const PAPERS_API = `${API_BASE}/api/papers`;
const HEALTH_API = `${API_BASE}/health`;

/* DOM ELEMENTS */

const topicsContainer = document.getElementById("topics");
const topicCount = document.getElementById("topic-count");
const message = document.getElementById("message");
const searchInput = document.getElementById("search");

const connectionStatus = document.getElementById("connection-status");
const connectionMessage = document.getElementById("connection-message");

const analyzeForm = document.getElementById("analyze-form");
const questionInput = document.getElementById("question-input");
const analyzeButton = document.getElementById("analyze-button");
const analyzeStatus = document.getElementById("analyze-status");
const analysisResults = document.getElementById("analysis-results");
const questionCharCount = document.getElementById("question-char-count");

const uploadForm = document.getElementById("paper-upload-form");
const paperNameInput = document.getElementById("paper-name");
const paperSubjectInput = document.getElementById("paper-subject");
const paperFileInput = document.getElementById("paper-file");
const selectedFile = document.getElementById("selected-file");
const uploadButton = document.getElementById("upload-button");
const uploadStatus = document.getElementById("upload-status");

const paperResults = document.getElementById("paper-results");
const paperSummary = document.getElementById("paper-summary");
const paperQuestionResults = document.getElementById(
    "paper-question-results"
);
const paperErrors = document.getElementById("paper-errors");

let allTopics = [];

/* GENERAL HELPERS */

function setStatus(element, text, type = "") {
    element.textContent = text;
    element.classList.remove("success", "error");

    if (type) {
        element.classList.add(type);
    }
}

async function fetchJson(url, options = {}) {
    const response = await fetch(url, options);

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
        throw new Error(
            data.error || `Request failed with HTTP ${response.status}`
        );
    }

    return data;
}

function setText(id, value, fallback = "Not available") {
    const element = document.getElementById(id);

    if (!element) {
        return;
    }

    element.textContent =
        value === null || value === undefined || value === ""
            ? fallback
            : String(value);
}

function showEmptyState(container, text) {
    container.replaceChildren();

    const element = document.createElement("p");
    element.className = "empty-state";
    element.textContent = text;

    container.appendChild(element);
}

/* BACKEND HEALTH */

async function checkBackend() {
    try {
        await fetchJson(HEALTH_API);

        connectionStatus.textContent = "Connected";
        connectionMessage.textContent = "Java backend responding";
        connectionStatus.style.color = "#168c65";
    } catch (error) {
        console.error("Backend health check failed:", error);

        connectionStatus.textContent = "Offline";
        connectionMessage.textContent = "Check Java backend";
        connectionStatus.style.color = "#c34444";
    }
}

/* TOPICS */

async function loadTopics() {
    setStatus(message, "Loading topics from MySQL...");

    try {
        const data = await fetchJson(TOPICS_API);

        if (!Array.isArray(data.topics)) {
            throw new Error("The topics API returned an invalid response.");
        }

        allTopics = data.topics;

        topicCount.textContent = String(allTopics.length);

        renderTopics(allTopics);

        setStatus(
            message,
            `Loaded ${allTopics.length} topic(s) from the database.`,
            "success"
        );
    } catch (error) {
        console.error("Unable to load topics:", error);

        topicCount.textContent = "--";

        showEmptyState(
            topicsContainer,
            "Topics could not be loaded. Check the Java backend and database."
        );

        setStatus(message, error.message, "error");
    }
}

function renderTopics(topics) {
    topicsContainer.replaceChildren();

    if (!topics.length) {
        showEmptyState(topicsContainer, "No matching topics found.");
        return;
    }

    const fragment = document.createDocumentFragment();

    topics.forEach((topic) => {
        const card = document.createElement("article");
        card.className = "topic-card";

        const number = document.createElement("span");
        number.className = "topic-number";
        number.textContent = `TOPIC ${topic.id}`;

        const title = document.createElement("h3");
        title.textContent = topic.topic_name || "Untitled topic";

        card.append(number, title);
        fragment.appendChild(card);
    });

    topicsContainer.appendChild(fragment);
}

searchInput.addEventListener("input", () => {
    const query = searchInput.value.trim().toLowerCase();

    const filteredTopics = allTopics.filter((topic) =>
        String(topic.topic_name || "").toLowerCase().includes(query)
    );

    renderTopics(filteredTopics);

    setStatus(
        message,
        `${filteredTopics.length} matching topic(s).`
    );
});

/* QUESTION CHARACTER COUNTER */

function updateQuestionCount() {
    questionCharCount.textContent =
        `${questionInput.value.length} / 5000 characters`;
}

questionInput.addEventListener("input", updateQuestionCount);

/* MANUAL QUESTION ANALYSIS */

function displayAnalysis(data) {
    setText("result-concept", data.main_concept);
    setText("result-difficulty", data.difficulty);
    setText("result-difficulty-reason", data.difficulty_reason);
    setText("result-bloom", data.bloom);
    setText("result-marks", data.suggested_marks);

    const score = Number(data.score);
    const maxScore = Number(data.score_out_of);

    let scoreText = "Not available";

    if (data.score !== null && data.score !== undefined &&
        Number.isFinite(score)) {
        scoreText = `${score.toFixed(1)} / ${
            Number.isFinite(maxScore) ? maxScore : 10
        }`;
    }

    setText("result-score", scoreText);

    const supporting = data.supporting_concepts;

    setText(
        "result-supporting",
        Array.isArray(supporting)
            ? supporting.join(", ")
            : supporting
    );

    const detectedList = document.getElementById("result-detected");
    detectedList.replaceChildren();

    if (
        Array.isArray(data.detected_concepts) &&
        data.detected_concepts.length
    ) {
        data.detected_concepts.forEach((item) => {
            const li = document.createElement("li");

            const concept = item.concept || "Unknown concept";
            const weight = Number(item.weight);

            li.textContent =
                `${concept}${
                    item.weight !== null &&
                    item.weight !== undefined &&
                    Number.isFinite(weight)
                        ? ` (weight: ${weight.toFixed(2)})`
                        : ""
                }`;

            detectedList.appendChild(li);
        });
    } else {
        const li = document.createElement("li");
        li.textContent = "No detected concepts returned.";
        detectedList.appendChild(li);
    }

    setText("result-explanation", data.analysis_explanation);

    analysisResults.hidden = false;

    analysisResults.scrollIntoView({
        behavior: "smooth",
        block: "start"
    });
}

analyzeForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const question = questionInput.value.trim();

    if (!question) {
        setStatus(analyzeStatus, "Enter a question first.", "error");
        questionInput.focus();
        return;
    }

    analyzeButton.disabled = true;
    analyzeButton.textContent = "Analyzing...";
    analysisResults.hidden = true;

    setStatus(analyzeStatus, "Sending your question to the ML service...");

    try {
        const data = await fetchJson(ANALYZE_API, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ question })
        });

        displayAnalysis(data);

        setStatus(
            analyzeStatus,
            "Question analysis completed successfully.",
            "success"
        );
    } catch (error) {
        console.error("Question analysis failed:", error);

        setStatus(
            analyzeStatus,
            `Analysis failed: ${error.message}. Check that Java and Python are running.`,
            "error"
        );
    } finally {
        analyzeButton.disabled = false;
        analyzeButton.innerHTML =
            '<span>Analyze Question</span><span aria-hidden="true">&rarr;</span>';
    }
});

/* PAPER FILE SELECTION */

paperFileInput.addEventListener("change", () => {
    const file = paperFileInput.files[0];

    selectedFile.textContent = file
        ? `${file.name} (${(file.size / 1024).toFixed(1)} KB)`
        : "No file selected.";
});

/* PAPER ERROR DISPLAY */

function displayPaperErrors(errors) {
    paperErrors.replaceChildren();

    if (!Array.isArray(errors) || !errors.length) {
        paperErrors.hidden = true;
        return;
    }

    const heading = document.createElement("strong");
    heading.textContent = "Some questions could not be analyzed:";
    paperErrors.appendChild(heading);

    errors.forEach((error) => {
        const p = document.createElement("p");

        if (typeof error === "string") {
            p.textContent = error;
        } else {
            p.textContent = JSON.stringify(error);
        }

        paperErrors.appendChild(p);
    });

    paperErrors.hidden = false;
}

/* PAPER ANALYSIS RESULTS */

function displayPaperResults(paper, analysis) {
    paperQuestionResults.replaceChildren();

    const results = Array.isArray(analysis.results)
        ? analysis.results
        : [];

    if (!results.length) {
        showEmptyState(
            paperQuestionResults,
            "No successful question analyses were returned."
        );
    } else {
        results.forEach((result) => {
            const item = document.createElement("li");

            const details = [
                `Question ID: ${result.question_id ?? "N/A"}`,
                `Concept: ${result.main_concept || "N/A"}`,
                `Difficulty: ${result.difficulty || "N/A"}`,
                `Bloom's level: ${result.bloom_level || "N/A"}`,
                `Suggested marks: ${result.suggested_marks || "N/A"}`,
                `Analysis score: ${
                    result.score === null || result.score === undefined
                        ? "N/A"
                        : result.score
                }`
            ];

            item.textContent = details.join(" | ");
            paperQuestionResults.appendChild(item);
        });
    }

    paperSummary.textContent =
        `Paper ID: ${paper.id} | ` +
        `Questions processed: ${analysis.total_questions ?? results.length} | ` +
        `Saved analyses: ${analysis.saved_analyses ?? results.length}`;

    displayPaperErrors(analysis.errors);

    paperResults.hidden = false;

    paperResults.scrollIntoView({
        behavior: "smooth",
        block: "start"
    });
}

async function extractPdfText(file) {
    if (!window.pdfjsLib) {
        throw new Error("PDF.js could not load. Check your internet connection.");
    }

    pdfjsLib.GlobalWorkerOptions.workerSrc =
        "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js";

    const pdf = await pdfjsLib.getDocument({
        data: await file.arrayBuffer()
    }).promise;

    const pages = [];

    for (let pageNumber = 1; pageNumber <= pdf.numPages; pageNumber++) {
        setStatus(
            uploadStatus,
            `Reading PDF page ${pageNumber} of ${pdf.numPages}...`
        );

        const page = await pdf.getPage(pageNumber);
        const content = await page.getTextContent();

        const lines = [];
        let currentLine = "";
        let previousY = null;

        for (const item of content.items) {
            if (!item.str || !item.str.trim()) continue;

            const y = item.transform[5];

            if (previousY !== null && Math.abs(y - previousY) > 3) {
                if (currentLine.trim()) lines.push(currentLine.trim());
                currentLine = "";
            }

            currentLine += (currentLine ? " " : "") + item.str.trim();
            previousY = y;

            if (item.hasEOL) {
                if (currentLine.trim()) lines.push(currentLine.trim());
                currentLine = "";
                previousY = null;
            }
        }

        if (currentLine.trim()) lines.push(currentLine.trim());

        pages.push(lines.join("\n"));
    }

    return pages.join("\n\n");
}
async function extractImageText(file) {
    if (!window.Tesseract) {
        throw new Error("Tesseract.js could not load. Check your internet connection.");
    }

    setStatus(uploadStatus, "Reading image text with OCR...");

    const result = await Tesseract.recognize(file, "eng", {
        logger: info => {
            if (info.status === "recognizing text" && info.progress) {
                setStatus(
                    uploadStatus,
                    `Recognizing image text: ${Math.round(info.progress * 100)}%`
                );
            }
        }
    });

    return result.data.text;
}

async function extractQuestionPaperText(file) {
    const extension = file.name.split(".").pop().toLowerCase();

    if (extension === "txt") {
        setStatus(uploadStatus, "Reading the text file...");
        return await file.text();
    }

    if (extension === "pdf") {
        return await extractPdfText(file);
    }

    if (["jpg", "jpeg", "png"].includes(extension)) {
        return await extractImageText(file);
    }

    throw new Error("Unsupported file format. Select TXT, PDF, JPG or PNG.");
}

function getPaperMimeType(file) {
    const extension = file.name.split(".").pop().toLowerCase();

    const mimeTypes = {
        txt: "text/plain",
        pdf: "application/pdf",
        jpg: "image/jpeg",
        jpeg: "image/jpeg",
        png: "image/png"
    };

    return mimeTypes[extension];
}
/* UPLOAD, EXTRACT, ANALYZE */

uploadForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const paperName = paperNameInput.value.trim();
    const subject = paperSubjectInput.value.trim();
    const file = paperFileInput.files[0];

    if (!paperName || !subject || !file) {
        setStatus(uploadStatus, "Enter the paper name and subject, then select a file.", "error");
        return;
    }

    const extension = file.name.split(".").pop().toLowerCase();
    const allowedExtensions = ["txt", "pdf", "jpg", "jpeg", "png"];

    if (!allowedExtensions.includes(extension)) {
        setStatus(uploadStatus, "Select a TXT, PDF, JPG or PNG file.", "error");
        return;
    }

    if (file.size === 0 || file.size > 5 * 1024 * 1024) {
        setStatus(uploadStatus, "Select a non-empty file no larger than 5 MB.", "error");
        return;
    }

    uploadButton.disabled = true;
    uploadButton.textContent = "Processing...";
    paperResults.hidden = true;

    try {
        setStatus(uploadStatus, "Extracting text from the paper...");

        const extractedText = await extractQuestionPaperText(file);

        if (!extractedText || !extractedText.trim()) {
            throw new Error("No readable text found in the selected file.");
        }

        setStatus(uploadStatus, "Saving paper details to MySQL...");

        const paper = await fetchJson(PAPERS_API, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                paper_name: paperName,
                subject,
                original_filename: file.name,
                mime_type: getPaperMimeType(file),
                stored_file_path: null,
                extracted_text: extractedText
            })
        });

        if (paper.id === null || paper.id === undefined) {
            throw new Error("The backend did not return a paper ID.");
        }

        setStatus(uploadStatus, "Extracting individual questions...");

        await fetchJson(
            `${PAPERS_API}/${encodeURIComponent(paper.id)}/extract`,
            { method: "POST" }
        );

        setStatus(uploadStatus, "Analyzing supported questions...");

        const analysis = await fetchJson(
            `${PAPERS_API}/${encodeURIComponent(paper.id)}/analyze`,
            { method: "POST" }
        );

        currentPaperMetadata = paper;
        displayPaperResults(paper, analysis);

        setStatus(uploadStatus, "Loading individual question details...");
        await loadIndividualQuestions(paper.id);

        const analyzedCount = analysis.analyzed_count ?? 0;
        const skippedCount = analysis.skipped_count ?? 0;

        if (analysis.errors?.length) {
            setStatus(
                uploadStatus,
                `Completed with errors. Analyzed: ${analyzedCount}, Skipped: ${skippedCount}.`,
                "error"
            );
        } else {
            setStatus(
                uploadStatus,
                `Completed! Analyzed: ${analyzedCount}, Skipped: ${skippedCount}.`,
                "success"
            );
        }

        await loadTopics();

    } catch (error) {
        console.error("Paper processing failed:", error);
        setStatus(uploadStatus, `Processing failed: ${error.message}`, "error");

    } finally {
        uploadButton.disabled = false;
        uploadButton.innerHTML =
            'Upload &amp; Analyze <span aria-hidden="true">&rarr;</span>';
    }
});

/* INDIVIDUAL QUESTIONS, QUESTION MAP AND BUILDER */

const individualQuestionList = document.getElementById("individual-question-list");
const questionMapContent = document.getElementById("question-map-content");
const questionBuilderList = document.getElementById("question-builder-list");
const builderQuestionCount = document.getElementById("builder-question-count");
const builderTotalMarks = document.getElementById("builder-total-marks");
const clearBuilderButton = document.getElementById("clear-builder-button");
const downloadBuilderButton = document.getElementById("download-builder-button");

let currentPaperQuestions = [];
let allPaperQuestions = [];
let selectedBuilderQuestions = [];
let currentPaperMetadata = null;

function getAnalysisValue(analysis, keys) {
    for (const key of keys) {
        const value = analysis?.[key];
        if (value !== null && value !== undefined && String(value).trim()) return String(value).trim();
    }
    return "";
}

function normalizeDifficulty(value) {
    const normalized = String(value || "").trim().toLowerCase();
    if (normalized.includes("easy") || normalized.includes("low")) return "Easy";
    if (normalized.includes("medium") || normalized.includes("moderate")) return "Medium";
    if (normalized.includes("hard") || normalized.includes("difficult") || normalized.includes("high")) return "Hard";
    return "Unclassified";
}

function analyticsSubjectFor(item, paperSubject, analyzed) {
    const explicit = getAnalysisValue(item, ["subject", "detected_subject", "subject_name"]) ||
        getAnalysisValue(item.analysis, ["subject", "detected_subject", "subject_name"]);
    if (explicit) return explicit;
    // The current analyzer supports Java. A successfully analyzed question therefore belongs to Java.
    if (analyzed) return "Java";
    // A single subject entered in the upload form is paper metadata, not a mixed-paper classifier.
    const raw = String(paperSubject || "").trim();
    if (raw && !/(,|\/|&|\band\b)/i.test(raw)) return raw;
    return "Unclassified / skipped";
}

let paperAnalyticsState = { paper: null, questions: [], selectedSubject: "All subjects", subjects: [] };
const paperCharts = {};

function destroyPaperCharts() {
    Object.values(paperCharts).forEach((chart) => chart?.destroy());
    Object.keys(paperCharts).forEach((key) => delete paperCharts[key]);
}

function getFilteredAnalyticsQuestions() {
    const { questions, selectedSubject, paper } = paperAnalyticsState;
    return questions.filter((item) => analyticsSubjectFor(item, paper?.subject, Boolean(item.analysis)) === selectedSubject || selectedSubject === "All subjects");
}

function chartDefaults() {
    return {
        responsive: true,
        maintainAspectRatio: false,
        animation: { duration: 850, easing: "easeOutQuart" },
        plugins: {
            legend: { display: false },
            tooltip: { backgroundColor: "#111a31", titleColor: "#fff", bodyColor: "#e7ecff", padding: 12, cornerRadius: 10, displayColors: true }
        }
    };
}

function makeChart(id, config) {
    const canvas = document.getElementById(id);
    if (!canvas || !window.Chart) return null;
    paperCharts[id] = new Chart(canvas, config);
    return paperCharts[id];
}

function renderSubjectFilters() {
    const host = document.getElementById("analytics-subject-filters");
    if (!host) return;
    host.replaceChildren();
    const labels = ["All subjects", ...paperAnalyticsState.subjects];
    labels.forEach((label) => {
        const button = createTextElement("button", `subject-filter ${paperAnalyticsState.selectedSubject === label ? "active" : ""}`, label);
        button.type = "button";
        button.setAttribute("aria-pressed", String(paperAnalyticsState.selectedSubject === label));
        button.addEventListener("click", () => {
            paperAnalyticsState.selectedSubject = label;
            renderSubjectFilters();
            renderFilteredCharts();
        });
        host.appendChild(button);
    });
}

function countBy(items, getter, fallback = "Not classified") {
    const counts = new Map();
    items.forEach((item) => {
        const key = getter(item) || fallback;
        counts.set(key, (counts.get(key) || 0) + 1);
    });
    return counts;
}

function renderDifficultyChart(items) {
    const analyzed = items.filter((item) => item.analysis);
    const counts = { Easy: 0, Medium: 0, Hard: 0 };
    analyzed.forEach((item) => {
        const level = normalizeDifficulty(getAnalysisValue(item.analysis, ["difficulty", "difficulty_level"]));
        if (counts[level] !== undefined) counts[level]++;
    });
    const total = counts.Easy + counts.Medium + counts.Hard;
    setText("difficulty-chart-caption", total ? `${total} analyzed questions in this view` : "No analyzed questions in this subject yet.");
    const colors = ["#28b889", "#f2ad4b", "#f16f86"];
    makeChart("difficulty-chart", {
        type: "doughnut",
        data: { labels: ["Easy", "Medium", "Hard"], datasets: [{ data: [counts.Easy, counts.Medium, counts.Hard], backgroundColor: colors, borderColor: "#fff", borderWidth: 5, hoverOffset: 12, borderRadius: 7 }] },
        options: { ...chartDefaults(), cutout: "72%", plugins: { ...chartDefaults().plugins, tooltip: { ...chartDefaults().plugins.tooltip, callbacks: { label: (ctx) => `${ctx.label}: ${ctx.raw} questions` } } } }
    });
    const legend = document.getElementById("difficulty-legend");
    legend.replaceChildren();
    ["Easy", "Medium", "Hard"].forEach((label, i) => {
        const item = createTextElement("div", "legend-item", "");
        const dot = createTextElement("i", "legend-dot", ""); dot.style.background = colors[i];
        const name = createTextElement("span", "", label);
        const value = createTextElement("strong", "", `${counts[label]} · ${total ? Math.round(counts[label] / total * 100) : 0}%`);
        item.append(dot, name, value); legend.appendChild(item);
    });
}

function renderFilteredCharts() {
    destroyPaperCharts();
    const all = paperAnalyticsState.questions;
    const selected = getFilteredAnalyticsQuestions();
    const analyzed = selected.filter((item) => item.analysis);
    const subjects = paperAnalyticsState.subjects;

    // Overall subject composition remains visible while the other charts drill into the selected subject.
    const subjectCounts = countBy(all, (item) => analyticsSubjectFor(item, paperAnalyticsState.paper?.subject, Boolean(item.analysis)));
    const subjectLabels = [...subjectCounts.keys()];
    const subjectValues = subjectLabels.map((label) => subjectCounts.get(label));
    makeChart("subject-chart", {
        type: "bar",
        data: { labels: subjectLabels, datasets: [{ label: "Questions", data: subjectValues, backgroundColor: subjectLabels.map((label) => label === paperAnalyticsState.selectedSubject ? "#6257e8" : "#a9a4f6"), borderRadius: 8, borderSkipped: false, maxBarThickness: 34 }] },
        options: { ...chartDefaults(), indexAxis: "y", scales: { x: { beginAtZero: true, grid: { color: "#edf0f7" }, ticks: { precision: 0 } }, y: { grid: { display: false } } }, onClick: (_event, elements) => { if (elements.length) { const label = subjectLabels[elements[0].index]; paperAnalyticsState.selectedSubject = label; renderSubjectFilters(); renderFilteredCharts(); } } }
    });

    renderDifficultyChart(selected);

    const diff = { Easy: [], Medium: [], Hard: [] };
    subjects.forEach((subject) => {
        const subset = all.filter((item) => analyticsSubjectFor(item, paperAnalyticsState.paper?.subject, Boolean(item.analysis)) === subject && item.analysis);
        const counts = { Easy: 0, Medium: 0, Hard: 0 };
        subset.forEach((item) => { const level = normalizeDifficulty(getAnalysisValue(item.analysis, ["difficulty", "difficulty_level"])); if (counts[level] !== undefined) counts[level]++; });
        Object.keys(diff).forEach((level) => diff[level].push(counts[level]));
    });
    makeChart("subject-difficulty-chart", {
        type: "bar", data: { labels: subjects, datasets: [
            { label: "Easy", data: diff.Easy, backgroundColor: "#28b889", borderRadius: 5, stack: "difficulty" },
            { label: "Medium", data: diff.Medium, backgroundColor: "#f2ad4b", borderRadius: 5, stack: "difficulty" },
            { label: "Hard", data: diff.Hard, backgroundColor: "#f16f86", borderRadius: 5, stack: "difficulty" }
        ] }, options: { ...chartDefaults(), scales: { x: { stacked: true, grid: { display: false } }, y: { stacked: true, beginAtZero: true, ticks: { precision: 0 }, grid: { color: "#edf0f7" } } }, plugins: { ...chartDefaults().plugins, legend: { display: true, position: "bottom", labels: { usePointStyle: true, boxWidth: 8, padding: 16 } } } }
    });

    const bloomCounts = countBy(analyzed, (item) => getAnalysisValue(item.analysis, ["bloom_level", "bloom", "blooms_level"]));
    makeChart("bloom-chart", {
        type: "bar", data: { labels: [...bloomCounts.keys()], datasets: [{ label: "Questions", data: [...bloomCounts.values()], backgroundColor: ["#8174ed", "#9b8cf0", "#6e83e9", "#58a3dc", "#4eb8ba", "#54b78a"], borderRadius: 7, borderSkipped: false }] },
        options: { ...chartDefaults(), indexAxis: "y", scales: { x: { beginAtZero: true, ticks: { precision: 0 }, grid: { color: "#edf0f7" } }, y: { grid: { display: false } } } }
    });

    const marksCounts = countBy(analyzed, (item) => getAnalysisValue(item.analysis, ["suggested_marks", "marks"]));
    makeChart("marks-chart", {
        type: "bar", data: { labels: [...marksCounts.keys()].map((label) => `${label} marks`), datasets: [{ label: "Questions", data: [...marksCounts.values()], backgroundColor: "#36a6a1", borderRadius: 7, borderSkipped: false }] },
        options: { ...chartDefaults(), scales: { x: { grid: { display: false } }, y: { beginAtZero: true, ticks: { precision: 0 }, grid: { color: "#edf0f7" } } } }
    });

    const insightBox = document.getElementById("analytics-insights");
    insightBox.replaceChildren();
    const easy = analyzed.filter((item) => normalizeDifficulty(item.analysis?.difficulty) === "Easy").length;
    const medium = analyzed.filter((item) => normalizeDifficulty(item.analysis?.difficulty) === "Medium").length;
    const hard = analyzed.filter((item) => normalizeDifficulty(item.analysis?.difficulty) === "Hard").length;
    const pending = selected.length - analyzed.length;
    const topBloom = [...bloomCounts.entries()].sort((a,b) => b[1]-a[1])[0];
    const insightLines = [
        [`${selected.length}`, paperAnalyticsState.selectedSubject === "All subjects" ? "questions in this paper" : `questions in ${paperAnalyticsState.selectedSubject}`],
        [`${easy}`, "easy questions analyzed"], [`${medium}`, "medium questions analyzed"], [`${hard}`, "hard questions analyzed"],
        [pending, "questions awaiting analysis"]
    ];
    insightLines.forEach(([value, label]) => { const row = createTextElement("div", "insight-line", ""); row.append(createTextElement("strong", "", String(value)), createTextElement("span", "", label)); insightBox.appendChild(row); });
    if (topBloom) insightBox.appendChild(createTextElement("p", "insight-highlight", `Most common Bloom's level: ${topBloom[0]} (${topBloom[1]} questions).`));
    if (!analyzed.length) insightBox.appendChild(createTextElement("p", "insight-highlight", "Detailed charts will populate when analysis results are available."));
}

function renderPaperAnalytics(paper, questions) {
    const panel = document.getElementById("paper-analytics");
    if (!panel) return;
    const all = Array.isArray(questions) ? questions : [];
    const analyzed = all.filter((item) => item.analysis);
    const pending = all.length - analyzed.length;
    const coverage = all.length ? Math.round(analyzed.length / all.length * 100) : 0;
    setText("analytics-total", all.length, "0");
    setText("analytics-analyzed", analyzed.length, "0");
    setText("analytics-pending", pending, "0");
    setText("analytics-coverage", `${coverage}%`, "0%");
    const fill = document.getElementById("analytics-coverage-fill"); if (fill) fill.style.width = `${coverage}%`;
    setText("analytics-paper-caption", `${paper?.paper_name || "Uploaded paper"} · ${all.length} extracted questions`);
    const subjectSet = new Set(all.map((item) => analyticsSubjectFor(item, paper?.subject, Boolean(item.analysis))));
    paperAnalyticsState = { paper, questions: all, selectedSubject: "All subjects", subjects: [...subjectSet].sort() };
    renderSubjectFilters();
    renderFilteredCharts();
    const note = document.getElementById("analytics-data-note");
    note.textContent = "Subject counts use explicit subject labels when available. Successfully analyzed questions are associated with the active Java analyzer when no subject label is returned. Questions without analysis are excluded from difficulty, Bloom's taxonomy and marks charts; unclassified questions are not guessed.";
    panel.hidden = false;
}

function createTextElement(tag, className, text) {
    const element = document.createElement(tag);
    if (className) element.className = className;
    element.textContent = text ?? "";
    return element;
}

function getMarkRange(value) {
    const matches = String(value ?? "").match(/\d+(?:\.\d+)?/g);
    if (!matches) return null;

    if (matches.length >= 2) {
        return { min: Number(matches[0]), max: Number(matches[1]) };
    }

    const number = Number(matches[0]);
    return { min: number, max: number };
}

function renderIndividualQuestions() {
    individualQuestionList.replaceChildren();

    if (!currentPaperQuestions.length) {
        showEmptyState(
            individualQuestionList,
            "No analyzed questions are available yet. Process a question paper first."
        );
        return;
    }

    currentPaperQuestions.forEach((item, index) => {
        const analysis = item.analysis || {};
        const card = createTextElement("article", "individual-question-card premium-question-card");

        const difficulty = normalizeDifficulty(
            getAnalysisValue(analysis, ["difficulty", "difficulty_level"])
        );
        const scoreRaw = analysis.score ?? analysis.difficulty_score;
        const score = Number(scoreRaw);
        const scoreMaxRaw = analysis.score_out_of ?? 10;
        const scoreMax = Number(scoreMaxRaw);
        const hasScore = scoreRaw !== null && scoreRaw !== undefined &&
            String(scoreRaw).trim() !== "" && Number.isFinite(score) &&
            Number.isFinite(scoreMax) && scoreMax > 0;
        const scorePercent = hasScore
            ? Math.max(0, Math.min(100, (score / scoreMax) * 100))
            : 0;

        const subject = analyticsSubjectFor(
            item,
            currentPaperMetadata?.subject,
            true
        );
        const top = createTextElement("div", "pq-topline");
        const identity = createTextElement("div", "pq-identity");
        identity.append(
            createTextElement("span", "pq-index", `Q${item.question_number || index + 1}`),
            createTextElement("span", "pq-subject", subject)
        );

        const difficultyBadge = createTextElement(
            "span",
            `pq-difficulty pq-${difficulty.toLowerCase()}`,
            difficulty === "Unclassified" ? "NOT CLASSIFIED" : difficulty.toUpperCase()
        );
        top.append(identity, difficultyBadge);

        const questionText = createTextElement(
            "h3",
            "pq-question",
            item.question_text || "Question text unavailable"
        );

        const overview = createTextElement("div", "pq-overview");
        const gauge = createTextElement("div", "pq-gauge");
        if (hasScore) {
            gauge.style.setProperty("--score-angle", `${scorePercent * 3.6}deg`);
            gauge.append(
                createTextElement("strong", "pq-score-number", score.toFixed(1)),
                createTextElement("span", "pq-score-scale", `/ ${scoreMax}`)
            );
        } else {
            gauge.classList.add("pq-gauge-unavailable");
            gauge.append(
                createTextElement("strong", "pq-score-number", "—"),
                createTextElement("span", "pq-score-scale", "Score unavailable")
            );
        }

        const summary = createTextElement("div", "pq-summary");
        summary.append(
            createTextElement("span", "pq-summary-label", "DIFFICULTY SCORE"),
            createTextElement("strong", "pq-summary-title",
                difficulty === "Unclassified" ? "Analysis label unavailable" : `${difficulty} question`),
            createTextElement("span", "pq-summary-meta",
                `Bloom's level · ${getAnalysisValue(analysis, ["bloom_level"]) || "Not available"}`)
        );
        overview.append(gauge, summary);

        const concepts = Array.isArray(analysis.detected_concepts)
            ? analysis.detected_concepts.map((concept) =>
                typeof concept === "string"
                    ? concept
                    : concept?.concept || concept?.name || ""
            ).filter(Boolean)
            : [];

        const conceptSection = createTextElement("section", "pq-section");
        conceptSection.append(
            createTextElement("div", "pq-section-heading", `✧  DETECTED CONCEPTS (${concepts.length})`)
        );
        const chips = createTextElement("div", "pq-concept-chips");
        if (concepts.length) {
            concepts.forEach((concept) => chips.appendChild(
                createTextElement("span", "pq-concept-chip", concept)
            ));
        } else {
            chips.appendChild(createTextElement("span", "pq-muted", "No detected concepts returned."));
        }
        conceptSection.appendChild(chips);

        const breakdownSection = createTextElement("section", "pq-section");
        breakdownSection.appendChild(
            createTextElement("div", "pq-section-heading", "▥  SCORE BREAKDOWN")
        );
        const breakdown = analysis.score_breakdown &&
            typeof analysis.score_breakdown === "object"
            ? Object.entries(analysis.score_breakdown)
                .filter(([, value]) => Number.isFinite(Number(value)))
            : [];

        if (breakdown.length) {
            const maxBreakdown = Math.max(...breakdown.map(([, value]) => Math.abs(Number(value))), 0.01);
            breakdown.forEach(([label, value], barIndex) => {
                const row = createTextElement("div", "pq-breakdown-row");
                const name = createTextElement("span", "pq-breakdown-name", label.replace(/_/g, " "));
                const track = createTextElement("span", "pq-breakdown-track");
                const fill = createTextElement("span", `pq-breakdown-fill pq-bar-${barIndex % 5}`);
                fill.style.width = `${Math.max(3, Math.min(100, Math.abs(Number(value)) / maxBreakdown * 100))}%`;
                track.appendChild(fill);
                const number = createTextElement("strong", "pq-breakdown-value", String(value));
                row.append(name, track, number);
                breakdownSection.appendChild(row);
            });
        } else {
            breakdownSection.appendChild(
                createTextElement("p", "pq-muted", "Score breakdown is not available for this question.")
            );
        }

        const explanation = createTextElement(
            "p",
            "pq-explanation-text",
            analysis.analysis_explanation || analysis.difficulty_reason ||
                "A detailed explanation was not returned by the analyzer."
        );

        const detailGrid = createTextElement("div", "pq-detail-grid");
        const detailItems = [
            ["Main concept", analysis.main_concept],
            ["Bloom's level", analysis.bloom_level],
            ["Marks", analysis.suggested_marks],
            ["Supporting concepts", analysis.supporting_concepts]
        ];
        detailItems.forEach(([label, value]) => {
            const tile = createTextElement("div", "pq-detail-tile");
            tile.append(
                createTextElement("span", "pq-detail-label", label),
                createTextElement("strong", "pq-detail-value",
                    value === null || value === undefined || value === "" ? "Not available" : String(value))
            );
            detailGrid.appendChild(tile);
        });

        const explanationPanel = createTextElement("section", "pq-explanation-panel");
        explanationPanel.append(
            createTextElement("div", "pq-section-heading", "✦  AI ANALYSIS"),
            explanation,
            detailGrid
        );

        const actions = createTextElement("div", "pq-actions");
        const addButton = createTextElement(
            "button",
            "add-to-builder-button pq-add-button",
            selectedBuilderQuestions.some((q) => q.id === item.id)
                ? "✓  Added to Question Paper"
                : "+  Add to Question Paper"
        );
        addButton.type = "button";
        addButton.disabled = selectedBuilderQuestions.some((q) => q.id === item.id);
        addButton.addEventListener("click", () => {
            if (selectedBuilderQuestions.some((q) => q.id === item.id)) return;
            selectedBuilderQuestions.push(item);
            renderQuestionBuilder();
            renderIndividualQuestions();
        });

        const toggleButton = createTextElement("button", "pq-toggle-button", "Hide analysis ↑");
        toggleButton.type = "button";
        const analysisContent = createTextElement("div", "pq-analysis-content");
        analysisContent.append(conceptSection, breakdownSection, explanationPanel);
        toggleButton.addEventListener("click", () => {
            const hidden = analysisContent.hidden;
            analysisContent.hidden = !hidden;
            toggleButton.textContent = hidden ? "Hide analysis ↑" : "View full analysis ↓";
            toggleButton.setAttribute("aria-expanded", String(hidden));
        });

        actions.append(toggleButton, addButton);
        card.append(top, questionText, overview, analysisContent, actions);
        individualQuestionList.appendChild(card);
    });
}

function renderQuestionMap() {
    questionMapContent.replaceChildren();

    if (!currentPaperQuestions.length) {
        showEmptyState(
            questionMapContent,
            "The question map will appear after question analysis."
        );
        return;
    }

    const groups = new Map();

    currentPaperQuestions.forEach((item) => {
        const concept = item.analysis?.main_concept || "Unclassified";
        if (!groups.has(concept)) groups.set(concept, []);
        groups.get(concept).push(item);
    });

    groups.forEach((questions, concept) => {
        const group = createTextElement("section", "concept-map-group");
        const title = createTextElement(
            "h3",
            "concept-map-title",
            `${concept} (${questions.length})`
        );

        group.appendChild(title);

        questions.forEach((item) => {
            group.appendChild(
                createTextElement(
                    "p",
                    "concept-map-question",
                    `Q${item.question_number}: ${item.question_text}`
                )
            );
        });

        questionMapContent.appendChild(group);
    });
}

function renderQuestionBuilder() {
    questionBuilderList.replaceChildren();

    if (!selectedBuilderQuestions.length) {
        showEmptyState(
            questionBuilderList,
            "Add questions from the Individual Questions section to build your paper."
        );
    } else {
        selectedBuilderQuestions.forEach((item) => {
            const row = createTextElement("div", "builder-question-item");
            const text = createTextElement(
                "p",
                "builder-question-text",
                `Q${item.question_number}: ${item.question_text}`
            );

            const removeButton = createTextElement(
                "button",
                "remove-builder-question",
                "Remove"
            );

            removeButton.type = "button";
            removeButton.addEventListener("click", () => {
                selectedBuilderQuestions = selectedBuilderQuestions.filter(
                    (question) => question.id !== item.id
                );
                renderQuestionBuilder();
                renderIndividualQuestions();
            });

            row.append(text, removeButton);
            questionBuilderList.appendChild(row);
        });
    }

    const ranges = selectedBuilderQuestions
        .map((item) => getMarkRange(item.analysis?.suggested_marks))
        .filter(Boolean);

    const minTotal = ranges.reduce((sum, range) => sum + range.min, 0);
    const maxTotal = ranges.reduce((sum, range) => sum + range.max, 0);

    downloadBuilderButton.disabled = selectedBuilderQuestions.length === 0;

    builderQuestionCount.textContent =
        `${selectedBuilderQuestions.length} question(s) selected`;

    builderTotalMarks.textContent = ranges.length
        ? `Total marks: ${minTotal}-${maxTotal}`
        : "Total marks: Not available";
}

function downloadQuestionPaper() {
    if (!selectedBuilderQuestions.length) {
        return;
    }

    if (!window.jspdf || !window.jspdf.jsPDF) {
        alert("PDF library could not load. Please check your internet connection and refresh.");
        return;
    }

    const { jsPDF } = window.jspdf;
    const doc = new jsPDF({ orientation: "portrait", unit: "mm", format: "a4" });

    const pageWidth = doc.internal.pageSize.getWidth();
    const pageHeight = doc.internal.pageSize.getHeight();
    const margin = 18;
    const contentWidth = pageWidth - margin * 2;
    let y = 20;

    const ranges = selectedBuilderQuestions
        .map((item) => getMarkRange(item.analysis?.suggested_marks))
        .filter(Boolean);

    const minTotal = ranges.reduce((sum, range) => sum + range.min, 0);
    const maxTotal = ranges.reduce((sum, range) => sum + range.max, 0);

    const totalMarks = ranges.length
        ? (minTotal === maxTotal ? `${minTotal}` : `${minTotal}-${maxTotal}`)
        : "Not available";

    function addPageIfNeeded(requiredHeight) {
        if (y + requiredHeight > pageHeight - 18) {
            doc.addPage();
            y = 20;
        }
    }

    // Document heading
    doc.setFont("helvetica", "bold");
    doc.setFontSize(19);
    doc.text("PaperMind AI", pageWidth / 2, y, { align: "center" });
    y += 9;

    doc.setFont("helvetica", "normal");
    doc.setFontSize(12);
    doc.text("Custom Question Paper", pageWidth / 2, y, { align: "center" });
    y += 7;

    doc.setFontSize(9);
    doc.text(`Date: ${new Date().toLocaleDateString()}`, pageWidth / 2, y, {
        align: "center"
    });
    y += 8;

    doc.setDrawColor(160);
    doc.line(margin, y, pageWidth - margin, y);
    y += 10;

    // Questions
    selectedBuilderQuestions.forEach((item, index) => {
        const range = getMarkRange(item.analysis?.suggested_marks);

        const marks = range
            ? (range.min === range.max
                ? `${range.min}`
                : `${range.min}-${range.max}`)
            : "Not specified";

        const questionLines = doc.splitTextToSize(
            String(item.question_text || ""),
            contentWidth
        );

        const requiredHeight = 12 + questionLines.length * 6 + 7;
        addPageIfNeeded(requiredHeight);

        doc.setFont("helvetica", "bold");
        doc.setFontSize(12);
        doc.text(`Question ${index + 1}`, margin, y);
        y += 7;

        doc.setFont("helvetica", "normal");
        doc.setFontSize(11);
        doc.text(questionLines, margin, y);
        y += questionLines.length * 6 + 2;

        doc.setFont("helvetica", "bold");
        doc.setFontSize(10);
        doc.text(`Marks: ${marks}`, margin, y);
        y += 9;

        doc.setDrawColor(220);
        doc.line(margin, y, pageWidth - margin, y);
        y += 8;
    });

    // Summary
    addPageIfNeeded(25);
    doc.setFont("helvetica", "bold");
    doc.setFontSize(11);
    doc.text(`Total questions: ${selectedBuilderQuestions.length}`, margin, y);
    y += 7;
    doc.text(`Total marks: ${totalMarks}`, margin, y);

    // Page numbers
    const pageCount = doc.internal.getNumberOfPages();

    for (let page = 1; page <= pageCount; page++) {
        doc.setPage(page);
        doc.setFont("helvetica", "normal");
        doc.setFontSize(8);
        doc.text(
            `PaperMind AI | Page ${page} of ${pageCount}`,
            pageWidth / 2,
            pageHeight - 8,
            { align: "center" }
        );
    }

    doc.save("PaperMind-AI-Question-Paper.pdf");
}
downloadBuilderButton.addEventListener("click", downloadQuestionPaper);
clearBuilderButton.addEventListener("click", () => {
    selectedBuilderQuestions = [];
    renderQuestionBuilder();
    renderIndividualQuestions();
});

async function loadIndividualQuestions(paperId) {
    showEmptyState(individualQuestionList, "Loading individual questions...");
    showEmptyState(questionMapContent, "Building question map...");

    const paperData = await fetchJson(
        `${PAPERS_API}/${encodeURIComponent(paperId)}`
    );

    if (!Array.isArray(paperData.questions)) {
        throw new Error("The paper details API returned an invalid questions list.");
    }

    const loadedQuestions = await Promise.all(
        paperData.questions.map(async (question) => {
            const detail = await fetchJson(
                `${API_BASE}/api/questions/${encodeURIComponent(question.id)}/analysis`
            );

            const analyses = Array.isArray(detail.analyses)
                ? detail.analyses
                : [];

            return {
                ...question,
                paper_id: paperId,
                analysis: analyses[0] || null
            };
        })
    );

    allPaperQuestions = loadedQuestions;
    currentPaperQuestions = loadedQuestions.filter((item) => item.analysis);

    renderPaperAnalytics(currentPaperMetadata, allPaperQuestions);
    renderIndividualQuestions();
    renderQuestionMap();
    renderQuestionBuilder();

    if (loadedQuestions.length && !currentPaperQuestions.length) {
        showEmptyState(
            individualQuestionList,
            "Questions were extracted, but no detailed analyses are available."
        );
    }
}

/* INITIALIZE DASHBOARD */

async function initializeDashboard() {
    await Promise.allSettled([
        checkBackend(),
        loadTopics()
    ]);

    updateQuestionCount();
}

initializeDashboard();














