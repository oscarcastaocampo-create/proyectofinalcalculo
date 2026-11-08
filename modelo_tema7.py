"""Proyecto final de Calculo Diferencial - Tema 7.
Modelo didactico radial tipo Poiseuille + cola M/M/1/K para congestion.
Los parametros son ilustrativos y no corresponden a mediciones de una red real.
Requisitos: Python 3.10+, numpy, matplotlib.
Ejecutar: python modelo_tema7.py
"""
from pathlib import Path
import csv
import numpy as np
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent
FIG = OUT / "figuras"
FIG.mkdir(exist_ok=True)

# ---------------- Modelo radial equivalente (adimensional) ----------------
# Ecuacion de la guia: dv/dr = (r/(2 mu)) dP/dz.
# Se define G = -dP/dz > 0; R=1, G=4, mu=1, por lo que v(r)=1-r^2.
R = 1.0
G = 4.0
MU = 1.0
SIGMA_G = 0.20       # incertidumbre estandar asumida (5 %)
SIGMA_MU = 0.05      # incertidumbre estandar asumida (5 %)
SIGMA_R = 0.01       # incertidumbre estandar asumida de r normalizado
r = np.linspace(0.0, R, 101)
v = G / (4.0 * MU) * (R**2 - r**2)
dv = -G * r / (2.0 * MU)
d2v = np.full_like(r, -G / (2.0 * MU))

# Propagacion de incertidumbres independientes de G, mu y r.
dv_dG = (R**2 - r**2) / (4.0 * MU)
dv_dmu = -G * (R**2 - r**2) / (4.0 * MU**2)
dv_dr = -G * r / (2.0 * MU)
sigma_v = np.sqrt((dv_dG * SIGMA_G)**2 + (dv_dmu * SIGMA_MU)**2 + (dv_dr * SIGMA_R)**2)

dgrad_dG = -r / (2.0 * MU)
dgrad_dmu = G * r / (2.0 * MU**2)
dgrad_dr = -G / (2.0 * MU)
sigma_dv = np.sqrt((dgrad_dG * SIGMA_G)**2 + (dgrad_dmu * SIGMA_MU)**2 + (dgrad_dr * SIGMA_R)**2)

# ---------------- Modelo complementario de congestion M/M/1/K --------------
K = 10                    # capacidad total del sistema (incluye servicio)
MU_S = 1000.0             # tasa de servicio (paquetes/s), supuesto
SIGMA_REL_LAMBDA = 0.02   # incertidumbre relativa asumida del 2 %
SIGMA_REL_MU_S = 0.02     # incertidumbre relativa asumida del 2 %

def blocking_probability(rho: float, capacity: int = K) -> float:
    """Probabilidad estacionaria de bloqueo en una cola M/M/1/K."""
    if rho < 0:
        raise ValueError("rho debe ser no negativo")
    if abs(rho - 1.0) < 1e-10:
        return 1.0 / (capacity + 1)
    # Forma equivalente y numericamente estable para rho cercano a 1.
    return rho**capacity / sum(rho**j for j in range(capacity + 1))

def dblocking_drho(rho: float, capacity: int = K) -> float:
    """Derivada analitica de P_K respecto a rho."""
    if rho <= 0:
        if capacity == 1:
            return 1.0
        return 0.0
    S = sum(rho**j for j in range(capacity + 1))
    dS = sum(j * rho**(j - 1) for j in range(1, capacity + 1))
    return (capacity * rho**(capacity - 1) * S - rho**capacity * dS) / S**2

arrival_rates = np.array([500., 700., 850., 950., 990.])
rows = []
for lam in arrival_rates:
    rho = lam / MU_S
    p = blocking_probability(rho)
    dpdrho = dblocking_drho(rho)
    sigma_rho = rho * np.sqrt(SIGMA_REL_LAMBDA**2 + SIGMA_REL_MU_S**2)
    sigma_p = abs(dpdrho) * sigma_rho
    dpdlambda = dpdrho / MU_S
    rows.append((lam, rho, p, 100*p, dpdrho, dpdlambda, sigma_p, 100*sigma_p))

