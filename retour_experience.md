# Retour d'expérience de l'EI proposé à CentraleSupélec

## Organisation pratique de l'EI

Enseignement d'Intégration proposé aux étudiants de 1ère année de CentraleSupélec ayant choisi la séquence thématique Big Data & Santé.

Encadrement par Sonia Priou et Charline Jean, avec l'accompagnement d'Arthur Tenenhaus et Laurent Le Brusquet (encadrants de la ST).

40 élèves ont suivi l'enseignement, répartis en 8 groupes de 5.

L'EI a duré 1 semaine complète, durant laquelle nous avons compartimenté le planning de la manière suivante :
- chaque jour = un nouveau type de données/enjeu de traitement (Déduplication, NLP, analyses bio, ...)
- présentation théorique le matin (~1h) suivie d'un exercice associé, avec la correction donnée + parcourue en live avec les étudiants
- avancement en autonomie sur le projet l'après-midi, en appliquant les méthodes vu le matin
  
Livrable requis:
- notebook de code reproductible
- court article scientifique 

## Résultats

Les livrables fournis par les étudiants sont disponibles dans le dossier `final_project/livrables_etudiants`.

## Améliorations pour une potentielle reconduite du projet
  
| Catégorie | Commentaire |
| :------------------ | :----------|
|Exos |	Ne pas mettre les corrections ? |
|Exos |	Couper le TD 4 en 2 --> assez lourd |
|Général |	Mettre à jour la version de numpy pour qu'elle coïncide avec celle requise par eds-nlp |
|Général |	Mettre "ne ... pas" dans les négations d'edsnlp |
|Global |	Déduplication : pourquoi on fait supprimer les person_id dupliqués ? Il vaut mieux propager les unique_person_id dans les autres tables et faire des groupby |par patient ? (= plusieurs visites par patient) |
|Projet |	Attention aux tables inutiles (dedup et note_nlp) |
|Projet |	Se rapprocher plus de la littérature pour les valeurs de la table (notamment % de fumeurs parmi les K) |
|Projet |	Augmenter l'effet de l'âge en univarié |
|Projet |	Séparer facteurs de risques et symptômes du cancer ? |
|Projet |	Lien hémoglobines / Cancer --> Baisse de l'hémoglobine chez les K ? |
|Projet |	Baisser le pourcentage de CIM-10 alcool |
|Projet |	Un jeu de données par groupe |
|Projet |	Augmenter le taux d'urée moyen (trop faible par rapport à la vraie vie) |
|Projet |	Réduire l'impact des antécécdents familiaux |