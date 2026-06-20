# Inventaire des données — Analyse RGPD

## 1. Objectif du document

Ce document recense les tables du modèle relationnel **ObRail Europe** et analyse si elles contiennent ou non des données personnelles.

L’objectif est de montrer que le modèle de données final ne stocke pas d’informations relatives à des personnes physiques identifiées ou identifiables.

---

## 2. Inventaire des tables

| Table | Données stockées | Données personnelles ? | Justification |
|---|---|---:|---|
| `country` | Identifiant du pays, nom du pays, code pays | Non | La table contient uniquement des informations géographiques générales. |
| `city` | Identifiant de la ville, nom de la ville, pays associé | Non | Une ville est une donnée géographique publique, pas une information sur une personne. |
| `station` | Identifiant de gare, nom de gare, code gare, latitude, longitude, fuseau horaire, ville associée | Non | Les coordonnées représentent des gares, c’est-à-dire des lieux publics. Elles ne localisent pas une personne physique. |
| `operator` | Identifiant opérateur, nom opérateur, code opérateur, pays associé | Non | Les opérateurs ferroviaires sont des entités ou personnes morales, pas des individus. |
| `train_type` | Identifiant du type de train, nom du type : `day` ou `night` | Non | Il s’agit d’une classification métier des trajets. |
| `data_source` | Source, URL, format, date d’extraction, licence, fichier brut, statut d’import | Non | La table documente l’origine technique des données. Elle ne contient pas de données personnelles. |
| `route` | Gare de départ, gare d’arrivée, opérateur, distance éventuelle | Non | Une route décrit une relation ferroviaire entre deux gares publiques. |
| `trip` | Trajet, route, type de train, source, code trajet, date de service, horaires, durée, estimation CO₂ | Non | Un trajet décrit un service ferroviaire. Il ne contient aucune information sur les passagers. |
| `trip_stop` | Arrêts d’un trajet, ordre des arrêts, horaires d’arrivée et de départ | Non | Les arrêts décrivent le parcours théorique ou structuré d’un train. |
| `quality_check` | Identifiant du contrôle, trajet concerné, anomalies détectées, score qualité, message d’erreur, date de contrôle | Non | La table contient des contrôles techniques sur les données, pas des informations sur des personnes. |

---

## 3. Colonnes sensibles ou personnelles

Aucune table du modèle final ne contient :

- nom ou prénom d’une personne physique ;
- adresse e-mail ;
- téléphone ;
- adresse personnelle ;
- identifiant utilisateur ;
- donnée de paiement ;
- donnée de réservation ;
- historique individuel de déplacement ;
- adresse IP ;
- donnée de santé ;
- donnée biométrique ;
- donnée sensible.

---

## 4. Données géographiques

Le projet contient des données géographiques, principalement dans la table `station`.

Ces données sont :

- la latitude d’une gare ;
- la longitude d’une gare ;
- le fuseau horaire d’une gare ;
- la ville et le pays associés à la gare.

Ces informations sont considérées comme des données relatives à des lieux publics.  
Elles ne permettent pas d’identifier ou de suivre une personne physique.

---

## 5. Données horaires

Les tables `trip` et `trip_stop` contiennent des horaires de départ et d’arrivée.

Ces horaires décrivent des trajets ferroviaires et des arrêts de train.  
Ils ne correspondent pas à des horaires personnels ou à des réservations individuelles.

---

## 6. Données de qualité

La table `quality_check` contient des informations techniques sur la qualité des données.

Elle permet d’identifier :

- des valeurs manquantes ;
- des erreurs horaires ;
- des doublons potentiels ;
- un score qualité.

Ces contrôles portent sur les trajets du jeu de données et non sur des personnes.

---

## 7. Conclusion

L’inventaire montre que le modèle relationnel **ObRail Europe** ne contient pas de données personnelles.

Les données stockées sont limitées à des informations ferroviaires, géographiques, horaires, techniques et analytiques.  
Le projet respecte donc le principe de minimisation et présente un risque RGPD faible.
