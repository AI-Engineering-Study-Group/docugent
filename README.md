# 🚀 Docugent

**Making documentation interactive and accessible for developers everywhere.**

Docugent is an AI-powered documentation assistant that transforms static documentation into interactive, conversational experiences. When developers face errors or need guidance, they can simply chat with Docugent to get exactly what they need - examples, best practices, and even the ability to test ideas in temporary containers.

## 🌟 Vision

**The Problem**: Documentation is often overwhelming, static, and doesn't adapt to individual developer needs. When developers face errors or need guidance, they spend valuable time sifting through pages of documentation.

**The Solution**: Docugent makes documentation conversational, contextual, and actionable. Developers can ask questions in natural language and get precise, relevant answers with examples and best practices.

## 🎯 Key Features

### 🤖 AI-Powered Documentation Assistant

- **Natural Language Queries**: Ask questions in plain English
- **Context-Aware Responses**: Get answers tailored to your specific situation
- **Code Examples**: Receive working code examples and best practices
- **Error Resolution**: Get step-by-step solutions for common issues

### 🔧 Interactive Development Environment

- **Temporary Containers**: Spin up isolated environments to test ideas
- **Live Code Execution**: Run and test code snippets safely
- **Environment Management**: Handle dependencies and configurations automatically

### 📚 Multi-Format Support

- **GitBook Integration**: Works as an extension for GitBook documentation
- **Standalone Deployment**: Self-hosted solution for your own documentation
- **API-First Design**: Easy integration with existing documentation platforms

### 🔐 Authentication & Authorization

- **JWT-Based Authentication**: Secure token-based authentication
- **Role-Based Access Control**: Admin, moderator, and user roles
- **User Management**: Registration, login, profile management
- **Password Security**: Bcrypt hashing with salt
- **Token Management**: Access and refresh tokens with blacklisting

### 🎨 Developer Experience

- **Clean, Modern UI**: Intuitive interface that doesn't get in your way
- **Session Management**: Maintain context across conversations
- **Export Capabilities**: Save solutions and examples for later reference

## 🏗️ Architecture

```
docugent/
├── app/
│   ├── agents/           # AI agent implementation
│   ├── api/             # FastAPI endpoints
│   ├── config/          # Configuration management
│   ├── schemas/         # Pydantic models
│   ├── services/        # Business logic
│   └── tools/           # AI agent tools
├── frontend/            # React TypeScript UI
├── data/               # Documentation data
├── docker/             # Containerization
└── scripts/            # Utility scripts
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- Docker & Docker Compose
- PostgreSQL (or use Docker)
- Google API Key (for AI capabilities)

### Option 1: Docker (Recommended)

````bash
# Clone the repository
git clone <repository-url>
cd docugent

# Set up environment with your cloud database
cp env.example .env
# Edit .env with your cloud database URL:
# DATABASE_URL=postgresql://user:password@your-cloud-host:5432/dbname
# SECRET_KEY=your-super-secret-key
# GOOGLE_API_KEY=your-google-api-key

# Start services (backend + nginx)
# Uses your cloud database - no local database needed
docker-compose up --build

# The system will automatically:
# - Connect to your cloud database
# - Create database tables via migrations
# - Set up default roles (admin, moderator, user)
# - Create default admin user
```Access the application at `http://localhost:2025`

**Default Admin Credentials:**

- Email: `admin@apiconf.com`
- Password: `admin123!@#`
- **⚠️ Change this password immediately after first login!**

### Option 2: Local Development with Poetry

```bash
# Install Poetry (if not already installed)
curl -sSL https://install.python-poetry.org | python3 -
export PATH="/home/vix/.local/bin:$PATH"

# Install backend dependencies
poetry install

# Set up environment
cp env.example .env
# Edit .env with your database and API configuration

# Run database migrations and initialization
poetry run alembic upgrade head
poetry run python scripts/init_db.py

# Start backend
poetry run python main.py

# Frontend setup (in another terminal)
cd frontend
npm install
npm run dev
````

## 📖 Usage Examples

### Basic Documentation Query

```
User: "How do I implement authentication in my FastAPI app?"
Docugent: "Here's a step-by-step guide with JWT authentication..."

