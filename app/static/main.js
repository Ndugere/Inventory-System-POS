document.addEventListener('DOMContentLoaded', function(){
    if(document.getElementById("password-toggle")){
        document.getElementById('password-toggle').addEventListener('click', function(){
            passwordToggle('password', 'password-toggle', 'password-toggle-icon')
        });        
    }
});
// password Toggle
function passwordToggle($fieldId, $toggleId, $iconId){
    const passwordToggle =  document.getElementById($toggleId);
    const passwordField = document.getElementById($fieldId);
    const toggleIcon = document.getElementById($iconId);
    if(passwordField.getAttribute('type') == 'password'){
            const icon = document.createElement('i');
            icon.setAttribute('class', 'fa fa-eye fa-1x');

            passwordField.setAttribute('type', 'text');
            passwordToggle.setAttribute('title', 'Hide');
            passwordToggle.innerHTML = '';
            passwordToggle.appendChild(icon);
    }
    else{
            const icon = document.createElement('i');
            icon.setAttribute('class', 'fa fa-eye-slash fa-1x');

            passwordField.setAttribute('type', 'password');
            passwordToggle.setAttribute('title', 'Show');
            passwordToggle.innerHTML = ''
            passwordToggle.appendChild(icon);
    }
}

// Post
function postData($url, $payload){
    fetch($url)
    .then()
    .then()
    .catch()
}

// Get
function getData($url, $payload){
    fetch($url)
    .then()
    .then()
    .catch()
}