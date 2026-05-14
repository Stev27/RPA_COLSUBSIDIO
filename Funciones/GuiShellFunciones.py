# ============================================
# Función Local: validacionME53N
# Autor: Paula Sierra Steven Navarro- NetApplications
# Descripcion: Ejecuta ME5A y exporta archivo TXT según estado.
# Ultima modificacion: 24/11/2025
# Propiedad de Colsubsidio
# Cambios: Ajustado Funciones para Arriendos 
# ============================================

#import win32com.client
#import traceback
import pandas as pd
import re
import time
import os
import pyperclip
import datetime
from Funciones.ConexionSAP import ConexionSAP
from Config.init_config import in_config
from Config.Database import Database
import logging
logger = logging.getLogger(__name__)


def esperar_sap_listo(session, timeout=10):
    """
    Espera hasta que la sesión de SAP GUI no esté ocupada (session.Busy es False).

    Args:
        session: La sesión activa de SAP GUI.
        timeout (int): Tiempo máximo de espera en segundos.

    Raises:
        TimeoutError: Si SAP sigue ocupado después del tiempo de espera.
    """
    inicio = time.time()

    while time.time() - inicio < timeout:
        try:
            if not session.Busy:
                return True
        except  Exception as e:
            logger.warning(f"Error al verificar estado de SAP: {e}")
            pass
        time.sleep(0.2)

    raise TimeoutError("SAP GUI no terminó de cargar (session.Busy)")



def AbrirTransaccion(session, transaccion):
    """
    session: objeto de SAP GUI
    transaccion: transaccion a buscar
    Realiza la busqueda de la transaccion requerida
    Args:  
        session: La sesión activa de SAP GUI.
        transaccion: La transacción a abrir en formato string.

    Raises:
        Exception: Si ocurre un error al abrir la transacción.
       
    """

    logger.info(f"Abrir Transaccion {transaccion}")

    try:
        
        # Validar sesion SAP
        if session is None:
            logger.error("Sesion SAP no disponible")
            raise Exception("Sesion SAP no disponible")

        # Abrir transaccion dinamica
        session.findById("wnd[0]/tbar[0]/okcd").text = transaccion
        session.findById("wnd[0]").sendVKey(0)
        time.sleep(1)

        logger.info(f"Transaccion {transaccion} abierta")
        return True
    except Exception as e:
        logger.exception(f"Error en AbrirTransaccion: {e}")
        return False
    
def LeerTXT_SAP_Universal(path: str) -> pd.DataFrame:
    """
    Parser universal para archivos TXT exportados desde SAP ALV con pipes.
    Diseñado para RPA productivo.
    
    Args:
        path (str): La ruta al archivo TXT exportado desde SAP ALV.
        
    Returns:
        pd.DataFrame: El DataFrame con los datos parseados.    
    """
  

    if not os.path.exists(path):
        raise FileNotFoundError(f"No existe archivo SAP: {path}")

    # --- 1. Leer archivo con fallback encoding ---
    lineas = []
    for enc in ("latin-1", "cp1252", "utf-8"):
        try:
            with open(path, "r", encoding=enc) as f:
                lineas = [linea.rstrip("\n") for linea in f]
            break
        except UnicodeDecodeError:
            continue

    if not lineas:
        raise ValueError("Archivo SAP vacío o no legible")

    # --- 2. Filtrar solo líneas de tabla SAP ---
    lineas_tabla = []
    for linea in lineas:
        if not linea.startswith("|"):
            continue
        if set(linea.replace("|", "").strip()) == {"-"}:
            continue
        lineas_tabla.append(linea)

    if not lineas_tabla:
        raise ValueError("No se detectó tabla SAP válida")

    # --- 3. Unificar multiline SAP ---
    filas = []
    buffer = None
    pipe_ref = None

    for linea in lineas_tabla:
        pipes = linea.count("|")

        if pipe_ref is None:
            pipe_ref = pipes
            buffer = linea
            continue

        if pipes == pipe_ref:
            if buffer:
                filas.append(buffer)
            buffer = linea
        else:
            buffer += linea[1:]

    if buffer:
        filas.append(buffer)

    # --- 4. Limpiar filas ---
    data = []
    for f in filas:
        partes = [p.strip() for p in f.split("|")]
        if partes and partes[0] == "":
            partes.pop(0)
        if partes and partes[-1] == "":
            partes.pop()

        # eliminar fila de totales SAP (*)
        if partes and partes[0] == "*":
            continue

        if partes:
            data.append(partes)

    if len(data) < 2:
        raise ValueError("Tabla SAP sin encabezado o sin datos")

    encabezado = data[0]
    cuerpo = data[1:]

    # --- 5. Ajustar longitud filas ---
    ancho = len(encabezado)
    cuerpo_ok = []

    for fila in cuerpo:
        if len(fila) > ancho:
            fila = fila[:ancho]
        elif len(fila) < ancho:
            fila = fila + [""] * (ancho - len(fila))
        cuerpo_ok.append(fila)

    df = pd.DataFrame(cuerpo_ok, columns=[c.strip() for c in encabezado])

    # --- 6. Eliminar encabezados repetidos en medio ---
    df = df[df.iloc[:, 0] != encabezado[0]]

    return df.reset_index(drop=True)

