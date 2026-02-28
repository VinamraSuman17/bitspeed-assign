# Identity Reconciliation System

This project is a FastAPI microservice that implements an identity graph reconciliation system. It processes incoming contact requests containing `email` and `phoneNumber` and links them together according to specified precedence rules using PostgreSQL.

## Core Features
1. **Identity Linking Rule**: Contacts are linked if their email OR phone number matches.
2. **Primary Contact Rule**: The oldest contact within a linked cluster becomes the primary contact, and all others become secondary contacts pointing to the primary.
3. **Primary Merging**: When a new request connects two previously independent primary contacts, the system identifies the oldest primary, converts the newer primary into a secondary, and updates all associated secondary contacts to link to the oldest primary.
4. **Relational Consistency**: Transactional guarantees to ensure the graph graph always results in clean relational links without dangling or cyclic dependencies.

## Architecture & Stack
- **FastAPI**: Asynchronous web framework for handling API requests.
- **PostgreSQL**: Relational database.
- **SQLAlchemy (ORM)**: For database modeling and querying.
- **Alembic**: Database schema migrations.
- **Pydantic**: Request and Response validation.
- **Docker Compose**: Pre-configured setup for running PostgreSQL locally.

## Project Structure
```text
app/
  ├── main.py                # FastAPI app & endpoints
  ├── database.py            # SQLAlchemy engine setup
  ├── models.py              # SQLAlchemy Data Models 
  ├── schemas.py             # Pydantic Schemas
  └── services/
      └── identify_service.py # Core transaction graph consolidation logic
alembic/                     # DB Migration Scripts
tests/                       # Pytest Integration Tests
```

## Setup & Running Locally

1. **Clone the repository and set up a Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Start the PostgreSQL Database**:
   ```bash
   docker-compose up -d
   ```
   *Note: To avoid local port conflicts, PostgreSQL maps to `127.0.0.1:5433`.*

3. **Run Database Migrations**:
   ```bash
   # Make sure DB is up before running migrations
   alembic upgrade head
   ```

4. **Run the FastAPI Server**:
   ```bash
   uvicorn app.main:app --reload
   ```

## Running Tests
Tests are written in `pytest` and use an in-memory SQLite database to ensure idempotency.
```bash
pytest
```

## API Usage

### `POST /identify`
Consolidate or create a contact identity.

**Request:**
```json
{
  "email": "george@hillvalley.edu",
  "phoneNumber": "717171"
}
```

**Response:**
```json
{
  "contact": {
    "primaryContatctId": 1,
    "emails": [
      "george@hillvalley.edu"
    ],
    "phoneNumbers": [
      "717171"
    ],
    "secondaryContactIds": []
  }
}
```

## Example Scenarios
- **Case 1: No match found**: Creates a new primary contact.
- **Case 2: Match found**: Consolidates the cluster. If the payload contains a new phone/email, it creates a new secondary contact linking to the oldest primary.
## Deployment to Render

This project includes a `Dockerfile` and is fully configured to be deployed on Render.com.

### Steps to Deploy:
1. Push this repository to GitHub.
2. Log into [Render.com](https://render.com) and create a new **PostgreSQL** database service.
   - Copy the "Internal Database URL" (it looks like `postgres://user:password@host:5432/dbname`).
3. Click "New +" and select **Web Service**.
4. Connect your GitHub repository.
5. In the Build and Deploy settings:
   - **Environment**: Docker
   - **Region**: (Choose the same region as your Database)
   - **Branch**: main
6. Scroll down to **Advanced** and add an Environment Variable:
   - **Key**: `DATABASE_URL`
   - **Value**: (Paste the Render Internal Database URL from Step 2)
7. Click **Create Web Service**.

When the server deploys, the `Dockerfile` will automatically run the `alembic upgrade head` command to create your database tables before starting Uvicorn.

Your API endpoint will then be available at: `https://<your-app-name>.onrender.com/identify`
