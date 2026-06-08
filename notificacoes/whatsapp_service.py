import requests
import logging
import os
import subprocess
import time
from pathlib import Path
from django.conf import settings

logger = logging.getLogger(__name__)

class WhatsAppService:
    """Serviço simplificado para Evolution API"""
    
    def __init__(self, instance_name=None):
        raw_api_url = getattr(settings, 'EVOLUTION_API_URL', None) or getattr(settings, 'WHATSAPP_API_URL', None) or 'http://localhost:8080'
        self.api_url = self._normalize_api_url(raw_api_url)
        self.api_key = getattr(settings, 'EVOLUTION_API_KEY', None) or getattr(settings, 'WHATSAPP_API_KEY', None) or ''
        # Se passar o nome, usa. Senão pega o padrão
        self.instance_name = instance_name or getattr(settings, 'EVOLUTION_INSTANCE_NAME', None) or getattr(settings, 'WHATSAPP_INSTANCE_NAME', None) or 'imobilpro'
        self.last_health_error = None
        self._owner_cache_ts = 0
        self._owner_cache_digits = ''
        
        self.headers = {
            'apikey': self.api_key,
            'Content-Type': 'application/json'
        }

    def get_owner_digits(self, max_age_seconds=60):
        now = time.time()
        try:
            if self._owner_cache_digits and (now - float(self._owner_cache_ts)) <= float(max_age_seconds):
                return self._owner_cache_digits
        except Exception:
            pass

        def _digits(value):
            s = str(value or '').strip()
            if not s:
                return ''
            d = ''.join(ch for ch in s if ch.isdigit())
            if 10 <= len(d) <= 15:
                return d
            if len(d) > 15 and ('@' in s or 'whatsapp' in s.lower()):
                d2 = d[:15]
                if 10 <= len(d2) <= 15:
                    return d2
            return ''

        def _collect_candidates(obj, out, limit=80):
            if limit <= 0:
                return
            if isinstance(obj, dict):
                priority = (
                    'owner', 'ownerJid', 'ownerjid', 'wid', 'me', 'jid',
                    'number', 'phoneNumber', 'phone_number', 'phone', 'msisdn',
                )
                for k in priority:
                    if k in obj:
                        d = _digits(obj.get(k))
                        if d:
                            out.append(d)
                for v in obj.values():
                    _collect_candidates(v, out, limit=limit - 1)
                return
            if isinstance(obj, list):
                for v in obj[:20]:
                    _collect_candidates(v, out, limit=limit - 1)
                return

        owner_digits = ''
        try:
            st = requests.get(
                f"{self.api_url}/instance/connectionState/{self.instance_name}",
                headers=self.headers,
                timeout=10,
            )
            if st.status_code == 200 and st.content:
                data = st.json()
                cand = []
                _collect_candidates(data, cand)
                owner_digits = max(cand, key=len) if cand else ''
        except Exception:
            owner_digits = ''

        if not owner_digits:
            try:
                info = requests.get(
                    f"{self.api_url}/instance/fetchInstances",
                    headers=self.headers,
                    timeout=10,
                )
                if info.status_code == 200 and info.content:
                    instances = info.json()
                    instances_list = None
                    if isinstance(instances, list):
                        instances_list = instances
                    elif isinstance(instances, dict):
                        for k in ('instances', 'data', 'result', 'response'):
                            if isinstance(instances.get(k), list):
                                instances_list = instances.get(k)
                                break

                    target = None
                    if instances_list:
                        for inst in instances_list:
                            if not isinstance(inst, dict):
                                continue
                            data = (inst.get('instance') or inst) if isinstance(inst, dict) else {}
                            name = ''
                            if isinstance(data, dict):
                                name = str(data.get('instanceName') or data.get('name') or data.get('instance') or '').strip()
                            if name == self.instance_name:
                                target = inst
                                break

                    cand = []
                    if target is not None:
                        _collect_candidates(target, cand)
                    else:
                        _collect_candidates(instances, cand)
                    owner_digits = max(cand, key=len) if cand else ''
            except Exception:
                owner_digits = ''

        try:
            self._owner_cache_ts = now
            self._owner_cache_digits = owner_digits or ''
        except Exception:
            pass
        return owner_digits or ''
    
    def _normalize_api_url(self, value):
        url = (value or '').strip()
        if not url:
            return ''
        if (url.startswith('"') and url.endswith('"')) or (url.startswith("'") and url.endswith("'")):
            url = url[1:-1].strip()
        if '=' in url and ('EVOLUTION_API_URL' in url or 'WHATSAPP_API_URL' in url):
            url = url.split('=', 1)[1].strip()
        if '://' not in url and '.' in url and ' ' not in url and not url.startswith('/'):
            url = 'https://' + url
        while url.endswith('/'):
            url = url[:-1]
        return url
        
    def docker_diagnostics(self):
        try:
            try:
                svc = subprocess.run(
                    ["powershell", "-NoProfile", "-Command", "Get-Service com.docker.service -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Status"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=6,
                    check=False,
                )
                svc_status = (svc.stdout or "").strip()
            except Exception:
                svc_status = ""

            proc = subprocess.run(
                ["docker", "version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=8,
                check=False,
            )
            out = (proc.stdout or "") + "\n" + (proc.stderr or "")
            if proc.returncode == 0:
                return {"ok": True, "message": "Docker OK"}
            if "dockerDesktopLinuxEngine" in out or "pipe" in out or "O sistema não pode encontrar o arquivo especificado" in out:
                if svc_status.lower() == "stopped":
                    return {"ok": False, "message": "Docker Desktop está fechado (serviço parado). Abra o Docker Desktop (se precisar, como Administrador) e aguarde iniciar."}
                return {"ok": False, "message": "Docker Desktop está fechado. Abra o Docker Desktop e aguarde o Engine iniciar."}
            return {"ok": False, "message": "Docker está indisponível."}
        except FileNotFoundError:
            return {"ok": False, "message": "Docker não está instalado ou não está no PATH."}
        except Exception:
            return {"ok": False, "message": "Não foi possível verificar o Docker."}

    def start_docker_desktop(self):
        try:
            docker_desktop_candidates = [
                r"C:\Program Files\Docker\Docker\Docker Desktop.exe",
                os.path.expandvars(r"%LOCALAPPDATA%\Programs\Docker\Docker\Docker Desktop.exe"),
            ]
            for p in docker_desktop_candidates:
                if p and os.path.exists(p):
                    try:
                        os.startfile(p)
                        return True
                    except Exception:
                        continue
            try:
                subprocess.run(
                    ["powershell", "-NoProfile", "-Command", "Start-Process 'Docker Desktop'"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=10,
                    check=False,
                )
                return True
            except Exception:
                return False
        except Exception:
            return False

    def start_evolution_compose_async(self):
        try:
            base_dir = getattr(settings, 'BASE_DIR', None)
            if not base_dir:
                return False
            compose_dir = Path(base_dir) / 'evolution-api'
            if not compose_dir.exists():
                return False
            compose_dir_str = str(compose_dir)
            inner = (
                "$ErrorActionPreference='SilentlyContinue';"
                "$composeDir='" + compose_dir_str.replace("'", "''") + "';"
                "for($i=0;$i -lt 90;$i++){"
                "try{docker version *> $null; if($LASTEXITCODE -eq 0){break}}catch{};"
                "Start-Sleep -Seconds 2"
                "};"
                "if(Test-Path $composeDir){"
                "Set-Location $composeDir;"
                "docker compose up -d"
                "}"
            )
            launcher = (
                "Start-Process powershell -WindowStyle Hidden -ArgumentList "
                f"'-NoProfile -Command \"{inner}\"'"
            )
            subprocess.Popen(
                ["powershell", "-NoProfile", "-Command", launcher],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True
        except Exception:
            return False

    def _try_start_evolution_docker(self):
        try:
            if not getattr(settings, 'EVOLUTION_AUTO_START_DOCKER', False):
                return False

            base_dir = getattr(settings, 'BASE_DIR', None)
            if not base_dir:
                return False

            compose_dir = Path(base_dir) / 'evolution-api'
            if not compose_dir.exists():
                return False

            self.start_docker_desktop()
            self.start_evolution_compose_async()
            return True
        except Exception:
            return False

    def check_api_health(self):
        """Verifica se a API está rodando"""
        self.last_health_error = None
        try:
            res = requests.get(
                f"{self.api_url}/instance/connectionState/{self.instance_name}",
                headers=self.headers,
                timeout=8,
            )
            if res.status_code in {200, 404}:
                return True
        except Exception as e:
            self.last_health_error = str(e)

        return False

    def get_status(self):
        """Retorna o status da conexão da instância"""
        try:
            res = requests.get(f"{self.api_url}/instance/connectionState/{self.instance_name}", headers=self.headers, timeout=10)
            
            if res.status_code == 404:
                # Instância não existe, tentar criá-area
                return self._create_instance()
                
            if res.status_code == 200:
                data = res.json()
                owner_digits = self.get_owner_digits()
                state = (
                    (data.get('instance', {}) or {}).get('state')
                    or (data.get('instance', {}) or {}).get('connectionState')
                    or data.get('state')
                    or data.get('connectionState')
                    or ''
                )
                state = str(state).lower().strip()
                if state in {'open', 'connected', 'online'}:
                    return {'status': 'connected', 'message': 'Conectado', 'owner': owner_digits}
                elif state in {'connecting'}:
                    return {'status': 'connecting', 'message': 'Conectando...', 'owner': owner_digits}
                else:
                    return {'status': 'disconnected', 'message': 'Desconectado', 'owner': owner_digits}
                    
            return {'status': 'error', 'message': f'Erro {res.status_code}', 'owner': ''}
        except Exception as e:
            logger.error(f"Erro ao obter status WhatsApp: {e}")
            return {'status': 'error', 'message': 'API Offline ou Erro Interno', 'owner': ''}
            
    def _create_instance(self):
        """Cria a instância se não existir"""
        try:
            payload = {
                "instanceName": self.instance_name,
                "qrcode": True,
                "integration": "WHATSAPP-BAILEYS"
            }
            res = requests.post(f"{self.api_url}/instance/create", headers=self.headers, json=payload, timeout=15)
            if res.status_code in [200, 201]:
                return {'status': 'disconnected', 'message': 'Instância Criada'}
            return {'status': 'error', 'message': 'Erro ao criar instância'}
        except:
            return {'status': 'error', 'message': 'Falha ao criar instância'}

    def get_qrcode(self):
        """Busca o QR code para conectar"""
        try:
            # Chama o connect que retorna o base64 do QR
            res = requests.get(
                f"{self.api_url}/instance/connect/{self.instance_name}",
                headers=self.headers,
                timeout=15,
            )

            if res.status_code == 404:
                self._create_instance()
                res = requests.get(
                    f"{self.api_url}/instance/connect/{self.instance_name}",
                    headers=self.headers,
                    timeout=15,
                )

            if res.status_code in [200, 201]:
                data = res.json() if res.content else {}
                raw = data.get('base64') or data.get('qrcode') or data.get('qrCode')
                if not raw:
                    return {'success': False, 'error': 'QR não disponível (instância já conectada?)'}

                qrcode = raw.strip() if isinstance(raw, str) else str(raw)
                if qrcode and not qrcode.startswith('data:image/'):
                    qrcode = 'data:image/png;base64,' + qrcode
                return {'success': True, 'qrcode': qrcode}

            return {'success': False, 'error': f'HTTP {res.status_code}'}
        except Exception as e:
            logger.error(f"Erro QR Code: {e}")
            return {'success': False, 'error': 'Erro de conexão com API'}

    def logout(self):
        """Desconecta o WhatsApp"""
        try:
            requests.delete(f"{self.api_url}/instance/logout/{self.instance_name}", headers=self.headers, timeout=15)
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}
            
    def format_phone(self, phone):
        """Formata o número para o padrão esperado pela Evolution API (apenas dígitos com DDI)."""
        if not phone:
            return ""
        nums = ''.join(filter(str.isdigit, str(phone)))
        if len(nums) == 11 and nums.startswith('0'):
            nums = nums[1:]

        country = ''
        rest = nums
        if rest.startswith('55'):
            country = '55'
            rest = rest[2:]

        if len(rest) == 10:
            ddd = rest[:2]
            subscriber = rest[2:]
            if subscriber and subscriber[0] in '6789' and subscriber[0] != '9':
                rest = ddd + '9' + subscriber

        if not country and len(rest) in [10, 11]:
            country = '55'

        nums = (country + rest) if country else rest
        if len(nums) < 12:
            return ""
        return nums

    def send_message(self, phone, text):
        """Envia mensagem de texto"""
        try:
            formatted_number = self.format_phone(phone)
            if not formatted_number:
                return {'success': False, 'error': 'Telefone inválido'}

            try:
                owner_digits = self.get_owner_digits()
                if owner_digits and (formatted_number.endswith(owner_digits) or owner_digits.endswith(formatted_number)):
                    return {'success': False, 'error': 'Não é possível enviar mensagem para o mesmo número conectado na instância. Teste com outro celular.'}
            except Exception:
                pass

            wa_exists = None
            wa_jid = ''
            try:
                check = requests.post(
                    f"{self.api_url}/chat/whatsappNumbers/{self.instance_name}",
                    headers=self.headers,
                    json={"numbers": [formatted_number]},
                    timeout=15,
                )
                if check.status_code == 200:
                    data = check.json()
                    if isinstance(data, list) and data:
                        wa_exists = bool(data[0].get('exists'))
                        wa_jid = str(data[0].get('jid') or '').strip()
                        if not wa_exists:
                            return {'success': False, 'error': f'Número não possui WhatsApp: {data[0].get("number") or formatted_number}', 'exists': wa_exists, 'jid': wa_jid}
            except Exception:
                pass

            payload = {"number": formatted_number, "text": text, "textMessage": {"text": text}}
            res = requests.post(
                f"{self.api_url}/message/sendText/{self.instance_name}",
                headers=self.headers,
                json=payload,
                timeout=15,
            )
            
            if res.status_code in [200, 201]:
                try:
                    body = res.json()
                except Exception:
                    body = None
                return {'success': True, 'response': body, 'http_status': res.status_code, 'exists': wa_exists, 'jid': wa_jid}
            else:
                return {'success': False, 'error': f"Erro HTTP {res.status_code}: {res.text}"}
        except requests.exceptions.ReadTimeout:
            return {'success': False, 'error': 'Timeout ao enviar na Evolution API (verifique se o container redis está rodando)'}
        except Exception as e:
            logger.error(f"Erro ao enviar WhatsApp: {e}")
            return {'success': False, 'error': str(e)}
