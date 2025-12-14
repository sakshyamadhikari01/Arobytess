/*
 * Gaun Roots API Client
 * Handles all communication with the backend server
 */

var API_BASE = 'http://localhost:8000/api';

// Main API object with all endpoint methods
var api = {
    
    // User registration - creates new account
    register: async function(name, type) {
        var response = await fetch(API_BASE + '/users/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: name, type: type })
        });
        
        if (!response.ok) {
            var errorData = await response.json();
            throw new Error(errorData.detail || 'Could not create account');
        }
        return response.json();
    },

    // User login - authenticates existing user
    login: async function(name, type) {
        var response = await fetch(API_BASE + '/users/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: name, type: type })
        });
        
        if (!response.ok) {
            var errorData = await response.json();
            throw new Error(errorData.detail || 'Login unsuccessful');
        }
        return response.json();
    },

    // Fetch user profile by ID
    getUser: async function(userId) {
        var response = await fetch(API_BASE + '/users/' + userId);
        if (!response.ok) {
            throw new Error('Could not find user');
        }
        return response.json();
    },

    // Add credits to user account
    addCredits: async function(userId, amount) {
        var response = await fetch(API_BASE + '/users/' + userId + '/add-credits?amount=' + amount, {
            method: 'POST'
        });
        if (!response.ok) {
            throw new Error('Credit addition failed');
        }
        return response.json();
    },

    // Add friend to user's list
    addFriend: async function(userId, friendName) {
        var encodedName = encodeURIComponent(friendName);
        var response = await fetch(API_BASE + '/users/' + userId + '/add-friend?friend_name=' + encodedName, {
            method: 'POST'
        });
        if (!response.ok) {
            throw new Error('Could not add friend');
        }
        return response.json();
    },

    // Get all products in marketplace
    getProducts: async function() {
        var response = await fetch(API_BASE + '/products');
        return response.json();
    },

    // Get products for specific seller
    getSellerProducts: async function(sellerId) {
        var response = await fetch(API_BASE + '/products/seller/' + sellerId);
        return response.json();
    },

    // Create new product listing
    createProduct: async function(product, sellerId, sellerName) {
        var encodedName = encodeURIComponent(sellerName);
        var url = API_BASE + '/products?seller_id=' + sellerId + '&seller_name=' + encodedName;
        
        var response = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(product)
        });
        
        if (!response.ok) {
            throw new Error('Product creation failed');
        }
        return response.json();
    },

    // Remove product from marketplace
    deleteProduct: async function(productId) {
        var response = await fetch(API_BASE + '/products/' + productId, {
            method: 'DELETE'
        });
        if (!response.ok) {
            throw new Error('Could not remove product');
        }
        return response.json();
    },

    // Track product view
    incrementView: async function(productId) {
        var response = await fetch(API_BASE + '/products/' + productId + '/view', {
            method: 'POST'
        });
        return response.json();
    }
};

// Session management functions

function getCurrentUser() {
    var userData = localStorage.getItem('currentUser');
    if (userData) {
        return JSON.parse(userData);
    }
    return null;
}

function setCurrentUser(user) {
    localStorage.setItem('currentUser', JSON.stringify(user));
}

function clearCurrentUser() {
    localStorage.removeItem('currentUser');
}
