const API_BASE = 'http://localhost:8000/api';

const api = {
    async register(name, type) {
        const res = await fetch(`${API_BASE}/users/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, type })
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Registration failed');
        }
        return res.json();
    },

    async login(name, type) {
        const res = await fetch(`${API_BASE}/users/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, type })
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Login failed');
        }
        return res.json();
    },

    async getUser(userId) {
        const res = await fetch(`${API_BASE}/users/${userId}`);
        if (!res.ok) throw new Error('User not found');
        return res.json();
    },

    async addCredits(userId, amount) {
        const res = await fetch(`${API_BASE}/users/${userId}/add-credits?amount=${amount}`, {
            method: 'POST'
        });
        if (!res.ok) throw new Error('Failed to add credits');
        return res.json();
    },

    async addFriend(userId, friendName) {
        const res = await fetch(`${API_BASE}/users/${userId}/add-friend?friend_name=${encodeURIComponent(friendName)}`, {
            method: 'POST'
        });
        if (!res.ok) throw new Error('Failed to add friend');
        return res.json();
    },

    async getProducts() {
        const res = await fetch(`${API_BASE}/products`);
        return res.json();
    },

    async getSellerProducts(sellerId) {
        const res = await fetch(`${API_BASE}/products/seller/${sellerId}`);
        return res.json();
    },

    async createProduct(product, sellerId, sellerName) {
        const res = await fetch(`${API_BASE}/products?seller_id=${sellerId}&seller_name=${encodeURIComponent(sellerName)}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(product)
        });
        if (!res.ok) throw new Error('Failed to create product');
        return res.json();
    },

    async deleteProduct(productId) {
        const res = await fetch(`${API_BASE}/products/${productId}`, {
            method: 'DELETE'
        });
        if (!res.ok) throw new Error('Failed to delete product');
        return res.json();
    },

    async incrementView(productId) {
        const res = await fetch(`${API_BASE}/products/${productId}/view`, {
            method: 'POST'
        });
        return res.json();
    }
};

function getCurrentUser() {
    return JSON.parse(localStorage.getItem('currentUser'));
}

function setCurrentUser(user) {
    localStorage.setItem('currentUser', JSON.stringify(user));
}

function clearCurrentUser() {
    localStorage.removeItem('currentUser');
}
