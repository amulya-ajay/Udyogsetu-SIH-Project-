# UDYOGSETU Deployment Guide

## Quick Start with Docker Compose

### Prerequisites
- Docker & Docker Compose installed
- Python 3.11+ (for local development)
- Node.js 18+ (for frontend development)

### Steps

1. **Clone and setup**
```bash
git clone <repository>
cd udyogsetu
./scripts/setup.sh
```

2. **Configure environment**
```bash
# Edit .env with your configuration
nano .env
```

3. **Start services**
```bash
./scripts/start-dev.sh
```

4. **Load initial data**
```bash
./scripts/load-data.sh
```

5. **Access services**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Nginx: http://localhost

## Production Deployment

### Database Setup
```bash
# Create PostgreSQL database
createdb udyogsetu

# Run migrations
cd backend
alembic upgrade head
```

### Environment Variables
```bash
DATABASE_URL=postgresql://user:pass@host:5432/udyogsetu
REDIS_URL=redis://host:6379/0
JWT_SECRET_KEY=<strong-random-key>
GEMINI_API_KEY=<your-key>
```

### Using Kubernetes
```bash
kubectl apply -f k8s/
```

## Troubleshooting

### Database Connection Issues
```bash
# Check database health
docker-compose exec postgres pg_isready -U udyogsetu
```

### Port Already in Use
```bash
# Change ports in docker-compose.yml or stop other services
docker-compose down
```

### Missing Dependencies
```bash
# Reinstall dependencies
pip install -r requirements.txt
npm install
```

## Support
For issues, check logs:
```bash
docker-compose logs backend
docker-compose logs frontend
docker-compose logs postgres
```
