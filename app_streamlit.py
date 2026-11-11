"""
app_streamlit.py : l'application web du projet (Streamlit).

Elle utilise exactement le meme calcul que application.py (simplexe du cours),
mais avec une interface : on choisit ou modifie les produits, on regle les parametres,
et on lit les reponses aux trois questions dans des onglets.

Lancer :  python -m streamlit run app_streamlit.py
"""

import pandas as pd
import streamlit as st

import donnees as d
from application import lire_produits, produits_aleatoires, repondre

SEUIL_DETAIL = 15          # jusqu'a 15 produits, on peut afficher les tableaux du simplexe
NB_MAX_GRAPHIQUE = 30      # au-dela, les graphiques montrent seulement 30 produits

CAS = ["Exemple à 2 produits (résolu à la main)", "6 produits d'un Super U",
       "Fichier CSV", "Produits générés au hasard"]

COLONNES_SAISIE = ["produit", "demande_jour", "cout_achat", "prix_vente", "delai",
                   "stock_securite", "capacite_rayon", "volume"]

NOMS_AFFICHES = {
    "produit": "Produit", "minimum": "Minimum", "quantite_optimale": "À commander",
    "maximum": "Demande de la semaine", "non_servi": "Demande non servie",
    "saturee": "Situation", "jours_couverts": "Jours couverts", "rupture": "Rupture",
    "marge_perdue": "Marge perdue (€)", "delai": "Délai (jours)",
    "jour_de_commande": "Jour de commande", "point_de_commande": "Point de commande",
    "demande_jour": "Demande par jour", "capacite_rayon": "Places actuelles",
    "places_optimales": "Places optimales", "ventes_actuelles": "Ventes par jour (actuel)",
    "ventes_optimales": "Ventes par jour (optimal)",
    "marge_actuelle": "Marge par jour (actuel, €)",
    "marge_optimale": "Marge par jour (optimal, €)",
    "contrainte": "Ressource", "utilise": "Utilisé", "limite": "Disponible",
    "ecart": "Reste", "etape": "Étape", "entrante": "Variable entrante",
    "profit_marginal": "Profit marginal", "sortante": "Variable sortante",
    "rapport": "Rapport", "pivot": "Pivot",
}


# ---------------------------------------------------------------------------
# 1. Les donnees : choix du cas, tableau modifiable
# ---------------------------------------------------------------------------
def donnees_du_cas(cas):
    """Renvoie les produits et les parametres par defaut du cas choisi."""
    if cas == CAS[0]:
        return d.PRODUITS_2, dict(d.PARAMETRES_2_PRODUITS)
    if cas == CAS[1]:
        parametres = {"budget": d.BUDGET_HEBDO, "reserve": d.CAPACITE_RESERVE,
                      "service_min": d.SERVICE_MIN, "volume_rayon": d.VOLUME_RAYON}
        return d.PRODUITS, parametres
    if cas == CAS[2]:
        fichier = st.sidebar.file_uploader("Fichier CSV (séparateur ;)", type="csv")
        if fichier is None:
            st.info("Chargez un fichier CSV dans le menu de gauche. "
                    "Modèle : `exemple_6_produits.csv`.")
            st.stop()
        produits = lire_produits(fichier)
        parametres = {"budget": d.BUDGET_HEBDO, "reserve": d.CAPACITE_RESERVE,
                      "service_min": d.SERVICE_MIN, "volume_rayon": 0}
        return produits, parametres
    nombre = st.sidebar.slider("Nombre de produits", 10, 1000, 100, step=10)
    return produits_aleatoires(nombre)


def preparer_produits(produits):
    """Ajoute le nom court et la marge, et verifie les valeurs."""
    produits = produits.dropna(subset=COLONNES_SAISIE).reset_index(drop=True)
    produits["nom_court"] = [f"p{i + 1}" for i in range(len(produits))]
    produits["marge"] = produits["prix_vente"] - produits["cout_achat"]
    if produits.empty:
        st.error("Aucun produit à calculer.")
        st.stop()
    if (produits["demande_jour"] <= 0).any() or (produits["cout_achat"] < 0).any() \
            or (produits["volume"] < 0).any():
        st.error("La demande doit être positive, le coût et le volume ne peuvent pas être négatifs.")
        st.stop()
    return produits


