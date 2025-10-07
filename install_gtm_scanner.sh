#!/bin/bash
# 🚀 GTM Scanner - Instalación Automática
# Ejecutar este script EN tu droplet: 159.223.149.3

set -e  # Salir si hay errores

echo "🚀 INSTALANDO GTM SCANNER EN DROPLET"
echo "===================================="
echo "📍 Droplet IP: $(curl -s ifconfig.me 2>/dev/null || echo 'IP no detectada')"
echo "📅 Fecha: $(date)"
echo ""

# Colores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Función para verificar si un comando existe
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Función para verificar puertos ocupados
check_port() {
    if netstat -tuln | grep -q ":$1 "; then
        return 0  # Puerto ocupado
    else
        return 1  # Puerto libre
    fi
}

echo "🔍 VERIFICACIÓN INICIAL"
echo "======================"

# Verificar que no estamos tocando nada existente
log_info "Verificando servicios existentes..."
echo "Servicios activos:"
systemctl list-units --state=active --type=service | grep -E "(nginx|apache|docker)" || echo "No se encontraron servicios web principales"

echo ""
log_info "Verificando puertos en uso..."
netstat -tuln | grep LISTEN | head -10

echo ""
log_info "Verificando recursos del sistema..."
echo "RAM disponible: $(free -h | awk 'NR==2{print $7}')"
echo "Espacio en disco: $(df -h | awk '$NF=="/"{print $4}')"

# Verificar puertos que vamos a usar
if check_port 8080; then
    log_error "Puerto 8080 ya está en uso. Usando puerto 8081 en su lugar."
    GTM_PORT=8081
else
    log_success "Puerto 8080 disponible"
    GTM_PORT=8080
fi

if check_port 9000; then
    log_error "Puerto 9000 ya está en uso. Usando puerto 9001 en su lugar."
    WEBHOOK_PORT=9001
else
    log_success "Puerto 9000 disponible para webhook"
    WEBHOOK_PORT=9000
fi

echo ""
echo "🏗️  PREPARANDO INSTALACIÓN"
echo "=========================="

# Crear directorio de trabajo
log_info "Creando directorio para GTM Scanner..."
mkdir -p /opt/gtm-scanner
cd /opt/gtm-scanner

log_success "Directorio de trabajo: /opt/gtm-scanner"

# Actualizar sistema
log_info "Actualizando paquetes del sistema..."
apt update -qq

# Instalar dependencias básicas
log_info "Instalando dependencias básicas..."
apt install -y git curl wget python3 python3-pip ufw

# Verificar/Instalar Docker
echo ""
echo "🐳 CONFIGURANDO DOCKER"
echo "====================="

if command_exists docker; then
    log_success "Docker ya está instalado"
    docker --version
else
    log_info "Instalando Docker..."
    apt install -y docker.io docker-compose
    systemctl start docker
    systemctl enable docker
    log_success "Docker instalado y configurado"
fi

# Verificar que Docker funciona
if docker run --rm hello-world > /dev/null 2>&1; then
    log_success "Docker funcionando correctamente"
else
    log_error "Problema con Docker, pero continuamos..."
fi

# Generar SSH key para GitHub
echo ""
echo "🔑 CONFIGURANDO ACCESO A GITHUB"
echo "==============================="

if [[ ! -f "./github_deploy_key" ]]; then
    log_info "Generando SSH key para GitHub..."
    ssh-keygen -t ed25519 -C "gtm-deploy@$(hostname)" -f ./github_deploy_key -N ""
    chmod 600 ./github_deploy_key
    chmod 644 ./github_deploy_key.pub
    log_success "SSH key generada"
else
    log_success "SSH key ya existe"
fi

