import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Field, SQLModel, Session, create_engine, select, delete
from datetime import datetime

# --- 1. DATABASE MODELS ---

class Gratitude(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    content: str
    category: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Scripture(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    reference: str  # e.g., "John 3:16"
    text: str       # e.g., "For God so loved..."
    category: Optional[str] = "General"

# --- 2. DATABASE CONFIGURATION ---

DATABASE_URL = os.environ.get("DATABASE_URL")

engine = create_engine(
    DATABASE_URL, 
    pool_pre_ping=True, 
    connect_args={"sslmode": "require"}
)

# --- 3. APP INITIALIZATION ---

app = FastAPI(title="Gratitude Jar & Scripture API")

# --- 4. CORS CONFIGURATION ---

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 5. STARTUP SCRIPT ---

@app.on_event("startup")
def on_startup():
    try:
        SQLModel.metadata.create_all(engine)
        print("✅ All database tables synced successfully!")
    except Exception as e:
        print(f"❌ Database sync failed: {e}")

# --- 6. API ROUTES ---

@app.get("/")
def health_check():
    return {"status": "online", "message": "API is running"}

# --- Gratitude Routes ---

@app.post("/gratitude/", response_model=Gratitude)
def create_gratitude(gratitude: Gratitude):
    with Session(engine) as session:
        session.add(gratitude)
        session.commit()
        session.refresh(gratitude)
        return gratitude

@app.get("/gratitude/", response_model=List[Gratitude])
def read_gratitudes():
    with Session(engine) as session:
        return session.exec(select(Gratitude)).all()

@app.delete("/gratitude/{gratitude_id}")
def delete_gratitude(gratitude_id: int):
    with Session(engine) as session:
        gratitude = session.get(Gratitude, gratitude_id)
        if not gratitude:
            raise HTTPException(status_code=404, detail="Gratitude not found")
        session.delete(gratitude)
        session.commit()
        return {"ok": True}

# --- Scripture Routes ---

@app.get("/scriptures/", response_model=List[Scripture])
def read_scriptures():
    with Session(engine) as session:
        return session.exec(select(Scripture)).all()

@app.post("/scriptures/", response_model=Scripture)
def create_scripture(scripture: Scripture):
    with Session(engine) as session:
        session.add(scripture)
        session.commit()
        session.refresh(scripture)
        return scripture

# --- System Routes ---

@app.delete("/reset/")
def reset_database():
    with Session(engine) as session:
        session.exec(delete(Gratitude))
        session.commit()
        return {"message": "Gratitude data has been reset"}
    
@app.delete("/scriptures/{scripture_id}")
def delete_scripture(scripture_id: int):
    with Session(engine) as session:
        scripture = session.get(Scripture, scripture_id)
        if not scripture:
            raise HTTPException(status_code=404, detail="Scripture not found")
        session.delete(scripture)
        session.commit()
        return {"ok": True}