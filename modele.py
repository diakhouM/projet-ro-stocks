"""
modele.py : les deux programmes lineaires du dossier, resolus par le simplexe du cours.

PL 1 "commandes" : combien commander chaque semaine pour maximiser la marge ?
                   -> on en deduit aussi quand il y a rupture et quand commander.
PL 2 "rayon"     : comment partager la place du rayon entre les produits ?

Lancer :  python modele.py
"""

import numpy as np
import pandas as pd

import donnees as d
from simplexe import simplexe

TOLERANCE = 1e-6
JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]


# ---------------------------------------------------------------------------
# PL 1 : combien commander ?
# ---------------------------------------------------------------------------
def pl_commandes(produits, budget=d.BUDGET_HEBDO, capacite=d.CAPACITE_RESERVE,
                 service_min=d.SERVICE_MIN, detail=True):
    """
    Max  somme( marge_i * x_i )
    s.c. somme( cout_i   * x_i ) <= budget
         somme( volume_i * x_i ) <= capacite
         service_min * H_i <= x_i <= H_i          (H_i = demande hebdomadaire)

    Changement de variable : x_i = minimum_i + z_i, avec z_i >= 0.
    Toutes les contraintes deviennent des "<=" : le simplexe du chapitre 1 suffit.
    """
    demande_hebdo = d.JOURS_PAR_SEMAINE * produits["demande_jour"].to_numpy()
    minimum = service_min * demande_hebdo
    noms = list(produits["nom_court"])
    nb = len(noms)

    # Ce qu'il reste de budget et de reserve une fois le minimum commande
    budget_restant = budget - produits["cout_achat"] @ minimum
    reserve_restante = capacite - produits["volume"] @ minimum
    if budget_restant < 0 or reserve_restante < 0:
        raise ValueError("Programme admissible vide : le service minimum "
                         "depasse le budget ou la reserve.")

    # Lignes : budget, reserve, puis un plafond par produit (z_i <= H_i - minimum_i)
    A = np.vstack([produits["cout_achat"], produits["volume"], np.eye(nb)])
    b = np.concatenate([[budget_restant, reserve_restante], demande_hebdo - minimum])
    contraintes = ["budget", "reserve"] + ["max_" + nom for nom in noms]

    resultat = simplexe(produits["marge"], A, b, noms, contraintes, detail)
    resultat["minimum"] = minimum
    resultat["marge_minimum"] = produits["marge"] @ minimum
    return resultat


def marge_totale(resultat):
    """Marge de la semaine = marge du minimum + marge trouvee par le simplexe."""
    return resultat["marge_minimum"] + resultat["Z"]


def tableau_commandes(produits, resultat):
    """Quantite optimale de chaque produit et borne atteinte."""
    noms = produits["nom_court"]
    t = pd.DataFrame({"produit": produits["produit"]})
    t["minimum"] = resultat["minimum"]
    t["quantite_optimale"] = t["minimum"] + [resultat["valeurs"][n] for n in noms]
    t["maximum"] = d.JOURS_PAR_SEMAINE * produits["demande_jour"]
    # Variable d'ecart du plafond = demande que l'on ne pourra pas servir
    t["non_servi"] = [resultat["valeurs"]["e_max_" + n] for n in noms]

    t["saturee"] = "non"
    t.loc[t["quantite_optimale"] <= t["minimum"] + TOLERANCE, "saturee"] = "service minimum"
    t.loc[t["non_servi"] <= TOLERANCE, "saturee"] = "plafond"

    return t


def tableau_ressources(resultat, budget=d.BUDGET_HEBDO, capacite=d.CAPACITE_RESERVE):
    """Budget et reserve : utilisation, ecart (variable d'ecart) et saturation."""
    ecarts = np.array([resultat["valeurs"]["e_budget"], resultat["valeurs"]["e_reserve"]])
    limites = np.array([budget, capacite])
    return pd.DataFrame({
        "contrainte": ["Budget (€)", "Réserve (litres)"],
        "utilise": limites - ecarts,
        "limite": limites,
        "ecart": ecarts,
        "saturee": ["oui" if e <= TOLERANCE else "non" for e in ecarts],
    })


