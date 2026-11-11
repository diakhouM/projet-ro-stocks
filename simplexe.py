"""
simplexe.py : l'algorithme du simplexe du cours (chapitre 1), en tableaux.

Il resout un programme lineaire canonique :

    max  Z = c1*x1 + ... + cn*xn
    s.c. A x <= b      (avec b >= 0)
         x >= 0

Etapes, comme dans le cours :
  1. on ajoute une variable d'ecart par contrainte : c'est la base de depart ;
  2. on calcule les profits marginaux (ligne Delta_j) ;
  3. la variable ENTRANTE est celle dont le profit marginal est le plus grand ;
  4. la variable SORTANTE est celle dont le rapport b_i / a_ij est le plus petit ;
  5. on pivote, et on recommence tant qu'il reste un profit marginal positif.
"""

import numpy as np
import pandas as pd

TOLERANCE = 1e-9     # en dessous, un nombre est considere comme nul
MAX_PIVOTS = 10000   # au-dela, on suppose que l'algorithme boucle


def profits_marginaux(tableau, couts, base):
    """Ligne Delta_j = c_j - somme( c_B * colonne j ). La derniere case vaut -Z."""
    couts_base = couts[base]
    delta = couts - couts_base @ tableau[:, :-1]
    moins_z = -(couts_base @ tableau[:, -1])
    return np.append(delta, moins_z)


def choisir_entrante(delta):
    """Colonne du plus grand profit marginal. None si aucun n'est positif (optimum)."""
    colonne = int(np.argmax(delta[:-1]))
    return colonne if delta[colonne] > TOLERANCE else None


def calculer_rapports(tableau, colonne):
    """Rapports b_i / a_ij, seulement pour les coefficients a_ij positifs."""
    rapports = np.full(len(tableau), np.inf)
    positifs = tableau[:, colonne] > TOLERANCE
    rapports[positifs] = tableau[positifs, -1] / tableau[positifs, colonne]
    return rapports


def pivoter(tableau, ligne, colonne):
    """Divise la ligne pivot par le pivot, puis annule la colonne dans les autres lignes."""
    tableau[ligne] = tableau[ligne] / tableau[ligne, colonne]
    for i in range(len(tableau)):
        if i != ligne:
            tableau[i] = tableau[i] - tableau[i, colonne] * tableau[ligne]


def tableau_lisible(tableau, couts, base, delta, noms, rapports=None):
    """Met le tableau du simplexe sous la forme du cours (c_B, base, variables, b_i)."""
    t = pd.DataFrame(tableau, columns=noms + ["b_i"])
    t.insert(0, "base", [noms[j] for j in base])
    t.insert(0, "c_B", couts[base])
    if rapports is not None:
        t["rapport"] = [r if np.isfinite(r) else np.nan for r in rapports]
    ligne_delta = dict(zip(noms + ["b_i"], delta), base="Delta_j")
    t = pd.concat([t, pd.DataFrame([ligne_delta])], ignore_index=True)
    return t.round(4)


def simplexe(c, A, b, noms_variables, noms_contraintes, detail=True):
    """
    Resout  max c.x  s.c.  A x <= b,  x >= 0.
    Renvoie un dictionnaire : valeurs des variables, Z, profits marginaux finaux,
    liste des tableaux et liste des pivots.
    detail=False : on ne garde pas les tableaux intermediaires (utile pour des centaines
    de produits, ou l'affichage de chaque tableau n'aurait plus de sens).
    """
    c, A, b = np.array(c, float), np.array(A, float), np.array(b, float)
    nb_contraintes, nb_variables = A.shape
    if (b < 0).any():
        raise ValueError("Second membre negatif : pas de solution de base initiale.")

    # Tableau initial : [ A | identite (variables d'ecart) | b ]
    noms = list(noms_variables) + ["e_" + nom for nom in noms_contraintes]
    tableau = np.hstack([A, np.eye(nb_contraintes), b.reshape(-1, 1)])
    couts = np.append(c, np.zeros(nb_contraintes))
    base = list(range(nb_variables, nb_variables + nb_contraintes))

    tableaux, pivots = [], []
    while True:
        if len(pivots) > MAX_PIVOTS:             # garde-fou contre un bouclage
            raise ValueError("Trop de pivots : le simplexe tourne en rond.")
        delta = profits_marginaux(tableau, couts, base)
        colonne = choisir_entrante(delta)
        if colonne is None:                      # plus de profit marginal positif
            if detail:
                tableaux.append(tableau_lisible(tableau, couts, base, delta, noms))
            break

        rapports = calculer_rapports(tableau, colonne)
        if not np.isfinite(rapports).any():      # pas de variable sortante (chapitre 3)
            raise ValueError("Programme admissible non borne : Z tend vers l'infini.")
        ligne = int(np.argmin(rapports))

        if detail:
            tableaux.append(tableau_lisible(tableau, couts, base, delta, noms, rapports))
        pivots.append({"etape": len(pivots) + 1,
                       "entrante": noms[colonne], "profit_marginal": delta[colonne],
                       "sortante": noms[base[ligne]], "rapport": rapports[ligne],
                       "pivot": tableau[ligne, colonne]})
        pivoter(tableau, ligne, colonne)
        base[ligne] = colonne
        pivots[-1]["Z"] = couts[base] @ tableau[:, -1]

    # Lecture de la solution dans le dernier tableau
    valeurs = dict.fromkeys(noms, 0.0)           # variables hors base = 0
    for i, j in enumerate(base):
        valeurs[noms[j]] = tableau[i, -1]
    delta_final = dict(zip(noms, delta[:-1]))
    return {"valeurs": valeurs, "Z": -delta[-1],
            "delta": delta_final, "base": [noms[j] for j in base],
            "tableaux": tableaux, "pivots": pd.DataFrame(pivots).round(4)}
