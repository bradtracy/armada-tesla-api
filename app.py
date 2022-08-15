from fastapi import FastAPI
import teslapy
import zoneinfo
from datetime import datetime, timedelta
from pydantic import BaseModel

app = FastAPI()
PAC = zoneinfo.ZoneInfo('America/Los_Angeles')


class User(BaseModel):
    email: str
    pw: str


@app.post("/token/")
async def get_token(user: User):
    print(user.email)
    print(user.pw)

    with teslapy.Tesla(user.email) as tesla:
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


@app.post("/vehicles/")
async def get_vehicles(user: User):
    with teslapy.Tesla(user.email) as tesla:
        vehicles = tesla.vehicle_list()
        # vehicles[0].sync_wake_up()
        # vehicles[0].command('ACTUATE_TRUNK', which_trunk='front')
        # vehicles[0].get_vehicle_data()
        # print(vehicles[0]['vehicle_state']['car_version'])
        return vehicles


