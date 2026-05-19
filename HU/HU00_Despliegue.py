# ================================
# GestionSOLPED – HU00: DespliegueAmbiente
# Autor: Mateo Naranjo -Steven Navarro - Santiago Pinzon - NetApplications
# Descripcion: Carga parámetros, valida carpetas y prepara entorno
# Ultima modificacion: 16/04/2026
# Propiedad de Colsubsidio
# Cambios:
# - 
# - 
# - 
# ================================


# Asegurar que la raíz del proyecto esté en el path, sin importar desde dónde se ejecute
#sys.path.insert(0, str(Path(__file__).resolve().parent.parent))



import getpass 
import logging
import subprocess
import socket
import json
import os

import pandas as pd

from pathlib import Path
from datetime import datetime,timedelta

from Config.init_config import init_config, in_config
from Config.Database import Database
from Config.Settings import Paths


class Reutilizables:
    """Clase para manejo de ambiente y logging del proyecto"""
    
    def __init__(self, path_proyecto, path_audit, path_logs, path_temp, path_insumo, path_resultado):
        self.path_proyecto = Path(path_proyecto)
        self.path_audit = Path(path_audit)
        self.path_logs = Path(path_logs)
        self.path_temp = Path(path_temp)
        self.path_insumo = Path(path_insumo)
        self.path_resultado = Path(path_resultado)
        
        # Configurar logger
        self._configurar_logger()
    
    def _configurar_logger(self):
        """Configura el sistema de logging"""
        # Crear carpeta de logs si no existe
        self.path_logs.mkdir(parents=True, exist_ok=True)
        maquina = socket.gethostname()
        usuario = getpass.getuser()
        # Nombre de archivo con timestamp
        timestamp = datetime.now().strftime("%Y%m%d")
        log_file = self.path_logs / f"Log_{maquina}_{usuario}_{timestamp}.txt"
        robbot = in_config("CodigoRobot")
        
        # Configuración del logger
        logging.basicConfig(
            level=logging.DEBUG, # Stev:  Cambiar a INFO, para borrar todos los mensajes modo DEBUG
            # FECHA HORA | ESTADO | MENSAJE | CODIGOROBOT | TASKNAME   
            format=rf'%(asctime)s | %(levelname)-2s | %(message)-10s | {robbot} | %(funcName)-20s ',
            #format='%(asctime)s | %(levelname)-8s | %(message)s | RIGO | %(funcName)-20s ',
            datefmt='%Y-%m-%d %H:%M:%S', # Hora militar (00-23)
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()  # También mostrar en consola
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        
        self.logger.debug("=" * 80)
        self.logger.debug("Sistema de logging inicializado")
        self.logger.debug("=" * 80)
        
    
    def crear_carpetas(self):
        """Crea todas las carpetas necesarias para el proyecto"""
        try:
            carpetas = {
                'Proyecto': self.path_proyecto,
                'Auditoría': self.path_audit,
                'Logs': self.path_logs,
                'Temporal': self.path_temp,
                'Insumos': self.path_insumo,
                'Resultados': self.path_resultado
            }
            
            for nombre, carpeta in carpetas.items():
                if not carpeta.exists():
                    carpeta.mkdir(parents=True, exist_ok=True)
                    self.logger.debug(f" Carpeta creada: {nombre} -> {carpeta}")
                else:
                    self.logger.debug(f"Carpeta ya existe: {nombre} -> {carpeta}")
            
            self.logger.debug("Despliegue de ambiente completado exitosamente")
            return True
            
        except Exception as e:
            self.logger.error(f"Error al crear carpetas: {str(e)}", exc_info=True)
            return False
        
    def limpiar_carpeta(self, ruta_carpeta, dias_retencion=365):
        """
        Limpia archivos de una ruta específica que superen los días de antigüedad permitidos.
        :param ruta_carpeta: String o Path de la carpeta a limpiar.
        :param dias_retencion: Int, cantidad de días que se conservarán los archivos.
        """
        try:
            path = Path(ruta_carpeta)
            if not path.exists():
                self.logger.warning(f"La ruta {ruta_carpeta} no existe. Saltando limpieza.")
                return False

            # Calculamos la fecha límite (Hoy - días de retención)
            fecha_limite = datetime.now() - timedelta(days=dias_retencion)
            # Convertimos a timestamp para comparar con el sistema de archivos
            segundos_limite = fecha_limite.timestamp()

            archivos_eliminados = 0
            self.logger.info(f"Iniciando limpieza en {path}. Retencion: {dias_retencion} dias.")

            for archivo in path.glob('*'):
                if archivo.is_file():
                    # st_mtime es la fecha de última modificación (más confiable que creación en Windows)
                    fecha_archivo = archivo.stat().st_mtime
                    
                    if fecha_archivo < segundos_limite:
                        archivo.unlink() # Borrar archivo
                        archivos_eliminados += 1
                        self.logger.debug(f"Eliminado por antiguedad: {archivo.name}")

            self.logger.info(f"Limpieza completada. Se eliminaron {archivos_eliminados} archivos antiguos.")
            return True

        except Exception as e:
            self.logger.exception(f"Error crítico al limpiar la carpeta {ruta_carpeta}: {str(e)}")
            return False
    
    def validar_archivo_existe(self, ruta_archivo):
        """Valida si un archivo existe"""
        archivo = Path(ruta_archivo)
        if archivo.exists():
            self.logger.info(f"Archivo encontrado: {archivo.name}")
            return True
        else:
            self.logger.warning(f"Archivo NO encontrado: {archivo}")
            return False
    
    def get_ruta_insumo(self, nombre_archivo):
        """Obtiene ruta completa de archivo en carpeta insumo"""
        return self.path_insumo / nombre_archivo
    
    def get_ruta_resultado(self, nombre_archivo):
        """Obtiene ruta completa de archivo en carpeta resultado"""
        return self.path_resultado / nombre_archivo
    
    def get_ruta_temp(self, nombre_archivo):
        """Obtiene ruta completa de archivo en carpeta temp"""
        return self.path_temp / nombre_archivo
    
    def cargar_configuracion():
        """Carga parámetros desde la base de datos en un diccionario """
        import logging
        logger = logging.getLogger(__name__)
        
        init_config()
        logger.info("In_config cargado:",in_config("CodigoRobot"), in_config("PathProyecto"))
        #self.logger.info("Configuracion global iniciada")
        
    def cargarParametros(esquema_custom=None):
        """
        Carga parámetros desde el Excel ParametrosRIGO.xlsx a SQL Server.
        - Se le puede pasar un diccionario 'esquema_custom' con los tipos de datos.
        - Si no se pasa 'esquema_custom', intenta leer la hoja '_TiposDatos' del Excel.
        - si no se pasa 'esquema_custom' y no existe la hoja '_TiposDatos', le lee un archivo json Config/esquema_tablas.json  
        - si no existe la tabla en SQL Server se crea con los tipos de datos del diccionario 'esquema_custom' o del archivo json
        - si existe la tabla en SQL Server y no coincide con el esquema de 'esquema_custom' o del archivo json, se actualiza la tabla con los tipos de datos del diccionario 'esquema_custom' o del archivo json  
        """
        import logging
        import pandas as pd
        from sqlalchemy import VARCHAR, Integer, Float, Date, DateTime, Boolean, Numeric, Text
        
        from Config.Settings import SCHEMA
        
        logger = logging.getLogger(__name__)
        # Asumo que db = Database() ya está definido en tu clase/módulo
        db = Database()
        engine = db.get_engine()

        HOJA_TIPOS = "_TiposDatos"
        ruta_excel = rf"{in_config('PathParametrosRIGO')}"
        esquema_destino = SCHEMA["Schema"]

        # --- Mapa de texto → tipo SQLAlchemy ---
        def resolver_tipo(tipo_str: str):
            if not tipo_str or str(tipo_str).strip().upper() in ('', 'NAN', 'NONE'):
                return VARCHAR(length=None)
            t = str(tipo_str).strip().upper()
            if t.startswith('VARCHAR'):
                import re
                match = re.search(r'\((\d+|MAX)\)', t)
                if match:
                    val = match.group(1)
                    return VARCHAR(length=None) if val == 'MAX' else VARCHAR(length=int(val))
                return VARCHAR(length=None)
            elif t in ('INT', 'INTEGER', 'BIGINT', 'SMALLINT'):
                return Integer()
            elif t in ('FLOAT', 'REAL'):
                return Float()
            elif t.startswith('NUMERIC') or t.startswith('DECIMAL'):
                import re
                match = re.search(r'\((\d+),\s*(\d+)\)', t)
                if match:
                    return Numeric(precision=int(match.group(1)), scale=int(match.group(2)))
                return Numeric()
            elif t in ('DATE',):
                return Date()
            elif t in ('DATETIME', 'DATETIME2'):
                return DateTime()
            elif t in ('BIT', 'BOOLEAN', 'BOOL'):
                return Boolean()
            elif t in ('TEXT', 'NTEXT'):
                return Text()
            else:
                return VARCHAR(length=None)

        try:
            logger.debug(f"--- Iniciando despliegue de parametros desde {ruta_excel} ---")

            # 1. Leer TODAS las hojas del Excel
            dict_hojas = pd.read_excel(ruta_excel, sheet_name=None)

            # 2. Definir el mapa de tipos
            mapa_tipos = {} 
            
            if esquema_custom:
                # OPCIÓN A: Usar el diccionario inyectado desde Python/JSON
                logger.debug("Usando esquema de tipos personalizado proporcionado por parámetro.")
                for tabla, columnas in esquema_custom.items():
                    mapa_tipos[tabla] = {}
                    for col, tipo in columnas.items():
                        mapa_tipos[tabla][col] = resolver_tipo(tipo)
                        
            elif HOJA_TIPOS in dict_hojas:
                # OPCIÓN B: Usar la hoja del Excel (Backward compatibility)
                df_tipos = dict_hojas[HOJA_TIPOS].dropna(subset=['Tabla', 'Columna'])
                for _, fila in df_tipos.iterrows():
                    tabla_t = str(fila['Tabla']).strip()
                    col_t   = str(fila['Columna']).strip()
                    tipo_t  = resolver_tipo(fila.get('TipoDato', ''))
                    mapa_tipos.setdefault(tabla_t, {})[col_t] = tipo_t
                logger.debug(f"Hoja '{HOJA_TIPOS}' leida: tipos definidos para {len(mapa_tipos)} tabla(s).")
            else:
                logger.debug("No se definió esquema custom ni se encontró hoja de tipos. Se usará VARCHAR(MAX).")

            hojas_ok, hojas_error = [], []

            for nombre_hoja, df in dict_hojas.items():
                if nombre_hoja == HOJA_TIPOS:
                    continue

                try:
                    df.columns = [str(col).strip() for col in df.columns]

                    # 4. Construir dtype
                    tipos_hoja = mapa_tipos.get(nombre_hoja, {})
                    dtype_final = {
                        col: tipos_hoja.get(col, VARCHAR(length=None))
                        for col in df.columns
                    }

                    # 5. Cargar a SQL Server
                    df.to_sql(
                        name=nombre_hoja,
                        con=engine,
                        schema=esquema_destino,
                        if_exists='replace',
                        index=False,
                        dtype=dtype_final
                    )

                    hojas_ok.append(nombre_hoja)
                    logger.debug(f"  OK: [{esquema_destino}].[{nombre_hoja}] - {len(df)} registros cargados.")

                except Exception as e_hoja:
                    hojas_error.append(nombre_hoja)
                    logger.error(f" Error al cargar hoja '{nombre_hoja}': {e_hoja}")

            logger.debug(f"--- Despliegue finalizado: {len(hojas_ok)} OK | {len(hojas_error)} con error ---")

        except Exception as e:
            logger.exception(f"Error crítico durante el despliegue: {str(e)}")
        
                    
    def cerrar_chrome():
        import logging
        logger = logging.getLogger(__name__)
        try:
            resultado = subprocess.run(["taskkill", "/f", "/im", "chrome.exe"], capture_output=True, text=True)
            
            # Registrar los cierres exitosos (stdout)
            if resultado.stdout:
                logger.debug(resultado.stdout.strip())
                
            # Procesar y filtrar los errores (stderr)
            if resultado.stderr:
                errores = resultado.stderr.strip()
                for error in errores:
                    # Filtramos los errores de permisos (tanto en inglés como en español)
                    if "Access is denied" not in error and "Acceso denegado" not in error:
                        logger.debug(f"[chrome.exe] {error.strip()}")
                
            logger.debug("[+] Chrome gestionado correctamente (ignorando procesos de otros usuarios).")
        except Exception as e:
            logger.exception(f"[-] Error crítico al ejecutar el cierre de Chrome: {e}")

    def cerrar_sap():
        
        import logging
        logger = logging.getLogger(__name__)
        try:
            # Cubrir variantes de SAP GUI
            for proceso in ["saplogon.exe", "saplgpad.exe", "sapgui.exe"]:
                # Ejecutamos taskkill capturando la salida
                resultado = subprocess.run(["taskkill", "/f", "/im", proceso], capture_output=True, text=True)
                
                # Registrar si el cierre fue exitoso (stdout)
                if resultado.stdout:
                    logger.debug(resultado.stdout.strip())
                
                # Procesar y filtrar los errores de "proceso no encontrado" (stderr)
                if resultado.stderr:
                    lineas_error = resultado.stderr.strip().split('\n')
                    for linea in lineas_error:
                        # Si el error NO es porque el proceso no existe, lo logueamos
                        # Esto permite ignorar el mensaje cuando SAP ya está cerrado
                        if "not found" not in linea.lower() and "no se encontró" not in linea.lower():
                            logger.warning(f"[{proceso}] {linea.strip()}")
                            
            logger.debug("[+] Intento de cierre de SAP completado.")
        except Exception as e:
            logger.exception(f"[-] Error crítico al intentar cerrar SAP: {e}")
            
    def cargarInsumosDB():
        """Carga insumos a la base de datos desde la carpeta de insumos en formato Excel"""
        
        import logging
        logger = logging.getLogger(__name__)
        db = Database()
        engine = db.get_engine()
        
        try:
            
            # Ejemplo: cargar una tabla llamada 'Insumos' del esquema 'PagoArriendos'
            RutaExcelInsumo = rf"{in_config("PathInsumo")}\BaseArriendoMedicamentos.xlsx"
            logger.debug(f"Cargando insumos desde: {RutaExcelInsumo}")
            df_insumos = pd.read_excel(RutaExcelInsumo, engine="openpyxl", header=3)  # Ajusta header si tu Excel tiene filas de encabezado diferentes
            
            columnas_interes = [
            "COD FIN",
            "SEDE",
            "No. DE CONTRATO",
            "MTS2 SEGÚN CONTRATO",
            "NIT",
            "ARRENDADOR",
            "NIT FACTURADOR",
            "NOMBRE FACTURADOR",
            "CIUDAD",
            "DEPTO",
            "TIPO",
            "IVA",
            "ORDEN 2025",
            "OBSERVACION DE PAGOS",
            "ENERO",
            "FEBRERO",
            "MARZO",
            "ABRIL",
            "MAYO",
            "JUNIO",
            "JULIO",
            "AGOSTO",
            "SEPTIEMBRE",
            "ACTUBRE",
            "NOVIEMBRE",
            "DICIEMBRE"]
            df_insumos = df_insumos[columnas_interes]
            df_insumos["EstadoRegistro"] = "Pendiente"
            
            df_insumos.rename(columns={
            "COD FIN":"cod_fin",
            "No. DE CONTRATO":"numero_contrato",
            "MTS2 SEGÚN CONTRATO": "mts2",
            "NIT": "nit",
            "NOMBRE FACTURADOR": "nombre_facturador",
            "TIPO": "tipo",
            "IVA": "iva",
            "ORDEN 2025": "orden_2025",
            "OBSERVACION DE PAGOS": "observaciones",
            "ENERO": "enero",
            "FEBRERO": "febrero",
            "MARZO": "marzo",
            "ABRIL": "abril",
            "MAYO": "mayo",
            "JUNIO": "junio",
            "JULIO": "julio",
            "AGOSTO": "agosto",
            "SEPTIEMBRE": "septiembre",
            "ACTUBRE": "octubre",   # Revisar insumo en producion para ajustar "ACTUBRE"
            "NOVIEMBRE": "noviembre",
            "DICIEMBRE": "diciembre"

            }, inplace=True)
                        
            
            df_insumos.to_sql("BaseArriendoMedicamentos", engine, schema="PagoArriendos", if_exists='replace', index=False)
                   
            logger.debug(f"Insumos cargados a la DB desde :{RutaExcelInsumo}")
            return True
            
        except Exception as e:
            logger.error(f"Error al cargar insumos desde DB: {str(e)}")
            return False



# -----------------------------------------------------------------------
# INICIALIZACIÓN AL IMPORTAR: solo configuración y carpetas
# Esto se ejecuta cuando cualquier otro módulo hace: from HU.HU00_Despliegue import ...
# -----------------------------------------------------------------------
Reutilizables.cargar_configuracion()

ambiente = Reutilizables(
    # in_config("PathProyecto"),
    # in_config("PathAudit"),
    # in_config("PathLog"),
    # in_config("PathTemp"),
    # in_config("PathInsumo"),
    # in_config("PathResultado")
    Paths.ROOT,
    Paths.AUDIT,
    Paths.LOGS,
    Paths.TEMP,
    Paths.INSUMO,
    Paths.RESULTADO,
    Paths.TEMP,
)
ambiente.crear_carpetas()
# ambiente.limpiar_carpeta(in_config('PathLog'), int(in_config("LimpiezaLogs"))) # Limpiar Carpeta Logs
# ambiente.limpiar_carpeta(in_config('PathScreenshots'), int(in_config("LimpiezaLogs")))  # Limpiar Carpeta Screenshots

ambiente.limpiar_carpeta(Paths.LOGS, int(in_config("LimpiezaLogs"))) # Limpiar Carpeta Logs
ambiente.limpiar_carpeta(Paths.LOGS, int(in_config("LimpiezaLogs")))  # Limpiar Carpeta Screenshots

mis_tablas_sql = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'Config', 'esquema_tablas.json')


try:
    with open(mis_tablas_sql, 'r', encoding='utf-8') as archivo:
        esquema_custom = json.load(archivo)
        
    logging.debug(f"Esquema cargado correctamente con {len(esquema_custom)} tablas.")
except FileNotFoundError:
    logging.error(f"Error: No se encontró el archivo de esquema en {mis_tablas_sql}")
    esquema_custom = None

Reutilizables.cargarParametros(esquema_custom)
#Reutilizables.limpiar_carpeta_temp() # revisar temporales antes de borrar
Reutilizables.cargarInsumosDB() # Carga insumos a la DB desde Excel (si aplica)
#Reutilizables.cerrar_chrome()
Reutilizables.cerrar_sap()


logging.info("=" * 80)
logging.info("Ambiente preparado. Listo para ejecutar las Historias de Usuario.")
logging.info("=" * 80)


# -----------------------------------------------------------------------
# EJECUCIÓN DIRECTA: sincronización Excel → SQL Server
# Solo se ejecuta si corres este archivo directamente: python HU00_Despliegue.py
# -----------------------------------------------------------------------
if __name__ == "__main__":
    Reutilizables.cargarParametros()



