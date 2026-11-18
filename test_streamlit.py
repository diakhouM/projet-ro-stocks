"""
test_streamlit.py : verifie l'interface Streamlit en mode "produits generes au hasard".

Probleme corrige : quand on changeait le nombre de produits, le budget et la reserve
gardaient la valeur du premier tirage, et l'application affichait l'erreur
"programme admissible vide". Ils suivent maintenant la taille du magasin (85 % du cout
et 90 % du volume de la demande).

Ce test a besoin de Streamlit (pip install streamlit). Sans Streamlit, il est ignore.

Lancer :  python test_streamlit.py
"""

import math

import donnees as d
from application import parametres_proportionnels, produits_aleatoires


def lancer_application():
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file("app_streamlit.py", default_timeout=120).run()
    at.sidebar.selectbox[0].set_value("Produits générés au hasard").run()
    return at


def test_budget_et_reserve_suivent_la_taille_du_magasin():
    at = lancer_application()
    for nombre in (100, 300, 10, 1000):
        if nombre != 100:
            at.sidebar.slider[0].set_value(nombre).run()
        assert not at.exception, at.exception
        assert not at.error, f"{nombre} produits : {[e.value for e in at.error]}"
        _, attendu = produits_aleatoires(nombre)
        assert math.isclose(at.sidebar.number_input[0].value, attendu["budget"], abs_tol=1)
        assert math.isclose(at.sidebar.number_input[1].value, attendu["reserve"], abs_tol=1)
        print(f"OK : {nombre} produits, budget {attendu['budget']:,.0f} €, "
              f"réserve {attendu['reserve']:,.0f} litres".replace(",", " "))


def test_service_minimum_trop_eleve_affiche_un_message():
    """Au-dela de 85 %, le budget ne suffit plus : l'application l'explique."""
    at = lancer_application()
    at.sidebar.slider[1].set_value(0.9).run()
    assert not at.exception
    assert len(at.error) == 1 and "Pas de solution" in at.error[0].value
    print("OK : service minimum de 90 %, message d'erreur clair")


if __name__ == "__main__":
    try:
        import streamlit  # noqa: F401
    except ImportError:
        print("Streamlit n'est pas installé : test ignoré (pip install streamlit).")
        raise SystemExit(0)
    test_budget_et_reserve_suivent_la_taille_du_magasin()
    test_service_minimum_trop_eleve_affiche_un_message()
    print("\n2 tests réussis.")