# Mostrar clave pública
echo ""
echo "📋 CLAVE PÚBLICA PARA GITHUB"
echo "============================"
echo "🔗 Ve a: https://github.com/Ckaox/gtm-scaner/settings/keys"
echo "➕ Click 'Add deploy key'"
echo "📝 Title: 'DigitalOcean Auto Deploy'"
echo "🔐 Copia esta clave:"
echo ""
cat ./github_deploy_key.pub
echo ""
echo "✅ Allow write access: NO"
echo "💾 Add key"
echo ""
read -p "Presiona ENTER cuando hayas agregado la clave a GitHub..."

# Configurar SSH para GitHub
log_info "Configurando SSH para GitHub..."
mkdir -p ~/.ssh
cat > ~/.ssh/config << EOF
Host github.com
    HostName github.com
    User git
    IdentityFile /opt/gtm-scanner/github_deploy_key
    StrictHostKeyChecking no
EOF
chmod 600 ~/.ssh/config

# Probar conexión con GitHub
log_info "Probando conexión con GitHub..."
if ssh -T git@github.com 2>&1 | grep -q "successfully authenticated"; then
    log_success "Conexión con GitHub establecida"
else
    log_error "Problema con conexión GitHub, pero continuamos..."
fi

# Clonar repositorio
echo ""
echo "📥 CLONANDO GTM SCANNER"
echo "======================"

if [[ -d "./gtm-scaner" ]]; then
    log_info "Repositorio ya existe, actualizando..."
    cd gtm-scaner
    git pull origin main
    cd ..
else
    log_info "Clonando repositorio GTM Scanner..."
    git clone git@github.com:Ckaox/gtm-scaner.git
fi

if [[ -d "./gtm-scaner" ]]; then
    log_success "Repositorio clonado correctamente"
else
    log_error "Error clonando repositorio"
    exit 1
fi

# Construir imagen Docker
echo ""
echo "🔨 CONSTRUYENDO GTM SCANNER"
echo "==========================="

cd gtm-scaner
log_info "Construyendo imagen Docker..."
docker build -t gtm-scanner . || {
    log_error "Error construyendo imagen Docker"
    exit 1
}

log_success "Imagen Docker construida"

# Detener contenedor existente si existe
if docker ps -a | grep -q gtm-scanner; then
    log_info "Deteniendo contenedor existente..."
    docker stop gtm-scanner 2>/dev/null || true
    docker rm gtm-scanner 2>/dev/null || true
fi

# Ejecutar GTM Scanner
log_info "Ejecutando GTM Scanner en puerto $GTM_PORT..."
docker run -d \
    --name gtm-scanner \
    -p $GTM_PORT:8000 \
    --restart unless-stopped \
    -e PORT=8000 \
    gtm-scanner

if docker ps | grep -q gtm-scanner; then
    log_success "GTM Scanner ejecutándose correctamente"
else
    log_error "Error ejecutando GTM Scanner"
    exit 1
fi

# Configurar firewall
echo ""
echo "🔥 CONFIGURANDO FIREWALL"
echo "========================"

log_info "Configurando reglas de firewall..."
ufw allow $GTM_PORT
ufw allow $WEBHOOK_PORT
log_success "Firewall configurado"

# Crear script de auto-deploy
echo ""
echo "🔄 CONFIGURANDO AUTO-DEPLOY"
echo "==========================="

cd /opt/gtm-scanner
cat > auto-deploy.sh << 'EOF'
#!/bin/bash
echo "$(date): Iniciando auto-deploy..." >> /opt/gtm-scanner/deploy.log
cd /opt/gtm-scanner/gtm-scaner
git pull origin main >> /opt/gtm-scanner/deploy.log 2>&1
docker stop gtm-scanner >> /opt/gtm-scanner/deploy.log 2>&1
docker rm gtm-scanner >> /opt/gtm-scanner/deploy.log 2>&1
docker build -t gtm-scanner . >> /opt/gtm-scanner/deploy.log 2>&1
docker run -d \
    --name gtm-scanner \
    -p GTM_PORT_PLACEHOLDER:8000 \
    --restart unless-stopped \
    -e PORT=8000 \
    gtm-scanner >> /opt/gtm-scanner/deploy.log 2>&1
