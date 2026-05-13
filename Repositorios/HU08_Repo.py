from sqlalchemy import text

class HU08Repository:
    def __init__(self, engine):
        self.engine = engine

    def ejecutar_merge_estrategias(self):
        """Ejecuta el MERGE masivo entre la tabla temporal y la maestra."""
        sql = """
            MERGE [PagoArriendos].[EstrategiasDeLiberacion] AS Target
            USING [Temp_Estrategias] AS Source
            ON (Target.[Doc.compr.] = Source.[Doc.compr.])
            WHEN MATCHED AND (Target.[Status Lib] <> Source.[Status Lib] OR Target.[Estr.] <> Source.[Estr.]) THEN
                UPDATE SET 
                    Target.[Status Lib] = Source.[Status Lib],
                    Target.[Estr.] = Source.[Estr.],
                    Target.[EstadoNotificacion] = CASE 
                        WHEN Target.[EstadoNotificacion] IN ('EnviadoL', 'Escalado') THEN Target.[EstadoNotificacion]
                        WHEN Source.[Status Lib] = 'L' AND Target.[CorreoArrendatarios] = 1 THEN 'EnviadoL'
                        WHEN Source.[Status Lib] = 'L' AND Target.[CorreoArrendatarios] = 0 THEN 'Pendiente'
                        ELSE 'Pendiente'
                    END,
                    Target.[FechaActualizacion] = GETDATE(),
                    Target.[ContadorEnvio] = CASE
                        WHEN Target.[EstadoNotificacion] IN ('EnviadoL', 'Escalado') THEN Target.[ContadorEnvio]
                        ELSE 0
                    END
            WHEN NOT MATCHED THEN
                INSERT ([Doc.compr.], [Fecha doc.], [Acreedor], [Nombre 1], [Creado], 
                        [Estr.], [Status Lib], [Precio neto],[FechaActualizacion],[EstadoNotificacion],[ContadorEnvio],[CorreoArrendatarios])
                VALUES (Source.[Doc.compr.], Source.[Fecha doc.], Source.[Acreedor], Source.[Nombre 1], Source.[Creado],
                        Source.[Estr.], Source.[Status Lib], Source.[Precio neto], GETDATE(),'Pendiente', 0, 0);
        """
        with self.engine.connect() as conn:
            conn.execute(text(sql))
            conn.commit()

    def actualizar_estado_notificacion(self, ids, nuevo_estado):
        """Actualiza el estado de una lista de IDs."""
        ids_str = ", ".join([f"'{i}'" for i in ids])
        sql = f"""
            UPDATE [PagoArriendos].[EstrategiasDeLiberacion]
            SET EstadoNotificacion = :estado, 
                FechaActualizacion = GETDATE(),
                ContadorEnvio = ContadorEnvio + 1
            WHERE [Doc.compr.] IN ({ids_str})
        """
        with self.engine.connect() as conn:
            conn.execute(text(sql), {"estado": nuevo_estado})
            conn.commit()