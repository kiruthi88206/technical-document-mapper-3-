/* ==========================================================================
   DOCUMENT UPLOAD & NLP ANALYSIS MODULE
   ========================================================================== */

const UploadManager = {
    selectedFile: null,

    init() {
        this.bindEvents();
    },

    bindEvents() {
        const dropzone = document.getElementById('upload-dropzone');
        const fileInput = document.getElementById('file-input');

        if (!dropzone || !fileInput) return;

        dropzone.addEventListener('click', () => fileInput.click());

        dropzone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropzone.classList.add('dragover');
        });

        dropzone.addEventListener('dragleave', () => {
            dropzone.classList.remove('dragover');
        });

        dropzone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropzone.classList.remove('dragover');
            if (e.dataTransfer.files.length > 0) {
                this.handleFileSelect(e.dataTransfer.files[0]);
            }
        });

        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                this.handleFileSelect(e.target.files[0]);
            }
        });

        document.getElementById('btn-remove-file')?.addEventListener('click', () => {
            this.clearFileSelect();
        });

        document.getElementById('btn-start-upload')?.addEventListener('click', () => {
            this.uploadFile();
        });

        document.getElementById('btn-trigger-analysis')?.addEventListener('click', () => {
            this.runAnalysis();
        });

        document.getElementById('btn-view-graph-direct')?.addEventListener('click', () => {
            App.switchView('view-graph');
        });
    },

    handleFileSelect(file) {
        const ext = file.name.split('.').pop().toLowerCase();
        if (!['pdf', 'docx', 'txt'].includes(ext)) {
            App.showToast('Unsupported file format. Please upload PDF, DOCX, or TXT.', 'danger');
            return;
        }

        this.selectedFile = file;
        document.getElementById('info-file-name').innerText = file.name;
        document.getElementById('info-file-size').innerText = (file.size / (1024 * 1024)).toFixed(2) + ' MB';
        
        document.getElementById('file-info-container').classList.remove('d-none');
        document.getElementById('btn-start-upload').removeAttribute('disabled');
    },

    clearFileSelect() {
        this.selectedFile = null;
        document.getElementById('file-input').value = '';
        document.getElementById('file-info-container').classList.add('d-none');
        document.getElementById('btn-start-upload').setAttribute('disabled', 'true');
    },

    async uploadFile() {
        if (!this.selectedFile) return;

        const formData = new FormData();
        formData.append('file', this.selectedFile);

        const btn = document.getElementById('btn-start-upload');
        btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin me-2"></i>Uploading...`;
        btn.disabled = true;

        try {
            const res = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });

            const data = await res.json();
            btn.innerHTML = `<i class="fa-solid fa-upload me-2"></i>Upload & Proceed to Analysis`;
            btn.disabled = false;

            if (res.ok) {
                App.showToast(data.message, 'success');
                App.setActiveDocument(data.document._id, data.document.filename);
                this.clearFileSelect();
                App.switchView('view-analyze');
            } else {
                App.showToast(data.error || 'Upload failed', 'danger');
            }

        } catch (err) {
            btn.innerHTML = `<i class="fa-solid fa-upload me-2"></i>Upload & Proceed to Analysis`;
            btn.disabled = false;
            App.showToast('Server error uploading file', 'danger');
        }
    },

    async runAnalysis() {
        if (!App.currentDocId) {
            App.showToast('No document uploaded to analyze. Please upload a file first.', 'warning');
            return;
        }

        const btn = document.getElementById('btn-trigger-analysis');
        btn.disabled = true;
        btn.innerHTML = `<i class="fa-solid fa-circle-notch fa-spin me-2"></i>Analyzing...`;

        // Reset step animations
        for (let i = 1; i <= 7; i++) {
            const stepEl = document.getElementById(`step-${i}`);
            stepEl.className = 'step-item';
            stepEl.querySelector('.step-spinner').classList.add('d-none');
            stepEl.querySelector('.step-check').classList.add('d-none');
        }
        document.getElementById('analysis-complete-banner').classList.add('d-none');

        // Animate simulated steps progression while API call runs
        let currentStep = 1;
        const stepInterval = setInterval(() => {
            if (currentStep <= 7) {
                const stepEl = document.getElementById(`step-${currentStep}`);
                stepEl.classList.add('active');
                stepEl.querySelector('.step-spinner').classList.remove('d-none');

                if (currentStep > 1) {
                    const prevEl = document.getElementById(`step-${currentStep - 1}`);
                    prevEl.classList.remove('active');
                    prevEl.classList.add('completed');
                    prevEl.querySelector('.step-spinner').classList.add('d-none');
                    prevEl.querySelector('.step-check').classList.remove('d-none');
                }
                currentStep++;
            }
        }, 500);

        try {
            const res = await fetch(`/api/analyze/${App.currentDocId}`, { method: 'POST' });
            const data = await res.json();
            clearInterval(stepInterval);

            // Complete all 7 steps UI
            for (let i = 1; i <= 7; i++) {
                const stepEl = document.getElementById(`step-${i}`);
                stepEl.className = 'step-item completed';
                stepEl.querySelector('.step-spinner').classList.add('d-none');
                stepEl.querySelector('.step-check').classList.remove('d-none');
            }

            btn.disabled = false;
            btn.innerHTML = `<i class="fa-solid fa-rotate-right me-2"></i>Re-Analyze Document`;

            if (res.ok) {
                App.showToast(data.message, 'success');
                document.getElementById('analysis-complete-banner').classList.remove('d-none');
                App.loadDashboardData();
            } else {
                App.showToast(data.error || 'Analysis failed', 'danger');
            }

        } catch (err) {
            clearInterval(stepInterval);
            btn.disabled = false;
            btn.innerHTML = `<i class="fa-solid fa-play me-2"></i>Analyze Document`;
            App.showToast('Error during NLP processing', 'danger');
        }
    }
};

document.addEventListener('DOMContentLoaded', () => {
    UploadManager.init();
});
