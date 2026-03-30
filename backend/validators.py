import re
from typing import Tuple, Optional

class ValidationError(Exception):
    def __init__(self, message: str, field: str = None):
        self.message = message
        self.field = field
        super().__init__(self.message)

def validate_connection_name(name: str) -> Tuple[bool, Optional[str]]:
    """验证连接名称"""
    if not name:
        return False, "连接名称不能为空"
    if len(name) > 64:
        return False, "连接名称不能超过64个字符"
    if not re.match(r'^[a-zA-Z0-9_-]+$', name):
        return False, "连接名称只能包含字母、数字、下划线和连字符"
    return True, None

def validate_wireguard_config(config: dict) -> Tuple[bool, Optional[str]]:
    """验证 WireGuard 配置"""
    if not isinstance(config, dict):
        return False, "配置必须是字典格式"
    
    if 'Interface' not in config:
        return False, "配置缺少 [Interface] 部分"
    
    interface = config.get('Interface', {})
    if not isinstance(interface, dict):
        return False, "[Interface] 必须是字典格式"
    
    if 'PrivateKey' not in interface:
        return False, "[Interface] 必须包含 PrivateKey"
    
    if not re.match(r'^[A-Za-z0-9+/]{42}[A-Za-z0-9+/=]{6}$', interface['PrivateKey']):
        return False, "私钥格式无效"
    
    if 'Address' not in interface:
        return False, "[Interface] 必须包含 Address"
    
    address = interface.get('Address', '')
    if not re.match(r'^[\d.:a-fA-F/]+$', address):
        return False, "IP 地址格式无效"
    
    if 'Peer' not in config:
        return False, "配置缺少 [Peer] 部分"
    
    peer = config.get('Peer')
    if isinstance(peer, dict):
        if 'PublicKey' not in peer:
            return False, "[Peer] 必须包含 PublicKey"
        if not re.match(r'^[A-Za-z0-9+/]{42}[A-Za-z0-9+/=]{6}$', peer['PublicKey']):
            return False, "公钥格式无效"
    elif isinstance(peer, list):
        for i, p in enumerate(peer):
            if not isinstance(p, dict):
                return False, f"[Peer] 第 {i+1} 个必须是字典格式"
            if 'PublicKey' not in p:
                return False, f"[Peer] 第 {i+1} 个必须包含 PublicKey"
    else:
        return False, "[Peer] 格式无效"
    
    return True, None

def validate_ip_address(ip: str) -> Tuple[bool, Optional[str]]:
    """验证 IP 地址格式"""
    ipv4_pattern = r'^(\d{1,3}\.){3}\d{1,3}(\/\d{1,2})?$'
    ipv6_pattern = r'^([0-9a-fA-F]{0,4}:){2,7}[0-9a-fA-F]{0,4}(\/\d{1,3})?$'
    
    if re.match(ipv4_pattern, ip) or re.match(ipv6_pattern, ip):
        return True, None
    return False, f"无效的 IP 地址格式: {ip}"

def validate_endpoint(endpoint: str) -> Tuple[bool, Optional[str]]:
    """验证端点格式"""
    pattern = r'^[\w.-]+:\d+$'
    if re.match(pattern, endpoint):
        return True, None
    return False, f"无效的端点格式: {endpoint}，应为 hostname:port"

def sanitize_filename(filename: str) -> str:
    """清理文件名，移除危险字符"""
    return re.sub(r'[^\w\s-]', '', filename).strip()
