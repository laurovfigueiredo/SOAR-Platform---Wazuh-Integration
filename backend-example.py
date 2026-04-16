"""
SOAR Platform - Backend Example
Exemplo de implementação do backend em Python usando Flask

Este é um exemplo de referência para implementar o backend real da plataforma SOAR.
A interface web React já está completa e funcional.
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import paramiko
import json
import os
from datetime import datetime
from typing import Dict, List, Optional

app = Flask(__name__)
CORS(app)

# =============================================================================
# CONFIGURAÇÕES
# =============================================================================

WAZUH_MANAGER_URL = os.getenv('WAZUH_MANAGER_URL', 'https://localhost:55000')
WAZUH_API_USER = os.getenv('WAZUH_API_USER', 'wazuh-api')
WAZUH_API_PASSWORD = os.getenv('WAZUH_API_PASSWORD', 'wazuh')

VIRUSTOTAL_API_KEY = os.getenv('VIRUSTOTAL_API_KEY', '')
ABUSEIPDB_API_KEY = os.getenv('ABUSEIPDB_API_KEY', '')

# =============================================================================
# 1. INGESTÃO E ESCUTA (Event Listener)
# =============================================================================

class WazuhConnector:
    """Conexão com o Wazuh Manager via API"""
    
    def __init__(self, url: str, user: str, password: str):
        self.url = url
        self.user = user
        self.password = password
        self.token = None
    
    def authenticate(self) -> str:
        """Autenticar na API do Wazuh"""
        auth_url = f"{self.url}/security/user/authenticate"
        response = requests.post(
            auth_url,
            auth=(self.user, self.password),
            verify=False
        )
        self.token = response.json()['data']['token']
        return self.token
    
    def get_alerts(self, level_min: int = 5) -> List[Dict]:
        """Obter alertas do Wazuh filtrados por nível"""
        if not self.token:
            self.authenticate()
        
        headers = {'Authorization': f'Bearer {self.token}'}
        alerts_url = f"{self.url}/security/events"
        params = {'level': f'>={level_min}', 'limit': 100}
        
        response = requests.get(
            alerts_url,
            headers=headers,
            params=params,
            verify=False
        )
        return response.json()['data']['items']
    
    def get_vulnerabilities(self, agent_id: str) -> List[Dict]:
        """Obter vulnerabilidades de um agente"""
        if not self.token:
            self.authenticate()
        
        headers = {'Authorization': f'Bearer {self.token}'}
        vuln_url = f"{self.url}/vulnerability/{agent_id}"
        
        response = requests.get(vuln_url, headers=headers, verify=False)
        return response.json()['data']['items']

# =============================================================================
# 2. ENRIQUECIMENTO DE CONTEXTO (Auto-Threat Intel)
# =============================================================================

class ThreatIntelligence:
    """Integração com serviços de Threat Intelligence"""
    
    @staticmethod
    def check_virustotal(file_hash: str) -> Dict:
        """Consultar VirusTotal sobre um hash de arquivo"""
        url = f"https://www.virustotal.com/api/v3/files/{file_hash}"
        headers = {'x-apikey': VIRUSTOTAL_API_KEY}
        
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()['data']['attributes']
            stats = data['last_analysis_stats']
            
            return {
                'source': 'VirusTotal',
                'reputation': 'malicious' if stats['malicious'] > 5 else 'clean',
                'score': stats['malicious'],
                'details': f"Detected by {stats['malicious']}/70 antivirus engines",
                'lastAnalysis': data['last_analysis_date']
            }
        return None
    
    @staticmethod
    def check_abuseipdb(ip: str) -> Dict:
        """Consultar AbuseIPDB sobre reputação de IP"""
        url = 'https://api.abuseipdb.com/api/v2/check'
        headers = {'Key': ABUSEIPDB_API_KEY, 'Accept': 'application/json'}
        params = {'ipAddress': ip, 'maxAgeInDays': 90}
        
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()['data']
            
            return {
                'source': 'AbuseIPDB',
                'reputation': 'malicious' if data['abuseConfidenceScore'] > 75 else 'suspicious' if data['abuseConfidenceScore'] > 25 else 'clean',
                'score': data['abuseConfidenceScore'],
                'details': f"IP reported {data['totalReports']} times in last 90 days"
            }
        return None

# =============================================================================
# 3. VALIDAÇÃO CONTROLADA (Validation Step)
# =============================================================================

class VulnerabilityValidator:
    """Validação de vulnerabilidades usando Nmap"""
    
    @staticmethod
    def validate_with_nmap(target_ip: str, cve: str) -> bool:
        """Validar se uma vulnerabilidade é explorável via Nmap NSE"""
        import nmap
        
        nm = nmap.PortScanner()
        # Executar scripts NSE de vulnerabilidade
        nm.scan(target_ip, arguments=f'--script vuln -sV')
        
        # Verificar se o CVE foi encontrado nos resultados
        for host in nm.all_hosts():
            if cve.lower() in str(nm[host]).lower():
                return True
        return False

# =============================================================================
# 4. EXECUÇÃO DE PLAYBOOKS (Action)
# =============================================================================

class RemediationEngine:
    """Motor de remediação - executa ações remotas"""
    
    @staticmethod
    def block_ip_via_ssh(target_host: str, ip_to_block: str, ssh_user: str = 'root') -> Dict:
        """Bloquear IP via SSH executando iptables"""
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            ssh.connect(target_host, username=ssh_user, key_filename=os.path.expanduser('~/.ssh/id_rsa'))
            
            commands = [
                f"iptables -A INPUT -s {ip_to_block} -j DROP",
                f"iptables -A OUTPUT -d {ip_to_block} -j DROP",
                "iptables-save > /etc/iptables/rules.v4"
            ]
            
            results = []
            for cmd in commands:
                stdin, stdout, stderr = ssh.exec_command(cmd)
                results.append({
                    'command': cmd,
                    'stdout': stdout.read().decode(),
                    'stderr': stderr.read().decode()
                })
            
            ssh.close()
            return {'success': True, 'results': results}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def patch_vulnerability(target_host: str, package: str, version: str, ssh_user: str = 'root') -> Dict:
        """Atualizar pacote vulnerável via SSH"""
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            ssh.connect(target_host, username=ssh_user, key_filename=os.path.expanduser('~/.ssh/id_rsa'))
            
            # Detectar gerenciador de pacotes
            stdin, stdout, stderr = ssh.exec_command("which apt || which yum")
            pkg_manager = stdout.read().decode().strip()
            
            if 'apt' in pkg_manager:
                cmd = f"apt update && apt install -y {package}={version}"
            elif 'yum' in pkg_manager:
                cmd = f"yum update -y {package}-{version}"
            else:
                return {'success': False, 'error': 'Unknown package manager'}
            
            stdin, stdout, stderr = ssh.exec_command(cmd)
            
            ssh.close()
            return {
                'success': True,
                'command': cmd,
                'stdout': stdout.read().decode(),
                'stderr': stderr.read().decode()
            }
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def wazuh_active_response(agent_id: str, command: str) -> Dict:
        """Executar Active Response do Wazuh"""
        wazuh = WazuhConnector(WAZUH_MANAGER_URL, WAZUH_API_USER, WAZUH_API_PASSWORD)
        wazuh.authenticate()
        
        headers = {'Authorization': f'Bearer {wazuh.token}'}
        ar_url = f"{WAZUH_MANAGER_URL}/active-response"
        
        payload = {
            'command': command,
            'agent_id': agent_id
        }
        
        response = requests.put(ar_url, headers=headers, json=payload, verify=False)
        return response.json()

# =============================================================================
# 5. VERIFICAÇÃO E FECHAMENTO (Double Check)
# =============================================================================

class VerificationEngine:
    """Motor de verificação pós-remediação"""
    
    @staticmethod
    def rescan_agent(agent_id: str) -> Dict:
        """Solicitar re-scan de um agente Wazuh"""
        wazuh = WazuhConnector(WAZUH_MANAGER_URL, WAZUH_API_USER, WAZUH_API_PASSWORD)
        wazuh.authenticate()
        
        headers = {'Authorization': f'Bearer {wazuh.token}'}
        scan_url = f"{WAZUH_MANAGER_URL}/syscheck/{agent_id}"
        
        response = requests.put(scan_url, headers=headers, verify=False)
        return response.json()
    
    @staticmethod
    def log_action(analyst: str, action: str, target: str, details: str) -> Dict:
        """Registrar ação em banco de dados para auditoria"""
        # Aqui você implementaria a gravação no banco de dados
        log_entry = {
            'id': f"log-{datetime.now().timestamp()}",
            'timestamp': datetime.now().isoformat(),
            'analyst': analyst,
            'action': action,
            'target': target,
            'details': details,
            'success': True
        }
        
        # TODO: Salvar em SQLite/PostgreSQL
        # db.session.add(AuditLog(**log_entry))
        # db.session.commit()
        
        return log_entry

# =============================================================================
# API ROUTES
# =============================================================================

@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    """Endpoint para obter alertas"""
    level_min = request.args.get('level_min', 5, type=int)
    
    wazuh = WazuhConnector(WAZUH_MANAGER_URL, WAZUH_API_USER, WAZUH_API_PASSWORD)
    alerts = wazuh.get_alerts(level_min)
    
    return jsonify({'success': True, 'data': alerts})

@app.route('/api/alerts/<alert_id>/enrich', methods=['POST'])
def enrich_alert(alert_id):
    """Enriquecer um alerta com threat intelligence"""
    data = request.json
    ip = data.get('ip')
    file_hash = data.get('file_hash')
    
    threat_intel = []
    
    if ip:
        abuse_data = ThreatIntelligence.check_abuseipdb(ip)
        if abuse_data:
            threat_intel.append(abuse_data)
    
    if file_hash:
        vt_data = ThreatIntelligence.check_virustotal(file_hash)
        if vt_data:
            threat_intel.append(vt_data)
    
    return jsonify({'success': True, 'threat_intel': threat_intel})

@app.route('/api/alerts/<alert_id>/contain', methods=['POST'])
def contain_alert(alert_id):
    """Executar contenção (isolamento de host)"""
    data = request.json
    target_host = data.get('target_host')
    ip_to_block = data.get('ip_to_block')
    
    result = RemediationEngine.block_ip_via_ssh(target_host, ip_to_block)
    
    # Registrar ação
    VerificationEngine.log_action(
        analyst='admin@security.local',
        action='containment',
        target=alert_id,
        details=f"IP {ip_to_block} blocked on {target_host}"
    )
    
    return jsonify({'success': result['success'], 'data': result})

@app.route('/api/vulnerabilities/<vuln_id>/patch', methods=['POST'])
def patch_vulnerability(vuln_id):
    """Aplicar patch em uma vulnerabilidade"""
    data = request.json
    target_host = data.get('target_host')
    package = data.get('package')
    version = data.get('version')
    
    result = RemediationEngine.patch_vulnerability(target_host, package, version)
    
    # Registrar ação
    VerificationEngine.log_action(
        analyst='admin@security.local',
        action='remediation',
        target=vuln_id,
        details=f"Package {package} updated to {version} on {target_host}"
    )
    
    # Re-scan do agente
    if result['success']:
        agent_id = data.get('agent_id')
        VerificationEngine.rescan_agent(agent_id)
    
    return jsonify({'success': result['success'], 'data': result})

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'online',
        'wazuh_connected': True,  # TODO: verificar conexão real
        'timestamp': datetime.now().isoformat()
    })

# =============================================================================
# MAIN
# =============================================================================

if __name__ == '__main__':
    # Modo desenvolvimento
    app.run(host='0.0.0.0', port=5000, debug=True)
    
    # Para produção, use Gunicorn:
    # gunicorn -w 4 -b 0.0.0.0:5000 app:app
