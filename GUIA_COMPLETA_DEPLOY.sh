#!/bin/bash
# 🚀 GUÍA COMPLETA - GTM Scanner con Auto-Deploy desde GitHub
# ===========================================================
# ⚠️  IMPORTANTE: Esta guía NO afecta servicios existentes
# ✅  Todo se instala en directorios separados y puertos diferentes

echo "🎯 OBJETIVO: Instalar GTM Scanner con auto-deploy desde GitHub"
echo "📊 DROPLET: 159.223.149.3 (2GB RAM, 60GB Disk, Ubuntu 22.04)"
echo "🔒 SEGURIDAD: Sin tocar servicios existentes"
echo ""

# =============================================================================
# PASO 1: CONEXIÓN INICIAL Y VERIFICACIÓN
# =============================================================================

echo "🔗 PASO 1: CONECTAR AL DROPLET"
echo "=============================="
echo ""
echo "1.1 Abrir terminal en tu computadora local y conectar:"
echo "ssh root@159.223.149.3"
echo ""
echo "1.2 Una vez conectado, verificar qué está corriendo actualmente:"
echo "# Ver servicios activos"
echo "sudo systemctl list-units --type=service --state=active"
echo ""
echo "# Ver puertos en uso"
echo "sudo netstat -tulpn | grep LISTEN"
echo ""
echo "# Ver contenedores Docker (si los hay)"
echo "sudo docker ps 2>/dev/null || echo 'Docker no instalado'"
echo ""
echo "# Ver uso de recursos"
echo "free -h"
echo "df -h"
echo ""
echo "📝 ANOTA QUÉ VES para asegurar que no toquemos nada existente"
echo ""

# =============================================================================
# PASO 2: PREPARAR AMBIENTE AISLADO
# =============================================================================

echo "🏗️  PASO 2: PREPARAR AMBIENTE AISLADO"
echo "====================================="
echo ""
echo "2.1 Crear directorio para GTM Scanner (separado de todo lo demás):"
cat << 'EOF'
# Crear estructura de directorios
sudo mkdir -p /opt/gtm-scanner
cd /opt/gtm-scanner

# Crear usuario específico para GTM Scanner (opcional pero recomendado)
sudo useradd -r -s /bin/bash -d /opt/gtm-scanner gtm-user
sudo chown -R gtm-user:gtm-user /opt/gtm-scanner
EOF
echo ""

echo "2.2 Instalar Docker (si no está instalado):"
cat << 'EOF'
# Verificar si Docker está instalado
docker --version

# Si no está instalado, instalarlo
if ! command -v docker &> /dev/null; then
    echo "Instalando Docker..."
    sudo apt update
    sudo apt install -y apt-transport-https ca-certificates curl gnupg lsb-release
    
    # Agregar clave GPG de Docker
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    
    # Agregar repositorio
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Instalar Docker
    sudo apt update
    sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose
    
    # Iniciar y habilitar Docker
    sudo systemctl start docker
    sudo systemctl enable docker
    
    # Agregar usuario actual al grupo docker
    sudo usermod -aG docker $USER
    
    echo "✅ Docker instalado correctamente"
else
    echo "✅ Docker ya está instalado"
fi
EOF
echo ""

echo "2.3 Instalar Git (si no está instalado):"
cat << 'EOF'
# Verificar Git
git --version || sudo apt install -y git

# Configurar Git (usar tus datos)
git config --global user.name "Tu Nombre"
git config --global user.email "tu@email.com"
EOF
echo ""

# =============================================================================
# PASO 3: CONFIGURAR AUTO-DEPLOY DESDE GITHUB
# =============================================================================

echo "🔄 PASO 3: CONFIGURAR AUTO-DEPLOY DESDE GITHUB"
echo "=============================================="
echo ""
echo "3.1 Generar SSH Key para GitHub:"
cat << 'EOF'
cd /opt/gtm-scanner

# Generar nueva SSH key
ssh-keygen -t ed25519 -C "gtm-scanner@159.223.149.3" -f ./gtm_deploy_key -N ""

# Mostrar la clave pública (la necesitarás para GitHub)
echo "📋 COPIA ESTA CLAVE PÚBLICA para agregar a GitHub:"
echo "=================================================="
cat ./gtm_deploy_key.pub
echo "=================================================="
echo ""
echo "🔗 Ve a: https://github.com/Ckaox/gtm-scaner/settings/keys"
echo "📌 Click 'Add deploy key'"
echo "📝 Title: 'DigitalOcean Auto-Deploy'"
echo "🔐 Key: pega la clave que copiaste arriba"
echo "✅ Allow write access: NO (solo lectura)"
echo "💾 Add key"
EOF
echo ""

