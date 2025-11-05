# Facebook Media Aggregator Dashboard

A secure, responsive web dashboard for visualizing media posts scraped from Facebook groups. Built with React, Flask, and PostgreSQL.

## 🎯 Features

- **Secure Authentication**: JWT-based authentication for admin access
- **Responsive Design**: Mobile-friendly interface built with TailwindCSS
- **Advanced Filtering**: Filter posts by author, date range, keyword, and sort options
- **Post Visualization**: Grid layout with image thumbnails, engagement metrics, and post details
- **Real-time Stats**: Dashboard analytics showing total posts, reactions, comments, shares, and authors
- **Post Detail Modal**: View full post details with images and engagement metrics

## 📁 Project Structure

```
.
├── backend/          # Flask API server
│   ├── app.py       # Main Flask application
│   └── requirements.txt
├── frontend/        # React frontend
│   ├── src/
│   │   ├── components/
│   │   ├── context/
│   │   ├── pages/
│   │   └── services/
│   └── package.json
├── docker-compose.yml
└── README.md
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 12+
- Docker & Docker Compose (optional)

### Option 1: Docker (Recommended)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd facebook-media-aggregator
   ```

2. **Create `.env` file in the root directory**
   ```env
   DB_HOST=postgres
   DB_PORT=5432
   DB_USER=postgres
   DB_PASS=yourpassword
   DB_NAME=facebook_aggregator
   JWT_SECRET=supersecretkey
   ADMIN_EMAIL=admin@example.com
   ADMIN_PASS=admin123
   ```

3. **Start services**
   ```bash
   docker-compose up -d
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:5000
   - PostgreSQL: localhost:5432

### Option 2: Manual Setup

#### Backend Setup

1. **Navigate to backend directory**
   ```bash
   cd backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create `.env` file in backend directory**
   ```env
   DB_HOST=localhost
   DB_PORT=5432
   DB_USER=postgres
   DB_PASS=yourpassword
   DB_NAME=facebook_aggregator
   JWT_SECRET=your-secure-random-secret-here
   ```
   
   **Important**: Generate a secure JWT secret:
   ```bash
   cd backend
   python generate_jwt_secret.py
   ```
   Copy the generated secret to your `.env` file. Never use the default `supersecretkey` in production!

5. **Set up PostgreSQL database**
   - Create the database:
     ```sql
     CREATE DATABASE facebook_aggregator;
     ```
   - Run the initialization script:
     ```bash
     psql -U postgres -d facebook_aggregator -f init_db.sql
     ```
     Or manually run the SQL from `backend/init_db.sql` which creates:
     - `users` table for authentication
     - `fb_media_posts` table for Facebook posts

6. **Create a user account**
   ```bash
   python create_user.py
   ```
   This will prompt you to enter an email, password, and name for the admin user.

7. **Run the Flask server**
   ```bash
   python app.py
   ```

   The backend will run on http://localhost:5000

#### Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Start development server**
   ```bash
   npm run dev
   ```

   The frontend will run on http://localhost:3000

## 🔐 Authentication

The dashboard uses JWT-based authentication with a database-backed user system. **Only admin users can login** - users must have `is_admin=true` in the database.

To create an admin user:

```bash
cd backend
python create_user.py
```

Enter your email, password, and name when prompted. When asked "Make this user an admin?", answer **y** (yes) to grant admin access. The password will be securely hashed before storing in the database.

**Important**: 
- Only users with `is_admin=true` can login to the dashboard
- The `ADMIN_USER_ID` in `.env` is optional and for reference only
- All authentication is handled through the `users` table in the database

## 📊 API Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `POST` | `/api/login` | Login and get JWT token | No |
| `GET` | `/api/posts` | Get paginated posts with filters | Yes |
| `GET` | `/api/posts/<id>` | Get post details | Yes |
| `GET` | `/api/stats` | Get dashboard statistics | Yes |
| `GET` | `/api/health` | Health check | No |

### Query Parameters for `/api/posts`

- `page` - Page number (default: 1)
- `per_page` - Posts per page (default: 20)
- `author` - Filter by author name (partial match)
- `keyword` - Search in post content (partial match)
- `date_from` - Filter posts from date (YYYY-MM-DD)
- `date_to` - Filter posts to date (YYYY-MM-DD)
- `sort_by` - Sort field: `created_at`, `reactions`, `comments`, `shares` (default: `created_at`)
- `order` - Sort order: `asc` or `desc` (default: `desc`)

