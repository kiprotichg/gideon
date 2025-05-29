let currentStep = 1;
let userLocation = null;

// Initialize the form
document.addEventListener('DOMContentLoaded', function() {
    getLocation();
    updateProgress();
});

// Get user's location
function getLocation() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            position => {
                userLocation = {
                    lat: position.coords.latitude,
                    lng: position.coords.longitude
                };
                document.getElementById('currentLocation').textContent = 
                    `Latitude: ${userLocation.lat.toFixed(4)}, Longitude: ${userLocation.lng.toFixed(4)}`;
                initMap();
            },
            error => {
                document.getElementById('currentLocation').textContent = 
                    'Error getting location. Please enter address manually.';
            }
        );
    }
}

// Navigation functions
function nextStep(step) {
    if (!validateStep(step)) {
        return;
    }
    
    document.getElementById(`step${step}`).classList.remove('active');
    document.getElementById(`step${step + 1}`).classList.add('active');
    currentStep = step + 1;
    updateProgress();
}

function prevStep(step) {
    document.getElementById(`step${step}`).classList.remove('active');
    document.getElementById(`step${step - 1}`).classList.add('active');
    currentStep = step - 1;
    updateProgress();
}

// Form validation functions
function validateStep(step) {
    switch(step) {
        case 1:
            return validatePersonalInfo();
        case 2:
            return validateIncidentDetails();
        default:
            return true;
    }
}

function validatePersonalInfo() {
    const name = document.getElementById('name').value;
    const phone = document.getElementById('phone').value;
    const email = document.getElementById('email').value;

    if (!name || !phone || !email) {
        alert('Please fill in all personal information fields');
        return false;
    }
    
    // Basic email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
        alert('Please enter a valid email address');
        return false;
    }
    
    // Basic phone validation
    const phoneRegex = /^\d{10}$/;
    if (!phoneRegex.test(phone.replace(/\D/g, ''))) {
        alert('Please enter a valid 10-digit phone number');
        return false;
    }
    
    return true;
}

function validateIncidentDetails() {
    const type = document.getElementById('incidentType').value;
    const description = document.getElementById('description').value;

    if (!type || !description) {
        alert('Please fill in all incident details');
        return false;
    }

    if (description.length < 20) {
        alert('Please provide a more detailed description (at least 20 characters)');
        return false;
    }

    return true;
}

// Update progress bar
function updateProgress() {
    const progress = ((currentStep - 1) / 3) * 100;
    document.getElementById('progress').style.width = `${progress}%`;
}

// Submit report
function submitReport() {
    const address = document.getElementById('address').value;
    if (!address) {
        alert('Please enter the incident address');
        return;
    }

    // Collect all form data
    const reportData = {
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
            address: address,
            coordinates: userLocation
        },
        timestamp: new Date().toISOString()
    };

    // Simulate sending report to server
    simulateReportSubmission(reportData);
}

function simulateReportSubmission(reportData) {
    // Show loading state
    const submitButton = document.querySelector('#step3 .btn:last-child');
    submitButton.disabled = true;
    submitButton.textContent = 'Submitting...';

    // Simulate API call delay
    setTimeout(() => {
        const reportId = generateReportId();
        const nearestStation = findNearestPoliceStation(reportData.location);
        
        document.getElementById('reportId').textContent = reportId;
        document.getElementById('policeStation').textContent = nearestStation.name;
        document.getElementById('responseTime').textContent = '5-10 minutes';

        document.getElementById(`step${currentStep}`).classList.remove('active');
        document.getElementById('confirmation').classList.add('active');

        // Simulate sending notification to police station
        simulatePoliceNotification(reportId, reportData);
        
        // Reset button state
        submitButton.disabled = false;
        submitButton.textContent = 'Submit Report';
    }, 2000);
}

function generateReportId() {
    const timestamp = Date.now().toString().slice(-6);
    const random = Math.floor(Math.random() * 1000).toString().padStart(3, '0');
    return `INC${timestamp}${random}`;
}

function findNearestPoliceStation(location) {
    // In a real application, this would query a database of police stations
    // and calculate the nearest one based on user's location
    return {
        name: 'Central Police Station',
        address: '123 Main Street',
        phone: '911',
        distance: '1.2 km'
    };
}

function simulatePoliceNotification(reportId, reportData) {
    // In a real application, this would send a notification to the police station's system
    console.log(`Police notification sent for report ${reportId}`, reportData);
}

function resetForm() {
    // Reset form to initial state
    document.getElementById('confirmation').classList.remove('active');
    document.getElementById('step1').classList.add('active');
    currentStep = 1;
    updateProgress();
    
    // Clear all input fields
    document.querySelectorAll('input, textarea, select').forEach(element => {
        element.value = '';
    });
    
    // Reset location
    document.getElementById('currentLocation').textContent = 'Detecting location...';
    getLocation();
}

// Map initialization (would require Google Maps API in real implementation)
function initMap() {
    // In a real application, this would initialize a map centered on the user's location
    console.log('Map initialized at:', userLocation);
}