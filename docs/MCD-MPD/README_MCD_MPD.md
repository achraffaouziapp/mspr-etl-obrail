# README — MCD et MPD du projet ObRail Europe

## 1. Objectif

Ce document explique la différence entre le **MCD** et le **MPD** réalisés pour le projet **ObRail Europe**.

L'objectif est de montrer que la modélisation des données a été pensée à deux niveaux :

- un niveau **conceptuel**, centré sur le métier ;
- un niveau **physique**, centré sur l'implémentation dans PostgreSQL.

---

## 2. Fichiers fournis

Ce livrable contient les éléments suivants :

- `mcd_obrail_europe.png` : modèle conceptuel de données (MCD) ;
- schéma relationnel / physique déjà produit dans le projet : modèle physique de données (MPD).

---

## 3. MCD — Modèle Conceptuel de Données

Le **MCD** présente les grandes entités métier du projet, sans entrer dans les détails techniques de l'implémentation SQL.

Il répond à une logique métier simple :

- un **PAYS** possède des **VILLE** ;
- un **PAYS** possède aussi des **OPERATEUR** ferroviaires ;
- une **VILLE** possède des **GARE** ;
- un **OPERATEUR** exploite des **ROUTE** ;
- une **ROUTE** relie une **GARE** de départ et une **GARE** d'arrivée ;
- une **ROUTE** possède des **TRAJET** ;
- un **TRAJET** appartient à un **TYPE_TRAIN** ;
- un **TRAJET** provient d'une **SOURCE_DONNEES** ;
- un **TRAJET** contient des **ARRET_TRAJET** ;
- une **GARE** est desservie dans **ARRET_TRAJET** ;
- un **TRAJET** possède un **CONTROLE_QUALITE**.

### Entités métier présentes dans le MCD

Le MCD comporte les entités suivantes :

- **PAYS**
- **VILLE**
- **GARE**
- **OPERATEUR**
- **SOURCE_DONNEES**
- **TYPE_TRAIN**
- **ROUTE**
- **TRAJET**
- **ARRET_TRAJET**
- **CONTROLE_QUALITE**

### Pourquoi ce MCD est utile

Le MCD permet de :

- représenter les objets métier du projet de manière claire ;
- montrer les relations principales entre ces objets ;
- justifier la structure générale de la base avant le passage en base relationnelle.

Autrement dit, le MCD répond à la question : **quelles informations métier voulons-nous représenter et comment sont-elles liées entre elles ?**

---

## 4. MPD — Modèle Physique de Données

Le **MPD** correspond à la traduction technique du modèle dans PostgreSQL.

Contrairement au MCD, le MPD contient :

- les **tables** réelles de la base ;
- les **clés primaires** ;
- les **clés étrangères** ;
- les **colonnes** ;
- les **types SQL** ;
- les contraintes relationnelles nécessaires à l'implémentation.

Dans le projet ObRail Europe, le MPD est matérialisé par :

- le script `create_tables.sql` ;
- le schéma relationnel illustré dans le projet ;
- la base PostgreSQL effectivement alimentée par le processus ETL.

### Exemples de traduction du MCD vers le MPD

Quelques exemples simples :

- l'entité **PAYS** devient la table `country` ;
- l'entité **VILLE** devient la table `city` ;
- l'entité **GARE** devient la table `station` ;
- l'entité **OPERATEUR** devient la table `operator` ;
- l'entité **TYPE_TRAIN** devient la table `train_type` ;
- l'entité **SOURCE_DONNEES** devient la table `data_source` ;
- l'entité **ROUTE** devient la table `route` ;
- l'entité **TRAJET** devient la table `trip` ;
- l'entité **ARRET_TRAJET** devient la table `trip_stop` ;
- l'entité **CONTROLE_QUALITE** devient la table `quality_check`.

Le MPD répond donc à la question : **comment le modèle est-il réellement implémenté dans la base PostgreSQL ?**

---

## 5. Justification des choix de modélisation

Les choix de modélisation ont été faits pour répondre au besoin d'analyse ferroviaire d'ObRail Europe.

### Séparation de la géographie

Les entités **PAYS**, **VILLE** et **GARE** sont séparées afin de :

- éviter la redondance ;
- faciliter les analyses par pays ou par ville ;
- garder une structure plus propre pour les jointures.

### Distinction entre route et trajet

La séparation entre **ROUTE** et **TRAJET** permet de distinguer :

- l'axe théorique entre deux gares ;
- l'occurrence concrète d'un trajet, avec ses horaires, sa source et son type.

### Traçabilité des sources

L'entité **SOURCE_DONNEES** permet d'identifier l'origine des informations chargées dans la base.

C'est particulièrement important dans ce projet, car les données proviennent de plusieurs sources hétérogènes : GTFS, JSON, CSV et scraping HTML.

### Contrôle de qualité dédié

L'entité **CONTROLE_QUALITE** permet d'isoler les indicateurs de qualité des trajets :

- valeurs manquantes ;
- erreurs d'horaires ;
- doublons ;
- score qualité.

Cette séparation rend les contrôles plus lisibles et plus exploitables dans le tableau de bord.

---

## 6. Différence simple entre MCD et MPD

En résumé :

- le **MCD** est une vision **métier** ;
- le **MPD** est une vision **technique**.

Le MCD dit :

> « Un pays possède des villes, une ville possède des gares, une route relie des gares, un trajet provient d'une source et appartient à un type de train. »

Le MPD dit :

> « Ces objets sont implémentés dans PostgreSQL sous forme de tables, avec des clés primaires, des clés étrangères et des types de colonnes. »

---

## 7. Conclusion

Le projet ObRail Europe dispose donc désormais :

- d'un **MCD**, qui formalise les entités métier et leurs relations ;
- d'un **MPD**, qui formalise l'implémentation réelle dans PostgreSQL.

Cette double modélisation permet de répondre de manière plus complète aux attentes du cahier des charges et de la grille de compétences.