def FiltrarArrendatariosCompletos(df = pd.DataFrame()) -> pd.DataFrame:
    """
    Solo mantiene a los Arrendatarios (Acreedor) cuyas OCs 
    están TODAS en estado 'L' o 'P'. Si hay alguna en 'B', se descarta el grupo.
    
    Args: df (pd.DataFrame): DataFrame con al menos las columnas 'Acreedor' y 'Status Lib'.
    Returns: pd.DataFrame: DataFrame filtrado con solo los arrendatarios que cumplen la condición.
    
    """
    # 1. Aseguramos que no haya espacios en blanco que arruinen la comparación
    df['Status Lib'] = df['Status Lib'].astype(str).str.strip()

    # 2. Definimos la condición de éxito por fila: ¿Es L o es P?
    # Esto devuelve True si es L o P, y False si es B (o cualquier otra cosa)
    df['StatusPermitido'] = df['Status Lib'].isin(['L', 'P'])

    # 3. Agrupamos por Acreedor y aplicamos el validador "ALL" (Todos)
    # Si un Acreedor tiene 10 filas y una sola es 'B', el 'all' devolverá False para todas las filas de ese Acreedor.
    df['AptoParaEnvio'] = df.groupby('Acreedor')['StatusPermitido'].transform('all')

    # 4. Filtramos los que pasaron la prueba
    df_para_envio = df[df['AptoParaEnvio']].copy()
    
    # --- LOG DE SEGUIMIENTO ---
    nits_excluidos = df[~df['AptoParaEnvio']]['Acreedor'].unique()
    if len(nits_excluidos) > 0:
        #logger.debug(f"EXCLUSION: Los siguientes NITs tienen OCs bloqueadas (B) o pendientes: {list(nits_excluidos)}")
        pass

    # Limpieza de columnas auxiliares antes de retornar o subir a DB
    return df_para_envio.drop(columns=['StatusPermitido', 'AptoParaEnvio'])



def impimmirdf(df: pd.DataFrame):
        
        #print(type(df))
        # print("Columnas obtenidas del df de la base de datos:")
        print(df.columns.tolist())
        # print("Columnas obtenidas del list(df):")
        # print(list(df))
        print("Columnas obtenidas del df.head():")
        print(df.head())
        #print(df.to_string())

        # print("Columnas obtenidas del  df.info()")
        # print(df.info())

