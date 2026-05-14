
#from Config.Database import Database
from Repositorios.ControlHU import ControlHURepository # Asumiendo que existe el repo
from HU.HU00_Despliegue import Reutilizables
# Imports de las Historias de Usuario
from HU.HU01_Ejemplo1 import HU01_Ejemplo1
from HU.HU02_Ejemplo2 import HU02_Ejemplo2

# ... (importa las demás HU que necesites)

# Configuración de Logging
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG) # DEBUG para desarrollo, INFO para producción  


def validar_ejecucion(repo, nombre_hu):
    """
    Consulta en la tabla ControlHU si la historia debe ejecutarse.
    """
    try:
        # Aquí asumo que tu repositorio tiene un método para obtener el estado
        # Si no lo tienes, puedes hacer un query directo con repo.db.engine
        esta_activa = repo.consultar_estado(nombre_hu) 
        
        if esta_activa == 1:
            logger.info(f" [{nombre_hu}] Activa. Iniciando ejecución...")
            return True
        else:
            logger.warning(f" [{nombre_hu}] Desactivada en ControlHU. Omitiendo.")
            return False
    except Exception as e:
        logger.error(f" Error al consultar ControlHU para {nombre_hu}: {e}")
        return False

if __name__ == "__main__":
    
    """
    Main donde se ejecuta orquestador de Historiar de Usuario 
    
    """
    
    # 1. Inicializar conexión y repositorio de control
    #db = Database()
    repo_control = ControlHURepository()

    # --- FLUJO DE EJECUCIÓN PARAMETRIZADO ---

    # Ejemplo HU02
    if validar_ejecucion(repo_control, "HU02_Ejemplo2"):
        
        #print("Stev Prueba debug")
        hu08 = HU02_Ejemplo2()
        hu08.ejecutar()
        Reutilizables.cerrar_sap()

    # Ejemplo HU01
    if validar_ejecucion(repo_control, "HU01_Ejemplo1"):
        print("Stev Prueba debug")
        hu07 = HU01_Ejemplo1()
        hu07.ejecutar()
        Reutilizables.cerrar_sap()



    logger.info("Fin de la ejecución del Orquestador RIGO.")
    
    
    
