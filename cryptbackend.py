import bcrypt, json, jwt, random
from datetime import datetime, timedelta
from fastapi import HTTPException
from redis import asyncio as aioredis
from cachetools import TTLCache



#It is not safe to store passwords as text, 
#but only few people has access to it and soon after presenting 
#I will remove database Redis Cloud account that's why I left it in plain text.
r = aioredis.from_url("redis://default:d9VRpwCIqwzvK2vUJFqy81qFAQaqifEp@redis-14795.c302.asia-northeast1-1.gce.cloud.redislabs.com:14795", 
                      decode_responses=True)

secret = "LAWDKAOSKDPOAWKasdka02ri1932ruijidosd098awuqr"
token_cache = TTLCache(maxsize=1024, ttl=300)


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
    existing_user_id = await r.get(f"email_to_id:{user['email']}")
    if existing_user_id:
        raise HTTPException(status_code=400, detail="Email already exists")

    plain_password = user["password"]
    hashed_password = bcrypt.hashpw(plain_password.encode('utf-8'), bcrypt.gensalt(rounds=12))

    user_id = await genUserId()

    await r.hset(f"user:{user_id}", mapping={
        "id": user_id,
        "username": user["username"],
        "email": user["email"],
        "password": hashed_password.decode('utf-8')
    })

    await r.set(f"email_to_id:{user['email']}", user_id)

async def checkPassword(password, email):
    user = await getUser(email)
    hashedpw = user["password"]
    return bcrypt.checkpw(password.encode('utf-8'), hashedpw.encode('utf-8'))


async def getUser(email):
    user_id = await r.get(f"email_to_id:{email}")
    if user_id:
        userData = await r.hgetall(f"user:{user_id}")
        return userData
    else:
        raise UserNotFoundError("Unable to find a user with provided email")


async def getUserId(email):
    async for key in r.scan_iter("user:*"):
        email_field = await r.hget(key, "email")
        if email_field == email:
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
        if auth in token_cache:
            return True
        try:
            if await checkToken(auth):
                token_cache[auth] = True
                return True
            else:
                raise HTTPException(status_code=401, detail="Invalid Token", headers={"X-Error": "Invalid Token"})
        except jwt.exceptions.DecodeError as e:
            raise HTTPException(status_code=401, detail=str(e), headers={"X-Error": str(e)})
    raise HTTPException(status_code=401, detail="Unauthorized", headers={"X-Error": "Unauthorized"})

async def mailInUse(email, current_email):
    if email == current_email:
        return False
    exists = await r.exists(f"email_to_id:{email}")
    return bool(exists)

async def hashPassword(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12))

async def usernameInUse(username, current_username):
    if username == current_username:
        return False
    exists = await r.exists(f"username_to_id:{username}")
    return exists



           
async def genUserId():
    while True:
        userID = random.randrange(100000000000000)
        exists = await r.exists(f"user:{userID}")
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