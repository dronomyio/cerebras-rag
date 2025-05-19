#!/usr/bin/env python3
"""
Flask Web Application for Cerebras RAG
--------------------------------------
Provides a chat interface with authentication for querying Ruppert's book
using Cerebras inference and Weaviate.
"""

import os
import json
import uuid
import logging
import requests
from datetime import datetime, timedelta
from functools import wraps

import weaviate
import redis
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_socketio import SocketIO, emit
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-change-in-production')
app.config['SESSION_TYPE'] = 'redis'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)

# Initialize Socket.IO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Initialize Redis
redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST', 'redis'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    password=os.getenv('REDIS_PASSWORD', ''),
    decode_responses=True
)

# Initialize Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, id, username, email):
        self.id = id
        self.username = username
        self.email = email

# User database (Redis-based)
def get_user_by_id(user_id):
    user_data = redis_client.hgetall(f"user:{user_id}")
    if not user_data:
        return None
    return User(user_id, user_data.get('username'), user_data.get('email'))

def get_user_by_email(email):
    user_id = redis_client.get(f"email:{email}")
    if not user_id:
        return None
    return get_user_by_id(user_id)

def create_user(username, email, password):
    user_id = str(uuid.uuid4())
    password_hash = generate_password_hash(password)
    
    # Store user data in Redis
    redis_client.hset(f"user:{user_id}", mapping={
        'username': username,
        'email': email,
        'password_hash': password_hash
    })
    redis_client.set(f"email:{email}", user_id)
    
    return User(user_id, username, email)

# Login form
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

# Registration form
class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    submit = SubmitField('Register')

# Flask-Login user loader
@login_manager.user_loader
def load_user(user_id):
    return get_user_by_id(user_id)

# Weaviate client
def get_weaviate_client():
    weaviate_url = os.getenv('WEAVIATE_URL', 'http://weaviate:8080')
    weaviate_api_key = os.getenv('WEAVIATE_API_KEY')
    
    auth_config = weaviate.auth.AuthApiKey(api_key=weaviate_api_key) if weaviate_api_key else None
    
    return weaviate.Client(
        url=weaviate_url,
        auth_client_secret=auth_config
    )

