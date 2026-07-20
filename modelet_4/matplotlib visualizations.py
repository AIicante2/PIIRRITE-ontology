import numpy as np
import matplotlib.pyplot as plt

# Paramètres
Rn = 50
fn = 0.25
Pn = 57.3

def smoothstep(edge0, edge1, x):
    """Fonction smoothstep classique : 3t^2 - 2t^3, clampée entre 0 et 1"""
    t = np.clip((x - edge0) / (edge1 - edge0), 0, 1)
    return t * t * (3 - 2 * t)

def A_bar_n(P, Rn, fn):
    edge0 = Rn
    edge1 = Rn + 20 * fn
    return smoothstep(edge0, edge1, P)

# Génération des points
P = np.linspace(48, 58, 1000)
A = A_bar_n(P, Rn, fn)

# Valeur au point Pn = 57.3
A_Pn = A_bar_n(np.array([Pn]), Rn, fn)[0]

# Plot
fig, ax = plt.subplots(figsize=(8, 5))

ax.plot(P, A, linewidth=2, color='steelblue', label=r'$\bar{A}_n(P)$')

# Bornes des axes (fixées avant de tracer les pointillés)
xmin, xmax = 48, 58
ymin, ymax = 0, 1.05
ax.set_xlim(xmin, xmax)
ax.set_ylim(ymin, ymax)

# Marquer le point Pn = 57.3
ax.scatter([Pn], [A_Pn], color='red', zorder=5, 
           label=f'$P_n={Pn}dB$, $\\bar{{A}}_n={A_Pn:.1f}$')

# Pointillés qui ne vont que jusqu'à la courbe (pas au-delà)
ax.plot([Pn, Pn], [ymin, A_Pn], color='red', linestyle=':', alpha=0.5)
ax.plot([xmin, Pn], [A_Pn, A_Pn], color='red', linestyle=':', alpha=0.5)

# Ligne verticale pour marquer Rn
ax.axvline(Rn, color='gray', linestyle='--', alpha=0.6, label=f'$R_n={Rn}dB$')

# Labels rouges sous l'axe des x et à gauche de l'axe des y
ax.text(Pn, ymin - 0.04, f'{Pn}', color='red', ha='center', va='top', fontsize=10)
ax.text(xmin - 0.8, A_Pn, f'{A_Pn:.1f}', color='red', ha='right', va='center', fontsize=10)

ax.set_xlabel(r'$P_n$', fontsize=12)
ax.set_ylabel(r'$\bar{A}_n(P)$', fontsize=12)
ax.set_title(f'Noise inadequacy $\\bar{{A}}_n(P)$ using $R_n={Rn}dB$, $f_n={fn}$ and $P_n={Pn}dB$', fontsize=13)
ax.legend(loc='lower center')
ax.grid(alpha=0.3)

plt.tight_layout()
fig.savefig(r'C:\Users\salom\Downloads\Noise inadequacy.png', dpi=300, bbox_inches='tight')

# TEMPERATURE

# Paramètres
# Rt = 24
# ft = 0.8
# Pt = 29.1

# def A_bar(P, Rt, ft):
#     result = np.zeros_like(P, dtype=float)

#     lower_bound = Rt - 10 * ft
#     upper_bound = Rt + 10 * ft

#     mask1 = P < lower_bound
#     mask2 = (P >= lower_bound) & (P <= Rt)
#     mask3 = (P > Rt) & (P <= upper_bound)
#     mask4 = P > upper_bound

#     result[mask1] = 1
#     result[mask2] = (Rt - P[mask2]) / (10 * ft)
#     result[mask3] = (P[mask3] - Rt) / (10 * ft)
#     result[mask4] = 1

#     return result

# # Génération des points
# P = np.linspace(12, 36, 1000)
# A = A_bar(P, Rt, ft)

# # Valeur au point Pt = 28.9
# A_Pt = A_bar(np.array([Pt]), Rt, ft)[0]

# # Plot
# fig, ax = plt.subplots(figsize=(8, 5))

# ax.plot(P, A, linewidth=2, color='steelblue', label=r'$\bar{A}_t(P)$')

# # Bornes des axes (fixées avant de tracer les pointillés)
# xmin, xmax = 12, 36
# ymin, ymax = 0, 1.05
# ax.set_xlim(xmin, xmax)
# ax.set_ylim(ymin, ymax)

# # Marquer le point Pt = 28.9
# ax.scatter([Pt], [A_Pt], color='red', zorder=5, 
#            label=f'$P_t={Pt}°C$, $\\bar{{A}}_t={A_Pt:.3f}$')

# # Pointillés qui ne vont que jusqu'à la courbe (pas au-delà)
# ax.plot([Pt, Pt], [ymin, A_Pt], color='red', linestyle=':', alpha=0.5)
# ax.plot([xmin, Pt], [A_Pt, A_Pt], color='red', linestyle=':', alpha=0.5)

# # Lignes verticales pour marquer Rt
# ax.axvline(Rt, color='gray', linestyle='--', alpha=0.6, label=f'$R_t={Rt}°C$')

# # Labels rouges sous l'axe des x et à gauche de l'axe des y
# ax.text(Pt, ymin - 0.04, f'{Pt}', color='red', ha='center', va='top', fontsize=10)
# ax.text(xmin - 0.5, A_Pt, f'{A_Pt:.3f}', color='red', ha='right', va='center', fontsize=10)

# ax.set_xlabel(r'$P_t$', fontsize=12)
# ax.set_ylabel(r'$\bar{A}_t(P)$', fontsize=12)
# ax.set_title(f'Temperature inadequacy $\\bar{{A}}_t(P)$ using $R_t={Rt}°C$, $f_t={ft}$ and $P_t={Pt}°C$', fontsize=13)
# ax.legend(loc='best')
# ax.grid(alpha=0.3)

# plt.tight_layout()
# fig.savefig(r'C:\Users\salom\Downloads\Temperature inadequacy.png', dpi=300, bbox_inches='tight')