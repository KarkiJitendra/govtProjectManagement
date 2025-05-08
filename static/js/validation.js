// static/js/validation.js

document.addEventListener('DOMContentLoaded', function() {
    // Function to validate name
    function validateName(name) {
        if (!/^[a-zA-Z ]+$/.test(name)) {
            return 'Name must contain only letters and spaces.';
        }
        return '';
    }

    // Function to validate email
    function validateEmail(email) {
        if (!/^\S+@\S+\.\S+$/.test(email)) {
            return 'Enter a valid email address.';
        }
        return '';
    }

    // Function to validate password
    function validatePassword(password) {
        let feedback = '';
        if (password.length < 8) {
            feedback += 'Password must be at least 8 characters long.\n';
        }
        if (!/[A-Z]/.test(password)) {
            feedback += 'Password must contain at least one uppercase letter.\n';
        }
        if (!/[a-z]/.test(password)) {
            feedback += 'Password must contain at least one lowercase letter.\n';
        }
        if (!/\d/.test(password)) {
            feedback += 'Password must contain at least one digit.\n';
        }
        if (!/[@$!%*?&]/.test(password)) {
            feedback += 'Password must contain at least one special character (@$!%*?&).\n';
        }
        return feedback;
    }

    // Function to validate confirm password
    function validateConfirmPassword(password, confirmPassword) {
        if (password !== confirmPassword) {
            return 'Passwords do not match.';
        }
        return '';
    }

    // Function to validate phone number
    function validatePhoneNumber(phoneNumber) {
        if (!/^\+?1?\d{9,15}$/.test(phoneNumber)) {
            return 'Enter a valid phone number.';
        }
        return '';
    }

    // Function to validate amount
    function validateAmount(amount) {
        if (!/^\d+(\.\d{1,2})?$/.test(amount)) {
            return 'Enter a valid amount (e.g., 123.45).';
        }
        return '';
    }

    // Add event listeners for real-time validation
    const nameInput = document.getElementById('name');
    const emailInput = document.getElementById('email');
    const passwordInput = document.getElementById('password');
    const confirmPasswordInput = document.getElementById('confirmPassword');
    const phoneNumberInput = document.getElementById('phoneNumber');
    const amountInput = document.getElementById('amount');

    const nameFeedback = document.getElementById('nameFeedback');
    const emailFeedback = document.getElementById('emailFeedback');
    const passwordFeedback = document.getElementById('passwordFeedback');
    const confirmPasswordFeedback = document.getElementById('confirmPasswordFeedback');
    const phoneNumberFeedback = document.getElementById('phoneNumberFeedback');
    const amountFeedback = document.getElementById('amountFeedback');

    nameInput.addEventListener('input', function() {
        const feedback = validateName(nameInput.value);
        nameFeedback.textContent = feedback;
        nameFeedback.className = feedback ? 'error' : '';
    });

    emailInput.addEventListener('input', function() {
        const feedback = validateEmail(emailInput.value);
        emailFeedback.textContent = feedback;
        emailFeedback.className = feedback ? 'error' : '';
    });

    passwordInput.addEventListener('input', function() {
        const feedback = validatePassword(passwordInput.value);
        passwordFeedback.textContent = feedback;
        passwordFeedback.className = feedback ? 'error' : '';
    });

    confirmPasswordInput.addEventListener('input', function() {
        const feedback = validateConfirmPassword(passwordInput.value, confirmPasswordInput.value);
        confirmPasswordFeedback.textContent = feedback;
        confirmPasswordFeedback.className = feedback ? 'error' : '';
    });

    phoneNumberInput.addEventListener('input', function() {
        const feedback = validatePhoneNumber(phoneNumberInput.value);
        phoneNumberFeedback.textContent = feedback;
        phoneNumberFeedback.className = feedback ? 'error' : '';
    });

    amountInput.addEventListener('input', function() {
        const feedback = validateAmount(amountInput.value);
        amountFeedback.textContent = feedback;
        amountFeedback.className = feedback ? 'error' : '';
    });

    // Add event listener to the form for final validation on submit
    const form = document.getElementById('validationForm');
    form.addEventListener('submit', function(event) {
        let isValid = true;
        let feedback = '';

        if (validateName(nameInput.value)) {
            isValid = false;
            nameFeedback.textContent = validateName(nameInput.value);
            nameFeedback.className = 'error';
        }

        if (validateEmail(emailInput.value)) {
            isValid = false;
            emailFeedback.textContent = validateEmail(emailInput.value);
            emailFeedback.className = 'error';
        }

        if (validatePassword(passwordInput.value)) {
            isValid = false;
            passwordFeedback.textContent = validatePassword(passwordInput.value);
            passwordFeedback.className = 'error';
        }

        if (validateConfirmPassword(passwordInput.value, confirmPasswordInput.value)) {
            isValid = false;
            confirmPasswordFeedback.textContent = validateConfirmPassword(passwordInput.value, confirmPasswordInput.value);
            confirmPasswordFeedback.className = 'error';
        }

        if (validatePhoneNumber(phoneNumberInput.value)) {
            isValid = false;
            phoneNumberFeedback.textContent = validatePhoneNumber(phoneNumberInput.value);
            phoneNumberFeedback.className = 'error';
        }

        if (validateAmount(amountInput.value)) {
            isValid = false;
            amountFeedback.textContent = validateAmount(amountInput.value);
            amountFeedback.className = 'error';
        }

        if (!isValid) {
            event.preventDefault(); // Prevent form submission
        }
    });
});