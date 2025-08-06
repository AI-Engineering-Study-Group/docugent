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
- Python 3.13+
- Node.js 18+
- Docker & Docker Compose
- Google API Key (for AI capabilities)

### Option 1: Docker (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd docugent

# Set up environment
cp env.example .env
# Edit .env with your API keys

# Start the application
docker-compose up --build
```

Access the application at `http://localhost:2025`

### Option 2: Local Development

```bash
# Backend setup
poetry install
poetry run python main.py

# Frontend setup (in another terminal)
cd frontend
npm install
npm run dev
```

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

| Variable | Description | Required |
|----------|-------------|----------|
| `GOOGLE_API_KEY` | Google ADK API key | Yes |
| `GOOGLE_MODEL_NAME` | AI model to use | No |
| `DATABASE_URL` | PostgreSQL connection | Yes |
| `REDIS_URL` | Redis for caching | No |
| `SECRET_KEY` | Application secret | Yes |

### Documentation Sources

Docugent can work with various documentation sources:
- **Static Files**: Markdown, HTML, PDF
- **APIs**: REST APIs, GraphQL
- **Databases**: Structured documentation data
- **Web Scraping**: Dynamic content extraction

## 🧪 Testing

```bash
# Backend tests
poetry run pytest

# Frontend tests
cd frontend && npm run lint
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

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [docs.docugent.dev](https://docs.docugent.dev)
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

@greyisheep Added Feature

## Developer Memory (Context Recall Across Sessions)
Allow users to resume conversations later, referencing past sessions and queries.

**Benefits:**
Feels like talking to a personal AI dev assistant

Boosts productivity for large docs/projects

**Built with ❤️ for developers who deserve better documentation experiences**

*Transform your documentation from static pages to interactive conversations with Docugent! 🚀✨* 
