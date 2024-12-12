// js/cookie-consent.js

document.addEventListener('DOMContentLoaded', function () {
    const cookieConsent = document.createElement('div');
    cookieConsent.id = 'cookie-consent';
    cookieConsent.innerHTML = `
        <div class="cookie-banner">
            <p>${window.mkdocsConfig.extra.consent.description}</p>
            <button id="accept-cookies">${window.mkdocsConfig.extra.consent.actions[0]}</button>
            <button id="manage-cookies">${window.mkdocsConfig.extra.consent.actions[1]}</button>
        </div>
    `;
    document.body.appendChild(cookieConsent);

    // Cookie Consent Acceptance
    const acceptButton = document.getElementById('accept-cookies');
    acceptButton.addEventListener('click', function () {
        Cookies.set('cookie-consent', 'accepted', { expires: 365 });
        cookieConsent.style.display = 'none';
    });

    // Cookie Consent Management
    const manageButton = document.getElementById('manage-cookies');
    manageButton.addEventListener('click', function () {
        // You can implement your cookie management logic here
        alert('Manage your cookie settings.');
    });

    // Check if the user has already accepted cookies
    if (Cookies.get('cookie-consent') === 'accepted') {
        cookieConsent.style.display = 'none';
    }
});