with (OUT / "resultados_cola.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["lambda_paquetes_s", "utilizacion_rho", "P_bloqueo", "P_bloqueo_porcentaje", "dP_drho", "dP_dlambda_por_paquete_s", "incertidumbre_P", "incertidumbre_P_porcentaje"])
    w.writerows(rows)

with (OUT / "perfil_radial.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["r_normalizado", "v_normalizada", "sigma_v", "dv_dr", "sigma_dv_dr", "d2v_dr2"])
    for vals in zip(r, v, sigma_v, dv, sigma_dv, d2v):
        w.writerow(vals)

# ---------------- Graficas reproducibles ----------------------------------
plt.figure(figsize=(8.2, 5.0))
plt.errorbar(r[::5], v[::5], yerr=sigma_v[::5], fmt='o', capsize=3, label='Modelo y barras de incertidumbre')
plt.plot(r, v, label=r'$v(r)=1-r^2$')
plt.xlabel('Radio normalizado, r/R')
plt.ylabel('Velocidad equivalente normalizada, v/vmax')
plt.title('Perfil radial de velocidad equivalente')
plt.grid(True, alpha=.3)
plt.legend()
plt.tight_layout()
plt.savefig(FIG / "perfil_radial_velocidad.png", dpi=220)
plt.close()

plt.figure(figsize=(8.2, 5.0))
plt.errorbar(r[::5], dv[::5], yerr=sigma_dv[::5], fmt='o', capsize=3, label='Derivada y barras de incertidumbre')
plt.plot(r, dv, label=r'$dv/dr=-2r$')
plt.axhline(0, linewidth=0.8)
plt.xlabel('Radio normalizado, r/R')
plt.ylabel('Tasa de cambio, dv/dr')
plt.title('Primera derivada del perfil radial')
plt.grid(True, alpha=.3)
plt.legend()
plt.tight_layout()
plt.savefig(FIG / "derivada_radial.png", dpi=220)
plt.close()

rho_curve = np.linspace(0.05, 0.999, 350)
p_curve = np.array([blocking_probability(x) for x in rho_curve])
plt.figure(figsize=(8.2, 5.0))
plt.plot(rho_curve, 100*p_curve, label='M/M/1/K, K=10')
for row in rows:
    lam, rho0, p, pct, dpdrho, dpdlambda, sigmap, sigmapct = row
    plt.errorbar(rho0, pct, yerr=sigmapct, fmt='o', capsize=3)
plt.xlabel(r'Utilizacion del enlace, $\rho=\lambda/\mu_s$')
plt.ylabel('Probabilidad de bloqueo (%)')
plt.title('Perdida por saturacion de un buffer finito')
plt.grid(True, alpha=.3)
plt.legend()
plt.tight_layout()
plt.savefig(FIG / "perdida_vs_utilizacion.png", dpi=220)
plt.close()

# Esquema propio de fibra y nodo de congestion (no se usa imagen con copyright).
fig, ax = plt.subplots(figsize=(9, 3.5))
ax.set_aspect('equal')
# Cable exterior y seccion del nucleo/revestimiento
from matplotlib.patches import Circle, FancyBboxPatch, FancyArrowPatch
ax.add_patch(Circle((1.5, 1.7), 1.15, facecolor='#dce6f1', edgecolor='#34495e', lw=2))
ax.add_patch(Circle((1.5, 1.7), 0.62, facecolor='#f6d365', edgecolor='#b9770e', lw=2))
ax.text(1.5, 1.7, 'Nucleo', ha='center', va='center', fontsize=11)
ax.text(1.5, 0.25, 'Revestimiento / cladding', ha='center', fontsize=9)
ax.add_patch(FancyArrowPatch((2.8,1.7),(4.0,1.7),arrowstyle='->',mutation_scale=18,lw=2,color='#2471a3'))
ax.text(3.4, 1.95, 'Enlace optico', ha='center', fontsize=9)
# router buffer
box = FancyBboxPatch((4.2,0.75),2.0,1.9,boxstyle='round,pad=0.08',facecolor='#e8f8f5',edgecolor='#117864',lw=2)
ax.add_patch(box)
ax.text(5.2,2.25,'Nodo / router',ha='center',fontsize=11)
for i in range(5):
    ax.add_patch(FancyBboxPatch((4.45+i*0.32,1.35),0.23,0.45,boxstyle='round,pad=0.02',facecolor='#76d7c4',edgecolor='#117864'))
ax.text(5.2,0.95,'Cola finita',ha='center',fontsize=9)
ax.add_patch(FancyArrowPatch((6.3,1.7),(7.6,1.7),arrowstyle='->',mutation_scale=18,lw=2,color='#2471a3'))
ax.text(8.05,1.7,'Destino',ha='center',va='center',fontsize=11)
ax.text(5.2,0.25,'La congestion y el bloqueo se modelan en el buffer del nodo',ha='center',fontsize=8.5)
ax.set_xlim(0,9); ax.set_ylim(0,3.4); ax.axis('off')
plt.tight_layout()
plt.savefig(FIG / "esquema_fibra_y_buffer.png", dpi=220, bbox_inches='tight')
plt.close()

print('Archivos generados en:', OUT)
print('Tabla de bloqueo:')
for row in rows:
    print(f'lambda={row[0]:.0f}, rho={row[1]:.2f}, P={row[3]:.4f}% +/- {row[7]:.4f}%')