def fomatodf(df: pd.DataFrame):
        """
        darle formato a los data frame 
        """
        # Limpiar espacios en los nombres de las columnas
        df.columns = [re.sub(r'\s+', ' ', str(col)).strip() for col in df.columns]
 
        # Identificar y renombrar duplicados
        cols = pd.Series(df.columns)
        for i in cols[cols.duplicated()].unique():
            cols[cols == i] = [f"{i}_{j}" if j != 0 else i for j in range(sum(cols == i))]
        df.columns = cols # Ahora las columnas se llamarán "Nombre 1" (la primera) y "Nombre 1_1" (la segunda)
        # 1. Quitamos filas donde Borrado es "L"
        # 2. Quitamos filas donde Status Lib sea NaN (nulo)
        # 3. Quitamos filas donde Status Lib esté vacío (espacios en blanco)

        df = df[
            (df['Borrado'] != 'L') & 
            (df['Status Lib'].notna()) & 
            (df['Status Lib'].astype(str).str.strip() != '')
        ].copy()
        
        # Renombramos columnas clave para cambios de layaout, pero solo si existen en el DataFrame original
        df.rename(columns={
            #"Fecha doc.":"Fecha doc.",
            "Prc.neto":"Precio neto",
            }, inplace=True)
                
        # Filtramos solo las columnas que existan en el DataFrame original #2
        columnas_interes = ['Fecha doc.','Acreedor','Nombre 1','Creado','Estr.', 'Doc.compr.', 'Status Lib', 'Precio neto', ]
        columnas_validas = [col for col in columnas_interes if col in df.columns]
        df = df[columnas_validas].copy() # Aseguramos que solo trabajamos con las columnas que realmente existen en el DataFrame original
        # Convertir 'Precio neto' a numérico, manejando comas y puntos
        df['Precio neto'] = pd.to_numeric(df['Precio neto'].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False),errors='coerce').fillna(0)

        # campo Acreedor se convierte a texto, es donde se encuentre el nit 
        df['Acreedor'] = df['Acreedor'].astype(str).str.strip()

        # Agregar la fecha y hora actual, Usamos format para que SQL lo reconozca como DATETIME fácilmente
        df['FechaActualizacion'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Limpia espacios en blanco alrededor de los textos
        df['Fecha doc.'] = df['Fecha doc.'].str.strip()

        # Convierte a fecha, y lo que no sea fecha lo vuelve NaT (Not a Time)
        df['Fecha doc.'] = pd.to_datetime(df['Fecha doc.'], dayfirst=True, errors='coerce')

        # Elimina filas donde la fecha sea indispensable y haya quedado vacía
        df = df.dropna(subset=['Fecha doc.'])
        
        # Agregar el estado de notificación inicial, Lo marcamos como 'Pendiente' para que el módulo de correo sepa qué procesar
        df['EstadoNotificacion'] = 'Pendiente'

        # Agrupar por 'Doc.compr.' y sumar 'Precio neto'
        df = df.groupby("Doc.compr.") .agg({  
                "Fecha doc.": "first",
                "Acreedor": "first",
                "Nombre 1": "first",
                "Creado": "first",
                "Estr.": "first", 
                "Status Lib": "first",
                "Precio neto": "sum", # Sumamos el precio neto para cada documento de compra  // STEV : se deja fuera del alcance por ahora.
                "FechaActualizacion": "first",
                "EstadoNotificacion": "first",
                #"Material": list
                #"CorreoArrendatarios":"first",
                # "Fecha Lib": "first",
                # "Usuario Li": "first",
                # "Fecha Lib.": "first",
                # "Usuario Li": "first"
            }).reset_index()
        
        df['ContadorEnvio']= 0
        df['CorreoArrendatarios'] = 0  

        return df

def descargadataestliberacion (session):
    """
    Pasos en SAP para descargar la data de estrategias de Liberacio, deja un TXT, en el file server.
    """

    try :
        db= Database()
        engine = db.get_engine()
        sap = ConexionSAP() 
        
        # sap = ConexionSAP(
        #     SAP_CONFIG.get('user'),
        #     SAP_CONFIG.get('password'),
        #     in_config('SapMandante'),
        #     in_config('SapIdioma'),
        #     in_config('SapRutaLogon'),
        #     in_config('SapSistema')
            
        # )
        if not session:
            return
        session = sap.conectar_SAP()
        AbrirTransaccion(session, "ZMM_68")
        ahora = datetime.datetime.now() # Obtenemos la fecha y hora actual
        fecha_formateada = ahora.strftime("%d.%m.%Y") # Ejemplo de salida: 01.01.2026
        primer_dia_anio = datetime.date(ahora.year, 1, 1)    # Crear una fecha usando el año actual, mes 1, día 1
        primer_dia_anio = primer_dia_anio.strftime("%d.%m.%Y")  # Ejemplo de salida: 01.01.2026

        session.findById("wnd[0]/usr/ctxtR_BEDAT-LOW").text = primer_dia_anio #Primer dia del año actual 
        session.findById("wnd[0]/usr/ctxtR_BEDAT-HIGH").text = fecha_formateada #Fecha actual
        
        # Grupo de Organización de Compras
        grupoOrgCompras = pd.read_sql_table("Config_Compras", engine, schema="PagoArriendos")
        grupoOrgCompras = grupoOrgCompras['CodigoOrg'].tolist()
        logger.debug(grupoOrgCompras)
        #grupoOrgCompras = ["OC03","OC30","OC02"]# Esto lo puedes traer de la tabla de la base de datos db, parametros 
        texto_sap = "\r\n".join(grupoOrgCompras)
        pyperclip.copy(texto_sap) # copia al portapapeles la informacion 
        session.findById("wnd[0]/usr/btn%_R_EKORG_%_APP_%-VALU_PUSH").press() # Abre Ventana org de Compras 
        session.findById("wnd[1]/tbar[0]/btn[16]").press() #Boton basura, borrar datos 
        session.findById("wnd[1]/tbar[0]/btn[24]").press() #Boton pegar datos 
        session.findById("wnd[1]/tbar[0]/btn[8]").press() # Ejecutar Filtro 
              
        # Responsable
        #session.findById("wnd[0]/usr/txtR_ERNAM-LOW").text = "FERNCAMS" #Responsable ERIIGUZV
        responsable = pd.read_sql_table("Responsables", engine, schema="PagoArriendos")
        responsable = responsable['Responsable'].tolist()
        #responsable = ["FERNCAMS","ERIIGUZV"] # Esto lo puedes traer de la tabla de la base de datos db, parametros 
        texto_sap = "\r\n".join(responsable)
        pyperclip.copy(texto_sap)
        session.findById("wnd[0]/usr/btn%_R_ERNAM_%_APP_%-VALU_PUSH").press() # Abre ventana responsable de la OC
        session.findById("wnd[1]/tbar[0]/btn[16]").press() # Boton basura, borrar datos
        session.findById("wnd[1]/tbar[0]/btn[24]").press()
        session.findById("wnd[1]/tbar[0]/btn[8]").press()
               
        
        # Ejecutar búsqueda
        session.findById("wnd[0]/tbar[1]/btn[8]").press() #Ejecutar búsqueda

        # Guardar resultados en txt
        rutaGuardar = fr"{in_config('PathTemp')}\HU08"
        session.findById("wnd[0]/tbar[1]/btn[45]").press()
        session.findById("wnd[1]/tbar[0]/btn[0]").press()
        session.findById("wnd[1]/usr/ctxtDY_PATH").text = rutaGuardar
        session.findById("wnd[1]/usr/ctxtDY_FILENAME").text = "EstrategiasDeLiberacion.txt"
        session.findById("wnd[1]/tbar[0]/btn[0]").press()

    except  Exception as e:
        logger.exception(f"Error en la descarga de data desde SAP Estrategias de liberacion {e}")

