// ============================================
// Login
// ============================================
document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }

    if (window.location.pathname.includes('index.html') && isAuthenticated()) {
        window.location.href = 'dashboard.html';
    }

    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', handleLogout);
    }

    // Display user info
    displayUserInfo();
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
            localStorage.setItem('access_token', data.access_token);
            
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

function displayUserInfo() {
    const user = getUser();
    if (user) {
        const nameEl = document.getElementById('userName');
        const roleEl = document.getElementById('userRole');
        if (nameEl) nameEl.textContent = 'Global Admin';
        if (roleEl) roleEl.textContent = user.role || 'Global_Admin';
    }
}