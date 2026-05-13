
#from Config.Database import Database
from Repositorios.ControlHU import ControlHURepository # Asumiendo que existe el repo
from HU.HU00_Despliegue import Reutilizables
# Imports de las Historias de Usuario
from HU.HU01_Ejemplo1 import HU01_Ejemplo1
from HU.HU02_Ejemplo2 import HU02_Ejemplo2
from HU.HU01_EgresosCuentasPorPagar import Facturas
# ... (importa las demás HU que necesites)

# Configuración de Logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    HU08: Estrategias de liberación de ordenes de compra
    HU07: Valida la creación y liberación de ordenes de compra
    HU01: Ingresa cadena descarga xml y hace la comparación de valores en sap
    hu04: valida tema de las facturas
    Hu03: se encargan de validar las facturas, valida que el monto este cargado y la factura este creada, 
    si no esta creada es culpa del proovedor y si no esta paga es culpa del cliente
    hu02: Validcion de facturas, por medio del hu03 en casos de error:
    hu06: Validacion de presupuesto
    hu05: Cargar reportes a la bse de datos
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

    # Ejemplo HU01
    if validar_ejecucion(repo_control, "HU01_EgresosCuentasPorPagar"):
        hu01 = Facturas()
        hu01.ejecutar()
        Reutilizables.cerrar_chrome()
    
    # if validar_ejecucion(repo_control, "HU08_EstrategiasDeLiberacion"):
    #     hu01 = Facturas()
    #     hu01.ejecutar()
    #     Reutilizables.cerrar_chrome()  
        


    logger.info("Fin de la ejecución del Orquestador RIGO.")
    
    
    

     
    # ejecucionHu04=HU04_Auditoria()
    # ejecucionHu04.ejecutar()
    # Reutilizables.cerrar_sap()

    # fecha_hora = datetime.now().strftime('%Y%m%d')
    # nombre_archivo=rf"Informe_Auditoria_Facturacion_{fecha_hora}.xlsx"

    # ejecucionHu03=HU03_DiagnosticoCierre()
    # ejecucionHu03.procesar_desde_excel(nombre_archivo)

    # ejecucionHu02=HU02_VerificacionDiaria()
    # ejecucionHu02.ejecutar()
    # Reutilizables.cerrar_sap()
    
    # PruebaHU6 = HU06_ProyeccionCostos()
    # PruebaHU6.ejecutar()
    # Reutilizables.cerrar_sap()
    
    # ruta = r"\\192.168.50.169\RPA_RIGO_GestionPagodeArrendamientos\Resultados\Reporte_HU03_Cierre_20260116_1306.xlsx"
    # HU05_CargueSQL.ejecutar_cargue_desde_excel(ruta)