### Example API Request

```bash
curl -X GET "http://localhost:5000/api/posts?page=1&per_page=20&author=John&sort_by=reactions&order=desc" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## 🎨 Features

### Dashboard

- **Stats Cards**: Display total posts, reactions, comments, shares, and authors
- **Responsive Grid**: Post cards in a responsive grid layout
- **Infinite Scroll**: Load more posts with pagination
- **Search**: Search posts by keyword in header
- **Sidebar Filters**: 
  - Sort by date, reactions, comments, or shares
  - Filter by author
  - Filter by date range
  - Sort order (ascending/descending)

### Post Cards

- Image thumbnail (with fallback)
- Post content preview
- Author name (clickable link to author profile)
- Engagement metrics (reactions, comments, shares)
- Creation date

### Post Detail Modal

- Full-size image
- Complete post content
- Author information
- Engagement metrics breakdown
- Link to original Facebook post

## 🛠️ Technologies Used

### Backend
- **Flask**: Python web framework
- **Flask-JWT-Extended**: JWT authentication
- **Flask-CORS**: Cross-origin resource sharing
- **psycopg2**: PostgreSQL adapter
- **python-dotenv**: Environment variable management

### Frontend
- **React 18**: UI library
- **Vite**: Build tool and dev server
- **React Router**: Client-side routing
- **TailwindCSS**: Utility-first CSS framework
- **Axios**: HTTP client
- **Chart.js**: Data visualization (optional)

## 📱 Responsive Design

The dashboard is fully responsive with breakpoints for:
- **Mobile**: Single column layout, collapsible sidebar
- **Tablet**: 2-column grid
- **Desktop**: 3-4 column grid

## 🔒 Security Considerations

- JWT tokens stored in localStorage
- API endpoints protected with `@jwt_required()`
- CORS configured for frontend origin
- Environment variables for sensitive data
- SQL injection prevention via parameterized queries

⚠️ **For Production**:
- Use HTTPS
- **Generate a strong JWT secret** using `python backend/generate_jwt_secret.py` (never use the default `supersecretkey`!)
- Configure CORS to allow only your frontend domain
- Use environment variables for all secrets
- Implement rate limiting
- Add input validation and sanitization

## 🐳 Docker

The project includes Docker support for easy deployment:

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

## 📝 Database Schema

```sql
-- Users table for authentication
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  name TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  is_active BOOLEAN DEFAULT TRUE,
  is_admin BOOLEAN DEFAULT FALSE
);

-- Facebook media posts table
CREATE TABLE fb_media_posts (
  post_url TEXT PRIMARY KEY,
  author_name TEXT,
  author_url TEXT,
  text_content TEXT,
  image_urls JSONB,
  group_id TEXT,
  created_at TIMESTAMP,
  reactions INT DEFAULT 0,
  comments INT DEFAULT 0
);
```

### Creating Admin Users

To create an admin user for login, use the `create_user.py` script:

```bash
cd backend
python create_user.py
```

This will prompt you for:
- Email address
- Password (will be securely hashed)
- Name (optional)
- Admin status (y/n - default: y)

**Important**: Only users with `is_admin=true` can login to the dashboard. Make sure to answer **y** when asked if the user should be an admin.

The script will display the user ID (UUID format) after creation, which you can optionally add to your `.env` file as `ADMIN_USER_ID` for reference.

**Note**: User IDs are now UUIDs (e.g., `634d09bf-73e4-4384-8014-d33707b04770`) instead of integers. If you're migrating from an existing database with integer IDs, you'll need to update the schema:

```sql
-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Alter table to use UUID (this requires migrating existing data)
ALTER TABLE users ALTER COLUMN id TYPE UUID USING gen_random_uuid();
```

## 🧪 Testing

### Health Check

```bash
curl http://localhost:5000/api/health
```

### Login Test

```bash
curl -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin123"}'
```

## 🚧 Development

### Backend Development

```bash
cd backend
export FLASK_ENV=development
python app.py
```

### Frontend Development

```bash
cd frontend
npm run dev
```

The frontend is configured to proxy `/api` requests to the backend during development.

## 📄 License

This project is licensed under the MIT License.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📞 Support

For issues and questions, please open an issue on the GitHub repository.

---

**Built with ❤️ using React, Flask, and PostgreSQL**

