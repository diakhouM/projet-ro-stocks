# Gestion des stocks d'un Super U : dossier de Recherche Opérationnelle

Sujet 3 du cours : « Problème de gestion des stocks ».

**Application en ligne : https://projet-ro-stocks.streamlit.app/**

Le projet répond à 3 questions avec les méthodes du cours (programmation linéaire, simplexe) :

1. **Quand y a-t-il rupture ?**
2. **Quand et combien commander ?**
3. **Comment répartir le stock entre le rayon et la réserve ?**

Il procède en deux temps :

- **Partie 2 du dossier : un magasin de 2 produits, résolu à la main.** Méthode graphique,
  méthode des sommets et simplexe en tableaux, pour comprendre chaque étape.
- **Partie 3 : une application Python** qui refait la même démarche pour un nombre quelconque
  de produits (2, 6, 100, 1 000...). Elle est vérifiée sur le cas à 2 produits, puis appliquée
  aux 6 produits d'un Super U (données imaginaires).

Aucun solveur n'est utilisé : l'algorithme du simplexe du cours est programmé dans `simplexe.py`.

## Comment lancer l'application

Il faut Python avec pandas et numpy (et matplotlib pour les figures).
Dans un terminal ouvert dans ce dossier :

```bash
python application.py --deux-produits
```
```bash
python application.py
```
```bash
python application.py --fichier exemple_6_produits.csv
```
```bash
python application.py --aleatoire 100
```

| Commande | Ce qu'elle fait |
|---|---|
| `--deux-produits` | l'exemple résolu à la main (tous les tableaux du simplexe sont affichés) |
| (aucune option) | les 6 produits du Super U |
| `--fichier f.csv` | vos propres produits (voir le format ci-dessous) |
| `--aleatoire N` | N produits générés au hasard (essayez 100, 300, 1000) |

Options pour changer les paramètres : `--budget`, `--reserve`, `--service-min`,
`--volume-rayon`, `--remplissages` (par exemple `--remplissages 2`).

**Format du fichier CSV** (séparateur point-virgule, décimale virgule) : une ligne par produit,
avec les colonnes `produit; demande_jour; cout_achat; prix_vente; delai; stock_securite;
capacite_rayon; volume`. Voir `exemple_2_produits.csv` et `exemple_6_produits.csv`.

## L'application web (Streamlit)

La même application, dans le navigateur : on choisit le cas, on modifie le tableau des
produits, on règle les paramètres, et les réponses aux trois questions s'affichent dans des
onglets (avec les tableaux du simplexe pas à pas pour les petits magasins).

```bash
pip install streamlit
```
```bash
python -m streamlit run app_streamlit.py
```

Le navigateur s'ouvre sur `http://localhost:8501`. Pour arrêter : `Ctrl + C` dans le terminal.

## Les fichiers

| Fichier | Rôle |
|---|---|
| `application.py` | lit les produits, répond aux trois questions, affiche (terminal) |
| `app_streamlit.py` | la même application dans le navigateur (Streamlit) |
| `requirements.txt` | les bibliothèques à installer : `pip install -r requirements.txt` |
| `simplexe.py` | l'algorithme du simplexe en tableaux |
| `modele.py` | les deux programmes linéaires, les ruptures, le calendrier |
| `donnees.py` | les produits et les paramètres (2 et 6 produits) |
| `test_modele.py` | 8 tests, dont le cas à 2 produits résolu à la main |
| `figures.py` | crée les graphiques du rapport (il faut matplotlib) |
| `rapport/rapport.pdf` | le dossier rédigé (17 pages), avec sa source `rapport.tex` |

Pour lancer les tests :

```bash
python test_modele.py
```

## Le modèle

`x_i` = quantité du produit i commandée pour la semaine ; `H_i = 7 × d_i` ; `s` = service minimum.

```
Commandes :  Max  somme( m_i × x_i )
             SC   somme( c_i × x_i ) ≤ budget
                  somme( v_i × x_i ) ≤ réserve
                  s × H_i ≤ x_i ≤ H_i

Rayon :      Max  somme( m_i × n × r_i )         r_i = places du produit i, n = remplissages par jour
             SC   somme( v_i × r_i ) ≤ volume du rayon
                  n × r_i ≤ d_i
```

Changement de variable `x_i = s × H_i + z_i` pour que le simplexe s'applique directement.

## Le cas à 2 produits (à la main)

```
Max  Z = 3a + 5b       SC   2a + 4b ≤ 400 (budget),  a + b ≤ 150 (réserve),  a ≤ 140,  b ≤ 140
```

| Question | Réponse |
|---|---|
| Combien commander ? | a = 100, b = 50, Z = 550 € (2 pivots : 4 puis 0,5) |
| Rupture ? | A à partir du samedi (5 jours couverts), B à partir du mercredi (2,5 jours) ; 570 € perdus |
| Quand commander ? | A le samedi (délai 2), B le vendredi (délai 3) |
| Rayon ou réserve ? | rayon de 30 L : 10 places pour A et 20 pour B, 130 € par jour au lieu de 120 ; 160 € avec 2 remplissages |

## Le cas à 6 produits

- Marge maximale : **5 630,55 € par semaine** (8 pivots), budget dépensé en entier, 185,83 L libres en réserve.
- Ruptures : lait et yaourts à partir du vendredi soir, eau le dimanche (711,45 € perdus par semaine).
- Rayon : 806 € par jour avec le partage actuel, 850,88 € avec le partage optimal, 906 € avec 2 remplissages.

## Passage à l'échelle (données aléatoires)

| Produits | Pivots | Temps |
|---|---|---|
| 6 | 15 | < 0,1 s |
| 100 | 164 | 0,05 s |
| 300 | 516 | 0,4 s |
| 1 000 | 1 648 | environ 8 s |
