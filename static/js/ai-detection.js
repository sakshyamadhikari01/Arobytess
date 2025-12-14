// Tab switching
const tabBtns = document.querySelectorAll('.tab-btn');
const uploadTab = document.getElementById('upload-tab');
const cameraTab = document.getElementById('camera-tab');

tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        tabBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        
        if (btn.dataset.tab === 'upload') {
            uploadTab.classList.add('active');
            cameraTab.classList.remove('active');
            stopCamera();
        } else {
            cameraTab.classList.add('active');
            uploadTab.classList.remove('active');
        }
    });
});

// File upload
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const previewSection = document.getElementById('previewSection');
const previewImage = document.getElementById('previewImage');

uploadArea.addEventListener('click', () => fileInput.click());

uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.classList.add('dragover');
});

uploadArea.addEventListener('dragleave', () => {
    uploadArea.classList.remove('dragover');
});

uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith('image/')) {
        handleImageFile(file);
    }
});

fileInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) handleImageFile(file);
});

let currentImageData = null;

function handleImageFile(file) {
    const reader = new FileReader();
    reader.onload = (e) => {
        currentImageData = e.target.result;
        previewImage.src = currentImageData;
        previewSection.style.display = 'block';
        document.getElementById('resultCard').style.display = 'none';
    };
    reader.readAsDataURL(file);
}

// Camera functionality
const cameraFeed = document.getElementById('cameraFeed');
const cameraCanvas = document.getElementById('cameraCanvas');
const startCameraBtn = document.getElementById('startCamera');
const captureBtn = document.getElementById('captureBtn');
const switchCameraBtn = document.getElementById('switchCamera');

let stream = null;
let facingMode = 'environment';

startCameraBtn.addEventListener('click', startCamera);
captureBtn.addEventListener('click', captureImage);
switchCameraBtn.addEventListener('click', switchCamera);

async function startCamera() {
    try {
        if (stream) stopCamera();
        
        stream = await navigator.mediaDevices.getUserMedia({
            video: { facingMode: facingMode, width: { ideal: 640 }, height: { ideal: 480 } }
        });
        
        cameraFeed.srcObject = stream;
        startCameraBtn.textContent = 'Stop Camera';
        startCameraBtn.onclick = stopCamera;
        captureBtn.disabled = false;
    } catch (err) {
        alert('Could not access camera: ' + err.message);
    }
}

function stopCamera() {
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
        stream = null;
    }
    cameraFeed.srcObject = null;
    startCameraBtn.textContent = 'Start Camera';
    startCameraBtn.onclick = startCamera;
    captureBtn.disabled = true;
}

async function switchCamera() {
    facingMode = facingMode === 'environment' ? 'user' : 'environment';
    if (stream) await startCamera();
}

function captureImage() {
    cameraCanvas.width = cameraFeed.videoWidth;
    cameraCanvas.height = cameraFeed.videoHeight;
    const ctx = cameraCanvas.getContext('2d');
    ctx.drawImage(cameraFeed, 0, 0);
    
    currentImageData = cameraCanvas.toDataURL('image/jpeg', 0.9);
    previewImage.src = currentImageData;
    previewSection.style.display = 'block';
    document.getElementById('resultCard').style.display = 'none';
}

// Analysis
const analyzeBtn = document.getElementById('analyzeBtn');
const loadingOverlay = document.getElementById('loadingOverlay');
const resultCard = document.getElementById('resultCard');

analyzeBtn.addEventListener('click', analyzeImage);

async function analyzeImage() {
    if (!currentImageData) {
        alert('Please select or capture an image first');
        return;
    }
    
    loadingOverlay.style.display = 'flex';
    
    try {
        const response = await fetch('/api/predict', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ image: currentImageData })
        });
        
        if (!response.ok) throw new Error('Analysis failed');
        
        const result = await response.json();
        displayResult(result);
    } catch (err) {
        alert('Error analyzing image: ' + err.message);
    } finally {
        loadingOverlay.style.display = 'none';
    }
}

function displayResult(result) {
    resultCard.style.display = 'block';
    
    const statusEl = document.getElementById('resultStatus');
    const confidenceFill = document.getElementById('confidenceFill');
    const confidenceValue = document.getElementById('confidenceValue');
    const detailsEl = document.getElementById('resultDetails');
    
    const isHealthy = result.prediction === 'healthy';
    const confidence = Math.round(result.confidence * 100);
    
    statusEl.className = 'result-status ' + (isHealthy ? 'healthy' : 'diseased');
    statusEl.innerHTML = isHealthy 
        ? '✅ Healthy Plant' 
        : '⚠️ Disease Detected';
    
    confidenceFill.style.width = confidence + '%';
    confidenceValue.textContent = confidence + '%';
    
    detailsEl.innerHTML = isHealthy
        ? `<h4>Great News!</h4><p>Your plant appears to be healthy. Continue with regular care and monitoring.</p>`
        : `<h4>Recommendations</h4>
           <p>• Isolate the affected plant from others<br>
           • Remove infected leaves carefully<br>
           • Consider using appropriate fungicide/pesticide<br>
           • Ensure proper drainage and air circulation<br>
           • Consult a local agricultural expert if condition persists</p>`;
    
    resultCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

// Menu functionality
const menuToggle = document.getElementById('menuToggle');
const sliderMenu = document.getElementById('sliderMenu');
const sliderClose = document.getElementById('sliderClose');
const sliderOverlay = document.getElementById('sliderOverlay');

menuToggle.addEventListener('click', () => {
    sliderMenu.classList.add('active');
    sliderOverlay.classList.add('active');
});

sliderClose.addEventListener('click', closeMenu);
sliderOverlay.addEventListener('click', closeMenu);

function closeMenu() {
    sliderMenu.classList.remove('active');
    sliderOverlay.classList.remove('active');
}
