from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
import teslapy
import zoneinfo
from datetime import datetime, timedelta
from pydantic.dataclasses import dataclass

app = FastAPI()

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:8000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PAC = zoneinfo.ZoneInfo('America/Los_Angeles')


@dataclass
class User:
    def __init__(self, state, code_verifier):
        self.state = state
        self.code_verifier = code_verifier

    state: str
    code_verifier: str


new_users = {}


@app.get("/tesla-url/{username}")
async def get_tesla_url(username: str):
    tesla = teslapy.Tesla(username)
    if not tesla.authorized:
        state = tesla.new_state()
        code_verifier = tesla.new_code_verifier()
        auth_url = tesla.authorization_url(state=state, code_verifier=code_verifier)
        new_user = User(state, code_verifier)
        new_users[username] = new_user
        return auth_url
    tesla.close()


@app.post("/token-from-callback/", status_code=status.HTTP_201_CREATED)
async def get_tesla_token(username: str, url: str):
    current_user = new_users[username]
    tesla = teslapy.Tesla(username, state=current_user.state, code_verifier=current_user.code_verifier)
    if not tesla.authorized:
        tesla.fetch_token(authorization_response=url)
    tesla.close()
    new_users.pop(username)
    return 201


@app.post("/token/")
async def get_token_v1(username: str):

    with teslapy.Tesla(username) as tesla:
        # print(tesla.authorization_url())
        # print(tesla.redirect_uri)
        response = tesla.fetch_token()

    expires_at = datetime.fromtimestamp(response['expires_at'], tz=PAC)
    access_token = response['access_token']
    # print outputs to screen
    print('[tesla]')
    print('access_token=' + access_token)
    print('refresh_token=' + response['refresh_token'])
    print(
        'created_at=' + datetime.strftime(expires_at - timedelta(seconds=response['expires_in']), '%Y-%m-%d %H:%M:%S'))
    print('expires_at=' + datetime.strftime(expires_at, '%Y-%m-%d %H:%M:%S'))

    return access_token


@app.get("/vehicles/{username}")
async def get_vehicles(username: str):
    with teslapy.Tesla(username) as tesla:
        vehicles = tesla.vehicle_list()
        return vehicles


@app.post("/vehicle/honk")
async def honk_horn(username: str):
    with teslapy.Tesla(username) as tesla:
        vehicles = tesla.vehicle_list()
        vehicles[0].sync_wake_up()
        try:
            vehicles[0].command('HONK_HORN')
        except teslapy.HTTPError as e:
            print(e)


@app.post("/vehicle/lights")
async def flash_lights(username: str):
    with teslapy.Tesla(username) as tesla:
        vehicles = tesla.vehicle_list()
        vehicles[0].sync_wake_up()
        try:
            vehicles[0].command('FLASH_LIGHTS')
        except teslapy.HTTPError as e:
            print(e)


@app.post("/vehicle/trunk")
async def open_trunk(username: str, location: str):
    with teslapy.Tesla(username) as tesla:
        vehicles = tesla.vehicle_list()
        if len(vehicles) < 1:
            return 404
        else:
            vehicles[0].sync_wake_up()
            # rear or front
            try:
                vehicles[0].command('ACTUATE_TRUNK', which_trunk=location)
            except teslapy.HTTPError as e:
                print(e)


@app.get("/vehicle/data/{username}")
async def get_vehicle_data(username: str):
    with teslapy.Tesla(username) as tesla:
        vehicles = tesla.vehicle_list()
        if len(vehicles) < 1:
            return 404
        else:
            vdata = vehicles[0].get_vehicle_data()
            return vdata
