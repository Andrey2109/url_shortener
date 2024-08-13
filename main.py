from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
from sqlalchemy import Column, String, create_engine, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import hashlib

# FastAPI instance
app = FastAPI()

# Database setup
DATABASE_URL = "postgresql://username:password@localhost/url_shortener_db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# URL model
class URL(Base):
    __tablename__ = "urls"
    id = Column(Integer, primary_key=True, index=True)
    short_code = Column(String, unique=True, index=True)
    original_url = Column(String)

# Create the database tables
Base.metadata.create_all(bind=engine)

# Pydantic models
class URLRequest(BaseModel):
    url: HttpUrl

# Helper function to generate short code
def generate_short_code(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()[:6]

# POST /shorten: Accept a long URL, return a shortened URL
@app.post("/shorten")
def shorten_url(url_request: URLRequest):
    db = SessionLocal()
    short_code = generate_short_code(url_request.url)

    db_url = db.query(URL).filter(URL.short_code == short_code).first()
    if db_url:
        return {"shortened_url": f"http://localhost:8000/{db_url.short_code}"}

    new_url = URL(short_code=short_code, original_url=url_request.url)
    db.add(new_url)
    db.commit()
    db.refresh(new_url)
    return {"shortened_url": f"http://localhost:8000/{new_url.short_code}"}

# GET /{short_code}: Redirect to the original URL
@app.get("/{short_code}")
def redirect_url(short_code: str):
    db = SessionLocal()
    db_url = db.query(URL).filter(URL.short_code == short_code).first()
    if db_url is None:
        raise HTTPException(status_code=404, detail="URL not found")
    return {"original_url": db_url.original_url}
