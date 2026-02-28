from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from app.database import get_db, engine, Base
from app.schemas import IdentifyRequest, ContactResponse
from app.services.identify_service import identify_contact

# In practice Alembic should manage these. This is fallback.
# Base.metadata.create_all(bind=engine)

app = FastAPI(title="Identity Reconciliation API", description="Bitespeed Backend Task", version="1.0.0")

@app.post("/identify", response_model=ContactResponse)
def identify(data: IdentifyRequest, db: Session = Depends(get_db)):
    return identify_contact(db, data)

@app.get("/health")
def health_check():
    return {"status": "ok"}
