from fastapi import FastAPI, Request, Depends, HTTPException, status, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import Body 
from datetime import datetime
from typing import Annotated
import os
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .models import UserCreate, User, Link
from .auth import get_password_hash, verify_password, create_access_token, get_current_user
from .database import db, check_db_connection

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.on_event("startup")
async def startup_db_client():
    await check_db_connection()

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return RedirectResponse(url="/login")

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register", response_model=User)
async def register(user: UserCreate):
    existing_user = await db["users"].find_one({"$or": [{"email": user.email}, {"username": user.username}]})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email or username already registered")
    
    hashed_password = get_password_hash(user.password)
    user_dict = user.model_dump()
    user_dict["password"] = hashed_password
    user_dict["created_at"] = datetime.utcnow()
    user_dict["is_active"] = True
    user_dict["links"] = []
    
    result = await db["users"].insert_one(user_dict)
    created_user = await db["users"].find_one({"_id": result.inserted_id})
    created_user["id"] = str(created_user["_id"])
    return created_user

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/token")
async def login(response: Response, form_data: OAuth2PasswordRequestForm = Depends()):
    user = await db["users"].find_one({"username": form_data.username})
    if not user or not verify_password(form_data.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    
    access_token = create_access_token(data={"sub": user["username"]})
    
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=1800,
        secure=False  # Set to True in production with HTTPS
    )
    
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, current_user: User = Depends(get_current_user)):
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": current_user
    })

@app.post("/links")
async def add_links(links: list[Link], current_user: User = Depends(get_current_user)):
    if len(links) > 2:
        raise HTTPException(status_code=400, detail="Maximum 2 links allowed")
    
    await db["users"].update_one(
        {"username": current_user["username"]},
        {"$set": {"links": [link.model_dump() for link in links]}}
    )
    return {"message": "Links updated successfully"}

@app.get("/{username}", response_class=HTMLResponse)
async def user_profile(username: str, request: Request):
    user = await db["users"].find_one({"username": username})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return templates.TemplateResponse("profile.html", {
        "request": request,
        "user": user
    })

@app.post("/link_click/{username}/{link_index}")
async def track_link_click(username: str, link_index: int):
    await db["users"].update_one(
        {"username": username},
        {"$inc": {f"links.{link_index}.clicks": 1}}
    )
    user = await db["users"].find_one({"username": username})
    return RedirectResponse(url=user["links"][link_index]["url"])

@app.post("/links")
async def add_links(
    links: list[Link] = Body(...),  # Explicitly specify this is the request body
    current_user: User = Depends(get_current_user)
):
    if len(links) > 2:
        raise HTTPException(status_code=400, detail="Maximum 2 links allowed")
    
    await db["users"].update_one(
        {"username": current_user["username"]},
        {"$set": {"links": [link.model_dump() for link in links]}}
    )
    return {"message": "Links updated successfully"}

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
    )