"""
figures.py : cree les graphiques du rapport dans rapport/figures/.

Lancer :  python figures.py     (il faut matplotlib : pip install matplotlib)
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")            # pas de fenetre : on enregistre seulement des fichiers
import matplotlib.pyplot as plt
import numpy as np

import donnees as d
from modele import (pl_commandes, tableau_commandes, tableau_ruptures,
                    pl_rayon, tableau_rayon)

DOSSIER = Path(__file__).parent / "rapport" / "figures"
BLEU, ORANGE, GRIS, ROUGE, VERT = "#1f4e79", "#e07b00", "#7f7f7f", "#b22222", "#2e7d32"
NOMS_COURTS = ["Pain de mie", "Lait", "Yaourts", "Eau", "Lessive", "Cosmétiques"]

plt.rcParams.update({"font.size": 10, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.grid": True,
                     "grid.alpha": 0.3, "figure.dpi": 150})


def enregistrer(nom):
    plt.tight_layout()
    plt.savefig(DOSSIER / nom)
    plt.close()
    print("  ", nom)


def figure_methode_graphique():
    """Programme admissible et optimum du cas a 2 produits."""
    a = np.linspace(0, 220, 200)
    plt.figure(figsize=(5.2, 4.0))
    sommets = [(0, 0), (140, 0), (140, 10), (100, 50), (0, 100)]
    plt.fill(*zip(*sommets), color=BLEU, alpha=0.15, label="Programme admissible")
    plt.plot(a, (400 - 2 * a) / 4, color=ORANGE, label="Budget : 2a + 4b = 400")
    plt.plot(a, 150 - a, color=VERT, label="Réserve : a + b = 150")
    plt.axvline(140, color=GRIS, linewidth=1, label="Plafond : a = 140")
    plt.plot(a, (550 - 3 * a) / 5, color=ROUGE, linestyle="--", label="Z = 3a + 5b = 550")
    for x, y in sommets:
        plt.plot(x, y, "o", color=BLEU, markersize=4)
    plt.plot(100, 50, "o", color=ROUGE, markersize=8)
    plt.annotate("Optimum (100 ; 50)\nZ = 550 €", (100, 50), (112, 78),
                 arrowprops={"arrowstyle": "->", "color": ROUGE}, color=ROUGE)
    plt.xlim(0, 220)
    plt.ylim(0, 160)
    plt.xlabel("a : quantité du produit A")
    plt.ylabel("b : quantité du produit B")
    plt.legend(loc="upper right", frameon=False, fontsize=8)
    enregistrer("methode_graphique.pdf")


def figure_rayon_2_produits():
    """Cas a 2 produits : partage du rayon (30 litres, 1 litre par place)."""
    x = np.linspace(0, 32, 100)
    plt.figure(figsize=(4.6, 3.8))
    sommets = [(0, 0), (20, 0), (20, 10), (10, 20), (0, 20)]
    plt.fill(*zip(*sommets), color=BLEU, alpha=0.15, label="Programme admissible")
    plt.plot(x, 30 - x, color=ORANGE, label="Rayon : $r_A + r_B = 30$")
    plt.axvline(20, color=GRIS, linewidth=1, label="Demande : $r_A = 20$")
    plt.axhline(20, color=VERT, linewidth=1, label="Demande : $r_B = 20$")
    plt.plot(x, (130 - 3 * x) / 5, color=ROUGE, linestyle="--", label="Z = 3$r_A$ + 5$r_B$ = 130")
    for sx, sy in sommets:
        plt.plot(sx, sy, "o", color=BLEU, markersize=4)
    plt.plot(10, 20, "o", color=ROUGE, markersize=8)
    plt.plot(15, 15, "s", color=GRIS, markersize=6)
    plt.annotate("partage actuel\n(15 ; 15) : 120 €", (15, 15), (20.5, 22.5),
                 arrowprops={"arrowstyle": "->", "color": GRIS}, color=GRIS, fontsize=8)
    plt.annotate("Optimum (10 ; 20)\n130 €", (10, 20), (0.5, 24.5),
                 arrowprops={"arrowstyle": "->", "color": ROUGE}, color=ROUGE, fontsize=8)
    plt.xlim(0, 32)
    plt.ylim(0, 30)
    plt.xlabel("$r_A$ : places du produit A")
    plt.ylabel("$r_B$ : places du produit B")
    plt.legend(loc="lower left", frameon=False, fontsize=7)
    enregistrer("rayon_2_produits.pdf")


def figure_solution(commandes):
    """Quantite optimale de chaque produit, en % de la demande hebdomadaire."""
    part = 100 * commandes["quantite_optimale"] / commandes["maximum"]
    couleurs = [BLEU if s == "plafond" else ORANGE if s == "service minimum" else VERT
                for s in commandes["saturee"]]

    plt.figure(figsize=(6.3, 3.0))
    plt.bar(NOMS_COURTS, part, color=couleurs)
    plt.axhline(70, color=GRIS, linestyle="--", linewidth=1)
    plt.axhline(100, color=GRIS, linestyle="--", linewidth=1)
    for i, valeur in enumerate(part):
        plt.text(i, valeur - 7, f"{valeur:.0f} %", ha="center", color="white", fontweight="bold")
    plt.text(5.45, 71, "service minimum", ha="right", color=GRIS, fontsize=8)
    plt.ylim(0, 108)
    plt.ylabel("% de la demande hebdomadaire")
    enregistrer("solution_optimale.pdf")


def figure_ruptures(ruptures):
    """Nombre de jours de vente couverts par la commande de la semaine."""
    jours = ruptures["jours_couverts"]
    couleurs = [BLEU if j >= 7 - 1e-6 else ROUGE for j in jours]
    plt.figure(figsize=(6.3, 2.8))
    plt.bar(NOMS_COURTS, jours, color=couleurs)
    plt.axhline(7, color="black", linestyle="--", linewidth=1)
    for i, valeur in enumerate(jours):
        plt.text(i, valeur - 0.8, f"{valeur:.1f} j", ha="center", color="white", fontweight="bold")
    plt.ylim(0, 7.8)
    plt.ylabel("Jours de vente couverts")
    enregistrer("ruptures.pdf")


def figure_rayon(rayon):
    """Places en rayon : aujourd'hui, a l'optimum, et demande d'une journee."""
    x = np.arange(len(NOMS_COURTS))
    plt.figure(figsize=(6.3, 3.0))
    plt.bar(x - 0.27, rayon["capacite_rayon"], width=0.27, color=ORANGE, label="Places actuelles")
    plt.bar(x, rayon["places_optimales"], width=0.27, color=BLEU, label="Places optimales")
    plt.bar(x + 0.27, rayon["demande_jour"], width=0.27, color=GRIS, label="Demande par jour")
    plt.xticks(x, NOMS_COURTS)
    plt.ylabel("Unités")
    plt.legend(loc="upper right", frameon=False)
    enregistrer("rayon.pdf")


if __name__ == "__main__":
    DOSSIER.mkdir(parents=True, exist_ok=True)
    print("Figures créées dans", DOSSIER)
    commandes = tableau_commandes(d.PRODUITS, pl_commandes(d.PRODUITS))
    figure_methode_graphique()
    figure_rayon_2_produits()
    figure_solution(commandes)
    figure_ruptures(tableau_ruptures(d.PRODUITS, commandes))
    figure_rayon(tableau_rayon(d.PRODUITS, pl_rayon(d.PRODUITS)))
