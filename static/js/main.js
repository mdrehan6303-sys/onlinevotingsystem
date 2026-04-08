// main.js
// Makes the website interactive and user friendly

// ─────────────────────────────────────────
// 1. AUTO HIDE ALERTS
// ─────────────────────────────────────────
// Flash messages (success/error) disappear
// automatically after 3 seconds
// ─────────────────────────────────────────
function autoHideAlerts() {
    const alerts = document.querySelectorAll('.alert');

    alerts.forEach(function(alert) {
        // Wait 3 seconds then slowly fade out
        setTimeout(function() {
            alert.style.transition = 'opacity 1s';
            alert.style.opacity = '0';

            // Remove from page after fade completes
            setTimeout(function() {
                alert.remove();
            }, 1000);
        }, 3000);
    });
}

// ─────────────────────────────────────────
// 2. LOADING SPINNER ON VOTE SUBMIT
// ─────────────────────────────────────────
// When voter clicks "Cast My Vote" button,
// show a loading spinner so they know
// their vote is being processed
// ─────────────────────────────────────────
function setupVoteButton() {
    const voteForm = document.querySelector('form');
    const submitBtn = document.querySelector('.btn-primary');

    if (voteForm && submitBtn) {
        voteForm.addEventListener('submit', function() {
            // Change button text to show loading
            submitBtn.innerHTML = '⏳ Processing your vote...';
            submitBtn.disabled = true;
            submitBtn.style.opacity = '0.7';
        });
    }
}

// ─────────────────────────────────────────
// 3. SMOOTH FADE IN ANIMATION
// ─────────────────────────────────────────
// When any page loads, content smoothly
// fades in instead of appearing suddenly
// ─────────────────────────────────────────
function setupFadeIn() {
    // Add fade-in style to page
    document.body.style.opacity = '0';
    document.body.style.transition = 'opacity 0.5s';

    // After tiny delay, fade in
    setTimeout(function() {
        document.body.style.opacity = '1';
    }, 100);
}

// ─────────────────────────────────────────
// 4. HIGHLIGHT ACTIVE NAV LINK
// ─────────────────────────────────────────
// Highlights the current page link
// in the navbar so user knows where they are
// ─────────────────────────────────────────
function highlightActiveNav() {
    const currentPage = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-links a');

    navLinks.forEach(function(link) {
        if (link.getAttribute('href') === currentPage) {
            link.style.background = 'rgba(255,255,255,0.3)';
            link.style.fontWeight = 'bold';
        }
    });
}

// ─────────────────────────────────────────
// 5. PROGRESS BAR ANIMATION
// ─────────────────────────────────────────
// On results page, progress bars animate
// from 0% to their actual value smoothly
// ─────────────────────────────────────────
function animateProgressBars() {
    const progressBars = document.querySelectorAll('.progress-fill');

    progressBars.forEach(function(bar) {
        // Save the target width
        const targetWidth = bar.style.width;

        // Start from 0
        bar.style.width = '0%';
        bar.style.transition = 'width 1.5s ease';

        // Animate to target after short delay
        setTimeout(function() {
            bar.style.width = targetWidth;
        }, 300);
    });
}

// ─────────────────────────────────────────
// 6. CONFIRM BEFORE LEAVING VOTE PAGE
// ─────────────────────────────────────────
// If voter accidentally clicks browser back
// button on vote page, warn them first
// ─────────────────────────────────────────
function setupLeaveWarning() {
    const voteForm = document.querySelector('form');

    if (voteForm) {
        let formSubmitted = false;

        // Mark as submitted when form is sent
        voteForm.addEventListener('submit', function() {
            formSubmitted = true;
        });

        // Warn if trying to leave without voting
        window.addEventListener('beforeunload', function(e) {
            if (!formSubmitted) {
                e.preventDefault();
                e.returnValue = 'Are you sure you want to leave? Your vote has not been cast!';
            }
        });
    }
}

// ─────────────────────────────────────────
// 7. STAT CARD COUNTER ANIMATION
// ─────────────────────────────────────────
// On admin dashboard, numbers count up
// from 0 to their real value like a counter
// ─────────────────────────────────────────
function animateCounters() {
    const statNumbers = document.querySelectorAll('.stat-number');

    statNumbers.forEach(function(stat) {
        const finalValue = stat.innerText;

        // Only animate if it's a pure number
        if (!isNaN(finalValue) && finalValue !== '') {
            let start = 0;
            const end = parseInt(finalValue);
            const duration = 1000; // 1 second
            const stepTime = 50;   // Update every 50ms
            const steps = duration / stepTime;
            const increment = end / steps;

            stat.innerText = '0';

            const counter = setInterval(function() {
                start += increment;
                if (start >= end) {
                    stat.innerText = end;
                    clearInterval(counter);
                } else {
                    stat.innerText = Math.floor(start);
                }
            }, stepTime);
        }
    });
}

// ─────────────────────────────────────────
// RUN EVERYTHING WHEN PAGE LOADS
// ─────────────────────────────────────────
document.addEventListener('DOMContentLoaded', function() {
    setupFadeIn();
    autoHideAlerts();
    setupVoteButton();
    highlightActiveNav();
    animateProgressBars();
    animateCounters();

    // Only setup leave warning on vote page
    if (window.location.pathname === '/vote') {
        setupLeaveWarning();
    }

    console.log('✅ SecureVote JS loaded successfully!');
});
