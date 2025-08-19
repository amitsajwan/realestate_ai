import requests
from utils.jwt_utils import create_jwt_token

async def authenticate_user(username: str, password: str):
    # Regular username/password auth logic
    pass

async def authenticate_facebook_user(facebook_token: str):
    # Verify Facebook token
    facebook_url = f"https://graph.facebook.com/me?access_token={facebook_token}&fields=id,name,email"
    response = requests.get(facebook_url)
    
    if response.status_code != 200:
        return None
        
    facebook_user = response.json()
    
    # Create or find user in your database
    # Generate JWT token
    token = create_jwt_token(facebook_user['id'])
    
    return {"token": token, "user_id": facebook_user['id']}
