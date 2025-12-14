function updateNavigation() {
    var currentUser = JSON.parse(localStorage.getItem('currentUser'));
    var isLoggedIn = !!currentUser;
    
    var profileUrl = 'profile.html';
    if (currentUser && currentUser.type === 'seller') {
        profileUrl = 'seller-profile.html';
    }

    var navMenus = [
        document.getElementById('navMenu'),
        document.querySelector('.slider-nav'),
        document.querySelector('.fullpage-nav')
    ];

    navMenus.forEach(function(menu) {
        if (!menu) return;
        
        var links = menu.querySelectorAll('a');
        links.forEach(function(link) {
            var href = link.getAttribute('href');
            var text = link.textContent.trim().toLowerCase();
            
            if (href === 'profile.html' || href === 'seller-profile.html' || text === 'profile') {
                if (isLoggedIn) {
                    link.setAttribute('href', profileUrl);
                    link.textContent = currentUser.name;
                } else {
                    link.setAttribute('href', 'profile.html');
                    link.textContent = 'Profile';
                }
            }
            
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

    var getStartedBtn = document.getElementById('getStartedBtn');
    if (getStartedBtn && isLoggedIn) {
        getStartedBtn.textContent = 'Go to Dashboard';
        getStartedBtn.onclick = function(e) {
            e.preventDefault();
            window.location.href = profileUrl;
        };
    }
}

document.addEventListener('DOMContentLoaded', updateNavigation);