User: "I'm getting a 500 error when deploying to production"
Docugent: "Let me help you debug this. First, let's check your logs..."
```

### Interactive Development

```
User: "Can you show me how to test this API endpoint?"
Docugent: "I'll create a temporary container with your code and run the tests..."
```

## 🔧 Configuration

### Environment Variables

| Variable                      | Description           | Required | Default                    |
| ----------------------------- | --------------------- | -------- | -------------------------- |
| `GOOGLE_API_KEY`              | Google ADK API key    | Yes      | -                          |
| `GOOGLE_MODEL_NAME`           | AI model to use       | No       | `gemini-2.5-flash`         |
| `DATABASE_URL`                | PostgreSQL connection | Yes      | -                          |
| `REDIS_URL`                   | Redis for caching     | No       | `redis://localhost:6379/0` |
| `SECRET_KEY`                  | JWT secret key        | Yes      | -                          |
| `JWT_ALGORITHM`               | JWT algorithm         | No       | `HS256`                    |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiry          | No       | `30`                       |
| `REFRESH_TOKEN_EXPIRE_DAYS`   | Refresh token expiry  | No       | `7`                        |

### Documentation Sources

Docugent can work with various documentation sources:

- **Static Files**: Markdown, HTML, PDF
- **APIs**: REST APIs, GraphQL
- **Databases**: Structured documentation data
- **Web Scraping**: Dynamic content extraction

## 🔌 API Endpoints

### Authentication (`/api/v1/auth`)

- `POST /register` - Register new user
- `POST /login` - User login
- `POST /refresh` - Refresh access token
- `POST /logout` - Logout user
- `GET /me` - Get current user info
- `POST /change-password` - Change password

### Role Management (`/api/v1/roles`) - Admin Only

- `POST /` - Create new role
- `GET /` - Get all roles
- `GET /{id}` - Get specific role
- `PUT /{id}` - Update role
- `DELETE /{id}` - Delete role

### User Management (`/api/v1/users`)

- `GET /` - Get all users (moderator+)
- `GET /{id}` - Get user details
- `PUT /{id}` - Update user
- `PATCH /{id}/activate` - Activate user (admin)
- `PATCH /{id}/deactivate` - Deactivate user (admin)

### AI Agents (`/api/v1/agents`)

- `POST /chat` - Send message to AI agent
- `GET /health` - Health check
- `GET /status` - Agent status

**📖 Full API Documentation**: Available at `/docs` when running the server

## 🧪 Testing

### Backend Tests

```bash
# Run authentication tests
poetry run python tests/test_auth_system.py

# Run full test suite
poetry run pytest

# Test API endpoints
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@apiconf.com","password":"admin123!@#"}'
```

### Frontend Tests

```bash
cd frontend
npm run test
npm run lint
```

## 🚀 Deployment

### Docker Deployment

```bash
docker-compose -f docker-compose.yml up -d
```

### Production Considerations

- **SSL/TLS**: Configure HTTPS certificates
- **Database**: Use managed PostgreSQL
- **Caching**: Redis for performance
- **Monitoring**: Health checks and logging
- **Scaling**: Load balancer configuration

## 🤝 Contributing

We welcome contributions from developers, designers, documentation writers, and AI/ML engineers! See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

### Quick Start for Contributors

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## � Complete Documentation

For comprehensive setup, authentication, deployment, and development guides, see:

**[📖 Complete Setup & Authentication Guide](docs/AUTHENTICATION.md)**

This comprehensive guide covers:

- Complete project setup with Poetry
- JWT authentication implementation
- Role-based authorization system
- Docker deployment with cloud databases
- Security configuration and best practices
- API documentation and usage examples
- Development workflow and troubleshooting

## �📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Complete Auth Setup Guide**: [AUTHENTICATION.md](docs/AUTHENTICATION.md)
- **Issues**: [GitHub Issues](https://github.com/your-org/docugent/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/docugent/discussions)

## 🎯 Roadmap

- [ ] GitBook extension development
- [ ] Multi-language documentation support
- [ ] Advanced container orchestration
- [ ] Real-time collaboration features
- [ ] Integration with popular documentation platforms
- [ ] Mobile app for on-the-go assistance
- [ ] Voice interface for hands-free development

---

**Built with ❤️ for developers who deserve better documentation experiences**

_Transform your documentation from static pages to interactive conversations with Docugent! 🚀✨_
