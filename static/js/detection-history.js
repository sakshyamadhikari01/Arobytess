/*
 * Detection History Module
 * Displays past plant scans with side-by-side layout
 */

var historyList = document.getElementById('historyList');
var emptyState = document.getElementById('emptyState');
var scanCount = document.getElementById('scanCount');
var detailPanel = document.getElementById('detailPanel');
var detailPlaceholder = document.getElementById('detailPlaceholder');
var detailContent = document.getElementById('detailContent');

var selectedRecordId = null;

// Get current user
function getCurrentUser() {
    var userData = localStorage.getItem('currentUser');
    return userData ? JSON.parse(userData) : null;
}

// Format date for display
function formatDate(isoString) {
    var date = new Date(isoString);
    var options = { 
        month: 'short', 
        day: 'numeric', 
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    };
    return date.toLocaleDateString('en-US', options);
}

// Load detection history
async function loadHistory() {
    var user = getCurrentUser();
    
    if (!user) {
        showEmptyState('Please login to view your history');
        return;
    }
    
    try {
        var response = await fetch('/api/detection-history/' + user.id);
        
        if (!response.ok) {
            throw new Error('Failed to load history');
        }
        
        var history = await response.json();
        renderHistory(history);
        
    } catch (err) {
        console.error('Error loading history:', err);
        showEmptyState('Failed to load history');
    }
}

// Render history list
function renderHistory(history) {
    if (!history || history.length === 0) {
        showEmptyState();
        return;
    }
    
    emptyState.style.display = 'none';
    scanCount.textContent = history.length + ' scan' + (history.length !== 1 ? 's' : '');
    
    var html = '';
    history.forEach(function(record) {
        var statusClass = record.prediction === 'healthy' ? 'healthy' : 'diseased';
        var statusText = record.prediction === 'healthy' ? 'Healthy' : 'Diseased';
        var confidence = Math.round(record.confidence * 100);
        
        html += '<div class="history-item" data-id="' + record.id + '" onclick="selectRecord(' + record.id + ')">' +
            '<img class="history-item-thumb" src="' + record.image + '" alt="Scan">' +
            '<div class="history-item-info">' +
                '<div class="history-item-status ' + statusClass + '">' + statusText + '</div>' +
                '<div class="history-item-date">' + formatDate(record.timestamp) + '</div>' +
                '<div class="history-item-confidence">' + confidence + '% confidence</div>' +
            '</div>' +
        '</div>';
    });
    
    historyList.innerHTML = html + emptyState.outerHTML;
    emptyState = document.getElementById('emptyState');
    emptyState.style.display = 'none';
    
    // Store history data for detail view
    window.historyData = history;
}

// Show empty state
function showEmptyState(message) {
    emptyState.style.display = 'flex';
    if (message) {
        emptyState.querySelector('p').textContent = message;
    }
    scanCount.textContent = '0 scans';
}

// Select a record to view details
function selectRecord(recordId) {
    selectedRecordId = recordId;
    
    // Update active state in list
    var items = document.querySelectorAll('.history-item');
    items.forEach(function(item) {
        item.classList.remove('active');
        if (parseInt(item.dataset.id) === recordId) {
            item.classList.add('active');
        }
    });
    
    // Find record data
    var record = window.historyData.find(function(r) {
        return r.id === recordId;
    });
    
    if (!record) return;
    
    // Show detail content
    detailPlaceholder.style.display = 'none';
    detailContent.style.display = 'flex';
    
    // Populate details
    document.getElementById('detailImage').src = record.image;
    
    var statusEl = document.getElementById('detailStatus');
    var isHealthy = record.prediction === 'healthy';
    statusEl.className = 'detail-status ' + (isHealthy ? 'healthy' : 'diseased');
    statusEl.textContent = isHealthy ? 'Healthy Plant' : 'Disease Detected';
    
    document.getElementById('detailDate').textContent = formatDate(record.timestamp);
    document.getElementById('detailConfidence').textContent = Math.round(record.confidence * 100) + '% confidence';
}

// Delete selected record
async function deleteSelectedRecord() {
    if (!selectedRecordId) return;
    
    if (!confirm('Delete this scan record?')) return;
    
    try {
        var response = await fetch('/api/detection-history/' + selectedRecordId, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            throw new Error('Delete failed');
        }
        
        // Reset detail view
        selectedRecordId = null;
        detailPlaceholder.style.display = 'flex';
        detailContent.style.display = 'none';
        
        // Reload history
        loadHistory();
        
    } catch (err) {
        alert('Failed to delete record');
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', loadHistory);
