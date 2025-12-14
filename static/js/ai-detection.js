/*
 * Plant Disease Detection Module
 * Handles image upload, camera capture, and AI analysis
 */

// DOM element references
var tabButtons = document.querySelectorAll('.tab-btn');
var uploadTabContent = document.getElementById('upload-tab');
var cameraTabContent = document.getElementById('camera-tab');

// Tab switching functionality
tabButtons.forEach(function(btn) {
    btn.addEventListener('click', function() {
        // Remove active state from all tabs
        tabButtons.forEach(function(b) { 
            b.classList.remove('active'); 
        });
        btn.classList.add('active');
        
        // Show appropriate content
        if (btn.dataset.tab === 'upload') {
            uploadTabContent.classList.add('active');
            cameraTabContent.classList.remove('active');
            stopCameraStream();
        } else {
            cameraTabContent.classList.add('active');
            uploadTabContent.classList.remove('active');
        }
    });
});

// File upload elements
var dropZone = document.getElementById('uploadArea');
var fileSelector = document.getElementById('fileInput');
var previewContainer = document.getElementById('previewSection');
var previewImg = document.getElementById('previewImage');

// Store current image data
var selectedImageData = null;

// Click to upload
dropZone.addEventListener('click', function() { 
    fileSelector.click(); 
});

// Drag and drop handlers
dropZone.addEventListener('dragover', function(e) {
    e.preventDefault();
    dropZone.classList.add('dragover');
});

dropZone.addEventListener('dragleave', function() {
    dropZone.classList.remove('dragover');
});

dropZone.addEventListener('drop', function(e) {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    
    var droppedFile = e.dataTransfer.files[0];
    if (droppedFile && droppedFile.type.startsWith('image/')) {
        processImageFile(droppedFile);
    }
});

// File input change handler
fileSelector.addEventListener('change', function(e) {
    var selectedFile = e.target.files[0];
    if (selectedFile) {
        processImageFile(selectedFile);
    }
});

// Process uploaded image file
function processImageFile(file) {
    var reader = new FileReader();
    
    reader.onload = function(e) {
        selectedImageData = e.target.result;
        previewImg.src = selectedImageData;
        previewContainer.style.display = 'block';
        document.getElementById('resultCard').style.display = 'none';
    };
    
    reader.readAsDataURL(file);
}

// Camera elements
var videoFeed = document.getElementById('cameraFeed');
var captureCanvas = document.getElementById('cameraCanvas');
var startCamBtn = document.getElementById('startCamera');
var capturePhotoBtn = document.getElementById('captureBtn');
var flipCamBtn = document.getElementById('switchCamera');

// Camera state
var cameraStream = null;
var cameraDirection = 'environment'; // back camera by default
var cameraActive = false;

// Camera control event listeners
startCamBtn.addEventListener('click', toggleCamera);
capturePhotoBtn.addEventListener('click', takePhoto);
flipCamBtn.addEventListener('click', flipCamera);

// Toggle camera on/off
function toggleCamera() {
    if (cameraActive) {
        stopCameraStream();
    } else {
        initializeCamera();
    }
}

// Start camera stream
async function initializeCamera() {
    try {
        cameraStream = await navigator.mediaDevices.getUserMedia({
            video: { 
                facingMode: cameraDirection, 
                width: { ideal: 640 }, 
                height: { ideal: 480 } 
            }
        });
        
        videoFeed.srcObject = cameraStream;
        startCamBtn.textContent = 'Stop Camera';
        capturePhotoBtn.disabled = false;
        cameraActive = true;
        
    } catch (err) {
        alert('Camera access denied: ' + err.message);
    }
}

// Stop camera stream
function stopCameraStream() {
    if (cameraStream) {
        cameraStream.getTracks().forEach(function(track) { 
            track.stop(); 
        });
        cameraStream = null;
    }
    videoFeed.srcObject = null;
    startCamBtn.textContent = 'Start Camera';
    capturePhotoBtn.disabled = true;
    cameraActive = false;
}

// Switch between front and back camera
async function flipCamera() {
    cameraDirection = (cameraDirection === 'environment') ? 'user' : 'environment';
    if (cameraStream) {
        await initializeCamera();
    }
}

