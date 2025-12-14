// Auth helper - updates navigation based on login state
function updateNavigation() {
    var currentUser = JSON.parse(localStorage.getItem('currentUser'));
    var isLoggedIn = !!currentUser;
    
    // Get profile link URL based on user type
    var profileUrl = 'profile.html';
    if (currentUser && currentUser.type === 'seller') {
        profileUrl = 'seller-profile.html';
    }

    // Update all navigation menus
    var navMenus = [
        document.getElementById('navMenu'),
        document.querySelector('.slider-nav'),
        document.querySelector('.fullpage-nav')
    ];

    navMenus.forEach(function(menu) {
        if (!menu) return;
        
        // Find and update profile/login links
        var links = menu.querySelectorAll('a');
        links.forEach(function(link) {
            var href = link.getAttribute('href');
            var text = link.textContent.trim().toLowerCase();
            
            // Update Profile link
            if (href === 'profile.html' || href === 'seller-profile.html' || text === 'profile') {
                if (isLoggedIn) {
                    link.setAttribute('href', profileUrl);
                    link.textContent = currentUser.name;
                } else {
                    link.setAttribute('href', 'profile.html');
                    link.textContent = 'Profile';
                }
            }
            
            // Update Login/Logout link
            if (href === 'login.html' || text === 'login' || text === 'logout') {
                if (isLoggedIn) {
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

    // Update Get Started button if exists
    var getStartedBtn = document.getElementById('getStartedBtn');
    if (getStartedBtn && isLoggedIn) {
        getStartedBtn.textContent = 'Go to Dashboard';
        getStartedBtn.onclick = function(e) {
            e.preventDefault();
            window.location.href = profileUrl;
        };
    }
}

// Run on page load
document.addEventListener('DOMContentLoaded', updateNavigation);
