# PropertyAI Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying the PropertyAI platform across different environments.

## Prerequisites

- Docker and Docker Compose
- Node.js 18+ and npm
- Python 3.11+
- MongoDB 6.0+
- Redis 6.0+
- Git

## Environment Variables

Create a `.env` file in the project root with the following variables:

```bash
# Application Settings
APP_NAME=PropertyAI
APP_VERSION=1.0.0
DEBUG=false
ENVIRONMENT=production

# Database
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=propertyai

# Security
JWT_SECRET_KEY=your_jwt_secret_key_here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# External Services
GROQ_API_KEY=your_groq_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here

# Email Settings
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
FROM_EMAIL=your_email@gmail.com

# Redis
REDIS_URL=redis://localhost:6379

# CORS
CORS_ORIGINS=http://localhost:3000,https://propertyai.com

# File Upload
MAX_FILE_SIZE=10485760
UPLOAD_DIRECTORY=uploads

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/app.log

# Feature Flags
ENABLE_FACEBOOK_INTEGRATION=true
ENABLE_EMAIL_NOTIFICATIONS=true
ENABLE_ANALYTICS=true
ENABLE_AI_FEATURES=true

# Monitoring
ENABLE_METRICS=true
METRICS_PORT=9090
HEALTH_CHECK_INTERVAL=30

# Backup
BACKUP_ENABLED=true
BACKUP_SCHEDULE=0 2 * * *
BACKUP_RETENTION_DAYS=30
```

## Local Development Setup

### 1. Clone Repository

```bash
git clone https://github.com/amitsajwan/realestate_ai.git
cd realestate_ai
```

### 2. Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Frontend Setup

```bash
cd frontend
npm install
```

### 4. Database Setup

```bash
# Start MongoDB
sudo systemctl start mongod
# Or on macOS with Homebrew
brew services start mongodb-community

# Start Redis
sudo systemctl start redis
# Or on macOS with Homebrew
brew services start redis
```

### 5. Run Application

```bash
# Terminal 1 - Backend
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 - Frontend
cd frontend
npm run dev
```

## Docker Deployment

### 1. Build Images

```bash
# Build backend image
docker build -t propertyai-backend ./backend

# Build frontend image
docker build -t propertyai-frontend ./frontend
```

### 2. Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  mongodb:
    image: mongo:6.0
    container_name: propertyai-mongodb
    restart: unless-stopped
    ports:
      - "27017:27017"
    environment:
      MONGO_INITDB_ROOT_USERNAME: admin
      MONGO_INITDB_ROOT_PASSWORD: password
    volumes:
      - mongodb_data:/data/db
      - ./mongodb-init:/docker-entrypoint-initdb.d

  redis:
    image: redis:6.0-alpine
    container_name: propertyai-redis
    restart: unless-stopped
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  backend:
    build: ./backend
    container_name: propertyai-backend
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      - MONGODB_URL=mongodb://mongodb:27017
      - REDIS_URL=redis://redis:6379
    depends_on:
      - mongodb
      - redis
    volumes:
      - ./uploads:/app/uploads

  frontend:
    build: ./frontend
    container_name: propertyai-frontend
    restart: unless-stopped
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
    depends_on:
      - backend

volumes:
  mongodb_data:
  redis_data:
```

### 3. Deploy with Docker Compose

```bash
docker-compose up -d
```

## Production Deployment

### 1. Server Requirements

- Ubuntu 20.04+ or CentOS 8+
- 4GB RAM minimum (8GB recommended)
- 50GB storage minimum
- SSL certificate

### 2. Install Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install Python
sudo apt install python3.11 python3.11-venv python3.11-dev

# Install MongoDB
wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | sudo apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/6.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-6.0.list
sudo apt-get update
sudo apt-get install -y mongodb-org

# Install Redis
sudo apt install redis-server

# Install Nginx
sudo apt install nginx

# Install Certbot for SSL
sudo apt install certbot python3-certbot-nginx
```

### 3. Configure Services

#### MongoDB Configuration

```bash
sudo systemctl start mongod
sudo systemctl enable mongod
```

#### Redis Configuration

```bash
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

#### Nginx Configuration

Create `/etc/nginx/sites-available/propertyai`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
```

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/propertyai /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 4. SSL Certificate

```bash
sudo certbot --nginx -d your-domain.com
```

### 5. Deploy Application

```bash
# Clone repository
git clone https://github.com/amitsajwan/realestate_ai.git
cd realestate_ai

# Setup backend
cd backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Setup frontend
cd ../frontend
npm install
npm run build

# Create systemd service for backend
sudo tee /etc/systemd/system/propertyai-backend.service > /dev/null <<EOF
[Unit]
Description=PropertyAI Backend
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/realestate_ai/backend
Environment=PATH=/path/to/realestate_ai/backend/venv/bin
ExecStart=/path/to/realestate_ai/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Create systemd service for frontend
sudo tee /etc/systemd/system/propertyai-frontend.service > /dev/null <<EOF
[Unit]
Description=PropertyAI Frontend
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/realestate_ai/frontend
Environment=PATH=/usr/bin:/usr/local/bin
ExecStart=/usr/bin/npm start
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Start services
sudo systemctl daemon-reload
sudo systemctl enable propertyai-backend
sudo systemctl enable propertyai-frontend
sudo systemctl start propertyai-backend
sudo systemctl start propertyai-frontend
```

