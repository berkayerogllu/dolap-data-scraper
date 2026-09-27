# 🛍️ Dolap Data Scraper API

A robust, production-ready REST API built with FastAPI to asynchronously scrape, process, and manage product data from the Dolap e-commerce ecosystem.

## ✨ Features

- **Asynchronous Scraping Engine:** High-performance data extraction using `httpx` and `asyncio`.
- **Background Processing:** Non-blocking operations ensure the API remains responsive while saving large datasets to Excel.
- **Hierarchical Data Storage:** Automatically organizes scraped data into date-based directories (`data/YYYY-MM-DD/`).
- **File Management API:** Built-in endpoints to securely list and download generated Excel reports.
- **Enterprise Security:** API endpoints are protected via an `X-API-Key` header verified against environment variables.
- **Path Traversal Protection:** Secure file downloading mechanism preventing unauthorized system access.
- **Fully Dockerized:** Containerized architecture with volume mapping for persistent data and logs, featuring `unless-stopped` resilience.

## 🛠️ Tech Stack

- **Framework:** [FastAPI](https://fastapi.tiangolo.com/)
- **Data Processing:** [Pandas](https://pandas.pydata.org/), Pydantic
- **Containerization:** Docker, Docker Compose
- **HTTP Client:** HTTPX (Async)
- **Environment Management:** python-dotenv

## 🚀 Getting Started

### Prerequisites
- [Docker](https://docs.docker.com/get-docker/) and Docker Compose installed on your system.

### 1. Environment Setup
Create a `.env` file in the root directory and define your secret API key:
```ini
SECRET_API_KEY=your_super_secret_api_key_here
```
*(Note: The `.env` file is ignored by Git and Docker for security purposes.)*

### 2. Run with Docker
The easiest way to start the application is via Docker Compose:
```bash
docker-compose up -d --build
```
The API will be available at `http://localhost:8000`.

## 📚 API Documentation

Once the server is running, access the interactive Swagger UI documentation at:
**[http://localhost:8000/docs](http://localhost:8000/docs)**

### Key Endpoints

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `POST` | `/scrape` | Starts a background scraping task for a specific keyword. | Yes (`X-API-Key`) |
| `GET` | `/files` | Lists all categorized Excel files in the server. | Yes (`X-API-Key`) |
| `GET` | `/download/{date}/{file}` | Downloads a specific Excel file securely. | Yes (`X-API-Key`) |

## 📁 Project Structure

```text
dolap-data-scraper/
├── data/                   # Persistent volume for scraped Excel files
│   └── YYYY-MM-DD/         # Date-based categorization
├── logs/                   # Persistent volume for application logs
├── .env                    # Environment variables (Not committed)
├── .dockerignore           # Docker ignore rules
├── docker-compose.yml      # Docker compose configuration
├── Dockerfile              # Docker image blueprint
├── main.py                 # FastAPI application and endpoints
├── logger.py               # Centralized logging configuration
├── schemas.py              # Pydantic data validation models
└── requirements.txt        # Python dependencies
```