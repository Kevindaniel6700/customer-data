# Mini Data Pipeline System

A simple data pipeline that fetches customer data from a Flask mock server and stores it in PostgreSQL via a FastAPI service.

## Architecture

```
Flask Mock Server (port 5001)
        |
        | HTTP (paginated fetch)
        v
FastAPI Pipeline Service (port 8000)
        |
        | SQLAlchemy ORM
        v
PostgreSQL Database (port 5432)
```

## Services

| Service           | Technology | Port |
|-------------------|------------|------|
| Mock Server       | Flask      | 5001 |
| Pipeline Service  | FastAPI    | 8000 |
| Database          | PostgreSQL | 5432 |

## Setup & Run

### Prerequisites
- Docker
- Docker Compose

### Start all services

```bash
docker-compose up -d
```

Wait ~10 seconds for all services to initialize, then test the endpoints below.

### Stop all services

```bash
docker-compose down
```

### Stop and remove data

```bash
docker-compose down -v
```

---

## API Endpoints

### Flask Mock Server (`http://localhost:5001`)

| Method | Endpoint                      | Description              |
|--------|-------------------------------|--------------------------|
| GET    | `/api/health`                 | Health check             |
| GET    | `/api/customers`              | Paginated customer list  |
| GET    | `/api/customers/{id}`         | Single customer by ID    |

### FastAPI Pipeline Service (`http://localhost:8000`)

| Method | Endpoint                      | Description                        |
|--------|-------------------------------|------------------------------------|
| GET    | `/api/health`                 | Health check                       |
| POST   | `/api/ingest`                 | Fetch from Flask → save to DB      |
| GET    | `/api/customers`              | Paginated customers from DB        |
| GET    | `/api/customers/{id}`         | Single customer from DB            |

FastAPI also provides auto-generated docs at: `http://localhost:8000/docs`

---

## Example curl Commands

### 1. Check Flask health
```bash
curl http://localhost:5001/api/health
```

### 2. Get customers from Flask (page 1, limit 5)
```bash
curl "http://localhost:5001/api/customers?page=1&limit=5"
```

### 3. Get a specific customer from Flask
```bash
curl http://localhost:5001/api/customers/CUST001
```

### 4. Trigger ingestion pipeline (Flask → PostgreSQL)
```bash
curl -X POST http://localhost:8000/api/ingest
```

### 5. Get customers from database (page 1, limit 5)
```bash
curl "http://localhost:8000/api/customers?page=1&limit=5"
```

### 6. Get a specific customer from database
```bash
curl http://localhost:8000/api/customers/CUST001
```

### 7. Check FastAPI health
```bash
curl http://localhost:8000/api/health
```

---

## Project Structure

```
project-root/
├── docker-compose.yml
├── README.md
├── .env
├── mock-server/
│   ├── app.py
│   ├── data/customers.json
│   ├── Dockerfile
│   └── requirements.txt
└── pipeline-service/
    ├── main.py
    ├── database.py
    ├── models/
    │   └── customer.py
    ├── services/
    │   └── ingestion.py
    ├── Dockerfile
    └── requirements.txt
```
