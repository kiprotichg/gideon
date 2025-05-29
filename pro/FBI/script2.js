// Global variables
let currentStep = 1;
let userLocation = null;
const POLICE_OFFICER_PHONE = "0768542405";

// Initialize when document loads
document.addEventListener('DOMContentLoaded', function() {
    initializeSystem();
});

function initializeSystem() {
    getLocation();
    updateProgress();
    setupEventListeners();
}

// Setup event listeners for all form elements
function setupEventListeners() {
    document.querySelectorAll('.btn').forEach(button => {
        button.addEventListener('click', handleButtonClick);
    });
}

function handleButtonClick(event) {
    const button = event.target;
    if (button.textContent === 'Next') {
        nextStep(currentStep);
    } else if (button.textContent === 'Previous') {
        prevStep(currentStep);
    } else if (button.textContent === 'Submit Report') {
        submitReport();
    } else if (button.textContent === 'Submit New Report') {
        resetForm();
    }
}

// Location handling
function getLocation() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            handleLocationSuccess,
            handleLocationError
        );
    }
}

function handleLocationSuccess(position) {
    userLocation = {
        lat: position.coords.latitude,
        lng: position.coords.longitude
    };
    updateLocationDisplay();
}

function handleLocationError(error) {
    document.getElementById('currentLocation').textContent = 
        'Error getting location. Please enter address manually.';
    console.error('Geolocation error:', error);
}

function updateLocationDisplay() {
    const locationElement = document.getElementById('currentLocation');
    if (locationElement && userLocation) {
        locationElement.textContent = 
            `Latitude: ${userLocation.lat.toFixed(4)}, Longitude: ${userLocation.lng.toFixed(4)}`;
    }
}

// Form navigation
function nextStep(step) {
    if (validateStep(step)) {
        updateFormStep(step, step + 1);
    }
}

function prevStep(step) {
    updateFormStep(step, step - 1);
}

function updateFormStep(currentStep, nextStep) {
    document.getElementById(`step${currentStep}`).classList.remove('active');
    document.getElementById(`step${nextStep}`).classList.add('active');
    currentStep = nextStep;
    updateProgress();
}

// Validation
function validateStep(step) {
    const validators = {
        1: validatePersonalInfo,
        2: validateIncidentDetails,
        3: validateLocation
    };
    return validators[step] ? validators[step]() : true;
}

function validatePersonalInfo() {
    const name = document.getElementById('name').value;
    const phone = document.getElementById('phone').value;
    const email = document.getElementById('email').value;

    if (!name || !phone || !email) {
        showError('Please fill in all personal information fields');
        return false;
    }

    if (!validateEmail(email)) {
        showError('Please enter a valid email address');
        return false;
    }

    if (!validatePhone(phone)) {
        showError('Please enter a valid phone number');
        return false;
    }

    return true;
}

function validateIncidentDetails() {
    const type = document.getElementById('incidentType').value;
    const description = document.getElementById('description').value;

    if (!type || !description) {
        showError('Please fill in all incident details');
        return false;
    }

    if (description.length < 20) {
        showError('Please provide a more detailed description (at least 20 characters)');
        return false;
    }

    return true;
}

function validateLocation() {
    const address = document.getElementById('address').value;
    if (!address) {
        showError('Please enter the incident address');
        return false;
    }
    return true;
}

// Helper validation functions
function validateEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

function validatePhone(phone) {
    return /^\d{10}$/.test(phone.replace(/\D/g, ''));
}

function showError(message) {
    alert(message); // Can be replaced with a more sophisticated error display
}

// Progress bar
function updateProgress() {
    const progress = ((currentStep - 1) / 3) * 100;
    document.getElementById('progress').style.width = `${progress}%`;
}

// Report submission
function submitReport() {
    if (!validateStep(3)) return;

    const reportData = collectFormData();
    sendReport(reportData);
}

function collectFormData() {
    return {
        reportId: generateReportId(),
        personalInfo: {
            name: document.getElementById('name').value,
            phone: document.getElementById('phone').value,
            email: document.getElementById('email').value
        },
        incidentDetails: {
            type: document.getElementById('incidentType').value,
            description: document.getElementById('description').value
        },
        location: {
            address: document.getElementById('address').value,
            coordinates: userLocation
        },
        timestamp: new Date().toISOString()
    };
}

// Police notification system
async function sendReport(reportData) {
    try {
        // Disable submit button and show loading state
        const submitButton = document.querySelector('#step3 .btn:last-child');
        submitButton.disabled = true;
        submitButton.textContent = 'Sending Report...';

        // Send notification to police
        await sendPoliceNotification(reportData);

        // Update UI with success
        showConfirmation(reportData);

        // Reset button state
        submitButton.disabled = false;
        submitButton.textContent = 'Submit Report';
    } catch (error) {
        console.error('Error sending report:', error);
        showError('Failed to send report. Please try again.');
        
        // Reset button state
        submitButton.disabled = false;
        submitButton.textContent = 'Submit Report';
    }
}

async function sendPoliceNotification(reportData) {
    const notificationData = {
        to: POLICE_OFFICER_PHONE,
        message: formatPoliceMessage(reportData),
        priority: 'high'
    };

    // Simulate sending SMS
    await simulateSMSService(notificationData);
    
    // Store notification record
    storeNotificationRecord(reportData.reportId, notificationData);
}

function formatPoliceMessage(reportData) {
    return `
🚨 URGENT: New Incident Report ${reportData.reportId}

Type: ${reportData.incidentDetails.type}
Location: ${reportData.location.address}
${reportData.location.coordinates ? 
    `Coordinates: ${reportData.location.coordinates.lat}, ${reportData.location.coordinates.lng}` : ''}

Reporter: ${reportData.personalInfo.name}
Contact: ${reportData.personalInfo.phone}

Description: ${reportData.incidentDetails.description}

Please respond ASAP.
    `.trim();
}

// Simulate SMS service (replace with actual SMS service integration)
function simulateSMSService(notificationData) {
    return new Promise((resolve) => {
        setTimeout(() => {
            console.log('SMS sent to:', notificationData.to);
            console.log('Message:', notificationData.message);
            resolve({
                status: 'delivered',
                timestamp: new Date().toISOString()
            });
        }, 2000);
    });
}

// Record keeping
function storeNotificationRecord(reportId, notificationData) {
    const record = {
        reportId,
        recipient: notificationData.to,
        message: notificationData.message,
        sentAt: new Date().toISOString(),
        status: 'delivered'
    };
    console.log('Notification record:', record);
    // In real application, save to database
}

function generateReportId() {
    const timestamp = Date.now().toString().slice(-6);
    const random = Math.floor(Math.random() * 1000).toString().padStart(3, '0');
    return `INC${timestamp}${random}`;
}

// UI updates
function showConfirmation(reportData) {
    document.getElementById(`step${currentStep}`).classList.remove('active');
    document.getElementById('confirmation').classList.add('active');
    
    document.getElementById('reportId').textContent = reportData.reportId;
    document.getElementById('policeStation').textContent = 'Central Police Station';
    document.getElementById('responseTime').textContent = '5-10 minutes';
}

// Form reset
function resetForm() {
    // Reset steps
    document.getElementById('confirmation').classList.remove('active');
    document.getElementById('step1').classList.add('active');
    currentStep = 1;
    updateProgress();
    
    // Clear form fields
    document.querySelectorAll('input, textarea, select').forEach(element => {
        element.value = '';
    });
    
    // Reset location
    document.getElementById('currentLocation').textContent = 'Detecting location...';
    getLocation();
}