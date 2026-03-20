# config.py
import os
from datetime import timedelta
#  ultima nd
class Config:
    SECRET_KEY = '3054=HitM'
    MYSQL_HOST = 'localhost'
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = 'contracena623'
    MYSQL_DB = 'beneficios'
    SESSION_TYPE = 'filesystem'
    SESSION_TYPE = 'filesystem'
  
   
    
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    BACKUP_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backups')
    
    @staticmethod
    def init_app(app):
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(Config.BACKUP_FOLDER, exist_ok=True)