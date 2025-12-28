# Docker Commands Quick Reference Card

## 🚀 Essential Commands

### Build & Deploy
```bash
# Build the Docker image
docker-compose build

# Start the container (background)
docker-compose up -d

# Start the container (foreground)
docker-compose up

# Stop the container
docker-compose stop

# Restart the container
docker-compose restart

# Stop and remove container
docker-compose down

# Stop and remove everything (including volumes)
docker-compose down -v
```

---

## 📊 Monitoring & Status

```bash
# Check container status
docker-compose ps

# View real-time logs
docker-compose logs -f

# View last 50 lines of logs
docker-compose logs --tail 50

# View logs from last hour
docker-compose logs --since 1h

# View resource usage (CPU, Memory)
docker stats edge-fhir-hybrid

# Check health status
docker-compose exec edge-fhir-hybrid curl http://localhost:5000/api/health
```

---

## 🐚 Container Access

```bash
# Enter container shell
docker-compose exec edge-fhir-hybrid bash

# Run command in container
docker-compose exec edge-fhir-hybrid python --version

# View file in container
docker-compose exec edge-fhir-hybrid cat /app/logs/alerts.log

# Copy file from container to host
docker cp edge-fhir-hybrid:/app/logs/alerts.log ./alerts-backup.log

# Copy file from host to container
docker cp ./data.json edge-fhir-hybrid:/app/data.json
```

---

## 🧹 Cleanup & Maintenance

```bash
# Remove stopped containers
docker container prune

# Remove unused images
docker image prune

# Remove unused volumes
docker volume prune

# Remove everything unused
docker system prune -a

# Remove specific image
docker rmi edge_fhir_hybrid:old-version

# Remove all containers
docker rm $(docker ps -a -q)
```

---

## 🔍 Debugging

```bash
# View detailed logs
docker-compose logs --tail 100

# Check container details
docker inspect edge-fhir-hybrid

# Get container's IP address
docker inspect -f '{{.NetworkSettings.IPAddress}}' edge-fhir-hybrid

# List running processes in container
docker top edge-fhir-hybrid

# Check container configuration
docker-compose exec edge-fhir-hybrid env
```

---

## 📦 Image Management

```bash
# List all images
docker image ls

# List all containers (including stopped)
docker ps -a

# View image history
docker history edge_fhir_hybrid:latest

# Tag image for Docker Hub
docker tag edge_fhir_hybrid:latest yourusername/edge-fhir-hybrid:latest

# Push to Docker Hub
docker push yourusername/edge-fhir-hybrid:latest

# Pull image from Docker Hub
docker pull yourusername/edge-fhir-hybrid:latest
```

---

## 🌐 Network & Volumes

```bash
# List all networks
docker network ls

# List all volumes
docker volume ls

# Inspect network
docker network inspect edge_fhir_hybrid_fhir-network

# Create volume
docker volume create my-volume

# Remove volume
docker volume rm my-volume

# Clean unused volumes
docker volume prune
```

---

## 🐳 Docker Compose Specific

```bash
# View docker-compose version
docker-compose --version

# Validate docker-compose.yml
docker-compose config

# Build images without starting
docker-compose build --no-cache

# Start service with specific environment file
docker-compose -f docker-compose.yml --env-file .env up -d

# Use production compose file
docker-compose -f docker-compose.prod.yml up -d

# Scale service (if configured)
docker-compose up -d --scale app=3
```

---

## 🔐 Security & Logs

```bash
# View Docker log driver
docker inspect edge-fhir-hybrid | grep -A 10 LogConfig

# View system logs
docker-compose logs --since 2025-01-01T00:00:00

# Filter error logs
docker-compose logs | grep -i error

# Export container as tar
docker export edge-fhir-hybrid > container.tar

# Save image as tar
docker save edge_fhir_hybrid:latest > image.tar

# Load image from tar
docker load < image.tar
```

---

## 💾 Backup & Restore

