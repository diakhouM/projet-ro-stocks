"""
application.py : l'application Python du dossier.

Elle repond aux trois questions pour N produits (2, 6, 10, 100, 300...) :
  1. Quand y a-t-il rupture ?
  2. Quand et combien commander ?
  3. Comment repartir le stock entre le rayon et la reserve ?

Elle utilise exactement la meme demarche que le calcul a la main sur 2 produits :
le simplexe de simplexe.py, applique aux deux programmes lineaires de modele.py.

Exemples :
  python application.py                          les 6 produits du dossier
  python application.py --deux-produits          l'exemple resolu a la main
  python application.py --fichier produits.csv   vos propres produits (CSV)
  python application.py --aleatoire 100          100 produits generes au hasard
"""

import argparse
import time

import numpy as np
import pandas as pd

import donnees as d
from modele import (pl_commandes, marge_totale, tableau_commandes, tableau_ressources,
                    tableau_ruptures, calendrier_commandes, pl_rayon, tableau_rayon)

COLONNES_OBLIGATOIRES = ["produit", "demande_jour", "cout_achat", "prix_vente", "delai",
                         "stock_securite", "capacite_rayon", "volume"]
SEUIL_AFFICHAGE_COMPLET = 15     # au-dela, on n'affiche que le resume et les premieres lignes


# ---------------------------------------------------------------------------
# 1. Les donnees : un fichier CSV ou des produits generes au hasard
# ---------------------------------------------------------------------------
def lire_produits(chemin):
    """Lit un fichier CSV (separateur point-virgule, decimale virgule)."""
    produits = pd.read_csv(chemin, sep=";", decimal=",", encoding="utf-8-sig")
    manquantes = [c for c in COLONNES_OBLIGATOIRES if c not in produits.columns]
    if manquantes:
        raise ValueError(f"Colonnes manquantes dans {chemin} : {manquantes}")
    if "nom_court" not in produits.columns:          # nom utilise dans les tableaux
        produits["nom_court"] = [f"p{i + 1}" for i in range(len(produits))]
    produits["marge"] = produits["prix_vente"] - produits["cout_achat"]
    return produits


def produits_aleatoires(nombre, graine=42):
    """
    Genere un magasin de `nombre` produits, avec un budget et une reserve
    proportionnels, pour tester l'application sur de grandes tailles.
    """
    rng = np.random.default_rng(graine)
    demande = np.round(np.exp(rng.uniform(np.log(20), np.log(400), nombre)))
    cout = np.round(rng.uniform(0.4, 6.0, nombre), 2)
    produits = pd.DataFrame({
        "produit": [f"Produit {i + 1}" for i in range(nombre)],
        "nom_court": [f"p{i + 1}" for i in range(nombre)],
        "demande_jour": demande,
        "cout_achat": cout,
        "prix_vente": np.round(cout * rng.uniform(1.3, 2.2, nombre), 2),
        "delai": rng.integers(1, 8, nombre),
        "stock_securite": np.round(demande * rng.uniform(0.3, 0.8, nombre)),
        "capacite_rayon": np.round(demande * rng.uniform(0.6, 1.4, nombre)),
        "volume": np.round(rng.uniform(0.5, 10.0, nombre), 1),
    })
    produits["marge"] = produits["prix_vente"] - produits["cout_achat"]

    # Budget et reserve un peu inferieurs a ce qu'il faudrait pour tout servir
    demande_hebdo = d.JOURS_PAR_SEMAINE * produits["demande_jour"]
    parametres = {
        "budget": round(0.85 * (produits["cout_achat"] * demande_hebdo).sum()),
        "reserve": round(0.90 * (produits["volume"] * demande_hebdo).sum()),
        "service_min": d.SERVICE_MIN,
        "volume_rayon": (produits["capacite_rayon"] * produits["volume"]).sum(),
    }
    return produits, parametres


# ---------------------------------------------------------------------------
# 2. Les reponses aux trois questions
# ---------------------------------------------------------------------------
def repondre(produits, budget, reserve, service_min, volume_rayon,
             nb_remplissages=1, detail=True):
    """Resout les deux programmes lineaires et rassemble les reponses."""
    debut = time.perf_counter()
    simplexe_commandes = pl_commandes(produits, budget, reserve, service_min, detail)
    commandes = tableau_commandes(produits, simplexe_commandes)
    simplexe_rayon = pl_rayon(produits, nb_remplissages, volume_rayon, detail)
    duree = time.perf_counter() - debut

    return {
        "simplexe_commandes": simplexe_commandes,
        "commandes": commandes,                                      # combien commander
        "ressources": tableau_ressources(simplexe_commandes, budget, reserve),
        "ruptures": tableau_ruptures(produits, commandes),           # quand il y a rupture
        "calendrier": calendrier_commandes(produits),                # quand commander
        "simplexe_rayon": simplexe_rayon,
        "rayon": tableau_rayon(produits, simplexe_rayon, nb_remplissages),
        "marge": marge_totale(simplexe_commandes),
        "duree": duree,
    }


