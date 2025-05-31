# HireOn ML Services

A FastAPI-based microservice providing AI and recommendation services for HireOn recruitment platform.

## Overview

This repository contains the machine learning services for the HireOn platform, including:

1. **Gen AI Services**: CV analysis, job matching, and cover letter generation using Gemini AI.
2. **Recommendation Engine**: Job recommendation system using semantic search and embeddings.

## Features

### Gen AI Services

- **CV Job Analysis**: Analyzes a candidate's CV against job details to:
  - Calculate a relevance score between the CV and job
  - Identify skill matches and gaps
  - Provide personalized improvement suggestions
  - Highlight strengths and areas for development

- **Cover Letter Generator**: Automatically generates personalized cover letters based on:
  - Candidate's CV content
  - Job description and requirements
  - Outputs as a professionally formatted PDF

### Recommendation Engine

- **Job Recommendations**: Provides personalized job recommendations based on:
  - Semantic understanding of CV content
  - Job title and description matching
  - Similarity scoring and ranking

- **CV Embeddings**: Stores and retrieves vector embeddings of user CVs for efficient similarity searching

## Tech Stack

- **FastAPI**: Modern, high-performance web framework for building APIs
- **Gemini AI**: Google's generative AI model for natural language processing tasks
- **ChromaDB**: Vector database for storing and querying embeddings
- **Google Cloud Storage**: For storing documents and generated PDFs
- **Docker**: Containerization for deployment
- **Python 3.12**: Core programming language

## Project Structure

```
.
├── app/                        # Main application package
│   ├── __init__.py             # Application initialization
│   ├── api/                    # API routes and models
│   │   ├── core/               # Core service components
│   │   ├── models/             # Data models and schemas
│   │   └── routes/             # API endpoints
│   │       ├── gen_ai_services.py     # Gen AI endpoints
│   │       └── recommendation_engine_services.py  # Recommendation endpoints
│   └── utils/                  # Utility functions
├── credentials/                # Service account credentials
├── data/                       # Data files
├── experiments/                # Experimental notebooks and scripts
├── notebook/                   # Jupyter notebooks for development
├── .env                        # Environment variables
├── .env.example                # Example environment configuration
├── Dockerfile                  # Docker configuration
├── docker-compose.yml          # Docker Compose configuration
├── main.py                     # Application entry point
└── requirements.txt            # Python dependencies
```

## Installation

### Prerequisites

- Python 3.12+
- Docker and Docker Compose (optional)
- Google Cloud account with Gemini API and Storage access

### Environment Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/hireon-ml-services.git
   cd hireon-ml-services
   ```

2. Set up a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env file with your API keys and configuration
   ```

5. Add your Google Cloud credentials to the `credentials/` directory.

## Running the Service

### Local Development

```bash
uvicorn main:app --reload
```

The API will be available at http://localhost:8000

### Using Docker

```bash
docker build -t hireon-ml-services .
docker run -p 8000:8000 hireon-ml-services
```

Or with Docker Compose:

```bash
docker-compose up
```

## API Documentation

When the service is running, API documentation is available at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Environment Variables

| Variable | Description |
|----------|-------------|
| `GEMINI_API_KEY` | Google Gemini API key |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to Google Cloud service account credentials |
| `GOOGLE_CLOUD_PROJECT` | Google Cloud project ID |
| `GOOGLE_CLOUD_LOCATION` | Google Cloud region |
| `GOOGLE_GENAI_USE_VERTEXAI` | Whether to use Vertex AI (true/false) |
| `MONGO_URI` | MongoDB connection string |
| `CHROMA_CLIENT_HOST` | ChromaDB server host |
| `CHROMA_CLIENT_PORT` | ChromaDB server port |
| `API_SECRET_KEY` | Secret key for API security |

## Development

### Adding New Endpoints

1. Create a new route file in `app/api/routes/` or extend existing ones
2. Define request/response models in `app/api/models/models.py`
3. Implement utility functions in `app/utils/`
4. Register the router in `app/__init__.py`

## API Endpoints

### Gen AI Services
- `/gen-ai/analyze-cv`: Analyze CV against job requirements
- `/gen-ai/generate-cover-letter`: Generate a personalized cover letter

### Recommendation Engine
- `/recommendation/get-job-recommendations`: Get job recommendations based on CV
- `/recommendation/store-cv-embedding`: Store CV embedding for future recommendations

## License

[License Information]

## Contributors

[Contributor Information] 