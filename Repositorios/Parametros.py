from Config.Database import Database
from Config.Settings import SCHEMA

import logging
logger = logging.getLogger(__name__)




class ParametrosRepository:

    @staticmethod
    def cargar_parametros() -> dict:
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()

        cursor.execute(f"""
            SELECT Nombre, Valor
            FROM {SCHEMA["Schema"]}.parametros
        """)

        config = {}
        for nombre, valor in cursor.fetchall():
            config[nombre] = valor

        cursor.close()
        conn.close()

        return config
