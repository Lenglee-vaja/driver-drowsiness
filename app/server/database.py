import motor.motor_asyncio
from bson.objectid import ObjectId
import bcrypt
import jwt
import datetime
import cv2
import numpy as np
import os
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from tensorflow.keras.models import load_model
from pygame import mixer
import json
from jwt import PyJWTError
from fastapi import HTTPException, Security
# from datetime import datetime
from server.models.user import ErrorResponseModel

MONGO_DETAILS = "mongodb+srv://servermark332:RyhXao4ikDIoia0l@cluster0.gpydpey.mongodb.net/driver_drowsiness"

client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_DETAILS)

database = client.driver_drowsiness

user_collection = database.get_collection("user_collection")
logs_collection = database.get_collection("logs_collection")

SECRET_KEY = "bounma@1234-2024"
security = HTTPBearer()


# ===========================================helpers================================

def user_helper(user) -> dict:
    return {
        "id": str(user["_id"]),
        "fullname": user["fullname"],
        "lastname": user["lastname"],
        "phonenumber": user["phonenumber"],
        "email": user["email"],
        "role": user["role"],
       
    }
def logs_helper(logs) -> dict:
    return {
        "id": str(logs["_id"]),
        "user_id": str(logs["user_id"]),
        "fullname": logs["fullname"],
        "lastname": logs["lastname"],
        "phonenumber": logs["phonenumber"],
        "email": logs["email"],
        "score": logs["score"],
        "status": logs["status"],
        "time": logs["time"],
       
    }

# ===========================================detect================================

mixer.init()
sound = mixer.Sound(os.path.join("app/server", "static", "alarm.wav"))

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_eye.xml")
model = load_model(os.path.join("app/server", "models", "models.keras"))

async def detect_eye_state(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, minNeighbors=3, scaleFactor=1.1, minSize=(25, 25))
    eyes = eye_cascade.detectMultiScale(gray, minNeighbors=1, scaleFactor=1.1)
    
    result = {"faces": [], "eyes": [], "status": "", "score": 0}
    
    for (x, y, w, h) in faces:
        result["faces"].append({"x": x, "y": y, "w": w, "h": h})
    
    for (x, y, w, h) in eyes:
        eye = frame[y:y+h, x:x+w]
        eye = cv2.resize(eye, (80, 80))
        eye = eye / 255.0
        eye = eye.reshape(80, 80, 3)
        eye = np.expand_dims(eye, axis=0)
        prediction = model.predict(eye)
        if prediction[0][0] > 0.30:
            result["status"] = "Closed"
            result["score"] += 1
            print("score================>", result["score"])
            if result["score"] > 6:
                sound.play()
        elif prediction[0][1] > 0.70:
            result["status"] = "Open"
            result["score"] -= 1
            if result["score"] < 0:
                result["score"] = 0
        
        result["eyes"].append({"x": x, "y": y, "w": w, "h": h, "prediction": prediction.tolist()})
    
    # return json.dumps(result)
    return "Open"

async def detect_eye_state_one(frame, payload):
    play_sound = "NO"
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, minNeighbors=3, scaleFactor=1.1, minSize=(25, 25))
    eyes = eye_cascade.detectMultiScale(gray, minNeighbors=1, scaleFactor=1.1)
    
    result = {"faces": [], "eyes": [], "status": "", "score": 0}
    
    for (x, y, w, h) in faces:
        result["faces"].append({"x": x, "y": y, "w": w, "h": h})
    
    for (x, y, w, h) in eyes:
        eye = frame[y:y+h, x:x+w]
        eye = cv2.resize(eye, (80, 80))
        eye = eye / 255.0
        eye = eye.reshape(80, 80, 3)
        eye = np.expand_dims(eye, axis=0)
        prediction = model.predict(eye)
        if prediction[0][0] > 0.30:
            result["status"] = "Closed"
            result["score"] += 1
            if result["score"] > 4:
                play_sound = "YES"
                sound.play()
        elif prediction[0][1] > 0.70:
            result["status"] = "Open"
            result["score"] -= 1
            if result["score"] < 0:
                result["score"] = 0
    if play_sound == "YES":
        id = payload["_id"]
        user = await user_collection.find_one({"_id": ObjectId(id)})
        current_time = datetime.datetime.now()
        logs = {    
                    "user_id": user["_id"],
                    "fullname": user["fullname"],
                    "lastname": user["lastname"],
                    "phonenumber": user["phonenumber"],
                    "email": user["email"],
                    "status": result["status"],
                    "score": result["score"],
                    "time": current_time
                }
        data_show =await logs_collection.insert_one(logs)
        print("show data", data_show)
    return play_sound



