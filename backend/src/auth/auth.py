import json
from flask import request, _request_ctx_stack, abort
from functools import wraps
from urllib.request import urlopen
from jose import jwt


AUTH0_DOMAIN = 'dev-1ffyv1sf.us.auth0.com'
ALGORITHMS = ['RS256']
API_AUDIENCE = 'coffee'

## AuthError Exception
'''
AuthError Exception
A standardized way to communicate auth failure modes
'''
class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code

def get_token_auth_header():
    """Split and get token """
    if 'Authorization' not in request.headers:
        raise AuthError({
            'code': 'authorization header is missing',
            'description': 'Authorization is exepected'
        }, 401)
       

    auth_header = request.headers['Authorization']
    header_parts = auth_header.split()
    
    if len(header_parts) !=2:
         raise AuthError({
            'code': 'invalid header',
            'description': 'Authorization header must be bearer token.'
        }, 401)

    elif header_parts[0].lower() != 'bearer':
         raise AuthError({
            'code': 'invalid_header',
            'description': 'Authorization header should start with "Bearer"'
        }, 401)
    return header_parts[1]


def check_permissions(permission, payload):
    if 'permissions'not in payload:
        abort(403)

    if permission not in payload['permissions']:
        abort(403)

    return True
    

'''
@TODO implement verify_decode_jwt(token) method
    @INPUTS
        token: a json web token (string)

    it should be an Auth0 token with key id (kid)
    it should verify the token using Auth0 /.well-known/jwks.json
    it should decode the payload from the token
    it should validate the claims
    return the decoded payload

    !!NOTE urlopen has a common certificate error described here: https://stackoverflow.com/questions/50236117/scraping-ssl-certificate-verify-failed-error-for-http-en-wikipedia-org
'''
def verify_decode_jwt(token):
    jsonurl = urlopen(f'https://{AUTH0_DOMAIN}/.well-known/jwks.json')
    jwks = json.loads(jsonurl.read())
    unverified_header = jwt.get_unverified_header(token)
    rsa_key= {}
    if 'kid' not in unverified_header:
        raise AuthError({'code': 'invalid_header',
        'description': 'Authorization malformed.'}, 401)
    for key in jwks['keys']:
        if key['kid'] == unverified_header['kid']:
            rsa_key = {
                'kty': key['kty'],
                'kid': key['kid'],
                'use': key['use'],
                'n': key['n'],
                'e': key['e']
            }
        if rsa_key:
            try:
                payload = jwt.decode(
                    token,
                    rsa_key,
                    algorithms = ALGORITHMS,
                    audience = API_AUDIENCE,
                    issuer = 'https://' + AUTH0_DOMAIN + '/'
                )

                return payload
            except jwt.ExpiredSignatureError:
                raise AuthError({
                    'code': 'token_expired',
                    'description': 'Token expired'
                }, 401)

            except jwt.JWTClaimsError:
                raise AuthError({
                    'code': 'invalid_claims',
                    'description': 'Incorrect claims, please check the audience and issuer'
                }, 401)

            except Exception:
                raise AuthError({
                    'code': 'inavlid_header',
                    'description': 'unable to parse authentication'
                }, 400)
            
        raise AuthError({
                    'code': 'invalid_header',
                    'description': 'Unable to find the appropriate '
                }, 400)

def requires_auth(permission=''):
    def requires_auth_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            token = get_token_auth_header()
            try:
                payload = verify_decode_jwt(token)
            except:
                abort(401)
            check_permissions(permission, payload)
            return f(payload, *args, **kwargs)

        return wrapper
    return requires_auth_decorator