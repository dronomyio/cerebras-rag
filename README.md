# Cerebras RAG Application for Ruppert's Book

This is a complete Docker-based solution for creating a Retrieval-Augmented Generation (RAG) system using Ruppert's "Statistics and Data Analysis for Financial Engineering" book, Cerebras inference API, and Weaviate vector database.

## Features

- **Chat Interface**: Interactive chat with conversation history
- **User Authentication**: Secure access control
- **PDF Processing**: Automatic extraction and chunking of content from Ruppert's book
- **Vector Search**: Semantic search using Weaviate
- **LLM Integration**: Cerebras inference API for high-quality responses
- **Code Execution**: Run R and Python examples from the book
- **Cloud Deployment**: Ready for deployment in cloud environments

## Architecture

The application consists of the following components:

1. **Weaviate**: Vector database for storing and retrieving book content
2. **PDF Processor**: Service for extracting and chunking text from the PDF
3. **Web Application**: Flask-based web interface with chat and authentication
4. **Cerebras Connector**: Service for connecting to Cerebras inference API
5. **Code Executor**: Secure service for running R and Python code examples
6. **Redis**: For session management and rate limiting

All components are containerized and orchestrated using Docker Compose.

## How run minimal
Minimum Requirements to Run the Application

Prerequisites:
Docker and Docker Compose installed
Cerebras API key
Ruppert book PDF file
Quick Start Steps:

a) Set up environment variables:
bash
# Create .env file from example
cp .env.example .env

# Edit the .env file with your values
# At minimum, you need to set:
CEREBRAS_API_KEY=your-api-key-here
RUPPERT_PDF_PATH=/absolute/path/to/ruppert.pdf
WEBAPP_SECRET_KEY=choose-a-secure-random-string
WEAVIATE_ADMIN_KEY=choose-a-secure-random-string
REDIS_PASSWORD=choose-a-secure-random-string
b) Start the application:
bash
# From the cerebras-rag directory
docker-compose up -d
c) Access the application:
Open your browser and navigate to: http://localhost
Log in with the default admin credentials:
Email: admin@example.com
Password: adminpassword (as specified in your .env file )

Minimal Configuration:
If you want to run with absolute minimal services, you can modify the docker-compose.yml to include only:
weaviate
t2v-transformers
redis
pdf-processor
webapp
nginx

The system will automatically process the Ruppert book PDF when first started, which may take a few minutes depending on your hardware. Once processing is complete, you can start asking questions about the book's content.
For more detailed instructions, please refer to the DEPLOYMENT.md file included in the project.
