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


def extract_group_id_from_url(post_url):
    """Extract group_id from Facebook post URL if group_id column is empty.
    
    Handles URLs like:
    - https://www.facebook.com/groups/pardodbiznesupardoduznemumu/posts/...
    - https://www.facebook.com/groups/grasis.lt/posts/...
    - https://www.facebook.com/groups/287451671699882/posts/...
    """
    if not post_url:
        return None
    
    import re
    from urllib.parse import urlparse
    
    try:
        # Pattern to match /groups/{group_id}/ in the URL
        pattern = r'/groups/([^/]+)/'
        match = re.search(pattern, post_url)
        if match:
            return match.group(1)
    except Exception as e:
        logger.error(f"Error extracting group_id from URL: {e}")
    
    return None


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

        # Validate sort_by and order - map to facebook_posts column names
        sort_field_map = {
            'created_at': 'fp.created_at',
            'reactions': 'fp.reaction_count',
            'comments': 'fp.comment_count'
        }
        if sort_by not in sort_field_map:
            sort_by = 'created_at'
        
        # Get the actual database column name for sorting
        sort_field = sort_field_map[sort_by]
        
        if order not in ['asc', 'desc']:
            order = 'desc'

        offset = (page - 1) * per_page

        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Build WHERE clause - use facebook_posts column names
        where_conditions = []
        params = []

        if author:
            where_conditions.append("fp.user_name ILIKE %s")
            params.append(f"%{author}%")

        if keyword:
            where_conditions.append("fp.post_text ILIKE %s")
            params.append(f"%{keyword}%")

        if group_id:
            # Handle group filtering: check both group_id column and extract from post_url
            # Use COALESCE to get group_id from column or extract from URL
            where_conditions.append("""
                (COALESCE(fp.group_id, 
                    CASE 
                        WHEN fp.post_url ~ '/groups/([^/]+)/' 
                        THEN (regexp_match(fp.post_url, '/groups/([^/]+)/'))[1]
                        ELSE NULL 
                    END
                ) = %s)
            """)
            params.append(group_id)

        if date_from:
            # Convert date string to timestamp for comparison with BIGINT created_at
            # Use start of day (00:00:00) for date_from
            where_conditions.append("to_timestamp(fp.created_at) >= %s::date")
            params.append(date_from)

        if date_to:
            # Convert date string to timestamp for comparison with BIGINT created_at
            # Use end of day (23:59:59) for date_to to include the entire day
            where_conditions.append("to_timestamp(fp.created_at) < (%s::date + INTERVAL '1 day')")
            params.append(date_to)

        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"

        # Get total count from facebook_posts
        count_query = f"SELECT COUNT(*) as total FROM facebook_posts fp WHERE {where_clause}"
        cursor.execute(count_query, params)
        total = cursor.fetchone()['total']

        # Get posts with attachments aggregated
        # Convert BIGINT created_at to TIMESTAMP, aggregate attachments
        # Extract group_id from post_url if group_id column is empty
        query = f"""
            SELECT 
                fp.id,
                fp.post_url,
                fp.user_name as author_name,
                fp.user_url as author_url,
                fp.post_text as text_content,
                COALESCE(
                    fp.group_id,
                    CASE 
                        WHEN fp.post_url ~ '/groups/([^/]+)/' 
                        THEN (regexp_match(fp.post_url, '/groups/([^/]+)/'))[1]
                        ELSE NULL 
                    END
                ) as group_id,
                fp.reaction_count as reactions,
                fp.comment_count as comments,
                fp.share_count as shares,
                to_timestamp(fp.created_at) as created_at,
                COALESCE(
                    json_agg(
                        DISTINCT jsonb_build_object(
                            'url', fa.attachment_url,
                            'type', fa.attachment_type
                        )
                    ) FILTER (WHERE fa.attachment_type = 'image'),
                    '[]'::json
                ) as image_attachments,
                COALESCE(
                    json_agg(
                        DISTINCT jsonb_build_object(
                            'url', fa.attachment_url,
                            'type', fa.attachment_type
                        )
                    ) FILTER (WHERE fa.attachment_type = 'video'),
                    '[]'::json
                ) as video_attachments
            FROM facebook_posts fp
            LEFT JOIN facebook_attachments fa ON fp.post_url = fa.post_url
            WHERE {where_clause}
            GROUP BY fp.id, fp.post_url, fp.user_name, fp.user_url, fp.post_text, 
                     fp.group_id, fp.reaction_count, fp.comment_count, fp.share_count, fp.created_at
            ORDER BY {sort_field} {order.upper()}
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
            
            # Extract image URLs from image_attachments JSON array
            image_urls = []
            if post_dict.get('image_attachments'):
                if isinstance(post_dict['image_attachments'], str):
                    try:
                        image_attachments = json.loads(post_dict['image_attachments'])
                    except:
                        image_attachments = []
                else:
                    image_attachments = post_dict['image_attachments']
                
                # Extract URLs from attachment objects
                if isinstance(image_attachments, list):
                    image_urls = [att.get('url') for att in image_attachments if att and att.get('url')]
            
            # Extract video URLs from video_attachments JSON array
            video_urls = []
            if post_dict.get('video_attachments'):
                if isinstance(post_dict['video_attachments'], str):
                    try:
                        video_attachments = json.loads(post_dict['video_attachments'])
                    except:
                        video_attachments = []
                else:
                    video_attachments = post_dict['video_attachments']
                
                # Extract URLs from attachment objects
                if isinstance(video_attachments, list):
                    video_urls = [att.get('url') for att in video_attachments if att and att.get('url')]
            
            # Set image_urls and media_url
            post_dict['image_urls'] = image_urls
            post_dict['media_url'] = image_urls[0] if image_urls and len(image_urls) > 0 else None
            
            # Set video_urls
            post_dict['video_urls'] = video_urls
            
            # Remove the attachment fields (not needed in response)
            post_dict.pop('image_attachments', None)
            post_dict.pop('video_attachments', None)
            
            # Set content_type based on attachments
            if video_urls and len(video_urls) > 0:
                post_dict['content_type'] = 'video'
            elif image_urls and len(image_urls) > 0:
                post_dict['content_type'] = 'image'
            else:
                post_dict['content_type'] = 'text'
            
            # Format date
            if post_dict.get('created_at'):
                post_dict['created_at'] = post_dict['created_at'].isoformat()
            
            # shares is already in the data from share_count
            if post_dict.get('shares') is None:
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
            SELECT 
                fp.id,
                fp.post_url,
                fp.user_name as author_name,
                fp.user_url as author_url,
                fp.post_text as text_content,
                fp.group_id,
                fp.reaction_count as reactions,
                fp.comment_count as comments,
                fp.share_count as shares,
                to_timestamp(fp.created_at) as created_at,
                COALESCE(
                    json_agg(
                        DISTINCT jsonb_build_object(
                            'url', fa.attachment_url,
                            'type', fa.attachment_type
                        )
                    ) FILTER (WHERE fa.attachment_type = 'image'),
                    '[]'::json
                ) as image_attachments,
                COALESCE(
                    json_agg(
                        DISTINCT jsonb_build_object(
                            'url', fa.attachment_url,
                            'type', fa.attachment_type
                        )
                    ) FILTER (WHERE fa.attachment_type = 'video'),
                    '[]'::json
                ) as video_attachments
            FROM facebook_posts fp
            LEFT JOIN facebook_attachments fa ON fp.post_url = fa.post_url
            WHERE fp.post_url = %s
            GROUP BY fp.id, fp.post_url, fp.user_name, fp.user_url, fp.post_text, 
                     fp.group_id, fp.reaction_count, fp.comment_count, fp.share_count, fp.created_at
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
            
            # Extract image URLs from image_attachments JSON array
            image_urls = []
            if post_dict.get('image_attachments'):
                if isinstance(post_dict['image_attachments'], str):
                    try:
                        image_attachments = json.loads(post_dict['image_attachments'])
                    except:
                        image_attachments = []
                else:
                    image_attachments = post_dict['image_attachments']
                
                if isinstance(image_attachments, list):
                    image_urls = [att.get('url') for att in image_attachments if att and att.get('url')]
            
            # Extract video URLs from video_attachments JSON array
            video_urls = []
            if post_dict.get('video_attachments'):
                if isinstance(post_dict['video_attachments'], str):
                    try:
                        video_attachments = json.loads(post_dict['video_attachments'])
                    except:
                        video_attachments = []
                else:
                    video_attachments = post_dict['video_attachments']
                
                if isinstance(video_attachments, list):
                    video_urls = [att.get('url') for att in video_attachments if att and att.get('url')]
            
            # Set image_urls and media_url
            post_dict['image_urls'] = image_urls
            post_dict['media_url'] = image_urls[0] if image_urls and len(image_urls) > 0 else None
            
            # Set video_urls
            post_dict['video_urls'] = video_urls
            
            # Remove the attachment fields
            post_dict.pop('image_attachments', None)
            post_dict.pop('video_attachments', None)
            
            # Set content_type based on attachments
            if video_urls and len(video_urls) > 0:
                post_dict['content_type'] = 'video'
            elif image_urls and len(image_urls) > 0:
                post_dict['content_type'] = 'image'
            else:
                post_dict['content_type'] = 'text'
            
            # shares is already in the data from share_count
            if post_dict.get('shares') is None:
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
    """Get list of all groups with post counts, including groups extracted from post_url"""
    try:
        import re
        from urllib.parse import urlparse
        
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Get groups from both group_id column and extract from post_url when group_id is empty
        # First, let's check for posts with empty group_id to see what URLs we have
        cursor.execute("""
            SELECT post_url, group_id 
            FROM facebook_posts 
            WHERE (group_id IS NULL OR group_id = '') 
            AND post_url LIKE '%/groups/%'
            LIMIT 10
        """)
        sample_empty_groups = cursor.fetchall()
        if sample_empty_groups:
            logger.info(f"Sample posts with empty group_id: {[(r['post_url'][:100] if r['post_url'] else 'None', r['group_id']) for r in sample_empty_groups]}")
        
        # Check specifically for the target groups
        cursor.execute("""
            SELECT COUNT(*) as count, post_url
            FROM facebook_posts 
            WHERE post_url LIKE '%/groups/pardodbiznesupardoduznemumu%'
               OR post_url LIKE '%/groups/grasis.lt%'
            GROUP BY post_url
            LIMIT 5
        """)
        target_posts = cursor.fetchall()
        if target_posts:
            logger.info(f"Found {len(target_posts)} posts from target groups")
            for tp in target_posts:
                logger.info(f"  Post URL sample: {tp['post_url'][:100] if tp['post_url'] else 'None'}")
        
        # Get groups from both group_id column and extract from post_url when group_id is empty
        # Improved regex to handle URLs with or without trailing slash, and with query parameters
        cursor.execute("""
            WITH extracted_groups AS (
                SELECT 
                    COALESCE(
                        NULLIF(fp.group_id, ''),
                        CASE 
                            WHEN fp.post_url ~ '/groups/([^/?]+)' 
                            THEN (regexp_match(fp.post_url, '/groups/([^/?]+)'))[1]
                            ELSE NULL 
                        END
                    ) as group_id
                FROM facebook_posts fp
            )
            SELECT 
                group_id,
                COUNT(*) as post_count
            FROM extracted_groups
            WHERE group_id IS NOT NULL 
            AND group_id != ''
            GROUP BY group_id
            ORDER BY post_count DESC
        """)
        groups = cursor.fetchall()
        
        # Log for debugging
        logger.info(f"Found {len(groups)} groups in database")
        if len(groups) > 0:
            sample_groups = [g['group_id'] for g in groups[:10] if g['group_id']]
            logger.info(f"Sample group IDs: {sample_groups}")
            
            # Check specifically for the two groups we're looking for
            target_groups = ['pardodbiznesupardoduznemumu', 'grasis.lt']
            found_targets = [g for g in groups if g['group_id'] in target_groups]
            if found_targets:
                logger.info(f"Found target groups: {[g['group_id'] for g in found_targets]}")
            else:
                logger.warning(f"Target groups {target_groups} not found in results")

        cursor.close()
        conn.close()

        # Format groups with readable names
        groups_list = []
        for row in groups:
            group_dict = dict(row)
            group_id = group_dict.get('group_id')
            
            # Skip if group_id is None, empty string, or whitespace
            if not group_id or not str(group_id).strip():
                logger.warning(f"Skipping group with empty/null group_id: {group_dict}")
                continue
            
            # Format the name nicely
            # Check if group_id is numeric (just digits)
            if group_id.isdigit():
                # For numeric IDs, show as "Group {id}"
                group_dict['group_name'] = f"Group {group_id}"
            else:
                # For readable names (like "pardodbiznesupardoduznemumu" or "grasis.lt")
                # Replace dots, dashes, underscores with spaces and title case
                formatted_name = group_id.replace('.', ' ').replace('-', ' ').replace('_', ' ').title()
                group_dict['group_name'] = formatted_name
            
            groups_list.append(group_dict)
        
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

        # Build WHERE clause (same logic as get_posts) - use facebook_posts column names
        where_conditions = []
        params = []

        if author:
            where_conditions.append("fp.user_name ILIKE %s")
            params.append(f"%{author}%")

        if keyword:
            where_conditions.append("fp.post_text ILIKE %s")
            params.append(f"%{keyword}%")

        if group_id:
            # Handle group filtering: check both group_id column and extract from post_url
            # Use COALESCE to get group_id from column or extract from URL
            where_conditions.append("""
                (COALESCE(fp.group_id, 
                    CASE 
                        WHEN fp.post_url ~ '/groups/([^/]+)/' 
                        THEN (regexp_match(fp.post_url, '/groups/([^/]+)/'))[1]
                        ELSE NULL 
                    END
                ) = %s)
            """)
            params.append(group_id)

        if date_from:
            # Use start of day (00:00:00) for date_from
            where_conditions.append("to_timestamp(fp.created_at) >= %s::date")
            params.append(date_from)

        if date_to:
            # Use end of day (23:59:59) for date_to to include the entire day
            where_conditions.append("to_timestamp(fp.created_at) < (%s::date + INTERVAL '1 day')")
            params.append(date_to)

        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"

        # Get all posts (no pagination for export) with attachments
        query = f"""
            SELECT 
                fp.id,
                fp.post_url,
                fp.user_name as author_name,
                fp.user_url as author_url,
                fp.post_text as text_content,
                fp.group_id,
                fp.reaction_count as reactions,
                fp.comment_count as comments,
                fp.share_count as shares,
                to_timestamp(fp.created_at) as created_at,
                COALESCE(
                    json_agg(
                        DISTINCT jsonb_build_object(
                            'url', fa.attachment_url,
                            'type', fa.attachment_type
                        )
                    ) FILTER (WHERE fa.attachment_type = 'image'),
                    '[]'::json
                ) as image_attachments,
                COALESCE(
                    json_agg(
                        DISTINCT jsonb_build_object(
                            'url', fa.attachment_url,
                            'type', fa.attachment_type
                        )
                    ) FILTER (WHERE fa.attachment_type = 'video'),
                    '[]'::json
                ) as video_attachments
            FROM facebook_posts fp
            LEFT JOIN facebook_attachments fa ON fp.post_url = fa.post_url
            WHERE {where_clause}
            GROUP BY fp.id, fp.post_url, fp.user_name, fp.user_url, fp.post_text, 
                     fp.group_id, fp.reaction_count, fp.comment_count, fp.share_count, fp.created_at
            ORDER BY fp.created_at DESC
        """
        cursor.execute(query, params)
        posts = cursor.fetchall()

        cursor.close()
        conn.close()

        # Format posts for export
        posts_list = []
        for post in posts:
            post_dict = dict(post)
            
            # Extract image URLs from image_attachments JSON array
            image_urls = []
            if post_dict.get('image_attachments'):
                if isinstance(post_dict['image_attachments'], str):
                    try:
                        image_attachments = json.loads(post_dict['image_attachments'])
                    except:
                        image_attachments = []
                else:
                    image_attachments = post_dict['image_attachments']
                
                if isinstance(image_attachments, list):
                    image_urls = [att.get('url') for att in image_attachments if att and att.get('url')]
            
            # Extract video URLs from video_attachments JSON array
            video_urls = []
            if post_dict.get('video_attachments'):
                if isinstance(post_dict['video_attachments'], str):
                    try:
                        video_attachments = json.loads(post_dict['video_attachments'])
                    except:
                        video_attachments = []
                else:
                    video_attachments = post_dict['video_attachments']
                
                if isinstance(video_attachments, list):
                    video_urls = [att.get('url') for att in video_attachments if att and att.get('url')]
            
            post_dict['image_urls'] = image_urls
            post_dict['video_urls'] = video_urls
            
            # Remove attachment fields
            post_dict.pop('image_attachments', None)
            post_dict.pop('video_attachments', None)
            
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
        cursor.execute("SELECT COUNT(*) as total FROM facebook_posts")
        total_posts = cursor.fetchone()['total']

        # Get total reactions, comments, and shares
        cursor.execute("""
            SELECT 
                SUM(reaction_count) as total_reactions,
                SUM(comment_count) as total_comments,
                SUM(share_count) as total_shares
            FROM facebook_posts
        """)
        engagement = cursor.fetchone()

        # Get unique authors count
        cursor.execute("SELECT COUNT(DISTINCT user_name) as total_authors FROM facebook_posts WHERE user_name IS NOT NULL")
        total_authors = cursor.fetchone()['total_authors']

        # Get posts by date (last 7 days) - convert BIGINT timestamp to date
        cursor.execute("""
            SELECT DATE(to_timestamp(created_at)) as date, COUNT(*) as count
            FROM facebook_posts
            WHERE to_timestamp(created_at) >= NOW() - INTERVAL '7 days'
            GROUP BY DATE(to_timestamp(created_at))
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
            'total_shares': engagement['total_shares'] or 0,
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

