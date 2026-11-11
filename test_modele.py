"""
test_modele.py : on verifie le programme sur le cas a 2 produits resolu a la main.

Cas a 2 produits (detail dans le rapport) :

    Max  Z = 3a + 5b
    s.c. 2a + 4b <= 400      (budget)
          a +  b <= 150      (reserve)
          a      <= 140      (plafond de A)
               b <= 140      (plafond de B)

    1er pivot  b entre, e_budget sort, pivot 4     -> Z = 500
    2e pivot   a entre, e_reserve sort, pivot 0,5  -> Z = 550
    Solution : a = 100, b = 50, Z = 550.

    Rayon (30 litres, demande de 20 par jour) : 2 pivots, A = 10 places, B = 20 places,
    Z = 130 euros par jour (120 avec 15 places chacun).

Lancer :  python test_modele.py
"""

import math

import donnees as d
from application import lire_produits, produits_aleatoires, repondre
from modele import (pl_commandes, marge_totale, tableau_commandes, tableau_ressources,
                    tableau_ruptures, calendrier_commandes, pl_rayon, tableau_rayon)

P2 = d.PRODUITS_2
PARAMETRES_2 = d.PARAMETRES_2_PRODUITS


def proche(a, b):
    """Vrai si a et b sont egaux a 0,01 pres."""
    return math.isclose(a, b, abs_tol=0.01)


def commandes_petit_cas():
    return pl_commandes(P2, PARAMETRES_2["budget"], PARAMETRES_2["reserve"],
                        PARAMETRES_2["service_min"])


# ---------------------------------------------------------------------------
# Le cas a 2 produits : on doit retrouver les calculs faits a la main
# ---------------------------------------------------------------------------
def test_pivots_du_petit_cas():
    pivots = commandes_petit_cas()["pivots"]
    assert list(pivots["entrante"]) == ["B", "A"]
    assert list(pivots["sortante"]) == ["e_budget", "e_reserve"]
    assert list(pivots["pivot"]) == [4, 0.5]
    assert list(pivots["Z"]) == [500, 550]


def test_solution_du_petit_cas():
    resultat = commandes_petit_cas()
    assert proche(marge_totale(resultat), 550)
    commandes = tableau_commandes(P2, resultat)
    assert proche(commandes["quantite_optimale"][0], 100)
    assert proche(commandes["quantite_optimale"][1], 50)
    # le budget et la reserve sont satures, les plafonds non (ecarts 40 et 90)
    ressources = tableau_ressources(resultat, 400, 150)
    assert list(ressources["saturee"]) == ["oui", "oui"]
    assert proche(commandes["non_servi"][0], 40) and proche(commandes["non_servi"][1], 90)


def test_ruptures_et_calendrier_du_petit_cas():
    commandes = tableau_commandes(P2, commandes_petit_cas())
    ruptures = tableau_ruptures(P2, commandes)
    assert list(ruptures["jours_couverts"].round(2)) == [5.0, 2.5]
    assert list(ruptures["rupture"]) == ["le samedi", "le mercredi"]
    assert proche(ruptures["marge_perdue"].sum(), 570)
    assert list(calendrier_commandes(P2)["jour_de_commande"]) == ["samedi", "vendredi"]


def test_rayon_du_petit_cas():
    resultat = pl_rayon(P2, 1, PARAMETRES_2["volume_rayon"])
    t = tableau_rayon(P2, resultat, 1)
    assert proche(resultat["Z"], 130)
    assert proche(t["places_optimales"][0], 10) and proche(t["places_optimales"][1], 20)
    assert proche(t["marge_actuelle"].sum(), 120)       # 15 places chacun
    assert len(resultat["pivots"]) == 2
    # avec 2 remplissages par jour, toute la demande est servie
    resultat = pl_rayon(P2, 2, PARAMETRES_2["volume_rayon"])
    assert proche(resultat["Z"], 160)


# ---------------------------------------------------------------------------
# Le cas a 6 produits
# ---------------------------------------------------------------------------
def test_pl_commandes_6_produits():
    resultat = pl_commandes(d.PRODUITS)
    assert proche(marge_totale(resultat), 5630.55)
    assert len(resultat["pivots"]) == 8
    ressources = tableau_ressources(resultat)
    assert list(ressources["saturee"]) == ["oui", "non"]
    assert proche(ressources["ecart"][1], 185.83)
    commandes = tableau_commandes(d.PRODUITS, resultat)
    assert proche((commandes["quantite_optimale"] * d.PRODUITS["cout_achat"]).sum(), 8000)


def test_pl_rayon_6_produits():
    resultat = pl_rayon(d.PRODUITS, nb_remplissages=1)
    assert proche(resultat["Z"], 850.88)
    assert proche(resultat["valeurs"]["eau"], 138.75)
    resultat = pl_rayon(d.PRODUITS, nb_remplissages=2)
    assert proche(resultat["Z"], 906)


# ---------------------------------------------------------------------------
# L'application
# ---------------------------------------------------------------------------
def test_lecture_csv():
    """Les fichiers CSV d'exemple donnent les memes produits que donnees.py."""
    produits = lire_produits("exemple_6_produits.csv")
    assert list(produits["produit"]) == list(d.PRODUITS["produit"])
    assert proche(produits["cout_achat"].sum(), d.PRODUITS["cout_achat"].sum())
    assert len(lire_produits("exemple_2_produits.csv")) == 2


def test_application_sur_50_produits():
    """Sur 50 produits generes au hasard, les contraintes sont respectees."""
    produits, parametres = produits_aleatoires(50)
    r = repondre(produits, detail=False, **parametres)
    x = r["commandes"]["quantite_optimale"]
    assert (produits["cout_achat"] * x).sum() <= parametres["budget"] + 0.01
    assert (produits["volume"] * x).sum() <= parametres["reserve"] + 0.01
    assert (x <= r["commandes"]["maximum"] + 1e-6).all()
    assert (x >= r["commandes"]["minimum"] - 1e-6).all()
    places = r["rayon"]["places_optimales"]
    assert (produits["volume"] * places).sum() <= parametres["volume_rayon"] + 0.01


if __name__ == "__main__":
    tests = [test_pivots_du_petit_cas, test_solution_du_petit_cas,
             test_ruptures_et_calendrier_du_petit_cas, test_rayon_du_petit_cas,
             test_pl_commandes_6_produits, test_pl_rayon_6_produits,
             test_lecture_csv, test_application_sur_50_produits]
    for test in tests:
        test()
        print("OK :", test.__name__)
    print(f"\n{len(tests)} tests réussis.")
