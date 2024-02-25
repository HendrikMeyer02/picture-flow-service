import bcrypt, json, jwt, random
from datetime import datetime, timedelta
from fastapi import HTTPException
from redis import asyncio as aioredis


#It is not safe to store passwords as text, 
#but only few people has access to it and soon after presenting 
#I will remove database Redis Cloud account that's why I left it in plain text.
r = aioredis.from_url("redis://default:WvxzTaBH7S13YqrAjrMIPXEW8iIHUQCQ@redis-18108.c299.asia-northeast1-1.gce.cloud.redislabs.com:18108", 
                      decode_responses=True)

secret = "LAWDKAOSKDPOAWKasdka02ri1932ruijidosd098awuqr"

class UserExistsError(Exception):
    def __init__(self, nachricht="Username already exists."):
        self.nachricht = nachricht
        super().__init__(self.nachricht)

class EmailExistsError(Exception):
    def __init__(self, nachricht="User with email already exists."):
        self.nachricht = nachricht
        super().__init__(self.nachricht)

class UserNotFoundError(Exception):
    def __init__(self, nachricht="Unable to find a user."):
        self.nachricht = nachricht
        super().__init__(self.nachricht)

async def adduser(user):
    plain_password = user["password"]
    hashed_password = bcrypt.hashpw(plain_password.encode('utf-8'), bcrypt.gensalt(rounds=12))
    
    with open("./user.json", 'r') as t:
        users = json.load(t)

    for i in users:
        if i["email"] == user["email"]:
            raise UserExistsError("Email already exists")
        elif i["username"] == user["username"]:
            raise UserExistsError("Username already exists")

    users.append({
        "id": await genUserId(),
        "username": user["username"],
        "email": user["email"],
        "password": hashed_password.decode('utf-8')
    })

    with open("./user.json", "w") as l:
        json.dump(users, l, indent=4)

async def checkPassword(password, email):
    user = await getUser(email)
    hashedpw = user["password"]
    return bcrypt.checkpw(password.encode('utf-8'), hashedpw.encode('utf-8'))

#For now it just iterates through all users and checks if the email is in the database
#It is not efficient and will be changed in the future
async def getUser(email):
    usersList = {}
    
    async for key in r.scan_iter("user:*"):
        userData = await r.hgetall(key)
        if userData.get('email') == email:
            usersList = userData
            break
    
    if usersList:
        return usersList
    else:
        raise UserNotFoundError("Unable to find a user with provided email")


async def getUserId(email):
    for key in r.scan_iter("user:*"):
        emailField = r.hget(key, "email")
        if emailField == email:
            return key.split(":")[1]
    raise UserNotFoundError("Unable to find a user with provided email")

async def genToken(email):
    user = await getUser(email)
    hashedpw = bcrypt.hashpw(user["password"].encode('utf-8'), salt=bcrypt.gensalt(rounds=12))
    hashedpw = hashedpw.decode('utf-8')
    return jwt.encode({"pw": hashedpw, "expiry": (datetime.now() + timedelta(days=14)).strftime('%y-%m-%d %H:%M:%S'), "email": email}, secret, algorithm="HS256")

async def checkToken(token):
    decoded = jwt.decode(token, secret, algorithms=["HS256"])
    try:
        user = await getUser(decoded["email"])
    except UserNotFoundError:
        return False
    if bcrypt.checkpw(user["password"].encode('utf-8'), decoded["pw"].encode('utf-8')):
        if datetime.now() < datetime.strptime(decoded["expiry"], '%y-%m-%d %H:%M:%S'):
            return True
    return False

async def checkAuth(request):
    if "auth" in request.headers:
        auth = request.headers["auth"]
        try:
            if await checkToken(auth):
                return True
            else:
                raise HTTPException(status_code=401, detail="Invalid Token", headers={"X-Error": "Invalid Token"})
        except jwt.exceptions.DecodeError:
            raise HTTPException(status_code=401, detail="Invalid Token", headers={"X-Error": "Invalid Token"})
    raise HTTPException(status_code=401, detail="Unauthorized", headers={"X-Error": "Unauthorized"})

async def mailInUse(email, useremail):
    if email == useremail:
        return False
    with open("./user.json", "r") as u:
        users = json.load(u)
        for i in users:
            if i["email"] == email:
                return True
    return False

async def hashPassword(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12))

async def usernameInUse(username, userusername):
    if username == userusername:
        return False
    with open("./user.json", "r") as u:
        users = json.load(u)
        for i in users:
            if i["username"] == username:
                return True
    return False



           
async def genUserId():
    while True:
        userID = random.randrange(100000000000000)
        exists = r.exists(f"user:{userID}")
        if not exists:
            return userID
            
async def getUserFromToken(token):
    decoded = jwt.decode(token, secret, algorithms=["HS256"])
    try:
        user = await getUser(decoded["email"])
        del user["password"]
        return user
    except UserNotFoundError:
        return False