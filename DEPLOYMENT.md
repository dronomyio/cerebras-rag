# Cerebras RAG Application Deployment Guide

This guide provides instructions for deploying the Cerebras RAG application for Ruppert's "Statistics and Data Analysis for Financial Engineering" book.

## Prerequisites

- Docker and Docker Compose installed
- Cerebras API key
- At least 8GB RAM and 20GB disk space
- The Ruppert book PDF file

## Quick Start

1. Clone the repository or extract the provided files
2. Copy the `.env.example` file to `.env` and update the values:
   ```
   cp .env.example .env
   ```
3. Edit the `.env` file with your specific configuration:
   - Set your Cerebras API key
   - Update the path to the Ruppert PDF
   - Change the default admin credentials
   - Set secure passwords for Redis and Weaviate
4. Start the application:
   ```
   docker-compose up -d
   ```
5. Access the web interface at http://localhost:80
6. Log in with the admin credentials specified in your `.env` file

## Detailed Configuration

### Environment Variables

- `WEBAPP_SECRET_KEY`: Secret key for the Flask application (change this!)
- `ADMIN_EMAIL` and `ADMIN_PASSWORD`: Default admin user credentials
- `WEAVIATE_ADMIN_KEY`: API key for Weaviate access
- `REDIS_PASSWORD`: Password for Redis
- `CEREBRAS_API_KEY`: Your Cerebras API key
- `CEREBRAS_API_URL`: Cerebras API endpoint (usually no need to change)
- `RUPPERT_PDF_PATH`: Absolute path to the Ruppert book PDF file

### Services

The application consists of the following services:

1. **Weaviate**: Vector database for storing and retrieving book content
2. **t2v-transformers**: Text-to-vector transformer model for Weaviate
3. **Redis**: For session management and caching
4. **PDF Processor**: Service for extracting and chunking text from the PDF
5. **Code Executor**: Service for running R and Python code examples
6. **Web Application**: Flask-based web interface with chat and authentication
7. **NGINX**: For SSL termination and serving static files

## Initial Data Processing

When the application starts for the first time, the PDF processor service will:

1. Extract text from the Ruppert book PDF
2. Identify chapters and sections
3. Chunk the content appropriately
4. Detect code blocks
5. Ingest the processed content into Weaviate

This process may take 5-10 minutes depending on your hardware. The application will be fully functional once this process completes.

## Security Considerations

- Change all default passwords in the `.env` file
- The application uses JWT-based authentication
- Code execution is performed in isolated Docker containers
- All services communicate over an internal Docker network

## Troubleshooting

### PDF Processing Issues

If the PDF processor fails to extract content correctly:
- Check that the PDF is not password-protected
- Ensure the path in `RUPPERT_PDF_PATH` is correct
- Check the logs: `docker-compose logs pdf-processor`

### Connection Issues

If you cannot connect to the web interface:
- Ensure all containers are running: `docker-compose ps`
- Check the logs: `docker-compose logs webapp`
- Verify that port 80 is not in use by another application

### Weaviate Issues

If search results are not relevant:
- Check that the ingestion completed successfully: `docker-compose logs pdf-processor`
- Verify Weaviate is running: `docker-compose logs weaviate`

## Backup and Restore

To backup the Weaviate data:
```
docker-compose exec -T weaviate weaviate-backup create --output-file=/tmp/weaviate-backup.tar.gz
docker cp $(docker-compose ps -q weaviate):/tmp/weaviate-backup.tar.gz ./weaviate-backup.tar.gz
```

To restore from backup:
```
docker cp ./weaviate-backup.tar.gz $(docker-compose ps -q weaviate):/tmp/weaviate-backup.tar.gz
docker-compose exec -T weaviate weaviate-backup restore --input-file=/tmp/weaviate-backup.tar.gz
```

## Cloud Deployment

For cloud deployment:

1. Ensure your cloud provider supports Docker Compose or Kubernetes
2. Adjust the `docker-compose.yml` file to use external volumes if needed
3. Configure proper SSL certificates for NGINX
4. Set up appropriate firewall rules to expose only ports 80 and 443
5. Consider using managed Redis and database services for better reliability

## Support

For issues or questions, please refer to the documentation or contact support.
