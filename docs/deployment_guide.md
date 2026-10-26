# Production Deployment Guide

## Technical Document Terminology and Concept Relationship Mapper

This guide provides end-to-end instructions for deploying the **Technical Document Terminology and Concept Relationship Mapper** across multiple production environments:
1. [Docker & Docker Compose (Recommended)](#1-docker--docker-compose-deployment)
2. [Cloud PaaS (Render, Railway, Fly.io)](#2-cloud-paas-deployment)
3. [Linux VM / VPS (Ubuntu with Nginx + Gunicorn + Systemd)](#3-linux-vps-deployment-ubuntu-nginx--gunicorn)
4. [Windows Server / Local On-Premise](#4-windows-server--on-premise-deployment)
5. [Production Database Migration (PostgreSQL)](#5-migrating-from-sqlite-to-postgresql)

---

## 1. Docker & Docker Compose Deployment

The application features a multi-stage `Dockerfile` that builds the React Single Page Application (SPA) with Node.js and packages it directly into the Python 3.12 Flask runtime served via **Gunicorn WSGI**.

### Prerequisites
- Docker Engine 24+ & Docker Compose installed.

### Commands to Build and Run
```bash
# Clone or navigate to the repository
cd technical-document-mapper

# Build and start the container in detached mode
docker compose up -d --build

# View container logs
docker compose logs -f

# Stop the container
docker compose down
```

The web application will be accessible at:
👉 **`http://<SERVER_IP>:5000`**

Persistent storage for uploads and database is automatically preserved in Docker named volumes (`app_data`, `app_uploads`, `app_exports`).

---

## 2. Cloud PaaS Deployment

### Deploying to Render.com
1. Fork or push this repository to GitHub.
2. In Render dashboard, click **New +** $\to$ **Web Service**.
3. Select your repository.
4. Set the following configuration:
   - **Environment**: `Docker`
   - **Dockerfile Path**: `./Dockerfile`
   - **Instance Type**: Free or Starter (at least 1GB RAM recommended for spaCy/TF-IDF)
5. Add Environment Variables:
   - `PORT`: `5000`
   - `FLASK_ENV`: `production`
   - `SECRET_KEY`: `<Generate a random 32-character string>`
6. Click **Create Web Service**. Render builds the React frontend and starts Gunicorn automatically.

### Deploying to Railway.app
1. Go to Railway $\to$ **New Project** $\to$ **Deploy from GitHub repo**.
2. Railway detects the `Dockerfile` automatically.
3. Under **Variables**, add:
   - `PORT`: `5000`
   - `FLASK_ENV`: `production`
   - `SECRET_KEY`: `<Generate random string>`
4. In **Settings** $\to$ **Networking**, click **Generate Domain**.

---

## 3. Linux VPS Deployment (Ubuntu + Nginx + Gunicorn)

### Step 1: Install System Dependencies
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv nginx curl git
```

### Step 2: Install Node.js (for frontend build)
```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
```

### Step 3: Clone Code and Set Up Environment
```bash
cd /var/www
sudo git clone <YOUR_REPO_URL> technical-document-mapper
sudo chown -R $USER:$USER /var/www/technical-document-mapper
cd technical-document-mapper

# Create Python Virtual Environment
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
python -m spacy download en_core_web_sm || true

# Build React Frontend
cd frontend
npm install
npm run build
cd ..

# Initialize and Seed Database
python scripts/seed_demo_data.py
```

### Step 4: Create Systemd Service for Gunicorn
Create `/etc/systemd/system/techmapper.service`:
```ini
[Unit]
Description=Technical Document Mapper Gunicorn Application
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/technical-document-mapper
Environment="PATH=/var/www/technical-document-mapper/venv/bin"
Environment="PYTHONPATH=/var/www/technical-document-mapper"
Environment="PORT=5000"
Environment="FLASK_ENV=production"
ExecStart=/var/www/technical-document-mapper/venv/bin/gunicorn \
          --workers 4 \
          --bind 127.0.0.1:5000 \
          --timeout 120 \
          "backend.app:create_app()"

Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo chown -R www-data:www-data /var/www/technical-document-mapper
sudo systemctl daemon-reload
sudo systemctl enable techmapper
sudo systemctl start techmapper
sudo systemctl status techmapper
```

### Step 5: Configure Nginx Reverse Proxy
Create `/etc/nginx/sites-available/techmapper`:
```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    client_max_body_size 30M;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable site and restart Nginx:
```bash
sudo ln -s /etc/nginx/sites-available/techmapper /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Step 6: SSL Security with Let's Encrypt
```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

---

## 4. Windows Server / On-Premise Deployment

### Option A: As a Windows Service using NSSM
1. Download **NSSM** (Non-Sucking Service Manager).
2. Install service:
   ```cmd
   nssm install TechDocumentMapper "C:\Python312\python.exe" "C:\Users\HP\.gemini\antigravity\scratch\technical-document-mapper\run.py"
   nssm set TechDocumentMapper AppDirectory "C:\Users\HP\.gemini\antigravity\scratch\technical-document-mapper"
   nssm start TechDocumentMapper
   ```

### Option B: Batch Runner
Simply run:
```cmd
run.bat
```

---

## 5. Migrating from SQLite to PostgreSQL

The project is built on **SQLAlchemy 2.0 ORM** with database-agnostic models. To use PostgreSQL in production:

1. Install psycopg2:
   ```bash
   pip install psycopg2-binary
   ```
2. Set the `DATABASE_URL` environment variable:
   ```bash
   DATABASE_URL=postgresql://dbuser:securepassword@localhost:5432/tech_mapper
   ```
3. Restart the service. SQLAlchemy will automatically create all required tables, constraints, and foreign keys in PostgreSQL on first boot.
