# ================================
# RIGO – Funciones/ControlHU.py
# Autor: Mateo Naranjo -Steven Navarro - Santiago Pinzon - NetApplications
# Descripción: Función para controlar el estado de las Historias de Usuario (HUs) en la base de datos.
# Ultima modificacion: 23/04/2026
# Propiedad de Colsubsidio
# Cambios:
# - 23/04/2026: Se agregó manejo de errores robusto y logging detallado (Stev)
# ================================


import socket
import re
#from Config.Database import Database
from Repositorios.ControlHU import ControlHURepository

# Configuramos un logger para este módulo específico

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG) # DEBUG para desarrollo, INFO para producción  

def ExtraerHU(iNombreHU: str) -> int:
    match = re.match(r'HU(\d+)', iNombreHU.upper())
    if not match:
        raise ValueError(f"Nombre de HU inválido: {iNombreHU}")
    return int(match.group(1))

def ControlHU(iNombreHU: str, estado: int):
    """
    Actualiza el estado de la HU en la base de datos.
    :param db: Instancia de la conexión a DB (necesaria para el Repo)
    :param iNombreHU: Nombre (ej. 'HU08_Estrategias')
    :param estado: Código de estado (0=Inicia, 99=Error, 100=Finaliza)
    """

    try:
        iHuId = ExtraerHU(iNombreHU)
        
        # Lógica de actividad
        # 0 = Iniciando (Activa) | 100 o 99 = Finalizado (Inactiva en ejecución)
        activa = 1 if estado not in (99, 100) else 0
        
        maquina = socket.gethostname()

        # Instanciamos el repositorio pasándole el motor de DB
        repo = ControlHURepository()
        exito = repo.ActualizarEstadoHU(iHuId=iHuId, iNombreHU=iNombreHU, estado=estado, activa=activa, maquina=maquina)
        

        if exito:
            logger.debug(f"Stev[ok] Estado HU {iHuId} actualizado a {estado} (Activa: {activa})")
        else:
            logger.warning(f"Stev[!] No se pudo actualizar el estado de la HU {iHuId} en DB")

    except Exception as e:
        logger.exception(f"Stev[-] Error en ControlHU para {iNombreHU}: {str(e)}")