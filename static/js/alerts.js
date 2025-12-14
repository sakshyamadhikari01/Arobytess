class AlertSystem {
    constructor() {
        this.baseUrl = '/api';
        this.init();
    }

    init() {
        this.loadRecentAlerts();
        this.setupFormHandlers();
    }

    async registerForAlerts(formData) {
        try {
            // Remove location from formData as it's auto-detected
            const { location, ...dataWithoutLocation } = formData;
            
            const response = await fetch(`${this.baseUrl}/register-alerts`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(dataWithoutLocation)
            });

            const result = await response.json();
            
            if (result.success) {
                this.showNotification('Successfully registered for SMS disease alerts! Location auto-detected.', 'success');
                return result;
            } else {
                throw new Error(result.message || 'Registration failed');
            }
        } catch (error) {
            this.showNotification(`Registration failed: ${error.message}`, 'error');
            throw error;
        }
    }

    async reportDisease(reportData) {
        try {
            // Remove location from reportData as it's auto-detected
            const { location, ...dataWithoutLocation } = reportData;
            
            const response = await fetch(`${this.baseUrl}/report-disease`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(dataWithoutLocation)
            });

            const result = await response.json();
            
            if (result.success) {
                this.showNotification(`Disease report submitted! Location auto-detected. ${result.notified_farmers} farmers notified via SMS.`, 'success');
                return result;
            } else {
                throw new Error(result.message || 'Report submission failed');
            }
        } catch (error) {
            this.showNotification(`Report failed: ${error.message}`, 'error');
            throw error;
        }
    }

    async loadRecentAlerts(location = null) {
        try {
            const url = location ? 
                `${this.baseUrl}/recent-alerts?location=${encodeURIComponent(location)}` : 
                `${this.baseUrl}/recent-alerts`;
            
            const response = await fetch(url);
            const result = await response.json();
            
            if (result.success) {
                this.displayRecentAlerts(result.alerts);
            }
        } catch (error) {
            console.error('Failed to load recent alerts:', error);
        }
    }

    displayRecentAlerts(alerts) {
        const container = document.querySelector('.recent-alerts');
        if (!container) return;

        const alertsHtml = alerts.map(alert => `
            <div class="alert-item">
                <div class="alert-info">
                    <h4>${alert.diseaseName} in ${alert.cropType}</h4>
                    <p>Detected in ${alert.location} - ${alert.description || 'Take immediate preventive measures'}</p>
                </div>
                <div class="alert-time">${this.formatTime(alert.reportedAt)}</div>
            </div>
        `).join('');

        container.innerHTML = `
            <h3 style="color: var(--white); margin-bottom: 20px;">Recent Alerts in Your Area</h3>
            ${alertsHtml || '<p style="color: rgba(255,255,255,0.7);">No recent alerts in your area.</p>'}
        `;
    }

    setupFormHandlers() {
        // Alert registration form
        const alertForm = document.getElementById('alertRegistrationForm');
        if (alertForm) {
            alertForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                
                const formData = {
                    farmerName: document.getElementById('farmerName').value,
                    phoneNumber: document.getElementById('phoneNumber').value,
                    cropTypes: document.getElementById('cropTypes').value,
                    alertRadius: parseInt(document.getElementById('alertRadius').value)
                };

                // Validate phone number
                if (!this.validatePhoneNumber(formData.phoneNumber)) {
                    this.showNotification('Please enter a valid phone number', 'error');
                    return;
                }

                try {
                    await this.registerForAlerts(formData);
                    alertForm.reset();
                } catch (error) {
                    // Error already handled in registerForAlerts
                }
            });
        }

        // Disease report form (if exists)
        const reportForm = document.getElementById('diseaseReportForm');
        if (reportForm) {
            reportForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                
                const reportData = {
                    diseaseName: document.getElementById('diseaseName').value,
                    cropType: document.getElementById('reportCropType').value,
                    severity: document.getElementById('severity').value,
                    description: document.getElementById('description').value,
                    reporterPhone: document.getElementById('reporterPhone').value
                };

                try {
                    await this.reportDisease(reportData);
                    reportForm.reset();
                } catch (error) {
                    // Error already handled in reportDisease
                }
            });
        }
    }

    validatePhoneNumber(phone) {
        // Remove spaces and dashes
        const cleanPhone = phone.replace(/[-\s]/g, '');
        // Check if it's a valid format (10-15 digits, optionally starting with +)
        const phoneRegex = /^\+?[0-9]{10,15}$/;
        return phoneRegex.test(cleanPhone);
    }

    formatTime(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const diffMs = now - date;
        const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
        const diffDays = Math.floor(diffHours / 24);

        if (diffHours < 1) {
            return 'Just now';
        } else if (diffHours < 24) {
            return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
        } else if (diffDays < 7) {
            return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
        } else {
            return date.toLocaleDateString();
        }
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <span>${message}</span>
            <button onclick="this.parentElement.remove()">×</button>
        `;

        // Add styles if not already present
        if (!document.querySelector('#notification-styles')) {
            const styles = document.createElement('style');
            styles.id = 'notification-styles';
            styles.textContent = `
                .notification {
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    padding: 15px 20px;
                    border-radius: 8px;
                    color: white;
                    font-weight: 500;
                    z-index: 10000;
                    display: flex;
                    align-items: center;
                    gap: 10px;
                    max-width: 400px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                    animation: slideIn 0.3s ease-out;
                }
                .notification-success { background: #28a745; }
                .notification-error { background: #dc3545; }
                .notification-info { background: #17a2b8; }
                .notification button {
                    background: none;
                    border: none;
                    color: white;
                    font-size: 18px;
                    cursor: pointer;
                    padding: 0;
                    width: 20px;
                    height: 20px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }
                @keyframes slideIn {
                    from { transform: translateX(100%); opacity: 0; }
                    to { transform: translateX(0); opacity: 1; }
                }
            `;
            document.head.appendChild(styles);
        }

        document.body.appendChild(notification);

        // Auto remove after 5 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 5000);
    }
}

// Initialize alert system when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.alertSystem = new AlertSystem();
});

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AlertSystem;
}