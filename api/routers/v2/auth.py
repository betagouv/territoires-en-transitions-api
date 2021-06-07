import requests
from fastapi import APIRouter, Response, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from starlette import status
from starlette.responses import JSONResponse

from api.config.configuration import AUTH_KEYCLOAK, AUTH_REALM, AUTH_CLIENT_ID, AUTH_SECRET, AUTH_USER_API
from api.models.pydantic.user_identity import UserIdentity
from api.models.pydantic.user_registration import UserRegistration

router = APIRouter(prefix='/v2/auth')

environment_domains = {
    "app": "https://territoiresentransitions.osc-fr1.scalingo.io",
    "sandbox": "https://sandboxterritoires.osc-fr1.scalingo.io",
    "local": "https://sandboxterritoires.osc-fr1.scalingo.io",
}

token_endpoint = f'{AUTH_KEYCLOAK}/auth/realms/{AUTH_REALM}/protocol/openid-connect/token'
auth_endpoint = f'{AUTH_KEYCLOAK}/auth/realms/{AUTH_REALM}/protocol/openid-connect/auth'
certs_endpoint = f'{AUTH_KEYCLOAK}/auth/realms/{AUTH_REALM}/protocol/openid-connect/certs'
users_endpoint = f'{AUTH_USER_API}/api/users'

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=token_endpoint)


@router.post('/register', response_class=JSONResponse)
async def register(registration: UserRegistration, response: Response):
    """Register a new user"""
    token_parameters = {
        'client_id': AUTH_CLIENT_ID,
        'client_secret': AUTH_SECRET,
        'grant_type': 'client_credentials',
    }
    token_response = requests.post(token_endpoint, data=token_parameters)
    token_json = token_response.json()
    access_token = token_json['access_token']

    headers = {'Authorization': 'Bearer ' + access_token}
    users_response = requests.post(users_endpoint, json=registration.dict(), headers=headers)

    if users_response.ok:
        user_data = users_response.json()
        user_id = user_data['userId']
        requests.put(f'{users_endpoint}/{user_id}/enableCGU', headers=headers)
        return users_response.json()

    response.status_code = token_response.status_code
    return {'content': token_response.content}


@router.get('/token', response_class=JSONResponse)
async def token(code: str, redirect_uri: str, response: Response):
    """Returns a token from an code"""
    parameters = {
        'client_id': AUTH_CLIENT_ID,
        'client_secret': AUTH_SECRET,
        'grant_type': 'authorization_code',
        'redirect_uri': redirect_uri,
        'code': code,
    }
    token_response = requests.post(token_endpoint, parameters)

    if token_response.ok:
        return token_response.json()

    response.status_code = token_response.status_code
    return {'content': token_response.content}


async def get_user_from_header(token: str = Depends(oauth2_scheme)) -> UserIdentity:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    jwk_set = requests.get(certs_endpoint).json()
    try:
        payload = jwt.decode(token, jwk_set)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        user = UserIdentity(id=user_id, firstname='', lastname='', email='')
    except JWTError:
        raise credentials_exception
    return user


@router.get('/identity', response_class=JSONResponse)
async def get_current_user(user: UserIdentity = Depends(get_user_from_header)):
    return user.json()