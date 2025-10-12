// Upload page JavaScript

const uploadBox = document.getElementById('uploadBox');
const uploadContent = document.getElementById('uploadContent');
const uploadProgress = document.getElementById('uploadProgress');
const fileInput = document.getElementById('fileInput');
const progressFill = document.getElementById('progressFill');
const uploadPercent = document.getElementById('uploadPercent');
const fileName = document.getElementById('fileName');
const uploadStatus = document.getElementById('uploadStatus');

function parseJSONSafe(payload) {
    try {
        return payload ? JSON.parse(payload) : null;
    } catch (error) {
        return null;
    }
}

// Click to browse
uploadBox.addEventListener('click', () => {
    fileInput.click();
});

// Drag and drop handlers
uploadBox.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadBox.style.borderColor = 'var(--primary)';
    uploadBox.style.background = 'rgba(0, 168, 255, 0.1)';
});

uploadBox.addEventListener('dragleave', (e) => {
    e.preventDefault();
    uploadBox.style.borderColor = 'var(--border)';
    uploadBox.style.background = '';
});

uploadBox.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadBox.style.borderColor = 'var(--border)';
    uploadBox.style.background = '';
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFileUpload(files[0]);
    }
});

// File input change
fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleFileUpload(e.target.files[0]);
    }
});

function handleFileUpload(file) {
    // Validate file extension
    const allowedExtensions = ['.mp4', '.mkv', '.mov', '.m4v', '.ts', '.m2ts', '.webm'];
    const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
    
    if (!allowedExtensions.includes(fileExtension)) {
        alert(`File type ${fileExtension} is not supported. Allowed: ${allowedExtensions.join(', ')}`);
        return;
    }
    
    // Validate file size (10GB)
    const maxSize = 10 * 1024 * 1024 * 1024;
    if (file.size > maxSize) {
        alert('File size exceeds maximum limit of 10GB');
        return;
    }
    
    // Show progress UI
    uploadContent.style.display = 'none';
    uploadProgress.style.display = 'block';
    fileName.textContent = file.name;
    
    // Upload file
    uploadFile(file);
}

function uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    const xhr = new XMLHttpRequest();
    
    // Progress event
    xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable) {
            const percent = Math.round((e.loaded / e.total) * 100);
            progressFill.style.width = percent + '%';
            uploadPercent.textContent = percent + '%';
        }
    });
    
    // Load event
    xhr.addEventListener('load', () => {
        const response = parseJSONSafe(xhr.responseText);
        const success = xhr.status === 200 && response && response.success;

        if (success) {
            uploadStatus.className = 'upload-status success';
            uploadStatus.textContent = '✓ Upload successful! Processing video...';

            // Redirect to dashboard after 2 seconds
            setTimeout(() => {
                window.location.href = '/dashboard';
            }, 2000);
            return;
        }

        let errorMessage = response && response.error ? response.error : '';

        if (!errorMessage) {
            if (xhr.status === 413) {
                errorMessage = 'Server rejected the upload because the file is too large.';
            } else if (xhr.status === 0) {
                errorMessage = 'Network error while uploading. Please check your connection.';
            } else if (xhr.status >= 500) {
                errorMessage = 'Unexpected server error. Please try again shortly.';
            } else {
                errorMessage = 'Upload failed';
            }
        }

        uploadStatus.className = 'upload-status error';
        uploadStatus.textContent = '✗ Error: ' + errorMessage;

        setTimeout(resetUploadUI, 3000);
    });
    
    // Error event
    xhr.addEventListener('error', () => {
        uploadStatus.className = 'upload-status error';
        uploadStatus.textContent = '✗ Upload failed. Please try again.';
        
        setTimeout(resetUploadUI, 3000);
    });
    
    // Send request
    xhr.open('POST', '/api/upload');
    xhr.send(formData);
}

function resetUploadUI() {
    uploadContent.style.display = 'block';
    uploadProgress.style.display = 'none';
    progressFill.style.width = '0%';
    uploadPercent.textContent = '0%';
    uploadStatus.className = 'upload-status';
    uploadStatus.textContent = '';
    fileInput.value = '';
}

// Keyboard accessibility
uploadBox.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        fileInput.click();
    }
});

// Make upload box focusable
uploadBox.setAttribute('tabindex', '0');
