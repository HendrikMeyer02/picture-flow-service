##IMplemnt search by username

from fastapi import FastAPI, File, Request, HTTPException, UploadFile
import uvicorn
from cryptbackend import adduser, UserExistsError, checkPassword, genToken, checkAuth, getUserFromToken, mailInUse, hashPassword, usernameInUse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from PIL import Image
import json, os, random, base64
import aiofiles
from redis import asyncio as aioredis

r = aioredis.from_url("redis://default:d9VRpwCIqwzvK2vUJFqy81qFAQaqifEp@redis-14795.c302.asia-northeast1-1.gce.cloud.redislabs.com:14795",
                       decode_responses=True)
app = FastAPI()

origins = [
    "http://localost",
    "http://localhost:5173",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/auth/login", status_code=200)
async def root(request: Request):
    try:
        auth = await request.json()
        email = auth.get("email")
        password = auth.get("password")
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Bad Request", headers={"X-Error": "Bad Request"})
    if not email or not password:
        raise HTTPException(status_code=400, detail="Bad Request", headers={"X-Error": "Bad Request"})

    if await checkPassword(password, email):
        auth_token = await genToken(email)
        return {"AuthToken": auth_token}
    else:
        raise HTTPException(status_code=401, detail="Unauthorized", headers={"X-Error": "Unauthorized"})
    
@app.post("/auth/register", status_code=200)
async def root(request: Request):
    try:
        auth = await request.json()
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Bad Request", headers={"X-Error": "Bad Request"})
    if "email" not in auth or "password" not in auth or "username" not in auth:
            raise HTTPException(status_code=400, detail="Bad Request", headers={"X-Error": "Bad Request"})
    try:
        await adduser(auth)
    except UserExistsError as e:
        raise HTTPException(status_code=400, detail=str(e), headers={"X-Error": str(e)})
    return {"AuthToken": await genToken(auth["email"])}

@app.get("/auth/check",status_code=200)
async def root(request: Request):
    if await checkAuth(request):
        return {"message":"Valid Token"}
    
@app.get("/api/pictures/getpicture")
async def root(request: Request, amount: int = 1):
    await checkAuth(request)

    ret = []
    picture_keys = await r.keys("picture:*")
    
    if len(picture_keys) > 0:
        selected_keys = random.sample(picture_keys, min(len(picture_keys), amount))
        
        pipe = r.pipeline()
        for key in selected_keys:
            pipe.hgetall(key)
        pictures = await pipe.execute()

        for picture_data, key in zip(pictures, selected_keys):
            picture_id = key.split(":")[-1]
            picture_data["id"] = picture_id

            author_id = picture_data["author"]
            picture_data["authorName"] = await getAuthorName(author_id)
            ret.append(picture_data)

    return {"pictures": ret}

    
@app.get("/api/pictures/getpicturesofprofile/{profile_id}")
async def root(request: Request, profile_id):
    await checkAuth(request)
    ret = []
    async for key in r.scan_iter(match=f"picture:*"):
        listpictures = await r.hgetall(key)
        if listpictures["author"] == str(profile_id):
                picture_id = key.split(":")[-1]
                listpictures["id"] = picture_id
                listpictures["authorName"] = await getAuthorName(listpictures["author"])
                ret.append(listpictures)
        return {"pictures": ret}
    
    
#WIP
@app.post("/api/updateProfile")
async def root(request: Request):
    await checkAuth(request)
    user = await getUserFromToken(request.headers["auth"])
    body = await request.json()
    user_id = user['id']
    user_key = f'user:{user_id}'

    if "email" in body and body["email"] != user["email"]:
        if await mailInUse(body["email"], user["email"]):
            raise HTTPException(status_code=400, detail="Email is already in use")
        else:
            await r.hset(user_key, "email", body["email"])

    if "password" in body:
        hashed_password = await hashPassword(body["password"])
        await r.hset(user_key, "password", hashed_password.decode("utf-8"))

    if "username" in body and body["username"] != user["username"]:
        if await usernameInUse(body["username"], user["username"]):
            raise HTTPException(status_code=400, detail="Username is already in use")
        else:
            await r.hset(user_key, "username", body["username"])

    token = await genToken(user['email'])

    return {"AuthToken": token}


@app.get("api/profilepicture/{profile_id}")
async def root(request: Request, profile_id):
    await checkAuth(request)
    await checkProfilePictureExists(profile_id)
    file = f"./pictures/{profile_id}.png"
    return FileResponse(file)

@app.post("/api/profilepicture")
async def root(request: Request, file: UploadFile = File(...)):
    await checkAuth(request)
    if file.filename == "":
        raise HTTPException(400, "File Missing")
    img_recovered = await file.read()
    user = await getUserFromToken(request.headers["auth"])
    picture_id = await editProfilePicture(user["id"], img_recovered)
    return {"picture_id": f"{picture_id}"}
    

@app.get("/api/picture/{picture_id}")
async def root(request: Request, picture_id):
    await checkAuth(request)
    await checkExists(picture_id)
    return FileResponse(f"./pictures/{picture_id}.png")
    
@app.get("/api/getOwnUser")
async def root(request: Request):
    await checkAuth(request)
    return await getUserFromToken(request.headers["auth"])

@app.delete("/api/delpicture/{picture_id}")
async def root(request: Request, picture_id):
    await checkAuth(request)
    user = await getUserFromToken(request.headers["auth"])
    await checkExists(picture_id)
    await checkIsOwnPicture(picture_id, user)
    await deletePicture(picture_id)
    return {"message": "Success"}

@app.post("/api/upload")
async def create_upload_file(request: Request):
    await checkAuth(request)
    body = await request.json()
    if "file" not in body:
        raise HTTPException(400, "File Missing")
    image_as_bytes = base64.b64decode(body["file"]) 
    user = await getUserFromToken(request.headers["auth"])
    description = body.get("description", "")
    picture_id = await genPictureId(r)
    
    picture_path = f"./pictures/{picture_id}.png"
    with open(picture_path, "wb") as f:
        f.write(image_as_bytes)

    img = Image.open(picture_path)
    
    picture_info = {
        "author": str(user["id"]),
        "width": img.width,
        "height": img.height,
        "description": description
    }
    await r.hset(f'picture:{picture_id}', mapping=picture_info)
    await createPicture(user["id"], img.width, img.height, description, picture_id)
    
    return {"picture_id": picture_id}
    
@app.get("api/usernames")
async def getUsernames(request : Request):
    await checkAuth(request)
    usermap = {}
    async for key in r.scan_iter(match=f"user:*"):
        user = await r.hgetall(key)
        usermap.append(user["username"])
    return {"usernames": usermap}
    
async def checkIsOwnPicture(picture_id, user):
    pictures = await r.hgetall(f"picture:{picture_id}")
    if not pictures:
        raise HTTPException(status_code=404, detail="Picture not found")
    if pictures["author"] == str(user["id"]):
        return True
    else:
        raise HTTPException(401, "Unauthorized")

async def genPictureId(r):
    while True:
        picID = random.randrange(100000000)
        exists = await r.exists(f"picture:{picID}")
        if not exists:
            return picID
        
async def getAuthorName(profile_id):
    user_data = await r.hgetall(f'user:{profile_id}')
    return user_data.get('username')

async def checkExists(picture_id):
    exists = await r.exists(f"picture:{picture_id}")
    if not exists or not os.path.isfile(f"./pictures/{picture_id}.png"):
        raise HTTPException(status_code=404, detail="Picture not found", headers={"X-Error": "File not found"})

async def genProfilePictureId():
    while True:
        picID = random.randrange(100000000)
        exists = r.exists(f"profilePic:{picID}")
        if not exists or not os.path.isfile(f"./profilepictures/{picID}.png"):
            return picID

async def checkProfilePictureExists(picture_id):
    exists = await r.exists(f"profilePic:{picture_id}")
    if not exists or not os.path.isfile(f"./profilepictures/{picture_id}.png"):
        raise HTTPException(status_code=404, detail="Picture not found", headers={"X-Error": "File not found"})
           
async def editProfilePicture(profile_id, img_recovered):
    filename = f"{profile_id}.png"
    picture_path = f"./pictures/{filename}"
    
    try:
        async with aiofiles.open(picture_path, "wb") as picture_file:
            await picture_file.write(img_recovered)
    except Exception as e:
        print(e)
        raise HTTPException(500, "Internal Server Error")

    try:
        await r.set(f'profile_picture:{profile_id}', filename)
        return filename
    except Exception as e:
        print(e)
        raise HTTPException(500, "Internal Server Error")

async def deletePicture(picture_id):
    await r.delete(f"picture:{picture_id}")

    pathPicture = f"./pictures/{picture_id}.png"
    if os.path.exists(pathPicture):
        os.remove(pathPicture)


async def createPicture(author, width, height, description, picture_id):
    await r.hset(f"picture:{picture_id}", mapping={
        "author": author,
        "width": str(width), 
        "height": str(height),
        "description": description
    })

