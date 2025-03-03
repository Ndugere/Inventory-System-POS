document.addEventListener('DOMContentLoaded', function () {
    //const loadingModal = new bootstrap.Modal(document.getElementById("loadingModal"));
    const overlay = document.getElementById("loadingOverlay");
    const loginForm = document.getElementById("login-form");

    if (loginForm) {
        const passwordToggleBtn = document.getElementById('password-toggle');
        const loginBtn = document.getElementById('login-btn');

        if (passwordToggleBtn) {
            passwordToggleBtn.addEventListener('click', function () {
                passwordToggle('password', 'password-toggle', 'password-toggle-icon');
            });
        }

        if (loginBtn) {
            loginBtn.addEventListener('click', function (e) {
                e.preventDefault();
                showLoading(overlay, true);

                const formData = new FormData(loginForm);
                const csrfToken = getCookie('csrftoken');

                fetch('/login', {
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken,
                    },
                    method: "post",
                    body: JSON.stringify(Object.fromEntries(formData.entries())),
                })
                .then(response => {
                    if (!response.ok) {
                        return response.json().then(err => {
                            throw new Error(err.error || "Something went wrong");
                        });
                    }
                    return response.json();
                })
                .then(results => {
                    document.querySelector('#dots').innerHTML = `<p>${results.data.message}</p>`;
                    setTimeout(() => {
                        window.location.href = results.data.redirect_url;
                    }, 3000);
                })
                .catch(error => {
                    setTimeout(() => {
                        showLoading(overlay, false);
                        document.querySelector('#error-message').innerHTML = `<p class='tw-text-red-500 tw-font-semibold tw-bg-white tw-p-2 tw-rounded-xl tw-text-sm'>
                            ⚠️ Oops! Login failed. Please check your email and password and try again.
                        </p>`;
                    }, 3000);
                });
            });
        }
    }
});

function passwordToggle(fieldId, toggleId, iconId) {
    const passwordField = document.getElementById(fieldId);
    const passwordToggle = document.getElementById(toggleId);
    const toggleIcon = document.getElementById(iconId);

    if (passwordField.type === 'password') {
        passwordField.type = 'text';
        passwordToggle.title = "Hide";
        toggleIcon.classList.remove('fa-eye-slash');
        toggleIcon.classList.add('fa-eye');
    } else {
        passwordField.type = 'password';
        passwordToggle.title = "Show";
        toggleIcon.classList.remove('fa-eye');
        toggleIcon.classList.add('fa-eye-slash');
    }
}

function showLoading(overlay, state) {    
    if (state) {
        overlay.hidden = false;
    } else {
        overlay.hidden = true;
    }
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
        let cookies = document.cookie.split(";");
        for (let i = 0; i < cookies.length; i++) {
            let cookie = cookies[i].trim();
            if (cookie.startsWith(name + "=")) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
