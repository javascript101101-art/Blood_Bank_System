// ============================================
// Login
// ============================================
document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }

    // Check if already logged in (redirect to dashboard)
    if (window.location.pathname.includes('index.html') && isAuthenticated()) {
        window.location.href = 'dashboard.html';
    }

    // Logout button
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', handleLogout);
    }
});

async function handleLogin(e) {
    e.preventDefault();
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const errorEl = document.getElementById('loginError');

    try {
        const response = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams({
                username: username,
                password: password
            })
        });

        const data = await response.json();

        if (response.ok) {
            // Save token and user info
            localStorage.setItem('access_token', data.access_token);
            
            // Decode JWT to get user info (optional)
            try {
                const payload = JSON.parse(atob(data.access_token.split('.')[1]));
                localStorage.setItem('user', JSON.stringify({
                    id: payload.sub,
                    role: payload.role
                }));
            } catch (e) {
                console.warn('Could not decode token');
            }

            window.location.href = 'dashboard.html';
        } else {
            errorEl.textContent = data.detail || 'Login failed. Please check your credentials.';
            errorEl.style.display = 'block';
        }
    } catch (error) {
        errorEl.textContent = 'Network error. Please try again.';
        errorEl.style.display = 'block';
    }
}

function handleLogout(e) {
    e.preventDefault();
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    window.location.href = 'index.html';
}

// ============================================
// Display User Info in Dashboard
// ============================================
function displayUserInfo() {
    const user = getUser();
    if (user) {
        const nameEl = document.getElementById('userName');
        const roleEl = document.getElementById('userRole');
        if (nameEl) nameEl.textContent = user.id ? 'User' : 'User';
        if (roleEl) roleEl.textContent = user.role || 'Staff';
    }
}

// Call when DOM is ready
if (document.getElementById('userName')) {
    displayUserInfo();
}