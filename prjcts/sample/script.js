document.getElementById('signupForm').addEventListener('submit', function(event) {
    event.preventDefault();
    alert('User  registered successfully!');
    document.getElementById('signup').style.display = 'none';
    document.getElementById('login').style.display = 'block';
});

document.getElementById('loginForm').addEventListener('submit', function(event) {
    event.preventDefault();
    alert('Login successful!');
    document.getElementById('login').style.display = 'none';
    document.getElementById('report').style.display = 'block';
});

document.getElementById('reportForm').addEventListener('submit', function(event) {
    event.preventDefault();
    alert('Report submitted successfully!');
    document.getElementById('report').style.display = 'none';
    document.getElementById('successMessage').style.display = 'block';
});

document.getElementById('showLogin').addEventListener('click', function() {
    document.getElementById('signup').style.display = 'none';
    document.getElementById('login').style.display = 'block';
});

document.getElementById('showSignup').addEventListener('click ', function() {
    document.getElementById('login').style.display = 'none';
    document.getElementById('signup').style.display = 'block';
});

document.getElementById('signOut').addEventListener('click', function() {
    document.getElementById('successMessage').style.display = 'none';
    document.getElementById('signup').style.display = 'block';
});