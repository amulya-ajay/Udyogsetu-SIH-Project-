# 🚀 UDYOGSETU - Quick Start & Deployment Guide

## One-Command Quick Start

```bash
# Clone the project
cd udyogsetu

# Start the entire stack
docker-compose up --build

# In a new terminal, initialize data (optional)
docker-compose exec backend bash scripts/load-data.sh
```

**Access the application**:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Database**: PostgreSQL on localhost:5432

---

## Step-by-Step Setup

### 1. Prerequisites
- Docker & Docker Compose installed
- Git
- 4GB RAM minimum
- 10GB disk space

### 2. Environment Configuration

```bash
# Create environment file
cp .env.example .env

# Edit .env and configure:
# - DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/udyogsetu
# - REDIS_URL=redis://redis:6379
# - JWT_SECRET_KEY=your-secret-key-here
```

### 3. Start Services

```bash
# Build and start all services
docker-compose up --build

# First time setup will:
# - Create PostgreSQL database
# - Run database migrations
# - Create necessary tables
# - Initialize Redis cache

# Wait for output:
# backend_1  | INFO:     Application startup complete
# frontend_1 | ▲ Next.js 14.0.0
```

### 4. Verify Installation

```bash
# Check health
curl http://localhost:8000/health

# Should return:
# {"status": "healthy", "version": "1.0.0"}
```

### 5. Initialize Sample Data (Optional)

```bash
# Load sample approval rules and schemes
docker-compose exec backend bash scripts/load-data.sh
```

---

## Testing

### Run Full Test Suite

```bash
# Backend tests
docker-compose exec backend pytest tests/ -v

# Coverage report
docker-compose exec backend pytest tests/ --cov=app --cov-report=html
```

### Manual API Testing

```bash
# Register user
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123!",
    "full_name": "Test User",
    "role": "ENTREPRENEUR"
  }'

# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123!"
  }'
```

---

## Common Operations

### View Logs

```bash
# Backend logs
docker-compose logs -f backend

# Frontend logs
docker-compose logs -f frontend

# Database logs
docker-compose logs -f postgres

# All logs
docker-compose logs -f
```

### Access Database

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U postgres -d udyogsetu

# Common queries:
# SELECT * FROM "user";
# SELECT COUNT(*) FROM project;
# SELECT * FROM approval;
```

### Stop Services

```bash
# Stop all services (keep data)
docker-compose stop

# Stop and remove containers (keep data)
docker-compose down

# Stop and remove everything including data
docker-compose down -v
```

### Restart Services

```bash
# Restart all services
docker-compose restart

# Restart specific service
docker-compose restart backend
docker-compose restart frontend
docker-compose restart postgres
```

---

## Production Deployment

### Pre-Deployment Checklist

- [ ] Review DEPLOYMENT_READINESS_REPORT.md
- [ ] Update .env with production values
- [ ] Configure SSL/TLS certificates
- [ ] Setup monitoring & logging
- [ ] Configure backups
- [ ] Test disaster recovery
- [ ] Setup domain & DNS
- [ ] Configure firewall rules

### Deploy to AWS

```bash
# 1. Create ECR repositories
aws ecr create-repository --repository-name udyogsetu-backend
aws ecr create-repository --repository-name udyogsetu-frontend

# 2. Push images
docker tag udyogsetu-backend:latest \
  [AWS_ACCOUNT].dkr.ecr.[REGION].amazonaws.com/udyogsetu-backend:latest

# 3. Deploy with ECS or Fargate
# (See DEPLOYMENT.md for detailed instructions)
```

### Deploy to Google Cloud

```bash
# 1. Build and push to GCR
docker build -t gcr.io/[PROJECT_ID]/udyogsetu-backend backend/
docker push gcr.io/[PROJECT_ID]/udyogsetu-backend

# 2. Deploy to Cloud Run
gcloud run deploy udyogsetu-backend \
  --image gcr.io/[PROJECT_ID]/udyogsetu-backend
```

### Deploy to Heroku

```bash
# 1. Create Heroku apps
heroku create udyogsetu-backend
heroku create udyogsetu-frontend

# 2. Push code
git push heroku main

# 3. Run migrations
heroku run python -c "from app.core.database import Base; Base.metadata.create_all()"
```

---

## Troubleshooting

### "Port already in use"
```bash
# Find process using port
lsof -i :8000
lsof -i :3000

# Kill process
kill -9 <PID>

# Or change port in docker-compose.yml
```

### "Cannot connect to database"
```bash
# Check if postgres is running
docker-compose ps postgres

# Check logs
docker-compose logs postgres