echo "$(date): Auto-deploy completado" >> /opt/gtm-scanner/deploy.log
EOF

# Reemplazar placeholder con puerto real
sed -i "s/GTM_PORT_PLACEHOLDER/$GTM_PORT/g" auto-deploy.sh
chmod +x auto-deploy.sh

log_success "Script de auto-deploy creado"

# Instalar Flask para webhook
log_info "Instalando Flask para webhook..."
pip3 install flask

# Crear webhook receiver
cat > webhook-receiver.py << EOF
#!/usr/bin/env python3
from flask import Flask, request
import subprocess
import os
import json

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        payload = request.get_json()
        if payload and payload.get('ref') == 'refs/heads/main':
            subprocess.run(['/opt/gtm-scanner/auto-deploy.sh'])
            return 'Deploy triggered', 200
        return 'No deploy needed', 200
    except Exception as e:
        return f'Error: {str(e)}', 500

@app.route('/status', methods=['GET'])
def status():
    return 'Webhook receiver is running', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=$WEBHOOK_PORT)
EOF

chmod +x webhook-receiver.py

# Crear servicio systemd para webhook
cat > /etc/systemd/system/gtm-webhook.service << EOF
[Unit]
Description=GTM Scanner Webhook Receiver
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/gtm-scanner
ExecStart=/usr/bin/python3 /opt/gtm-scanner/webhook-receiver.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Habilitar y iniciar servicio webhook
systemctl daemon-reload
systemctl enable gtm-webhook
systemctl start gtm-webhook

if systemctl is-active --quiet gtm-webhook; then
    log_success "Webhook receiver configurado y ejecutándose"
else
    log_error "Problema con webhook receiver"
fi

# Verificación final
echo ""
echo "✅ VERIFICACIÓN FINAL"
echo "===================="

# Test local
log_info "Probando GTM Scanner localmente..."
sleep 2
if curl -s "http://localhost:$GTM_PORT/docs" > /dev/null; then
    log_success "GTM Scanner responde correctamente"
else
    log_error "GTM Scanner no responde"
fi

# Test webhook
log_info "Probando webhook receiver..."
if curl -s "http://localhost:$WEBHOOK_PORT/status" > /dev/null; then
    log_success "Webhook receiver funcionando"
else
    log_error "Webhook receiver no responde"
fi

# Mostrar información final
echo ""
echo "🎉 INSTALACIÓN COMPLETADA"
echo "========================="
echo ""
echo "📊 GTM Scanner está funcionando en:"
echo "   🌐 http://$(curl -s ifconfig.me):$GTM_PORT"
echo "   📋 Docs: http://$(curl -s ifconfig.me):$GTM_PORT/docs"
echo ""
echo "🔗 Webhook receiver en:"
echo "   📡 http://$(curl -s ifconfig.me):$WEBHOOK_PORT/webhook"
echo ""
echo "📝 SIGUIENTE PASO: Configurar webhook en GitHub"
echo "   🔗 Ve a: https://github.com/Ckaox/gtm-scaner/settings/hooks"
echo "   ➕ Add webhook:"
echo "   📍 Payload URL: http://$(curl -s ifconfig.me):$WEBHOOK_PORT/webhook"
echo "   📊 Content type: application/json"
echo "   🎯 Which events: Just the push event"
echo ""
echo "🧪 PRUEBA TU API:"
echo 'curl -X POST "http://'$(curl -s ifconfig.me)':'"$GTM_PORT"'/scan" \'
echo '     -H "Content-Type: application/json" \'
echo '     -d '"'"'{"domain": "ejemplo.com"}'"'"
echo ""
echo "📂 Archivos de configuración en: /opt/gtm-scanner/"
echo "📜 Logs de deploy en: /opt/gtm-scanner/deploy.log"
echo ""
log_success "¡GTM Scanner está listo para usar!"