from pexels_api import API
from cryptbackend import adduser, getUserId, UserNotFoundError
from PIL import Image
import requests
import asyncio
from redis import asyncio as aioredis
import aiofiles

async def main():
    r = aioredis.from_url("redis://default:d9VRpwCIqwzvK2vUJFqy81qFAQaqifEp@redis-14795.c302.asia-northeast1-1.gce.cloud.redislabs.com:14795", 
                          decode_responses=True)
    api_key = 'wxrEHmpY8ApoHm230f6qwcYRLGcIavIFzF45j7vl8GasfePaC8HgwovY'
    second_api_key = 'H2jk9uKnhRmL6WPwh89zBezWvr'
    api = API(api_key)
    response = requests.get("https://api.pexels.com/v1/curated?per_page=100", headers={'Authorization': api_key})
    photos = response.json()["photos"]

    for photo in photos:
        email = f'{photo["photographer"].replace(" ", ".")}@bilderfluss.com'
        try:
            userid = await getUserId(email)
        except UserNotFoundError:
            password = "1234"
            username = photo["photographer"]
            user = {"username": username, "email": email, "password": password}
            await adduser(user)
            userid = await getUserId(email)


        picture_id = photo["id"]
        await downloadPicture(photo["src"]["large"], picture_id)
        await r.hset(f'picture:{picture_id}', mapping={
            "author": userid,
            "width": photo["width"],
            "height": photo["height"],
            "description": photo["alt"]
        })

async def downloadPicture(url, picture_id):
    response = requests.get(url)
    image_data = response.content
    filename = f'./pictures/{picture_id}.png'
    async with aiofiles.open(filename, 'wb') as file:
        await file.write(image_data)

if __name__ == "__main__":
    asyncio.run(main())
