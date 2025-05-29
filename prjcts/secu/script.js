function toggleForms() {
    const signupForm = document.getElementById('signup-form');
    const loginForm = document.getElementById('login-form');
    const resetPasswordForm = document.getElementById('reset-password-form');

    if (signupForm.style.display === "none") {
        signupForm.style.display = "block";
        loginForm.style.display = "none";
        resetPasswordForm.style.display = "none";
    } else {
        signupForm.style.display = "none";
        loginForm.style.display = "block";
        resetPasswordForm.style.display = "none";
    }
}

function toggleResetPassword() {
    const signupForm = document.getElementById('signup-form');
    const loginForm = document.getElementById('login-form');
    const resetPasswordForm = document.getElementById('reset-password-form');

    signupForm.style.display = "none";
    loginForm.style.display = "none";
    resetPasswordForm.style.display = "block";
}