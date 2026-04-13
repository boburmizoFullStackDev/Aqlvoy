const API_BASE = window.location.origin;

async function apiRequest(path, options = {}) {
    const response = await fetch(`${API_BASE}${path}`, {
        headers: {
            'Content-Type': 'application/json',
            ...(options.headers || {}),
        },
        ...options,
    });

    let data = {};
    try {
        data = await response.json();
    } catch (error) {
        data = {};
    }

    if (!response.ok) {
        throw new Error(data.detail || data.message || "Server bilan bog'lanishda xatolik yuz berdi.");
    }

    return data;
}

function persistUserSession(user) {
    localStorage.setItem('userName', user.name || 'Foydalanuvchi');
    localStorage.setItem('userEmail', user.email || '');
    localStorage.setItem('selectedRole', user.role || 'student');

    if (user.studentClass) {
        localStorage.setItem('studentClass', user.studentClass);
    } else {
        localStorage.removeItem('studentClass');
    }

    if (user.teacherSubject) {
        localStorage.setItem('teacherSubject', user.teacherSubject);
    } else {
        localStorage.removeItem('teacherSubject');
    }

    if (user.teacherExp) {
        localStorage.setItem('teacherExp', user.teacherExp);
    } else {
        localStorage.removeItem('teacherExp');
    }

    if (user.childName) {
        localStorage.setItem('childName', user.childName);
    } else {
        localStorage.removeItem('childName');
    }

    if (user.childClass) {
        localStorage.setItem('childClass', user.childClass);
    } else {
        localStorage.removeItem('childClass');
    }
}

function routeForRole(role) {
    if (role === 'teacher') return 'teacher.html';
    if (role === 'parent') return 'parent.html';
    return 'student.html';
}


function escapeHtml(value) {
    const div = document.createElement('div');
    div.textContent = value == null ? '' : String(value);
    return div.innerHTML;
}

function currentUserEmail(fallback = '') {
    return localStorage.getItem('userEmail') || fallback;
}
