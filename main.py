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

if __name__ == "__main__":
    # Create the tables if they don't exist
    from database import get_db, Base, engine
    Base.metadata.create_all(bind=engine)
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
