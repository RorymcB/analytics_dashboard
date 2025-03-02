from dotenv import load_dotenv
import os
import logging

load_dotenv()  # Load .env variables into environment

apikeys = {
    "chatgpt": os.getenv("CHATGPT_API_KEY"),
    "alpha_vantage": os.getenv("ALPHA_VANTAGE_API_KEY")
}

# Email Settings
MAIL_SERVER = "smtp.gmail.com"
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USERNAME = os.getenv("MAIL_USERNAME")  # Your email
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")  # Your email password
MAIL_DEFAULT_SENDER = "noreply@yourdomain.com"

# MySQL Database Config
DB_USER = "dashboard_user"
DB_PASSWORD = "securepassword"
DB_HOST = "localhost"
DB_NAME = "dashboard_db"

# MySQL
SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")

#sqlite
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
print(BASE_DIR)
SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/data/dashboard_dblite.db")
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Configure logging to also print to console
# logging.basicConfig(
#     filename="app.log",
#     level=logging.DEBUG,
#     format="%(asctime)s - %(levelname)s - %(message)s",
#     handlers=[
#         logging.FileHandler("app.log"),  # ✅ Log to file
#         logging.StreamHandler()  # ✅ Log to console
#     ]
# )
# Configure logging correctly
logging.basicConfig(
    level=logging.DEBUG,  # ✅ Set log level
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("app.log"),  # ✅ Log to file
        logging.StreamHandler()  # ✅ Log to console
    ]
)