def parametres_lateraux(cas, produits, defauts):
    """Zone de gauche : budget, reserve, service minimum, rayon, remplissages."""
    st.sidebar.header("Paramètres")
    cle = cas[:10]                           # une cle par cas, pour reinitialiser les valeurs
    budget = st.sidebar.number_input("Budget par semaine (€)", min_value=0.0,
                                     value=float(defauts["budget"]), step=100.0,
                                     key=f"budget_{cle}")
    reserve = st.sidebar.number_input("Capacité de la réserve (litres)", min_value=0.0,
                                      value=float(defauts["reserve"]), step=100.0,
                                      key=f"reserve_{cle}")
    service_min = st.sidebar.slider("Service minimum (part de la demande)", 0.0, 1.0,
                                    float(defauts["service_min"]), step=0.05,
                                    key=f"service_{cle}")

    volume_actuel = float((produits["capacite_rayon"] * produits["volume"]).sum())
    calculer = st.sidebar.checkbox("Volume du rayon = volume des places actuelles", value=True)
    if calculer:
        volume_rayon = volume_actuel
        st.sidebar.caption(f"Volume du rayon : {nombre(volume_actuel, 1)} litres")
    else:
        volume_rayon = st.sidebar.number_input("Volume du rayon (litres)", min_value=0.0,
                                               value=volume_actuel, step=50.0)
    remplissages = st.sidebar.radio("Remplissages du rayon par jour", [1, 2, 3], horizontal=True)
    return budget, reserve, service_min, volume_rayon, remplissages


# ---------------------------------------------------------------------------
# 2. L'affichage
# ---------------------------------------------------------------------------
def nombre(x, decimales=0):
    """Formate un nombre a la francaise : 5 630,55 (espace pour les milliers, virgule)."""
    return f"{x:,.{decimales}f}".replace(",", " ").replace(".", ",")


def montrer(tableau, **options):
    """Affiche un tableau avec des noms de colonnes en francais."""
    st.dataframe(tableau.rename(columns=NOMS_AFFICHES).round(2), hide_index=True,
                 width="stretch", **options)


def graphique(tableau, colonnes, titre):
    """Diagramme en barres (les NB_MAX_GRAPHIQUE premiers produits)."""
    t = tableau.set_index("produit")[colonnes].rename(columns=NOMS_AFFICHES)
    if len(t) > NB_MAX_GRAPHIQUE:
        st.caption(f"{titre} : graphique limité aux {NB_MAX_GRAPHIQUE} premiers produits.")
        t = t.head(NB_MAX_GRAPHIQUE)
    else:
        st.caption(titre)
    st.bar_chart(t, stack=False)        # barres cote a cote, pas empilees


def onglet_commandes(r):
    st.subheader("Combien commander ?")
    montrer(r["commandes"][["produit", "minimum", "quantite_optimale", "maximum",
                            "saturee"]])
    graphique(r["commandes"], ["minimum", "quantite_optimale", "maximum"],
              "Quantité à commander, entre le minimum et la demande de la semaine")
    st.markdown("**Budget et réserve**")
    montrer(r["ressources"])
    ecarts = r["ressources"]
    for _, ligne in ecarts.iterrows():
        if ligne["saturee"] == "oui":
            st.write(f"- **{ligne['contrainte']}** : entièrement utilisé, c'est un facteur limitant.")
        else:
            st.write(f"- **{ligne['contrainte']}** : il en reste {ligne['ecart']:.1f}, "
                     "ce n'est pas un facteur limitant.")


def onglet_ruptures(r):
    st.subheader("Quand y a-t-il rupture ?")
    st.write("La demande non servie se lit dans les variables d'écart du tableau final. "
             "Avec une livraison le lundi matin, la commande tient « jours couverts » jours.")
    ruptures = r["ruptures"]
    en_rupture = ruptures[ruptures["rupture"] != "aucune"]
    st.write(f"**{len(en_rupture)} produit(s) sur {len(ruptures)}** en rupture avant la fin "
             f"de la semaine. Marge perdue : **{nombre(ruptures['marge_perdue'].sum(), 2)} €** "
             "par semaine.")
    if len(ruptures) > SEUIL_DETAIL:
        montrer(en_rupture.sort_values("marge_perdue", ascending=False).head(20)
                [["produit", "jours_couverts", "rupture", "non_servi", "marge_perdue"]])
    else:
        montrer(ruptures[["produit", "quantite_optimale", "non_servi", "jours_couverts",
                          "rupture", "marge_perdue"]])
    graphique(ruptures, ["jours_couverts"], "Jours de vente couverts (7 = pas de rupture)")


def onglet_calendrier(r):
    st.subheader("Quand commander ?")
    st.write("Pour être livré le lundi matin, on commande « délai » jours avant. "
             "Le point de commande est la demande pendant le délai plus le stock de sécurité.")
    montrer(r["calendrier"])


