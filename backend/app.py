from flask import Flask, request, jsonify, send_file
from wireguard_manager import WireGuardManager
from config import Config
from validators import (
    validate_connection_name, 
    validate_wireguard_config,
    ValidationError as ConfigValidationError
)
from errors import (
    APIError, ValidationError, NotFoundError, 
    ConflictError, setup_logging, log_error, log_request
)
import os
import tempfile
import logging
from functools import wraps

app = Flask(__name__)
app.config.from_object(Config)

setup_logging(level=logging.INFO)
logger = logging.getLogger(__name__)

wm = WireGuardManager(base_path=app.config['WG_PATH'])

def validate_json(*required_fields):
    """JSON 验证装饰器"""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not request.is_json:
                return jsonify({'error': '请求必须是 JSON 格式'}), 400
            
            data = request.get_json()
            missing = [field for field in required_fields if field not in data or data[field] is None]
            
            if missing:
                return jsonify({
                    'error': f'缺少必需字段: {", ".join(missing)}',
                    'missing_fields': missing
                }), 400
            return f(*args, **kwargs)
        return wrapper
    return decorator

def require_connected(f):
    """连接状态验证装饰器"""
    @wraps(f)
    def wrapper(name, *args, **kwargs):
        connection = wm.get_connection(name)
        if not connection:
            return jsonify({'error': '连接不存在'}), 404
        return f(name, *args, **kwargs)
    return wrapper

@app.route('/api/v1/health', methods=['GET'])
@log_error
def health_check():
    """健康检查"""
    return jsonify({
        'status': 'healthy',
        'version': 'v1',
        'wg_path': wm.base_path,
        'platform': 'Darwin' if __import__('platform').system() == 'Darwin' else 'Linux',
        'timestamp': __import__('datetime').datetime.now().isoformat()
    })

@app.route('/api/v1/config/path', methods=['GET'])
@log_error
def get_config_path():
    """获取配置文件路径"""
    return jsonify({
        'path': wm.base_path,
        'default': Config.DEFAULT_WG_PATH
    })

@app.route('/api/v1/config/path', methods=['POST'])
@log_error
@validate_json('path')
def set_config_path():
    """设置配置文件路径"""
    data = request.json
    new_path = data.get('path', Config.DEFAULT_WG_PATH)
    
    if not os.path.exists(new_path):
        return jsonify({'error': f'路径不存在: {new_path}'}), 400
    
    global wm
    wm = WireGuardManager(base_path=new_path)
    logger.info(f"配置路径已更新为: {new_path}")
    return jsonify({
        'path': new_path, 
        'message': '配置路径已更新',
        'timestamp': __import__('datetime').datetime.now().isoformat()
    })

@app.route('/api/v1/keys/generate', methods=['POST'])
@log_error
def generate_keys():
    """生成 WireGuard 密钥对"""
    private_key, public_key = wm.generate_keypair()
    logger.info("生成了新的 WireGuard 密钥对")
    return jsonify({
        'privateKey': private_key,
        'publicKey': public_key,
        'timestamp': __import__('datetime').datetime.now().isoformat()
    })

@app.route('/api/v1/keys/preshared', methods=['POST'])
@log_error
def generate_preshared_key():
    """生成 WireGuard 预共享密钥"""
    psk = wm.generate_preshared_key()
    logger.info("生成了新的预共享密钥")
    return jsonify({
        'presharedKey': psk,
        'timestamp': __import__('datetime').datetime.now().isoformat()
    })

@app.route('/api/v1/keys/derive', methods=['POST'])
@log_error
@validate_json('privateKey')
def derive_public_key():
    """从私钥派生公钥"""
    data = request.json
    private_key = data.get('privateKey')
    
    if not private_key:
        return jsonify({'error': '私钥不能为空'}), 400
    
    public_key = wm.derive_public_key(private_key)
    if public_key:
        return jsonify({
            'publicKey': public_key,
            'timestamp': __import__('datetime').datetime.now().isoformat()
        })
    return jsonify({'error': '无效的私钥格式'}), 400

