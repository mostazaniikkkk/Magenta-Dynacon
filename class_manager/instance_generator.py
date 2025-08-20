# # Genera e inserta una instancia según nombre de tabla y dict de datos.
# # Requiere: models = generate_classes(engine)  (dict {table_name: Class})

def create_instance(models: dict, session, table_name: str, data: dict):
    # # data debe ser un dict con campos válidos para la tabla
    if not isinstance(data, dict) or not data:
        raise ValueError("data debe ser un dict con al menos un campo.")

    # # Resuelve la clase por nombre exacto de tabla; fallback case-insensitive
    Model = models.get(table_name) or models.get(table_name.lower()) or models.get(table_name.upper())
    if Model is None:
        # # Mapa lower por si el caller es creativo con mayúsculas
        lower_map = {k.lower(): v for k, v in models.items()}
        Model = lower_map.get(table_name.lower())
        if Model is None:
            raise KeyError(f"Tabla '{table_name}' no encontrada en models.")

    # # Crea la instancia usando el CRUDMixin de la clase dinámica
    obj = Model.create(session, **data)
    return obj