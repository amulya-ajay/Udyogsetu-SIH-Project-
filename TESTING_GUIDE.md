# UDYOGSETU - Testing & Verification Guide

## Quick Start Verification

### 1. Backend Health Check
```bash
curl http://localhost:8000/health
# Expected: {"status": "healthy", "version": "1.0.0"}
```

### 2. API Documentation
```bash
# Access Swagger UI
open http://localhost:8000/docs
```

## Manual Testing Scenarios

### Scenario 1: Entrepreneur Onboarding Flow

1. **Register Account**
   ```bash
   curl -X POST http://localhost:8000/api/auth/register \
     -H "Content-Type: application/json" \
     -d '{
       "email": "entrepreneur@example.com",
       "password": "SecurePass123!",
       "full_name": "John Doe",
       "role": "ENTREPRENEUR"
     }'
   # Expected: 201 Created
   ```

2. **Login**
   ```bash
   curl -X POST http://localhost:8000/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{
       "email": "entrepreneur@example.com",
       "password": "SecurePass123!"
     }'
   # Expected: 200 OK with access_token
   ```

3. **Create Project**
   ```bash
   curl -X POST http://localhost:8000/api/projects \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "Textile Unit - Pune",
       "sector": "Textile",
       "state": "Maharashtra",
       "district": "Pune",
       "capacity": 150,
       "employees": 75
     }'
   # Expected: 201 Created with project_id
   ```

4. **Get Project Approvals**
   ```bash
   curl http://localhost:8000/api/projects/PROJECT_ID/approvals \
     -H "Authorization: Bearer YOUR_TOKEN"
   # Expected: List of required approvals with dependencies
   ```

### Scenario 2: Regulatory Guidance Flow

1. **Query Regulatory Knowledge**
   ```bash
   curl -X POST http://localhost:8000/api/regulatory/query \
     -H "Content-Type: application/json" \
     -d '{
       "query": "What approvals do I need for a textile unit in Maharashtra?",
       "project_id": "PROJECT_ID"
     }'
   # Expected: Answer with sources and evidence
   ```

2. **Check Government Status**
   ```bash
   curl http://localhost:8000/api/regulatory/government/MAITRI/status/APP-001
   # Expected: Application status from mock government system
   ```

### Scenario 3: Document Management Flow

1. **Upload Document**
   ```bash
   curl -X POST http://localhost:8000/api/documents/upload \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -F "file=@factory_license.pdf" \
     -F "project_id=PROJECT_ID" \
     -F "document_type=license" \
     -F "sector=manufacturing"
   # Expected: Extracted fields and validation results
   ```

2. **Validate Document**
   ```bash
   curl http://localhost:8000/api/documents/validate/DOC_ID \
     -H "Authorization: Bearer YOUR_TOKEN"
   # Expected: Validation results
   ```

### Scenario 4: Business Intelligence Flow

1. **Get Compliance Score**
   ```bash
   curl http://localhost:8000/api/compliance/PROJECT_ID/score \
     -H "Authorization: Bearer YOUR_TOKEN"
   # Expected: Compliance score with component breakdown
   ```

2. **Find Matching Schemes**
   ```bash
   curl -X POST http://localhost:8000/api/schemes/match \
     -H "Content-Type: application/json" \
     -d '{
       "sector": "Textile",
       "state": "Maharashtra",
       "investment_amount": 2000000,
       "employees": 75
     }'
   # Expected: Matching incentive schemes with subsidy calculations
   ```

3. **Run Scenario Simulation**
   ```bash
   curl -X POST http://localhost:8000/api/simulate/scenario \
     -H "Content-Type: application/json" \
     -d '{
       "scenario_type": "location_change",
       "project_data": {
         "location": "Pune, Maharashtra",
         "sector": "Manufacturing"
       },
       "parameters": {
         "new_location": {
           "name": "Ahmedabad, Gujarat",
           "state": "Gujarat"
         }
       }
     }'
   # Expected: Impact analysis
   ```

## Frontend Component Testing

### 1. Onboarding Wizard
```bash
# Navigate to: http://localhost:3000/onboarding
# Test:
# - All 5 steps render
# - Form validation works
# - Next/Previous navigation
# - Submit creates project
```

### 2. Approval Dependency Graph
```bash
# Navigate to: http://localhost:3000/project/PROJECT_ID/approvals
# Test:
# - Dependency graph displays
# - Color coding (mandatory=red, optional=green)
# - Statistics update correctly
```

### 3. Application Tracker
```bash
# Navigate to: http://localhost:3000/project/PROJECT_ID/tracker
# Test:
# - Applications listed
# - Status filters work
# - SLA progress bars update
# - Risk indicators display
```

### 4. Regulatory Copilot
```bash
# Navigate to: http://localhost:3000/project/PROJECT_ID/chat
# Test:
# - Chat interface loads
# - Suggested questions clickable
# - Message sending works
# - Sources panel displays
```

### 5. Officer Dashboard
```bash
# Navigate to: http://localhost:3000/officer-dashboard
# Test:
# - Metrics display
# - Application table shows
# - Filters work
# - Quick actions accessible
```

## Automated Testing

### Run All Backend Tests
```bash
cd backend
pytest tests/ -v --cov=app --cov-report=html

# Generate coverage report
open htmlcov/index.html
```