# Cerebras client
def query_cerebras(prompt, conversation_history=None):
    api_key = os.getenv('CEREBRAS_API_KEY')
    api_url = os.getenv('CEREBRAS_API_URL', 'https://api.cerebras.ai/v1/text/completions')
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    # Format conversation history if provided
    formatted_history = ""
    if conversation_history:
        for msg in conversation_history:
            role = "User" if msg['role'] == 'user' else "Assistant"
            formatted_history += f"{role}: {msg['content']}\n\n"
    
    # Prepare the request payload
    payload = {
        'model': 'cerebras/Cerebras-GPT-4.5-8B',  # Adjust model as needed
        'prompt': prompt,
        'max_tokens': 1024,
        'temperature': 0.2,
        'stream': False
    }
    
    try:
        response = requests.post(api_url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()['choices'][0]['text']
    except Exception as e:
        logger.error(f"Error querying Cerebras API: {e}")
        return f"Error: Unable to get response from Cerebras API. {str(e)}"

# Code execution
def execute_code(code, language):
    code_executor_url = os.getenv('CODE_EXECUTOR_URL', 'http://code-executor:5000')
    
    payload = {
        'code': code,
        'language': language
    }
    
    try:
        response = requests.post(f"{code_executor_url}/execute", json=payload)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Error executing code: {e}")
        return {
            'success': False,
            'stdout': '',
            'stderr': f"Error: Unable to execute code. {str(e)}"
        }

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('chat'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = get_user_by_email(form.email.data)
        if user and check_password_hash(redis_client.hget(f"user:{user.id}", 'password_hash'), form.password.data):
            login_user(user)
            return redirect(url_for('chat'))
        flash('Invalid email or password')
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        if get_user_by_email(form.email.data):
            flash('Email already registered')
            return render_template('register.html', form=form)
        
        user = create_user(form.username.data, form.email.data, form.password.data)
        login_user(user)
        return redirect(url_for('chat'))
    return render_template('register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/chat')
@login_required
def chat():
    return render_template('chat.html', username=current_user.username)

@app.route('/health')
def health():
    return jsonify({'status': 'ok'})

# API endpoints
@app.route('/api/conversation', methods=['GET'])
@login_required
def get_conversation():
    conversation_id = request.args.get('id')
    if not conversation_id:
        return jsonify({'error': 'Conversation ID required'}), 400
    
    # Get conversation from Redis
    conversation_key = f"conversation:{current_user.id}:{conversation_id}"
    if not redis_client.exists(conversation_key):
        return jsonify({'error': 'Conversation not found'}), 404
    
    conversation = []
    for i in range(redis_client.llen(conversation_key)):
        message = json.loads(redis_client.lindex(conversation_key, i))
        conversation.append(message)
    
    return jsonify({'conversation': conversation})

@app.route('/api/conversations', methods=['GET'])
@login_required
def get_conversations():
    # Get all conversation IDs for the user
    pattern = f"conversation:{current_user.id}:*"
    conversation_keys = redis_client.keys(pattern)
    
    conversations = []
    for key in conversation_keys:
        conversation_id = key.split(':')[-1]
        # Get the first message to use as title
        first_message = json.loads(redis_client.lindex(key, 0))
        title = first_message.get('content', 'Untitled')[:50] + '...'
        
        # Get timestamp of last message
        last_message = json.loads(redis_client.lindex(key, -1))
        timestamp = last_message.get('timestamp', datetime.now().isoformat())
        
        conversations.append({
            'id': conversation_id,
            'title': title,
            'timestamp': timestamp
        })
    
    # Sort by timestamp, newest first
    conversations.sort(key=lambda x: x['timestamp'], reverse=True)
    
    return jsonify({'conversations': conversations})

@app.route('/api/execute-code', methods=['POST'])
@login_required
def api_execute_code():
    data = request.json
    code = data.get('code')
    language = data.get('language', 'python')
    
    if not code:
        return jsonify({'error': 'Code required'}), 400
    
    result = execute_code(code, language)
    return jsonify(result)

# Socket.IO events
@socketio.on('connect')
def handle_connect():
    if not current_user.is_authenticated:
        return False
    logger.info(f"User {current_user.username} connected")

@socketio.on('disconnect')
def handle_disconnect():
    logger.info(f"User {current_user.username if current_user.is_authenticated else 'Anonymous'} disconnected")

@socketio.on('new_conversation')
def handle_new_conversation():
    conversation_id = str(uuid.uuid4())
    emit('conversation_created', {'id': conversation_id})
    return conversation_id

@socketio.on('message')
def handle_message(data):
    user_message = data.get('message')
    conversation_id = data.get('conversation_id')
    
    if not user_message or not conversation_id:
        emit('error', {'message': 'Message and conversation ID required'})
        return
    
    # Store user message
    conversation_key = f"conversation:{current_user.id}:{conversation_id}"
    user_message_obj = {
        'role': 'user',
        'content': user_message,
        'timestamp': datetime.now().isoformat()
    }
    redis_client.rpush(conversation_key, json.dumps(user_message_obj))
    
    # Get conversation history
    conversation = []
    for i in range(redis_client.llen(conversation_key)):
        message = json.loads(redis_client.lindex(conversation_key, i))
        conversation.append(message)
    
    # Query Weaviate for relevant chunks
    try:
        weaviate_client = get_weaviate_client()
        query_result = weaviate_client.query.get(
            "RuppertContent", 
            ["content", "chapterNumber", "chapterTitle", "sectionNumber", "sectionTitle", "hasCode", "codeBlocks", "codeLanguages"]
        ).with_near_text({
            "concepts": [user_message]
        }).with_limit(5).do()
        
        chunks = query_result['data']['Get']['RuppertContent']
    except Exception as e:
        logger.error(f"Error querying Weaviate: {e}")
        chunks = []
    
    # Format context for Cerebras
    context = ""
    sources = []
    
    for i, chunk in enumerate(chunks):
        context += f"\nPassage {i+1}:\n"
        
        # Add chapter and section info
        chapter_info = f"Chapter {chunk.get('chapterNumber', 'N/A')}: {chunk.get('chapterTitle', 'N/A')}"
        if chunk.get('sectionNumber') and chunk.get('sectionTitle'):
            chapter_info += f", Section {chunk.get('sectionNumber')}: {chunk.get('sectionTitle')}"
        
        context += f"{chapter_info}\n\n"
        context += chunk.get('content', '') + "\n\n"
        
        # Add code blocks if present
        code_blocks = chunk.get('codeBlocks', [])
        code_languages = chunk.get('codeLanguages', [])
        
        for j, (code, lang) in enumerate(zip(code_blocks, code_languages)):
            context += f"Code Example ({lang}):\n```{lang}\n{code}\n```\n\n"
        
        # Add to sources
        sources.append({
            'chapter': chunk.get('chapterNumber', 'N/A'),
            'chapterTitle': chunk.get('chapterTitle', 'N/A'),
            'section': chunk.get('sectionNumber', 'N/A'),
            'sectionTitle': chunk.get('sectionTitle', 'N/A')
        })
    
    # Create prompt for Cerebras
    prompt = f"""You are a financial engineering assistant with expertise in statistics and data analysis.
Based on the following passages from Ruppert's "Statistics and Data Analysis for Financial Engineering" book, 
answer the user's question. Include relevant statistical formulas and code examples if available.

{context}

Previous conversation:
"""
    
    # Add conversation history to prompt
    for msg in conversation[:-1]:  # Exclude the current message
        role = "User" if msg['role'] == 'user' else "Assistant"
        prompt += f"{role}: {msg['content']}\n\n"
    
    prompt += f"User: {user_message}\n\nAssistant:"
    
    # Query Cerebras
    try:
        response = query_cerebras(prompt)
    except Exception as e:
        logger.error(f"Error querying Cerebras: {e}")
        response = "I'm sorry, I encountered an error while processing your request. Please try again later."
    
    # Store assistant response
    assistant_message_obj = {
        'role': 'assistant',
        'content': response,
        'sources': sources,
        'timestamp': datetime.now().isoformat()
    }
    redis_client.rpush(conversation_key, json.dumps(assistant_message_obj))
    
    # Set expiration on conversation (30 days)
    redis_client.expire(conversation_key, 60 * 60 * 24 * 30)
    
    # Send response to client
    emit('message', {
        'message': response,
        'sources': sources
    })

# Main entry point
if __name__ == '__main__':
    # Create admin user if it doesn't exist
    admin_email = os.getenv('ADMIN_EMAIL', 'admin@example.com')
    admin_password = os.getenv('ADMIN_PASSWORD', 'adminpassword')
    
    if not get_user_by_email(admin_email):
        create_user('Admin', admin_email, admin_password)
        logger.info(f"Created admin user: {admin_email}")
    
    # Start the server
    socketio.run(app, host='0.0.0.0', port=8000, debug=False)
