import requests
from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from starlette.responses import JSONResponse

from api.config.configuration import AUTH_KEYCLOAK, AUTH_REALM, AUTH_CLIENT_ID, AUTH_SECRET

router = APIRouter(prefix='/v2/auth')

environment_domains = {
    "app": "https://territoiresentransitions.osc-fr1.scalingo.io",
    "sandbox": "https://sandboxterritoires.osc-fr1.scalingo.io",
    "local": "https://sandboxterritoires.osc-fr1.scalingo.io",
}


@router.post('/{environment}/register', response_class=HTMLResponse)
async def register(environment: str):
    """todo: call users API"""
    pass


@router.get('/{environment}/token', response_class=JSONResponse)
async def token(environment: str, code: str):
    """Returns a token from an code"""
    token_endpoint = f'{AUTH_KEYCLOAK}/auth/realms/{AUTH_REALM}/protocol/openid-connect/token'
    parameters = {
        'client_id': AUTH_CLIENT_ID,
        'client_secret': AUTH_SECRET,
        'grant_type': 'client_credentials',
        'code': code,
    }
    response = requests.post(token_endpoint, parameters)
    return response.json()