@app.route('/api/v1/connections', methods=['GET'])
@log_error
def list_connections():
    """列出所有连接"""
    connections = wm.list_connections()
    return jsonify({
        'connections': connections,
        'count': len(connections),
        'timestamp': __import__('datetime').datetime.now().isoformat()
    })

@app.route('/api/v1/connections/all-status', methods=['GET'])
@log_error
def get_all_status():
    """获取所有连接的状态"""
    status = wm.get_all_status()
    for conn in status['connections']:
        if conn['transfer']['rx']:
            conn['transfer']['rx_formatted'] = wm.format_bytes(conn['transfer']['rx'])
        if conn['transfer']['tx']:
            conn['transfer']['tx_formatted'] = wm.format_bytes(conn['transfer']['tx'])
    return jsonify(status)

@app.route('/api/v1/connections/<name>', methods=['GET'])
@log_error
def get_connection(name):
    """获取单个连接详情"""
    valid, error = validate_connection_name(name)
    if not valid:
        return jsonify({'error': error}), 400
    
    connection = wm.get_connection(name)
    if not connection:
        return jsonify({'error': '连接不存在'}), 404
    
    if connection['connected'] and 'status' in connection:
        for peer in connection['status'].get('peers', []):
            if peer['transfer']['rx']:
                peer['transfer']['rx_formatted'] = wm.format_bytes(peer['transfer']['rx'])
            if peer['transfer']['tx']:
                peer['transfer']['tx_formatted'] = wm.format_bytes(peer['transfer']['tx'])
    
    return jsonify({
        'connection': connection,
        'timestamp': __import__('datetime').datetime.now().isoformat()
    })

@app.route('/api/v1/connections', methods=['POST'])
@log_error
@validate_json('name', 'config')
def add_connection():
    """添加新连接"""
    data = request.json
    name = data.get('name')
    config_content = data.get('config')
    
    valid, error = validate_connection_name(name)
    if not valid:
        return jsonify({'error': error}), 400
    
    existing = wm.get_connection(name)
    if existing:
        return jsonify({'error': f'连接 "{name}" 已存在'}), 409
    
    if isinstance(config_content, dict):
        valid, error = validate_wireguard_config(config_content)
        if not valid:
            return jsonify({'error': error}), 400
    
    success, result = wm.add_connection(name, config_content)
    if success:
        logger.info(f"添加了新连接: {name}")
        return jsonify({
            'message': '连接添加成功',
            'connection': result,
            'timestamp': __import__('datetime').datetime.now().isoformat()
        }), 201
    return jsonify({'error': result}), 400

@app.route('/api/v1/connections/<name>', methods=['PUT'])
@log_error
def update_connection(name):
    """更新连接配置"""
    valid, error = validate_connection_name(name)
    if not valid:
        return jsonify({'error': error}), 400
    
    data = request.json
    config_content = data.get('config')
    
    if not config_content:
        return jsonify({'error': '配置内容不能为空'}), 400
    
    existing = wm.get_connection(name)
    if not existing:
        return jsonify({'error': '连接不存在'}), 404
    
    if isinstance(config_content, dict):
        valid, error = validate_wireguard_config(config_content)
        if not valid:
            return jsonify({'error': error}), 400
    
    success, result = wm.update_connection(name, config_content)
    if success:
        logger.info(f"更新了连接配置: {name}")
        return jsonify({
            'message': result,
            'timestamp': __import__('datetime').datetime.now().isoformat()
        })
    return jsonify({'error': result}), 400

@app.route('/api/v1/connections/<name>', methods=['DELETE'])
@log_error
def delete_connection(name):
    """删除连接"""
    valid, error = validate_connection_name(name)
    if not valid:
        return jsonify({'error': error}), 400
    
    existing = wm.get_connection(name)
    if not existing:
        return jsonify({'error': '连接不存在'}), 404
    
    success, result = wm.delete_connection(name)
    if success:
        logger.info(f"删除了连接: {name}")
        return jsonify({
            'message': result,
            'timestamp': __import__('datetime').datetime.now().isoformat()
        })
    return jsonify({'error': result}), 400

