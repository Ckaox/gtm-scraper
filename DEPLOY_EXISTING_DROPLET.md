# GTM Scanner - Deploy en Droplet Existente
# ==========================================

## 🎯 Resumen
Tu droplet ya está funcionando, vamos a agregar el GTM Scanner sin afectar tus otros servicios.

## 📊 Configuración Propuesta

| Servicio | Puerto | URL |
|----------|--------|-----|
| Reachflow (actual) | 80/443 | http://159.223.149.3 |
| GTM Scanner (nuevo) | 8080 | http://159.223.149.3:8080 |

## 🚀 Proceso de Instalación

### 1. Conectar al Droplet
```bash
ssh root@159.223.149.3
```

### 2. Verificar Recursos Disponibles
```bash
# Ver recursos actuales
free -h
df -h
docker ps  # Ver contenedores actuales
```

### 3. Instalar GTM Scanner
```bash
# Clonar repositorio
cd /opt
git clone https://github.com/Ckaox/gtm-scaner.git
cd gtm-scaner

# Construir y ejecutar
docker build -t gtm-scanner .
docker run -d \
  --name gtm-scanner \
  -p 8080:8000 \
  --restart unless-stopped \
  gtm-scanner
```

### 4. Verificar Funcionamiento
```bash
# Verificar que está corriendo
docker ps | grep gtm-scanner

# Test local
curl http://localhost:8080/docs

# Test externo (desde tu computadora)
curl http://159.223.149.3:8080/docs
```

## 🔧 Configuración Avanzada (Opcional)

### Nginx Reverse Proxy
Si quieres un subdominio como `gtm.tudominio.com`:

```nginx
server {
    listen 80;
    server_name gtm.reachflow.org;
    
    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### SSL con Certbot
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d gtm.reachflow.org
```

## 📱 URLs Resultantes

**Después del deploy tendrás:**
- 📋 **API Docs:** http://159.223.149.3:8080/docs
- 🔍 **Scanner:** POST http://159.223.149.3:8080/scan
- 📊 **Health:** http://159.223.149.3:8080/health (si existe)

## 🧪 Test de la API

```bash
# Test básico
curl -X POST "http://159.223.149.3:8080/scan" \
     -H "Content-Type: application/json" \
     -d '{"domain": "reachflow.org"}'
```

## 💾 Monitoreo de Recursos

Con 2GB RAM en tu droplet:
- **Reachflow:** ~500MB
- **GTM Scanner:** ~300-500MB  
- **Sistema:** ~200MB
- **Disponible:** ~800MB ✅

## 🔄 Actualizaciones

Para actualizar el GTM Scanner:
```bash
cd /opt/gtm-scaner
git pull origin main
docker stop gtm-scanner
docker rm gtm-scanner
docker build -t gtm-scanner .
docker run -d --name gtm-scanner -p 8080:8000 --restart unless-stopped gtm-scanner
```

## 🚨 Troubleshooting

**Si hay problemas de puerto:**
```bash
# Ver qué usa el puerto 8080
sudo netstat -tulpn | grep :8080
# Cambiar a otro puerto si es necesario
```

**Si hay problemas de memoria:**
```bash
# Monitorear recursos
htop
docker stats
```