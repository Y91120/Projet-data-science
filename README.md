# Projet-data-science
*Par Camille Foix et Eliott Sarfati*

## Présentation du dépôt

Notre projet est localisé dans le notebook main.ipynb, qui constitue le rapport final.

Le dossier data contient nos différentes sources de données, récupérées via la partie I. Collecte du main. Néanmoins, elle est longue à exécuter donc les données sont sauvegardées pour une exécution immédiate du reste du main.
Ce dossier est subdivisé en 4 sous-dossiers : 
- gtfs contenant les données GTFS d'Ile de France Mobilités
- poi contenant les POI récupérés via Open Street Map
- validations contenant les données de validations sur le réseau ferré et le réseau de surface
- ref contenant des fichiers généraux sur les lignes de transports, utilisés uniquement dans l'annexe

Le dossier Traces de recherches contient les codes et notebooks ayant servi à la construction de notre projet. Ils n'apportent pas plus d'informations pour répondre à la problématique. On y trouve en particulier annexe-rds.ipynb qui contient la même sorte d'analyse que le projet appliqué au réseau de surface (bus, tramway). Nous avons décidé de limiter le projet au réseau ferré, mais avons conservé nos traces de recherche sur le réseau de surface.