@app.route('/api/v1/connections/<name>/connect', methods=['POST'])
@log_error
def connect(name):
    """连接WireGuard"""
    valid, error = validate_connection_name(name)
    if not valid:
        return jsonify({'error': error}), 400
    
    connection = wm.get_connection(name)
    if not connection:
        return jsonify({'error': '连接不存在'}), 404
    
    logger.info(f"正在连接: {name}")
    success, message = wm.connect(name)
    if success:
        return jsonify({
            'message': message,
            'connection': name,
            'timestamp': __import__('datetime').datetime.now().isoformat()
        })
    return jsonify({'error': message}), 500

@app.route('/api/v1/connections/<name>/disconnect', methods=['POST'])
@log_error
def disconnect(name):
    """断开WireGuard连接"""
    valid, error = validate_connection_name(name)
    if not valid:
        return jsonify({'error': error}), 400
    
    connection = wm.get_connection(name)
    if not connection:
        return jsonify({'error': '连接不存在'}), 404
    
    logger.info(f"正在断开连接: {name}")
    success, message = wm.disconnect(name)
    if success:
        return jsonify({
            'message': message,
            'connection': name,
            'timestamp': __import__('datetime').datetime.now().isoformat()
        })
    return jsonify({'error': message}), 500

@app.route('/api/v1/connections/<name>/status', methods=['GET'])
@log_error
def get_connection_status(name):
    """获取连接状态"""
    valid, error = validate_connection_name(name)
    if not valid:
        return jsonify({'error': error}), 400
    
    status = wm.get_connection_status(name)
    if status.get('connected'):
        for peer in status.get('peers', []):
            if peer['transfer']['rx']:
                peer['transfer']['rx_formatted'] = wm.format_bytes(peer['transfer']['rx'])
            if peer['transfer']['tx']:
                peer['transfer']['tx_formatted'] = wm.format_bytes(peer['transfer']['tx'])
    
    return jsonify({
        'status': status,
        'timestamp': __import__('datetime').datetime.now().isoformat()
    })

