
from fastapi import FastAPI


from fastapi.middleware.cors import CORSMiddleware
import os

from fastapi import Request
from fastapi.responses import JSONResponse
from keycloak import KeycloakOpenID
from starlette.middleware.base import BaseHTTPMiddleware, \
    RequestResponseEndpoint
from starlette.responses import Response

KEYCLOAK_OPENID = KeycloakOpenID(
    server_url=os.getenv('KEYCLOAK_URL', None),
    client_id=os.getenv('CLIENT_ID', None),
    realm_name=os.getenv('REALM', None),
)
the_user = None

class AuthMiddleware(BaseHTTPMiddleware):
    """

    This code defines an AuthMiddleware class that extends BaseHTTPMiddleware
    to handle authentication for incoming HTTP requests. It checks if the
    request URL is in a predefined list of paths that do not require
    authentication. If the URL is not in this list, it verifies the
    presence of a valid API key in the request headers before allowing
    the request to proceed.

     """
    __jump_paths__ = ['/docs', '/openapi.json', '/redoc',
                      '/health', '/favicon.ico', ]

    __name__api_key__ = 'API_KEY'
    __auth__ = 'authorization'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @staticmethod
    def unauthorised(
            code: int = 401, msg: str = 'Unauthorised') -> JSONResponse:
        """
            Return a message of unauthorised
        """
        return JSONResponse(status_code=code, content=msg)

    def _is_jump_url_(self, request: Request) -> bool:
        return request.url.path in self.__jump_paths__

    def decode_token(self, token: str):
        token_ = token.replace('Bearer ', '')
        payload = KEYCLOAK_OPENID.decode_token(token_)
        global the_user
        the_user = payload
        return payload

    def get_header_token(self, request: Request):
        return request.headers.get(self.__auth__, '')

    def get_user_config(self, request: Request) -> dict:
        token = self.get_header_token(request)
        try:
            decode_token = self.decode_token(token)
            return decode_token
        except Exception:
            return {}

    def is_auth(self, request: Request) -> dict:
        """
        queda por implementar
        :param request:
        :return:
        """
        return self.get_user_config(request)

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """
        The dispatch method in the AuthMiddleware class is an asynchronous
        middleware function that processes incoming HTTP requests.
        It checks if the request URL is in a predefined list of paths
        that do not require authentication. If the URL is not in this
        list, it verifies the presence of a valid API key in the request
         headers before allowing the request to proceed.

        :param request:  An instance of Request representing the incoming
            HTTP request.
        :param call_next: A callable (RequestResponseEndpoint) that processes
            the next middleware or the actual request handler

        :return: Returns a Response object, either from the next
            middleware/request handler or an unauthorized response.
        """
        if self._is_jump_url_(request):
            return await call_next(request)

        response = self.unauthorised()

        if len(self.is_auth(request)) > 0:
            response = await call_next(request)

        return response

app = FastAPI()

app.add_middleware(AuthMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/protected")
def read_protected(message: str = 'probe'):
    return {"message": message + "Received", "user": the_user}


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app=app, host="localhost", port=8000)
