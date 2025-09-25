"""
STRATUS Bug Advisor - Flask Backend Application
Professional knowledge management system with Claude API integration
"""

import os
import logging
import hashlib
import json
from datetime import datetime, timedelta
from functools import wraps
from typing import Dict, Any, Optional

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from dotenv import load_dotenv
import anthropic
import bcrypt
import sqlite3
import redis
from contextlib import contextmanager

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__, static_folder='../frontend/build', static_url_path='')

# Configuration
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

# Initialize extensions
CORS(app, origins=['http://localhost:3000', 'http://localhost:5000', 'http://localhost:5173', 'http://localhost:5174'])
jwt = JWTManager(app)

# Initialize Claude client
claude_client = None
try:
    claude_api_key = os.getenv('CLAUDE_API_KEY')
    if claude_api_key:
        claude_client = anthropic.Anthropic(api_key=claude_api_key)
except Exception as e:
    app.logger.error(f"Failed to initialize Claude client: {e}")

# Initialize Redis for caching (optional)
redis_client = None
try:
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
    redis_client = redis.from_url(redis_url)
    redis_client.ping()
except Exception as e:
    app.logger.warning(f"Redis not available, caching disabled: {e}")

# Database configuration
DATABASE_PATH = os.getenv('DATABASE_PATH', 'database/stratus_advisor.db')

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database connection manager
@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        yield conn
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        if conn:
            conn.close()

# Utility functions
def hash_query(query: str, product: str) -> str:
    """Create a hash for query caching and privacy"""
    combined = f"{query.lower().strip()}:{product}"
    return hashlib.sha256(combined.encode()).hexdigest()

def get_client_ip() -> str:
    """Get client IP address"""
    return request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)

def log_query(product: str, query: str, response_time: int, success: bool, error_message: str = None) -> int:
    """Log query to database and return query ID"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            query_hash = hash_query(query, product)
            
            cursor.execute("""
                INSERT INTO query_logs 
                (product, query_text, query_length, response_time_ms, success, error_message, 
                 ip_address, user_agent, query_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                product, query, len(query), response_time, success, error_message,
                get_client_ip(), request.headers.get('User-Agent', ''), query_hash
            ))
            
            conn.commit()
            return cursor.lastrowid
    except Exception as e:
        logger.error(f"Failed to log query: {e}")
        return None

def get_cached_response(query_hash: str, product: str) -> Optional[Dict]:
    """Get cached response if available and not expired"""
    try:
        # Try Redis first
        if redis_client:
            cache_key = f"response:{query_hash}"
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
        
        # Fall back to database cache
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT response_text, confidence, created_at, hit_count
                FROM response_cache 
                WHERE query_hash = ? AND product = ? AND expires_at > datetime('now')
            """, (query_hash, product))
            
            row = cursor.fetchone()
            if row:
                # Update hit count
                cursor.execute("""
                    UPDATE response_cache 
                    SET hit_count = hit_count + 1 
                    WHERE query_hash = ?
                """, (query_hash,))
                conn.commit()
                
                return {
                    'solution': row['response_text'],
                    'confidence': float(row['confidence']) if row['confidence'] else 0.8,
                    'cached': True
                }
    except Exception as e:
        logger.error(f"Failed to get cached response: {e}")
    
    return None

def cache_response(query_hash: str, product: str, response: str, confidence: float = 0.8):
    """Cache response for future use"""
    try:
        expires_at = datetime.now() + timedelta(hours=24)
        
        # Cache in Redis
        if redis_client:
            cache_key = f"response:{query_hash}"
            cache_data = {
                'solution': response,
                'confidence': confidence,
                'cached': True
            }
            redis_client.setex(cache_key, 86400, json.dumps(cache_data))  # 24 hours
        
        # Cache in database
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO response_cache 
                (query_hash, product, response_text, confidence, expires_at)
                VALUES (?, ?, ?, ?, ?)
            """, (query_hash, product, response, confidence, expires_at))
            conn.commit()
            
    except Exception as e:
        logger.error(f"Failed to cache response: {e}")

