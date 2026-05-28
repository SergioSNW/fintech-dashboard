import os

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'your_secret_key')
    DATABASE_URI = os.getenv('DATABASE_URI', 'sqlite:///fintech_dashboard.db')
    
    