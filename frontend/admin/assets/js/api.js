const API_BASE = '/api';

function getToken() {
    return localStorage.getItem('admin_token');
}

function setToken(token) {
    localStorage.setItem('admin_token', token);
}

function clearToken() {
    localStorage.removeItem('admin_token');
}

function requireAuth() {
    if (!getToken()) {
        window.location.href = '/admin/login.html';
    }
}

function logout() {
    clearToken();
    window.location.href = '/admin/login.html';
}

async function apiRequest(endpoint, options = {}) {
    const token = getToken();
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
        
        if (response.status === 401) {
            clearToken();
            window.location.href = '/admin/login.html';
            return null;
        }
        
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            throw new Error('Invalid server response');
        }
        
        const data = await response.json();
        
        if (!response.ok) {
            const errMsg = typeof data.detail === 'string' ? data.detail : (data.message || 'Server error');
            throw new Error(errMsg);
        }
        
        return data;
    } catch (error) {
        console.error(error);
        throw error;
    }
}

function ensureToastContainer() {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        const lang = (typeof getCurrentLang === 'function') ? getCurrentLang() : 'en';
        const isRtl = lang === 'fa';
        const positionSide = isRtl ? 'left' : 'right';
        container.style.cssText = `position:fixed;bottom:20px;${positionSide}:20px;z-index:99999;display:flex;flex-direction:column;gap:8px;pointer-events:none;`;
        document.body.appendChild(container);
    }
    return container;
}

function showToast(message, type = 'info') {
    const container = ensureToastContainer();
    
    const colors = {
        success: '#10b981',
        error: '#ef4444',
        info: '#3b82f6',
        warning: '#f59e0b'
    };
    
    const icons = {
        success: '✓',
        error: '✗',
        info: 'ℹ',
        warning: '⚠'
    };
    
    const lang = (typeof getCurrentLang === 'function') ? getCurrentLang() : 'en';
    const isRtl = lang === 'fa';
    const dir = isRtl ? 'rtl' : 'ltr';
    const slideFrom = isRtl ? 'translateX(120%)' : 'translateX(-120%)';
    const slideTo = 'translateX(0)';
    
    const toast = document.createElement('div');
    toast.style.cssText = `
        background: ${colors[type] || colors.info};
        color: white;
        padding: 12px 20px;
        border-radius: 12px;
        font-size: 14px;
        font-family: 'Vazir', 'Segoe UI', sans-serif;
        box-shadow: 0 10px 25px rgba(0,0,0,0.4);
        min-width: 260px;
        max-width: 400px;
        display: flex;
        align-items: center;
        gap: 10px;
        transform: ${slideFrom};
        transition: transform 0.3s ease-out;
        pointer-events: auto;
        direction: ${dir};
    `;
    
    toast.innerHTML = `<span style="font-size:18px;font-weight:bold;">${icons[type] || icons.info}</span><span style="flex:1;">${message}</span>`;
    container.appendChild(toast);
    
    requestAnimationFrame(() => {
        toast.style.transform = slideTo;
    });
    
    setTimeout(() => {
        toast.style.transform = slideFrom;
        setTimeout(() => toast.remove(), 300);
    }, 3500);
}

function formatDate(dateString) {
    if (!dateString) return '-';
    try {
        let cleanStr = dateString;
        if (typeof dateString === 'string' && !dateString.endsWith('Z') && !dateString.includes('+') && !dateString.includes('GMT')) {
            cleanStr = dateString.replace(' ', 'T') + 'Z';
        }
        const date = new Date(cleanStr);
        const lang = (typeof getCurrentLang === 'function') ? getCurrentLang() : 'en';
        
        if (lang === 'fa') {
            return new Intl.DateTimeFormat('fa-IR-u-ca-persian', {
                year: 'numeric', month: '2-digit', day: '2-digit',
                hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false
            }).format(date);
        } else if (lang === 'ru') {
            return new Intl.DateTimeFormat('ru-RU', {
                year: 'numeric', month: '2-digit', day: '2-digit',
                hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false
            }).format(date);
        } else {
            return new Intl.DateTimeFormat('en-US', {
                year: 'numeric', month: 'short', day: '2-digit',
                hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false
            }).format(date);
        }
    } catch (e) {
        console.error(e);
        return dateString;
    }
}

function formatBytes(gb) {
    if (gb >= 1024) return (gb / 1024).toFixed(2) + ' TB';
    return gb.toFixed(2) + ' GB';
}

function copyToClipboard(text) {
    if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(text).then(() => {
            const msg = (typeof t === 'function') ? t('common.copied') : 'Copied!';
            showToast(msg, 'success');
        }).catch(() => {
            fallbackCopy(text);
        });
    } else {
        fallbackCopy(text);
    }
}

function fallbackCopy(text) {
    const textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.style.position = 'fixed';
    textarea.style.opacity = '0';
    document.body.appendChild(textarea);
    textarea.select();
    try {
        document.execCommand('copy');
        const msg = (typeof t === 'function') ? t('common.copied') : 'Copied!';
        showToast(msg, 'success');
    } catch {
        showToast('Error copying', 'error');
    }
    document.body.removeChild(textarea);
}