import os
from functools import lru_cache
from lxml import etree
from shapely.geometry import Point, Polygon
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

# Namespace KML estándar
KML_NS = "http://www.opengis.net/kml/2.2"

# DICCIONARIO DE CHOFERES - v8.2/8.3 Protegido
CHOFERES = {
    "MENEGHIN GABRIEL LUIS": "5493413040368", "JUAN JOSE, CISNEROS": "5493412501746",
    "PARDO JUAN IGNACIO": "5493416589548", "JOSE, CAPPUCCIO": "5493416728180",
    "ROMERO SERGIO": "5493425517414", "MARCOS MARTINEZ": "5493416181394",
    "VRANCICH DIEGO": "5493416563798", "MAXIMILIANO SEBES": "5493415601516",
    "CLAUDIO ROMERO": "5493413083314", "JESÚS AGUILERA": "5493413768478",
    "MARCOS WENK": "5493425517414", "ALEJANDRA FERRARO": "5493413021451",
    "HUGO MARTINUCCI": "5493415870243", "FERNANDO GIANNI": "5493413099216",
    "FERNANDO MANSILLA": "5493416843864", "SEBASTIAN GARCIA": "5493412615425",
    "JONATAN SCHUMAKER": "5493425517414", "DAMIÁN FLAMENCO": "5493414004879",
    "CRISTIAN SANGUINETTI": "5493412806479", "OMAR MIGUEL RAMIREZ": "5493416748237",
    "CANAVO, CRISTIAN MARTIN": "5493402523716", "EREZUMA MARTIN": "5493416194298",
    "ANGULO DIEGO": "5493415624965", "GANANOPULO NICOLAS": "5493416596751",
    "PERRETTA ROMINA": "5493416176424", "DATTO ACTIS ADRIAN": "5493364277548",
    "RODRIGUEZ PABLO MARIANO": "5493416136973", "PRADO WILBER": "5493417195251"
}

# user_agent fijo para evitar throttling/bloqueos de Nominatim
geolocator = Nominatim(user_agent="inner_logistics_rosario_v1")

# Caché de geocodificación en memoria
_cache_geo = {}

def geocodificar(direccion: str):
    """
    Geocodifica dentro del bounding box de Rosario para evitar resultados erróneos.
    Bounding box: lon [-60.78, -60.58], lat [-32.83, -33.05]
    Si no encuentra resultado con bounded=True, reintenta sin restricción.
    """
    key = direccion.strip().lower()
    if key in _cache_geo:
        return _cache_geo[key]

    # Intento 1: forzar búsqueda dentro de Rosario
    loc = geolocator.geocode(
        direccion + ", Rosario, Santa Fe, Argentina",
        viewbox=[(-60.78, -32.83), (-60.58, -33.05)],
        bounded=True,
        timeout=10
    )
    # Fallback: si no encuentra nada, intenta sin restricción geográfica
    if not loc:
        loc = geolocator.geocode(
            direccion + ", Rosario, Santa Fe, Argentina",
            timeout=10
        )
    _cache_geo[key] = loc
    return loc

def _parsear_coordenadas(texto: str):
    """Convierte el texto de <coordinates> en una lista de tuplas (lon, lat)."""
    coords = []
    for token in texto.strip().split():
        partes = token.split(",")
        if len(partes) >= 2:
            try:
                lon, lat = float(partes[0]), float(partes[1])
                coords.append((lon, lat))
            except ValueError:
                continue
    return coords

def _extraer_poligonos_kml(ruta_archivo: str):
    """
    Usa lxml directamente para extraer todos los polígonos del KML.
    Devuelve lista de tuplas: (nombre_folder, nombre_placemark, Polygon)
    """
    poligonos = []
    tree = etree.parse(ruta_archivo)
    root = tree.getroot()
    ns = {"k": KML_NS}

    def _procesar_placemark(placemark, nombre_folder):
        poly_el = placemark.find(".//k:Polygon", ns)
        if poly_el is None:
            return None
        coords_el = poly_el.find(".//k:outerBoundaryIs//k:coordinates", ns)
        if coords_el is None or not coords_el.text:
            return None
        coords = _parsear_coordenadas(coords_el.text)
        if len(coords) < 3:
            return None
        return (nombre_folder, Polygon(coords))

    # Caso 1: Placemarks dentro de Folders (estructura repartos.kml)
    for folder in root.findall(".//k:Folder", ns):
        nombre_folder = ""
        name_el = folder.find("k:name", ns)
        if name_el is not None and name_el.text:
            nombre_folder = name_el.text.strip()
        for placemark in folder.findall("k:Placemark", ns):
            resultado = _procesar_placemark(placemark, nombre_folder)
            if resultado:
                poligonos.append(resultado)

    # Caso 2: Placemarks directos en Document sin Folder (estructura 275.kml)
    if not poligonos:
        doc_name_el = root.find("k:Document/k:name", ns)
        nombre_doc = doc_name_el.text.strip() if doc_name_el is not None and doc_name_el.text else ""
        for placemark in root.findall("k:Document/k:Placemark", ns):
            resultado = _procesar_placemark(placemark, nombre_doc)
            if resultado:
                poligonos.append(resultado)

    return poligonos

@lru_cache(maxsize=None)
def cargar_zonas():
    """Lee y parsea todos los KML una única vez al arrancar."""
    zonas = []
    if not os.path.exists("zonas"):
        return tuple()
    for archivo in os.listdir("zonas"):
        if archivo.endswith(".kml"):
            ruta = os.path.join("zonas", archivo)
            for nombre_folder, poligono in _extraer_poligonos_kml(ruta):
                zonas.append((nombre_folder, poligono))
    return tuple(zonas)

def consultar_zona(direccion):
    if not direccion:
        return "Ingrese dirección."

    try:
        loc = geocodificar(direccion)
    except GeocoderTimedOut:
        return "❌ Timeout: Nominatim tardó demasiado. Reintentá en unos segundos."
    except GeocoderServiceError as e:
        return f"❌ Error de servicio geocoder: {e}"

    if not loc:
        return f"❌ No encontrada: {direccion}"

    punto = Point(loc.longitude, loc.latitude)
    area_seguridad = punto.buffer(0.0015)  # ~150m buffer para calles limítrofes

    zonas = cargar_zonas()
    if not zonas:
        return "⚠️ Carpeta /zonas no encontrada o vacía."

    try:
        for nombre_folder, poligono in zonas:
            if poligono.intersects(area_seguridad):
                return f"📍 {nombre_folder}"
    except Exception as e:
        return f"❌ Error al procesar zonas: {e}"

    return f"🔍 GPS: ({loc.latitude:.5f}, {loc.longitude:.5f}) fuera de límites."
