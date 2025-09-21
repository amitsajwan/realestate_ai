#!/bin/bash
# Production Deployment Script for PropertyAI
# ===========================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="propertyai"
APP_DIR="/opt/propertyai"
SERVICE_USER="propertyai"
NGINX_SITE="propertyai"
DOMAIN="${1:-your-domain.com}"

echo -e "${BLUE}🚀 Starting PropertyAI Production Deployment${NC}"
echo "Domain: $DOMAIN"
echo "App Directory: $APP_DIR"

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo -e "${RED}❌ This script should not be run as root${NC}"
   exit 1
fi

# Update system packages
echo -e "${YELLOW}📦 Updating system packages...${NC}"
sudo apt update && sudo apt upgrade -y

# Install required packages
echo -e "${YELLOW}📦 Installing required packages...${NC}"
sudo apt install -y \
    python3.11 \
    python3.11-venv \
    python3.11-dev \
    python3-pip \
    nodejs \
    npm \
    nginx \
    certbot \
    python3-certbot-nginx \
    mongodb \
    redis-server \
    git \
    curl \
    wget \
    htop \
    ufw \
    fail2ban

# Create application user
echo -e "${YELLOW}👤 Creating application user...${NC}"
if ! id "$SERVICE_USER" &>/dev/null; then
    sudo useradd -r -s /bin/false -d "$APP_DIR" "$SERVICE_USER"
fi

# Create application directory
echo -e "${YELLOW}📁 Creating application directory...${NC}"
sudo mkdir -p "$APP_DIR"
sudo chown "$USER:$SERVICE_USER" "$APP_DIR"

# Clone or update repository
echo -e "${YELLOW}📥 Setting up application code...${NC}"
if [ -d "$APP_DIR/.git" ]; then
    cd "$APP_DIR"
    git pull origin main
else
    git clone https://github.com/amitsajwan/realestate_ai.git "$APP_DIR"
    cd "$APP_DIR"
fi

# Setup backend
echo -e "${YELLOW}🐍 Setting up Python backend...${NC}"
cd "$APP_DIR/backend"
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Setup frontend
echo -e "${YELLOW}⚛️ Setting up Node.js frontend...${NC}"
cd "$APP_DIR/frontend"
npm install
npm run build

# Create production environment file
echo -e "${YELLOW}⚙️ Creating production environment...${NC}"
sudo tee "$APP_DIR/.env.production" > /dev/null <<EOF
# Application Settings
APP_NAME=PropertyAI
APP_VERSION=2.0.0
DEBUG=false
ENVIRONMENT=production

# Database
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=propertyai_prod

# Security
JWT_SECRET_KEY=$(openssl rand -hex 32)
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# External Services
GROQ_API_KEY=${GROQ_API_KEY:-your-groq-api-key}
OPENAI_API_KEY=${OPENAI_API_KEY:-your-openai-api-key}
GOOGLE_MAPS_API_KEY=${GOOGLE_MAPS_API_KEY:-your-google-maps-api-key}

# Email Settings
SMTP_SERVER=${SMTP_SERVER:-smtp.gmail.com}
SMTP_PORT=${SMTP_PORT:-587}
SMTP_USERNAME=${SMTP_USERNAME:-your-email@gmail.com}
SMTP_PASSWORD=${SMTP_PASSWORD:-your-app-password}
FROM_EMAIL=${FROM_EMAIL:-your-email@gmail.com}

# Redis
REDIS_URL=redis://localhost:6379

# CORS
CORS_ORIGINS=https://$DOMAIN,https://www.$DOMAIN

# File Upload
MAX_FILE_SIZE=10485760
UPLOAD_DIRECTORY=$APP_DIR/uploads

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60

# Logging
LOG_LEVEL=INFO
LOG_FILE=$APP_DIR/logs/app.log

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
EOF

# Create uploads directory
sudo mkdir -p "$APP_DIR/uploads"
sudo mkdir -p "$APP_DIR/logs"
sudo chown -R "$SERVICE_USER:$SERVICE_USER" "$APP_DIR"

# Create systemd service for backend
echo -e "${YELLOW}🔧 Creating backend systemd service...${NC}"
sudo tee /etc/systemd/system/propertyai-backend.service > /dev/null <<EOF
[Unit]
Description=PropertyAI Backend
After=network.target mongodb.service redis.service

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$APP_DIR/backend
Environment=PATH=$APP_DIR/backend/venv/bin
EnvironmentFile=$APP_DIR/.env.production
ExecStart=$APP_DIR/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=propertyai-backend

[Install]
WantedBy=multi-user.target
EOF

# Create systemd service for frontend
echo -e "${YELLOW}🔧 Creating frontend systemd service...${NC}"
sudo tee /etc/systemd/system/propertyai-frontend.service > /dev/null <<EOF
[Unit]
Description=PropertyAI Frontend
After=network.target propertyai-backend.service

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$APP_DIR/frontend
Environment=NODE_ENV=production
Environment=NEXT_PUBLIC_API_URL=https://$DOMAIN/api
ExecStart=/usr/bin/npm start
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=propertyai-frontend

