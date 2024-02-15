Authentication API - Picture-Flow
To start the Authentication API for the Picture-Flow project, follow these steps:

Prerequisites
Install the required Python packages:

```
pip install fastapi[all]
pip install pyjwt
pip install bcrypt
pip install pexels-api
pip install pillow
```
Navigate to the backend directory using the following command:


Start the API using Uvicorn:

```
uvicorn api:app --reload
```
The API will be available at http://localhost:8000.

API Calls
1. Login
Endpoint: http://localhost:8000/auth/login
Request body:
json
Copy code
{
    "email": "...",
    "password": "..."
}
Response:
If incorrect credentials: Error message
If successful: Authentication token
Example test credentials:

json
Copy code
{
    "email": "naul.peusel@sap.com",
    "password": "1234"
}

2. Register
Endpoint: http://localhost:8000/auth/register
Request body:
json
Copy code
{
    "username": "...",
    "email": "...",
    "password": "..."
}
Response:
If username or email is already taken: Error message
If successful: Authentication token

3. Get Picture Metadata
Endpoint: http://localhost:8000/api/pictures/getpicture
Headers: Include "Auth-Token" with the authentication token
Response: Metadata about a picture with the specified ID

4. Get Picture by ID
Endpoint: http://localhost:8000/api/picture/{id}
Headers: Include "Auth-Token" with the authentication token
Response: The picture corresponding to the provided ID

5. Check Token Validity
Endpoint: http://localhost:8000/auth/check
Headers: Include "Auth-Token" with the authentication token
Response:
If valid token: Response with "Valid Token"
If invalid token: Response with "Invalid Token"
Note on Auth Tokens
All requests, except /auth/login and /auth/register, must include an "Auth-Token" in the request header. Failure to do so results in a 401 Unauthorized response.
Auth tokens expire; currently set to 3 days. After expiration, obtain a new token using /auth/login.
Save the token using cookies or a similar method for subsequent requests.