echo "3.2 Configurar SSH para GitHub:"
cat << 'EOF'
# Configurar SSH para usar la clave específica
mkdir -p ~/.ssh
cat >> ~/.ssh/config << EOL
Host github.com
    HostName github.com
    User git
    IdentityFile /opt/gtm-scanner/gtm_deploy_key
    StrictHostKeyChecking no
EOL

# Ajustar permisos
chmod 600 /opt/gtm-scanner/gtm_deploy_key
chmod 644 /opt/gtm-scanner/gtm_deploy_key.pub
chmod 600 ~/.ssh/config

# Probar conexión a GitHub
ssh -T git@github.com
EOF
echo ""

echo "3.3 Crear script de auto-deploy:"
cat << 'EOF'
# Crear script que se ejecutará cuando GitHub notifique cambios
cat > /opt/gtm-scanner/auto-deploy.sh << 'DEPLOY_SCRIPT'
#!/bin/bash
# Auto-deploy script para GTM Scanner

LOG_FILE="/opt/gtm-scanner/deploy.log"
REPO_DIR="/opt/gtm-scanner/gtm-scaner"

echo "$(date): Iniciando auto-deploy..." >> $LOG_FILE

cd $REPO_DIR

# Pull latest changes
git pull origin main >> $LOG_FILE 2>&1

# Rebuild and restart container
docker stop gtm-scanner >> $LOG_FILE 2>&1
docker rm gtm-scanner >> $LOG_FILE 2>&1
docker build -t gtm-scanner . >> $LOG_FILE 2>&1
docker run -d \
  --name gtm-scanner \
  -p 8080:8000 \
  --restart unless-stopped \
  gtm-scanner >> $LOG_FILE 2>&1

echo "$(date): Auto-deploy completado" >> $LOG_FILE
echo "-----------------------------------" >> $LOG_FILE
DEPLOY_SCRIPT

# Hacer ejecutable
chmod +x /opt/gtm-scanner/auto-deploy.sh
EOF
echo ""

# =============================================================================
# PASO 4: DEPLOY INICIAL
# =============================================================================

echo "🚀 PASO 4: DEPLOY INICIAL"
echo "========================="
echo ""
echo "4.1 Clonar repositorio:"
cat << 'EOF'
cd /opt/gtm-scanner

# Clonar usando SSH
git clone git@github.com:Ckaox/gtm-scaner.git

# Verificar que se clonó correctamente
cd gtm-scaner
ls -la
EOF
echo ""

echo "4.2 Construir y ejecutar GTM Scanner:"
cat << 'EOF'
cd /opt/gtm-scanner/gtm-scaner

# Construir imagen Docker
docker build -t gtm-scanner .

# Verificar que la imagen se creó
docker images | grep gtm-scanner

# Ejecutar contenedor en puerto 8080 (sin conflictos)
docker run -d \
  --name gtm-scanner \
  -p 8080:8000 \
  --restart unless-stopped \
  -e PYTHONPATH=/app \
  gtm-scanner

# Verificar que está corriendo
docker ps | grep gtm-scanner
EOF
echo ""

echo "4.3 Configurar firewall para permitir puerto 8080:"
cat << 'EOF'
# Permitir puerto 8080
sudo ufw allow 8080

# Verificar reglas del firewall
sudo ufw status
EOF
echo ""

# =============================================================================
# PASO 5: CONFIGURAR WEBHOOK DE GITHUB
# =============================================================================

echo "📡 PASO 5: CONFIGURAR WEBHOOK DE GITHUB"
echo "======================================="
echo ""
echo "5.1 Instalar webhook listener:"
cat << 'EOF'
# Instalar webhook listener simple
sudo apt install -y python3-pip
pip3 install flask

# Crear webhook receiver
cat > /opt/gtm-scanner/webhook-receiver.py << 'WEBHOOK_SCRIPT'
#!/usr/bin/env python3
from flask import Flask, request
import subprocess
import hmac
import hashlib
import os

app = Flask(__name__)

# Secret para validar webhooks (puedes cambiarlo)
WEBHOOK_SECRET = "gtm-scanner-secret-2025"

