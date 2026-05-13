import xml.etree.ElementTree as ET
from pathlib import Path

class LectorFacturaXML:
    """Clase para extraer datos de facturas electrónicas (UBL 2.1)"""
    
    def __init__(self, ruta_xml):
        self.ruta = Path(ruta_xml)
        # Namespaces estándar de la DIAN para UBL 2.1
        self.ns = {
            'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
            'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2',
            'ad': 'urn:oasis:names:specification:ubl:schema:xsd:AttachedDocument-2'
        }

    def obtener_datos(self):
        """Retorna NIT y Número de Factura"""
        try:
            tree = ET.parse(self.ruta)
            root = tree.getroot()
            
            # 1. Obtener NIT (SenderParty -> ID)
            # En tu XML es 900631450
            nit_raw = root.find(".//cac:SenderParty/cac:PartyTaxScheme/cbc:CompanyID", self.ns)
            nit = nit_raw.text if nit_raw is not None else ""
            
            # 2. Obtener Prefijo + Número (ParentDocumentID)
            # En tu XML es FRE25233
            factura_raw = root.find(".//cbc:ParentDocumentID", self.ns)
            factura = factura_raw.text if factura_raw is not None else ""
            
            return {
                "nit": nit,
                "factura": factura
            }
        except Exception as e:
            raise Exception(f"Error al procesar el archivo XML: {str(e)}")