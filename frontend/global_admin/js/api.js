// ============================================
// API Configuration (Global Server)
// ============================================
const API_BASE = 'http://localhost:8001/api/v1';

// ============================================
// Fetch Wrapper with JWT Token
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

        // 204 No Content
        if (response.status === 204) {
            return { status: response.status, data: null };
        }

        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            const data = await response.json();
            return { status: response.status, data };
        }

        return { status: response.status, data: null };

    } catch (error) {
        console.error('API Request Error:', error);
        throw error;
    }
}

function isAuthenticated() {
    return !!localStorage.getItem('access_token');
}

function getUser() {
    try {
        return JSON.parse(localStorage.getItem('user'));
    } catch {
        return null;
    }
}