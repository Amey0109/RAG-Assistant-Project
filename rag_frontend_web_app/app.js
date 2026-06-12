const API_BASE_URL = "http://127.0.0.1:8000";

// ── Auth state ──────────────────────────────────────────────
let authToken = sessionStorage.getItem("authToken");
let currentUsername = sessionStorage.getItem("username");
let currentAuthTab = "login";

const authScreen   = document.getElementById("authScreen");
const authUsername = document.getElementById("authUsername");
const authPassword = document.getElementById("authPassword");
const authSubmitBtn = document.getElementById("authSubmitBtn");
const authError    = document.getElementById("authError");
const userBadge    = document.getElementById("userBadge");

// ── DOM refs (same as before) ───────────────────────────────
const pdfInput       = document.getElementById("pdfInput");
const fileName       = document.getElementById("fileName");
const uploadBtn      = document.getElementById("uploadBtn");
const uploadStatus   = document.getElementById("uploadStatus");
const replaceExisting = document.getElementById("replaceExisting");
const documentsList  = document.getElementById("documentsList");
const refreshDocsBtn = document.getElementById("refreshDocsBtn");
const chatForm       = document.getElementById("chatForm");
const queryInput     = document.getElementById("queryInput");
const chatMessages   = document.getElementById("chatMessages");
const sendBtn        = document.getElementById("sendBtn");
const apiBadge       = document.getElementById("apiBadge");
const dropZone       = document.querySelector(".drop-zone");

// Auto-restore session on page load
document.addEventListener("DOMContentLoaded", () => {
    if (authToken) {
        authScreen.classList.add("hidden");
        userBadge.textContent = `👤 ${currentUsername}`;
        checkApiHealth();
        loadDocuments();
    }
});

// ── Auth helpers ────────────────────────────────────────────

function switchAuthTab(tab) {
    currentAuthTab = tab;
    document.getElementById("loginTabBtn").classList.toggle("active", tab === "login");
    document.getElementById("registerTabBtn").classList.toggle("active", tab === "register");
    authSubmitBtn.textContent = tab === "login" ? "Login" : "Register";
    authError.textContent = "";
}

async function handleAuth() {
    const username = authUsername.value.trim();
    const password = authPassword.value.trim();

    if (!username || !password) {
        authError.textContent = "Username and password are required.";
        return;
    }

    authSubmitBtn.disabled = true;
    authSubmitBtn.textContent = "Please wait...";
    authError.textContent = "";

    try {
        const endpoint = currentAuthTab === "login" ? "/auth/login" : "/auth/register";
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, password })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Authentication failed.");
        }

        authToken = data.token;
        currentUsername = data.username;
        sessionStorage.setItem("authToken", data.token);    // persist token
        sessionStorage.setItem("username", data.username);  // persist username

        authScreen.classList.add("hidden");
        userBadge.textContent = `👤 ${currentUsername}`;

        checkApiHealth();
        loadDocuments();

    } catch (error) {
        authError.textContent = error.message;
    } finally {
        authSubmitBtn.disabled = false;
        authSubmitBtn.textContent = currentAuthTab === "login" ? "Login" : "Register";
    }
}

function logout() {
    authToken = null;
    currentUsername = null;
    sessionStorage.removeItem("authToken");   // clear on logout
    sessionStorage.removeItem("username");    // clear on logout
    authUsername.value = "";
    authPassword.value = "";
    authError.textContent = "";
    authScreen.classList.remove("hidden");

    chatMessages.innerHTML = `
        <div class="message assistant-message">
            <div class="avatar">AI</div>
            <div class="bubble"><p>Hello! Upload a PDF, then ask me questions about your documents.</p></div>
        </div>`;
    documentsList.innerHTML = `<div class="empty-state">No documents loaded yet.</div>`;
}
// ── API helper — adds auth header, handles 401 ──────────────
async function apiFetch(url, options = {}) {
    if (!authToken) {
        logout();
        throw new Error("Not authenticated.");
    }
    const headers = {
        ...(options.headers || {}),
        "Authorization": `Bearer ${authToken}`
    };

    const response = await fetch(url, { ...options, headers });

    if (response.status === 401) {
        const errorData = await response.json().catch(() => ({}));
        console.error("401 error detail:", errorData);

        // Only logout if token is actually invalid
        if (errorData.detail === "Invalid or expired token.") {
            logout();
            throw new Error("Session expired. Please log in again.");
        }

        // Otherwise just throw without logging out
        throw new Error(errorData.detail || "Unauthorized.");
    }

    return response;
}

// ── Existing functions (updated to use apiFetch) ────────────

function setStatus(element, message, type = "") {
    element.textContent = message;
    element.className = `status-text ${type}`.trim();
}

function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function addMessage(role, text = "") {
    const message = document.createElement("div");
    message.className = `message ${role === "user" ? "user-message" : "assistant-message"}`;

    const avatar = document.createElement("div");
    avatar.className = "avatar";
    avatar.textContent = role === "user" ? "YOU" : "AI";

    const bubble = document.createElement("div");
    bubble.className = "bubble";

    const content = document.createElement("p");
    content.textContent = text;

    bubble.appendChild(content);
    message.appendChild(avatar);
    message.appendChild(bubble);
    chatMessages.appendChild(message);
    scrollToBottom();

    return content;
}

function autoResizeTextarea() {
    queryInput.style.height = "auto";
    queryInput.style.height = `${queryInput.scrollHeight}px`;
}

async function checkApiHealth() {
    try {
        const response = await fetch(`${API_BASE_URL}/`);
        if (!response.ok) throw new Error();
        apiBadge.textContent = "Connected";
        apiBadge.classList.add("ok");
        apiBadge.classList.remove("error");
    } catch {
        apiBadge.textContent = "Disconnected";
        apiBadge.classList.add("error");
        apiBadge.classList.remove("ok");
    }
}