```bash
# Backup volume data
docker run --rm -v edge_fhir_hybrid_logs:/data \
  -v $(pwd):/backup alpine \
  tar czf /backup/logs-backup.tar.gz -C /data .

# Backup database
docker-compose exec postgres pg_dump -U user db > backup.sql

# Restore database
docker-compose exec -T postgres psql -U user db < backup.sql

# List volume data
docker run --rm -v edge_fhir_hybrid_logs:/data \
  alpine ls -la /data/
```

---

## 🚨 Troubleshooting Commands

```bash
# Check if port is in use
netstat -ano | findstr :5000        # Windows
lsof -i :5000                       # macOS/Linux

# Kill process using port
taskkill /PID <PID> /F              # Windows
kill -9 $(lsof -t -i:5000)          # macOS/Linux

# Rebuild without cache
docker-compose build --no-cache

# Force restart
docker-compose restart -f

# Check disk usage
docker system df

# View logs with timestamps
docker-compose logs --timestamps

# Follow logs with tail
docker-compose logs -f --tail 0
```

---

## 🎯 Common Workflows

### Fresh Start
```bash
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
docker-compose logs -f
```

### Deploy New Version
```bash
git pull
docker-compose build --no-cache
docker-compose up -d
docker-compose logs -f
```

### Debug Issue
```bash
docker-compose logs
docker-compose exec edge-fhir-hybrid bash
# Inside container: check logs, run tests, etc.
exit
docker-compose restart
```

### Backup Before Update
```bash
docker-compose exec edge-fhir-hybrid bash
cp logs/alerts.log logs/alerts.log.backup
exit
docker-compose stop
docker-compose build
docker-compose up -d
```

### Monitor Application
```bash
# In one terminal:
docker-compose logs -f

# In another terminal:
watch -n 1 'docker stats --no-stream edge-fhir-hybrid'
```

---

## 📝 Quick Reference Table

| Task | Command |
|------|---------|
| **Start** | `docker-compose up -d` |
| **Stop** | `docker-compose stop` |
| **Restart** | `docker-compose restart` |
| **Remove** | `docker-compose down` |
| **Logs** | `docker-compose logs -f` |
| **Status** | `docker-compose ps` |
| **Shell** | `docker-compose exec edge-fhir-hybrid bash` |
| **Health** | `curl http://localhost:5000/api/health` |
| **Stats** | `docker stats edge-fhir-hybrid` |
| **Rebuild** | `docker-compose build --no-cache` |

---

## ⚡ Pro Tips

1. **Use `.env` file** for sensitive variables
2. **Add `--no-cache`** when rebuilding to get fresh dependencies
3. **Use `tail`** for large logs: `docker-compose logs --tail 100`
4. **Monitor resources**: `docker stats` shows real-time usage
5. **Keep images small**: Use multi-stage builds
6. **Always backup**: Use `docker export/save` before major changes
7. **Clean regularly**: `docker system prune -a` quarterly
8. **Use volumes** for persistent data
9. **Set resource limits** in production
10. **Use health checks** for automatic recovery

---

## 🆘 Emergency Commands

```bash
# Force stop all containers
docker-compose kill

# Remove all images
docker rmi $(docker images -q)

# Remove all containers
docker rm $(docker ps -a -q)

# Nuclear option (remove everything)
docker system prune -a --volumes

# Reset Docker daemon
systemctl restart docker              # Linux
killall com.docker.osx.hypervisor.service  # macOS
# Windows: Restart Docker Desktop UI
```

---

## 📚 Related Files

- `docker-compose.yml` - Configuration file
- `Dockerfile` - Image specification
- `.dockerignore` - Build exclusions
- `DOCKER_DEPLOYMENT.md` - Detailed guide
- `DOCKER_QUICKSTART.md` - Quick start
- `DOCKER_BEST_PRACTICES.md` - Advanced practices

---

**Print this card and keep it handy!** 📌

For more detailed information, see `DOCKER_DEPLOYMENT.md`
