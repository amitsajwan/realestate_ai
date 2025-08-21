# PropertyAI - Deployment Guide
*Production Deployment and Maintenance*

## 🚀 Quick Deployment Options

### Option 1: Local Development
```bash
# Clone repository
git clone <repository-url>
cd realestate_ai

# Setup Python environment
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Setup database
python database_setup.py

# Start application
python simple_backend.py
```

### Option 2: Docker Deployment
```bash
# Build and run with Docker
docker build -t propertyai .
docker run -p 8003:8003 --env-file .env propertyai

# Or use Docker Compose
docker-compose up -d
```

### Option 3: Cloud Deployment
- **AWS**: Use Elastic Beanstalk or ECS
- **Google Cloud**: App Engine or Cloud Run
- **Heroku**: Direct git deployment
- **DigitalOcean**: App Platform

## 📋 Pre-Deployment Checklist

### ✅ Environment Configuration
- [ ] `GROQ_API_KEY` - AI content generation
- [ ] `FB_APP_ID` - Facebook integration
- [ ] `FB_APP_SECRET` - Facebook OAuth
- [ ] `FB_REDIRECT_URI` - OAuth callback URL
- [ ] `JWT_SECRET_KEY` - Authentication security
- [ ] `ENCRYPTION_KEY` - Token encryption
- [ ] `DATABASE_URL` - Production database

### ✅ Security Setup
- [ ] SSL certificate configured
- [ ] CORS origins restricted
- [ ] Rate limiting enabled
- [ ] Input validation active
- [ ] Database access secured
- [ ] API keys rotated
- [ ] Backup strategy implemented

### ✅ Performance Optimization
- [ ] Database indexes created
- [ ] Response caching configured
- [ ] Static file CDN setup
- [ ] Image optimization enabled
- [ ] Monitoring tools deployed

## 🔧 Production Configuration

### Environment Variables
```env
# Core Application
DEBUG=False
HOST=0.0.0.0
PORT=8003
WORKERS=4

# Database
DATABASE_URL=postgresql://user:password@host:5432/propertyai
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30

# Security
JWT_SECRET_KEY=your-super-secret-jwt-key-min-32-chars
ENCRYPTION_KEY=your-fernet-encryption-key-44-chars
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# AI Integration
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxx
GROQ_MODEL=llama3-8b-8192
AI_RATE_LIMIT=100

# Facebook Integration
FB_APP_ID=123456789012345
FB_APP_SECRET=abcdef123456789abcdef123456789ab
FB_REDIRECT_URI=https://yourdomain.com/api/facebook/callback
FB_GRAPH_API_VERSION=v19.0

# Monitoring
SENTRY_DSN=https://xxxxx@sentry.io/xxxxx
LOG_LEVEL=INFO
METRICS_ENABLED=True

# Redis (for caching)
REDIS_URL=redis://localhost:6379/0
CACHE_TTL=300
```

### Database Migration to PostgreSQL
```python
# production_setup.py
import os
import psycopg2
from database_setup import get_database_connection

def migrate_to_postgresql():
    # PostgreSQL connection
    pg_conn = psycopg2.connect(os.getenv('DATABASE_URL'))
    pg_cursor = pg_conn.cursor()
    
    # SQLite connection
    sqlite_conn = get_database_connection()
    sqlite_cursor = sqlite_conn.cursor()
    
    # Migrate each table
    tables = ['users', 'agent_profiles', 'properties', 'facebook_connections']
    
    for table in tables:
        print(f"Migrating {table}...")
        sqlite_cursor.execute(f"SELECT * FROM {table}")
        rows = sqlite_cursor.fetchall()
        
        # Insert into PostgreSQL
        for row in rows:
            placeholders = ','.join(['%s'] * len(row))
            pg_cursor.execute(f"INSERT INTO {table} VALUES ({placeholders})", row)
    
    pg_conn.commit()
    print("Migration completed!")

if __name__ == "__main__":
    migrate_to_postgresql()
```

