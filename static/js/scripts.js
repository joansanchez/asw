function onSignIn(googleUser) {
    let email = googleUser.getBasicProfile().getEmail();
    let token = googleUser.getAuthResponse().id_token;
    $.post('users',
        {token: token,
        email: email},
        function (data, status) {
            localStorage.setItem('token', token)
            $('#googleButton').text(email)
            $('#googleButton').off()
        });
}

function prepareGoogleSignIn() {
    gapi.load('auth2', function () {
        gapi.auth2.init({
            client_id: '443234130566-cba0cgt2np2alo9e3jhpb7au9hmeptoh.apps.googleusercontent.com',
            cookiepolicy: 'single_host_origin'
        }).attachClickHandler(document.getElementById('googleButton'), {}, onSignIn, function (error) {
            alert(JSON.stringify(error, undefined, 2));
        })
    });
};

prepareGoogleSignIn();
