// ============================================
// Login & General App Startup
// ============================================
document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }

    // 🆕 Register Form
    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
        registerForm.addEventListener('submit', handleRegister);
    }

    if (window.location.pathname.includes('index.html') && isAuthenticated()) {
        window.location.href = 'dashboard.html';
    }

    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', handleLogout);
    }

    displayUserInfo();

    // ============================================
    // 🟢 Staff (Clinic) Portal UI Control
    // ============================================
    const user = getUser();
    const role = user?.role || 'Hospital_Admin';

    // 🟢 ဤနေရာတွင် Clinic ဟု ပြောင်းထားပါသည်
    if (role === 'Clinic') {
        
        // ၁။ Sidebar မှ Donors မီနူးကို ဖျောက်မည်
        const donorsMenu = document.getElementById('navDonors');
        if (donorsMenu) donorsMenu.style.display = 'none';

        // ၂။ 🆕 Sidebar မှ Global Request မီနူးကို ဖျောက်မည်
        const globalRequestMenu = document.getElementById('navGlobalRequest');
        if (globalRequestMenu) globalRequestMenu.style.display = 'none';

        // ၃။ Sidebar Header ကို "Clinic Portal" ဟု ပြောင်းမည်
        const sidebarHeader = document.querySelector('.sidebar-header h2');
        if (sidebarHeader) sidebarHeader.textContent = '🏥 Clinic Portal';

        // ၄။ Dashboard ရှိ Admin သီးသန့် Approve လုပ်မည့် Section ကို ဖျောက်မည်
        const adminApprovalSec = document.getElementById('adminApprovalSection');
        if (adminApprovalSec) adminApprovalSec.style.display = 'none';

        // ၅။ Inventory Page ရှိ "+ Add Inventory" ခလုတ်ကို ဖျောက်မည်
        const addInventoryBtn = document.getElementById('addInventoryBtn');
        if (addInventoryBtn) addInventoryBtn.style.display = 'none';

        // ၆။ 🆕 Dashboard ပေါ်ရှိ Donors နှင့်သက်ဆိုင်သော အပိုင်းများကို ဖျောက်မည်
        const totalDonorsCard = document.getElementById('totalDonors');
        if (totalDonorsCard) totalDonorsCard.closest('.stat-card').style.display = 'none';

        const recentDonorsTable = document.getElementById('recentDonorsTable');
        if (recentDonorsTable) recentDonorsTable.closest('.recent-section').style.display = 'none';
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

// ============================================
// 🆕 Register (Clinic Data ပါဝင်အောင် ပြင်ဆင်ထားသည်)
// ============================================
async function handleRegister(e) {
    e.preventDefault();
    
    // User Data
    const username = document.getElementById('username').value;
    const full_name = document.getElementById('full_name').value;
    const password = document.getElementById('password').value;
    const confirm_password = document.getElementById('confirm_password').value;
    const role = document.getElementById('role').value;

    // 🏥 Clinic Data
    const clinic_name = document.getElementById('regClinicName') ? document.getElementById('regClinicName').value : null;
    const license = document.getElementById('regLicense') ? document.getElementById('regLicense').value : null;
    const contact_phone = document.getElementById('regContactPhone') ? document.getElementById('regContactPhone').value : null;
    const contact_email = document.getElementById('regContactEmail') ? document.getElementById('regContactEmail').value : null;
    const clinic_address = document.getElementById('regClinicAddress') ? document.getElementById('regClinicAddress').value : null;
    
    const errorEl = document.getElementById('registerError');
    const successEl = document.getElementById('registerSuccess');
    errorEl.style.display = 'none';
    successEl.style.display = 'none';

    // Validation
    if (password !== confirm_password) {
        errorEl.textContent = 'Passwords do not match.';
        errorEl.style.display = 'block';
        return;
    }

    if (password.length < 6) {
        errorEl.textContent = 'Password must be at least 6 characters.';
        errorEl.style.display = 'block';
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/auth/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                username: username,
                full_name: full_name,
                password: password,
                role: role,
                // 🟢 API သို့ Clinic Data များ တွဲပို့ပေးခြင်း
                clinic_name: clinic_name,
                license: license,
                contact_phone: contact_phone,
                contact_email: contact_email,
                clinic_address: clinic_address
            })
        });

        const data = await response.json();

        if (response.ok) {
            successEl.textContent = data.message || 'Registration successful! Please wait for admin approval.';
            successEl.style.display = 'block';
            document.getElementById('registerForm').reset();
        } else {
            errorEl.textContent = data.detail || 'Registration failed. Please try again.';
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
        if (nameEl) nameEl.textContent = user.id ? 'User' : 'User';
        if (roleEl) roleEl.textContent = user.role || 'Clinic';
    }
}