@app.route('/webhook', methods=['POST'])
def webhook():
    signature = request.headers.get('X-Hub-Signature-256')
    
    if signature:
        # Verificar signature de GitHub
        payload = request.get_data()
        expected_signature = 'sha256=' + hmac.new(
            WEBHOOK_SECRET.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        if hmac.compare_digest(signature, expected_signature):
            # Ejecutar auto-deploy
            subprocess.run(['/opt/gtm-scanner/auto-deploy.sh'])
            return 'Deploy triggered', 200
    
    return 'Unauthorized', 401

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9000)
WEBHOOK_SCRIPT

# Hacer ejecutable
chmod +x /opt/gtm-scanner/webhook-receiver.py
EOF
echo ""

echo "5.2 Crear servicio systemd para webhook:"
cat << 'EOF'
# Crear servicio systemd
sudo cat > /etc/systemd/system/gtm-webhook.service << 'SERVICE'
[Unit]
Description=GTM Scanner Webhook Receiver
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/gtm-scanner
ExecStart=/usr/bin/python3 /opt/gtm-scanner/webhook-receiver.py
Restart=always

[Install]
WantedBy=multi-user.target
SERVICE

# Habilitar y iniciar servicio
sudo systemctl daemon-reload
sudo systemctl enable gtm-webhook
sudo systemctl start gtm-webhook

# Verificar que está corriendo
sudo systemctl status gtm-webhook
EOF
echo ""

echo "5.3 Permitir puerto del webhook:"
cat << 'EOF'
# Permitir puerto 9000 para webhooks
sudo ufw allow 9000
EOF
echo ""

# =============================================================================
# PASO 6: CONFIGURAR WEBHOOK EN GITHUB
# =============================================================================

echo "🔗 PASO 6: CONFIGURAR WEBHOOK EN GITHUB"
echo "======================================="
echo ""
echo "📌 Ve a: https://github.com/Ckaox/gtm-scaner/settings/hooks"
echo "➕ Click 'Add webhook'"
echo ""
echo "📝 Configurar así:"
echo "   Payload URL: http://159.223.149.3:9000/webhook"
echo "   Content type: application/json"
echo "   Secret: gtm-scanner-secret-2025"
echo "   Which events: Just the push event"
echo "   Active: ✅"
echo ""
echo "💾 Add webhook"
echo ""

# =============================================================================
# PASO 7: VERIFICACIÓN FINAL
# =============================================================================

echo "✅ PASO 7: VERIFICACIÓN FINAL"
echo "=============================="
echo ""
echo "7.1 Verificar todos los servicios:"
cat << 'EOF'
# Verificar GTM Scanner
curl http://localhost:8080/docs

# Verificar webhook receiver
curl http://localhost:9000/webhook

# Ver logs
docker logs gtm-scanner
sudo systemctl status gtm-webhook

# Verificar puertos
sudo netstat -tulpn | grep -E ':(8080|9000)'
EOF
echo ""

echo "7.2 Test completo desde tu computadora:"
echo "curl http://159.223.149.3:8080/docs"
echo ""
echo "7.3 Test del scanner:"
echo 'curl -X POST "http://159.223.149.3:8080/scan" \'
echo '     -H "Content-Type: application/json" \'
echo '     -d '"'"'{"domain": "ejemplo.com"}'"'"
echo ""

# =============================================================================
# RESUMEN FINAL
# =============================================================================

echo ""
echo "🎉 RESUMEN FINAL"
echo "==============="
echo ""
echo "Después de seguir estos pasos tendrás:"
echo ""
echo "✅ GTM Scanner funcionando en: http://159.223.149.3:8080"
echo "✅ Auto-deploy configurado desde GitHub"
echo "✅ Webhook funcionando en puerto 9000"
echo "✅ Sin afectar servicios existentes"
echo ""
echo "🔄 FUNCIONAMIENTO AUTO-DEPLOY:"
echo "1. Haces push a GitHub"
echo "2. GitHub envía webhook a tu droplet"
echo "3. Se ejecuta auto-deploy automáticamente"
echo "4. GTM Scanner se actualiza sin intervención manual"
echo ""
echo "📂 ARCHIVOS CREADOS:"
echo "/opt/gtm-scanner/                 # Directorio principal"
echo "├── gtm-scaner/                   # Código del proyecto"
echo "├── auto-deploy.sh                # Script de auto-deploy"
echo "├── webhook-receiver.py           # Recibidor de webhooks"
echo "├── gtm_deploy_key                # SSH key para GitHub"
echo "└── deploy.log                    # Log de deployments"
echo ""
echo "🚨 IMPORTANTE: Los servicios existentes NO se tocan"
echo "🔒 SEGURIDAD: Todo está aislado en /opt/gtm-scanner"