#!/bin/bash
# deploy_to_existing_droplet.sh
# Script para instalar GTM Scanner en droplet existente de DigitalOcean

echo "🚀 INSTALANDO GTM SCANNER EN DROPLET EXISTENTE"
echo "=============================================="
echo "IP Droplet: 159.223.149.3"
echo "Proyecto: Reachflow"
echo ""

# Variables
DROPLET_IP="159.223.149.3"
GTM_PORT="8080"  # Puerto diferente para no conflictar
REPO_URL="https://github.com/Ckaox/gtm-scaner.git"

echo "📋 PASO A PASO:"
echo ""

echo "1️⃣ CONECTAR AL DROPLET"
echo "----------------------"
echo "ssh root@$DROPLET_IP"
echo ""

echo "2️⃣ ACTUALIZAR SISTEMA"
echo "---------------------"
cat << 'EOF'
# Actualizar paquetes
sudo apt update && sudo apt upgrade -y

# Instalar dependencias básicas
sudo apt install -y git curl wget htop nano
EOF
echo ""

echo "3️⃣ INSTALAR DOCKER (si no está instalado)"
echo "------------------------------------------"
cat << 'EOF'
# Verificar si Docker está instalado
docker --version

# Si no está instalado, instalar Docker
sudo apt install -y docker.io docker-compose
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER

# Verificar instalación
sudo docker run hello-world
EOF
echo ""

echo "4️⃣ CLONAR GTM SCANNER"
echo "--------------------"
cat << 'EOF'
# Ir al directorio de aplicaciones
cd /opt
sudo mkdir -p /opt/apps
cd /opt/apps

# Clonar el repositorio
sudo git clone https://github.com/Ckaox/gtm-scaner.git
cd gtm-scaner

# Dar permisos
sudo chown -R $USER:$USER /opt/apps/gtm-scaner
EOF
echo ""

echo "5️⃣ CONSTRUIR Y EJECUTAR"
echo "----------------------"
cat << 'EOF'
cd /opt/apps/gtm-scaner

# Construir imagen Docker
sudo docker build -t gtm-scanner .

# Ejecutar en puerto 8080 (para no conflictar con otros servicios)
sudo docker run -d \
  --name gtm-scanner \
  -p 8080:8000 \
  --restart unless-stopped \
  -e PORT=8000 \
  gtm-scanner

# Verificar que está funcionando
sudo docker ps
curl http://localhost:8080/docs
EOF
echo ""

echo "6️⃣ CONFIGURAR FIREWALL"
echo "----------------------"
cat << 'EOF'
# Permitir puerto 8080
sudo ufw allow 8080

# Verificar reglas
sudo ufw status
EOF
echo ""

echo "7️⃣ CONFIGURAR NGINX (OPCIONAL - Para dominio personalizado)"
echo "-----------------------------------------------------------"
cat << 'EOF'
# Instalar Nginx si no está instalado
sudo apt install -y nginx

# Crear configuración para GTM Scanner
sudo nano /etc/nginx/sites-available/gtm-scanner

# Contenido del archivo:
server {
    listen 80;
    server_name gtm.tudominio.com;  # Cambiar por tu dominio

    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Habilitar sitio
sudo ln -s /etc/nginx/sites-available/gtm-scanner /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
EOF
echo ""

echo "8️⃣ VERIFICAR FUNCIONAMIENTO"
echo "---------------------------"
echo "# Directamente por IP:"
echo "curl http://$DROPLET_IP:8080/docs"
echo ""
echo "# En navegador:"
echo "http://$DROPLET_IP:8080/docs"
echo ""

echo "9️⃣ ACTUALIZACIONES FUTURAS"
echo "--------------------------"
cat << 'EOF'
# Script para actualizar GTM Scanner
cd /opt/apps/gtm-scaner
sudo git pull origin main
sudo docker stop gtm-scanner
sudo docker rm gtm-scanner
sudo docker build -t gtm-scanner .
sudo docker run -d \
  --name gtm-scanner \
  -p 8080:8000 \
  --restart unless-stopped \
  -e PORT=8000 \
  gtm-scanner
EOF
echo ""

echo "✅ DESPUÉS DEL DEPLOY:"
echo "====================="
echo "🌐 API Docs: http://$DROPLET_IP:8080/docs"
echo "🔗 Test endpoint: POST http://$DROPLET_IP:8080/scan"
echo "📱 Ejemplo de uso:"
echo 'curl -X POST "http://'$DROPLET_IP':8080/scan" \'
echo '     -H "Content-Type: application/json" \'
echo '     -d '"'"'{"domain": "ejemplo.com"}'"'"
echo ""
echo "💡 TIPS:"
echo "- El GTM Scanner correrá en puerto 8080"
echo "- No interferirá con otros servicios en puerto 80/443"
echo "- Se reiniciará automáticamente si el droplet se reinicia"
echo "- Para SSL, configura Nginx + Certbot después"