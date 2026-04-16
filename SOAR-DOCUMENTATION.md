# SOAR Platform - Wazuh Integration

## 📋 Visão Geral

Ferramenta SOAR (Security Orchestration, Automation, and Response) completa que atua como uma camada de inteligência acima do Wazuh, automatizando a triagem, enriquecimento e remediação de alertas críticos e vulnerabilidades em ambientes Linux.

## 🎯 Objetivo

Desenvolver uma ferramenta que automatize completamente o ciclo de vida de resposta a incidentes:
- **Detecção** automática via Wazuh
- **Análise** com enriquecimento de contexto
- **Decisão** facilitada através de interface intuitiva
- **Remediação** automatizada
- **Verificação** e auditoria completa

## 🏗️ Arquitetura do Fluxo SOAR

### 1️⃣ Ingestão e Escuta (Event Listener)
**Objetivo:** Conexão com o Wazuh para captura de eventos críticos

**Funcionalidades:**
- Conexão via API REST do Wazuh (`https://wazuh-manager:55000/security/events`)
- Monitoramento do arquivo `alerts.json` em `/var/ossec/logs/alerts/alerts.json`
- Filtro inteligente de níveis críticos (5-12, 15+)
- Detecção via Vulnerability Detector e Threat Hunter

**Stack Técnica:** Python + Wazuh API / File Monitoring

### 2️⃣ Enriquecimento de Contexto (Auto-Threat Intel)
**Objetivo:** Validar gravidade antes de alertar o analista

**Integrações:**
- **VirusTotal API:** Análise de arquivos e URLs
- **AbuseIPDB:** Reputação de IPs
- **URLVoid:** Validação de domínios maliciosos

**Resultado:** Alertas chegam enriquecidos com contexto:
- "Este IP é um nó de saída Tor conhecido"
- "Este arquivo é um Ransomware confirmado por 50 antivírus"

**Stack Técnica:** Python `requests` + APIs de Threat Intelligence

### 3️⃣ Validação Controlada (Validation Step)
**Objetivo:** Confirmar explorabilidade de vulnerabilidades

**Métodos:**
- Scripts Nmap NSE para validação de serviços
- Integração com Metasploit (msfconsole) para testes controlados
- Verificação de portas e versões de serviços

**Stack Técnica:** python-nmap + Metasploit Framework

### 4️⃣ Painel de Decisão (The Gatekeeper)
**Objetivo:** Interface para o analista tomar decisão imediata

**3 Opções de Ação:**

**🔴 Opção A - Contenção (Isolamento)**
- Bloqueia o host da rede
- Executa via Wazuh Active Response
- Aplica regras iptables/nftables remotamente

**🟠 Opção B - Remediação (Patch/Update)**
- Atualiza pacotes vulneráveis via SSH
- Executa comandos `apt upgrade` ou `yum update` específicos
- Utiliza Ansible para automação em escala

**⚪ Opção C - Falso Positivo (Ignorar)**
- Adiciona às exceções
- Registra decisão do analista
- Evita alertas futuros do mesmo tipo

**Stack Técnica:** Flask/FastAPI (Backend) + React (Frontend)

### 5️⃣ Execução de Playbooks (Action)
**Objetivo:** Executar a ação escolhida pelo analista

**Comandos Executados:**

**Contenção:**
```bash
# Bloqueio via iptables
iptables -A INPUT -s <IP_ATACANTE> -j DROP
iptables -A OUTPUT -d <IP_ATACANTE> -j DROP

# Via Active Response Wazuh
/var/ossec/active-response/bin/firewall-drop.sh
```

**Remediação:**
```bash
# Atualização via SSH
ssh user@host
apt update && apt install <pacote>=<versao_segura>

# Via Ansible
ansible-playbook -i inventory patch_vulnerability.yml
```

**Stack Técnica:** Paramiko (SSH) + Ansible + Wazuh Active Response

### 6️⃣ Verificação e Fechamento (Double Check)
**Objetivo:** Validar que a ação resolveu o problema

**Processos:**
- Re-scan via Wazuh syscheck
- Verificação de status da vulnerabilidade (CVE resolvido?)
- Registro em banco de dados (SQLite/PostgreSQL)
- Auditoria completa: quem, quando, o que foi feito

**Stack Técnica:** SQLite/PostgreSQL + Wazuh API

## 🚀 Diferenciais da Ferramenta

### ✅ Solução Pronta
Diferente de um SIEM comum que **apenas avisa**, esta ferramenta **propõe a solução pronta**. O analista não precisa abrir o terminal do servidor afetado; ele gerencia a crise de dentro da interface.

### ⚡ MTTR Reduzido
Redução do **MTTR (Tempo Médio de Resposta) de horas para segundos** através da automação completa do fluxo.

### 🧠 Inteligência Automatizada
Enriquecimento automático com threat intelligence **antes** de alertar o analista, eliminando ruídos e falsos positivos.

### 📊 Auditoria Completa
Registro completo de todas as ações: quem autorizou, o que foi executado, e se o status mudou para "Resolved".

## 📦 Stack Tecnológica Completa

### Backend
- **Python 3.x** - Linguagem principal
- **Flask** ou **FastAPI** - API REST
- **Paramiko** - Automação SSH
- **python-nmap** - Validação de vulnerabilidades
- **requests** - Integração com APIs

### Integrações
- **Wazuh API** - SIEM principal
- **VirusTotal API** - Análise de malware
- **AbuseIPDB API** - Reputação de IPs
- **Metasploit** - Validação de exploits

