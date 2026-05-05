from pydantic import BaseModel, EmailStr

# Register
class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str

# Login
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

# Token response
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"