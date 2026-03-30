import logging
import traceback
from datetime import datetime
from functools import wraps
from flask import jsonify

logger = logging.getLogger(__name__)

class APIError(Exception):
    status_code = 500
    
    def __init__(self, message: str, status_code: int = None, field: str = None):
        super().__init__()
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.field = field
    
    def to_dict(self):
        return {
            'error': self.message,
            'status': 'error',
            'timestamp': datetime.now().isoformat(),
            'field': self.field
        }

class ValidationError(APIError):
    status_code = 400

class NotFoundError(APIError):
    status_code = 404

class ConflictError(APIError):
    status_code = 409

class InternalError(APIError):
    status_code = 500

def setup_logging(log_file: str = None, level: int = logging.INFO):
    """配置日志"""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    handlers = [logging.StreamHandler()]
    
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=level,
        format=log_format,
        handlers=handlers
    )

def log_error(func):
    """错误日志装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except APIError as e:
            logger.warning(f"API Error: {e.message} (field: {e.field})")
            return jsonify(e.to_dict()), e.status_code
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {str(e)}")
            logger.error(traceback.format_exc())
            return jsonify({
                'error': '服务器内部错误',
                'status': 'error',
                'timestamp': datetime.now().isoformat(),
                'detail': str(e) if logger.level <= logging.DEBUG else None
            }), 500
    return wrapper

def log_request(func):
    """请求日志装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        from flask import request
        logger.info(f"Request: {request.method} {request.path}")
        return func(*args, **kwargs)
    return wrapper
