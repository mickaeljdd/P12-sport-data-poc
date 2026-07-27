# P12 – Sport Data POC

## Présentation

Ce projet a été réalisé dans le cadre d'un Proof of Concept (POC) autour de la promotion du sport en entreprise.

L'objectif est de développer un pipeline ETL capable de traiter des données RH et sportives, d'enrichir ces données avec les distances domicile–entreprise grâce à Google Routes API, puis de calculer différents indicateurs liés à la mobilité durable et au bien-être des salariés.

Les données produites sont ensuite exploitées dans un tableau de bord Power BI.

---

## Fonctionnalités

Le projet permet de :

- importer les données RH et sportives ;
- calculer les distances domicile–entreprise via Google Routes API ;
- adapter le calcul d'itinéraire au moyen de déplacement déclaré ;
- mettre en cache les distances afin d'éviter les appels API inutiles ;
- générer un historique sportif simulé au premier lancement ;
- ajouter 3 à 10 nouvelles activités à chaque lancement suivant ;
- déterminer les salariés éligibles aux aides à la mobilité ;
- calculer les jours de bien-être et les primes associées ;
- générer des messages Slack ;
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

services/
    Services métier

simulation/
    Génération des activités sportives

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

---

## Installation

Installer les dépendances :

```bash
pip install -r requirements.txt
```

<<<<<<< HEAD
Créer un fichier `.env` à partir de `.env_sample.txt` puis renseigner la clé Google Routes API.
=======
Créer un fichier `.env` à partir de `.env_sample` puis renseigner les paramètres nécessaires.
>>>>>>> 7fa90747e5dabb70273a8c18eddf2aa67f29113f

Pour exécuter les calculs réels Google Routes, configurer :

```dotenv
GOOGLE_MAPS_API_KEY=votre_cle
DISTANCE_PROVIDER=google
```

Pour une exécution locale sans appel externe, conserver :

```dotenv
DISTANCE_PROVIDER=mock
```

La clé API ne doit jamais être ajoutée au dépôt : le fichier `.env` est ignoré par Git.

### Règles métier

Le moyen de déplacement déclaré dans les données RH est considéré comme le moyen majoritaire du salarié. La distance calculée doit être cohérente avec cette déclaration :

- Marche : maximum 15 km ;
- Vélo/Trottinette/Autres : maximum 25 km ;
- autres modes : pas de prime sportive.

Une personne éligible reçoit une prime de 5 % de son salaire brut annuel. Les journées bien-être sont accordées à partir de 15 activités sur 12 mois, à raison de 5 jours.

---

## Exécution

Lancer le pipeline :

```bash
python -m etl.pipeline
```

Les résultats sont générés dans :

```
data/processed/
```

- employees.csv
- activities.csv
- slack_messages.csv

Les données sont aussi chargées dans `database/sport_poc.db`.

Le premier lancement sur une base vide génère un historique de 12 mois. Les lancements suivants fonctionnent en mode incrémental : 3 à 10 nouvelles activités sont ajoutées, avec exactement un nouveau message Slack par activité. Les indicateurs de bien-être restent recalculés sur l'historique complet.

Le cache `data/cache/google_distances.csv` mémorise les distances par adresse et par mode de trajet (`DRIVE`, `WALK`, `BICYCLE`, `TRANSIT`). Il peut être supprimé pour forcer un recalcul complet.

Le pipeline bloque l'exécution lorsqu'il détecte des données RH ou des activités incohérentes : identifiant salarié dupliqué, adresse ou salaire invalide, moyen de déplacement inconnu, date invalide, distance d'activité négative ou salarié inconnu.

---

## Tests

Exécuter les tests :

```bash
python -m pytest
```

Le projet est couvert par une suite de tests unitaires permettant de valider les principaux composants (ETL, services, cache, API Google, génération des activités, etc.).

---

## Tableau de bord

Le fichier Power BI (`powerbi/P12.pbix`) permet de visualiser notamment :

- le nombre de salariés et de sportifs ;
- les activités générées ;
- les salariés éligibles à la mobilité ;
- les primes calculées ;
- les jours de bien-être ;
- la répartition des sports ;
- l'évolution mensuelle des activités.

---

## Test d'envoi Slack

Le pipeline génère les messages Slack mais ne les publie pas
automatiquement afin d'éviter l'envoi de l'historique simulé.

Créer un Incoming Webhook Slack puis renseigner :

```dotenv
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
```
---
## Auteur

Projet réalisé dans le cadre du parcours de formation Data & IA.

<<<<<<< HEAD
---

## Streaming avec Redpanda

Le pipeline peut publier les nouvelles données sous forme d'événements dans Redpanda. Le chargement historique initial reste traité en batch afin d'éviter l'envoi de milliers de notifications. À partir du deuxième lancement, chaque nouvelle activité et chaque message Slack sont publiés individuellement.

### Architecture

```text
Pipeline incrémental
        |
        +--> sport.activities  --> consommateurs métier
        |
        +--> sport.slack       --> consommateur Slack
        |
        +--> sport.monitoring  --> supervision / Redpanda Console
```

SQLite et les exports CSV restent alimentés par le pipeline afin de conserver la compatibilité avec Power BI. Redpanda ajoute une diffusion événementielle découplée, observable dans Redpanda Console.

### Démarrer Redpanda

Docker Desktop et Docker Compose doivent être installés.

```bash
docker compose -f docker-compose.redpanda.yml up -d
```

Redpanda Console est ensuite accessible sur `http://localhost:8080`.

### Activer le streaming

Dans le fichier `.env` :

```dotenv
STREAMING_ENABLED=true
REDPANDA_BOOTSTRAP_SERVERS=localhost:19092
REDPANDA_CLIENT_ID=sport-data-poc
REDPANDA_ACTIVITIES_TOPIC=sport.activities
REDPANDA_SLACK_TOPIC=sport.slack
REDPANDA_MONITORING_TOPIC=sport.monitoring
```

Installer les dépendances puis lancer le pipeline :

```bash
pip install -r requirements.txt
python -m etl.pipeline
```

Lors du premier lancement, seul l'événement de monitoring est publié. Lors des lancements incrémentaux, les nouvelles activités et leurs messages Slack sont également diffusés.

### Consommer les notifications Slack

Dans un terminal séparé :

```bash
python -m scripts.consume_slack_events
```

Le consommateur utilise `SLACK_WEBHOOK_URL` et valide l'offset seulement après un envoi réussi. Un événement non traité reste donc disponible pour une nouvelle tentative.

### Observer les événements

Les topics suivants sont visibles dans Redpanda Console :

- `sport.activities` : nouvelles activités sportives ;
- `sport.slack` : messages Slack prêts à envoyer ;
- `sport.monitoring` : résultats des exécutions du pipeline.

Un consommateur de démonstration permet également d'afficher les événements de monitoring :

```bash
python -m scripts.consume_monitoring_events
```

### Arrêter Redpanda

```bash
docker compose -f docker-compose.redpanda.yml down
```

Pour supprimer également les données persistées dans Redpanda :

```bash
docker compose -f docker-compose.redpanda.yml down -v
```
=======
Projet réalisé dans le cadre du parcours de formation Data & IA.
>>>>>>> 7fa90747e5dabb70273a8c18eddf2aa67f29113f
