import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def run_around_tests():
    # Setup
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    # Teardown
    Base.metadata.drop_all(bind=engine)


def test_no_match():
    response = client.post("/identify", json={"email": "lorraine@hillvalley.edu", "phoneNumber": "123456"})
    assert response.status_code == 200
    data = response.json()
    assert data["contact"]["primaryContatctId"] > 0
    assert data["contact"]["emails"] == ["lorraine@hillvalley.edu"]
    assert data["contact"]["phoneNumbers"] == ["123456"]
    assert data["contact"]["secondaryContactIds"] == []

def test_match_existing_email_adds_phone():
    # Primary created
    client.post("/identify", json={"email": "lorraine@hillvalley.edu", "phoneNumber": "123456"})
    
    # Same email, new phone
    response = client.post("/identify", json={"email": "lorraine@hillvalley.edu", "phoneNumber": "654321"})
    assert response.status_code == 200
    data = response.json()
    assert len(data["contact"]["emails"]) == 1
    assert "lorraine@hillvalley.edu" in data["contact"]["emails"]
    assert len(data["contact"]["phoneNumbers"]) == 2
    assert "123456" in data["contact"]["phoneNumbers"]
    assert "654321" in data["contact"]["phoneNumbers"]
    assert len(data["contact"]["secondaryContactIds"]) == 1

def test_primary_merge():
    # Primary 1
    resp1 = client.post("/identify", json={"email": "biff@hillvalley.edu", "phoneNumber": "111111"})
    prim1_id = resp1.json()["contact"]["primaryContatctId"]

    # Primary 2
    resp2 = client.post("/identify", json={"email": "doc@hillvalley.edu", "phoneNumber": "222222"})
    prim2_id = resp2.json()["contact"]["primaryContatctId"]

    # Merge them
    response = client.post("/identify", json={"email": "biff@hillvalley.edu", "phoneNumber": "222222"})
    data = response.json()

    assert data["contact"]["primaryContatctId"] == prim1_id
    assert prim2_id in data["contact"]["secondaryContactIds"]
    assert "biff@hillvalley.edu" in data["contact"]["emails"]
    assert "doc@hillvalley.edu" in data["contact"]["emails"]

def test_same_request_repeated_does_not_create_duplicate():
    client.post("/identify", json={"email": "lorraine@hillvalley.edu", "phoneNumber": "123456"})
    response = client.post("/identify", json={"email": "lorraine@hillvalley.edu", "phoneNumber": "123456"})
    
    data = response.json()
    assert len(data["contact"]["secondaryContactIds"]) == 0

def test_missing_both_fields():
    response = client.post("/identify", json={"email": None, "phoneNumber": None})
    assert response.status_code == 400
