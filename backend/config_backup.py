import os
import shutil
import json
from datetime import datetime
from typing import List, Optional

class ConfigBackup:
    def __init__(self, data_dir: str, max_backups: int = 10):
        self.data_dir = data_dir
        self.backup_dir = os.path.join(data_dir, 'backups')
        os.makedirs(self.backup_dir, exist_ok=True)
        self.max_backups = max_backups
    
    def backup(self, config_name: str, config_content: str) -> str:
        """创建配置文件备份"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f'{config_name}_{timestamp}.conf'
        backup_path = os.path.join(self.backup_dir, backup_name)
        
        with open(backup_path, 'w') as f:
            f.write(config_content)
        
        self._cleanup_old_backups(config_name)
        
        metadata = self._load_metadata()
        if config_name not in metadata:
            metadata[config_name] = []
        
        metadata[config_name].append({
            'timestamp': timestamp,
            'backup_file': backup_name,
            'created_at': datetime.now().isoformat()
        })
        self._save_metadata(metadata)
        
        return backup_path
    
    def restore(self, config_name: str, timestamp: str = None) -> Optional[str]:
        """恢复配置文件"""
        metadata = self._load_metadata()
        
        if config_name not in metadata:
            return None
        
        backups = metadata[config_name]
        
        if timestamp:
            backup_info = next((b for b in backups if b['timestamp'] == timestamp), None)
        else:
            backup_info = backups[-1] if backups else None
        
        if not backup_info:
            return None
        
        backup_path = os.path.join(self.backup_dir, backup_info['backup_file'])
        
        if os.path.exists(backup_path):
            with open(backup_path, 'r') as f:
                return f.read()
        return None
    
    def list_backups(self, config_name: str = None) -> List[dict]:
        """列出所有备份"""
        metadata = self._load_metadata()
        
        if config_name:
            return metadata.get(config_name, [])
        
        all_backups = []
        for name, backups in metadata.items():
            for backup in backups:
                backup['config_name'] = name
                all_backups.append(backup)
        
        return sorted(all_backups, key=lambda x: x['created_at'], reverse=True)
    
    def delete_backup(self, config_name: str, timestamp: str) -> bool:
        """删除备份"""
        metadata = self._load_metadata()
        
        if config_name not in metadata:
            return False
        
        backups = metadata[config_name]
        backup_info = next((b for b in backups if b['timestamp'] == timestamp), None)
        
        if not backup_info:
            return False
        
        backup_path = os.path.join(self.backup_dir, backup_info['backup_file'])
        if os.path.exists(backup_path):
            os.remove(backup_path)
        
        metadata[config_name] = [b for b in backups if b['timestamp'] != timestamp]
        self._save_metadata(metadata)
        
        return True
    
    def _cleanup_old_backups(self, config_name: str):
        """清理旧备份"""
        metadata = self._load_metadata()
        
        if config_name not in metadata:
            return
        
        backups = metadata[config_name]
        
        if len(backups) > self.max_backups:
            backups_to_delete = backups[:-self.max_backups]
            
            for backup in backups_to_delete:
                backup_path = os.path.join(self.backup_dir, backup['backup_file'])
                if os.path.exists(backup_path):
                    os.remove(backup_path)
            
            metadata[config_name] = backups[-self.max_backups:]
            self._save_metadata(metadata)
    
    def _load_metadata(self) -> dict:
        """加载元数据"""
        metadata_file = os.path.join(self.backup_dir, 'metadata.json')
        if os.path.exists(metadata_file):
            with open(metadata_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_metadata(self, metadata: dict):
        """保存元数据"""
        metadata_file = os.path.join(self.backup_dir, 'metadata.json')
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
