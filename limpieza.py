"""Limpieza y categorización del parte diario de trabajos 2025 (pozos de agua potable, Tucumán).

Entrada : Excel original, hoja 'SALIDAS 2025' (no se incluye en el repositorio).
Salida  : data/salidas_2025_limpio.csv (anonimizado, listo para SQL / Power BI).
"""
import re
import sys
import pandas as pd

ARCHIVO = sys.argv[1] if len(sys.argv) > 1 else "SALIDAS_2025_-_2.xlsx"
SALIDA = "data/salidas_2025_limpio.csv"

# --- 1. Lectura: el encabezado real está en la fila 6; los datos empiezan en la fila 8 ---
raw = pd.read_excel(ARCHIVO, sheet_name="SALIDAS 2025", header=None)
df = raw.iloc[7:, [0, 1, 2, 3, 4, 9, 10, 11]].copy()
df.columns = ["fecha", "localidad", "comuna", "departamento", "tarea", "id_pozo", "resultado_texto", "agente"]

# --- 2. La fecha solo figura en la primera fila de cada día: se completa hacia abajo ---
df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce").ffill()

# --- 3. Filas sin tarea, o con datos personales (teléfonos) en lugar de tarea ---
for c in ["localidad", "comuna", "departamento", "tarea", "id_pozo", "resultado_texto", "agente"]:
    df[c] = df[c].astype("string").str.strip().str.upper()
df = df[df["tarea"].notna()]
df = df[~df["tarea"].str.contains(r"\d{3}-?\d{5,}", regex=True)]          # teléfonos
df = df[df["fecha"].notna()].copy()
df["id_salida"] = range(1, len(df) + 1)   # id estable, asignado antes de excluir filas

# --- 4. Normalización de departamentos ---
df["departamento"] = df["departamento"].replace(
    {"TAFI VIEJO": "TAFÍ VIEJO", "TAFI DEL VALLE": "TAFÍ DEL VALLE", "J.B. ALBERDI": "ALBERDI",
     "RIO CHICO": "RÍO CHICO", "SOSA VERONICA": pd.NA})
df["id_pozo"] = df["id_pozo"].replace({"-": pd.NA})
# Una salida sin departamento corresponde a un traslado de repuestos de un vehículo (no es tarea de pozos): se excluye
df = df[df["departamento"].notna()].copy()

# --- 5. Categorización de las ~450 formas de escribir la tarea ---
def sistema(t):
    reglas = [
        ("Cloración", r"CLORACION"),
        ("Tablero y protecciones", r"TABLERO|PROTECC|AUTOMATIC|ARRANCADOR|CONTACTOR|GUARDAMOTOR"),
        ("Falla eléctrica / cableado", r"ELECTRIC|ENERGIA|CABLE|FASE"),
        ("Red, tanque y reserva", r"TANQUE|CISTERNA|RESERVA|PRESION|RED "),
        ("Cabezal, cañerías y pozo", r"CABEZAL|FILTRO|CAÑO|PESCA|SOPLADO|TAPON|POZO|ENSAYO|AFORO|PRUEBA|NIVELES|ENDOSCOPIA|PERFORACION"),
        ("Bomba / equipo de bombeo", r"BOMBA|BOMBEO|EQUIPO"),
    ]
    for nombre, patron in reglas:
        if re.search(patron, t):
            return nombre
    return "Inspección general / otros"

def tipo(t):
    if re.search(r"RECAMBIO|CAMBIO|INSTALACION|ISNTALACION|REEMPLAZO|REMPLAZO|COLOCACION|EXTRACCION|PUESTA EN FUNCIONAMIENTO|ARMADO", t):
        return "Recambio / instalación"
    if re.search(r"REPARACION|REACONDICION|SELLADO|REGULACION|CORRECCION|MANTENIMIENTO|LIMPIAR|SOPLADO|PESCA", t):
        return "Reparación"
    if re.search(r"INSP|INPE|ISNP|CONTROL|ENSAYO|PRUEBA|AFORO|RELEV|VERIFIC|MEDICION|NIVELES|ENDOSCOPIA|FALLA", t):
        return "Inspección / diagnóstico"
    return "Otros"

df["sistema"] = df["tarea"].map(sistema)
df["tipo_trabajo"] = df["tarea"].map(tipo)

# --- 5b. Correcciones manuales de clasificación (revisadas una por una) ---
corr = pd.read_csv("data/correcciones_manuales.csv", dtype=str).fillna("")
for _, fila in corr.iterrows():
    idx = df["id_salida"] == int(fila["id_salida"])
    if fila["sistema"]:
        df.loc[idx, "sistema"] = fila["sistema"]
    if fila["tipo_trabajo"]:
        df.loc[idx, "tipo_trabajo"] = fila["tipo_trabajo"]

# --- 6. Resultado: banderas simples a partir del texto libre ---
r = df["resultado_texto"].fillna("")
df["resultado"] = "Sin dato"
df.loc[r.str.len() > 2, "resultado"] = "Otro"
df.loc[r.str.contains("CORRECTAMENTE|SOLUCIONADO|FUNCIONANDO"), "resultado"] = "Funcionando"
df.loc[r.str.contains("QUEMAD"), "resultado"] = "Bomba quemada"
df.loc[r.str.contains("DAÑO ELECTRICO|FUERA DE SERVICIO"), "resultado"] = "Daño eléctrico / fuera de servicio"
df["espera_compra_comuna"] = r.str.contains("COMUNA ADQUIERA|DELEGADO|COMUNA|CUANDO LA").astype(int)

# --- 7. Anonimización de operarios ---
codigos = {a: f"Agente {i+1}" for i, a in enumerate(df["agente"].dropna().value_counts().index)
           if a not in ("SOVER", "SIN SALIDA")}
df["agente"] = df["agente"].map(codigos)

# --- 8. Variables derivadas ---
df["mes"] = df["fecha"].dt.to_period("M").astype(str)
df["dia_semana"] = df["fecha"].dt.day_name()

cols = ["id_salida", "fecha", "mes", "dia_semana", "localidad", "comuna", "departamento", "id_pozo",
        "tarea", "tipo_trabajo", "sistema", "resultado", "espera_compra_comuna", "agente"]
df[cols].to_csv(SALIDA, index=False, encoding="utf-8-sig")
print(f"{len(df)} salidas limpias -> {SALIDA}")
print(df["tipo_trabajo"].value_counts(), df["sistema"].value_counts(), df["resultado"].value_counts(), sep="\n\n")
