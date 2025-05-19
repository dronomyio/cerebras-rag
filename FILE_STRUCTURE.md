# Cerebras RAG Application - File Structure

```
cerebras-rag/
├── README.md                 # Project overview
├── architecture.md           # Detailed system architecture
├── todo.md                   # Development checklist
├── docker-compose.yml        # Main orchestration file
├── .env.example              # Example environment variables
├── DEPLOYMENT.md             # Deployment instructions
├── USER_GUIDE.md             # End-user documentation
├── sample_queries.md         # Test queries for validation
│
├── pdf-processor/            # PDF processing service
│   ├── Dockerfile            # Container definition
│   ├── requirements.txt      # Python dependencies
│   ├── extract_pdf.py        # PDF extraction script
│   └── ingest.py             # Weaviate ingestion script
│
├── webapp/                   # Web application
│   ├── Dockerfile            # Container definition
│   ├── requirements.txt      # Python dependencies
│   ├── app.py                # Flask application
│   └── templates/            # HTML templates
│       ├── login.html        # Login page
│       ├── register.html     # Registration page
│       └── chat.html         # Main chat interface
│
└── code-executor/            # Code execution service
    ├── Dockerfile            # Container definition
    ├── requirements.txt      # Python dependencies
    └── app.py                # Flask application for code execution
```
