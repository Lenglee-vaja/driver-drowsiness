from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
import json
from server.routes.user import router as UserRouter
from server.database import detect_eye_state

import base64
import numpy as np
import cv2
app = FastAPI()
# Include CORS middleware
# CORS settings
origins = [
    "http://localhost",
    "http://localhost:5173/",  # Adjust this to your actual frontend origin
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],  # Include WebSocket methods if needed
    allow_headers=["Authorization", "Content-Type"],
)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        try:
            data = await websocket.receive_text()
            print("received data")
            image_data = base64.b64decode(data)
            np_arr = np.fromstring(image_data, np.uint8)
            frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            
            result = await detect_eye_state(frame)
            
            # await websocket.send_text(json.dumps(result))
            await websocket.send_text(result)
        except Exception as e:
            print(f"WebSocket error: {e}")
            await websocket.close()
            break

app.include_router(UserRouter, tags=["User"], prefix="/user")


@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to  Driver Drowsiness Detection Website"}