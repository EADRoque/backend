from fastapi import FastAPI, Depends, HTTPException
from sqlmodel import SQLModel, Session, select, Field, delete
from typing import List, Optional
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine # We need to create the engine
import os
from dotenv import load_dotenv

load_dotenv()

# --- DATABASE SETUP ---
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./local_database.db")

# Fix for Render/Supabase URLs if needed later
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL, echo=True)

def get_session():
    with Session(engine) as session:
        yield session

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

# --- MODELS ---
class Gratitude(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    content: str
    mood: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Scripture(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    verse_text: str
    reference: str
    category: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

# --- APP LIFECYCLE ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

# --- HERE IS THE "app" VARIABLE UVICORN IS LOOKING FOR ---
app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- ENDPOINTS ---
@app.get("/")
def read_root():
    return {"message": "API is running!"}

@app.post("/gratitude/", response_model=Gratitude)
def create_gratitude(gratitude: Gratitude, session: Session = Depends(get_session)):
    session.add(gratitude)
    session.commit()
    session.refresh(gratitude)
    return gratitude

@app.get("/gratitude/", response_model=List[Gratitude])
def read_gratitudes(session: Session = Depends(get_session)):
    statement = select(Gratitude).order_by(Gratitude.created_at.desc())
    return session.exec(statement).all()

@app.post("/scriptures/", response_model=Scripture)
def create_scripture(scripture: Scripture, session: Session = Depends(get_session)):
    session.add(scripture)
    session.commit()
    session.refresh(scripture)
    return scripture

@app.get("/scriptures/", response_model=List[Scripture])
def read_scriptures(session: Session = Depends(get_session)):
    statement = select(Scripture).order_by(Scripture.category, Scripture.reference)
    return session.exec(statement).all()

@app.delete("/reset/")
def reset_database(session: Session = Depends(get_session)):
    # Delete all rows from both tables
    session.exec(delete(Gratitude))
    session.exec(delete(Scripture))
    session.commit()
    return {"message": "Database reset successfully"}