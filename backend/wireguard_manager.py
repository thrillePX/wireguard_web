import os
import subprocess
import uuid
import re
import platform
from pathlib import Path
from datetime import datetime, timedelta

from connection_history import ConnectionHistory
from config_backup import ConfigBackup

class WireGuardManager:
    def __init__(self, base_path='/etc/wireguard/'):
        self.base_path = base_path
        os.makedirs(self.base_path, exist_ok=True)
        self.data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
        os.makedirs(self.data_dir, exist_ok=True)
        self.history = ConnectionHistory(self.data_dir)
        self.backup = ConfigBackup(self.data_dir)
    
    def get_uptime_file(self, config_name):
        """获取连接启动时间记录文件路径"""
        return os.path.join(self.data_dir, f'{config_name}.uptime')
    
    def record_uptime_start(self, config_name):
        """记录连接开始时间"""
        uptime_file = self.get_uptime_file(config_name)
        with open(uptime_file, 'w') as f:
            f.write(datetime.now().isoformat())
    
    def record_uptime_end(self, config_name):
        """清除连接开始时间记录"""
        uptime_file = self.get_uptime_file(config_name)
        if os.path.exists(uptime_file):
            os.remove(uptime_file)
    
    def get_connection_uptime(self, config_name):
        """获取连接累计运行时长（秒）"""
        uptime_file = self.get_uptime_file(config_name)
        if not os.path.exists(uptime_file):
            return None
        try:
            with open(uptime_file, 'r') as f:
                start_time_str = f.read().strip()
            start_time = datetime.fromisoformat(start_time_str)
            elapsed = (datetime.now() - start_time).total_seconds()
            return max(0, elapsed)
        except Exception:
            return None

    def generate_keypair(self):
        """生成WireGuard密钥对"""
        private_key = subprocess.run(
            ['wg', 'genkey'],
            capture_output=True,
            text=True
        ).stdout.strip()
        
        public_key = subprocess.run(
            ['wg', 'pubkey'],
            input=private_key,
            capture_output=True,
            text=True
        ).stdout.strip()
        
        return private_key, public_key

    def derive_public_key(self, private_key):
        """从私钥派生公钥"""
        try:
            public_key = subprocess.run(
                ['wg', 'pubkey'],
                input=private_key,
                capture_output=True,
                text=True
            ).stdout.strip()
            return public_key
        except Exception as e:
            return None

    def generate_preshared_key(self):
        """生成预共享密钥"""
        return subprocess.run(
            ['wg', 'genpsk'],
            capture_output=True,
            text=True
        ).stdout.strip()

    def parse_config(self, config_path):
        """解析配置文件"""
        if not os.path.exists(config_path):
            return {}
        
        config = {}
        current_section = None
        
        with open(config_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith('[') and line.endswith(']'):
                    current_section = line[1:-1]
                    config[current_section] = {}
                elif '=' in line and current_section:
                    key, value = line.split('=', 1)
                    config[current_section][key.strip()] = value.strip()
        
        return config

    def is_connected(self, config_name):
        """检查连接是否活跃"""
        try:
            interface_config = self.parse_config(os.path.join(self.base_path, f'{config_name}.conf'))
            interface_info = interface_config.get('Interface', {})
            client_address = interface_info.get('Address', '')
            check_ip = client_address.split('/')[0]
            
            if not check_ip:
                return False
            
            system = platform.system()
            
            if system == 'Darwin':
                result = subprocess.run(
                    ['ifconfig'],
                    capture_output=True,
                    text=True
                )
                if result.returncode != 0:
                    return False
                
                for line in result.stdout.split('\n'):
                    if 'inet ' in line and check_ip in line:
                        return True
                return False
            else:
                result = subprocess.run(
                    ['ip', 'link', 'show'],
                    capture_output=True,
                    text=True
                )
                if config_name in result.stdout:
                    wg_result = subprocess.run(
                        ['wg', 'show', config_name],
                        capture_output=True,
                        text=True
                    )
                    return wg_result.returncode == 0
                return False
        except:
            return False

    def get_interface_name(self, config_name):
        """获取配置文件对应的接口名称（macOS上可能是utun）"""
        try:
            interface_config = self.parse_config(os.path.join(self.base_path, f'{config_name}.conf'))
            interface_info = interface_config.get('Interface', {})
            client_address = interface_info.get('Address', '')
            check_ip = client_address.split('/')[0]
            
            if not check_ip:
                return None
            
            system = platform.system()
            
            if system == 'Darwin':
                result = subprocess.run(
                    ['ifconfig'],
                    capture_output=True,
                    text=True
                )
                if result.returncode != 0:
                    return None
                
                lines = result.stdout.split('\n')
                for i, line in enumerate(lines):
                    if 'inet ' in line and check_ip in line:
                        if i > 0:
                            prev_line = lines[i-1]
                            if 'utun' in prev_line:
                                return prev_line.split(':')[0].strip()
                return None
            else:
                return config_name
        except:
            return None

    def connect(self, config_name):
        """连接WireGuard"""
        config_path = os.path.join(self.base_path, f'{config_name}.conf')
        if not os.path.exists(config_path):
            return False, "配置文件不存在"
        
        system = platform.system()
        
        try:
            if system == 'Darwin':
                result = subprocess.run(
                    ['wg-quick', 'up', config_path],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    self.record_uptime_start(config_name)
                    self.history.record_connect(config_name)
                    return True, "连接成功"
                else:
                    return False, result.stderr or "连接失败"
            else:
                result = subprocess.run(
                    ['wg-quick', 'up', config_name],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    self.record_uptime_start(config_name)
                    self.history.record_connect(config_name)
                    return True, "连接成功"
                else:
                    return False, result.stderr or "连接失败"
        except Exception as e:
            return False, str(e)

    def disconnect(self, config_name):
        """断开WireGuard连接"""
        config_path = os.path.join(self.base_path, f'{config_name}.conf')
        
        system = platform.system()
        
        try:
            if system == 'Darwin':
                result = subprocess.run(
                    ['wg-quick', 'down', config_path],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    self.record_uptime_end(config_name)
                    self.history.record_disconnect(config_name)
                    return True, "已断开连接"
                else:
                    return False, result.stderr or "断开失败"
            else:
                result = subprocess.run(
                    ['wg-quick', 'down', config_name],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    self.record_uptime_end(config_name)
                    self.history.record_disconnect(config_name)
                    return True, "已断开连接"
                else:
                    return False, result.stderr or "断开失败"
        except Exception as e:
            return False, str(e)

    def get_connection_status(self, config_name):
        """获取连接的详细状态"""
        interface_name = self.get_interface_name(config_name)
        
        if not interface_name:
            return {
                'connected': False,
                'interface': None,
                'transfer': {'rx': 0, 'tx': 0},
                'latest_handshake': None,
                'peers': []
            }
        
        try:
            result = subprocess.run(
                ['wg', 'show', interface_name],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                return {
                    'connected': False,
                    'interface': interface_name,
                    'transfer': {'rx': 0, 'tx': 0},
                    'latest_handshake': None,
                    'peers': []
                }
            
            output = result.stdout
            status = {
                'connected': True,
                'interface': interface_name,
                'transfer': {'rx': 0, 'tx': 0},
                'latest_handshake': None,
                'peers': []
            }
            
            lines = output.split('\n')
            current_peer = None
            
            for line in lines:
                line = line.strip()
                if line.startswith('peer:'):
                    current_peer = {
                        'public_key': line.replace('peer:', '').strip(),
                        'endpoint': None,
                        'allowed_ips': None,
                        'latest_handshake': None,
                        'transfer': {'rx': 0, 'tx': 0}
                    }
                    status['peers'].append(current_peer)
                elif line.startswith('endpoint:'):
                    if current_peer:
                        current_peer['endpoint'] = line.replace('endpoint:', '').strip()
                elif line.startswith('allowed ip:'):
                    if current_peer:
                        current_peer['allowed_ips'] = line.replace('allowed ip:', '').strip()
                elif line.startswith('latest handshake:'):
                    if current_peer:
                        current_peer['latest_handshake'] = line.replace('latest handshake:', '').strip()
                elif line.startswith('transfer:'):
                    if current_peer:
                        transfer_data = line.replace('transfer:', '').strip()
                        parts = transfer_data.split(',')
                        for part in parts:
                            part = part.strip()
                            if 'received' in part:
                                rx = part.replace('received', '').strip()
                                current_peer['transfer']['rx'] = self._parse_bytes(rx)
                            elif 'sent' in part:
                                tx = part.replace('sent', '').strip()
                                current_peer['transfer']['tx'] = self._parse_bytes(tx)
            
            return status
            
        except Exception as e:
            return {
                'connected': False,
                'interface': interface_name,
                'transfer': {'rx': 0, 'tx': 0},
                'latest_handshake': None,
                'peers': [],
                'error': str(e)
            }

    def _parse_bytes(self, byte_str):
        """解析字节字符串"""
        byte_str = byte_str.strip()
        try:
            if 'TiB' in byte_str:
                return float(byte_str.replace('TiB', '').strip()) * 1024 * 1024 * 1024 * 1024
            elif 'GiB' in byte_str:
                return float(byte_str.replace('GiB', '').strip()) * 1024 * 1024 * 1024
            elif 'MiB' in byte_str:
                return float(byte_str.replace('MiB', '').strip()) * 1024 * 1024
            elif 'KiB' in byte_str:
                return float(byte_str.replace('KiB', '').strip()) * 1024
            elif 'B' in byte_str:
                return float(byte_str.replace('B', '').strip())
            else:
                return float(byte_str)
        except:
            return 0

    def format_bytes(self, bytes_num):
        """格式化字节数为可读字符串"""
        if bytes_num >= 1024 * 1024 * 1024 * 1024:
            return f"{bytes_num / (1024 * 1024 * 1024 * 1024):.2f} TB"
        elif bytes_num >= 1024 * 1024 * 1024:
            return f"{bytes_num / (1024 * 1024 * 1024):.2f} GB"
        elif bytes_num >= 1024 * 1024:
            return f"{bytes_num / (1024 * 1024):.2f} MB"
        elif bytes_num >= 1024:
            return f"{bytes_num / 1024:.2f} KB"
        else:
            return f"{bytes_num:.0f} B"

    def calculate_uptime(self, latest_handshake, config_name=None):
        """根据连接开始时间计算累计运行时长"""
        if config_name:
            seconds = self.get_connection_uptime(config_name)
            if seconds is not None:
                return self.format_uptime(seconds)
        return None
    
    def format_uptime(self, seconds):
        """格式化运行时长"""
        if seconds is None or seconds <= 0:
            return None
        
        td = timedelta(seconds=int(seconds))
        days = td.days
        hours, remainder = divmod(td.seconds, 3600)
        minutes, secs = divmod(remainder, 60)
        
        parts = []
        if days > 0:
            parts.append(f"{days}天")
        if hours > 0:
            parts.append(f"{hours}时")
        if minutes > 0:
            parts.append(f"{minutes}分")
        if secs > 0 and days == 0:
            parts.append(f"{secs}秒")
        
        return ''.join(parts) if parts else '< 1秒'

    def list_connections(self):
        """列出所有WireGuard配置"""
        connections = []
        
        if not os.path.exists(self.base_path):
            return connections
        
        for file in os.listdir(self.base_path):
            if file.endswith('.conf'):
                config_path = os.path.join(self.base_path, file)
                config_data = self.parse_config(config_path)
                
                interface_info = config_data.get('Interface', {})
                peer_info = config_data.get('Peer', {})
                
                connection = {
                    'name': file.replace('.conf', ''),
                    'path': config_path,
                    'config': config_data,
                    'interface': interface_info,
                    'peer': peer_info,
                    'connected': self.is_connected(file.replace('.conf', '')),
                    'interface_name': self.get_interface_name(file.replace('.conf', '')),
                    'uptime': None
                }
                
                if connection['connected']:
                    connection['uptime'] = self.calculate_uptime(None, file.replace('.conf', ''))
                
                connections.append(connection)
        
        return connections

    def get_connection(self, name):
        """获取单个连接详情"""
        config_path = os.path.join(self.base_path, f'{name}.conf')
        
        if not os.path.exists(config_path):
            return None
        
        config_data = self.parse_config(config_path)
        interface_info = config_data.get('Interface', {})
        peer_info = config_data.get('Peer', {})
        
        connection = {
            'name': name,
            'path': config_path,
            'config': config_data,
            'interface': interface_info,
            'peer': peer_info,
            'connected': self.is_connected(name),
            'interface_name': self.get_interface_name(name)
        }
        
        if connection['connected']:
            status = self.get_connection_status(name)
            connection['status'] = status
        
        return connection

    def add_connection(self, name, config_content):
        """添加新连接"""
        if not name.endswith('.conf'):
            name = f'{name}.conf'
        
        config_path = os.path.join(self.base_path, name)
        
        if os.path.exists(config_path):
            return False, "连接已存在"
        
        try:
            with open(config_path, 'w') as f:
                f.write(config_content)
            os.chmod(config_path, 0o600)
            return True, f"连接 '{name.replace('.conf', '')}' 已添加"
        except Exception as e:
            return False, str(e)

    def update_connection(self, name, config_content):
        """更新连接配置"""
        config_path = os.path.join(self.base_path, f'{name}.conf')
        
        if not os.path.exists(config_path):
            return False, "连接不存在"
        
        try:
            with open(config_path, 'r') as f:
                old_config = f.read()
            
            self.backup.backup(name, old_config)
            
            with open(config_path, 'w') as f:
                f.write(config_content)
            os.chmod(config_path, 0o600)
            return True, "配置已更新"
        except Exception as e:
            return False, str(e)

    def delete_connection(self, name):
        """删除连接"""
        config_path = os.path.join(self.base_path, f'{name}.conf')
        
        if not os.path.exists(config_path):
            return False, "连接不存在"
        
        try:
            if self.is_connected(name):
                self.disconnect(name)
            
            os.remove(config_path)
            return True, "连接已删除"
        except Exception as e:
            return False, str(e)

    def import_config(self, config_file):
        """导入配置文件"""
        try:
            config_content = config_file.read().decode('utf-8')
            config_data = self.parse_config(config_content)
            
            if 'Interface' not in config_data:
                return False, "无效的配置文件：缺少 [Interface] 部分"
            
            interface_info = config_data.get('Interface', {})
            address = interface_info.get('Address', '')
            
            if not address:
                return False, "无效的配置文件：缺少 Address"
            
            base_name = address.split('/')[0].replace('.', '_')
            name = f"{base_name}.conf"
            counter = 1
            
            while os.path.exists(os.path.join(self.base_path, name)):
                name = f"{base_name}_{counter}.conf"
                counter += 1
            
            config_path = os.path.join(self.base_path, name)
            
            with open(config_path, 'w') as f:
                f.write(config_content)
            os.chmod(config_path, 0o600)
            
            return True, {
                'name': name.replace('.conf', ''),
                'path': config_path,
                'message': f"配置文件已导入为 '{name.replace('.conf', '')}'"
            }
        except Exception as e:
            return False, str(e)

    def get_all_status(self):
        """获取所有连接的状态"""
        connections = self.list_connections()
        status = {
            'total': len(connections),
            'connected': len([c for c in connections if c['connected']]),
            'disconnected': len([c for c in connections if not c['connected']]),
            'connections': []
        }
        
        for conn in connections:
            conn_status = {
                'name': conn['name'],
                'connected': conn['connected'],
                'interface': conn.get('interface_name'),
                'endpoint': None,
                'transfer': {'rx': 0, 'tx': 0},
                'uptime': None
            }
            
            if conn['connected']:
                detail = self.get_connection_status(conn['name'])
                if detail and detail.get('peers'):
                    peer = detail['peers'][0]
                    conn_status['endpoint'] = peer.get('endpoint')
                    conn_status['transfer'] = peer.get('transfer', {'rx': 0, 'tx': 0})
                    conn_status['latest_handshake'] = peer.get('latest_handshake')
                conn_status['uptime'] = self.calculate_uptime(None, conn['name'])
            
            status['connections'].append(conn_status)
        
        return status
