# 🚀 One-Click ngrok + Docker Deployment

## External Configuration Architecture

This solution implements a **clean external configuration** approach where:
- ✅ **Application stays clean** - No ngrok URLs hardcoded inside the app
- ✅ **External mapping** - ngrok → nginx → internal services
- ✅ **Environment separation** - All external config via Docker/nginx
- ✅ **Production ready** - Easy transition to production domains

## 🎯 One-Click Deployment

### Prerequisites
1. **Docker Desktop** installed and running
2. **ngrok** installed and configured

### Quick Start
```powershell
# One-click deployment (default action)
.\start-ngrok-docker-external.ps1

# Or explicitly specify oneclick
.\start-ngrok-docker-external.ps1 -Action oneclick
```

### What it does:
1. ✅ Creates external configuration files
2. ✅ Starts Docker services with ngrok configuration
3. ✅ Starts ngrok tunnel automatically
4. ✅ Provides access URLs and next steps

## 📋 Available Actions

```powershell
# One-click deployment (recommended)
.\start-ngrok-docker-external.ps1 -Action oneclick

# Setup only (creates config files)
.\start-ngrok-docker-external.ps1 -Action setup

# Start Docker only (after setup)
.\start-ngrok-docker-external.ps1 -Action start

# Check status
.\start-ngrok-docker-external.ps1 -Action status

# View logs
.\start-ngrok-docker-external.ps1 -Action logs

# Stop services
.\start-ngrok-docker-external.ps1 -Action stop

# Clean up
.\start-ngrok-docker-external.ps1 -Action clean
```

## 🌐 Access URLs

After deployment:
- **Local Access**: http://localhost:80
- **ngrok Dashboard**: http://localhost:4040
- **API Documentation**: http://localhost:80/docs
- **Health Check**: http://localhost:80/health

## 🏗️ Architecture

```
ngrok (external) → nginx:80 → internal services
```

- **ngrok**: Provides public HTTPS tunnel
- **nginx**: Handles CORS, routing, and security
- **Frontend**: Uses relative API URLs (clean)
- **Backend**: Internal CORS only (secure)
- **Database**: Standard MongoDB configuration

## 🔧 Configuration Files

- `docker-compose.ngrok.yml` - Docker Compose override for ngrok
- `docker/nginx-ngrok.conf` - nginx configuration with CORS mapping
- `start-ngrok-docker-external.ps1` - One-click deployment script

## 🚨 Important Notes

1. **Application stays clean** - No ngrok URLs are added to the application
2. **CORS handled externally** - nginx validates ngrok origins
3. **Easy switching** - Switch between local/ngrok/production easily
4. **Production ready** - Architecture supports production deployment

## 📞 Support

For issues or questions:
1. Check the logs: `.\start-ngrok-docker-external.ps1 -Action logs`
2. Check status: `.\start-ngrok-docker-external.ps1 -Action status`
3. Review the DevOps package: `DEVOPS_REVIEW_PACKAGE.md`

---

**Ready to deploy? Run:** `.\start-ngrok-docker-external.ps1`
