const API_BASE = window.location.origin;

// ---------------------------------------------------------------------------
// Token helpers
// ---------------------------------------------------------------------------

function getAccessToken()  { return localStorage.getItem('accessToken');  }
function getRefreshToken() { return localStorage.getItem('refreshToken'); }

function saveTokens(access, refresh) {
    localStorage.setItem('accessToken',  access);
    localStorage.setItem('refreshToken', refresh);
}

function clearTokens() {
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
}

// ---------------------------------------------------------------------------
// Core request helper — injects Bearer token automatically
// ---------------------------------------------------------------------------

async function apiRequest(path, options = {}) {
    const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };

    const token = getAccessToken();
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const response = await fetch(`${API_BASE}${path}`, { ...options, headers });

    let data = {};
    try { data = await response.json(); } catch (_) { data = {}; }

    if (!response.ok) {
        throw new Error(
            data.detail ||
            data.message ||
            (data.errors ? Object.values(data.errors)[0] : null) ||
            "Server bilan bog'lanishda xatolik yuz berdi."
        );
    }

    return data;
}

// ---------------------------------------------------------------------------
// Session persistence
// ---------------------------------------------------------------------------

function persistUserSession(user, access, refresh) {
    if (access && refresh) saveTokens(access, refresh);
    localStorage.setItem('userName',     user.name  || 'Foydalanuvchi');
    localStorage.setItem('userPhone',    user.phone || '');
    localStorage.setItem('selectedRole', user.role  || 'student');
    if (user.grade != null) localStorage.setItem('studentGrade', user.grade);
    else                    localStorage.removeItem('studentGrade');
}

function clearUserSession() {
    clearTokens();
    ['userName', 'userPhone', 'selectedRole', 'studentGrade'].forEach(k => localStorage.removeItem(k));
}

// ---------------------------------------------------------------------------
// Routing — maps role to Django URL
// ---------------------------------------------------------------------------

function routeForRole(role) {
    if (role === 'teacher') return '/teacher/';
    if (role === 'parent')  return '/parent/';
    return '/student/';
}

// ---------------------------------------------------------------------------
// Logout
// ---------------------------------------------------------------------------

async function logoutUser() {
    const refresh = getRefreshToken();
    try {
        if (refresh) {
            await apiRequest('/api/auth/logout', {
                method: 'POST',
                body: JSON.stringify({ refresh }),
            });
        }
    } catch (_) { /* ignore errors — clear session regardless */ }
    clearUserSession();
    window.location.href = '/';
}

// ---------------------------------------------------------------------------
// Utils
// ---------------------------------------------------------------------------

function escapeHtml(value) {
    const div = document.createElement('div');
    div.textContent = value == null ? '' : String(value);
    return div.innerHTML;
}

function currentUserPhone(fallback = '') {
    return localStorage.getItem('userPhone') || fallback;
}
