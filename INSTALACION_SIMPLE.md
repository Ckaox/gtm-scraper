# 🚀 GTM Scanner - Instalación Súper Simple
# =========================================

## 📋 LO QUE VAMOS A HACER (sin tocar nada existente):

✅ **Instalar GTM Scanner** en puerto 8080 (separado de tus otros servicios)  
✅ **Auto-deploy** desde GitHub (push → actualización automática)  
✅ **Webhook** para recibir notificaciones de GitHub  
✅ **Zero downtime** para tus servicios actuales  

---

## 🎯 PASO A PASO SÚPER SIMPLE

### **PASO 1: Conectar a tu droplet**

Desde tu computadora local:
```bash
ssh root@159.223.149.3
```

### **PASO 2: Ejecutar el instalador automático**

Una vez conectado al droplet, ejecuta este **único comando**:

```bash
curl -sSL https://raw.githubusercontent.com/Ckaox/gtm-scaner/main/install_gtm_scanner.sh | bash
```

**¡Eso es todo!** El script se encarga de:
- ✅ Verificar que no toque servicios existentes
- ✅ Instalar Docker si no está
- ✅ Clonar tu repositorio
- ✅ Configurar auto-deploy
- ✅ Configurar webhook receiver
- ✅ Abrir puertos en firewall
- ✅ Ejecutar GTM Scanner

### **PASO 3: Configurar webhook en GitHub (2 minutos)**

El script te dará un link y la configuración exacta. Solo tienes que:

1. **Ir a:** https://github.com/Ckaox/gtm-scaner/settings/hooks
2. **Click:** "Add webhook"
3. **Pegar la URL** que te da el script
4. **Configurar:** Content type = application/json
5. **Seleccionar:** Just the push event
6. **Save**

---

## 🎉 RESULTADO FINAL

Después de 5-10 minutos tendrás:

📊 **GTM Scanner funcionando en:** `http://159.223.149.3:8080`  
📋 **API Docs en:** `http://159.223.149.3:8080/docs`  
🔄 **Auto-deploy:** Push a GitHub → Update automático  
🔒 **Servicios existentes:** Sin tocar, funcionando normal  

---

## 🧪 PROBAR TU API

```bash
# Test básico
curl http://159.223.149.3:8080/docs

# Test del scanner
curl -X POST "http://159.223.149.3:8080/scan" \
     -H "Content-Type: application/json" \
     -d '{"domain": "reachflow.org"}'
```

---

## 🔄 CÓMO FUNCIONA EL AUTO-DEPLOY

1. **Haces cambios** en tu código local
2. **Push a GitHub:** `git push origin main`
3. **GitHub envía webhook** a tu droplet
4. **Se ejecuta auto-deploy:** Descarga código nuevo, rebuild, restart
5. **Tu API se actualiza** automáticamente sin que tengas que hacer nada

---

## 🆘 SI ALGO SALE MAL

```bash
# Ver logs de GTM Scanner
docker logs gtm-scanner

# Ver logs de auto-deploy
cat /opt/gtm-scanner/deploy.log

# Ver logs de webhook
systemctl status gtm-webhook

# Reiniciar todo
cd /opt/gtm-scanner && ./auto-deploy.sh
```

---

## ⚠️ IMPORTANTE

- ✅ **Puerto 8080:** GTM Scanner (nuevo)
- ✅ **Puerto 9000:** Webhook receiver (nuevo)
- ✅ **Puerto 80/443:** Tus servicios existentes (sin tocar)
- ✅ **Directorio:** `/opt/gtm-scanner` (aislado)

**¡No hay riesgo de conflictos!** Todo está completamente separado.

---

## 💡 TIPS

**Para actualizar manualmente:**
```bash
ssh root@159.223.149.3
cd /opt/gtm-scanner && ./auto-deploy.sh
```

**Para ver el estado:**
```bash
docker ps | grep gtm-scanner
systemctl status gtm-webhook
```

**Para detener (si necesitas):**
```bash
docker stop gtm-scanner
systemctl stop gtm-webhook
```