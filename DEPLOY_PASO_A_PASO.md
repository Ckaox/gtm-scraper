# 🚀 GTM Scanner - Deploy Paso a Paso (Sin tocar nada existente)
# ===============================================================

## ⚠️ IMPORTANTE
- ✅ **NO afectará** servicios existentes en tu droplet
- ✅ **Puerto diferente** (8080) para evitar conflictos  
- ✅ **Directorio separado** (/opt/gtm-scanner)
- ✅ **Auto-deploy** desde GitHub configurado

---

## 📋 PASO 1: CONECTAR AL DROPLET

```bash
# Desde tu computadora local
ssh root@159.223.149.3
```

**Una vez conectado, verificar qué tienes actualmente:**
```bash
# Ver qué servicios están corriendo
sudo systemctl list-units --state=active | grep -E '(nginx|apache|docker)'

# Ver qué puertos están ocupados
sudo netstat -tulpn | grep LISTEN

# Ver uso de recursos actual
free -h && df -h
```

---

## 📂 PASO 2: CREAR DIRECTORIO AISLADO

```bash
# Crear directorio para GTM Scanner (separado de todo)
sudo mkdir -p /opt/gtm-scanner
cd /opt/gtm-scanner

# Verificar que estamos en el lugar correcto
pwd  # Debe mostrar: /opt/gtm-scanner
```

---

## 🐳 PASO 3: INSTALAR DOCKER (si no está)

```bash
# Verificar si Docker está instalado
docker --version

# Si NO está instalado, instalarlo:
sudo apt update
sudo apt install -y docker.io docker-compose
sudo systemctl start docker
sudo systemctl enable docker

# Verificar instalación
sudo docker run hello-world
```

---

## 🔑 PASO 4: CONFIGURAR ACCESO A GITHUB

```bash
cd /opt/gtm-scanner

# Generar SSH key para GitHub
ssh-keygen -t ed25519 -C "gtm-deploy@159.223.149.3" -f ./github_key -N ""

# Mostrar la clave pública
echo "=== COPIA ESTA CLAVE ==="
cat ./github_key.pub
echo "========================"
```

**📌 Ahora ve a GitHub:**
1. Abre: https://github.com/Ckaox/gtm-scaner/settings/keys
2. Click "Add deploy key"
3. Title: `DigitalOcean Deploy`
4. Key: pega la clave que copiaste
5. ✅ Add key

**Configurar SSH:**
```bash
# Configurar SSH para GitHub
mkdir -p ~/.ssh
cat >> ~/.ssh/config << EOF
Host github.com
    HostName github.com
    User git
    IdentityFile /opt/gtm-scanner/github_key
    StrictHostKeyChecking no
EOF

chmod 600 /opt/gtm-scanner/github_key
chmod 600 ~/.ssh/config

# Probar conexión
ssh -T git@github.com
```

---

## 📥 PASO 5: CLONAR Y DEPLOY INICIAL

```bash
cd /opt/gtm-scanner

# Clonar repositorio
git clone git@github.com:Ckaox/gtm-scaner.git
cd gtm-scaner

# Construir imagen Docker
sudo docker build -t gtm-scanner .

# Ejecutar en puerto 8080 (sin conflictos)
sudo docker run -d \
  --name gtm-scanner \
  -p 8080:8000 \
  --restart unless-stopped \
  gtm-scanner

# Verificar que funciona
sudo docker ps | grep gtm-scanner
```

---

## 🔥 PASO 6: CONFIGURAR FIREWALL

```bash
# Permitir puerto 8080
sudo ufw allow 8080

# Verificar reglas
sudo ufw status
```

---

## 🔄 PASO 7: CONFIGURAR AUTO-DEPLOY

```bash
cd /opt/gtm-scanner

# Crear script de auto-deploy
cat > auto-deploy.sh << 'EOF'
#!/bin/bash
echo "$(date): Iniciando auto-deploy..."
cd /opt/gtm-scanner/gtm-scaner
git pull origin main
sudo docker stop gtm-scanner
sudo docker rm gtm-scanner
sudo docker build -t gtm-scanner .
sudo docker run -d --name gtm-scanner -p 8080:8000 --restart unless-stopped gtm-scanner
echo "$(date): Deploy completado"
EOF

chmod +x auto-deploy.sh
```

**Crear webhook receiver:**
```bash
# Instalar Flask
sudo apt install -y python3-pip
pip3 install flask

# Crear webhook receiver
cat > webhook.py << 'EOF'
from flask import Flask, request
import subprocess
import os

app = Flask(__name__)

@app.route('/deploy', methods=['POST'])
def deploy():
    if request.json and request.json.get('ref') == 'refs/heads/main':
        subprocess.run(['/opt/gtm-scanner/auto-deploy.sh'])
        return 'Deploy triggered', 200
    return 'No deploy needed', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9000)
EOF

# Crear servicio para webhook
sudo cat > /etc/systemd/system/gtm-webhook.service << EOF
[Unit]
Description=GTM Webhook
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/gtm-scanner
ExecStart=/usr/bin/python3 webhook.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Iniciar servicio
sudo systemctl daemon-reload
sudo systemctl enable gtm-webhook
sudo systemctl start gtm-webhook

# Permitir puerto webhook
sudo ufw allow 9000
```

---

## 🔗 PASO 8: CONFIGURAR WEBHOOK EN GITHUB

**📌 Ve a:** https://github.com/Ckaox/gtm-scaner/settings/hooks

**➕ Add webhook con:**
- **Payload URL:** `http://159.223.149.3:9000/deploy`
- **Content type:** `application/json`
- **Which events:** `Just the push event`
- **Active:** ✅

---

## ✅ PASO 9: VERIFICAR TODO FUNCIONA

```bash
# Test local del GTM Scanner
curl http://localhost:8080/docs

# Test del webhook
curl http://localhost:9000/deploy

# Ver logs
sudo docker logs gtm-scanner
sudo systemctl status gtm-webhook
```

**Test desde tu computadora:**
```bash
# API Docs
curl http://159.223.149.3:8080/docs

# Test scanner
curl -X POST "http://159.223.149.3:8080/scan" \
     -H "Content-Type: application/json" \
     -d '{"domain": "ejemplo.com"}'
```

---

## 🎉 RESULTADO FINAL

Después de estos pasos tendrás:

✅ **GTM Scanner:** http://159.223.149.3:8080/docs  
✅ **Auto-deploy:** Push a GitHub → Deploy automático  
✅ **Sin conflictos:** Puerto 8080, directorio separado  
✅ **Servicios existentes:** Sin tocar, funcionando normal  

## 🔄 CÓMO FUNCIONA EL AUTO-DEPLOY

1. Haces `git push` a GitHub
2. GitHub envía webhook a tu droplet
3. Se ejecuta auto-deploy automáticamente
4. GTM Scanner se actualiza solo

## 🆘 SI ALGO SALE MAL

```bash
# Ver logs de Docker
sudo docker logs gtm-scanner

# Ver logs de webhook
sudo systemctl status gtm-webhook

# Reiniciar todo
cd /opt/gtm-scanner && ./auto-deploy.sh
```