# 🚀 Guia de Instalação - SOAR Platform

## Pré-requisitos

### Sistema Operacional
- **Linux:** Ubuntu 20.04+, CentOS 8+, Debian 11+
- **Recursos:** 4GB RAM mínimo, 20GB disco
- **Python:** 3.8 ou superior
- **Node.js:** 18.x ou superior (para o frontend)

### Wazuh Manager
- Wazuh 4.x instalado e funcionando
- API REST habilitada (porta 55000)
- Pelo menos 1 agente Linux conectado

## 📦 Instalação do Backend (Python)

### 1. Clonar o repositório
```bash
git clone https://github.com/seu-repo/soar-wazuh.git
cd soar-wazuh
```

### 2. Criar ambiente virtual Python
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

### 3. Instalar dependências Python
```bash
pip install -r requirements.txt
```

### 4. Configurar variáveis de ambiente
```bash
cp .env.example .env
nano .env
```

Edite o arquivo `.env`:
```env
# Wazuh Configuration
WAZUH_MANAGER_URL=https://wazuh-manager:55000
WAZUH_API_USER=wazuh-api-user
WAZUH_API_PASSWORD=sua-senha-segura

# Threat Intelligence APIs
VIRUSTOTAL_API_KEY=sua-chave-virustotal
ABUSEIPDB_API_KEY=sua-chave-abuseipdb

# Database
DATABASE_URL=sqlite:///soar.db
# Para PostgreSQL:
# DATABASE_URL=postgresql://user:password@localhost/soar

# SSH Configuration
SSH_PRIVATE_KEY_PATH=/home/user/.ssh/id_rsa
DEFAULT_SSH_USER=root

# Application
SECRET_KEY=gere-uma-chave-secreta-aleatoria
DEBUG=False
```

### 5. Inicializar banco de dados
```bash
python backend/init_db.py
```

### 6. Iniciar o backend
```bash
# Modo desenvolvimento
python backend/app.py

# Modo produção (com Gunicorn)
gunicorn -w 4 -b 0.0.0.0:5000 backend.app:app
```

## 🎨 Instalação do Frontend (React)

### 1. Instalar dependências
```bash
cd frontend
npm install
# ou
pnpm install
```

### 2. Configurar endpoint da API
```bash
cp .env.example .env.local
nano .env.local
```

Edite o arquivo `.env.local`:
```env
VITE_API_URL=http://localhost:5000/api
```

### 3. Iniciar o frontend
```bash
# Modo desenvolvimento
npm run dev

# Build para produção
npm run build
```

## 🔧 Configuração do Wazuh

### 1. Habilitar API REST
Edite `/var/ossec/etc/ossec.conf`:
```xml
<ossec_config>
  <api>
    <enabled>yes</enabled>
    <host>0.0.0.0</host>
    <port>55000</port>
  </api>
</ossec_config>
```

Reinicie o Wazuh Manager:
```bash
systemctl restart wazuh-manager
```

### 2. Criar usuário da API
```bash
/var/ossec/bin/manage_users
```

### 3. Configurar Active Response
Edite `/var/ossec/etc/ossec.conf`:
```xml
<active-response>
  <command>firewall-drop</command>
  <location>local</location>
  <rules_id>100002,100003</rules_id>
  <timeout>600</timeout>
</active-response>
```

## 🛠️ Ferramentas Opcionais

### Nmap (para validação de vulnerabilidades)
```bash
# Ubuntu/Debian
sudo apt install nmap

# CentOS/RHEL
sudo yum install nmap
```

### Ansible (para automação em escala)
```bash
pip install ansible
```

### Metasploit (para validação avançada)
```bash
curl https://raw.githubusercontent.com/rapid7/metasploit-omnibus/master/config/templates/metasploit-framework-wrappers/msfupdate.erb > msfinstall
chmod 755 msfinstall
./msfinstall
```

## 🔐 Segurança

### 1. Configurar HTTPS (Nginx)
```bash
sudo apt install nginx certbot python3-certbot-nginx

# Obter certificado SSL
sudo certbot --nginx -d soar.seu-dominio.com
```

Configuração Nginx (`/etc/nginx/sites-available/soar`):
```nginx
server {
    listen 80;
    server_name soar.seu-dominio.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name soar.seu-dominio.com;

    ssl_certificate /etc/letsencrypt/live/soar.seu-dominio.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/soar.seu-dominio.com/privkey.pem;

    # Frontend
    location / {
        root /var/www/soar/frontend/dist;
        try_files $uri /index.html;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 2. Configurar Firewall
```bash
# Permitir apenas portas necessárias
sudo ufw allow 22/tcp  # SSH
sudo ufw allow 443/tcp # HTTPS
sudo ufw enable
```

### 3. Criar usuário dedicado
```bash
sudo useradd -m -s /bin/bash soar
sudo chown -R soar:soar /opt/soar
```

## 🧪 Testar a Instalação

### 1. Verificar conectividade com Wazuh
```bash
python backend/test_wazuh_connection.py
```

### 2. Testar APIs de Threat Intel
```bash
python backend/test_threat_intel.py
```

### 3. Acessar a interface web
```
https://soar.seu-dominio.com
```

Login padrão:
- **Usuário:** admin@security.local
- **Senha:** (definida durante a instalação)

## 📊 Monitoramento

### Logs da aplicação
```bash
# Backend
tail -f backend/logs/soar.log

# Nginx
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

### Status dos serviços
```bash
systemctl status wazuh-manager
systemctl status nginx
systemctl status soar-backend  # Se configurado como systemd service
```

## 🔄 Atualização

```bash
# Parar serviços
systemctl stop soar-backend

# Atualizar código
git pull origin main

# Atualizar dependências
source venv/bin/activate
pip install -r requirements.txt --upgrade

cd frontend
npm install

# Rebuild frontend
npm run build

# Reiniciar serviços
systemctl start soar-backend
systemctl reload nginx
```

## ⚠️ Troubleshooting

### Erro: "Conexão recusada ao Wazuh Manager"
```bash
# Verificar se a API está rodando
curl -k https://localhost:55000

# Verificar firewall
sudo ufw status
```

### Erro: "API Key inválida para VirusTotal"
- Verifique se a chave está correta no arquivo `.env`
- Confirme que a chave está ativa em https://www.virustotal.com/gui/my-apikey

### Erro: "Permissão negada ao executar SSH"
```bash
# Verificar permissões da chave SSH
chmod 600 ~/.ssh/id_rsa

# Testar conexão SSH manualmente
ssh -i ~/.ssh/id_rsa user@host
```

## 📞 Suporte

- **Documentação completa:** [SOAR-DOCUMENTATION.md](./SOAR-DOCUMENTATION.md)
- **Issues:** https://github.com/seu-repo/soar-wazuh/issues
- **Email:** security-team@sua-empresa.com

---

**Instalação completa! Sua plataforma SOAR está pronta para reduzir o MTTR de horas para segundos.** ⚡🔐
