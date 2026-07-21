# P12 – Sport Data POC

## Présentation

Ce projet a été réalisé dans le cadre d'un Proof of Concept (POC) autour de la promotion du sport en entreprise.

L'objectif est de développer un pipeline ETL capable de traiter des données RH et sportives, d'enrichir ces données avec les distances domicile–entreprise grâce à Google Routes API, puis de calculer différents indicateurs liés à la mobilité durable et au bien-être des salariés.

Lors du premier lancement, le pipeline génère un historique complet d'activités sportives simulées. Les exécutions suivantes fonctionnent en mode incrémental en ajoutant uniquement de nouvelles activités.

Les données produites sont stockées dans une base SQLite, exportées au format CSV et exploitées dans un tableau de bord Power BI.

---

## Fonctionnalités

Le projet permet de :

- importer les données RH et sportives ;
- calculer les distances domicile–entreprise via Google Routes API ;
- adapter le calcul d'itinéraire au moyen de déplacement déclaré ;
- mettre en cache les distances afin d'éviter les appels API inutiles ;
- générer un historique d'activités sportives simulées ;
- générer de nouvelles activités lors des exécutions suivantes ;
- déterminer les salariés éligibles aux aides à la mobilité ;
- calculer les jours de bien-être et les primes associées ;
- générer et envoyer des notifications Slack pour les nouvelles activités ;
- enregistrer les exécutions du pipeline (monitoring) ;
- exporter les résultats au format CSV ;
- visualiser les résultats dans Power BI.

---

## Structure du projet

```
data/
    raw/            Données sources
    processed/      Données générées
    cache/          Cache des distances Google

database/
    Gestion de la base SQLite

etl/
    Pipeline ETL

monitoring/
    Suivi des exécutions

services/
    Services métier

simulation/
    Génération des activités

tests/
    Tests unitaires

powerbi/
    Tableau de bord
```

---

## Technologies utilisées

- Python
- Pandas
- SQLite
- Google Routes API
- Pytest
- Power BI
- Slack Incoming Webhooks

---

## Installation

Installer les dépendances :

```bash
pip install -r requirements.txt
```

Créer un fichier `.env` à partir de `.env_sample` puis renseigner les paramètres nécessaires.

Pour utiliser Google Routes API :

```dotenv
GOOGLE_MAPS_API_KEY=votre_cle
DISTANCE_PROVIDER=google
```

Pour utiliser le calcul simulé :

```dotenv
DISTANCE_PROVIDER=mock
```

Pour activer les notifications Slack :

```dotenv
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
```

Le fichier `.env` ne doit jamais être versionné.

---

## Règles métier

Le moyen de déplacement déclaré dans les données RH est considéré comme le moyen principal du salarié.

Les règles d'éligibilité sont les suivantes :

- Marche : distance maximale de 15 km ;
- Vélo, trottinette ou autre mobilité douce : distance maximale de 25 km ;
- Autres moyens de transport : non éligibles.

Une personne éligible reçoit une prime représentant **5 % de son salaire brut annuel**.

Les journées de bien-être sont accordées à partir de **15 activités sportives sur une période glissante de 12 mois**, à raison de **5 jours**.

---

## Exécution

Lancer le pipeline :

```bash
python -m etl.pipeline
```

### Premier lancement

Le pipeline :

- importe les données RH ;
- calcule les distances ;
- génère l'historique complet des activités ;
- calcule les indicateurs métier ;
- alimente la base SQLite ;
- exporte les fichiers CSV.

Aucune notification Slack n'est envoyée lors de cette première exécution.

### Exécutions suivantes

Le pipeline :

- génère uniquement de nouvelles activités ;
- ajoute ces activités dans la base SQLite ;
- recalcule les indicateurs métier ;
- exporte les nouvelles données ;
- envoie une notification Slack pour chaque nouvelle activité ;
- enregistre les statistiques d'exécution dans le tableau de monitoring.

Les résultats sont générés dans :

```
data/processed/
```

- employees.csv
- activities.csv
- slack_messages.csv
- pipeline_runs.csv

Les données sont également enregistrées dans :

```
database/sport_poc.db
```

Le cache `data/cache/google_distances.csv` mémorise les distances par adresse et par mode de trajet (`DRIVE`, `WALK`, `BICYCLE`, `TRANSIT`). Il peut être supprimé afin de forcer un recalcul complet.

Le pipeline valide les données avant traitement et interrompt l'exécution lorsqu'une incohérence est détectée.

---

## Monitoring

Chaque exécution du pipeline est enregistrée avec notamment :

- date de début ;
- date de fin ;
- durée d'exécution ;
- statut (SUCCESS ou FAILED) ;
- nombre d'activités générées ;
- nombre de messages Slack générés ;
- coût des primes mobilité ;
- nombre de jours bien-être accordés ;
- message d'erreur éventuel.

Ces informations sont utilisées dans le tableau de bord Power BI.

---

## Tests

Lancer les tests :

```bash
python -m pytest
```

Le projet est couvert par **76 tests unitaires** validant :

- le pipeline ETL ;
- la validation des données ;
- le repository SQLite ;
- le calcul des distances ;
- le cache Google ;
- les règles d'éligibilité ;
- la génération historique et incrémentale des activités ;
- les notifications Slack ;
- le monitoring des exécutions.

---

## Tableau de bord

Le tableau de bord Power BI (`powerbi/P12.pbix`) permet notamment de visualiser :

- les salariés et les sportifs ;
- les activités sportives générées ;
- les primes mobilité ;
- les jours de bien-être ;
- la répartition des sports ;
- l'évolution des activités ;
- les notifications Slack ;
- le suivi des exécutions du pipeline (monitoring).

---

## Auteur

Mickael DARMON

Projet réalisé dans le cadre du parcours de formation Data & IA.
