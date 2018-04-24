from google.auth.transport import requests
from google.oauth2 import id_token


def validate_token(username_token):
    # Specify the CLIENT_ID of the app that accesses the backend:
    client_id = '443234130566-cba0cgt2np2alo9e3jhpb7au9hmeptoh.apps.googleusercontent.com'
    id_info = id_token.verify_oauth2_token(username_token, requests.Request(), client_id)

    if id_info['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
        raise ValueError('Wrong issuer.')

    # ID token is valid. Get the user's Google Account ID from the decoded token.
    user_id = id_info['sub']
    return user_id