## Monitoring and Logging

### 1. Application Logs

```bash
# Backend logs
sudo journalctl -u propertyai-backend -f

# Frontend logs
sudo journalctl -u propertyai-frontend -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### 2. Health Checks

```bash
# Backend health
curl http://localhost:8000/health

# Frontend health
curl http://localhost:3000

# Database health
mongosh --eval "db.adminCommand('ping')"
```

### 3. Performance Monitoring

```bash
# Install monitoring tools
sudo apt install htop iotop nethogs

# Monitor system resources
htop

# Monitor disk I/O
sudo iotop

# Monitor network usage
sudo nethogs
```

## Backup and Recovery

### 1. Database Backup

```bash
# Create backup script
sudo tee /usr/local/bin/backup-propertyai.sh > /dev/null <<EOF
#!/bin/bash
BACKUP_DIR="/var/backups/propertyai"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Backup MongoDB
mongodump --db propertyai --out $BACKUP_DIR/mongodb_$DATE

# Backup uploads
tar -czf $BACKUP_DIR/uploads_$DATE.tar.gz /path/to/realestate_ai/uploads

# Clean old backups (keep 30 days)
find $BACKUP_DIR -type d -mtime +30 -exec rm -rf {} \;
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
EOF

sudo chmod +x /usr/local/bin/backup-propertyai.sh

# Add to crontab
echo "0 2 * * * /usr/local/bin/backup-propertyai.sh" | sudo crontab -
```

### 2. Restore from Backup

```bash
# Restore MongoDB
mongorestore --db propertyai /var/backups/propertyai/mongodb_YYYYMMDD_HHMMSS/propertyai

# Restore uploads
tar -xzf /var/backups/propertyai/uploads_YYYYMMDD_HHMMSS.tar.gz -C /
```

## Security Considerations

### 1. Firewall Configuration

```bash
# Install UFW
sudo apt install ufw

# Configure firewall
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

### 2. SSL/TLS Configuration

```bash
# Generate strong SSL configuration
sudo tee /etc/nginx/snippets/ssl-propertyai.conf > /dev/null <<EOF
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
ssl_prefer_server_ciphers off;
ssl_session_cache shared:SSL:10m;
ssl_session_timeout 10m;
ssl_stapling on;
ssl_stapling_verify on;
add_header Strict-Transport-Security "max-age=63072000" always;
EOF
```

### 3. Application Security

- Use environment variables for sensitive data
- Enable HTTPS only
- Implement rate limiting
- Regular security updates
- Monitor access logs

## Troubleshooting

### Common Issues

1. **Port already in use**
   ```bash
   sudo lsof -i :8000
   sudo kill -9 <PID>
   ```

2. **Permission denied**
   ```bash
   sudo chown -R www-data:www-data /path/to/realestate_ai
   ```

3. **Database connection failed**
   ```bash
   sudo systemctl status mongod
   sudo systemctl restart mongod
   ```

4. **Frontend build failed**
   ```bash
   cd frontend
   rm -rf node_modules package-lock.json
   npm install
   npm run build
   ```

### Log Analysis

```bash
# Check system logs
sudo journalctl -xe

# Check application logs
tail -f /var/log/nginx/error.log
tail -f /var/log/mongodb/mongod.log
```

## Scaling

### Horizontal Scaling

1. **Load Balancer Configuration**
2. **Database Replication**
3. **CDN Integration**
4. **Caching Strategy**

### Vertical Scaling

1. **Increase Server Resources**
2. **Optimize Database Queries**
3. **Implement Caching**
4. **Code Optimization**

## Maintenance

### Regular Tasks

1. **Security Updates**
   ```bash
   sudo apt update && sudo apt upgrade
   ```

2. **Log Rotation**
   ```bash
   sudo logrotate -f /etc/logrotate.conf
   ```

3. **Database Optimization**
   ```bash
   mongosh --eval "db.runCommand({compact: 'your_collection'})"
   ```

4. **Backup Verification**
   ```bash
   /usr/local/bin/backup-propertyai.sh
   ```

## Support

For deployment issues or questions:

1. Check the troubleshooting section
2. Review application logs
3. Check system resources
4. Contact the development team

## Environment Variables Reference

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `APP_NAME` | Application name | PropertyAI | No |
| `DEBUG` | Debug mode | false | No |
| `MONGODB_URL` | MongoDB connection string | mongodb://localhost:27017 | Yes |
| `JWT_SECRET_KEY` | JWT signing key | - | Yes |
| `GROQ_API_KEY` | Groq API key | - | Yes |
| `REDIS_URL` | Redis connection string | redis://localhost:6379 | No |
| `CORS_ORIGINS` | Allowed CORS origins | http://localhost:3000 | No |

## Conclusion

This deployment guide provides comprehensive instructions for deploying PropertyAI across different environments. Follow the steps carefully and ensure all prerequisites are met before proceeding with deployment.

For additional support or questions, please refer to the project documentation or contact the development team.