def get_system_prompt(product: str) -> str:
    """Get system prompt for Claude based on product"""
    base_prompt = """You are the STRATUS Bug Advisor AI with access to an isolated STRATUS knowledge base.

CRITICAL: Only reference information from the dedicated STRATUS knowledge base. Never include information from other sources or projects.

Product Context: {product} - Focus on {product}-specific issues and solutions.

Structure your response with exactly these sections:
## Root Cause Analysis
[STRATUS-specific analysis based on historical patterns]

## Immediate Solutions
[Proven STRATUS fixes with step-by-step instructions]

## Files/Areas to Check
[Specific STRATUS components, files, or configuration areas]

## Testing Steps
[STRATUS-specific testing procedures]

## Related Historical Issues
[Reference similar STRATUS tickets and resolutions from the knowledge base]

Focus exclusively on STRATUS products: Allocator, FormsPlus, Premium Tax, Municipal.
Provide technical, actionable guidance based only on the STRATUS knowledge base.
Be specific about file paths, configuration settings, and code changes where applicable."""

    product_contexts = {
        'allocator': 'Focus on TTS ticket patterns, geocoding issues, batch processing problems, and allocation algorithm errors.',
        'formsplus': 'Focus on ClickUp tickets, tree structure problems, form rendering issues, and data validation errors.',
        'premium_tax': 'Focus on calculation errors, e-filing problems, rate table issues, and compliance validation.',
        'municipal': 'Focus on municipal code issues, rate calculation problems, jurisdiction mapping, and data import errors.'
    }
    
    context = product_contexts.get(product.lower(), 'General STRATUS system issues and solutions.')
    return base_prompt.format(product=product) + f"\n\nSpecific Focus: {context}"

