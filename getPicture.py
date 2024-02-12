from pexels_api import API
from cryptbackend import adduser, getUserId, UserNotFoundError
from PIL import Image
import requests, json, asyncio, os

async def main():
    api_key = 'wxrEHmpY8ApoHm230f6qwcYRLGcIavIFzF45j7vl8GasfePaC8HgwovY'
    second_api_key = 'H2jk9uKnhRmL6WPwh89zBezWvr'
    api = API(api_key)
    photosforjson = []
    r = requests.get("https://api.pexels.com/v1/curated?per_page=100",headers={'Authorization':api_key})
    photos = r.json()["photos"]
    print(r.json())

    for i in photos:
        try:
            userid = await getUserId(f'{i["photographer"].replace(" ", ".")}@bilderfluss.com')
        except UserNotFoundError:
            user = {"username": i["photographer"], "email":f'{i["photographer"].replace(" ", ".")}@bilderfluss.com', "password": "1234"}
            await adduser(user)
            userid = await getUserId(user["email"])
            r = requests.get(f'https://www.pexels.com/en-us/api/v3/users/{i["photographer_id"]}/portfolio', headers={'Secret-Key':second_api_key})
            with open("./profilepictures.json", "r") as j:
                profilepics = json.load(j)
                profilepics[userid] = "pexels-logo.png"
            with open("./profilepictures.json", "w") as j:
                json.dump(profilepics, j, indent=4)
        await downloadPicture(i["src"]["large"], i["id"])
        photosforjson.append({
            i["id"] : {
                "author": str(userid),
                "width": i["width"],
                "height": i["height"],
                "description": i["alt"],
            }
        })
        print("+1")
    with open("./pictures.json", "r") as j:
        picturesjson = json.load(j)
    for i in photosforjson:
        for g in i.keys():
            picturesjson[str(g)] = i[g]
    with open("./pictures.json", "w") as j:
        json.dump(picturesjson, j, indent=4)
       

        

async def downloadPicture(url, id):
    img_data = requests.get(url).content
    with open(f'./pictures/{id}.jpg', 'wb') as handler:
        handler.write(img_data)
    im = Image.open(f'./pictures/{id}.jpg')
    im.save(f'./pictures/{id}.png')
    os.remove(f'./pictures/{id}.jpg')
    


if __name__ == "__main__":
    asyncio.run(main())