# Registre simplifié du traitement — ObRail Europe

## 1. Nom du traitement

**ObRail Europe — Traitement ETL de données ferroviaires européennes**

---

## 2. Responsable du traitement

Projet académique réalisé dans le cadre de la MSPR TPRE612.

Le traitement est réalisé à des fins pédagogiques pour démontrer la mise en œuvre d’un processus ETL, d’une base de données, d’une API REST et d’un dashboard.

---

## 3. Finalité du traitement

Le traitement a pour finalité de collecter, transformer, stocker et visualiser des données ferroviaires européennes.

Les objectifs sont :

- extraire des données depuis plusieurs sources ;
- harmoniser les formats ;
- construire un modèle relationnel ;
- charger les données dans PostgreSQL ;
- contrôler la qualité des données ;
- exposer les données via une API REST ;
- présenter les indicateurs dans un dashboard Streamlit.

---

## 4. Base légale

Le projet est réalisé dans un cadre académique et pédagogique.

Les données utilisées sont des données ferroviaires ouvertes ou publiques.  
Le projet ne traite pas de données personnelles.

---

## 5. Catégories de données traitées

Les catégories de données traitées sont :

- pays ;
- villes ;
- gares ;
- coordonnées géographiques de gares ;
- opérateurs ferroviaires ;
- sources de données ;
- routes ferroviaires ;
- trajets ;
- horaires ;
- arrêts intermédiaires ;
- contrôles qualité.

---

## 6. Catégories de personnes concernées

Aucune personne physique n’est concernée par le traitement.

Le projet ne contient pas de données relatives à des voyageurs, utilisateurs, clients ou employés.

---

## 7. Données personnelles traitées

Aucune donnée personnelle n’est traitée.

Le projet ne stocke pas :

- de nom ;
- de prénom ;
- d’adresse e-mail ;
- de téléphone ;
- d’adresse personnelle ;
- d’identifiant utilisateur ;
- de données de réservation ;
- de données de paiement ;
- de données sensibles.

---

## 8. Destinataires des données

Les données sont utilisées par les composants suivants du projet :

- scripts d’extraction ;
- scripts de transformation ;
- base PostgreSQL ;
- API FastAPI ;
- dashboard Streamlit ;
- utilisateur du projet académique.

Les données ne sont pas transmises à des tiers dans le cadre du projet.

---

## 9. Sources des données

Les sources utilisées sont :

- Back-on-Track Night Train Data ;
- SNCF GTFS ;
- Gares de voyageurs SNCF ;
- Wikipedia — List of busiest railway stations in Europe ;
- European Sleeper Timetable.

Chaque source est documentée dans la table `data_source` et dans les fichiers `metadata.json` générés lors de l’extraction.

---

## 10. Durée de conservation

Les données sont conservées pendant la durée du projet académique.

Dans un contexte de production, une durée de conservation devrait être définie selon les besoins métier et les règles internes de l’organisation.

---

## 11. Mesures de sécurité

Les mesures de sécurité appliquées dans le projet sont :

- base PostgreSQL isolée dans Docker ;
- accès local à la base de données ;
- configuration de connexion via variables d’environnement ;
- API REST principalement en lecture ;
- séparation entre données brutes, données transformées et base relationnelle ;
- absence de données personnelles dans le modèle final ;
- documentation de l’origine des données ;
- contrôle qualité des données transformées.

---

## 12. Transfert hors Union européenne

Aucun transfert de données personnelles hors Union européenne n’est réalisé.

Le projet utilise des sources ouvertes accessibles publiquement et ne contient pas de données personnelles.

---

## 13. Analyse des risques

Le risque RGPD est faible car :

- aucune donnée personnelle n’est collectée ;
- aucune donnée sensible n’est traitée ;
- aucune personne physique n’est suivie ou profilée ;
- aucune décision automatisée n’est prise sur des individus ;
- les données sont utilisées uniquement dans un contexte académique.

---

## 14. Conclusion du registre

Le traitement **ObRail Europe** est documenté et limité à des données ferroviaires non personnelles.

Le projet respecte une démarche de conformité adaptée au contexte académique :

- données minimisées ;
- sources tracées ;
- base relationnelle structurée ;
- sécurité locale ;
- absence de données personnelles.
