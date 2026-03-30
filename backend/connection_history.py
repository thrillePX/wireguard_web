import os
import json
from datetime import datetime
from typing import List, Dict, Optional

class ConnectionHistory:
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        self.history_file = os.path.join(data_dir, 'connection_history.json')
        self._ensure_history_file()
    
    def _ensure_history_file(self):
        """确保历史文件存在"""
        if not os.path.exists(self.history_file):
            with open(self.history_file, 'w') as f:
                json.dump([], f)
    
    def _load_history(self) -> List[Dict]:
        """加载历史记录"""
        try:
            with open(self.history_file, 'r') as f:
                return json.load(f)
        except Exception:
            return []
    
    def _save_history(self, history: List[Dict]):
        """保存历史记录"""
        with open(self.history_file, 'w') as f:
            json.dump(history, f, indent=2)
    
    def record_connect(self, connection_name: str, timestamp: datetime = None):
        """记录连接开始"""
        if timestamp is None:
            timestamp = datetime.now()
        
        history = self._load_history()
        
        record = {
            'type': 'connect',
            'connection': connection_name,
            'start_time': timestamp.isoformat(),
            'end_time': None,
            'duration': None
        }
        
        history.insert(0, record)
        
        self._save_history(history)
        return record
    
    def record_disconnect(self, connection_name: str, timestamp: datetime = None):
        """记录连接断开"""
        if timestamp is None:
            timestamp = datetime.now()
        
        history = self._load_history()
        
        for record in history:
            if record['type'] == 'connect' and \
               record['connection'] == connection_name and \
               record['end_time'] is None:
                record['end_time'] = timestamp.isoformat()
                start = datetime.fromisoformat(record['start_time'])
                duration = (timestamp - start).total_seconds()
                record['duration'] = duration
                break
        
        self._save_history(history)
    
    def get_connection_stats(self, connection_name: str = None) -> Dict:
        """获取连接统计"""
        history = self._load_history()
        
        if connection_name:
            records = [r for r in history if r['connection'] == connection_name]
        else:
            records = history
        
        total_connects = len([r for r in records if r['type'] == 'connect'])
        completed_connects = len([r for r in records if r['type'] == 'connect' and r['end_time']])
        
        total_duration = sum(r['duration'] for r in records if r.get('duration'))
        avg_duration = total_duration / completed_connects if completed_connects > 0 else 0
        
        last_connect = None
        for r in records:
            if r['type'] == 'connect':
                last_connect = r
                break
        
        return {
            'connection': connection_name,
            'total_connects': total_connects,
            'completed_connects': completed_connects,
            'total_duration': total_duration,
            'total_duration_formatted': self._format_duration(total_duration),
            'avg_duration': avg_duration,
            'avg_duration_formatted': self._format_duration(avg_duration),
            'last_connect': last_connect['start_time'] if last_connect else None
        }
    
    def get_all_stats(self) -> List[Dict]:
        """获取所有连接统计"""
        history = self._load_history()
        connections = set(r['connection'] for r in history)
        return [self.get_connection_stats(conn) for conn in connections]
    
    def get_recent_history(self, limit: int = 50) -> List[Dict]:
        """获取最近的连接历史"""
        history = self._load_history()
        return history[:limit]
    
    def _format_duration(self, seconds: float) -> str:
        """格式化时长"""
        if seconds < 60:
            return f"{int(seconds)}秒"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            secs = int(seconds % 60)
            return f"{minutes}分{secs}秒"
        elif seconds < 86400:
            hours = int(seconds / 3600)
            minutes = int((seconds % 3600) / 60)
            return f"{hours}时{minutes}分"
        else:
            days = int(seconds / 86400)
            hours = int((seconds % 86400) / 3600)
            return f"{days}天{hours}时"
    
    def clear_history(self, connection_name: str = None):
        """清除历史记录"""
        if connection_name:
            history = self._load_history()
            history = [r for r in history if r['connection'] != connection_name]
            self._save_history(history)
        else:
            self._save_history([])
