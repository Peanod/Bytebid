/**
 * ByteBid Frontend Client
 * Helper untuk komunikasi ke backend API + manajemen auth state
 */
(function (window) {
  const API_BASE = window.BYTEBID_API_BASE || 'http://localhost:5000';
  const TOKEN_KEY = 'bytebid_token';
  const USER_KEY = 'bytebid_user';

  // ── Storage helpers ──────────────────────────────────────────────────────
  const storage = {
    getToken: () => localStorage.getItem(TOKEN_KEY),
    setToken: (t) => localStorage.setItem(TOKEN_KEY, t),
    clearToken: () => localStorage.removeItem(TOKEN_KEY),
    getUser: () => {
      const raw = localStorage.getItem(USER_KEY);
      return raw ? JSON.parse(raw) : null;
    },
    setUser: (u) => localStorage.setItem(USER_KEY, JSON.stringify(u)),
    clearUser: () => localStorage.removeItem(USER_KEY),
  };

  // ── Generic fetch wrapper ────────────────────────────────────────────────
  async function apiRequest(path, options = {}) {
    const token = storage.getToken();
    const headers = { ...(options.headers || {}) };

    // Set JSON content type kecuali body berupa FormData
    if (!(options.body instanceof FormData)) {
      headers['Content-Type'] = headers['Content-Type'] || 'application/json';
    }
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const res = await fetch(`${API_BASE}${path}`, { ...options, headers });

    let data = null;
    try { data = await res.json(); } catch (e) { /* non-JSON response */ }

    if (!res.ok) {
      // Token expired/invalid → auto logout
      if (res.status === 401 && token) {
        storage.clearToken();
        storage.clearUser();
      }
      const err = new Error(data?.message || `HTTP ${res.status}`);
      err.status = res.status;
      err.data = data;
      throw err;
    }
    return data;
  }

  // ── Auth methods ─────────────────────────────────────────────────────────
  const auth = {
    async register({ username, name, email, password }) {
      const data = await apiRequest('/api/auth/register', {
        method: 'POST',
        body: JSON.stringify({ username, name, email, password }),
      });
      if (data.token) {
        storage.setToken(data.token);
        storage.setUser(data.user);
      }
      return data;
    },

    async login({ identifier, password }) {
      const data = await apiRequest('/api/auth/login', {
        method: 'POST',
        body: JSON.stringify({ identifier, password }),
      });
      if (data.token) {
        storage.setToken(data.token);
        storage.setUser(data.user);
      }
      return data;
    },

    async forgot(identifier) {
      return apiRequest('/api/auth/forgot', {
        method: 'POST',
        body: JSON.stringify({ identifier }),
      });
    },

    async reset(token, password) {
      return apiRequest('/api/auth/reset', {
        method: 'POST',
        body: JSON.stringify({ token, password }),
      });
    },

    async me() {
      return apiRequest('/api/auth/me');
    },

    logout() {
      storage.clearToken();
      storage.clearUser();
      window.location.href = '/';
    },

    isAuthenticated: () => !!storage.getToken(),
    currentUser: () => storage.getUser(),
  };

  // ── Items / Bids / Notifications / Admin ─────────────────────────────────
  const items = {
    list: (params = {}) => {
      const qs = new URLSearchParams(params).toString();
      return apiRequest(`/api/items${qs ? '?' + qs : ''}`);
    },
    get: (id) => apiRequest(`/api/items/${id}`),
    categories: () => apiRequest('/api/items/categories'),
  };

  const bids = {
    place: (itemId, amount) => apiRequest(`/api/bids/${itemId}`, {
      method: 'POST',
      body: JSON.stringify({ amount }),
    }),
    forItem: (itemId) => apiRequest(`/api/bids/item/${itemId}`),
    mine: () => apiRequest('/api/bids/me'),
  };

  const notifications = {
    list: () => apiRequest('/api/notifications'),
    markRead: (id) => apiRequest(`/api/notifications/${id}/read`, { method: 'POST' }),
    markAllRead: () => apiRequest('/api/notifications/read-all', { method: 'POST' }),
  };

  const admin = {
    dashboard: () => apiRequest('/api/admin/dashboard'),
    createItem: (formData) => apiRequest('/api/admin/items', {
      method: 'POST',
      body: formData,   // FormData untuk upload gambar
    }),
    updateItem: (id, formData) => apiRequest(`/api/admin/items/${id}`, {
      method: 'PUT',
      body: formData,
    }),
    deleteItem: (id) => apiRequest(`/api/admin/items/${id}`, { method: 'DELETE' }),
    cancelItem: (id) => apiRequest(`/api/admin/items/${id}/cancel`, { method: 'POST' }),
    endItem: (id) => apiRequest(`/api/admin/items/${id}/end`, { method: 'POST' }),
  };

  // ── Utility ──────────────────────────────────────────────────────────────
  function formatRupiah(amount) {
    if (amount == null) return 'Rp0';
    return 'Rp' + Math.round(amount).toLocaleString('id-ID');
  }

  function formatTimer(seconds) {
    if (seconds <= 0) return '00:00:00';
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = seconds % 60;
    return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
  }

  function escapeHtml(s) {
    if (s == null) return '';
    return String(s).replace(/[&<>"']/g, (c) => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[c]));
  }

  // Update UI nav based on auth state
  function renderNavAuth() {
    const navAuth = document.getElementById('nav-auth');
    if (!navAuth) return;
    const user = storage.getUser();
    if (user) {
      navAuth.innerHTML = `
        <a href="/notifications" class="btn btn-ghost" id="nav-notif">🔔</a>
        <span style="color:var(--muted);font-size:.875rem;align-self:center">${escapeHtml(user.name)}</span>
        <a href="#" class="btn btn-ghost" onclick="ByteBid.auth.logout();return false;">Keluar</a>
      `;
      // Update badge unread
      notifications.list().then(d => {
        const badge = document.getElementById('nav-notif');
        if (badge && d.unread_count > 0) {
          badge.innerHTML = `🔔 <span style="background:var(--red);color:#fff;border-radius:50%;padding:0 6px;font-size:.7rem;margin-left:4px">${d.unread_count}</span>`;
        }
      }).catch(() => { /* not logged in or API down */ });
    } else {
      navAuth.innerHTML = `
        <a href="/login" class="btn btn-ghost">Masuk</a>
        <a href="/register" class="btn btn-red">Daftar</a>
      `;
    }
  }

  // ── Toast notification ───────────────────────────────────────────────────
  function toast(message, type = 'info') {
    const colors = { info: '#00bcd4', success: '#00d68f', error: '#e8173a' };
    const el = document.createElement('div');
    el.style.cssText = `
      position:fixed;top:80px;right:20px;z-index:9999;
      background:#1e1e2a;border-left:4px solid ${colors[type] || colors.info};
      color:#f0f0f8;padding:14px 20px;border-radius:8px;
      box-shadow:0 4px 12px rgba(0,0,0,.4);font-size:.9rem;
      max-width:340px;animation:slideIn .3s ease;
    `;
    el.textContent = message;
    document.body.appendChild(el);
    setTimeout(() => { el.style.opacity = '0'; el.style.transition = 'opacity .3s'; }, 3500);
    setTimeout(() => el.remove(), 4000);
  }

  // Auto-render nav saat DOM ready
  document.addEventListener('DOMContentLoaded', renderNavAuth);

  // ── Export ───────────────────────────────────────────────────────────────
  window.ByteBid = {
    API_BASE,
    auth, items, bids, notifications, admin,
    formatRupiah, formatTimer, escapeHtml, toast, renderNavAuth,
    apiRequest,
  };
})(window);
