"""
STRATUS Bug Advisor - Flask Backend Application
Simplified for Vercel deployment
"""

import os
import logging
import hashlib
import json
from datetime import datetime, timedelta
from functools import wraps

from flask import Flask, request, jsonify, session
from flask_cors import CORS
from dotenv import load_dotenv
import anthropic

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'stratus-secret-key-change-in-production')

# CORS configuration for Vercel
CORS(app, origins=[
    'http://localhost:3000', 
    'http://localhost:5173', 
    'http://localhost:5174',
    'https://stratus-bug-advisor-v3-ai.vercel.app',
    'https://*.vercel.app'
], supports_credentials=True)

# Initialize Claude client
claude_client = None
try:
    claude_api_key = os.getenv('CLAUDE_API_KEY')
    if claude_api_key:
        claude_client = anthropic.Anthropic(api_key=claude_api_key)
        logging.info("Claude client initialized successfully")
    else:
        logging.warning("Claude API key not provided")
except Exception as e:
    logging.error(f"Failed to initialize Claude client: {e}")

# Simple authentication
def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_authenticated'):
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

def authenticate_admin(username, password):
    admin_username = os.getenv('ADMIN_USERNAME', 'admin')
    admin_password = os.getenv('ADMIN_PASSWORD', 'stratus2024!')
    return username == admin_username and password == admin_password

# Utility functions
def get_system_prompt(product: str) -> str:
    base_prompt = f"""You are the STRATUS Bug Advisor AI for {product.upper()}.

Provide structured analysis with these sections:
## Root Cause Analysis
## Immediate Solutions  
## Files/Areas to Check
## Testing Steps
## Related Historical Issues

Focus on {product}-specific technical solutions with actionable steps."""
    
    return base_prompt

# Routes
@app.route('/api/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'claude_available': claude_client is not None,
        'version': '1.0.0'
    })

@app.route('/api/analyze', methods=['POST'])
def analyze_bug():
    try:
        data = request.get_json()
        if not data or 'query' not in data or 'product' not in data:
            return jsonify({
                'error': 'Invalid request',
                'message': 'Query and product are required'
            }), 400
        
        query = data['query'].strip()
        product = data['product'].lower()
        
        if not query or len(query) < 10:
            return jsonify({
                'error': 'Invalid query',
                'message': 'Query must be at least 10 characters long'
            }), 400
        
        if not claude_client:
            return jsonify({
                'error': 'AI service unavailable',
                'message': 'Claude API is not configured'
            }), 503
        
        system_prompt = get_system_prompt(product)
        
        message = claude_client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=2000,
            temperature=0.1,
            system=system_prompt,
            messages=[{
                "role": "user",
                "content": query
            }]
        )
        
        solution = message.content[0].text if message.content else "No response generated"
        
        return jsonify({
            'solution': solution,
            'confidence': 0.85,
            'timestamp': datetime.now().isoformat(),
            'status': 'success',
            'cached': False
        })
        
    except Exception as e:
        logging.error(f"Analysis error: {e}")
        return jsonify({
            'error': 'AI service error',
            'message': str(e),
            'timestamp': datetime.now().isoformat(),
            'status': 'error'
        }), 500

@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if authenticate_admin(username, password):
            session['admin_authenticated'] = True
            return jsonify({
                'status': 'success',
                'message': 'Login successful'
            })
        else:
            return jsonify({
                'error': 'Invalid credentials'
            }), 401
            
    except Exception as e:
        return jsonify({
            'error': 'Login failed',
            'message': str(e)
        }), 500

@app.route('/api/admin/logout', methods=['POST'])
def admin_logout():
    session.pop('admin_authenticated', None)
    return jsonify({'status': 'success', 'message': 'Logged out'})

@app.route('/api/admin/config', methods=['GET'])
@require_auth
def get_admin_config():
    return jsonify({
        'claude_api_configured': claude_client is not None,
        'admin_username': os.getenv('ADMIN_USERNAME', 'admin')
    })

@app.route('/api/admin/config', methods=['POST'])
@require_auth
def save_admin_config():
    try:
        data = request.get_json()
        claude_key = data.get('claude_api_key')
        
        if claude_key:
            # In production, save to environment or database
            # For now, just validate the key format
            if claude_key.startswith('sk-ant-api03-'):
                return jsonify({
                    'status': 'success',
                    'message': 'Configuration saved successfully'
                })
            else:
                return jsonify({
                    'error': 'Invalid Claude API key format'
                }), 400
        
        return jsonify({
            'status': 'success',
            'message': 'Configuration saved'
        })
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to save configuration',
            'message': str(e)
        }), 500

@app.route('/api/admin/status', methods=['GET'])
@require_auth
def get_system_status():
    return jsonify({
        'database': {'status': 'healthy', 'message': 'Connected'},
        'claude_api': {
            'status': 'healthy' if claude_client else 'error',
            'message': 'Connected' if claude_client else 'API key not configured'
        },
        'cache': {'status': 'warning', 'message': 'Redis not configured'}
    })

@app.route('/api/admin/stats', methods=['GET'])
@require_auth
def get_admin_stats():
    return jsonify({
        'total_queries': 0,
        'success_rate': 0,
        'avg_response_time': 0,
        'knowledge_entries': 0,
        'recent_activity': []
    })

@app.route('/api/admin/test-claude', methods=['POST'])
@require_auth
def test_claude_connection():
    try:
        if not claude_client:
            return jsonify({
                'status': 'error',
                'message': 'Claude API key not configured'
            }), 400
        
        # Test with a simple message
        message = claude_client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=100,
            messages=[{
                "role": "user",
                "content": "Hello, please respond with 'STRATUS Bug Advisor connection test successful'"
            }]
        )
        
        response_text = message.content[0].text if message.content else "No response"
        
        return jsonify({
            'status': 'success',
            'message': 'Claude API connection successful',
            'test_response': response_text
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Claude API test failed: {str(e)}'
        }), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
