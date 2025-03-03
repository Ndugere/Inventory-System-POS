document.addEventListener('DOMContentLoaded', function () {
    const loadingModal = new bootstrap.Modal(document.getElementById("loadingModal"));
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
                showLoading(loadingModal, true);
                const formData = new FormData(loginForm);
                postData('/login', Array.from(formData.entries()), loadingModal);
                /**
                setTimeout(function () {
                    showLoading(loadingModal, false);
                }, 10000);*/
            });
        }
    }
});

// ✅ Improved Password Toggle Function
function passwordToggle(fieldId, toggleId, iconId) {
    const passwordField = document.getElementById(fieldId);
    const passwordToggle = document.getElementById(toggleId);
    const toggleIcon = document.getElementById(iconId);

    if (passwordField.type === 'password') {
        passwordField.type = 'text';
        passwordToggle.title="Hide";
        toggleIcon.classList.remove('fa-eye-slash');
        toggleIcon.classList.add('fa-eye');
    } else {
        passwordField.type = 'password';
        passwordToggle.title="Show";
        toggleIcon.classList.remove('fa-eye');
        toggleIcon.classList.add('fa-eye-slash');
    }
}

// ✅ Bootstrap Modal Instance (Initialized Once)

function showLoading(modal, state) {
    if (state) {
        modal.show();
    } else {
        modal.hide();
    }
}

// ✅ Improved `postData` Function (Handles Response)
function postData(url, payload, modal) {
    fetch(url, {
        headers: {
            'Content-Type': 'Application/json',
        },
        method: "POST",
        body: JSON.stringify(payload),
    })
    .then(response =>{
        if(response.ok){
            return response.json();
        }
        throw new Error(response);
        
    })
    .then(result =>{
        alert(result);
    })
    .catch(error => {
        showLoading(modal, false)
        console.log(error);

    })
}

// ✅ Improved `getData` Function (Handles Response)
async function getData(url) {
    try {
        const response = await fetch(url);

        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }

        return await response.json(); // Process response JSON
    } catch (error) {
        console.error("Error fetching data:", error);
    }
}
