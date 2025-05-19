# Cerebras RAG Application Architecture

![architecture_diagram](https://github.com/user-attachments/assets/d2b8e9a0-a5ca-47db-89cc-750319dcedf7)

## If a pluggable unstructured.io document processing module is added

![updated_architecture_diagram](https://github.com/user-attachments/assets/dd9d4e26-95bb-45f9-969e-4856442541e9)


## System Architecture

The application follows a microservices architecture with the following components:

### 1. Weaviate Vector Database
- **Purpose**: Store and retrieve vector embeddings of book content
- **Technology**: Weaviate
- **Configuration**: 
  - Custom schema for financial engineering content
  - Text2vec-transformers vectorizer
  - Configured for high recall on financial terminology

### 2. PDF Processor Service
- **Purpose**: Extract, clean, and chunk text from Ruppert's book
- **Technology**: Python with PyMuPDF (fitz), NLTK
- **Features**:
  - Intelligent chunking based on section boundaries
  - Formula and code block detection
  - Metadata extraction (chapter, section, page numbers)
  - Image extraction and description

### 3. Web Application
- **Purpose**: Provide user interface and orchestrate system components
- **Technology**: Flask, Flask-SocketIO, Flask-Login
- **Features**:
  - Real-time chat interface
  - User authentication and session management
  - Conversation history tracking
  - Source citation display
  - Admin dashboard for system monitoring

### 4. Cerebras Connector
- **Purpose**: Interface with Cerebras inference API
- **Technology**: Python with Cerebras Cloud SDK
- **Features**:
  - Prompt engineering for financial context
  - Response streaming
  - Fallback mechanisms
  - Rate limiting and token management

### 5. Code Executor
- **Purpose**: Safely run R and Python code examples
- **Technology**: Docker-in-Docker with restricted permissions
- **Features**:
  - Isolated execution environments
  - Resource limitations
  - Timeout enforcement
  - Result capturing and formatting

### 6. Redis
- **Purpose**: Session management, rate limiting, and caching
- **Technology**: Redis
- **Features**:
  - Conversation history storage
  - API call caching
  - Rate limit enforcement

## Data Flow

1. **Ingestion Flow**:
   - PDF Processor extracts text from Ruppert's book
   - Content is chunked and processed
   - Chunks are vectorized and stored in Weaviate
   - Metadata is indexed for filtering

2. **Query Flow**:
   - User submits question via chat interface
   - Web App authenticates and processes request
   - Relevant chunks retrieved from Weaviate
   - Cerebras Connector generates response with context
   - Response and sources returned to user

3. **Code Execution Flow**:
   - User requests code execution
   - Code Executor creates isolated container
   - Code runs with appropriate dependencies
   - Results captured and returned
   - Container destroyed

## Security Considerations

- JWT-based authentication
- Rate limiting to prevent abuse
- Sandboxed code execution
- Input validation and sanitization
- Secure environment variable handling
- HTTPS enforcement

## Deployment Considerations

- Scalable container orchestration
- Persistent volume for Weaviate data
- Environment-specific configuration
- Health monitoring and logging
- Backup and recovery procedures
