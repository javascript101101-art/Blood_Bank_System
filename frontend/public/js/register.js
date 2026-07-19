// ============================================
// Public Hospital Registration
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('registerForm');
    const submitBtn = document.getElementById('submitBtn');
    const errorDiv = document.getElementById('errorMessage');
    const successDiv = document.getElementById('successMessage');

    form.addEventListener('submit', async function(e) {
        e.preventDefault();

        // Hide previous messages
        errorDiv.style.display = 'none';
        successDiv.style.display = 'none';

        // Get form data
        const hospitalName = document.getElementById('hospitalName').value.trim();
        const address = document.getElementById('address').value.trim();
        const contactEmail = document.getElementById('contactEmail').value.trim();

        // Validate
        if (!hospitalName) {
            showError('Please enter hospital name.');
            return;
        }
        if (!contactEmail) {
            showError('Please enter contact email.');
            return;
        }
        if (!isValidEmail(contactEmail)) {
            showError('Please enter a valid email address.');
            return;
        }

        // Disable button
        submitBtn.disabled = true;
        submitBtn.textContent = '⏳ Submitting...';

        try {
            const response = await fetch('http://localhost:8001/api/v1/public/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    hospital_name: hospitalName,
                    address: address || null,
                    contact_email: contactEmail,
                }),
            });

            const data = await response.json();

            if (response.ok) {
                // Success
                successDiv.style.display = 'block';
                form.reset();
                submitBtn.textContent = '✅ Submitted Successfully!';
            } else {
                // Error from server
                const errorMsg = data.detail || 'Registration failed. Please try again.';
                showError(errorMsg);
                submitBtn.textContent = '📨 Submit Registration Request';
                submitBtn.disabled = false;
            }
        } catch (error) {
            console.error('Registration error:', error);
            showError('Network error. Please check your connection and try again.');
            submitBtn.textContent = '📨 Submit Registration Request';
            submitBtn.disabled = false;
        }
    });

    function showError(message) {
        errorDiv.textContent = '❌ ' + message;
        errorDiv.style.display = 'block';
        errorDiv.style.background = '#f8d7da';
        errorDiv.style.color = '#721c24';
        errorDiv.style.padding = '12px 16px';
        errorDiv.style.borderRadius = '8px';
        errorDiv.style.borderLeft = '4px solid #dc3545';
        errorDiv.style.marginTop = '12px';
        errorDiv.style.fontSize = '14px';
    }

    function isValidEmail(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    }
});