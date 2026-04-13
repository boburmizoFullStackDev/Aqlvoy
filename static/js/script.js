// Umumiy JavaScript funksiyalari

// Splash ekranini yashirish
setTimeout(() => {
    const splash = document.getElementById('splash');
    if (splash) {
        splash.classList.add('out');
        setTimeout(() => {
            splash.style.display = 'none';
        }, 700);
    }
}, 2200);

// Scroll navbar
window.addEventListener('scroll', () => {
    const nav = document.getElementById('navbar');
    if (nav) {
        if (window.scrollY > 20) {
            nav.classList.add('scrolled');
        } else {
            nav.classList.remove('scrolled');
        }
    }
    checkReveal();
    animateStats();
});

// Reveal on scroll
function checkReveal() {
    document.querySelectorAll('.reveal, .reveal-scale').forEach(el => {
        const rect = el.getBoundingClientRect();
        if (rect.top < window.innerHeight * 0.88) {
            el.classList.add('visible');
        }
    });
}

// Animate stats
let statsAnimated = false;
function animateStats() {
    if (statsAnimated) return;
    const statsSection = document.getElementById('progress');
    if (!statsSection) return;
    const rect = statsSection.getBoundingClientRect();
    if (rect.top < window.innerHeight * 0.85) {
        statsAnimated = true;
        document.querySelectorAll('.stat-number[data-target]').forEach(el => {
            const target = parseInt(el.getAttribute('data-target'));
            const suffix = el.getAttribute('data-suffix') || '';
            let current = 0;
            const step = target / 50;
            const timer = setInterval(() => {
                current += step;
                if (current >= target) {
                    el.textContent = target.toLocaleString() + suffix;
                    clearInterval(timer);
                } else {
                    el.textContent = Math.floor(current).toLocaleString() + suffix;
                }
            }, 30);
        });
    }
}

// Scroll to section
function scrollToSection(id) {
    const el = document.getElementById(id);
    if (el) {
        el.scrollIntoView({ behavior: 'smooth' });
    }
}

// Mobile menu
function toggleMenu() {
    const menu = document.getElementById('mobile-menu');
    if (menu) {
        menu.classList.toggle('open');
    }
}

function closeMenu() {
    const menu = document.getElementById('mobile-menu');
    if (menu) {
        menu.classList.remove('open');
    }
}

// FAQ toggle
function toggleFaq(btn) {
    const item = btn.closest('.faq-item');
    if (item) {
        item.classList.toggle('open');
    }
}

// Password toggle
function togglePassword(inputId) {
    const input = document.getElementById(inputId);
    if (input) {
        input.type = input.type === 'password' ? 'text' : 'password';
    }
}

// Logout function
function logout() {
    localStorage.clear();
    window.location.href = 'index.html';
}

// Initialize on load
document.addEventListener('DOMContentLoaded', () => {
    checkReveal();
    animateStats();
});

window.addEventListener('scroll', checkReveal, { passive: true });
setTimeout(checkReveal, 100);