async function loadDocuments() {
    documentsList.innerHTML = `<div class="empty-state">Loading documents...</div>`;
    try {
        const response = await apiFetch(`${API_BASE_URL}/documents`);
        if (!response.ok) throw new Error("Failed to load documents");

        const data = await response.json();
        const documents = data.documents || [];

        if (documents.length === 0) {
            documentsList.innerHTML = `<div class="empty-state">No documents loaded yet.</div>`;
            return;
        }

        documentsList.innerHTML = "";
        documents.forEach((docName) => {
            const item = document.createElement("div");
            item.className = "document-item";

            const info = document.createElement("div");
            const name = document.createElement("div");
            name.className = "document-name";
            name.textContent = docName;

            const meta = document.createElement("div");
            meta.className = "document-meta";
            meta.textContent = "Ready to chat";

            info.appendChild(name);
            info.appendChild(meta);

            const deleteBtn = document.createElement("button");
            deleteBtn.className = "delete-btn";
            deleteBtn.textContent = "Delete";
            deleteBtn.onclick = () => deleteDocument(docName);

            item.appendChild(info);
            item.appendChild(deleteBtn);
            documentsList.appendChild(item);
        });
    } catch (error) {
        documentsList.innerHTML = `<div class="empty-state">Could not load documents.</div>`;
    }
}

async function uploadDocument() {
    const file = pdfInput.files[0];
    if (!file) { setStatus(uploadStatus, "Please choose a PDF file first.", "error"); return; }
    if (!file.name.toLowerCase().endsWith(".pdf")) { setStatus(uploadStatus, "Only PDF files are allowed.", "error"); return; }

    const formData = new FormData();
    formData.append("file", file);

    const replace = replaceExisting.checked ? "true" : "false";
    const url = `${API_BASE_URL}/documents/upload?replace_existing_source=${replace}`;

    uploadBtn.disabled = true;
    uploadBtn.textContent = "Adding...";
    setStatus(uploadStatus, "Adding document. This may take some time...", "");

    try {
        const response = await apiFetch(url, { method: "POST", body: formData });
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "Upload failed");

        setStatus(uploadStatus, "Document added successfully.", "success");
        pdfInput.value = "";
        fileName.textContent = "Choose a PDF";
        await loadDocuments();
    } catch (error) {
        setStatus(uploadStatus, error.message, "error");
    } finally {
        uploadBtn.disabled = false;
        uploadBtn.textContent = "Add Document";
    }
}

async function deleteDocument(sourceName) {
    if (!confirm(`Delete "${sourceName}" from ChromaDB?`)) return;

    try {
        const url = `${API_BASE_URL}/documents?source_name=${encodeURIComponent(sourceName)}`;
        const response = await apiFetch(url, { method: "DELETE" });
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "Delete failed");

        addMessage("assistant", `Deleted "${sourceName}".`);
        await loadDocuments();
    } catch (error) {
        addMessage("assistant", `Delete failed: ${error.message}`);
    }
}

function askStreamingQuestion(query) {
    addMessage("user", query);

    const assistantContent = addMessage("assistant", "");
    assistantContent.classList.add("loading-dots");
    assistantContent.textContent = "Thinking";

    sendBtn.disabled = true;
    queryInput.disabled = true;

    // SSE with auth token — EventSource doesn't support headers
    // so we pass token as query param
    const url = `${API_BASE_URL}/query/stream?query=${encodeURIComponent(query)}&token=${encodeURIComponent(authToken)}`;
    const eventSource = new EventSource(url);
    let started = false;

    eventSource.onmessage = (event) => {
        if (!started) {
            assistantContent.classList.remove("loading-dots");
            assistantContent.textContent = "";
            started = true;
        }
        const data = JSON.parse(event.data);
        assistantContent.textContent += data.content;
        scrollToBottom();
    };

    eventSource.addEventListener("done", () => {
        eventSource.close();
        sendBtn.disabled = false;
        queryInput.disabled = false;
        queryInput.focus();
        if (!assistantContent.textContent.trim()) {
            assistantContent.textContent = "No response received.";
        }
    });

    eventSource.addEventListener("error", () => {
        eventSource.close();
        assistantContent.classList.remove("loading-dots");
        if (!assistantContent.textContent.trim()) {
            assistantContent.textContent = "Streaming connection error.";
        }
        sendBtn.disabled = false;
        queryInput.disabled = false;
        queryInput.focus();
    });
}

// ── Event listeners (unchanged) ─────────────────────────────

pdfInput.addEventListener("change", () => {
    fileName.textContent = pdfInput.files[0] ? pdfInput.files[0].name : "Choose a PDF";
});

uploadBtn.addEventListener("click", uploadDocument);
refreshDocsBtn.addEventListener("click", loadDocuments);

chatForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const query = queryInput.value.trim();
    if (!query) return;
    queryInput.value = "";
    autoResizeTextarea();
    askStreamingQuestion(query);
});

queryInput.addEventListener("input", autoResizeTextarea);

queryInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        chatForm.requestSubmit();
    }
});

["dragenter", "dragover"].forEach((e) => {
    dropZone.addEventListener(e, (event) => { event.preventDefault(); dropZone.classList.add("drag-over"); });
});
["dragleave", "drop"].forEach((e) => {
    dropZone.addEventListener(e, (event) => { event.preventDefault(); dropZone.classList.remove("drag-over"); });
});
dropZone.addEventListener("drop", (event) => {
    const file = event.dataTransfer.files[0];
    if (!file) return;
    const dt = new DataTransfer();
    dt.items.add(file);
    pdfInput.files = dt.files;
    fileName.textContent = file.name;
});