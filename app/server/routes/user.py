from fastapi import APIRouter, Body, WebSocket, FastAPI, File, UploadFile, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field

import base64
import numpy as np
import cv2

from server.database import (
    add_user,
    login_user,
    delete_user,
    retrieve_users,
    retrieve_user,
    update_user,
    register_user,
    detect_eye_state_one,
    verify_jwt_token,
    verify_jwt_token_and_role,
    retrieve_logs,
    retrieve_log
)
from server.models.user import (
    ErrorResponseModel,
    ResponseModel,
    ResponseModels,
    ResponseLogin,
    UserSchema,
    UserLoginSchema,
    UpdateUserModel,
)

router = APIRouter()


@router.post("/", response_description="User data added into the database")
async def add_student_data(user: UserSchema= Body(...), payload: dict = Depends(verify_jwt_token_and_role)):
    print("payload===================>", payload)
    user = jsonable_encoder(user)
    new_user = await add_user(user)
    return ResponseModel(new_user, "User added successfully.")


@router.post("/register", response_description="register into the database")
async def register_user_data(user: UserSchema= Body(...)):
    user = jsonable_encoder(user)
    new_user = await register_user(user)
    if "error" in new_user and new_user["error"] == "YES":
        return ErrorResponseModel(new_user["error"] ,new_user["code"], new_user["message"])
    return ResponseModel(new_user, "SUCCESSFULLY")

@router.post("/login", response_description="user login")
async def login_user_data(user: UserLoginSchema= Body(...)):
    user = jsonable_encoder(user)
    token, user_data = await login_user(user)
    return ResponseLogin(user_data,token, "SUCCESSFULLY")

@router.post("/detect", response_description="Predict eye state")
async def predict_eye_state(file: UploadFile = File(...), payload: dict = Depends(verify_jwt_token)):
    # Read the image file
    contents = await file.read()
    np_arr = np.fromstring(contents, np.uint8)
    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    
    # Perform eye state detection
    result = await detect_eye_state_one(frame, payload)
    
    # Return the result as JSON
    return ResponseModel(result, "SUCCESSFULLY")


@router.get("/logs", response_description="logs retrieved")
async def retrieve_many_logs(payload: dict = Depends(verify_jwt_token_and_role)):
    logs = await retrieve_logs()
    return ResponseModels(logs, "SUCCESSFULLY")

@router.get("/log/{id}", response_description="log retrieved")
async def retrieve_one_log(id, payload: dict = Depends(verify_jwt_token)):
    log = await retrieve_log(id)
    if log:
        return ResponseModel(log, "SUCCESSFULLY")
    return ErrorResponseModel("ERROR", 404, "STUDENT_NOT_FOUND")



@router.get("/users", response_description="user many retrieved")
async def retrieve_many_users(payload: dict = Depends(verify_jwt_token_and_role)):
    users = await retrieve_users()
    return ResponseModels(users, "SUCCESSFULLY")


@router.get("/user/{id}", response_description="user retrieved")
async def retrieve_one_user(id, payload: dict = Depends(verify_jwt_token)):
    user = await retrieve_user(id)
    if user:
        return ResponseModel(user, "SUCCESSFULLY")
    return ErrorResponseModel("ERROR", 404, "USER_NOT_FOUND")