# ---------------------------------------------------------------------------
# 3. L'affichage
# ---------------------------------------------------------------------------
def afficher_tableau(tableau, complet):
    """Affiche tout le tableau, ou seulement les premieres lignes s'il est long."""
    tableau = tableau.round(2)
    if complet or len(tableau) <= SEUIL_AFFICHAGE_COMPLET:
        print(tableau.to_string(index=False, na_rep=""))
    else:
        print(tableau.head(5).to_string(index=False, na_rep=""))
        print(f"... ({len(tableau) - 5} autres lignes)")


def afficher(produits, r, nb_remplissages=1):
    """Affiche les reponses, dans l'ordre des trois questions."""
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 40)
    petit = len(produits) <= SEUIL_AFFICHAGE_COMPLET
    nb = len(produits)

    print(f"=== {nb} produits ===")
    if petit:
        for i, tableau in enumerate(r["simplexe_commandes"]["tableaux"]):
            print(f"\nSimplexe 'commandes', tableau {i + 1} :")
            print(tableau.to_string(index=False, na_rep=""))
    print("\nPivots du simplexe 'commandes' :")
    afficher_tableau(r["simplexe_commandes"]["pivots"], petit)

    print("\n--- Combien commander ? ---")
    afficher_tableau(r["commandes"], petit)
    print(f"Marge hebdomadaire maximale : {r['marge']:.2f} €")
    print(r["ressources"].round(2).to_string(index=False))

    print("\n--- Quand y a-t-il rupture ? ---")
    ruptures = r["ruptures"]
    if petit:
        afficher_tableau(ruptures, True)
    else:
        en_rupture = ruptures[ruptures["rupture"] != "aucune"]
        print(f"{len(en_rupture)} produits sur {nb} en rupture avant la fin de la semaine")
        print(en_rupture.sort_values("marge_perdue", ascending=False).head(5)
              .round(2).to_string(index=False))
    print(f"Marge perdue à cause des ruptures : {ruptures['marge_perdue'].sum():.2f} € par semaine")

    print("\n--- Quand commander ? ---")
    afficher_tableau(r["calendrier"], petit)

    print(f"\n--- Rayon ou réserve ? ({nb_remplissages} remplissage(s) par jour) ---")
    afficher_tableau(r["rayon"], petit)
    rayon = r["rayon"]
    print(f"Marge par jour : {rayon['marge_actuelle'].sum():.2f} € avec le partage actuel, "
          f"{rayon['marge_optimale'].sum():.2f} € avec le partage optimal")

    pivots = len(r["simplexe_commandes"]["pivots"]) + len(r["simplexe_rayon"]["pivots"])
    print(f"\nCalcul : {pivots} pivots du simplexe en {r['duree']:.2f} secondes")


# ---------------------------------------------------------------------------
# 4. Le programme principal
# ---------------------------------------------------------------------------
def lire_options():
    p = argparse.ArgumentParser(description="Gestion des stocks : rupture, commandes, rayon.")
    groupe = p.add_mutually_exclusive_group()
    groupe.add_argument("--fichier", help="fichier CSV des produits")
    groupe.add_argument("--aleatoire", type=int, help="nombre de produits a generer")
    groupe.add_argument("--deux-produits", action="store_true", help="l'exemple a la main")
    p.add_argument("--budget", type=float, help="budget hebdomadaire (euros)")
    p.add_argument("--reserve", type=float, help="capacite de la reserve (litres)")
    p.add_argument("--service-min", type=float, help="service minimum, entre 0 et 1")
    p.add_argument("--volume-rayon", type=float, help="volume du rayon (litres)")
    p.add_argument("--remplissages", type=int, default=1, help="remplissages du rayon par jour")
    return p.parse_args()


def choisir_cas(options):
    """Renvoie les produits et les parametres demandes (6 produits par defaut)."""
    if options.deux_produits:
        produits, parametres = d.PRODUITS_2, dict(d.PARAMETRES_2_PRODUITS)
    elif options.aleatoire:
        produits, parametres = produits_aleatoires(options.aleatoire)
    elif options.fichier:
        produits = lire_produits(options.fichier)
        parametres = {"budget": d.BUDGET_HEBDO, "reserve": d.CAPACITE_RESERVE,
                      "service_min": d.SERVICE_MIN,
                      "volume_rayon": (produits["capacite_rayon"] * produits["volume"]).sum()}
    else:
        produits = d.PRODUITS
        parametres = {"budget": d.BUDGET_HEBDO, "reserve": d.CAPACITE_RESERVE,
                      "service_min": d.SERVICE_MIN, "volume_rayon": d.VOLUME_RAYON}

    # Les options de la ligne de commande remplacent les valeurs par defaut
    for nom, valeur in [("budget", options.budget), ("reserve", options.reserve),
                        ("service_min", options.service_min),
                        ("volume_rayon", options.volume_rayon)]:
        if valeur is not None:
            parametres[nom] = valeur
    return produits, parametres


if __name__ == "__main__":
    options = lire_options()
    produits, parametres = choisir_cas(options)
    detail = len(produits) <= SEUIL_AFFICHAGE_COMPLET    # tableaux gardes seulement si petits
    reponses = repondre(produits, nb_remplissages=options.remplissages, detail=detail,
                        **parametres)
    afficher(produits, reponses, options.remplissages)
