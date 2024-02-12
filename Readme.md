Um die Authentication API zu starten müssen folgende Pakete installiert werden:

pip install fastapi\[all\]
pip install pyjwt
pip install bcrypt
pip install pexels-api
pip install pillow

Anschließend mit Hilfe von cd in den backend Ordner navigieren

uvicorn api:app

Startet die API. Diese hört auf den Port 8000.
Syntax zu den API calls:

http://localhost:8000/auth/login

Request body:

{
    "email":"...",
    "password":"..."
}

als return bekommt ihr entweder einen fehler, wenn falsche zugangsdaten oder ein authToken, wenn richtige Zugangsdaten.

Als Test könnt ihr 
{
    "email": "naul.peusel@sap.com",
    "password": "1234"
}
verwenden.
Die register funktion unter

http://localhost:8000/auth/register

nimmt folgenden Request Body:

{
    "username":"...",
    "email":"...",
    "password":"..."
}

auch hier bekommt ihr entweder einen fehler wenn username oder mail schon belegt ist, oder ein authentication token wenn es geklappt hat.

http://localhost:8000/api/pictures/getpicture

benötigt im Header ein Auth Token und liefert anschließend Metadaten über ein Bild mit der Id des Bildes zurück

http://localhost:8000/api/picture/{id}

benötigt im Header ein Auth Token und liefert das zu der ID gehörenden Bild zurück

http://localhost:8000/auth/check 
nimmt ein auth token im header und liefert entweder eine Response mit Valid Token oder eine Response mit Invalid Token zurück, damit könnt ihr also testen, ob das Token noch valide ist

Zu den Auth Tokens: Alle Requests, die nicht /auth/login oder /auth/register sind, müssen im Request Header als auth ein auth token hinzugefügt bekommen. Ist das nicht der fall, wird eine 401 Unauthorized Response geworfen. Die Auth Tokens laufen ab, aktuell ist nach 3 Tagen eingestellt, auch dann muss ein neues Token per /auth/login angefordert werden. Das Token müsst ihr also irgendwie per cookie oder ähnlichem abspeichern.