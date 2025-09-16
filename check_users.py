import sys
import os
sys.path.insert(0, os.path.dirname(__file__) + '/backend')

import asyncio
from app.core.database import get_database

async def check_users():
    db = get_database()
    users = await db.users.find({}).to_list(10)
    print(f'Found {len(users)} users:')
    for user in users:
        print(f'  - {user.get("email")}: {user.get("id")}')

if __name__ == "__main__":
    asyncio.run(check_users())