### Run Specific Test Suite
```bash
# Test only API endpoints
pytest tests/test_api.py -v

# Test only services
pytest tests/test_services.py -v

# Test with markers
pytest -m "not slow" -v
```

### Run Frontend Tests (when configured)
```bash
cd frontend
npm test
npm test -- --coverage
```

## Performance Testing

### Load Testing
```bash
# Using Apache Bench
ab -n 1000 -c 10 http://localhost:8000/health

# Using wrk
wrk -t12 -c400 -d30s http://localhost:8000/health
```

### Database Query Performance
```bash
# Enable query logging in settings
# Check slow query log
docker-compose exec postgres psql -U postgres -d udyogsetu -c "SELECT * FROM pg_stat_statements LIMIT 10;"
```

## Integration Testing Checklist

### User Authentication
- [ ] User can register
- [ ] User can login
- [ ] Tokens refresh correctly
- [ ] Invalid credentials rejected
- [ ] Password reset works

### Project Management
- [ ] User can create project
- [ ] Project details persist
- [ ] User can view own projects only
- [ ] Project status updates

### Approval Processing
- [ ] Approvals auto-determined by sector
- [ ] Dependency graph generates correctly
- [ ] SLA tracking works
- [ ] Status updates process correctly

### Document Processing
- [ ] Documents upload successfully
- [ ] Fields extract automatically
- [ ] Validation identifies issues
- [ ] Cross-document matching works

### Regulatory Guidance
- [ ] Knowledge base queries return answers
- [ ] Sources cited correctly
- [ ] Government status retrieval works
- [ ] Chat interface functional

### Business Intelligence
- [ ] Compliance scores calculate
- [ ] Scheme matching accurate
- [ ] Subsidy calculations correct
- [ ] Scenarios simulate properly

### Officer Functions
- [ ] Officer can view all applications
- [ ] SLA tracking accurate
- [ ] Alerts generate correctly
- [ ] Reports generate successfully

## Error Scenario Testing

### 1. Authentication Failures
```bash
# Invalid email format
curl -X POST http://localhost:8000/api/auth/login \
  -d '{"email": "invalid", "password": "pass"}'
# Expected: 422 Validation Error

# Non-existent user
curl -X POST http://localhost:8000/api/auth/login \
  -d '{"email": "nonexistent@example.com", "password": "pass"}'
# Expected: 401 Unauthorized
```

### 2. Authorization Failures
```bash
# Access other user's project
curl http://localhost:8000/api/projects/OTHER_USER_PROJECT_ID \
  -H "Authorization: Bearer YOUR_TOKEN"
# Expected: 403 Forbidden
```

### 3. Validation Failures
```bash
# Invalid project data
curl -X POST http://localhost:8000/api/projects \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"name": ""}'  # Missing required fields
# Expected: 422 Validation Error
```

### 4. Database Failures
```bash
# Stop database and try request
docker-compose stop postgres

curl http://localhost:8000/api/projects
# Expected: 503 Service Unavailable or connection error
```

## Deployment Verification

### Docker Compose Health Checks
```bash
# Check all services running
docker-compose ps
# All should be Up

# Check logs
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres

# Health check
curl http://localhost:8000/health
curl http://localhost:3000/
```

### Database Verification
```bash
# Connect to database
docker-compose exec postgres psql -U postgres -d udyogsetu

# Check tables created
\dt

# Check record counts
SELECT COUNT(*) FROM "user";
SELECT COUNT(*) FROM project;
SELECT COUNT(*) FROM approval;
```

## Performance Baseline

Expected response times:
- Health check: < 10ms
- Login: < 100ms
- Get projects: < 200ms
- Create project: < 500ms
- Query regulatory: < 1000ms
- Submit application: < 500ms

## Monitoring

### Application Metrics
```bash
# Check logs for errors
docker-compose logs backend | grep ERROR

# Monitor resource usage
docker stats

# Check database connections
docker-compose exec postgres psql -U postgres -c "SELECT count(*) FROM pg_stat_activity;"
```

## Cleanup & Reset

### Reset Everything
```bash
# Stop and remove all containers
docker-compose down -v

# Remove local database
rm -rf postgresql_data/

# Restart fresh
docker-compose up --build
```

### Reset Single Component
```bash
# Reset frontend only
docker-compose restart frontend

# Reset backend only
docker-compose restart backend

# Reset database
docker-compose down postgres
docker-compose up -d postgres
```

## Troubleshooting Guide

### Backend not responding
1. Check logs: `docker-compose logs backend`
2. Check port: `lsof -i :8000`
3. Restart: `docker-compose restart backend`

### Database connection error
1. Check PostgreSQL: `docker-compose ps postgres`
2. Check URL in .env
3. Reset database: `docker-compose down -v && docker-compose up`

### Frontend build fails
1. Clear cache: `rm -rf frontend/.next frontend/node_modules`
2. Reinstall: `npm install`
3. Rebuild: `npm run build`

### Document upload fails
1. Check file permissions
2. Check file size limits
3. Check temp directory space

## Success Criteria

✅ All tests passing
✅ API response time < 500ms
✅ Database queries < 100ms
✅ UI renders without errors
✅ All approvals calculate correctly
✅ Government integrations respond
✅ Documents process successfully
✅ Compliance scores accurate
✅ Schemes match appropriately
✅ Scenarios simulate correctly

---

For detailed feature documentation, see COMPLETE_FEATURE_GUIDE.md
