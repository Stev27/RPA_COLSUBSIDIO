
# RIGO – Repositorios/ControlHU.py

import traceback

from Config.Database import Database
from sqlalchemy import text

db= Database()



class ControlHURepository:

        
    def consultar_estado(self, nombre_hu: str):
        """
        Consulta si la HU está activa (1) o inactiva (0)
        """
        query = text("SELECT Activa FROM PagoArriendos.ControlHU WHERE NombreHU = :nombre")
        with db.engine.connect() as connection:
            result = connection.execute(query, {"nombre": nombre_hu}).fetchone()
            # Si existe el registro devuelve el valor, si no, devuelve 0 (inactiva)
            return result[0] if result else 0

    @staticmethod
    def upsert_control_hu(hu_id: int, nombre_hu: str, estado: int, activa: int, maquina: str):
        """
        Inserta o actualiza la HU
        """
        query = """
        MERGE PagoArriendos.ControlHU as target
        USING (SELECT ? AS HU) AS source
        ON target.hu = source.HU
        WHEN MATCHED THEN
            UPDATE SET
                Estado = ?,
                Activa = ?,
                Maquina = ?,
                FechaActualizacion = SYSDATETIME()
        WHEN NOT MATCHED THEN
            INSERT (HU, NombreHU, Estado, Activa, Maquina)
            VALUES (?, ?, ?, ?, ?);
        """
        db= Database() # <-- Stev: cambiar a self.db = db para usar la instancia que se pasa al crear el repo, en vez de crear una nueva conexión cada vez.
        #db = db

        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                query,
                (
                    hu_id,
                    estado,
                    activa,
                    maquina,
                    hu_id,
                    nombre_hu,
                    estado,
                    activa,
                    maquina
                )
            )
            conn.commit()
            
    def ActualizarEstadoHU(self,iHuId: int, iNombreHU: str, estado: int, activa: int, maquina: str) -> bool:
        """
        Inicializa el repositorio con un esquema específico.

        Args:
            schema (str): Nombre del esquema (ej. 'GestionSolped'). 
                          Si es None, se utiliza el valor por defecto schemadb.
        """
        query = """
        MERGE PagoArriendos.ControlHU AS target
        USING (SELECT ? AS HU) AS source
        ON target.HU = source.HU
        WHEN MATCHED THEN
            UPDATE SET
                NombreHU = ?,
                Estado = ?,
                Activa = ?,
                Maquina = ?,
                FechaActualizacion = CAST(GETDATE() AS DATE)
        WHEN NOT MATCHED THEN
            INSERT (HU, NombreHU, Estado, Activa, Maquina, FechaActualizacion) 
            VALUES (?, ?, ?, ?, ?,CAST(GETDATE() AS DATE));
        """
        
        with db.get_connection() as conn:
            try:
                cursor = conn.cursor()
                cursor.execute(
                    query,
                    (
                        iHuId,
                        iNombreHU,
                        estado,
                        activa,
                        maquina,
                        iHuId,
                        iNombreHU,
                        estado,
                        int(activa),
                        maquina
                    )
                )
                conn.commit()
                return True
            except Exception as e:
                print(f"Error al actualizar el estado de HU: {e} - {traceback.format_exc()}")
                return False