# ================================
# GestionSOLPED – HU01: 
# Ruta Relativa: HU/HU01_Ejemplo1.py
# Autor: Steven Navarro  - NetApplications
# Descripcion: Ejemplo de HU 
# Ultima modificacion: 05/13/2026
# Propiedad de Colsubsidio
# Cambios:
# - 
# - 
# - 
# ================================


from pathlib import Path

from Config.Settings import SAP_CONFIG
from Config.init_config import in_config
from Config.Database import Database
from Funciones.ConexionSAP import ConexionSAP
from Funciones.ControlHU import ControlHU


import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG) # DEBUG para desarrollo, INFO para producción  


db = Database()



class HU01_Ejemplo1:
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
        self.rutaTemporal=in_config('PathTemp')
        self.carpeta=self.rutaTemporal+"\\HU07"
        self.rutaHU07=Path(self.carpeta)
        self.sesion = None
        #self.nombreTabla = "BaseMedicamentoslimpio"
        self.nombreTabla = "BaseArriendoMedicamentos" 

    def ejecutar(self):
        
        nombre_hu = "HU01_Ejemplo1"
        try:
            logger.info("Inicio de Ejecucion HU01_Ejemplo1 ")
                                  
            logger.debug(f" Aqui va la logica de la historia de Usuario HU1_Ejemplo {self.nombreTabla}...")
            
            self.sap.iniciar_sesion_sap()
            
            breakpoint()
            
            
            logger.info("fin de Ejecucion HU01_Ejemplo1")
            ControlHU(nombre_hu, 100) #control HU exitoso
            
        except Exception as e:
            logger.exception(f"Falla crítica en HU07: {e}")
            ControlHU(nombre_hu, 99) #contol HU con error critico
            
            
    