# ---------------------------------------------------------------------------
# Quand y a-t-il rupture ? Quand commander ?
# ---------------------------------------------------------------------------
def tableau_ruptures(produits, commandes):
    """Avec la quantite commandee, combien de jours le stock tient-il ?"""
    t = commandes[["produit", "quantite_optimale", "non_servi"]].copy()
    t["jours_couverts"] = t["quantite_optimale"] / produits["demande_jour"]
    t["rupture"] = "aucune"
    for i, jours in enumerate(t["jours_couverts"]):
        if jours < d.JOURS_PAR_SEMAINE - TOLERANCE:
            t.loc[i, "rupture"] = "le " + JOURS[int(jours + TOLERANCE)]
    marge_perdue = t["non_servi"] * produits["marge"]
    t["marge_perdue"] = marge_perdue
    return t


def calendrier_commandes(produits):
    """Pour etre livre le lundi matin, quel jour faut-il commander ?"""
    t = produits[["produit", "delai"]].copy()
    # lundi = jour 0 ; on remonte de "delai" jours dans la semaine precedente
    t["jour_de_commande"] = [JOURS[(-delai) % 7] for delai in t["delai"]]
    # Seuil d'alerte : demande pendant le delai + stock de securite
    t["point_de_commande"] = produits["demande_jour"] * produits["delai"] + produits["stock_securite"]
    return t


# ---------------------------------------------------------------------------
# PL 2 : comment partager le rayon ?
# ---------------------------------------------------------------------------
def pl_rayon(produits, nb_remplissages=d.NB_REMPLISSAGES, volume_rayon=d.VOLUME_RAYON,
             detail=True):
    """
    r_i = nombre de places du produit i dans le rayon.
    Avec n remplissages par jour, on vend n * r_i unites par jour au maximum.

    Max  somme( marge_i * n * r_i )            marge vendue par jour
    s.c. somme( volume_i * r_i ) <= volume du rayon
         n * r_i <= demande_i                  inutile d'exposer plus que la demande
    """
    noms = list(produits["nom_court"])
    nb = len(noms)
    A = np.vstack([produits["volume"], nb_remplissages * np.eye(nb)])
    b = np.concatenate([[volume_rayon], produits["demande_jour"]])
    contraintes = ["rayon"] + ["dem_" + nom for nom in noms]
    return simplexe(nb_remplissages * produits["marge"], A, b, noms, contraintes, detail)


def tableau_rayon(produits, resultat, nb_remplissages=d.NB_REMPLISSAGES):
    """Compare la repartition actuelle du rayon et la repartition optimale."""
    t = produits[["produit", "demande_jour", "capacite_rayon"]].copy()
    t["places_optimales"] = [resultat["valeurs"][n] for n in produits["nom_court"]]
    for nom, colonne in [("ventes_actuelles", "capacite_rayon"),
                         ("ventes_optimales", "places_optimales")]:
        t[nom] = np.minimum(nb_remplissages * t[colonne], t["demande_jour"])
    t["marge_actuelle"] = t["ventes_actuelles"] * produits["marge"]
    t["marge_optimale"] = t["ventes_optimales"] * produits["marge"]
    return t


# ---------------------------------------------------------------------------
# Affichage quand on lance le fichier
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 30)

    print("=== PL 1 : combien commander ? ===")
    resultat = pl_commandes(d.PRODUITS)
    print("\nTableau initial du simplexe :")
    print(resultat["tableaux"][0].to_string(index=False, na_rep=""))
    print("\nPivots successifs :")
    print(resultat["pivots"].to_string(index=False))
    print("\nTableau final :")
    print(resultat["tableaux"][-1].to_string(index=False, na_rep=""))

    commandes = tableau_commandes(d.PRODUITS, resultat)
    print("\nSolution optimale :")
    print(commandes.round(2).to_string(index=False))
    print(f"Marge hebdomadaire maximale : {marge_totale(resultat):.2f} €")
    print("\nRessources :")
    print(tableau_ressources(resultat).round(3).to_string(index=False))

    print("\n=== Quand y a-t-il rupture ? ===")
    print(tableau_ruptures(d.PRODUITS, commandes).round(2).to_string(index=False))
    print("\n=== Quand commander ? ===")
    print(calendrier_commandes(d.PRODUITS).to_string(index=False))

    for nb in (1, 2):
        print(f"\n=== PL 2 : partage du rayon, {nb} remplissage(s) par jour ===")
        rayon = pl_rayon(d.PRODUITS, nb_remplissages=nb)
        t = tableau_rayon(d.PRODUITS, rayon, nb)
        print(t.round(2).to_string(index=False))
        print(f"Marge par jour : {t['marge_actuelle'].sum():.2f} € aujourd'hui, "
              f"{t['marge_optimale'].sum():.2f} € à l'optimum")
