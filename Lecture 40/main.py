from fastapi import FastAPI, HTTPException, Request
from typing import Any
from schemas import UserCreateRequest, PermissionsRequest, UserCreateResponse

app = FastAPI()


@app.get('/')
def root():
    return {'message': 'Welcome to my greatest application'}


@app.get('/users')
async def get_users(limit: int = 5, name: str = 'Jane'):
    users = [
        {'id': 1, 'name': 'John'},
        {'id': 2, 'name': 'Jane'},
        {'id': 3, 'name': 'Jane'},
        {'id': 4, 'name': 'Jane'},
        {'id': 5, 'name': 'Jane'},
        {'id': 6, 'name': 'Jane'},
    ]


    user_with_name = None

    for user in users:
        if user['name'] == name:
            user_with_name = user

    if not user_with_name:
        raise HTTPException(status_code=404, detail='User not found')

    # return users[:limit]
    return user_with_name


@app.post('/users')
async def create_user(data: dict):
    print(data)
    return {'message': 'User created successfully'}


@app.post('/users-any')
async def create_user(data: Any):
    print(data)
    return {'message': 'User created successfully'}


@app.post('/users-request')
async def create_user(data: Request):
    json_obj = await data.json()

    if not 'name' in json_obj.keys():
        return {'error': 'name attribute missing'}

    if not 'password' in json_obj.keys():
        return {'error': 'password attribute missing'}

    print(json_obj)
    return {'message': 'User created successfully'}


@app.post('/users-pydantic', response_model=UserCreateResponse)
async def create_user(data: UserCreateRequest):
    print(data)
    # print(data.name)
    # print(data.age)
    # print(data.email)
    return UserCreateResponse(**data.dict())


@app.post('/permissions')
async def create_permission(data: PermissionsRequest):
    print(data)
    return {'message': 'Permission created successfully'}


@app.put('/users/{user_id}')
async def update_user(user_id: int):
    return {'id': user_id, 'message': 'User updated successfully'}


@app.delete('/users/{user_id}')
async def delete_user(user_id: int):
    return {'id': user_id, 'message': 'User deleted successfully'}