// Capture photo from video feed
function takePhoto() {
    captureCanvas.width = videoFeed.videoWidth;
    captureCanvas.height = videoFeed.videoHeight;
    
    var ctx = captureCanvas.getContext('2d');
    ctx.drawImage(videoFeed, 0, 0);
    
    selectedImageData = captureCanvas.toDataURL('image/jpeg', 0.9);
    previewImg.src = selectedImageData;
    previewContainer.style.display = 'block';
    document.getElementById('resultCard').style.display = 'none';
}

// Analysis elements
var analyzeButton = document.getElementById('analyzeBtn');
var loadingScreen = document.getElementById('loadingOverlay');
var resultsCard = document.getElementById('resultCard');

analyzeButton.addEventListener('click', runAnalysis);

// Send image to API for analysis
async function runAnalysis() {
    if (!selectedImageData) {
        alert('Please upload or capture an image first');
        return;
    }
    
    loadingScreen.style.display = 'flex';
    
    try {
        var response = await fetch('/api/predict', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ image: selectedImageData })
        });
        
        if (!response.ok) {
            throw new Error('Analysis request failed');
        }
        
        var analysisResult = await response.json();
        showResults(analysisResult);
        
    } catch (err) {
        alert('Analysis error: ' + err.message);
    } finally {
        loadingScreen.style.display = 'none';
    }
}

// Display analysis results
function showResults(result) {
    resultsCard.style.display = 'block';
    
    var statusDisplay = document.getElementById('resultStatus');
    var detailsSection = document.getElementById('resultDetails');
    
    var plantHealthy = result.prediction === 'healthy';
    
    // Update status display
    statusDisplay.className = 'result-status ' + (plantHealthy ? 'healthy' : 'diseased');
    statusDisplay.innerHTML = plantHealthy 
        ? 'Healthy Plant' 
        : 'Disease Detected';
    
    // Show appropriate recommendations
    if (plantHealthy) {
        detailsSection.innerHTML = '<h4>Good News!</h4>' +
            '<p>Your plant looks healthy. Keep up the good care and continue monitoring regularly.</p>';
    } else {
        detailsSection.innerHTML = '<h4>Recommended Fertilizers</h4>' +
            '<div class="fertilizer-recommendations">' +
                '<div class="fertilizer-item">' +
                    '<strong>NPK 20-20-20</strong><br>' +
                    '<span>Available at: Krishak Krishi Kendra, Nepal Fertilizer Suppliers</span>' +
                '</div>' +
                '<div class="fertilizer-item">' +
                    '<strong>Urea (46-0-0)</strong><br>' +
                    '<span>Available at: Shree Ganesh Agro Center, Himalayan Agro Traders</span>' +
                '</div>' +
                '<div class="fertilizer-item">' +
                    '<strong>DAP (18-46-0)</strong><br>' +
                    '<span>Available at: Green Valley Fertilizers, Siddhartha Krishi Sewa</span>' +
                '</div>' +
            '</div>' +
            '<h4>Preventive Measures</h4>' +
            '<ul class="preventive-measures">' +
                '<li>Isolate infected plants from healthy ones immediately</li>' +
                '<li>Remove and destroy infected leaves and plant parts</li>' +
                '<li>Apply fungicide (Mancozeb or Copper-based) as per instructions</li>' +
                '<li>Ensure proper spacing between plants for air circulation</li>' +
                '<li>Avoid overhead watering to reduce leaf wetness</li>' +
                '<li>Practice crop rotation to prevent soil-borne diseases</li>' +
                '<li>Use disease-resistant plant varieties when possible</li>' +
                '<li>Maintain proper soil drainage to prevent root diseases</li>' +
                '<li>Sanitize gardening tools after use on infected plants</li>' +
                '<li>Consult a local agricultural expert if symptoms persist</li>' +
            '</ul>';
    }
    
    // Scroll to results
    resultsCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

// Mobile menu functionality
var menuBtn = document.getElementById('menuToggle');
var sideMenu = document.getElementById('sliderMenu');
var closeMenuBtn = document.getElementById('sliderClose');
var menuOverlay = document.getElementById('sliderOverlay');

if (menuBtn) {
    menuBtn.addEventListener('click', function() {
        sideMenu.classList.add('active');
        menuOverlay.classList.add('active');
    });
}

if (closeMenuBtn) {
    closeMenuBtn.addEventListener('click', closeSideMenu);
}

if (menuOverlay) {
    menuOverlay.addEventListener('click', closeSideMenu);
}

function closeSideMenu() {
    sideMenu.classList.remove('active');
    menuOverlay.classList.remove('active');
}
