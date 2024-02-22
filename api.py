from fastapi import FastAPI, Request, HTTPException, UploadFile
from cryptbackend import adduser, UserExistsError, checkPassword, genToken, checkAuth, getUserFromToken, mailInUse, hashPassword, usernameInUse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from PIL import Image
import json, os, random, base64

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
    with open("./user.json", "r") as t:
        users = json.load(t)
        try:
            auth = await request.json()
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Bad Request", headers={"X-Error": "Bad Request"})
        if "email" not in auth or "password" not in auth:
            raise HTTPException(status_code=400, detail="Bad Request", headers={"X-Error": "Bad Request"})
        for i in users:
            if(i["email"] == auth["email"] and await checkPassword(auth["password"], auth["email"])):
                return {"AuthToken": await genToken(auth["email"])}
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
    with open("./pictures.json", "r") as t:
        listpictures = list(json.load(t).items())
        for i in range(0,amount):
            l = random.choice(listpictures)
            listpictures.remove(l)
            g = l[1]
            g["id"] = l[0]
            g["authorName"] = await getAuthorName(g["author"])
            ret.append(g)
        return {"pictures": ret}
    
@app.get("/api/pictures/getpicturesofprofile/{profile_id}")
async def root(request: Request, profile_id):
    await checkAuth(request)
    ret = []
    with open("./pictures.json", "r") as t:
        listpictures = list(json.load(t).items())
        for i in listpictures:
            if(i[1]["author"] == str(profile_id)):
                g = i[1]
                g["id"] = i[0]
                g["authorName"] = await getAuthorName(g["author"])
                ret.append(g)
        return {"pictures": ret}
    
    
#WIP
@app.post("/api/updateProfile")
async def root(request: Request):
    await checkAuth(request)
    user = (await getUserFromToken(request.headers["auth"]))
    body = await request.json()
    with open("./user.json", "r") as u:
        users = json.load(u)
    for i in users:
        if i["id"] == user["id"]:
            savedUser = i
    if "email" in body:
        if not await mailInUse(body["email"], user["email"]):
            savedUser["email"] = body["email"]
    if "password" in body:
        savedUser["password"] = await hashPassword(body["password"])
        savedUser["password"] = savedUser["password"].decode("utf-8")
    if "username" in body:
        if not await usernameInUse(body["username"], user["username"]):
            savedUser["username"] = body["username"]
    for i in users:
        if savedUser["id"] == i["id"]:
            i = savedUser
    with open("./user.json", "w") as u:
        json.dump(users, u, indent=4)
    token = await genToken(savedUser["email"])
    return {"AuthToken":token}

@app.get("api/profilepicture/{profile_id}")
async def root(request: Request, profile_id):
    await checkAuth(request)
    await checkProfilePictureExists(profile_id)
    filename = await getProfilePicturePath(profile_id)
    return FileResponse(f"./pictures/{filename}")

@app.post("api/profilepicture")
async def root(request: Request):
    await checkAuth(request)
    body = await request.json()
    if "file" not in body:
        raise HTTPException(400, "File Missing")
    image_as_bytes = str.encode(body["file"])  # convert string to bytes
    img_recovered = base64.b64decode(image_as_bytes)
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
    image_as_bytes = str.encode(body["file"])  # convert string to bytes
    img_recovered = base64.b64decode(image_as_bytes)
    user = await getUserFromToken(request.headers["auth"])
    description = ""
    if "description" in body:
        description = body["description"]
    picture_id = await genPictureId()
    with open(f"./pictures/{picture_id}.png", "wb") as f:
        f.write(img_recovered)
    img = Image.open(f"./pictures/{picture_id}.png")
    await createPicture(str(user["id"]), img.width, img.height, description, picture_id)
    
    return {"picture_id": f"{picture_id}"}
    
    
async def checkIsOwnPicture(picture_id, user):
    with open("./pictures.json", "r") as l:
        pictures = json.load(l)
        if pictures[picture_id]["author"] == str(user["id"]):
            return True
        else:
            raise HTTPException(401, "Unauthorized")

async def genPictureId():
    with open("./pictures.json", "r") as t:
        l = json.load(t)
        while True:
            t = random.randrange(100000000000000)
            if str(t) not in l:
                return t
        
async def getAuthorName(profile_id):
    with open("./user.json", "r") as t:
        users = json.load(t)
        for i in users:
            if str(i["id"]) == profile_id:
                return i["username"]

async def checkExists(picture_id):
    with open("./pictures.json", "r") as t:
        l = json.load(t)
        if not picture_id in l or not os.path.isfile(f"./pictures/{picture_id}.png"):
            raise HTTPException(status_code=404, detail="Picture not found", headers={"X-Error": "File not found"})

async def genProfilePictureId():
    with open("./profilepictures.json", "r") as t:
        l = json.load(t)
        while True:
            t = random.randrange(100000000000000)
            if str(t) not in l:
                return t
            
async def getProfilePicturePath(user_id):
    with open("./profilepictures.json", "r") as t:
        l = json.load(t)
        return l[str(user_id)]
        

async def checkProfilePictureExists(picture_id):
    with open("./profilepictures.json", "r") as t:
        l = json.load(t)
        if not picture_id in l or not os.path.isfile(f"./profilepictures/{picture_id}.png"):
            raise HTTPException(status_code=404, detail="Picture not found", headers={"X-Error": "File not found"})
       
async def editProfilePicture(profile_id):
    filename = f"{profile_id}.png"
    picture_path = f"./pictures" + filename
    with open(picture_path, "wb") as picture_file:
        picture_file.write(await FileResponse(f"./pictures/{filename}"))
    with open("profile_picture.json", "r") as json_file:
        profile_picture_data = json.load(json_file)
    profile_picture_data[profile_id] = filename
    with open("profile_picture.json", "w") as json_file:
        json.dump(profile_picture_data, json_file) 
    return f"{profile_id}.png"

async def deletePicture(picture_id):
    with open("./pictures.json", "r") as f:
        l = json.load(f)
        del l[picture_id]
    with open("./pictures.json", "w") as t:
        json.dump(l, t, indent=4)
    os.remove(f"./pictures/{picture_id}.png")


async def createPicture(author, width, heigth, description, picture_id):
    new_picture = {
        "author" : author,
        "width" : width,
        "heigth" : heigth,
        "description" : description
    }
    with open ("./pictures.json", "r") as f:
        l = json.load(f)
        l[picture_id] = new_picture
    with open("./pictures.json", "w") as t:
        json.dump(l,t,indent=4)