### Production Application Configuration
```python
# production_backend.py
import os
import logging
from fastapi import FastAPI
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
import redis

# Production settings
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
WORKERS = int(os.getenv('WORKERS', '4'))

# Setup logging
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(429, _rate_limit_exceeded_handler)

# Redis for caching
redis_client = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379'))

# Production CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv('CORS_ORIGINS', '').split(','),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "production_backend:app",
        host=os.getenv('HOST', '0.0.0.0'),
        port=int(os.getenv('PORT', 8003)),
        workers=WORKERS,
        access_log=not DEBUG
    )
```

## 🐳 Docker Configuration

### Dockerfile
```dockerfile
FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8003

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8003/health')"

# Start application
CMD ["python", "production_backend.py"]
```

### Docker Compose for Production
```yaml
version: '3.8'

services:
  app:
    build: .
    restart: unless-stopped
    ports:
      - "8003:8003"
    environment:
      - DATABASE_URL=postgresql://postgres:${POSTGRES_PASSWORD}@db:5432/propertyai
      - REDIS_URL=redis://redis:6379/0
    env_file:
      - .env
    depends_on:
      - db
      - redis
    volumes:
      - ./logs:/app/logs
    networks:
      - propertyai-network

  db:
    image: postgres:13-alpine
    restart: unless-stopped
    environment:
      POSTGRES_DB: propertyai
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    ports:
      - "5432:5432"
    networks:
      - propertyai-network

  redis:
    image: redis:6-alpine
    restart: unless-stopped
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    networks:
      - propertyai-network

  nginx:
    image: nginx:alpine
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - app
    networks:
      - propertyai-network

volumes:
  postgres_data:
  redis_data:

networks:
  propertyai-network:
    driver: bridge
```

### Nginx Configuration
```nginx
# nginx.conf
events {
    worker_connections 1024;
}

http {
    upstream app {
        server app:8003;
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    
    server {
        listen 80;
        server_name yourdomain.com www.yourdomain.com;
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name yourdomain.com www.yourdomain.com;

        # SSL configuration
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;

        # Security headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        add_header Strict-Transport-Security "max-age=31536000";

        # Static files
        location /static/ {
            alias /app/static/;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }

        # API endpoints with rate limiting
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Main application
        location / {
            proxy_pass http://app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
```

## ☁️ Cloud Deployment Examples

### AWS Elastic Beanstalk
```yaml
# .ebextensions/01_packages.config
packages:
  yum:
    postgresql-devel: []
    gcc: []

# .platform/hooks/prebuild/01_setup.sh
#!/bin/bash
pip install -r requirements.txt
python database_setup.py
```

### Google Cloud Run
```yaml
# cloudbuild.yaml
steps:
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/propertyai', '.']
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/propertyai']
  - name: 'gcr.io/cloud-builders/gcloud'
    args:
      - 'run'
      - 'deploy'
      - 'propertyai'
      - '--image'
      - 'gcr.io/$PROJECT_ID/propertyai'
      - '--region'
      - 'us-central1'
      - '--platform'
      - 'managed'
```

### Heroku Deployment
```bash
# Procfile
web: python production_backend.py

# runtime.txt
python-3.9.18

# Deploy commands
heroku create propertyai-app
heroku addons:create heroku-postgresql:hobby-dev
heroku addons:create heroku-redis:hobby-dev
heroku config:set GROQ_API_KEY=your_key
git push heroku main
```

## 📊 Monitoring and Logging

### Application Monitoring
```python
# monitoring.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

# Sentry setup
sentry_sdk.init(
    dsn=os.getenv('SENTRY_DSN'),
    integrations=[
        FastApiIntegration(auto_enabling_integrations=False),
        SqlalchemyIntegration(),
    ],
    traces_sample_rate=0.1,
    environment=os.getenv('ENVIRONMENT', 'production')
)

# Custom metrics
from prometheus_client import Counter, Histogram, generate_latest

request_count = Counter('requests_total', 'Total requests', ['method', 'endpoint'])
request_duration = Histogram('request_duration_seconds', 'Request duration')

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    request_count.labels(method=request.method, endpoint=request.url.path).inc()
    request_duration.observe(duration)
    
    return response

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

### Logging Configuration
```python
# logging_config.py
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
            
        return json.dumps(log_entry)

