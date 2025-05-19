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
