# UDYOGSETU

**From Idea to Industry — One Intelligent Journey**

A production-quality intelligent industrial approval, compliance, and government-support platform for the Smart India Hackathon 2026.

**Problem Statement:** 26130  
**Organization:** Government of Maharashtra  
**Department:** Maharashtra State Innovation Society  

## Overview

UdyogSetu is an AI-powered platform that helps entrepreneurs and industrial units navigate the complex landscape of government approvals, compliance requirements, and support schemes. The platform intelligently determines applicable approvals, tracks applications, validates documents, manages compliance obligations, and connects users with government incentive programs.

### Core Capabilities

- **Intelligent Approval Determination** - Rule-based engine determining applicable approvals based on project characteristics
- **Approval Dependency Visualization** - Interactive flow showing approval sequences and parallelization opportunities
- **Document Intelligence** - AI-powered document upload, validation, OCR, and cross-document verification
- **Regulatory Copilot** - Chat interface for regulatory knowledge with grounded RAG-based responses
- **Application Tracking** - Real-time status tracking with SLA monitoring and alert system
- **Compliance Management** - Post-approval compliance tracking, renewals, and compliance scoring
- **Government Incentive Matching** - Scheme discovery and eligibility matching
- **Scenario Simulation** - What-if analysis for project parameter changes
- **Government Integration** - Adapter-based integration with MAITRI, MPCB, MIDC, and other systems
- **Officer Analytics** - Government dashboards for SLA monitoring and bottleneck identification

## Technology Stack

### Frontend
- **Framework:** Next.js with React & TypeScript
- **Styling:** Tailwind CSS + shadcn/ui
- **Forms:** React Hook Form + Zod
- **Data Management:** TanStack Query
- **Visualization:** React Flow (approval dependencies), Recharts (analytics)
- **Icons:** Lucide Icons

### Backend
- **Framework:** FastAPI (Python)
- **ORM:** SQLAlchemy
- **Database Migrations:** Alembic
- **Validation:** Pydantic
- **Background Jobs:** Celery or RQ
- **Caching:** Redis

### Database & Search
- **Primary:** PostgreSQL
- **Vector Search:** pgvector (for RAG embeddings)
- **Document Processing:** PyMuPDF, python-docx, Pillow, OpenCV
- **OCR:** Tesseract

### AI & LLM
- **Provider Abstraction:** Support for Google Gemini, Groq, Ollama
- **Embeddings:** Google embedding model / Sentence Transformers / Local models
- **RAG Framework:** Vector-based retrieval with pgvector

### DevOps
- **Containerization:** Docker & Docker Compose
- **Web Server:** Nginx
- **CI/CD:** GitHub Actions (optional)

## Project Structure

```
udyogsetu/
├── frontend/              # Next.js application
│   ├── app/              # App router and pages
│   ├── components/       # React components
│   ├── features/         # Feature modules
│   ├── hooks/            # Custom React hooks
│   ├── lib/              # Utilities and helpers
│   ├── services/         # API client services
│   ├── types/            # TypeScript type definitions
│   └── public/           # Static assets
├── backend/              # FastAPI application
│   ├── app/
│   │   ├── api/          # API endpoints
│   │   ├── core/         # Core configs and dependencies
│   │   ├── models/       # Database models
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── services/     # Business logic
│   │   ├── repositories/ # Data access layer
│   │   ├── integrations/ # External system adapters
│   │   ├── ai/           # AI/LLM abstractions
│   │   ├── rag/          # RAG pipeline
│   │   ├── rules/        # Rule engine
│   │   ├── workflows/    # Complex workflows
│   │   ├── notifications/# Notification system
│   │   ├── audit/        # Audit logging
│   │   └── workers/      # Background jobs
│   └── tests/            # Test suite
├── data/                 # Sample data and configurations
│   ├── regulations/      # Regulatory documents
│   ├── schemes/          # Incentive schemes
│   ├── approvals/        # Approval definitions
│   ├── sample_documents/ # Sample documents
│   └── mock_government_data/ # Mock API responses
├── infrastructure/       # Deployment configurations
│   ├── docker/          # Docker files
│   └── nginx/           # Nginx configuration
├── scripts/             # Utility scripts
├── docs/                # Documentation
├── docker-compose.yml   # Multi-container orchestration
├── .env.example         # Environment template
└── README.md           # This file
```

## Getting Started

### Prerequisites
- Docker & Docker Compose
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+

### Quick Start with Docker

```bash
# Clone the repository
git clone https://github.com/maharashtra-innovation/udyogsetu.git
cd udyogsetu

# Copy environment template
cp .env.example .env

# Start all services
docker-compose up --build

# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Local Development Setup

#### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload
```

#### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Key Features

### 1. Approval Intelligence Engine
- Rule-based determination of applicable approvals
- Support for AND/OR/NOT logic in approval conditions
- Estimated processing timelines
- Risk assessment

### 2. Document Intelligence
- Multi-format support (PDF, PNG, JPG, DOCX)
- Automated OCR and text extraction
- Metadata and field extraction
- Cross-document validation with fuzzy matching
- Document classification and state tracking

### 3. RAG-Powered Regulatory Copilot
- Semantic search across regulatory documents
- Grounded responses with source attribution
- Context-aware regulatory guidance
- Integration with approval determinations

