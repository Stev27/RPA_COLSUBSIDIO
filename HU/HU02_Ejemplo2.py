# ================================
# GestionSOLPED – HU00: DespliegueAmbiente
# Autor: Mateo Naranjo - Steven Navarro - Santiago Pinzon - NetApplications
# Descripcion: Carga parámetros, valida carpetas y prepara entorno
# Ultima modificacion: 28/04/2026
# Propiedad de Colsubsidio
# Cambios:
# - Se agregó la HU08_EstrategiasDeLiberacion con su lógica de negocio completa (Stev)
# - Se implementó el ControlHU con logging detallado y manejo de errores (Stev)
# - Se desarrolló el orquestador en MainPrueba1.py para ejecutar las HU de forma parametrizada (Stev) 
# ================================


import os

import pandas as pd
import datetime

from Config.Settings import SAP_CONFIG
from Config.init_config import in_config
from Funciones.ConexionSAP import ConexionSAP
from Config.Database import Database
from Funciones.ControlHU import ControlHU
from Funciones.GuiShellFunciones import  descargadataestliberacion, fomatodf,FiltrarArrendatariosCompletos,LeerTXT_SAP_Universal
from Funciones.EmailSender import EnviarCorreoPersonalizado
from sqlalchemy import text


import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG) # DEBUG para desarrollo, INFO para producción  

class  HU02_Ejemplo2:
    def __init__(self):
        """
        Inicializa los componentes de conexión y logging.
        """        
        self.sap = ConexionSAP(
            SAP_CONFIG.get('user'),
            SAP_CONFIG.get('password'),
            in_config('SapMandante'),
            in_config('SapIdioma'),
            in_config('SapRutaLogon'),
            in_config('SapSistema')
        )

    def ejecutar(self):
        """
            Método principal para ejecutar la lógica de la HU08.
            Controla el flujo completo: desde la descarga de datos en SAP, procesamiento, actualización en BD y envío de notificaciones.
            Incluye manejo de errores robusto y logging detallado en cada paso.
            TODO: crear funciones auxiliares para cada bloque lógico (descarga, procesamiento, BD, notificaciones) para mejorar la legibilidad y mantenibilidad.
            
        """
        
        try :
            
            nombre_hu = "HU08_EstrategiasDeLiberacion"
            
            db= Database()
            engine = db.get_engine()
            logger.info(f"Inicio de Ejecucion - {nombre_hu}")
            schema = "PagoArriendos"
            
            #TODO: en donde se debe enviar correo de notificacion de inicio HU, en cada HU dentro o fuera de la HU 
            #EnviarNotificacionCorreo(codigoCorreo=1,nombreTarea="Probando db")  #Probando metodos de envio de correo
                               
            descargadataestliberacion (session = self.sap.iniciar_sesion_sap()) # Descarga de SAP la data de la transaccion "ZMM_68"
            
            df = pd.read_sql( "ControlHU", engine, schema = schema )
            
            print(f"{df}")
            logger.debug(f"dataframe de Control HU {df}")
            logger.info(f"Fin de Ejecucion{nombre_hu}")
            ControlHU(nombre_hu, 100)
        
        except Exception as e:
            logger.exception(f"Falla crítica en HU08: {e}")
            ControlHU(nombre_hu, 99)