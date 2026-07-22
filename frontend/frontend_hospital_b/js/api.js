// ============================================
// API Configuration (Hospital B)
// ============================================
// Hospital B Server Port: 8002
// Frontend Port: 5502
const API_BASE = window.location.hostname === 'localhost' 
    ? 'http://localhost:8002/api/v1'   // Hospital B Server (Local)
    : 'https://blood-hospital-b.onrender.com/api/v1';  // Production

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

        // 204 No Content - No body to parse
        if (response.status === 204) {
            return { status: response.status, data: null };
        }

        // Parse JSON response
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