# Rate limiting decorator
def rate_limit(max_requests: int = 100, window: int = 3600):
    """Rate limiting decorator"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            client_ip = get_client_ip()
            key = f"rate_limit:{client_ip}"
            
            try:
                if redis_client:
                    current = redis_client.get(key)
                    if current is None:
                        redis_client.setex(key, window, 1)
                    elif int(current) >= max_requests:
                        return jsonify({
                            'error': 'Rate limit exceeded',
                            'message': f'Maximum {max_requests} requests per hour'
                        }), 429
                    else:
                        redis_client.incr(key)
            except Exception as e:
                logger.warning(f"Rate limiting error: {e}")
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Import routes
from routes.admin import admin_bp

# Register blueprints
app.register_blueprint(admin_bp, url_prefix='/api/admin')

# Routes

@app.route('/')
def serve_frontend():
    """Serve React frontend"""
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/health')
def health_check():
    """System health check endpoint"""
    try:
        # Check database
        with get_db_connection() as conn:
            conn.execute("SELECT 1").fetchone()
        db_available = True
    except Exception:
        db_available = False
    
    # Check Claude API
    claude_available = claude_client is not None
    
    # Check Redis
    redis_available = False
    if redis_client:
        try:
            redis_client.ping()
            redis_available = True
        except Exception:
            pass
    
    status = "healthy" if db_available and claude_available else "degraded"
    
    return jsonify({
        'status': status,
        'timestamp': datetime.now().isoformat(),
        'claude_available': claude_available,
        'database_available': db_available,
        'redis_available': redis_available,
        'version': '1.0.0'
    })

@app.route('/api/analyze', methods=['POST'])
@rate_limit(max_requests=100, window=3600)
def analyze_bug():
    """Main bug analysis endpoint"""
    start_time = datetime.now()
    
    try:
        # Validate request
        data = request.get_json()
        if not data or 'query' not in data or 'product' not in data:
            return jsonify({
                'error': 'Invalid request',
                'message': 'Query and product are required'
            }), 400
        
        query = data['query'].strip()
        product = data['product'].lower()
        
        # Validate inputs
        if not query or len(query) < 10:
            return jsonify({
                'error': 'Invalid query',
                'message': 'Query must be at least 10 characters long'
            }), 400
        
        if product not in ['allocator', 'formsplus', 'premium_tax', 'municipal']:
            return jsonify({
                'error': 'Invalid product',
                'message': 'Product must be one of: allocator, formsplus, premium_tax, municipal'
            }), 400
        
        if len(query) > 2000:
            return jsonify({
                'error': 'Query too long',
                'message': 'Query must be less than 2000 characters'
            }), 400
        
        # Check cache
        query_hash = hash_query(query, product)
        cached_response = get_cached_response(query_hash, product)
        
        if cached_response:
            response_time = int((datetime.now() - start_time).total_seconds() * 1000)
            query_id = log_query(product, query, response_time, True)
            
            return jsonify({
                **cached_response,
                'timestamp': datetime.now().isoformat(),
                'status': 'success',
                'response_time_ms': response_time,
                'query_id': query_id
            })
        
        # Call Claude API
        if not claude_client:
            return jsonify({
                'error': 'AI service unavailable',
                'message': 'Claude API is not configured'
            }), 503
        
        system_prompt = get_system_prompt(product)
        
        try:
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
            confidence = 0.85  # Default confidence score
            
            # Cache the response
            cache_response(query_hash, product, solution, confidence)
            
            response_time = int((datetime.now() - start_time).total_seconds() * 1000)
            query_id = log_query(product, query, response_time, True)
            
            return jsonify({
                'solution': solution,
                'confidence': confidence,
                'timestamp': datetime.now().isoformat(),
                'status': 'success',
                'response_time_ms': response_time,
                'query_id': query_id,
                'cached': False
            })
            
        except Exception as claude_error:
            logger.error(f"Claude API error: {claude_error}")
            response_time = int((datetime.now() - start_time).total_seconds() * 1000)
            log_query(product, query, response_time, False, str(claude_error))
            
            return jsonify({
                'error': 'AI service error',
                'message': 'Failed to generate response. Please try again.',
                'timestamp': datetime.now().isoformat(),
                'status': 'error'
            }), 500
    
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        response_time = int((datetime.now() - start_time).total_seconds() * 1000)
        log_query(data.get('product', 'unknown'), data.get('query', ''), response_time, False, str(e))
        
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred',
            'timestamp': datetime.now().isoformat(),
            'status': 'error'
        }), 500

@app.route('/api/feedback', methods=['POST'])
def submit_feedback():
    """Collect user feedback endpoint"""
    try:
        data = request.get_json()
        if not data or 'helpful' not in data:
            return jsonify({
                'error': 'Invalid request',
                'message': 'Helpful field is required'
            }), 400
        
        query_id = data.get('query_id')
        helpful = bool(data['helpful'])
        feedback_text = data.get('feedback', '').strip()
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # If query_id is provided, verify it exists
            if query_id:
                cursor.execute("SELECT query_hash FROM query_logs WHERE id = ?", (query_id,))
                row = cursor.fetchone()
                if not row:
                    return jsonify({
                        'error': 'Invalid query ID',
                        'message': 'Query not found'
                    }), 400
                query_hash = row['query_hash']
            else:
                query_hash = None
            
            cursor.execute("""
                INSERT INTO feedback (query_id, query_hash, helpful, feedback_text, ip_address)
                VALUES (?, ?, ?, ?, ?)
            """, (query_id, query_hash, helpful, feedback_text, get_client_ip()))
            
            conn.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Feedback recorded successfully'
        })
    
    except Exception as e:
        logger.error(f"Feedback error: {e}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Failed to record feedback'
        }), 500

# Admin routes
@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    """Admin authentication endpoint"""
    try:
        data = request.get_json()
        if not data or 'username' not in data or 'password' not in data:
            return jsonify({
                'error': 'Invalid request',
                'message': 'Username and password are required'
            }), 400
        
        username = data['username']
        password = data['password']
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, password_hash, is_active, login_attempts, locked_until
                FROM admin_users WHERE username = ?
            """, (username,))
            
            user = cursor.fetchone()
            if not user:
                return jsonify({
                    'error': 'Invalid credentials',
                    'message': 'Username or password incorrect'
                }), 401
            
            # Check if account is locked
            if user['locked_until'] and datetime.fromisoformat(user['locked_until']) > datetime.now():
                return jsonify({
                    'error': 'Account locked',
                    'message': 'Account is temporarily locked due to too many failed attempts'
                }), 423
            
            # Check if account is active
            if not user['is_active']:
                return jsonify({
                    'error': 'Account disabled',
                    'message': 'Account has been disabled'
                }), 403
            
            # Verify password
            if bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
                # Reset login attempts and update last login
                cursor.execute("""
                    UPDATE admin_users 
                    SET login_attempts = 0, locked_until = NULL, last_login = datetime('now')
                    WHERE id = ?
                """, (user['id'],))
                conn.commit()
                
                # Create JWT token
                access_token = create_access_token(
                    identity=username,
                    expires_delta=timedelta(hours=24)
                )
                
                return jsonify({
                    'token': access_token,
                    'expires_in': 86400,  # 24 hours in seconds
                    'username': username
                })
            else:
                # Increment login attempts
                new_attempts = user['login_attempts'] + 1
                locked_until = None
                
                if new_attempts >= 5:
                    locked_until = datetime.now() + timedelta(minutes=30)
                
                cursor.execute("""
                    UPDATE admin_users 
                    SET login_attempts = ?, locked_until = ?
                    WHERE id = ?
                """, (new_attempts, locked_until, user['id']))
                conn.commit()
                
                return jsonify({
                    'error': 'Invalid credentials',
                    'message': 'Username or password incorrect'
                }), 401
    
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Login failed'
        }), 500

