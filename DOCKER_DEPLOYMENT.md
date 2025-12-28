# Docker Deployment Guide

## Quick Start

### Prerequisites
- Docker installed ([Download](https://www.docker.com/products/docker-desktop))
- Docker Compose (included with Docker Desktop)

### Deploy in 3 Commands

```bash
# 1. Build the Docker image
docker-compose build

# 2. Start the container
docker-compose up -d

# 3. Check logs
docker-compose logs -f
```

### Access the Application
- **Dashboard**: http://localhost:5000/
- **API Health**: http://localhost:5000/api/health
- **Alerts API**: http://localhost:5000/api/alerts

---

## Detailed Setup

### 1. Build the Docker Image

```bash
docker-compose build
```

**Output:**
```
Building edge-fhir-hybrid
Step 1/11 : FROM python:3.10-slim as builder
Step 2/11 : WORKDIR /build
...
Successfully built abc123def456
Successfully tagged edge_fhir_hybrid:latest
```

### 2. Start the Container

```bash
# Start in background (detached mode)
docker-compose up -d

# Or start in foreground (see logs immediately)
docker-compose up
```

**Expected Output:**
```
Creating edge-fhir-hybrid ... done
```

### 3. Verify Container is Running

```bash
# Check container status
docker-compose ps

# View logs
docker-compose logs

# Follow logs (tail -f)
docker-compose logs -f

# View last 50 lines
docker-compose logs --tail 50
```

---

## Docker Commands

### Basic Operations

```bash
# Start container (if stopped)
docker-compose start

# Stop container (gracefully)
docker-compose stop

# Restart container
docker-compose restart

# Stop and remove container
docker-compose down

# Remove volumes too (WARNING: deletes logs!)
docker-compose down -v

# Remove image
docker-compose down --rmi all
```

### Inspection

```bash
# Check container status
docker-compose ps

# Inspect container
docker-compose exec edge-fhir-hybrid bash

# View resource usage
docker stats edge-fhir-hybrid

# View environment variables
docker-compose exec edge-fhir-hybrid env
```

### Debugging

```bash
# View logs
docker-compose logs

# View only error logs
docker-compose logs | grep -i error

# View logs from last hour
docker-compose logs --since 1h

# Enter container shell
docker-compose exec edge-fhir-hybrid bash

# Run command in container
docker-compose exec edge-fhir-hybrid python --version

# Check health status
docker-compose exec edge-fhir-hybrid curl http://localhost:5000/api/health
```

---

## Configuration

### Environment Variables

Edit `docker-compose.yml` to configure the application:

```yaml
environment:
  FLASK_ENV: production
  FHIR_SERVER_BASE_URL: https://hapi.fhir.org/baseR4
  FHIR_POLLING_ENABLED: "true"
  FHIR_POLLING_INTERVAL: "30"
  FHIR_POLLING_BATCH_SIZE: "20"
```

### Port Mapping

Change the exposed port in `docker-compose.yml`:

```yaml
ports:
  - "8080:5000"  # Access at http://localhost:8080
```

### Volume Mounts

The compose file persists:
- `./logs` - Alert logs
- `./.fhir_polling_tracker.json` - Polling state

To disable persistence, remove volume entries:

```yaml
volumes:
  # Remove or comment out these lines
  # - ./logs:/app/logs
  # - ./.fhir_polling_tracker.json:/app/.fhir_polling_tracker.json
```

---

## Production Deployment

### 1. Update Configuration for Production

Edit `app/config.py` before building:

```python
FLASK_DEBUG = False           # Disable debug mode
FLASK_HOST = '0.0.0.0'        # Accept external connections
```

Or set via environment variables in docker-compose.yml:

```yaml
environment:
  FLASK_ENV: production
```

### 2. Use a Production WSGI Server

For production, replace the Flask development server with Gunicorn:

**Update requirements.txt:**
```bash
gunicorn==20.1.0
```

**Update Dockerfile CMD:**
```dockerfile
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "60", "app.server:app"]
```

### 3. Add Environment File

Create `.env.production`:
```
FLASK_ENV=production
FHIR_SERVER_BASE_URL=https://your-fhir-server.com/baseR4
```

Update docker-compose.yml:
```yaml
env_file:
  - .env.production
```

### 4. Configure Reverse Proxy (Nginx)

Create `nginx.conf`:
```nginx
upstream edge_fhir {
    server edge-fhir-hybrid:5000;
}

server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://edge_fhir;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Add to docker-compose.yml:
```yaml
services:
  nginx:
    image: nginx:latest
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf
    depends_on:
      - edge-fhir-hybrid
    networks:
      - fhir-network
```

### 5. Enable HTTPS

Add SSL certificates and configure Nginx:

```bash
# Generate self-signed certificate
openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365
```

Update nginx.conf:
```nginx
server {
    listen 443 ssl;
    ssl_certificate /etc/nginx/certs/cert.pem;
    ssl_certificate_key /etc/nginx/certs/key.pem;
    # ... rest of config
}
```

---

## Docker Hub (Optional)

### Push Image to Docker Hub

```bash
# Login
docker login

# Tag image
docker tag edge_fhir_hybrid:latest yourusername/edge-fhir-hybrid:latest

# Push
docker push yourusername/edge-fhir-hybrid:latest

# Deploy from Docker Hub
docker run -d \
  -p 5000:5000 \
  -v $(pwd)/logs:/app/logs \
  yourusername/edge-fhir-hybrid:latest
```

---

## Kubernetes Deployment (Advanced)

### Deployment Manifest

Create `k8s-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: edge-fhir-hybrid
spec:
  replicas: 2
  selector:
    matchLabels:
      app: edge-fhir-hybrid
  template:
    metadata:
      labels:
        app: edge-fhir-hybrid
    spec:
      containers:
      - name: edge-fhir-hybrid
        image: edge_fhir_hybrid:latest
        ports:
        - containerPort: 5000
        env:
        - name: FLASK_ENV
          value: "production"
        livenessProbe:
          httpGet:
            path: /api/health
            port: 5000
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /api/health
            port: 5000
          initialDelaySeconds: 5
          periodSeconds: 10
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        volumeMounts:
        - name: logs
          mountPath: /app/logs
      volumes:
      - name: logs
        persistentVolumeClaim:
          claimName: edge-fhir-logs-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: edge-fhir-hybrid-service
spec:
  selector:
    app: edge-fhir-hybrid
  ports:
  - protocol: TCP
    port: 80
    targetPort: 5000
  type: LoadBalancer
```

Deploy:
```bash
kubectl apply -f k8s-deployment.yaml
```

---

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose logs

# Check for port conflicts
docker ps
lsof -i :5000  # (macOS/Linux)
netstat -ano | findstr :5000  # (Windows)

# Rebuild image
docker-compose build --no-cache
```

### Port Already in Use

```bash
# Option 1: Use different port in docker-compose.yml
ports:
  - "8080:5000"

# Option 2: Kill process using port 5000
# macOS/Linux:
kill -9 $(lsof -t -i:5000)

# Windows:
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

### Volume Permission Issues

```bash
# Fix log directory permissions
chmod 777 logs

# Or recreate with proper permissions
docker-compose down -v
mkdir -p logs
docker-compose up -d
```

### Container Exits Immediately

```bash
# Check detailed error logs
docker-compose logs --tail 100

# Run with interactive shell for debugging
docker-compose run --rm edge-fhir-hybrid bash

# Check Python imports
docker-compose exec edge-fhir-hybrid python -c "import flask; print(flask.__version__)"
```

### High Memory/CPU Usage

```bash
# Monitor resources
docker stats edge-fhir-hybrid

# Limit resources in docker-compose.yml
services:
  edge-fhir-hybrid:
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M
```

---

## Monitoring

### View Logs

```bash
# Real-time logs
docker-compose logs -f

# Last N lines
docker-compose logs --tail 100

# Since timestamp
docker-compose logs --since 2025-01-01T00:00:00

# Specific service
docker-compose logs edge-fhir-hybrid
```

### Health Checks

```bash
# Manual health check
curl http://localhost:5000/api/health

# Via docker
docker-compose exec edge-fhir-hybrid curl http://localhost:5000/api/health

# Check container health status
docker-compose ps
```

### Performance Metrics

```bash
# Real-time stats
docker stats edge-fhir-hybrid

# CPU and memory usage
docker-compose exec edge-fhir-hybrid ps aux

# Process tree
docker-compose exec edge-fhir-hybrid pstree
```

---

## Maintenance

### Update Image

```bash
# Pull latest code
git pull

# Rebuild image
docker-compose build --no-cache

# Restart container
docker-compose up -d
```

### Backup Logs

```bash
# Backup logs volume
docker run --rm -v edge_fhir_hybrid_logs:/logs -v $(pwd):/backup \
  alpine tar czf /backup/logs-$(date +%Y%m%d).tar.gz -C /logs .

# Or manually
cp -r logs logs-backup-$(date +%Y%m%d)
```

### Clean Up

```bash
# Remove stopped containers
docker container prune

# Remove unused images
docker image prune

# Remove unused volumes
docker volume prune

# Remove everything unused
docker system prune -a
```

---

## Summary

| Task | Command |
|------|---------|
| **Build** | `docker-compose build` |
| **Start** | `docker-compose up -d` |
| **Stop** | `docker-compose stop` |
| **Logs** | `docker-compose logs -f` |
| **Restart** | `docker-compose restart` |
| **Remove** | `docker-compose down` |
| **Shell** | `docker-compose exec edge-fhir-hybrid bash` |
| **Health** | `curl http://localhost:5000/api/health` |

---

## Next Steps

1. **Deploy**: Run `docker-compose up -d`
2. **Access Dashboard**: Open http://localhost:5000/
3. **Monitor**: Run `docker-compose logs -f`
4. **Scale**: Add more services to docker-compose.yml
5. **Secure**: Use reverse proxy for production

**Happy deploying!** 🐳