### 4. Government Integration Layer
- Adapter-based architecture for different systems
- Mock APIs for development and testing
- Real API support when credentials available
- Transparent to application logic

### 5. Application Tracking & SLA Management
- Real-time status tracking
- SLA monitoring with risk indicators
- Automated alerts and notifications
- Next action recommendations

### 6. Compliance Management
- Post-approval compliance obligations
- Renewal tracking and reminders
- Compliance scoring and dashboard
- Document requirement management

### 7. Incentive Discovery
- Scheme matching using rule engine
- Eligibility explanation
- Personalized scheme recommendations
- Benefits and requirements breakdown

### 8. Scenario Simulator
- What-if project parameter analysis
- Impact on approvals and compliance
- Investment and employment scenarios
- Risk level assessment

### 9. Government Analytics
- Application performance metrics
- SLA breach analysis
- Bottleneck identification
- Department-wise analytics

## API Documentation

Complete API documentation available at `/docs` endpoint when running the backend.

### Key Endpoints

**Authentication**
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `POST /api/auth/refresh` - Refresh JWT token

**Projects**
- `POST /api/projects` - Create new project
- `GET /api/projects/{id}` - Get project details
- `PUT /api/projects/{id}` - Update project
- `GET /api/projects/{id}/approvals` - Get applicable approvals

**Documents**
- `POST /api/documents/upload` - Upload document
- `GET /api/documents/{id}` - Get document details
- `POST /api/documents/validate` - Validate document

**Regulatory Copilot**
- `POST /api/chat/query` - Submit regulatory question
- `GET /api/chat/history` - Get chat history

**Application Tracking**
- `GET /api/applications` - List applications
- `GET /api/applications/{id}` - Get application status
- `GET /api/applications/{id}/sla` - Get SLA status

**Compliance**
- `GET /api/compliance/{project_id}` - Get compliance dashboard
- `GET /api/compliance/{project_id}/items` - Get compliance items

**Incentives**
- `POST /api/schemes/match` - Find matching schemes
- `GET /api/schemes/{id}` - Get scheme details

## Architecture Decisions

### Rule Engine Over Pure LLM
The approval determination uses a deterministic rule engine with optional LLM explanations rather than relying entirely on LLM outputs. This ensures:
- Consistency and auditability
- Compliance with actual regulations
- Reduced hallucination risk

### Adapter Pattern for Government Integration
Government integrations use the adapter pattern to:
- Support multiple systems (MAITRI, MPCB, MIDC, etc.)
- Enable seamless switching between real and mock APIs
- Isolate integration logic from business logic

### RAG for Regulatory Knowledge
Retrieval-Augmented Generation ensures:
- Answers grounded in official documents
- Source attribution and traceability
- Reduced AI hallucination
- Easy knowledge updates

## Security & Compliance

- **Authentication:** JWT-based with role-based access control
- **Authorization:** Endpoint-level RBAC for Entrepreneur, Officer, Admin roles
- **Data Protection:** TLS/HTTPS, secrets via environment variables
- **Audit Logging:** Comprehensive audit trail for all actions
- **Input Validation:** Pydantic schema validation on all inputs
- **Rate Limiting:** API rate limiting to prevent abuse

## Development

### Contributing

1. Create a feature branch
2. Make changes with tests
3. Run linting and tests
4. Submit PR with description

### Running Tests

```bash
cd backend
pytest tests/

cd ../frontend
npm run test
```

### Code Standards

- Python: PEP 8 style with Black formatter
- TypeScript: ESLint + Prettier
- Both: Type safety enforced

## Deployment

### Production Deployment

```bash
# Build images
docker-compose -f docker-compose.yml -f docker-compose.prod.yml build

# Push to registry
docker push your-registry/udyogsetu-backend:latest
docker push your-registry/udyogsetu-frontend:latest

# Deploy
kubectl apply -f k8s/
```

### Environment Configuration

Copy `.env.example` to `.env` and configure:
- Database connection strings
- Redis connection
- API keys (Gemini, Groq, etc.)
- JWT secret
- CORS settings

## Performance & Scalability

- **Horizontal Scaling:** Stateless FastAPI backend
- **Caching:** Redis for frequently accessed data
- **Database Optimization:** Indexed queries, connection pooling
- **Vector Search:** pgvector for efficient similarity search
- **Background Jobs:** Celery for long-running tasks

## Future Enhancements

- **SMS/WhatsApp Notifications:** Beyond email
- **Mobile Application:** Native iOS/Android apps
- **Advanced Analytics:** ML-based bottleneck prediction
- **Multi-language Support:** Regional language interfaces
- **Blockchain Integration:** Immutable audit trails
- **Kubernetes Deployment:** Cloud-native orchestration
- **GraphQL API:** Alternative to REST

## Support & Contact

- **Issues:** GitHub Issues
- **Discussions:** GitHub Discussions
- **Email:** support@udyogsetu.gov.in

## License

[To be specified by Government of Maharashtra]

## Acknowledgments

**Smart India Hackathon 2026**  
Government of Maharashtra, Department of Skills, Employment, Entrepreneurship and Innovation

---

**Last Updated:** August 2026  
**Version:** 1.0.0-MVP
