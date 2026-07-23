from fastapi import FastAPI, HTTPException

app = FastAPI()


@app.get('/')
def root():
    return {'message': 'Welcome to my greatest application'}


@app.get('/users')
def get_users(limit: int = 5, name: str = 'Jane'):
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
def create_user():
    return {'message': 'User created successfully'}


@app.put('/users/{user_id}')
def update_user(user_id: int):
    return {'id': user_id, 'message': 'User updated successfully'}


@app.delete('/users/{user_id}')
def delete_user(user_id: int):
    return {'id': user_id, 'message': 'User deleted successfully'}