# Setup
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logging.getLogger().addHandler(handler)
logging.getLogger().setLevel(logging.INFO)
```

## 🔄 Backup and Recovery

### Database Backup Script
```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"
DB_NAME="propertyai"

# PostgreSQL backup
pg_dump $DATABASE_URL > "$BACKUP_DIR/propertyai_$DATE.sql"

# Compress backup
gzip "$BACKUP_DIR/propertyai_$DATE.sql"

# Upload to S3 (optional)
aws s3 cp "$BACKUP_DIR/propertyai_$DATE.sql.gz" s3://your-backup-bucket/

# Clean old backups (keep last 30 days)
find $BACKUP_DIR -name "propertyai_*.sql.gz" -mtime +30 -delete

echo "Backup completed: propertyai_$DATE.sql.gz"
```

### Automated Backup with Cron
```bash
# Add to crontab: crontab -e
# Daily backup at 2 AM
0 2 * * * /path/to/backup.sh >> /var/log/backup.log 2>&1

# Weekly full backup
0 3 * * 0 /path/to/full_backup.sh >> /var/log/backup.log 2>&1
```

## 🔒 Security Hardening

### SSL/TLS Configuration
```bash
# Generate SSL certificate with Let's Encrypt
certbot certonly --webroot -w /var/www/html -d yourdomain.com -d www.yourdomain.com

# Auto-renewal
echo "0 12 * * * /usr/bin/certbot renew --quiet" | crontab -
```

### Firewall Configuration
```bash
# UFW (Ubuntu)
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw deny 8003/tcp  # Block direct access to app
ufw enable

# Fail2ban for SSH protection
apt install fail2ban
systemctl enable fail2ban
systemctl start fail2ban
```

### Environment Security
```bash
# Secure environment file
chmod 600 .env
chown app:app .env

# Remove sensitive files from git
echo ".env" >> .gitignore
echo "*.key" >> .gitignore
echo "*.pem" >> .gitignore
```

## 📈 Performance Tuning

### Database Optimization
```sql
-- Performance indexes
CREATE INDEX CONCURRENTLY idx_properties_created_at ON properties(created_at DESC);
CREATE INDEX CONCURRENTLY idx_facebook_posts_user_id_created ON facebook_posts(user_id, created_at DESC);

-- Query optimization
EXPLAIN ANALYZE SELECT * FROM properties WHERE user_id = 1 ORDER BY created_at DESC LIMIT 10;

-- Connection pooling
ALTER SYSTEM SET max_connections = 200;
ALTER SYSTEM SET shared_buffers = '256MB';
SELECT pg_reload_conf();
```

### Application Caching
```python
# Redis caching layer
import asyncio
import json
import redis.asyncio as redis

class CacheManager:
    def __init__(self):
        self.redis = redis.from_url(os.getenv('REDIS_URL'))
    
    async def get(self, key: str):
        try:
            data = await self.redis.get(key)
            return json.loads(data) if data else None
        except Exception:
            return None
    
    async def set(self, key: str, value, ttl: int = 300):
        try:
            await self.redis.setex(key, ttl, json.dumps(value))
        except Exception:
            pass

cache = CacheManager()

# Cache expensive operations
async def get_properties_cached(user_id: int):
    cache_key = f"properties:{user_id}"
    cached = await cache.get(cache_key)
    
    if cached:
        return cached
    
    properties = await get_user_properties(user_id)
    await cache.set(cache_key, properties, ttl=300)
    return properties
```

---

*PropertyAI Deployment Guide - Production Ready Configuration*

