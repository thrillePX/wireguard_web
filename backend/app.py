from flask import Flask, request, jsonify, send_file
from wireguard_manager import WireGuardManager
from config import Config
import os
import tempfile

app = Flask(__name__)
app.config.from_object(Config)

wm = WireGuardManager(base_path=app.config['WG_PATH'])

@app.route('/api/config/path', methods=['GET'])
def get_config_path():
    """获取配置文件路径"""
    return jsonify({'path': wm.base_path})

@app.route('/api/config/path', methods=['POST'])
def set_config_path():
    """设置配置文件路径"""
    data = request.json
    new_path = data.get('path', Config.DEFAULT_WG_PATH)
    global wm
    wm = WireGuardManager(base_path=new_path)
    return jsonify({'path': new_path, 'message': '配置路径已更新'})

@app.route('/api/connections', methods=['GET'])
def list_connections():
    """列出所有连接"""
    connections = wm.list_connections()
    return jsonify(connections)

@app.route('/api/keys/generate', methods=['POST'])
def generate_keys():
    """生成 WireGuard 密钥对"""
    private_key, public_key = wm.generate_keypair()
    return jsonify({
        'privateKey': private_key,
        'publicKey': public_key
    })

@app.route('/api/keys/preshared', methods=['POST'])
def generate_preshared_key():
    """生成 WireGuard 预共享密钥"""
    psk = wm.generate_preshared_key()
    return jsonify({
        'presharedKey': psk
    })

@app.route('/api/keys/derive', methods=['POST'])
def derive_public_key():
    """从私钥派生公钥"""
    data = request.json
    private_key = data.get('privateKey')
    
    if not private_key:
        return jsonify({'error': '私钥不能为空'}), 400
    
    public_key = wm.derive_public_key(private_key)
    if public_key:
        return jsonify({
            'publicKey': public_key
        })
    return jsonify({'error': '无效的私钥'}), 400

@app.route('/api/connections/all-status', methods=['GET'])
def get_all_status():
    """获取所有连接的状态"""
    status = wm.get_all_status()
    for conn in status['connections']:
        if conn['transfer']['rx']:
            conn['transfer']['rx_formatted'] = wm.format_bytes(conn['transfer']['rx'])
        if conn['transfer']['tx']:
            conn['transfer']['tx_formatted'] = wm.format_bytes(conn['transfer']['tx'])
    return jsonify(status)

@app.route('/api/connections/<name>', methods=['GET'])
def get_connection(name):
    """获取单个连接详情"""
    connection = wm.get_connection(name)
    if not connection:
        return jsonify({'error': '连接不存在'}), 404
    
    if connection['connected'] and 'status' in connection:
        for peer in connection['status'].get('peers', []):
            if peer['transfer']['rx']:
                peer['transfer']['rx_formatted'] = wm.format_bytes(peer['transfer']['rx'])
            if peer['transfer']['tx']:
                peer['transfer']['tx_formatted'] = wm.format_bytes(peer['transfer']['tx'])
    
    return jsonify(connection)

@app.route('/api/connections', methods=['POST'])
def add_connection():
    """添加新连接"""
    data = request.json
    name = data.get('name')
    config_content = data.get('config')
    
    if not name or not config_content:
        return jsonify({'error': '名称和配置内容不能为空'}), 400
    
    success, result = wm.add_connection(name, config_content)
    if success:
        return jsonify(result)
    return jsonify({'error': result}), 400

@app.route('/api/connections/<name>', methods=['PUT'])
def update_connection(name):
    """更新连接配置"""
    data = request.json
    config_content = data.get('config')
    
    if not config_content:
        return jsonify({'error': '配置内容不能为空'}), 400
    
    success, result = wm.update_connection(name, config_content)
    if success:
        return jsonify({'message': result})
    return jsonify({'error': result}), 400

@app.route('/api/connections/<name>', methods=['DELETE'])
def delete_connection(name):
    """删除连接"""
    success, result = wm.delete_connection(name)
    if success:
        return jsonify({'message': result})
    return jsonify({'error': result}), 400

@app.route('/api/connections/<name>/connect', methods=['POST'])
def connect(name):
    """连接WireGuard"""
    success, message = wm.connect(name)
    if success:
        return jsonify({'message': message})
    return jsonify({'error': message}), 500

@app.route('/api/connections/<name>/disconnect', methods=['POST'])
def disconnect(name):
    """断开WireGuard连接"""
    success, message = wm.disconnect(name)
    if success:
        return jsonify({'message': message})
    return jsonify({'error': message}), 500

@app.route('/api/connections/<name>/status', methods=['GET'])
def get_connection_status(name):
    """获取连接状态"""
    status = wm.get_connection_status(name)
    if status.get('connected'):
        for peer in status.get('peers', []):
            if peer['transfer']['rx']:
                peer['transfer']['rx_formatted'] = wm.format_bytes(peer['transfer']['rx'])
            if peer['transfer']['tx']:
                peer['transfer']['tx_formatted'] = wm.format_bytes(peer['transfer']['tx'])
    return jsonify(status)

@app.route('/api/connections/import', methods=['POST'])
def import_config():
    """导入配置文件"""
    if 'file' not in request.files:
        return jsonify({'error': '没有上传文件'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400
    
    success, result = wm.import_config(file)
    if success:
        return jsonify(result)
    return jsonify({'error': result}), 400

@app.route('/api/connections/<name>/export', methods=['GET'])
def export_config(name):
    """导出配置文件"""
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

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        'status': 'healthy',
        'wg_path': wm.base_path,
        'platform': 'Darwin' if __import__('platform').system() == 'Darwin' else 'Linux'
    })

if __name__ == '__main__':
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)