[Install]
WantedBy=multi-user.target
EOF

# Configure Nginx
echo -e "${YELLOW}🌐 Configuring Nginx...${NC}"
sudo tee /etc/nginx/sites-available/$NGINX_SITE > /dev/null <<EOF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied expired no-cache no-store private must-revalidate auth;
    gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml+rss application/javascript;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        proxy_read_timeout 86400;
    }

    # API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        proxy_read_timeout 86400;
    }

    # Health check
    location /health {
        proxy_pass http://localhost:8000/api/v1/health;
        access_log off;
    }

    # Static files
    location /static {
        alias $APP_DIR/frontend/out/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Uploads
    location /uploads {
        alias $APP_DIR/uploads;
        expires 1y;
        add_header Cache-Control "public";
    }
}
EOF

# Enable Nginx site
sudo ln -sf /etc/nginx/sites-available/$NGINX_SITE /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t

# Configure firewall
echo -e "${YELLOW}🔥 Configuring firewall...${NC}"
sudo ufw --force reset
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw --force enable

# Configure fail2ban
echo -e "${YELLOW}🛡️ Configuring fail2ban...${NC}"
sudo tee /etc/fail2ban/jail.local > /dev/null <<EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3

[nginx-http-auth]
enabled = true

[nginx-limit-req]
enabled = true

[sshd]
enabled = true
port = ssh
logpath = /var/log/auth.log
maxretry = 3
EOF

# Start services
echo -e "${YELLOW}🚀 Starting services...${NC}"
sudo systemctl daemon-reload
sudo systemctl enable mongodb redis-server propertyai-backend propertyai-frontend nginx
sudo systemctl start mongodb redis-server
sudo systemctl start propertyai-backend propertyai-frontend
sudo systemctl start nginx

# Wait for services to start
echo -e "${YELLOW}⏳ Waiting for services to start...${NC}"
sleep 10

# Check service status
echo -e "${YELLOW}🔍 Checking service status...${NC}"
sudo systemctl status propertyai-backend --no-pager
sudo systemctl status propertyai-frontend --no-pager
sudo systemctl status nginx --no-pager

# Get SSL certificate
echo -e "${YELLOW}🔒 Getting SSL certificate...${NC}"
sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN --non-interactive --agree-tos --email admin@$DOMAIN

# Setup log rotation
echo -e "${YELLOW}📝 Setting up log rotation...${NC}"
sudo tee /etc/logrotate.d/propertyai > /dev/null <<EOF
$APP_DIR/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 $SERVICE_USER $SERVICE_USER
    postrotate
        systemctl reload propertyai-backend propertyai-frontend
    endscript
}
EOF

# Setup backup script
echo -e "${YELLOW}💾 Setting up backup script...${NC}"
sudo tee /usr/local/bin/backup-propertyai.sh > /dev/null <<EOF
#!/bin/bash
BACKUP_DIR="/var/backups/propertyai"
DATE=\$(date +%Y%m%d_%H%M%S)
mkdir -p \$BACKUP_DIR

# Backup MongoDB
mongodump --db propertyai_prod --out \$BACKUP_DIR/mongodb_\$DATE

# Backup uploads
tar -czf \$BACKUP_DIR/uploads_\$DATE.tar.gz $APP_DIR/uploads

# Backup logs
tar -czf \$BACKUP_DIR/logs_\$DATE.tar.gz $APP_DIR/logs

# Clean old backups (keep 30 days)
find \$BACKUP_DIR -type d -mtime +30 -exec rm -rf {} \;
find \$BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

echo "Backup completed: \$DATE"
EOF

sudo chmod +x /usr/local/bin/backup-propertyai.sh

# Add backup to crontab
echo "0 2 * * * /usr/local/bin/backup-propertyai.sh" | sudo crontab -

# Final health check
echo -e "${YELLOW}🏥 Running final health check...${NC}"
sleep 5
curl -f http://localhost/api/v1/health || echo -e "${RED}❌ Health check failed${NC}"

echo -e "${GREEN}✅ PropertyAI Production Deployment Complete!${NC}"
echo -e "${BLUE}🌐 Your application is available at: https://$DOMAIN${NC}"
echo -e "${BLUE}📊 Health check: https://$DOMAIN/api/v1/health${NC}"
echo -e "${BLUE}📚 API docs: https://$DOMAIN/docs${NC}"
echo -e "${YELLOW}📝 Next steps:${NC}"
echo "1. Update DNS records to point to this server"
echo "2. Configure your domain in the application"
echo "3. Set up monitoring and alerting"
echo "4. Test all functionality"
echo "5. Set up regular backups"

echo -e "${GREEN}🎉 Deployment successful!${NC}"