def onglet_rayon(r, remplissages):
    st.subheader("Rayon ou réserve ?")
    rayon = r["rayon"]
    actuel, optimal = rayon["marge_actuelle"].sum(), rayon["marge_optimale"].sum()
    st.write(f"Avec **{remplissages} remplissage(s)** par jour : "
             f"**{nombre(actuel, 2)} €** par jour avec le partage actuel, "
             f"**{nombre(optimal, 2)} €** avec le partage optimal "
             f"(gain : {nombre(optimal - actuel, 2)} € par jour).")
    if optimal - actuel < 0.005:
        st.success("Avec ce nombre de remplissages, le rayon actuel suffit déjà à servir "
                   "toute la demande : il n'y a rien à redistribuer.")
    montrer(rayon[["produit", "demande_jour", "capacite_rayon", "places_optimales",
                   "ventes_actuelles", "ventes_optimales"]])
    graphique(rayon, ["capacite_rayon", "places_optimales", "demande_jour"],
              "Places en rayon : actuelles, optimales, et demande par jour")


def onglet_simplexe(r):
    st.subheader("Le simplexe pas à pas")
    for nom, cle in [("commandes", "simplexe_commandes"), ("rayon", "simplexe_rayon")]:
        resultat = r[cle]
        st.markdown(f"**Programme « {nom} »** : {len(resultat['pivots'])} pivots")
        montrer(resultat["pivots"])
        for i, tableau in enumerate(resultat["tableaux"]):
            with st.expander(f"Tableau {i + 1}" + (" (final)" if i == len(resultat["tableaux"]) - 1 else "")):
                st.dataframe(tableau.round(3), hide_index=True, width="stretch")


# ---------------------------------------------------------------------------
# 3. La page
# ---------------------------------------------------------------------------
def main():
    st.set_page_config(page_title="Gestion des stocks", page_icon="📦", layout="wide")
    st.title("Gestion des stocks d'un supermarché")
    st.caption("Quand y a-t-il rupture ? Quand et combien commander ? "
               "Comment répartir le stock entre le rayon et la réserve ? "
               "Calcul par l'algorithme du simplexe.")

    cas = st.sidebar.selectbox("Cas étudié", CAS)
    produits, defauts = donnees_du_cas(cas)

    st.subheader("Les produits")
    if len(produits) <= 30:
        st.caption("Vous pouvez modifier les valeurs ou ajouter des lignes.")
        saisie = st.data_editor(produits[COLONNES_SAISIE], num_rows="dynamic",
                                hide_index=True, width="stretch", key=f"produits_{cas[:10]}")
    else:
        st.caption(f"{len(produits)} produits (tableau en lecture seule).")
        saisie = produits[COLONNES_SAISIE]
        st.dataframe(saisie, hide_index=True, width="stretch", height=250)
    produits = preparer_produits(saisie)

    budget, reserve, service_min, volume_rayon, remplissages = \
        parametres_lateraux(cas, produits, defauts)

    try:
        reponses = repondre(produits, budget, reserve, service_min, volume_rayon,
                            nb_remplissages=remplissages,
                            detail=len(produits) <= SEUIL_DETAIL)
    except ValueError as erreur:
        st.error(f"Pas de solution : {erreur} Baissez le service minimum ou augmentez "
                 "le budget et la réserve.")
        st.stop()

    ruptures, rayon = reponses["ruptures"], reponses["rayon"]
    colonnes = st.columns(4)
    colonnes[0].metric("Marge par semaine", f"{nombre(reponses['marge'])} €")
    colonnes[1].metric("Marge perdue (ruptures)", f"{nombre(ruptures['marge_perdue'].sum())} €")
    colonnes[2].metric("Produits en rupture",
                       f"{(ruptures['rupture'] != 'aucune').sum()} sur {len(produits)}")
    colonnes[3].metric("Gain du rayon par jour",
                       f"{nombre(rayon['marge_optimale'].sum() - rayon['marge_actuelle'].sum())} €")

    noms = ["Combien commander", "Rupture", "Quand commander", "Rayon ou réserve"]
    if len(produits) <= SEUIL_DETAIL:
        noms.append("Simplexe pas à pas")
    onglets = st.tabs(noms)
    with onglets[0]:
        onglet_commandes(reponses)
    with onglets[1]:
        onglet_ruptures(reponses)
    with onglets[2]:
        onglet_calendrier(reponses)
    with onglets[3]:
        onglet_rayon(reponses, remplissages)
    if len(produits) <= SEUIL_DETAIL:
        with onglets[4]:
            onglet_simplexe(reponses)
    st.caption(f"Calcul : {len(reponses['simplexe_commandes']['pivots']) + len(reponses['simplexe_rayon']['pivots'])} "
               f"pivots du simplexe en {reponses['duree']:.2f} secondes.")


main()
