import time
import threading
from pywinauto import Desktop

def _interaccion_ventana_windows(ruta_archivo, titulo, logger):
    """
    Función interna para manejar la ventana de Windows (Hilo secundario).
    """
    logger.info("Hilo secundario: Vigilando ventana 'Import file'...")
    desktop = Desktop(backend="win32")
    ventana = desktop.window(title_re=titulo)
    inicio = time.time()
    
    while (time.time() - inicio) < 20: # Timeout de 20 segundos
        try:
            # Buscamos la ventana por título (Regex insensible a mayúsculas)
            if ventana.exists():
                ventana.set_focus()
                time.sleep(1)
                
                # Escribir ruta y dar Enter
                edit_box = ventana.child_window(class_name="Edit")
                edit_box.set_edit_text(ruta_archivo)
                time.sleep(0.5)
                edit_box.type_keys('{ENTER}')
                
                logger.info("Hilo secundario: Ventana de Windows procesada.")
                return True
        except Exception as e:
            logger.warning(f"Error en hilo secundario: {e}")
        time.sleep(0.5)
    return False

def cargar_archivo_gos(sesion, num_oc, ruta_archivo, logger):
    """
    Función principal para cargar anexos vía GOS en ME22N.
    """
    try:
        # 1. Navegar y cargar OC
        # sesion.findById("wnd[0]/tbar[0]/okcd").text = "/n"
        sesion.findById("wnd[0]").sendVKey(0)
        sesion.findById("wnd[0]/tbar[0]/okcd").text = "ME22N"
        sesion.findById("wnd[0]").sendVKey(0)
        
        sesion.findById("wnd[0]/tbar[1]/btn[17]").press()
        sesion.findById("wnd[1]/usr/subSUB0:SAPLMEGUI:0003/ctxtMEPO_SELECT-EBELN").text = str(num_oc)
        sesion.findById("wnd[1]").sendVKey(0)
        time.sleep(1)

        # Verificar si la OC está bloqueada por otro usuario
        if sesion.findById("wnd[0]/sbar").messagetype == "E":
            logger.error(f"OC {num_oc} bloqueada o con error: {sesion.findById('wnd[0]/sbar').text}")
            return False
        
        titulo = "(?i)Importar.*fichero.*"

        # 2. LANZAR HILO PARA VENTANA DE WINDOWS
        hilo_externo = threading.Thread(target=_interaccion_ventana_windows, args=(ruta_archivo, titulo, logger))
        hilo_externo.daemon = True
        hilo_externo.start()

        # 3. DISPARAR ACCIÓN GOS (Esto congela el código hasta que el hilo termine)
        sesion.findById("wnd[0]/titl/shellcont/shell").pressContextButton("%GOS_TOOLBOX")
        sesion.findById("wnd[0]/titl/shellcont/shell").selectContextMenuItem("%GOS_PCATTA_CREA")

        # 4. MANEJO DE POPUP DE SEGURIDAD 'ALLOW'
        time.sleep(2) 
        if sesion.Children.Count > 1:
            try:
                # Opción A: Botón estándar de SAP Security
                sesion.findById("wnd[1]/usr/btnSPOP-VAROCB1").press()
            except:  # noqa: E722
                try:
                    # Opción B: Botón genérico
                    sesion.findById("wnd[1]/usr/btnBUTTON_1").press()
                except  Exception as e:
                    logger.warning(f"No se pudo cerrar el popup de seguridad automáticamente. {e}")

        # 5. GUARDAR CAMBIOS (Botón diskette)
        sesion.findById("wnd[0]/tbar[0]/btn[11]").press()
        
        logger.info(f"OC {num_oc}: Anexo cargado correctamente.")
        return True

    except Exception as e:
        logger.error(f"Error cargando anexo OC {num_oc}: {e}")
        return False