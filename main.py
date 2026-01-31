import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Field, SQLModel, Session, create_engine, select
from datetime import datetime

# 1. DATABASE MODELS
class Gratitude(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    content: str
    category: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

# 2. DATABASE CONFIGURATION
# Render will pull this from the Environment Variables you set
DATABASE_URL = os.environ.get("DATABASE_URL")

# pool_pre_ping=True is essential for Supabase Transaction Poolers (Port 6543)
# It checks if the connection is still alive before sending a query
engine = create_engine(
    DATABASE_URL, 
    pool_pre_ping=True, 
    connect_args={"sslmode": "require"}
)

# 3. APP INITIALIZATION
app = FastAPI(title="Gratitude Jar API")

# 4. CORS CONFIGURATION
# Allows your Vercel frontend to talk to this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For production, replace "*" with your Vercel URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 5. STARTUP SCRIPT
@app.on_event("startup")
def on_startup():
    try:
        SQLModel.metadata.create_all(engine)
        print("✅ Database tables synced successfully!")
    except Exception as e:
        print(f"❌ Database sync failed, but server is starting: {e}")

# 6. API ROUTES
@app.get("/")
def health_check():
    return {"status": "online", "message": "Gratitude API is running"}

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
        gratitudes = session.exec(select(Gratitude)).all()
        return gratitudes

@app.delete("/gratitude/{gratitude_id}")
def delete_gratitude(gratitude_id: int):
    with Session(engine) as session:
        gratitude = session.get(Gratitude, gratitude_id)
        if not gratitude:
            raise HTTPException(status_code=404, detail="Gratitude not found")
        session.delete(gratitude)
        session.commit()
        return {"ok": True}