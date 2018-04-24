function onSignIn(googleUser) {
    let email = googleUser.getBasicProfile().getEmail();
    let token = googleUser.getAuthResponse().id_token;

    let $form = $('<form>', {
        action: 'login',
        method: 'post'
    });
    $('<input>').attr({
        type: "hidden",
        name: 'token',
        value: token
    }).appendTo($form);
    $('<input>').attr({
        type: "hidden",
        name: 'email',
        value: email
    }).appendTo($form);
    $form.appendTo('body').submit();
}

function prepareSignIn() {
    if (document.getElementById('googleButton')) {
        gapi.load('auth2', function () {
            gapi.auth2.init({
                client_id: '443234130566-cba0cgt2np2alo9e3jhpb7au9hmeptoh.apps.googleusercontent.com',
                cookiepolicy: 'single_host_origin'
            }).attachClickHandler(document.getElementById('googleButton'), {}, onSignIn, function (error) {
                alert(JSON.stringify(error, undefined, 2));
            })
        });
    }
}

prepareSignIn();