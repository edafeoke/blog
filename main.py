from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.templating import Jinja2Templates
from fastapi import Form, Request, Response
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from database import get_db, Base, engine
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from pydantic import BaseModel
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
from models import User, Blog

Base.metadata.create_all(bind=engine)


secret_key="secret_key"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI()

# Load templates
templates = Jinja2Templates(directory="templates")

# Security and authentication
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Define an OAuth2 password request form model
class TokenData(BaseModel):
    username: str = None

# Define a function to get the current user based on the token
async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, secret_key, algorithms=[algorithm])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.username == token_data.username).first()
    if user is None:
        raise credentials_exception

    return user

# Define the routes and handlers
@app.get("/")
async def read_blogs(request: Request, db: Session = Depends(get_db)):
    # Retrieve blogs from the database and display them on the homepage
    blogs = db.query(Blog).all()  # Correct the query here
    return templates.TemplateResponse("index.html", {"request": request, "blogs": blogs})

@app.get("/blog/{blog_id}")
async def read_blog(blog_id: int, request: Request, db: Session = Depends(get_db)):
    # Retrieve a specific blog and display it
    blog = db.query(Blog).filter(Blog.id == blog_id).first()  # Correct the query here
    if blog is None:
        raise HTTPException(status_code=404, detail="Blog not found")
    return templates.TemplateResponse("blog.html", {"request": request, "blog": blog})

# ...

@app.post("/create-blog")
async def create_blog(title: str = Form(...), body: str = Form(...), user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Create a new blog and store it in the database
    blog = Blog(title=title, body=body, author_id=user.id)
    db.add(blog)
    db.commit()
    return {"message": "Blog created successfully"}

# Add login, registration, and user management routes as well
# Registration Form Model
class UserCreate(BaseModel):
    username: str
    password: str

# User Registration Routes
# Render the registration page
@app.get("/register")
async def render_register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register")
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    # Check if the username is already in use
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username is already taken")

    # Hash the user's password before storing it in the database
    hashed_password = pwd_context.hash(user_data.password)
    user = User(username=user_data.username, password=hashed_password)
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Render a success page using a template
    return templates.TemplateResponse("registration_success.html", {"request": request})

#LOGIN
@app.get("/login")
async def render_login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# Login Route
@app.post("/login")
async def login(response: Response, form_data: OAuth2PasswordRequestForm = Depends(), templates: Jinja2Templates = Depends()):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not pwd_context.verify(form_data.password, user.password):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    # Create a token for the user
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    
    # Set the token as a cookie and return it
    response.set_cookie(key="access_token", value=access_token)

    # Render a success page using a template
    return templates.TemplateResponse("login_success.html", {"request": request})

if __name__ == "__main__":
    # Create the tables if they don't exist
    from database import get_db, Base, engine
    Base.metadata.create_all(bind=engine)
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