### Automação
- **Ansible** - Orquestração de patches
- **Wazuh Active Response** - Resposta automática
- **iptables/nftables** - Firewall rules

### Banco de Dados
- **SQLite** (desenvolvimento)
- **PostgreSQL** (produção)

### Frontend
- **React** - Interface web
- **Tailwind CSS** - Estilização
- **React Router** - Navegação

## 🔧 Requisitos do Sistema

### Servidor SOAR (Esta Aplicação)
- Linux (Ubuntu 20.04+ ou CentOS 8+)
- Python 3.8+
- 4GB RAM mínimo
- Acesso à rede do Wazuh Manager

### Wazuh Manager
- Wazuh 4.x instalado e configurado
- API REST habilitada
- Agentes Linux conectados

### Ferramentas Opcionais
- Nmap 7.x
- Metasploit Framework
- Ansible 2.9+

## 🎨 Funcionalidades da Interface Web

### Dashboard Principal
- Visão geral de alertas críticos
- Estatísticas de vulnerabilidades
- Ações recentes do sistema
- Métricas em tempo real

### Gestão de Alertas
- Lista de alertas com filtros avançados
- Detalhes completos de cada alerta
- Enriquecimento de contexto em tempo real
- Painel de decisão com 3 opções

### Gestão de Vulnerabilidades
- Lista de CVEs detectados
- Detalhes técnicos (CVSS, exploitabilidade)
- Validação de vulnerabilidades
- Aplicação automática de patches

### Fluxo SOAR Visual
- Diagrama do fluxo completo
- Documentação de cada etapa
- Stack técnica utilizada

### Logs de Auditoria
- Histórico completo de ações
- Filtros por tipo de ação e alvo
- Exportação em CSV
- Rastreabilidade total

### Quarentena
- Itens isolados do sistema
- Opções de restauração ou exclusão
- Documentação de motivos

## 🔐 Segurança

- Todas as ações são registradas com timestamp e analista responsável
- Comunicação com Wazuh via HTTPS
- Credenciais armazenadas de forma segura
- Validação de permissões antes de executar ações críticas

## 📈 Métricas de Sucesso

- **MTTR (Mean Time To Response):** De horas para segundos
- **Taxa de Falsos Positivos:** Redução através de enriquecimento automático
- **Cobertura de Resposta:** 100% dos alertas críticos tratados
- **Auditoria:** 100% das ações registradas

## 🔄 Fluxo Completo de Tratamento

```
┌─────────────────────────────────────────────────────────────┐
│ 1. DETECÇÃO                                                 │
│    Wazuh detecta alerta/vulnerabilidade crítica             │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. ENRIQUECIMENTO                                           │
│    Consulta VirusTotal, AbuseIPDB, URLVoid                  │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. VALIDAÇÃO (Opcional para vulnerabilidades)              │
│    Testa explorabilidade via Nmap/Metasploit               │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. DECISÃO DO ANALISTA                                      │
│    [A] Contenção | [B] Remediação | [C] Ignorar            │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. EXECUÇÃO                                                 │
│    SSH/Ansible executa playbook escolhido                   │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. VERIFICAÇÃO                                              │
│    Re-scan + Log de auditoria + Status atualizado          │
└─────────────────────────────────────────────────────────────┘
```

## 🎓 Casos de Uso

### Caso 1: Brute Force SSH Detectado
1. **Detecção:** Wazuh alerta sobre múltiplas tentativas de login falhas
2. **Enriquecimento:** AbuseIPDB confirma que o IP é malicioso (score 100/100)
3. **Decisão:** Analista escolhe "Contenção"
4. **Execução:** IP bloqueado via iptables remotamente
5. **Verificação:** Logs confirmam bloqueio bem-sucedido

### Caso 2: Vulnerabilidade Crítica CVE-2024-3094 (XZ Utils)
1. **Detecção:** Wazuh Vulnerability Detector encontra xz-utils 5.2.5
2. **Validação:** Nmap confirma que o serviço está exposto e vulnerável
3. **Decisão:** Analista escolhe "Remediação"
4. **Execução:** `apt install xz-utils=5.4.5` via SSH
5. **Verificação:** Re-scan confirma CVE resolvido

### Caso 3: Malware Ransomware Detectado
1. **Detecção:** Wazuh detecta arquivo suspeito em /tmp/
2. **Enriquecimento:** VirusTotal: 48/70 antivírus confirmam Trojan
3. **Decisão:** Analista escolhe "Contenção" + Quarentena
4. **Execução:** Arquivo movido para quarentena, processo terminado, host isolado
5. **Verificação:** Quarentena registrada, logs salvos

## 📝 Roadmap Futuro

- [ ] Integração com MISP (Malware Information Sharing Platform)
- [ ] Machine Learning para predição de ataques
- [ ] Dashboards customizáveis por equipe
- [ ] Integração com Slack/Teams para notificações
- [ ] API pública para integrações externas
- [ ] Suporte a Windows Agents
- [ ] Playbooks customizáveis via interface

## 🤝 Contribuindo

Esta é uma ferramenta open-source para a comunidade de segurança. Contribuições são bem-vindas!

## 📄 Licença

MIT License - Livre para uso em ambientes corporativos e pessoais.

---

**Desenvolvido para reduzir o tempo de resposta a incidentes de segurança de horas para segundos.** ⚡🔐
