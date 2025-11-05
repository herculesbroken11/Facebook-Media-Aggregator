from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import logging
from werkzeug.security import check_password_hash, generate_password_hash
import json

# Load environment variables (check current dir and parent dir)
load_dotenv()
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

app = Flask(__name__)

# Configuration
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET', 'supersecretkey')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
app.config['JWT_ALGORITHM'] = 'HS256'

# Initialize extensions
jwt = JWTManager(app)
CORS(app, origins="*")  # In production, specify your frontend URL

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASS', ''),
    'database': os.getenv('DB_NAME', 'facebook_aggregator')
}

# Password hashing is now handled via database

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_db_connection():
    """Create and return a database connection"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except psycopg2.Error as e:
        logger.error(f"Database connection error: {e}")
        raise


@app.route('/api/login', methods=['POST'])
def login():
    """Authenticate user and return JWT token"""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400

        # Query user from database
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("SELECT id, email, password_hash, name, is_active, is_admin FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        
        cursor.close()
        conn.close()

        if not user:
            return jsonify({'error': 'Invalid credentials'}), 401

        if not user['is_active']:
            return jsonify({'error': 'Account is disabled'}), 403

        # Check if user is admin
        if not user.get('is_admin', False):
            return jsonify({'error': 'Access denied. Admin privileges required.'}), 403

        # Verify password
        if check_password_hash(user['password_hash'], password):
            access_token = create_access_token(identity=email)
            # Convert UUID to string for JSON serialization
            user_id = str(user['id']) if user['id'] else None
            return jsonify({
                'access_token': access_token,
                'user': {
                    'email': user['email'],
                    'name': user['name'],
                    'id': user_id,
                    'is_admin': user['is_admin']
                }
            }), 200
        else:
            return jsonify({'error': 'Invalid credentials'}), 401

    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({'error': 'Login failed'}), 500


@app.route('/api/posts', methods=['GET'])
@jwt_required()
def get_posts():
    """Get paginated list of posts with optional filters"""
    try:
        # Get query parameters
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        author = request.args.get('author', '')
        keyword = request.args.get('keyword', '')
        group_id = request.args.get('group_id', '')
        sort_by = request.args.get('sort_by', 'created_at')  # created_at, reactions, comments, shares
        order = request.args.get('order', 'desc')  # asc, desc
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')

        # Validate sort_by and order
        valid_sort_fields = ['created_at', 'reactions', 'comments']
        if sort_by not in valid_sort_fields:
            sort_by = 'created_at'
        
        if order not in ['asc', 'desc']:
            order = 'desc'

        offset = (page - 1) * per_page

        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Build WHERE clause
        where_conditions = []
        params = []

        if author:
            where_conditions.append("author_name ILIKE %s")
            params.append(f"%{author}%")

        if keyword:
            where_conditions.append("text_content ILIKE %s")
            params.append(f"%{keyword}%")

        if group_id:
            where_conditions.append("group_id = %s")
            params.append(group_id)

        if date_from:
            where_conditions.append("created_at >= %s")
            params.append(date_from)

        if date_to:
            where_conditions.append("created_at <= %s")
            params.append(date_to)

        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"

        # Get total count
        count_query = f"SELECT COUNT(*) as total FROM fb_media_posts WHERE {where_clause}"
        cursor.execute(count_query, params)
        total = cursor.fetchone()['total']

        # Get posts
        query = f"""
            SELECT id, post_url, author_name, author_url, text_content, image_urls, 
                   video_urls, content_type, reactions, comments, created_at, group_id
            FROM fb_media_posts
            WHERE {where_clause}
            ORDER BY {sort_by} {order.upper()}
            LIMIT %s OFFSET %s
        """
        params.extend([per_page, offset])
        cursor.execute(query, params)
        posts = cursor.fetchall()

        # Convert to list of dicts and format dates
        posts_list = []
        for post in posts:
            post_dict = dict(post)
            # Convert post_url to post_id for frontend compatibility
            post_dict['post_id'] = post_dict.pop('post_url')
            # Convert author_name to author for frontend compatibility
            post_dict['author'] = post_dict.pop('author_name')
            # Convert text_content to content for frontend compatibility
            post_dict['content'] = post_dict.pop('text_content')
            # Handle JSONB image_urls - convert to single media_url or array
            if post_dict.get('image_urls'):
                if isinstance(post_dict['image_urls'], str):
                    try:
                        image_urls = json.loads(post_dict['image_urls'])
                    except:
                        image_urls = [post_dict['image_urls']]
                else:
                    image_urls = post_dict['image_urls']
                # Use first image as media_url for compatibility
                post_dict['media_url'] = image_urls[0] if image_urls and len(image_urls) > 0 else None
                post_dict['image_urls'] = image_urls if isinstance(image_urls, list) else [image_urls]
            else:
                post_dict['media_url'] = None
                post_dict['image_urls'] = []
            
            # Handle JSONB video_urls
            if post_dict.get('video_urls'):
                if isinstance(post_dict['video_urls'], str):
                    try:
                        video_urls = json.loads(post_dict['video_urls'])
                    except:
                        video_urls = [post_dict['video_urls']]
                else:
                    video_urls = post_dict['video_urls']
                post_dict['video_urls'] = video_urls if isinstance(video_urls, list) else [video_urls]
            else:
                post_dict['video_urls'] = []
            
            # Set content_type if not present
            if not post_dict.get('content_type'):
                if post_dict.get('video_urls') and len(post_dict['video_urls']) > 0:
                    post_dict['content_type'] = 'video'
                elif post_dict.get('image_urls') and len(post_dict['image_urls']) > 0:
                    post_dict['content_type'] = 'image'
                else:
                    post_dict['content_type'] = 'text'
            # Format date
            if post_dict.get('created_at'):
                post_dict['created_at'] = post_dict['created_at'].isoformat()
            # Remove shares (not in new schema)
            post_dict['shares'] = 0
            posts_list.append(post_dict)

        cursor.close()
        conn.close()

        return jsonify({
            'posts': posts_list,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page
            }
        }), 200

    except Exception as e:
        logger.error(f"Get posts error: {e}")
        return jsonify({'error': 'Failed to fetch posts'}), 500


@app.route('/api/posts/<post_id>', methods=['GET'])
@jwt_required()
def get_post(post_id):
    """Get detailed information about a specific post"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        query = """
            SELECT id, post_url, author_name, author_url, text_content, image_urls, 
                   video_urls, content_type, reactions, comments, created_at, group_id
            FROM fb_media_posts
            WHERE post_url = %s
        """
        cursor.execute(query, (post_id,))
        post = cursor.fetchone()

        cursor.close()
        conn.close()

        if post:
            post_dict = dict(post)
            # Convert to frontend-compatible format
            post_dict['post_id'] = post_dict.pop('post_url')
            post_dict['author'] = post_dict.pop('author_name')
            post_dict['content'] = post_dict.pop('text_content')
            
            # Handle JSONB image_urls
            if post_dict.get('image_urls'):
                if isinstance(post_dict['image_urls'], str):
                    try:
                        image_urls = json.loads(post_dict['image_urls'])
                    except:
                        image_urls = [post_dict['image_urls']]
                else:
                    image_urls = post_dict['image_urls']
                post_dict['media_url'] = image_urls[0] if image_urls and len(image_urls) > 0 else None
                post_dict['image_urls'] = image_urls if isinstance(image_urls, list) else [image_urls]
            else:
                post_dict['media_url'] = None
                post_dict['image_urls'] = []
            
            # Handle JSONB video_urls
            if post_dict.get('video_urls'):
                if isinstance(post_dict['video_urls'], str):
                    try:
                        video_urls = json.loads(post_dict['video_urls'])
                    except:
                        video_urls = [post_dict['video_urls']]
                else:
                    video_urls = post_dict['video_urls']
                post_dict['video_urls'] = video_urls if isinstance(video_urls, list) else [video_urls]
            else:
                post_dict['video_urls'] = []
            
            # Set content_type if not present
            if not post_dict.get('content_type'):
                if post_dict.get('video_urls') and len(post_dict['video_urls']) > 0:
                    post_dict['content_type'] = 'video'
                elif post_dict.get('image_urls') and len(post_dict['image_urls']) > 0:
                    post_dict['content_type'] = 'image'
                else:
                    post_dict['content_type'] = 'text'
            
            # Add shares (default to 0 since not in schema)
            post_dict['shares'] = 0
            
            if post_dict.get('created_at'):
                post_dict['created_at'] = post_dict['created_at'].isoformat()
            return jsonify(post_dict), 200
        else:
            return jsonify({'error': 'Post not found'}), 404

    except Exception as e:
        logger.error(f"Get post error: {e}")
        return jsonify({'error': 'Failed to fetch post'}), 500


@app.route('/api/groups', methods=['GET'])
@jwt_required()
def get_groups():
    """Get list of all groups with post counts"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute("""
            SELECT 
                group_id,
                COUNT(*) as post_count
            FROM fb_media_posts
            WHERE group_id IS NOT NULL
            GROUP BY group_id
            ORDER BY post_count DESC
        """)
        groups = cursor.fetchall()

        cursor.close()
        conn.close()

        groups_list = [dict(row) for row in groups]
        return jsonify({'groups': groups_list}), 200

    except Exception as e:
        logger.error(f"Get groups error: {e}")
        return jsonify({'error': 'Failed to fetch groups'}), 500


@app.route('/api/posts/export', methods=['GET'])
@jwt_required()
def export_posts():
    """Export posts in various formats (CSV, JSON, XLS)"""
    try:
        import csv
        import io
        from datetime import datetime

        format_type = request.args.get('format', 'json').lower()
        
        # Get all filters (same as get_posts)
        author = request.args.get('author', '')
        keyword = request.args.get('keyword', '')
        group_id = request.args.get('group_id', '')
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')

        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Build WHERE clause (same logic as get_posts)
        where_conditions = []
        params = []

        if author:
            where_conditions.append("author_name ILIKE %s")
            params.append(f"%{author}%")

        if keyword:
            where_conditions.append("text_content ILIKE %s")
            params.append(f"%{keyword}%")

        if group_id:
            where_conditions.append("group_id = %s")
            params.append(group_id)

        if date_from:
            where_conditions.append("created_at >= %s")
            params.append(date_from)

        if date_to:
            where_conditions.append("created_at <= %s")
            params.append(date_to)

        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"

        # Get all posts (no pagination for export)
        query = f"""
            SELECT id, post_url, author_name, author_url, text_content, image_urls, 
                   video_urls, content_type, reactions, comments, created_at, group_id
            FROM fb_media_posts
            WHERE {where_clause}
            ORDER BY created_at DESC
        """
        cursor.execute(query, params)
        posts = cursor.fetchall()

        cursor.close()
        conn.close()

        # Format posts for export
        posts_list = []
        for post in posts:
            post_dict = dict(post)
            # Handle JSONB image_urls
            if post_dict.get('image_urls'):
                if isinstance(post_dict['image_urls'], str):
                    try:
                        image_urls = json.loads(post_dict['image_urls'])
                    except:
                        image_urls = [post_dict['image_urls']]
                else:
                    image_urls = post_dict['image_urls']
                post_dict['image_urls'] = image_urls if isinstance(image_urls, list) else [image_urls]
            else:
                post_dict['image_urls'] = []
            
            # Handle JSONB video_urls
            if post_dict.get('video_urls'):
                if isinstance(post_dict['video_urls'], str):
                    try:
                        video_urls = json.loads(post_dict['video_urls'])
                    except:
                        video_urls = [post_dict['video_urls']]
                else:
                    video_urls = post_dict['video_urls']
                post_dict['video_urls'] = video_urls if isinstance(video_urls, list) else [video_urls]
            else:
                post_dict['video_urls'] = []
            
            if post_dict.get('created_at'):
                post_dict['created_at'] = post_dict['created_at'].isoformat()
            posts_list.append(post_dict)

        # Generate export based on format
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if format_type == 'csv':
            output = io.StringIO()
            if posts_list:
                writer = csv.DictWriter(output, fieldnames=[
                    'id', 'post_url', 'author_name', 'author_url', 'text_content', 
                    'reactions', 'comments', 'created_at', 'group_id', 'content_type',
                    'image_urls', 'video_urls'
                ])
                writer.writeheader()
                for post in posts_list:
                    row = post.copy()
                    # Convert arrays to strings for CSV
                    row['image_urls'] = ', '.join(row.get('image_urls', []))
                    row['video_urls'] = ', '.join(row.get('video_urls', []))
                    writer.writerow(row)
            
            response = app.response_class(
                output.getvalue(),
                mimetype='text/csv',
                headers={'Content-Disposition': f'attachment; filename=posts_export_{timestamp}.csv'}
            )
            return response

        elif format_type == 'xls' or format_type == 'xlsx':
            try:
                import openpyxl
                from openpyxl import Workbook
                
                wb = Workbook()
                ws = wb.active
                ws.title = "Posts"
                
                # Headers
                headers = ['Post URL', 'Author Name', 'Author URL', 'Text Content', 
                          'Reactions', 'Comments', 'Created At', 'Group ID', 'Content Type',
                          'Image URLs', 'Video URLs']
                ws.append(headers)
                
                # Data rows
                for post in posts_list:
                    row = [
                        post.get('post_url', ''),
                        post.get('author_name', ''),
                        post.get('author_url', ''),
                        post.get('text_content', ''),
                        post.get('reactions', 0),
                        post.get('comments', 0),
                        post.get('created_at', ''),
                        post.get('group_id', ''),
                        post.get('content_type', 'text'),
                        ', '.join(post.get('image_urls', [])),
                        ', '.join(post.get('video_urls', []))
                    ]
                    ws.append(row)
                
                # Save to BytesIO
                output = io.BytesIO()
                wb.save(output)
                output.seek(0)
                
                response = app.response_class(
                    output.read(),
                    mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    headers={'Content-Disposition': f'attachment; filename=posts_export_{timestamp}.xlsx'}
                )
                return response
            except ImportError:
                return jsonify({'error': 'XLSX export requires openpyxl. Install with: pip install openpyxl'}), 500

        else:  # Default to JSON
            response = app.response_class(
                json.dumps(posts_list, indent=2),
                mimetype='application/json',
                headers={'Content-Disposition': f'attachment; filename=posts_export_{timestamp}.json'}
            )
            return response

    except Exception as e:
        logger.error(f"Export posts error: {e}")
        return jsonify({'error': 'Failed to export posts'}), 500


@app.route('/api/stats', methods=['GET'])
@jwt_required()
def get_stats():
    """Get dashboard statistics"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Get total posts
        cursor.execute("SELECT COUNT(*) as total FROM fb_media_posts")
        total_posts = cursor.fetchone()['total']

        # Get total reactions and comments (shares not in schema)
        cursor.execute("""
            SELECT 
                SUM(reactions) as total_reactions,
                SUM(comments) as total_comments
            FROM fb_media_posts
        """)
        engagement = cursor.fetchone()

        # Get unique authors count
        cursor.execute("SELECT COUNT(DISTINCT author_name) as total_authors FROM fb_media_posts")
        total_authors = cursor.fetchone()['total_authors']

        # Get posts by date (last 7 days)
        cursor.execute("""
            SELECT DATE(created_at) as date, COUNT(*) as count
            FROM fb_media_posts
            WHERE created_at >= NOW() - INTERVAL '7 days'
            GROUP BY DATE(created_at)
            ORDER BY date ASC
        """)
        posts_by_date = cursor.fetchall()

        cursor.close()
        conn.close()

        # Format posts_by_date with ISO date strings
        posts_by_date_formatted = []
        for row in posts_by_date:
            row_dict = dict(row)
            if row_dict['date']:
                row_dict['date'] = row_dict['date'].isoformat()
            posts_by_date_formatted.append(row_dict)

        return jsonify({
            'total_posts': total_posts,
            'total_reactions': engagement['total_reactions'] or 0,
            'total_comments': engagement['total_comments'] or 0,
            'total_shares': 0,  # Not in schema, default to 0
            'total_authors': total_authors,
            'posts_by_date': posts_by_date_formatted
        }), 200

    except Exception as e:
        logger.error(f"Get stats error: {e}")
        return jsonify({'error': 'Failed to fetch statistics'}), 500


