// handles alert signups and disease reports

var AlertSystem = (function() {
    
    var apiEndpoint = '/api';
    
    // Initialize the alert system
    function init() {
        fetchRecentAlerts();
        attachFormListeners();
    }
    
    // Register farmer for SMS alerts
    async function registerFarmer(formData) {
        try {
            // Location is auto-detected, remove from payload
            var payload = {
                farmerName: formData.farmerName,
                phoneNumber: formData.phoneNumber,
                cropTypes: formData.cropTypes,
                alertRadius: formData.alertRadius
            };
            
            var response = await fetch(apiEndpoint + '/register-alerts', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            var result = await response.json();
            
            if (result.success) {
                displayNotification('Registration successful! You will receive SMS alerts for your area.', 'success');
                return result;
            } else {
                throw new Error(result.message || 'Registration unsuccessful');
            }
        } catch (error) {
            displayNotification('Registration failed: ' + error.message, 'error');
            throw error;
        }
    }

    // Submit disease outbreak report
    async function submitDiseaseReport(reportData) {
        try {
            var payload = {
                diseaseName: reportData.diseaseName,
                cropType: reportData.cropType,
                severity: reportData.severity,
                description: reportData.description,
                location: 'Bharatpur'
            };
            
            var response = await fetch(apiEndpoint + '/report-disease', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            var result = await response.json();
            
            if (result.success) {
                var msg = 'Disease report submitted! All farmers in the community have been alerted about this outbreak.';
                displayNotification(msg, 'success');
                return result;
            } else {
                throw new Error(result.message || 'Report submission failed');
            }
        } catch (error) {
            displayNotification('Report failed: ' + error.message, 'error');
            throw error;
        }
    }

    // Fetch recent alerts for display
    async function fetchRecentAlerts(location) {
        try {
            var url = apiEndpoint + '/recent-alerts';
            if (location) {
                url += '?location=' + encodeURIComponent(location);
            }
            
            var response = await fetch(url);
            var result = await response.json();
            
            if (result.success) {
                renderAlertsList(result.alerts);
            }
        } catch (error) {
            console.error('Could not load alerts:', error);
        }
    }

    // Render alerts in the UI
    function renderAlertsList(alerts) {
        var container = document.querySelector('.recent-alerts');
        if (!container) return;

        var html = '<h3 style="color: var(--white); margin-bottom: 20px;">What\'s been reported lately</h3>';
        
        if (alerts.length === 0) {
            html += '<p style="color: rgba(255,255,255,0.7);">No recent reports in the community.</p>';
        } else {
            alerts.forEach(function(alert) {
                html += '<div class="alert-item">' +
                    '<div class="alert-info">' +
                        '<h4>' + alert.diseaseName + ' on ' + alert.cropType + '</h4>' +
                        '<p>Bharatpur - ' + (alert.description || 'Take preventive measures') + '</p>' +
                    '</div>' +
                    '<div class="alert-time">' + formatTimeAgo(alert.reportedAt) + '</div>' +
                '</div>';
            });
        }

        container.innerHTML = html;
    }

    // Attach event listeners to forms
    function attachFormListeners() {
        // Registration form
        var regForm = document.getElementById('alertRegistrationForm');
        if (regForm) {
            regForm.addEventListener('submit', async function(e) {
                e.preventDefault();
                
                var data = {
                    farmerName: document.getElementById('farmerName').value,
                    phoneNumber: document.getElementById('phoneNumber').value,
                    cropTypes: document.getElementById('cropTypes').value,
                    alertRadius: parseInt(document.getElementById('alertRadius').value)
                };

                if (!isValidPhone(data.phoneNumber)) {
                    displayNotification('Please enter a valid phone number', 'error');
                    return;
                }

                try {
                    await registerFarmer(data);
                    regForm.reset();
                } catch (err) {
                    // Error handled in registerFarmer
                }
            });
        }

        // Disease report form
        var reportForm = document.getElementById('diseaseReportForm');
        if (reportForm) {
            reportForm.addEventListener('submit', async function(e) {
                e.preventDefault();
                
                var data = {
                    diseaseName: document.getElementById('diseaseName').value,
                    cropType: document.getElementById('reportCropType').value,
                    severity: document.getElementById('severity').value,
                    description: document.getElementById('description').value
                };

                try {
                    await submitDiseaseReport(data);
                    reportForm.reset();
                    // Close modal after successful submission
                    if (typeof closeReportModal === 'function') {
                        closeReportModal();
                    }
                } catch (err) {
                    // Error handled in submitDiseaseReport
                }
            });
        }
    }

    // Validate phone number format
    function isValidPhone(phone) {
        var cleaned = phone.replace(/[-\s]/g, '');
        var pattern = /^\+?[0-9]{10,15}$/;
        return pattern.test(cleaned);
    }

    // Format timestamp to relative time
    function formatTimeAgo(timestamp) {
        var date = new Date(timestamp);
        var now = new Date();
        var diffMs = now - date;
        var diffHours = Math.floor(diffMs / (1000 * 60 * 60));
        var diffDays = Math.floor(diffHours / 24);

        if (diffHours < 1) {
            return 'Just now';
        } else if (diffHours < 24) {
            return diffHours + ' hour' + (diffHours > 1 ? 's' : '') + ' ago';
        } else if (diffDays < 7) {
            return diffDays + ' day' + (diffDays > 1 ? 's' : '') + ' ago';
        } else {
            return date.toLocaleDateString();
        }
    }

    // Display notification toast
    function displayNotification(message, type) {
        type = type || 'info';
        
        var toast = document.createElement('div');
        toast.className = 'toast-notification toast-' + type;
        toast.innerHTML = '<span>' + message + '</span>' +
            '<button onclick="this.parentElement.remove()">×</button>';

        // Add styles if not present
        if (!document.querySelector('#toast-styles')) {
            var styles = document.createElement('style');
            styles.id = 'toast-styles';
            styles.textContent = 
                '.toast-notification {' +
                    'position: fixed; top: 20px; right: 20px;' +
                    'padding: 15px 20px; border-radius: 8px;' +
                    'color: white; font-weight: 500; z-index: 10000;' +
                    'display: flex; align-items: center; gap: 10px;' +
                    'max-width: 400px; box-shadow: 0 4px 12px rgba(0,0,0,0.3);' +
                    'animation: toastSlide 0.3s ease-out;' +
                '}' +
                '.toast-success { background: #28a745; }' +
                '.toast-error { background: #dc3545; }' +
                '.toast-info { background: #17a2b8; }' +
                '.toast-notification button {' +
                    'background: none; border: none; color: white;' +
                    'font-size: 18px; cursor: pointer; padding: 0;' +
                '}' +
                '@keyframes toastSlide {' +
                    'from { transform: translateX(100%); opacity: 0; }' +
                    'to { transform: translateX(0); opacity: 1; }' +
                '}';
            document.head.appendChild(styles);
        }

        document.body.appendChild(toast);

        // Auto-remove after 5 seconds
        setTimeout(function() {
            if (toast.parentElement) {
                toast.remove();
            }
        }, 5000);
    }

    // Public interface
    return {
        init: init,
        registerFarmer: registerFarmer,
        submitDiseaseReport: submitDiseaseReport,
        fetchRecentAlerts: fetchRecentAlerts
    };
    
})();

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    AlertSystem.init();
});

// Make available globally
window.alertSystem = AlertSystem;