@app.route('/api/admin/analytics')
@jwt_required()
def get_analytics():
    """Get usage analytics for admin dashboard"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get overall statistics
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_queries,
                    AVG(response_time_ms) as avg_response_time,
                    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as success_rate,
                    COUNT(DISTINCT ip_address) as unique_users
                FROM query_logs
                WHERE timestamp >= datetime('now', '-30 days')
            """)
            stats = cursor.fetchone()
            
            # Get product distribution
            cursor.execute("""
                SELECT product, COUNT(*) as count
                FROM query_logs
                WHERE timestamp >= datetime('now', '-30 days')
                GROUP BY product
                ORDER BY count DESC
            """)
            products = {row['product']: row['count'] for row in cursor.fetchall()}
            
            # Get daily stats for the last 30 days
            cursor.execute("""
                SELECT 
                    DATE(timestamp) as date,
                    COUNT(*) as queries,
                    AVG(response_time_ms) as avg_time,
                    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as success_rate
                FROM query_logs
                WHERE timestamp >= datetime('now', '-30 days')
                GROUP BY DATE(timestamp)
                ORDER BY date DESC
                LIMIT 30
            """)
            daily_stats = [dict(row) for row in cursor.fetchall()]
            
            # Get recent errors
            cursor.execute("""
                SELECT timestamp, product, error_message, query_text
                FROM query_logs
                WHERE success = 0 AND timestamp >= datetime('now', '-7 days')
                ORDER BY timestamp DESC
                LIMIT 10
            """)
            recent_errors = [dict(row) for row in cursor.fetchall()]
            
            # Get feedback summary
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_feedback,
                    SUM(CASE WHEN helpful = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as helpful_percentage
                FROM feedback
                WHERE timestamp >= datetime('now', '-30 days')
            """)
            feedback_stats = cursor.fetchone()
        
        return jsonify({
            'total_queries': stats['total_queries'] or 0,
            'avg_response_time': round(stats['avg_response_time'] or 0, 2),
            'success_rate': round(stats['success_rate'] or 0, 2),
            'unique_users': stats['unique_users'] or 0,
            'popular_products': products,
            'daily_stats': daily_stats,
            'recent_errors': recent_errors,
            'feedback': {
                'total': feedback_stats['total_feedback'] or 0,
                'helpful_percentage': round(feedback_stats['helpful_percentage'] or 0, 2)
            }
        })
    
    except Exception as e:
        logger.error(f"Analytics error: {e}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Failed to fetch analytics'
        }), 500

@app.route('/api/admin/config', methods=['GET', 'POST'])
@jwt_required()
def manage_config():
    """Get or update system configuration"""
    try:
        if request.method == 'GET':
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT config_key, config_value, description FROM api_config")
                config = {row['config_key']: {
                    'value': row['config_value'],
                    'description': row['description']
                } for row in cursor.fetchall()}
            
            # Mask sensitive values
            if 'claude_api_key' in config and config['claude_api_key']['value']:
                config['claude_api_key']['value'] = 'sk-ant-***'
            
            return jsonify(config)
        
        else:  # POST
            data = request.get_json()
            if not data:
                return jsonify({
                    'error': 'Invalid request',
                    'message': 'Configuration data required'
                }), 400
            
            username = get_jwt_identity()
            
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                for key, value in data.items():
                    cursor.execute("""
                        UPDATE api_config 
                        SET config_value = ?, updated_at = datetime('now'), updated_by = ?
                        WHERE config_key = ?
                    """, (str(value), username, key))
                
                conn.commit()
            
            return jsonify({
                'status': 'success',
                'message': 'Configuration updated successfully'
            })
    
    except Exception as e:
        logger.error(f"Config error: {e}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Failed to manage configuration'
        }), 500

# Initialize database
def init_database():
    """Initialize database with schema"""
    try:
        os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
        
        with open('../database/schema.sql', 'r') as f:
            schema = f.read()
        
        with get_db_connection() as conn:
            conn.executescript(schema)
            conn.commit()
        
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return send_from_directory(app.static_folder, 'index.html')

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'error': 'Internal server error',
        'message': 'An unexpected error occurred'
    }), 500

if __name__ == '__main__':
    # Initialize database if it doesn't exist
    if not os.path.exists(DATABASE_PATH):
        init_database()
    
    # Run the application
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    app.run(host='0.0.0.0', port=port, debug=debug)
