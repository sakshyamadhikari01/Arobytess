/*
 * Authentication and Navigation Handler
 * Updates navigation links based on user login state
 */

function updateNavigation() {
    // Get current user from storage
    var user = JSON.parse(localStorage.getItem('currentUser'));
    var loggedIn = user !== null;
    
    // Determine correct profile page based on user type
    var profilePage = 'profile.html';
    if (user && user.type === 'seller') {
        profilePage = 'seller-profile.html';
    }

    // Find all navigation menus on the page
    var navContainers = [
        document.getElementById('navMenu'),
        document.querySelector('.slider-nav'),
        document.querySelector('.fullpage-nav')
    ];

    // Update each navigation menu
    navContainers.forEach(function(nav) {
        if (!nav) return;
        
        var links = nav.querySelectorAll('a');
        
        links.forEach(function(link) {
            var href = link.getAttribute('href');
            var linkText = link.textContent.trim().toLowerCase();
            
            // Update profile links
            if (href === 'profile.html' || href === 'seller-profile.html' || linkText === 'profile') {
                if (loggedIn) {
                    link.setAttribute('href', profilePage);
                    link.textContent = user.name;
                } else {
                    link.setAttribute('href', 'profile.html');
                    link.textContent = 'Profile';
                }
            }
            
            // Update login/logout links
            if (href === 'login.html' || linkText === 'login' || linkText === 'logout') {
                if (loggedIn) {
                    link.textContent = 'Logout';
                    link.setAttribute('href', '#');
                    link.onclick = function(e) {
                        e.preventDefault();
                        localStorage.removeItem('currentUser');
                        window.location.href = 'home.html';
                    };
                } else {
                    link.textContent = 'Login';
                    link.setAttribute('href', 'login.html');
                    link.onclick = null;
                }
            }
        });
    });

    // Update "Get Started" button on home page
    var startBtn = document.getElementById('getStartedBtn');
    if (startBtn && loggedIn) {
        startBtn.textContent = 'Go to Dashboard';
        startBtn.onclick = function(e) {
            e.preventDefault();
            window.location.href = profilePage;
        };
    }
}

// Run when page loads
document.addEventListener('DOMContentLoaded', updateNavigation);