@app.route('/api/v1/connections/import', methods=['POST'])
@log_error
def import_config():
    """导入配置文件"""
    if 'file' not in request.files:
        return jsonify({'error': '没有上传文件'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400
    
    if not file.filename.endswith('.conf'):
        return jsonify({'error': '只支持 .conf 文件'}), 400
    
    success, result = wm.import_config(file)
    if success:
        logger.info(f"导入了配置文件: {result.get('name')}")
        return jsonify({
            'message': '配置导入成功',
            'connection': result,
            'timestamp': __import__('datetime').datetime.now().isoformat()
        }), 201
    return jsonify({'error': result}), 400

@app.route('/api/v1/connections/<name>/export', methods=['GET'])
@log_error
def export_config(name):
    """导出配置文件"""
    valid, error = validate_connection_name(name)
    if not valid:
        return jsonify({'error': error}), 400
    
    connection = wm.get_connection(name)
    if not connection:
        return jsonify({'error': '连接不存在'}), 404
    
    config_data = connection.get('config', {})
    config_lines = []
    
    if 'Interface' in config_data:
        config_lines.append('[Interface]')
        for key, value in config_data['Interface'].items():
            config_lines.append(f'{key} = {value}')
    
    if 'Peer' in config_data:
        if isinstance(config_data['Peer'], dict):
            config_lines.append('\n[Peer]')
            for key, value in config_data['Peer'].items():
                config_lines.append(f'{key} = {value}')
        elif isinstance(config_data['Peer'], list):
            for peer in config_data['Peer']:
                config_lines.append('\n[Peer]')
                for key, value in peer.items():
                    config_lines.append(f'{key} = {value}')
    
    config_content = '\n'.join(config_lines)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.conf', delete=False) as f:
        f.write(config_content)
        temp_path = f.name
    
    return send_file(
        temp_path,
        as_attachment=True,
        download_name=f'{name}.conf',
        mimetype='text/plain'
    )

@app.errorhandler(404)
def not_found(e):
    return jsonify({
        'error': 'API 端点不存在',
        'status': 'error',
        'path': request.path
    }), 404

@app.errorhandler(500)
def internal_error(e):
    logger.error(f"Internal server error: {str(e)}")
    return jsonify({
        'error': '服务器内部错误',
        'status': 'error'
    }), 500

@app.route('/api/v1/stats/connections', methods=['GET'])
@log_error
def get_connection_stats():
    """获取连接统计"""
    stats = wm.history.get_all_stats()
    return jsonify({
        'stats': stats,
        'timestamp': __import__('datetime').datetime.now().isoformat()
    })

@app.route('/api/v1/stats/connections/<connection_name>', methods=['GET'])
@log_error
def get_single_connection_stats(connection_name):
    """获取单个连接的统计"""
    valid, error = validate_connection_name(connection_name)
    if not valid:
        return jsonify({'error': error}), 400
    
    stats = wm.history.get_connection_stats(connection_name)
    return jsonify({
        'stats': stats,
        'timestamp': __import__('datetime').datetime.now().isoformat()
    })

@app.route('/api/v1/stats/history', methods=['GET'])
@log_error
def get_history():
    """获取连接历史"""
    limit = request.args.get('limit', 50, type=int)
    limit = min(limit, 200)
    history = wm.history.get_recent_history(limit)
    return jsonify({
        'history': history,
        'count': len(history),
        'timestamp': __import__('datetime').datetime.now().isoformat()
    })

@app.route('/api/v1/stats/history', methods=['DELETE'])
@log_error
def clear_history():
    """清除连接历史"""
    connection_name = request.args.get('connection')
    wm.history.clear_history(connection_name)
    return jsonify({
        'message': '历史记录已清除',
        'timestamp': __import__('datetime').datetime.now().isoformat()
    })

@app.route('/api/v1/backups', methods=['GET'])
@log_error
def list_backups():
    """列出所有备份"""
    connection_name = request.args.get('connection')
    backups = wm.backup.list_backups(connection_name)
    return jsonify({
        'backups': backups,
        'count': len(backups),
        'timestamp': __import__('datetime').datetime.now().isoformat()
    })

@app.route('/api/v1/backups/<connection_name>/restore', methods=['POST'])
@log_error
def restore_backup(connection_name):
    """恢复备份"""
    valid, error = validate_connection_name(connection_name)
    if not valid:
        return jsonify({'error': error}), 400
    
    data = request.json or {}
    timestamp = data.get('timestamp')
    
    config_content = wm.backup.restore(connection_name, timestamp)
    if config_content is None:
        return jsonify({'error': '备份不存在或无法恢复'}), 404
    
    config_path = os.path.join(wm.base_path, f'{connection_name}.conf')
    with open(config_path, 'w') as f:
        f.write(config_content)
    
    logger.info(f"恢复了连接 {connection_name} 的备份")
    return jsonify({
        'message': '备份恢复成功',
        'timestamp': __import__('datetime').datetime.now().isoformat()
    })

@app.route('/api/v1/backups/<connection_name>/<timestamp>', methods=['DELETE'])
@log_error
def delete_backup(connection_name, timestamp):
    """删除备份"""
    valid, error = validate_connection_name(connection_name)
    if not valid:
        return jsonify({'error': error}), 400
    
    success = wm.backup.delete_backup(connection_name, timestamp)
    if success:
        return jsonify({
            'message': '备份已删除',
            'timestamp': __import__('datetime').datetime.now().isoformat()
        })
    return jsonify({'error': '备份不存在'}), 404

if __name__ == '__main__':
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)
