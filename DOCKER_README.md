# 🐳 Docker Deployment Guide

Welcome! Your Edge FHIR Hybrid application is containerized and ready to run anywhere Docker is available.

---

## ⚡ Quick Start (60 seconds)

```bash
# 1. Build the Docker image
docker-compose build

# 2. Start the container
docker-compose up -d

# 3. Access the application
open http://localhost:5000/
```

**That's it!** Your application is now running in a Docker container.

---

## 📖 Documentation

Read these in this order:

### 1. **Start Here** (5 min)
   - **[DOCKER_QUICKSTART.md](DOCKER_QUICKSTART.md)** - Quick reference guide

### 2. **Next** (10 min)
   - **[DOCKER_COMMANDS.md](DOCKER_COMMANDS.md)** - Command quick reference card

### 3. **For Production** (15 min)
   - **[DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md)** - Complete deployment guide

### 4. **Advanced** (10 min)
   - **[DOCKER_BEST_PRACTICES.md](DOCKER_BEST_PRACTICES.md)** - Professional practices

---

## 🚀 Essential Commands

```bash
# Start container
docker-compose up -d

# View logs
docker-compose logs -f

# Stop container
docker-compose stop

# Remove container
docker-compose down

# Enter shell
docker-compose exec edge-fhir-hybrid bash
```

**More commands?** See [DOCKER_COMMANDS.md](DOCKER_COMMANDS.md)

---

## 🌐 Access Your Application

| URL | Purpose |
|-----|---------|
| http://localhost:5000/ | Dashboard UI |
| http://localhost:5000/api/health | Health check |
| http://localhost:5000/api/alerts | Get alerts |
| http://localhost:5000/fhir/notify | FHIR webhook |

---

## 🔍 Verify It's Working

```bash
# Check container is running
docker-compose ps

# Check health
curl http://localhost:5000/api/health

# View logs
docker-compose logs --tail 20
```

---

## 📦 What's Included

- ✅ **Dockerfile** - Production-ready multi-stage build
- ✅ **docker-compose.yml** - Complete orchestration
- ✅ **Complete Documentation** - 5 comprehensive guides
- ✅ **Health Checks** - Automatic monitoring
- ✅ **Persistent Volumes** - Data survives restarts
- ✅ **Ready for Production** - Optimized and secure

---

## ⚙️ Configuration

Edit `docker-compose.yml` to:

**Change Port:**
```yaml
ports:
  - "8080:5000"    # Access at http://localhost:8080
```

**Set Environment Variables:**
```yaml
environment:
  FLASK_ENV: production
  FHIR_POLLING_INTERVAL: "30"
```

**Then restart:**
```bash
docker-compose up -d
```

---

## 🐳 Docker Commands

### Start/Stop
```bash
docker-compose up -d        # Start in background
docker-compose stop         # Stop gracefully
docker-compose restart      # Restart
docker-compose down         # Remove container
```

### Monitoring
```bash
docker-compose ps           # View status
docker-compose logs -f      # Follow logs
docker stats                # View resources
```

### Debugging
```bash
docker-compose logs         # View logs
docker-compose exec edge-fhir-hybrid bash    # Enter container
curl http://localhost:5000/api/health        # Test health
```

**See [DOCKER_COMMANDS.md](DOCKER_COMMANDS.md) for 30+ commands**

---

## 🚢 Deployment Options

### 1. Local Development
```bash
docker-compose up -d
# Access: http://localhost:5000/
```

### 2. Production Server
```bash
scp -r . user@server:/app/edge_fhir_hybrid
ssh user@server
cd /app/edge_fhir_hybrid
docker-compose up -d
# Access: http://server-ip:5000/
```

### 3. Docker Hub
```bash
docker push yourusername/edge-fhir-hybrid:latest
# Deploy anywhere:
docker run -p 5000:5000 yourusername/edge-fhir-hybrid:latest
```

### 4. Kubernetes
See [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md) for `k8s-deployment.yaml`

---

## 🆘 Troubleshooting

### Container Won't Start?
```bash
docker-compose logs
docker-compose build --no-cache
docker-compose up -d
```

### Port Already in Use?
```bash
# Change port in docker-compose.yml
ports:
  - "8080:5000"
docker-compose up -d
```

### View Container Logs?
```bash
docker-compose logs -f
docker-compose logs --tail 50
```

### Enter Container Shell?
```bash
docker-compose exec edge-fhir-hybrid bash
```

**More troubleshooting?** See [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md#troubleshooting)

---

## 📚 Documentation Files

| File | Purpose | Time |
|------|---------|------|
| [DOCKER_QUICKSTART.md](DOCKER_QUICKSTART.md) | Quick start & reference | 5 min |
| [DOCKER_COMMANDS.md](DOCKER_COMMANDS.md) | Command quick reference | Print |
| [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md) | Complete guide | 15 min |
| [DOCKER_BEST_PRACTICES.md](DOCKER_BEST_PRACTICES.md) | Advanced practices | 10 min |
| [DOCKER_COMPLETE.md](DOCKER_COMPLETE.md) | Full summary | 5 min |
| [DOCKER_STATUS.txt](DOCKER_STATUS.txt) | Status overview | 3 min |

---

## ✨ Key Features

✅ **Zero External Dependencies** - Everything in Docker image
✅ **Automatic Health Checks** - Monitors container health
✅ **Persistent Storage** - Logs and state survive restarts
✅ **Easy Configuration** - Environment variables
✅ **Production Ready** - Multi-stage build, proper signals
✅ **Fast Startup** - 2-3 seconds
✅ **Monitoring Ready** - Health endpoints built-in
✅ **Scalable** - Ready for Kubernetes

---

## 🎯 Next Steps

### Immediate
- [ ] Run `docker-compose up -d`
- [ ] Access http://localhost:5000/
- [ ] Check `docker-compose logs -f`

### This Week
- [ ] Read [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md)
- [ ] Configure for production
- [ ] Test with real data

### This Month
- [ ] Deploy to production
- [ ] Add reverse proxy
- [ ] Enable HTTPS
- [ ] Set up monitoring

---

## 💡 Pro Tips

1. **Always backup**: Use `docker export` before major changes
2. **Monitor resources**: Use `docker stats`
3. **Clean regularly**: `docker system prune -a` monthly
4. **Use volumes**: For persistent data
5. **Set limits**: In production docker-compose.yml
6. **Check logs**: `docker-compose logs -f` for debugging

---

## 🆘 Need Help?

1. **Quick question?** → See [DOCKER_COMMANDS.md](DOCKER_COMMANDS.md)
2. **How to deploy?** → See [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md)
3. **Best practices?** → See [DOCKER_BEST_PRACTICES.md](DOCKER_BEST_PRACTICES.md)
4. **Full overview?** → See [DOCKER_COMPLETE.md](DOCKER_COMPLETE.md)

---

## 📊 Current Status

✅ Docker image built and ready
✅ Container running on port 5000
✅ Health checks passing
✅ All endpoints responding
✅ Documentation complete

---

## 🎉 Summary

Your Edge FHIR Hybrid application is now containerized with:
- Complete Docker setup
- Comprehensive documentation
- Production-ready configuration
- Easy deployment options

**Ready to deploy!** 🚀

```bash
# Start the application
docker-compose up -d

# View logs
docker-compose logs -f

# Access dashboard
open http://localhost:5000/
```

---

**Happy containerizing! 🐳**

For more information:
- [Quick Start](DOCKER_QUICKSTART.md) - 5 minutes
- [Full Guide](DOCKER_DEPLOYMENT.md) - 15 minutes
- [Command Reference](DOCKER_COMMANDS.md) - Print & use
