function onSignIn(googleUser) {
    var profile = googleUser.getBasicProfile();
    console.log('ID: ' + profile.getId()); // Do not send to your backend! Use an ID token instead.
    console.log('Name: ' + profile.getName());
    console.log('Image URL: ' + profile.getImageUrl());
    console.log('Email: ' + profile.getEmail()); // This is null if the 'email' scope is not present.

    $.post('users',
        {token: googleUser.getAuthResponse().id_token,
        email: googleUser.getBasicProfile().getEmail()},
        function (data, status) {
            console.log(data);
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