# Reset database
docker-compose down -v postgres
docker-compose up postgres
```

### "Frontend build fails"
```bash
# Clear cache and reinstall
docker-compose exec frontend bash
rm -rf .next node_modules
npm install
npm run build
```

### "API returns 500 error"
```bash
# Check backend logs
docker-compose logs backend

# Restart backend
docker-compose restart backend

# Check database connection
docker-compose exec backend python -c "from app.core.database import engine; print(engine)"
```

---

## Performance Tuning

### Database Optimization

```bash
# Check slow queries
docker-compose exec postgres psql -U postgres -d udyogsetu
SELECT * FROM pg_stat_statements LIMIT 10;

# Analyze query plans
EXPLAIN ANALYZE SELECT ...;
```

### Frontend Optimization

```bash
# Build analysis
cd frontend
npm run build

# Check bundle size
npm run analyze
```

### Caching Optimization

```bash
# Monitor Redis
docker-compose exec redis redis-cli INFO

# Check cache hit rate
docker-compose exec redis redis-cli INFO stats
```

---

## Monitoring

### Basic Monitoring

```bash
# CPU and memory usage
docker stats

# Network statistics
docker-compose exec backend curl http://localhost:8000/health

# Database connections
docker-compose exec postgres psql -U postgres -d udyogsetu -c "SELECT count(*) FROM pg_stat_activity;"
```

### Application Metrics

```bash
# Backend metrics endpoint (when configured)
curl http://localhost:8000/metrics

# Frontend performance
# Open DevTools → Performance → Record and analyze
```

### Log Aggregation

```bash
# Forward logs to external service
docker-compose logs --timestamps --tail=100 backend | \
  curl -X POST https://your-logging-service/logs -d @-
```

---

## Backup & Recovery

### Database Backup

```bash
# Backup entire database
docker-compose exec postgres pg_dump -U postgres udyogsetu > backup.sql

# Restore from backup
docker-compose exec -T postgres psql -U postgres udyogsetu < backup.sql
```

### File Backup

```bash
# Backup uploaded files (if using local storage)
docker cp udyogsetu-postgres-1:/var/lib/postgresql/data ./postgres_backup

# Backup database volumes
docker-compose exec postgres tar czf /tmp/db_backup.tar.gz /var/lib/postgresql/data
docker cp udyogsetu-postgres-1:/tmp/db_backup.tar.gz ./
```

---

## Scaling

### Horizontal Scaling

```bash
# Run multiple backend instances
docker-compose up -d --scale backend=3

# Load balancing via Nginx
# (Already configured in docker-compose.yml)
```

### Database Replication

```bash
# Setup read replicas for PostgreSQL
# See DEPLOYMENT.md for details
```

### Caching Strategy

```bash
# Configure Redis clustering
# See docker-compose.yml for Redis configuration
```

---

## Security Hardening

### Update Secrets

```bash
# Generate new JWT secret
openssl rand -hex 32

# Update .env
JWT_SECRET_KEY=<new-secret>

# Restart services
docker-compose restart backend
```

### Enable HTTPS

```bash
# Update docker-compose.yml Nginx configuration
# Configure SSL certificates
# Redirect HTTP to HTTPS

# Test SSL
curl -I https://your-domain.com
```

### Security Headers

```bash
# Nginx automatically adds:
# - X-Content-Type-Options: nosniff
# - X-Frame-Options: DENY
# - Content-Security-Policy headers
```

---

## Maintenance

### Regular Tasks

- [ ] Monitor disk space
- [ ] Review logs for errors
- [ ] Update dependencies
- [ ] Run backups
- [ ] Review security patches
- [ ] Monitor performance metrics
- [ ] Clean up old data
- [ ] Test disaster recovery

### Update Docker Images

```bash
# Pull latest images
docker-compose pull

# Rebuild and restart
docker-compose up --build -d
```

### Database Maintenance

```bash
# Vacuum database
docker-compose exec postgres psql -U postgres -d udyogsetu -c "VACUUM ANALYZE;"

# Check index usage
docker-compose exec postgres psql -U postgres -d udyogsetu -c "SELECT * FROM pg_stat_user_indexes;"
```

---

## Support & Documentation

- **API Docs**: http://localhost:8000/docs (Swagger UI)
- **Features Guide**: COMPLETE_FEATURE_GUIDE.md
- **Testing Guide**: TESTING_GUIDE.md
- **Deployment Guide**: DEPLOYMENT.md
- **README**: README.md

---

## Success Indicators

✅ Application is ready when you see:
- Backend: "Application startup complete"
- Frontend: "Ready in X.XXs"
- All services in docker-compose ps: "Up"
- Health check returns: {"status": "healthy"}

---

**Happy Deploying! 🚀**

For issues, refer to TESTING_GUIDE.md troubleshooting section or review service logs.
