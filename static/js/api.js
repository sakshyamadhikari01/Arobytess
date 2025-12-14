var API_BASE = 'http://localhost:8000/api';

var api = {
    register: async function(name, type) {
        var res = await fetch(API_BASE + '/users/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: name, type: type })
        });
        if (!res.ok) {
            var err = await res.json();
            throw new Error(err.detail || 'Registration failed');
        }
        return res.json();
    },

    login: async function(name, type) {
        var res = await fetch(API_BASE + '/users/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: name, type: type })
        });
        if (!res.ok) {
            var err = await res.json();
            throw new Error(err.detail || 'Login failed');
        }
        return res.json();
    },

    getUser: async function(userId) {
        var res = await fetch(API_BASE + '/users/' + userId);
        if (!res.ok) throw new Error('User not found');
        return res.json();
    },

    addCredits: async function(userId, amount) {
        var res = await fetch(API_BASE + '/users/' + userId + '/add-credits?amount=' + amount, {
            method: 'POST'
        });
        if (!res.ok) throw new Error('Failed to add credits');
        return res.json();
    },

    addFriend: async function(userId, friendName) {
        var res = await fetch(API_BASE + '/users/' + userId + '/add-friend?friend_name=' + encodeURIComponent(friendName), {
            method: 'POST'
        });
        if (!res.ok) throw new Error('Failed to add friend');
        return res.json();
    },

    getProducts: async function() {
        var res = await fetch(API_BASE + '/products');
        return res.json();
    },

    getSellerProducts: async function(sellerId) {
        var res = await fetch(API_BASE + '/products/seller/' + sellerId);
        return res.json();
    },

    createProduct: async function(product, sellerId, sellerName) {
        var res = await fetch(API_BASE + '/products?seller_id=' + sellerId + '&seller_name=' + encodeURIComponent(sellerName), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(product)
        });
        if (!res.ok) throw new Error('Failed to create product');
        return res.json();
    },

    deleteProduct: async function(productId) {
        var res = await fetch(API_BASE + '/products/' + productId, {
            method: 'DELETE'
        });
        if (!res.ok) throw new Error('Failed to delete product');
        return res.json();
    },

    incrementView: async function(productId) {
        var res = await fetch(API_BASE + '/products/' + productId + '/view', {
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
