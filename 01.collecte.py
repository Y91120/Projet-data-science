import os
import io
import zipfile
import logging
import requests
import pandas as pd
import geopandas as gpd
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# CHEMINS
# ---------------------------------------------------------------------------
DATA_DIR = Path("Projet-data-science/data")
GTFS_DIR = DATA_DIR / "gtfs"
POI_DIR  = DATA_DIR / "poi"

GTFS_DIR.mkdir(parents=True, exist_ok=True)
POI_DIR.mkdir(parents=True, exist_ok=True)

# BBOX Ile-de-France
IDF_BBOX = {
    "south": 48.0,
    "north": 49.2,
    "west": 1.4,
    "east": 3.6,
}

DEPARTEMENTS_IDF = ["75", "77", "78", "91", "92", "93", "94", "95"]

# POI : séléction des POI les plus utiles pour notre analyse
POI_CATEGORIES = {
    "commerce": {"tags": {"shop": True}},
    "restaurants": {"tags": {"amenity": "restaurant"}},
    "bureaux": {"tags": {"office": True}},
    "administration": {"tags": {"amenity": ["townhall", "Government"]}},
    "culture": {"tags": {"amenity": ["theatre", "museum", "cinema", "arts_centre"]}},
    "education": {"tags": {"amenity": "school"}},
    "sante": {"tags": {"amenity": "hospital"}},
    "logement": {"tags": {"building": ["residential", "apartments", "house", "detached", "semi-detached"]}},
    "monument": {"tags": {"historic": "monument", "tourism": "attraction"}},
    "sports": {"tags": {"Leisure": ["sports_centre", "pitch", "stadium", "swimming_pool"]}},
    "commerce_proximite": {"tags":{"amenity": ["cafe","bar","fast_food"], "shop": ["bakery","supermarket","convenience"]}},
    "commerce_majeur": {"tags":{"shop": ["mall","department_store"]}},
    "education2": {"tags":{"amenity": ["school","kindergarten","college","university"]}},
    "sante2": {"tags":{"amenity": ["hospital", "clinic", "doctors"]}},
    "administration2": {"tags":{"amenity": ["townhall","courthouse","police","post_office"]}},
    "culture_tourisme": {"tags":{"amenity":["museum","cinema","theatre"], "tourism":["attraction","museum"], "historic":"monument"}},
    "bureaux2": {"tags":{"office": ["company", "corporate", "it", "administrative", "government"]}}, 
    "sports_loisirs": {"tags":{"leisure": ["sports_centre","stadium","pitch","swimming_pool"]}}
}


try:
    import osmnx as ox
except ImportError:
    ox = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("collecte_simplifiee")

# ---------------------------------------------------------------------------
# 1. GTFS IDFM
# ---------------------------------------------------------------------------

def telecharger_gtfs_idfm():
    url = "https://eu.ftp.opendatasoft.com/stif/GTFS/IDFM-gtfs.zip"
    r = requests.get(url, timeout=120)
    r.raise_for_status()

    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
        for f in ["agency.txt","calendar_dates.txt","stops.txt", "routes.txt", "trips.txt", "stop_times.txt","calendar.txt","transfers.txt","trips.txt"]:
            if f in z.namelist():
                z.extract(f, GTFS_DIR)
                logger.info(f"GTFS extrait : {f}")

    gtfs = {}
    for f in ["agency.txt","calendar_dates.txt","stops.txt", "routes.txt", "trips.txt", "stop_times.txt","calendar.txt","transfers.txt","trips.txt"]:
        path = GTFS_DIR / f
        if path.exists():
            gtfs[f.split(".")[0]] = pd.read_csv(path)

    return gtfs

# ---------------------------------------------------------------------------
# 2. POI OSM
# ---------------------------------------------------------------------------

def extraire_poi_osm(categorie):
    if ox is None:
        logger.error("osmnx non disponible")
        return None

    tags = POI_CATEGORIES[categorie]["tags"]
    bbox = (
        IDF_BBOX["west"],
        IDF_BBOX["south"],
        IDF_BBOX["east"],
        IDF_BBOX["north"],
    )

    gdf = ox.features_from_bbox(bbox, tags)

    # simplification : on prend le centroïde pour tous les objets
    if "geometry" in gdf.columns:
        gdf["geometry"] = gdf.geometry.centroid

    # Sauvegarde GeoJSON
    geojson_path = POI_DIR / f"poi_{categorie}.geojson"
    gdf.to_file(geojson_path, driver="GeoJSON")

    # Sauvegarde Parquet optimisé pour les plus lourds
    parquet_path = POI_DIR / f"poi_{categorie}.parquet"
    gdf.to_parquet(parquet_path, index=False)

    logger.info(f"POI {categorie} exporté → {geojson_path.name} + {parquet_path.name}")

    return gdf
#Pour les geojson pas encore convertis 
def convertir_geojson_en_parquet(poi_dir=POI_DIR):
    """
    Convertit tous les geojson présents dans data/poi/ en parquet.
    Si un fichier parquet du même nom existe déjà → il est ignoré.
    """

    files = list(poi_dir.glob("*.geojson"))
    if not files:
        print("Aucun GeoJSON trouvé.")
        return

    for geojson_file in files:
        parquet_file = geojson_file.with_suffix(".parquet")

        # Saut si déjà converti
        if parquet_file.exists():
            print(f"✔ Déjà converti : {parquet_file.name}")
            continue

        print(f"Conversion : {geojson_file.name} → {parquet_file.name}")

        try:
            gdf = gpd.read_file(geojson_file)

            # On s'assure que tout a bien un CRS cohérent (WGS84)
            if gdf.crs is None:
                print(f" Pas de CRS détecté pour {geojson_file.name} → assignation EPSG:4326")
                gdf = gdf.set_crs("EPSG:4326", allow_override=True)

            # Conversion et sauvegarde
            gdf.to_parquet(parquet_file, index=False)
            print(f"OK : {parquet_file.name} généré")

        except Exception as e:
            print(f"ERREUR pour {geojson_file.name} —> {e}")

    print("\nConversion GeoJSON → Parquet terminée.")

# ---------------------------------------------------------------------------
# UTILISATION
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    #telecharger_gtfs_idfm()

    convertir_geojson_en_parquet()
    
    for cat in POI_CATEGORIES:
        out_file = POI_DIR / f"poi_{cat}.geojson"
        if out_file.exists(): #pour ne pas re télécharger des fichiers existants
            logger.info(f"POI {cat} déjà existant, passage")
            continue
        extraire_poi_osm(cat)

    print("=== Collecte terminée ===")

