# Analyse RGPD — ObRail Europe

## 1. Objectif du document

Ce document explique la démarche RGPD appliquée dans le projet **ObRail Europe**.

Le projet consiste à extraire, transformer, stocker et visualiser des données ferroviaires européennes.  
Il ne s’agit pas d’un projet centré sur des utilisateurs, des voyageurs ou des clients. L’objectif est uniquement d’analyser des données liées au transport ferroviaire : gares, villes, pays, opérateurs, routes, trajets, horaires, arrêts et sources de données.

---

## 2. Nature des données traitées

Les données manipulées dans le projet sont des données ferroviaires issues de sources ouvertes ou publiques.

Les principales catégories de données sont :

- pays ;
- villes ;
- gares ;
- coordonnées géographiques de gares ;
- opérateurs ferroviaires ;
- types de train ;
- sources de données ;
- routes ferroviaires ;
- trajets ;
- horaires de départ et d’arrivée ;
- arrêts intermédiaires ;
- contrôles qualité techniques.

Ces données décrivent des infrastructures, des horaires et des services ferroviaires.  
Elles ne décrivent pas des personnes physiques.

---

## 3. Absence de données personnelles

Le projet ne collecte pas et ne stocke pas de données personnelles.

Aucune des données suivantes n’est présente dans la base :

- nom ou prénom de voyageur ;
- adresse e-mail ;
- numéro de téléphone ;
- adresse postale personnelle ;
- date de naissance ;
- numéro de carte bancaire ;
- identifiant de compte utilisateur ;
- adresse IP d’utilisateur ;
- donnée de géolocalisation d’une personne ;
- information de réservation ;
- historique individuel de voyage ;
- donnée de santé ;
- donnée biométrique ;
- donnée sensible.

Les coordonnées géographiques présentes dans la table `station` correspondent à des lieux publics, c’est-à-dire des gares ferroviaires.  
Elles ne correspondent pas à la position d’une personne physique.

---

## 4. Finalité du traitement

La finalité du projet est de construire un jeu de données ferroviaires exploitable pour :

- centraliser plusieurs sources hétérogènes ;
- structurer les données dans un modèle relationnel ;
- distinguer les trains de jour et les trains de nuit ;
- contrôler la qualité des données transformées ;
- exposer les données via une API REST ;
- visualiser les volumes et les connexions ferroviaires dans un dashboard.

Le traitement est donc limité à un objectif académique et analytique.

---

## 5. Principe de minimisation

Le projet applique une logique de minimisation des données.

Les sources brutes peuvent contenir plus de colonnes que nécessaire, mais le modèle final ne conserve que les informations utiles à l’analyse ferroviaire :

- données géographiques générales ;
- données d’infrastructure ;
- données horaires ;
- données de sources ;
- données de contrôle qualité.

Les informations qui ne sont pas utiles au besoin métier ne sont pas intégrées dans les tables finales.

---

## 6. Traçabilité des sources

La traçabilité est assurée par la table `data_source`.

Cette table permet de conserver :

- le nom de la source ;
- l’URL de la source ;
- le format du fichier source ;
- la date d’extraction ;
- le nom des fichiers bruts ;
- le statut d’import.

Chaque extraction génère également un fichier `metadata.json` dans le dossier `data/raw/`.  
Cela permet de retrouver l’origine des données utilisées dans le pipeline ETL.

---

## 7. Sécurité et accès

Le projet prévoit plusieurs mesures simples de sécurité :

- la base PostgreSQL est lancée dans un conteneur Docker ;
- l’accès à la base est local dans le cadre du projet ;
- les paramètres de connexion sont externalisés dans un fichier `.env` ;
- les services Docker utilisent des variables d’environnement ;
- l’API REST expose uniquement des endpoints de consultation ;
- aucune fonctionnalité d’écriture depuis l’API n’est prévue ;
- aucune donnée personnelle n’est stockée dans la base.

Dans un contexte de production, il faudrait renforcer ces mesures avec une gestion des rôles, des droits d’accès, des mots de passe forts, du chiffrement et une journalisation des accès.

---

## 8. Durée de conservation

Les données sont conservées pendant la durée du projet académique.

Dans un contexte professionnel, une durée de conservation devrait être définie selon :

- la finalité du traitement ;
- les besoins métier ;
- les contraintes réglementaires ;
- la politique interne de l’organisation.

---

## 9. Analyse d’impact

Une analyse d’impact approfondie n’est pas nécessaire dans le cadre de ce projet, car :

- aucune donnée personnelle n’est collectée ;
- aucune donnée sensible n’est traitée ;
- aucun profilage de personne physique n’est réalisé ;
- aucune décision automatisée concernant des individus n’est produite ;
- le projet traite uniquement des données ferroviaires ouvertes ou publiques.

Le niveau de risque RGPD est donc faible.

---

## 10. Conclusion

Le projet **ObRail Europe** respecte une démarche RGPD adaptée à son contexte.

Même si le projet ne traite pas de données personnelles, il applique des principes importants :

- analyse de la nature des données ;
- minimisation des données conservées ;
- traçabilité des sources ;
- documentation du traitement ;
- sécurisation de la configuration ;
- séparation entre données brutes, données transformées, API et dashboard.

Cette démarche permet de montrer que la base de données a été conçue de manière structurée, documentée et compatible avec les principes du RGPD.
