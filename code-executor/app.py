#!/usr/bin/env python3
"""
Code Executor Service for Cerebras RAG
--------------------------------------
Provides a secure environment for executing R and Python code examples
from Ruppert's book.
"""

import os
import uuid
import json
import logging
import tempfile
import subprocess
import docker
from flask import Flask, request, jsonify

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Docker client for container management
docker_client = docker.from_env()

# Configuration
MAX_EXECUTION_TIME = int(os.getenv('MAX_EXECUTION_TIME', 30))  # seconds
MAX_MEMORY = os.getenv('MAX_MEMORY', '512m')

@app.route('/health')
def health():
    return jsonify({'status': 'ok'})

@app.route('/execute', methods=['POST'])
def execute_code():
    data = request.json
    code = data.get('code')
    language = data.get('language', 'python').lower()
    
    if not code:
        return jsonify({'success': False, 'stderr': 'No code provided'}), 400
    
    if language not in ['python', 'r']:
        return jsonify({'success': False, 'stderr': f'Unsupported language: {language}'}), 400
    
    try:
        # Execute code in appropriate container
        if language == 'python':
            result = execute_python(code)
        else:  # R
            result = execute_r(code)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error executing {language} code: {e}")
        return jsonify({
            'success': False,
            'stdout': '',
            'stderr': f"Error: {str(e)}"
        })

def execute_python(code):
    """Execute Python code in a secure container."""
    # Create a unique container name
    container_name = f"python-exec-{uuid.uuid4().hex[:8]}"
    
    try:
        # Write code to a temporary file
        with tempfile.NamedTemporaryFile(suffix='.py', mode='w', delete=False) as f:
            f.write(code)
            code_file = f.name
        
        # Run in container with appropriate libraries
        container = docker_client.containers.run(
            "python:3.11-slim",
            command=f"python {os.path.basename(code_file)}",
            volumes={os.path.dirname(code_file): {'bind': '/code', 'mode': 'ro'}},
            working_dir="/code",
            remove=True,
            detach=True,
            name=container_name,
            mem_limit=MAX_MEMORY,
            network_mode="none",  # No network access
            environment={
                "PYTHONPATH": "/code"
            }
        )
        
        # Wait for execution to complete with timeout
        try:
            result = container.wait(timeout=MAX_EXECUTION_TIME)
            logs = container.logs().decode('utf-8')
            
            return {
                'success': result['StatusCode'] == 0,
                'stdout': logs if result['StatusCode'] == 0 else '',
                'stderr': '' if result['StatusCode'] == 0 else logs
            }
        except Exception as e:
            # Kill container if it's still running
            try:
                container.kill()
            except:
                pass
            
            raise Exception(f"Execution timed out or failed: {str(e)}")
    
    finally:
        # Clean up
        if os.path.exists(code_file):
            os.unlink(code_file)
        
        # Ensure container is removed
        try:
            container = docker_client.containers.get(container_name)
            container.remove(force=True)
        except:
            pass

def execute_r(code):
    """Execute R code in a secure container."""
    # Create a unique container name
    container_name = f"r-exec-{uuid.uuid4().hex[:8]}"
    
    try:
        # Write code to a temporary file
        with tempfile.NamedTemporaryFile(suffix='.R', mode='w', delete=False) as f:
            f.write(code)
            code_file = f.name
        
        # Run in container with appropriate libraries
        container = docker_client.containers.run(
            "rocker/tidyverse:latest",  # Includes common R packages for data analysis
            command=f"Rscript {os.path.basename(code_file)}",
            volumes={os.path.dirname(code_file): {'bind': '/code', 'mode': 'ro'}},
            working_dir="/code",
            remove=True,
            detach=True,
            name=container_name,
            mem_limit=MAX_MEMORY,
            network_mode="none",  # No network access
        )
        
        # Wait for execution to complete with timeout
        try:
            result = container.wait(timeout=MAX_EXECUTION_TIME)
            logs = container.logs().decode('utf-8')
            
            return {
                'success': result['StatusCode'] == 0,
                'stdout': logs if result['StatusCode'] == 0 else '',
                'stderr': '' if result['StatusCode'] == 0 else logs
            }
        except Exception as e:
            # Kill container if it's still running
            try:
                container.kill()
            except:
                pass
            
            raise Exception(f"Execution timed out or failed: {str(e)}")
    
    finally:
        # Clean up
        if os.path.exists(code_file):
            os.unlink(code_file)
        
        # Ensure container is removed
        try:
            container = docker_client.containers.get(container_name)
            container.remove(force=True)
        except:
            pass

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