@app.route('/api/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get current user profile"""
    try:
        current_user_email = get_jwt_identity()
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute(
            "SELECT id, email, name, is_admin, created_at FROM users WHERE email = %s",
            (current_user_email,)
        )
        user = cursor.fetchone()
        
        cursor.close()
        conn.close()

        if user:
            user_dict = dict(user)
            user_dict['id'] = str(user_dict['id']) if user_dict['id'] else None
            if user_dict.get('created_at'):
                user_dict['created_at'] = user_dict['created_at'].isoformat()
            return jsonify(user_dict), 200
        else:
            return jsonify({'error': 'User not found'}), 404

    except Exception as e:
        logger.error(f"Get profile error: {e}")
        return jsonify({'error': 'Failed to fetch profile'}), 500


@app.route('/api/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update user profile (name and email)"""
    try:
        current_user_email = get_jwt_identity()
        data = request.get_json()
        new_email = data.get('email', '').strip()
        new_name = data.get('name', '').strip()

        if not new_email:
            return jsonify({'error': 'Email is required'}), 400

        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Check if new email is already taken by another user
        if new_email != current_user_email:
            cursor.execute("SELECT id FROM users WHERE email = %s AND email != %s", (new_email, current_user_email))
            if cursor.fetchone():
                cursor.close()
                conn.close()
                return jsonify({'error': 'Email already exists'}), 400

        # Update user profile
        cursor.execute("""
            UPDATE users 
            SET email = %s, name = %s, updated_at = CURRENT_TIMESTAMP
            WHERE email = %s
            RETURNING id, email, name, is_admin
        """, (new_email, new_name, current_user_email))
        
        updated_user = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()

        if updated_user:
            user_dict = dict(updated_user)
            user_dict['id'] = str(user_dict['id']) if user_dict['id'] else None
            
            # If email changed, user needs to login again with new email
            email_changed = new_email != current_user_email
            
            return jsonify({
                'user': user_dict,
                'email_changed': email_changed,
                'message': 'Profile updated successfully' + (' - Please login again with your new email' if email_changed else '')
            }), 200
        else:
            return jsonify({'error': 'User not found'}), 404

    except Exception as e:
        logger.error(f"Update profile error: {e}")
        return jsonify({'error': 'Failed to update profile'}), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        conn = get_db_connection()
        conn.close()
        return jsonify({'status': 'healthy', 'database': 'connected'}), 200
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'database': 'disconnected', 'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

