"""Genera los gráficos del análisis a partir de data/salidas_2025_limpio.csv"""
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams.update({"font.family": "DejaVu Sans", "axes.spines.top": False, "axes.spines.right": False,
                     "axes.titleweight": "bold", "axes.titlesize": 13})
AZUL, GRIS, NARANJA = "#1F4E79", "#9AA5B1", "#D9822B"
d = pd.read_csv("data/salidas_2025_limpio.csv", parse_dates=["fecha"])

# 1. Salidas por mes
m = d.groupby("mes").size()
fig, ax = plt.subplots(figsize=(8, 4))
colores = [NARANJA if v == m.max() else AZUL for v in m]
ax.bar([x[5:] for x in m.index], m.values, color=colores)
for i, v in enumerate(m.values):
    ax.text(i, v + 1, v, ha="center", fontsize=9)
ax.set_title("Salidas de cuadrillas por mes (2025)")
ax.set_xlabel("Mes (octubre incompleto: datos hasta el 20)")
ax.set_ylabel("Salidas")
fig.tight_layout(); fig.savefig("graficos/01_salidas_por_mes.png", dpi=150); plt.close(fig)

# 2. Trabajo por sistema
s = d["sistema"].value_counts().sort_values()
fig, ax = plt.subplots(figsize=(8, 4))
ax.barh(s.index, s.values, color=AZUL)
for i, v in enumerate(s.values):
    ax.text(v + 2, i, f"{v} ({v/len(d):.0%})", va="center", fontsize=9)
ax.set_title("¿Dónde se concentra el trabajo? Salidas por sistema")
ax.set_xlim(0, s.max() * 1.2)
fig.tight_layout(); fig.savefig("graficos/02_salidas_por_sistema.png", dpi=150); plt.close(fig)

# 3. Departamentos: % del total y % de fallas eléctricas
dep = d.dropna(subset=["departamento"]).groupby("departamento").agg(
    salidas=("id_salida", "count"),
    electricas=("sistema", lambda x: x.isin(["Tablero y protecciones", "Falla eléctrica / cableado"]).sum()))
dep = dep[dep.salidas >= 20].sort_values("salidas")
fig, ax = plt.subplots(figsize=(8, 5))
ax.barh(dep.index, dep.salidas - dep.electricas, color=AZUL, label="Otras causas")
ax.barh(dep.index, dep.electricas, left=dep.salidas - dep.electricas, color=NARANJA, label="Tablero / falla eléctrica")
ax.set_title("Salidas por departamento y peso de lo eléctrico")
ax.legend(frameon=False, loc="lower right")
fig.tight_layout(); fig.savefig("graficos/03_departamentos.png", dpi=150); plt.close(fig)

# 4. Pozos reincidentes
p = d.dropna(subset=["id_pozo"]).groupby("id_pozo").size().sort_values(ascending=False).head(10).sort_values()
fig, ax = plt.subplots(figsize=(8, 4))
ax.barh(p.index, p.values, color=GRIS)
ax.barh(p.index[-3:], p.values[-3:], color=NARANJA)
for i, v in enumerate(p.values):
    ax.text(v + 0.2, i, v, va="center", fontsize=9)
ax.set_title("Los 10 pozos con más salidas en el año")
ax.set_xlabel("Salidas (ene–oct 2025)")
fig.tight_layout(); fig.savefig("graficos/04_pozos_reincidentes.png", dpi=150); plt.close(fig)
print("4 gráficos generados")
