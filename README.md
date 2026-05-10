# Automotive Document Intelligence System

A multimodal RAG (Retrieval-Augmented Generation) system for querying automotive service manuals. Built with FastAPI, Google Gemini, PyMuPDF, and ChromaDB.

## Features

- **PDF Processing**: Extract text, diagrams, and structural information from automotive service manuals using PyMuPDF
- **Vision Analysis**: Analyze technical diagrams using Google Gemini Vision API
- **Vector Storage**: Store and search embeddings using ChromaDB
- **SAE Terminology**: Normalize automotive terminology to SAE/JASO standards
- **REST API**: FastAPI-based REST API for document upload and querying

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Interface                           │
│                     (Web App / Mobile / API)                    │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                         FastAPI Server                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │   /upload   │  │  /query     │  │      /documents          │  │
│  │   endpoint  │  │  endpoint   │  │      endpoints           │  │
│  └──────┬──────┘  └──────┬──────┘  └───────────┬─────────────┘  │
└─────────┼───────────────┼─────────────────────┼────────────────┘
          │               │                     │
          ▼               ▼                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                      RAG Query Pipeline                         │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  1. Query Normalization (Text Cleaning + SAE Normalizer) │  │
│  │  2. ChromaDB Similarity Search                            │  │
│  │  3. Context Assembly                                      │  │
│  │  4. Gemini Pro Response Generation                        │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────┬─────────────────────────────────────────────────────┘
          │
    ┌─────┴─────┐
    │           │
    ▼           ▼
┌────────┐  ┌──────────────┐
│ChromaDB│  │  Gemini API  │
│  DB    │  │  (Vision+Pro)│
└────────┘  └──────────────┘
```

## Tech Stack

- **Backend**: Python, FastAPI
- **AI/ML**: Google Gemini (Vision + Pro)
- **PDF Processing**: PyMuPDF (fitz)
- **Vector Database**: ChromaDB
- **Embeddings**: Sentence Transformers (all-MiniLM-L6-v2)
- **Deployment**: Docker, GitHub Actions

## Getting Started

### Prerequisites

- Python 3.11+
- Google AI API key
- 4GB+ RAM (for embedding model)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd automotive_doc_intelligence
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY
```

5. Run the application:
```bash
python main.py
```

6. Access the API documentation:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Using Docker

```bash
# Build the image
docker build -t automotive-doc-intel .

# Run the container
docker run -p 8000:8000 -e GOOGLE_API_KEY=your_api_key automotive-doc-intel
```

## API Endpoints

### Document Management
- `POST /api/documents/upload` - Upload and process a PDF
- `GET /api/documents/collections` - Get collection statistics
- `DELETE /api/documents/collections/{doc_name}` - Delete a document

### Query
- `POST /api/query/` - Query the knowledge base
- `GET /api/query/suggested-questions` - Get suggested queries
- `GET /api/query/health` - Query service health check

## Example Usage

### Upload a Document
```bash
curl -X POST "http://localhost:8000/api/documents/upload" \
  -F "file=@/path/to/service_manual.pdf"
```

### Query
```bash
curl -X POST "http://localhost:8000/api/query/" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How do I replace the brake pads on a 2020 Toyota Camry?",
    "user_context": "2020 Toyota Camry XLE"
  }'
```

## Project Structure

```
automotive_doc_intelligence/
├── main.py                 # FastAPI app entry point
├── config.py               # Configuration management
├── requirements.txt        # Python dependencies
├── Dockerfile              # Docker build configuration
├── .env.example            # Environment template
├── api/                    # FastAPI endpoints
│   ├── document_router.py  # Document upload endpoints
│   └── query_router.py     # Query endpoints
├── ingestion/              # PDF processing
│   └── pdf_processor.py    # PyMuPDF integration
├── vision/                 # Vision analysis
│   └── gemini_processor.py # Gemini Vision API
├── vector_store/           # Vector storage
│   └── chroma_manager.py  # ChromaDB management
├── rag/                    # RAG pipeline
│   └── query_pipeline.py  # Query processing
└── utils/                 # Utilities
    ├── text_cleaner.py     # Text cleaning
    ├── sae_normalizer.py  # SAE terminology
    └── logger.py           # Logging setup
```

## Configuration Options

| Variable | Default | Description |
|----------|---------|-------------|
| `GOOGLE_API_KEY` | (required) | Google AI API key |
| `PORT` | 8000 | Server port |
| `CHROMA_PERSIST_DIR` | ./chroma_db | Vector database directory |
| `EMBEDDING_MODEL` | all-MiniLM-L6-v2 | Embedding model |
| `CHUNK_SIZE` | 512 | Text chunk size |
| `MAX_RETRIEVAL_RESULTS` | 5 | Max results to retrieve |

## Testing

```bash
# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html
```

## License

MIT License

## Acknowledgments

- Google Gemini AI
- ChromaDB
- FastAPI
- The open-source community