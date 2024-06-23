from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserSchema(BaseModel):
    fullname : str = Field(...)
    lastname: str = Field(...)
    phonenumber: str = Field(...)
    email: EmailStr = Field(...)
    password:str = Field(...)

class UserLoginSchema(BaseModel):
    phonenumber: str = Field(...)
    password:str = Field(...)



class UpdateUserModel(BaseModel):
    fullname : Optional[str]
    lastname: Optional[str]
    phonenumber:Optional[str]
    email: Optional[EmailStr]
    password:Optional[str]
    
    
def ResponseModel(data, message):
    return {
        "data": data,
        "code": 200,
        "message": message,
    }

def ResponseModels(data, message):
    return {
        "data": [data],
        "code": 200,
        "message": message,
    }
    
def ResponseLogin(data,token, message):
    return {
        "data": {
            "user":data,
            "token": token
            },
        "code": 200,
        "message": message,
    }

def ErrorResponseModel(error, code, message):
    return {
        "error": error, 
        "code": code, 
        "message": message
    }