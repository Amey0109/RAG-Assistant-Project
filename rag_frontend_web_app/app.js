const API_BASE_URL = "http://127.0.0.1:8000";

const pdfInput = document.getElementById("pdfInput");
const fileName = document.getElementById("fileName");
const uploadBtn = document.getElementById("uploadBtn");
const uploadStatus = document.getElementById("uploadStatus");
const replaceExisting = document.getElementById("replaceExisting");
const documentsList = document.getElementById("documentsList");
const refreshDocsBtn = document.getElementById("refreshDocsBtn");
const chatForm = document.getElementById("chatForm");
const queryInput = document.getElementById("queryInput");
const chatMessages = document.getElementById("chatMessages");
const sendBtn = document.getElementById("sendBtn");
const apiBadge = document.getElementById("apiBadge");
const dropZone = document.querySelector(".drop-zone");

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
        if (!response.ok) {
            throw new Error("API not available");
        }

        apiBadge.textContent = "Connected";
        apiBadge.classList.add("ok");
        apiBadge.classList.remove("error");
    } catch (error) {
        apiBadge.textContent = "Disconnected";
        apiBadge.classList.add("error");
        apiBadge.classList.remove("ok");
    }
}

async function loadDocuments() {
    documentsList.innerHTML = `<div class="empty-state">Loading documents...</div>`;

    try {
        const response = await fetch(`${API_BASE_URL}/documents`);

        if (!response.ok) {
            throw new Error("Failed to load documents");
        }

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
        documentsList.innerHTML = `<div class="empty-state">Could not load documents. Please check the connection.</div>`;
    }
}

async function uploadDocument() {
    const file = pdfInput.files[0];

    if (!file) {
        setStatus(uploadStatus, "Please choose a PDF file first.", "error");
        return;
    }

    if (!file.name.toLowerCase().endsWith(".pdf")) {
        setStatus(uploadStatus, "Only PDF files are allowed.", "error");
        return;
    }

    const formData = new FormData();
    formData.append("file", file);

    const replace = replaceExisting.checked ? "true" : "false";
    const url = `${API_BASE_URL}/documents/upload?replace_existing_source=${replace}`;

    uploadBtn.disabled = true;
    uploadBtn.textContent = "Adding...";
    setStatus(uploadStatus, "Adding document. This may take some time...", "");

    try {
        const response = await fetch(url, {
            method: "POST",
            body: formData,
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Upload failed");
        }

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
    const confirmed = confirm(`Delete "${sourceName}" from ChromaDB?`);

    if (!confirmed) {
        return;
    }

    try {
        const url = `${API_BASE_URL}/documents?source_name=${encodeURIComponent(sourceName)}`;

        const response = await fetch(url, {
            method: "DELETE",
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Delete failed");
        }

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

    const url = `${API_BASE_URL}/query/stream?query=${encodeURIComponent(query)}`;

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

    eventSource.addEventListener("error", (event) => {
        eventSource.close();
        assistantContent.classList.remove("loading-dots");

        if (!assistantContent.textContent.trim()) {
            assistantContent.textContent = "Streaming connection error.";
        } else {
            assistantContent.textContent += "\n\n[Streaming connection ended.]";
        }

        sendBtn.disabled = false;
        queryInput.disabled = false;
        queryInput.focus();
    });
}

pdfInput.addEventListener("change", () => {
    const file = pdfInput.files[0];
    fileName.textContent = file ? file.name : "Choose a PDF";
});

uploadBtn.addEventListener("click", uploadDocument);
refreshDocsBtn.addEventListener("click", loadDocuments);

chatForm.addEventListener("submit", (event) => {
    event.preventDefault();

    const query = queryInput.value.trim();

    if (!query) {
        return;
    }

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

["dragenter", "dragover"].forEach((eventName) => {
    dropZone.addEventListener(eventName, (event) => {
        event.preventDefault();
        dropZone.classList.add("drag-over");
    });
});

["dragleave", "drop"].forEach((eventName) => {
    dropZone.addEventListener(eventName, (event) => {
        event.preventDefault();
        dropZone.classList.remove("drag-over");
    });
});

dropZone.addEventListener("drop", (event) => {
    const file = event.dataTransfer.files[0];

    if (!file) {
        return;
    }

    const dataTransfer = new DataTransfer();
    dataTransfer.items.add(file);
    pdfInput.files = dataTransfer.files;

    fileName.textContent = file.name;
});

checkApiHealth();
loadDocuments();
