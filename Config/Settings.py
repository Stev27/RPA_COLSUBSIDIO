# config/Settings.py

import os
from dotenv import load_dotenv
from pathlib import Path
#from Config.init_config import in_config

# Cargar .env
load_dotenv()

# Ruta base del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent

def get_env_variable(key: str, required: bool = True):
    value = os.getenv(key)

    if required and not value:
        raise EnvironmentError(f"La variable '{key}' no está definida en .env")

    return value



# Configuración del proceso
PROCESO_CONFIG = {
    'DIAS_ESPERA_LIBERACION': 2,
    'HORA_LIMITE_ENVIO': '11:45',
    'ReIntentos': 3,
    'TIMEOUT_SAP': 30
}

# ========= CONFIG SAP ==========
SAP_CONFIG = {
    "user": get_env_variable("SAP_USUARIO"),
    "password": get_env_variable("SAP_PASSWORD"),
}

CADENA_CONFIG={
    "usuario":get_env_variable("CADENA_USUARIO"),
    "contrasena":get_env_variable("CADENA_CONTRASENA"),
    "ruta":get_env_variable("CADENA_RUTA")
}

# ========= CONEXION BASE DE DATOS ==========
DB_CONFIG = {
    "host": get_env_variable("SERVERDB"),
    "Database": get_env_variable("NAMEDB"),
    "user": get_env_variable("USERDB"),
    "password": get_env_variable("PASSWORDDB"),    
}


# ========= CONFIG EMAIL ==========
CONFIG_EMAIL = {
    "smtp_server": get_env_variable("EMAIL_SMTP_SERVER"),
    "smtp_port": get_env_variable("EMAIL_SMTP_PORT"),
    "email": get_env_variable("EMAIL_USER"),
    "password": get_env_variable("EMAIL_PASSWORD"),  # IMPORTANTE: Cambiar por variable de entorno en producción
}

SCHEMA = {
    "Schema": get_env_variable("SCHEMA")
}



class Paths:
    # 1. Obtenemos la raíz desde el .env
    # Si no existe en el .env, usa la carpeta actual como fallback
    ROOT = Path(os.getenv("ROOT_PATH", os.getcwd()))

    # 2. Definimos las subcarpetas de forma relativa
    # ¡Aquí es donde ocurre la magia de la escalabilidad!
    AUDIT      = ROOT / "Audit"
    LOGS       = AUDIT / "Logs"
    SCREENSHOTS = AUDIT / "Screenshots"
    TEMP       = ROOT / "Temp"
    INSUMO     = ROOT / "Insumo"
    RESULTADO  = ROOT / "Resultado"
    XMLS       = INSUMO / "XMLs"

    # 3. Archivos específicos
    EXCEL_PARAMETROS = INSUMO / "ParametrosRIGO.xlsx"
    EXCEL_CORREOS    = INSUMO / "EnvioCorreos.xlsx"

    @classmethod
    def init_dirs(cls):
        """Crea todas las carpetas automáticamente si no existen"""
        for attr, value in cls.__dict__.items():
            if isinstance(value, Path):
                value.mkdir(parents=True, exist_ok=True)