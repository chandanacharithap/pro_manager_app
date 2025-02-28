import os

class Config:
    """Configuration settings for the Flask application."""

    # Database Configuration
    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root:root@localhost/project_management"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Flask Secret Key (for sessions, CSRF protection, etc.)
    SECRET_KEY = os.getenv("SECRET_KEY", "your_default_secret_key")

    # OpenAI API Key (Loaded from Environment Variables)
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    # Task Assignment Settings
    TASK_ASSIGNMENT_INTERVAL = 60  # Time in seconds for periodic task assignment

    # Debug Mode
    DEBUG = True
