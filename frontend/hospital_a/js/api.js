// ============================================
// API Configuration
// ============================================
const API_BASE = window.location.hostname === 'localhost' 
    ? 'http://localhost:8000/api/v1'
    : 'https://blood-local-hospital-a.onrender.com/api/v1';

// ============================================
// Fetch Wrapper with JWT Token (FIXED)
// ============================================
async function apiRequest(endpoint, options = {}) {
    const token = localStorage.getItem('access_token');
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };
    
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    try {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            ...options,
            headers
        });

        // 401 Unauthorized - Redirect to Login
        if (response.status === 401) {
            localStorage.removeItem('access_token');
            localStorage.removeItem('user');
            window.location.href = 'index.html';
            return null;
        }

        // ★★★ FIX: 204 No Content အတွက် JSON Parse မလုပ်တော့ဘူး ★★★
        if (response.status === 204) {
            return { status: response.status, data: null };
        }

        // Only try to parse JSON for non-204 responses
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            const data = await response.json();
            return { status: response.status, data };
        }

        return { status: response.status, data: null };

    } catch (error) {
        // Network error (server down, CORS, etc.)
        console.error('API Request Error:', error);
        throw error; // ဒီ Error ကို Caller ဆီ ပြန်ပို့ပါ
    }
}

// ============================================
// Helper Functions
// ============================================
function getAuthToken() {
    return localStorage.getItem('access_token');
}

function getUser() {
    try {
        return JSON.parse(localStorage.getItem('user'));
    } catch {
        return null;
    }
}

function isAuthenticated() {
    return !!localStorage.getItem('access_token');
}