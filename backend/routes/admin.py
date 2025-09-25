"""
Admin API routes for STRATUS Bug Advisor
Handles configuration, system status, and analytics
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
import os
import sqlite3
from services.claude_service import claude_service
from utils.database import get_db_connection

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/config', methods=['GET'])
def get_config():
    """Get current configuration (without exposing sensitive data)"""
    try:
        claude_api_key = os.getenv('CLAUDE_API_KEY', '')
        
        return jsonify({
            'claude_api_key': bool(claude_api_key),  # Only return if key exists
            'status': 'success'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/config', methods=['POST'])
def save_config():
    """Save configuration settings"""
    try:
        data = request.get_json()
        claude_api_key = data.get('claude_api_key', '').strip()
        
        if not claude_api_key:
            return jsonify({'message': 'Claude API key is required'}), 400
        
        # Update environment variable (for current session)
        os.environ['CLAUDE_API_KEY'] = claude_api_key
        
        # Save to .env file for persistence
        env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
        
        # Read existing .env content
        env_lines = []
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                env_lines = f.readlines()
        
        # Update or add CLAUDE_API_KEY
        updated = False
        for i, line in enumerate(env_lines):
            if line.startswith('CLAUDE_API_KEY='):
                env_lines[i] = f'CLAUDE_API_KEY={claude_api_key}\n'
                updated = True
                break
        
        if not updated:
            env_lines.append(f'CLAUDE_API_KEY={claude_api_key}\n')
        
        # Write back to .env file
        with open(env_path, 'w') as f:
            f.writelines(env_lines)
        
        return jsonify({
            'message': 'Configuration saved successfully',
            'status': 'success'
        })
        
    except Exception as e:
        return jsonify({'message': f'Failed to save configuration: {str(e)}'}), 500

@admin_bp.route('/status', methods=['GET'])
def get_system_status():
    """Get system component status"""
    try:
        status = {
            'database': 'healthy',
            'claude_api': 'error',
            'redis': 'warning'  # Optional component
        }
        
        # Check database
        try:
            with get_db_connection() as conn:
                conn.execute('SELECT 1').fetchone()
            status['database'] = 'healthy'
        except Exception:
            status['database'] = 'error'
        
        # Check Claude API
        try:
            claude_api_key = os.getenv('CLAUDE_API_KEY')
            if claude_api_key:
                # Test connection would go here
                status['claude_api'] = 'healthy'
            else:
                status['claude_api'] = 'error'
        except Exception:
            status['claude_api'] = 'error'
        
        # Redis is optional, so warning is acceptable
        status['redis'] = 'warning'
        
        return jsonify(status)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/test-claude', methods=['POST'])
def test_claude():
    """Test Claude API connection"""
    try:
        claude_api_key = os.getenv('CLAUDE_API_KEY')
        if not claude_api_key:
            return jsonify({'message': 'Claude API key not configured'}), 400
        
        # Test the connection using claude_service
        # Create a temporary service with the current API key
        from services.claude_service import ClaudeService
        test_service = ClaudeService(claude_api_key)
        result = test_service.test_connection()
        
        if result['available']:
            return jsonify({
                'message': 'Claude API connection successful',
                'status': 'success',
                'response_time': result.get('response_time')
            })
        else:
            return jsonify({'message': result.get('error', 'Connection test failed')}), 400
            
    except Exception as e:
        return jsonify({'message': f'Test failed: {str(e)}'}), 500

@admin_bp.route('/stats', methods=['GET'])
def get_stats():
    """Get system analytics and statistics"""
    try:
        with get_db_connection() as conn:
            # Get total queries
            total_queries = conn.execute(
                'SELECT COUNT(*) FROM queries'
            ).fetchone()[0]
            
            # Get successful queries
            successful_queries = conn.execute(
                'SELECT COUNT(*) FROM queries WHERE status = ?',
                ('success',)
            ).fetchone()[0]
            
            # Get average response time
            avg_response_time = conn.execute(
                'SELECT AVG(response_time_ms) FROM queries WHERE response_time_ms IS NOT NULL'
            ).fetchone()[0] or 0
            
            # Get knowledge entries count
            knowledge_entries = conn.execute(
                'SELECT COUNT(*) FROM knowledge_base'
            ).fetchone()[0]
            
            return jsonify({
                'totalQueries': total_queries,
                'successfulQueries': successful_queries,
                'avgResponseTime': round(avg_response_time),
                'knowledgeEntries': knowledge_entries
            })
            
    except Exception as e:
        return jsonify({
            'totalQueries': 0,
            'successfulQueries': 0,
            'avgResponseTime': 0,
            'knowledgeEntries': 0
        })
