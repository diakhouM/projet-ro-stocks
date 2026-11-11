"""
donnees.py : toutes les hypotheses du projet (cas d'etude : un Super U moyen).

Les chiffres sont imaginaires. Pour tester un autre scenario,
il suffit de modifier ce fichier : le reste du code s'adapte tout seul.
"""

import pandas as pd

# ---------------------------------------------------------------------------
# 0. Le cas a 2 produits (resolu a la main dans le rapport)
# ---------------------------------------------------------------------------
# Meme colonnes que pour les 6 produits (voir COLONNES plus bas).
LIGNES_2_PRODUITS = [
    ["Produit A", "A", 20, 2.0, 5.0, 2, 20, 15, 1.0],
    ["Produit B", "B", 20, 4.0, 9.0, 3, 20, 15, 1.0],
]
PARAMETRES_2_PRODUITS = {
    "budget": 400,          # euros par semaine
    "reserve": 150,         # litres
    "service_min": 0,       # pas de service minimum dans l'exemple a la main
    "volume_rayon": 30,     # litres (15 places de A et 15 places de B)
}

# ---------------------------------------------------------------------------
# 1. Les 6 produits
# ---------------------------------------------------------------------------
# Chaque ligne = un produit. L'ordre des valeurs suit la liste COLONNES.
COLONNES = [
    "produit",          # nom complet du produit
    "nom_court",        # nom utilise dans les tableaux du simplexe
    "demande_jour",     # demande par jour (unites)
    "cout_achat",       # prix d'achat unitaire (euros)
    "prix_vente",       # prix de vente unitaire (euros)
    "delai",            # delai de livraison (jours)
    "stock_securite",   # stock de securite (unites)
    "capacite_rayon",   # nombre d'unites dans le rayon aujourd'hui
    "volume",           # volume d'une unite (litres)
]

LIGNES = [
    ["Pain de mie",              "pain",    400, 0.45, 1.00, 1, 200, 300,  3.0],
    ["Lait frais 1 L",           "lait",    250, 0.80, 1.15, 2, 150, 250,  1.2],
    ["Yaourts (pack de 4)",      "yaourts", 300, 1.10, 1.75, 2, 200, 350,  1.0],
    ["Eau (pack 6 x 1,5 L)",     "eau",     200, 1.50, 2.40, 3, 200, 150, 10.0],
    ["Lessive 2 L",              "lessive",  40, 5.50, 8.90, 5,  60,  80,  2.5],
    ["Cosmétiques (gel douche)", "cosm",     25, 4.00, 7.50, 7,  50, 100,  0.5],
]

PRODUITS = pd.DataFrame(LIGNES, columns=COLONNES)
PRODUITS["marge"] = PRODUITS["prix_vente"] - PRODUITS["cout_achat"]

PRODUITS_2 = pd.DataFrame(LIGNES_2_PRODUITS, columns=COLONNES)
PRODUITS_2["marge"] = PRODUITS_2["prix_vente"] - PRODUITS_2["cout_achat"]

# ---------------------------------------------------------------------------
# 2. Parametres generaux
# ---------------------------------------------------------------------------
BUDGET_HEBDO = 8000         # budget de commande par semaine (euros)
CAPACITE_RESERVE = 25000    # capacite de la reserve (litres) = 25 m3
SERVICE_MIN = 0.70          # commander au moins 70 % de la demande hebdomadaire
JOURS_PAR_SEMAINE = 7
NB_REMPLISSAGES = 1         # nombre de remplissages du rayon par jour (1 = le matin)

# Volume total du rayon : celui qu'occupent les capacites actuelles (3 300 litres)
VOLUME_RAYON = (PRODUITS["capacite_rayon"] * PRODUITS["volume"]).sum()
