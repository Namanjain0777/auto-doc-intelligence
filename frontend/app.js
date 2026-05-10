const API_BASE = 'http://localhost:8000/api';

document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    initUpload();
    initQuery();
    loadSuggestedQuestions();
    loadStats();
});

// Tab Navigation
function initTabs() {
    const navBtns = document.querySelectorAll('.nav-btn');
    const sections = document.querySelectorAll('.tab-section');

    navBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const tab = btn.dataset.tab;
            
            navBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            sections.forEach(s => s.classList.remove('active'));
            document.getElementById(`${tab}-section`).classList.add('active');
            
            if (tab === 'documents') {
                loadStats();
            }
        });
    });
}

// Upload Functions
function initUpload() {
    const uploadArea = document.getElementById('upload-area');
    const fileInput = document.getElementById('file-input');

    uploadArea.addEventListener('click', () => fileInput.click());
    
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = 'var(--primary)';
    });
    
    uploadArea.addEventListener('dragleave', () => {
        uploadArea.style.borderColor = 'var(--gray-300)';
    });
    
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = 'var(--gray-300)';
        const files = e.dataTransfer.files;
        if (files.length) handleFileUpload(files[0]);
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length) handleFileUpload(e.target.files[0]);
    });
}

async function handleFileUpload(file) {
    if (!file.name.toLowerCase().endsWith('.pdf')) {
        alert('Please upload a PDF file');
        return;
    }

    const uploadArea = document.getElementById('upload-area');
    const uploadProgress = document.getElementById('upload-progress');
    const fileName = document.getElementById('file-name');
    const progressPercent = document.getElementById('progress-percent');
    const progressFill = document.getElementById('progress-fill');
    const progressStatus = document.getElementById('progress-status');

    uploadArea.classList.add('hidden');
    uploadProgress.classList.remove('hidden');
    fileName.textContent = file.name;
    progressPercent.textContent = '0%';
    progressFill.style.width = '0%';
    progressStatus.textContent = 'Uploading...';

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch(`${API_BASE}/documents/upload`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) throw new Error('Upload failed');

        const result = await response.json();
        
        progressPercent.textContent = '100%';
        progressFill.style.width = '100%';
        progressStatus.textContent = 'Processing...';

        // Wait a bit for processing
        setTimeout(() => {
            uploadProgress.classList.add('hidden');
            uploadArea.classList.remove('hidden');
            addUploadedFile(file.name, 'Processed');
            loadStats();
        }, 2000);

    } catch (error) {
        alert('Error uploading file: ' + error.message);
        uploadProgress.classList.add('hidden');
        uploadArea.classList.remove('hidden');
    }
}

function addUploadedFile(name, status) {
    const uploadedFiles = document.getElementById('uploaded-files');
    const filesList = document.getElementById('files-list');

    uploadedFiles.classList.remove('hidden');
    
    const li = document.createElement('li');
    li.innerHTML = `
        <span class="file-icon">📄</span>
        <span class="file-name">${name}</span>
        <span class="file-status">✓ ${status}</span>
    `;
    filesList.appendChild(li);
}

// Query Functions
function initQuery() {
    const queryInput = document.getElementById('query-input');
    const queryBtn = document.getElementById('query-btn');

    queryBtn.addEventListener('click', executeQuery);
    queryInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && e.ctrlKey) executeQuery();
    });
}

async function loadSuggestedQuestions() {
    try {
        const response = await fetch(`${API_BASE}/query/suggested-questions`);
        const data = await response.json();
        
        const suggestionsList = document.getElementById('suggestions-list');
        data.suggested_questions.slice(0, 6).forEach(q => {
            const chip = document.createElement('span');
            chip.className = 'suggestion-chip';
            chip.textContent = q;
            chip.addEventListener('click', () => {
                document.getElementById('query-input').value = q;
            });
            suggestionsList.appendChild(chip);
        });
    } catch (error) {
        console.error('Error loading suggestions:', error);
    }
}

async function executeQuery() {
    const queryInput = document.getElementById('query-input');
    const queryBtn = document.getElementById('query-btn');
    const queryResults = document.getElementById('query-results');
    const loading = document.getElementById('loading');
    const answerContent = document.getElementById('answer-content');
    const sourcesList = document.getElementById('sources-list');
    const confidenceBadge = document.getElementById('confidence-badge');

    const query = queryInput.value.trim();
    if (!query) return;

    queryBtn.disabled = true;
    queryResults.classList.add('hidden');
    loading.classList.remove('hidden');

    try {
        const response = await fetch(`${API_BASE}/query/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                query: query,
                max_results: 5,
                include_diagrams: true
            })
        });

        if (!response.ok) throw new Error('Query failed');

        const data = await response.json();

        answerContent.textContent = data.answer;
        
        const confidence = Math.round(data.confidence_score * 100);
        confidenceBadge.textContent = `Confidence: ${confidence}%`;
        confidenceBadge.style.background = confidence > 70 ? 'var(--success)' : 
                                            confidence > 40 ? 'var(--warning)' : 'var(--error)';

        sourcesList.innerHTML = '';
        data.sources.forEach(source => {
            const li = document.createElement('li');
            li.className = 'source-item';
            li.innerHTML = `
                <div class="source-page">${source.metadata?.document || 'Document'} - Page ${source.metadata?.page_number || '?'}</div>
                <div class="source-text">${source.content?.substring(0, 200)}...</div>
            `;
            sourcesList.appendChild(li);
        });

        loading.classList.add('hidden');
        queryResults.classList.remove('hidden');

    } catch (error) {
        alert('Error executing query: ' + error.message);
        loading.classList.add('hidden');
        queryBtn.disabled = false;
    }
}

// Document Stats
async function loadStats() {
    try {
        const response = await fetch(`${API_BASE}/documents/collections`);
        const data = await response.json();

        const stats = data.data?.vector_store || {};
        
        document.getElementById('doc-count').textContent = stats.document_count || 0;
        document.getElementById('chunk-count').textContent = stats.total_chunks || 0;
        document.getElementById('model-name').textContent = stats.embedding_model || '--';

    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

// Reset Knowledge Base
document.getElementById('reset-btn')?.addEventListener('click', async () => {
    if (!confirm('Are you sure you want to delete all documents? This cannot be undone.')) return;
    
    try {
        await fetch(`${API_BASE}/documents/reset`, { method: 'POST' });
        loadStats();
        alert('Knowledge base has been reset');
    } catch (error) {
        alert('Error resetting knowledge base: ' + error.message);
    }
});