#===========================auth user===============================


async def register_user(user_data: dict) -> dict:
    user = await user_collection.find_one({"phonenumber": user_data["phonenumber"]})
    if user:
        return {"error": "YES", "code": 400, "message": "PHONE_NUMBER_ALREADY_EXISTS"}
        # raise HTTPException(status_code=400, detail="PHONE_NUMBER_ALREADY_EXISTS")
    user_data['role'] = 'user'
    password = user_data.get("password")
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    user_data["password"] = hashed_password
    user = await user_collection.insert_one(user_data)
    new_user = await user_collection.find_one({"_id": user.inserted_id})
    
    return user_helper(new_user)

async def login_user(login_data: dict) -> dict:
    phone_number = login_data.get("phonenumber")
    password = login_data.get("password")
    
    # Find the user by phone number
    user = await user_collection.find_one({"phonenumber": phone_number})
    
    if not user:
        raise HTTPException(status_code=404, detail="USER_NOT_FOUND")
    if bcrypt.checkpw(password.encode('utf-8'), user["password"]):
        token = generate_jwt_token(user)
        return token, user_helper(user)
    
    raise HTTPException(status_code=401, detail="INVALID_PASSWORD")

def generate_jwt_token(user):
    payload = {
        "_id": str(user["_id"]),
        "role": user["role"],
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24)  # Token expires in 24 hours
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token


def verify_jwt_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except PyJWTError:
        raise HTTPException(status_code=401, detail="INVALID_TOKEN")
    
def verify_jwt_token_and_role(credentials: HTTPAuthorizationCredentials = Security(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        if payload["role"] == "admin":
            return payload
        raise HTTPException(status_code=401, detail="UNAUTHORIZED")
    except PyJWTError:
        raise HTTPException(status_code=401, detail="INVALID_TOKEN")
    

    

#===========================crud user===============================



async def retrieve_users():
    users = []
    async for user in user_collection.find():
        users.append(user_helper(user))
    return users


# Add a new user into to the database
async def add_user(user_data: dict) -> dict:
    user = await user_collection.insert_one(user_data)
    new_user = await user_collection.find_one({"_id": user.inserted_id})
    return user_helper(new_user)
# Retrieve a student with a matching ID
async def retrieve_user(id: str) -> dict:
    user = await user_collection.find_one({"_id": ObjectId(id)})
    if user:
        return user_helper(user)


# Update a student with a matching ID
async def update_user(id: str, data: dict):
    # Return false if an empty request body is sent.
    if len(data) < 1:
        return False
    user = await user_collection.find_one({"_id": ObjectId(id)})
    if user:
        updated_user = await user_collection.update_one(
            {"_id": ObjectId(id)}, {"$set": data}
        )
        if updated_user:
            return True
        return False


# Delete a student from the database
async def delete_user(id: str):
    user = await user_collection.find_one({"_id": ObjectId(id)})
    if user:
        await user_collection.delete_one({"_id": ObjectId(id)})
        return True
    


# ============================================crud logs ===========================================


async def retrieve_logs():
    log_list = []  # Use a different variable name to avoid conflicts
    async for log in logs_collection.find():  # Change 'logs' to 'log' here
        log_list.append(logs_helper(log))  # Append 'logs_helper(log)' to 'log_list'
    return log_list  # Return 'log_list' instead of 'logs'

async def retrieve_log(user_id: str) -> dict:
    print(user_id)
    log = await logs_collection.find_one({"user_id": ObjectId(user_id)})
    if log:
        return logs_helper(log)