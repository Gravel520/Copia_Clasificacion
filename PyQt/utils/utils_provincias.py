'''
Script en PYthon.
'''

import requests
import time

from config_paths import PROVINCIAS_ES, PROVINCIAS_FR, PROVINCIAS_PT

from utils.utils_cache import normalizar_texto

# ============================================================
#  NORMALIZACIÓN DE NOMBRES
# ============================================================

def normalizar_provincia(nombre):
    if not nombre:
        return None
    
    nombre = nombre.strip()

    # Correcciones típicas de España
    reemplazos = {
        "Castilla-La Mancha": "Castilla La Mancha",
        "Castilla y León": "Castilla y Leon",
        "Comunidad de Madrid": "Madrid",
        "Galicia": "Galicia",
        "Andalucía": "Andalucia",
        "Principado de Asturias": "Asturias",
        "Comunidad Valenciana": "Valencia",
        "Cataluña": "Catalunya",
        "País Vasco": "Pais Vasco",
        "Comunidad Foral de Navarra": "Navarra",
        "Alacant / Alicante": "Alicante",
    }

    if nombre in reemplazos:
        return reemplazos[nombre]

    return nombre

def capitalizar_lugar(texto):
    # Lista de palabras que deben permanecer en minúscula
    excepciones = {"de", "del", "al", "la", "el", "los", "las", "y", "e", "en", "sobre", "por"}

    # Dividimos el texto en palabras individuales
    palabras = texto.lower().split()

    resultado = []
    for i, palabra in enumerate(palabras):
        # La primera palabra SIEMPRE va en mayúscula.
        # Las siguientes solo van en mayúscula si NO están en la lista
        if i == 0 or palabra not in excepciones:
            resultado.append(palabra.capitalize())
        else:
            resultado.append(palabra)

    return " ".join(resultado)


# ============================================================
#  GEOCODING ROBUSTO
# ============================================================
def extraer_provincia_geocode_ciudad(ciudad, pais):
    """
    Devuelve lat, lon, provincia usando Nominatim con fallback robusto.
    """

    url = "https://nominatim.openstreetmap.org/search"

    country_map = {
        "es": "es",
        "españa": "es",
        "spain": "es",
        "pt": "pt",
        "portugal": "pt",
        "fr": "fr",
        "francia": "fr",
        "france": "fr"
    }


    params = {
        "city": ciudad,
        "countrycodes": country_map.get(pais.lower(), ""),
        "format": "json",
        "addressdetails": 1,
        "limit": 1
    }

    try:
        time.sleep(1)
        r = requests.get(
            url,
            params=params,
            headers={"User-Agent": "Copilot-Geocoder"},
            timeout=10
        )
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"[ERROR] Geocoding falló para {ciudad}, {pais}: {e}")
        return None

    if not data:
        print(f"[WARN] Nominatim no encontró nada para: ({ciudad}, {pais})")
        return None
    
    addr = data[0].get("address", {})

    # ============================================================
    #  FALLBACKS ESPECÍFICOS POR PAÍS
    # ============================================================
    # Portugal
    if pais.lower() == "portugal":
        # Muchos pueblos devuelven solo municipality
        provincia = (
            addr.get("municipality")
            or addr.get("city")
        )

    # España
    elif pais.lower() == "españa":
        # Muchos pueblos devuelven sólo city/town
        provincia = (
            addr.get("province")
            or addr.get("county")
            or addr.get("state_district")
            or addr.get("municipality")
            or addr.get("city")
            or addr.get("town")
    )

    # Francia
    elif pais.lower() == "francia":
        provincia = (
            addr.get("country") 
            or addr.get("municipality")
            or addr.get("state")
        )

    # Azores / Madeira
    if not provincia and "state_district" in addr:
        provincia = addr["state_district"]

    # Último fallback
    if not provincia:
        print(f"[WARN] Geocoding falló para: ({ciudad}, {pais})")
        return None
    
    return normalizar_provincia(provincia)

# ============================================================
#  FUNCION GLOBAL DE AUTOCOMPLETADO
# ============================================================
def completar_datos_registro(info):
    pais = info.get("pais", "")

    if pais == "Espana":
        mapa_provincias = PROVINCIAS_ES
    elif pais == "Francia":
        mapa_provincias = PROVINCIAS_FR
    elif pais == "Portugal":
        mapa_provincias = PROVINCIAS_PT
    else:
        return False
    
    extractor = NominatimExtractor(mapa_provincias)

    ciudad = info.get("ciudad", "")
    provincia = info.get("provincia", "")
    postal = info.get("postal", "")

    cambios = False

    # ----------------------------
    # Completar ciudad/provincia
    # ----------------------------
    if not ciudad or not provincia:
        lat = info.get["lat"]
        lon = info.get["lon"]

        if lat is not None and lon is not None:

            try:
                url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json&addressdetails=1"
                r = requests.get(url, headers={"User-Agent": "Copia_Clasificacion"})
                datos = r.json()
                # Ciudad: intentar varios campos habituales
                address = datos.get("address", {}) if isinstance(info, dict) else {}
                ciudad = address.get("city") or address.get("town") or address.get("village") or address.get("municipality") or ""

                _, provincia_geo = extractor.extract(datos)

                if not provincia:
                    provincia = provincia_geo

            except Exception as e:
                print(f"[ERROR] Nominatim: {e}")

    ciudad = normalizar_texto(ciudad)
    provincia = normalizar_texto(provincia)

    # ----------------------------
    # Código postal
    # ----------------------------
    if (not postal and ciudad and provincia):
        try:
            cp = DistritoPostal.buscar_cp_directo(ciudad, provincia, pais)
            if cp:
                postal = cp

        except Exception as e:
            print(f"[ERROR] DistritoPostal: {e}")

    # ----------------------------
    # Guardar
    # ----------------------------
    if ciudad and ciudad != info.get("ciudad", ""):
        info["ciudad"] = ciudad
        cambios = True

    if provincia and provincia != info.get("provincia", ""):
        info["provincia"] = provincia
        cambios = True

    if postal and postal != info.get("postal", ""):
        info["postal"] = postal
        cambios = True

    return cambios

import re
import difflib
from typing import Any, Dict, Iterable, Tuple

class NominatimExtractor:
    POSTAL_RE = re.compile(r"\b(\d{5})\b")
    # Claves que suelen indicar provincia en respuestas OSM/Nominatim
    PROVINCE_KEYS = {
        "province", "state", "region", "county", "state_district",
        "administrative", "municipality", "state_code"
    }
    POSTAL_KEYS = {
        "postcode", "postal", "postal_code", "zip"
    }

    def __init__(self, provincias_map: Dict[str, str]):
        """
        provincias_map: dict con prefijo CP (2 dígitos) -> nombre provincia
        """
        self.provincias_map = provincias_map
        # Lista de nombres normalizados para comparación difisa
        self.provincias_nombre = [self._norm(v) for v in provincias_map.values()]
        # Mapping normalizado -> nombre original
        self.norm_to_original = {self._norm(v): v for v in provincias_map.values()}

    def _norm(self, s: str) -> str:
        if not s:
            return ""
        s = s.lower().strip()
        replacements = {"á":"a","é":"e","í":"i","ó":"o","ú":"u","ü":"u","ñ":"n"}
        for k, v in replacements.items():
            s = s.replace(k, v)
        return s
    
    def _find_postal_in_text(self, text: str):
        if not text:
            return None
        m = self.POSTAL_RE.search(text)
        if m:
            return m.group(1)
        return None
    
    def _recursive_search(self, obj: Any, found: Dict[str, set]):
        if isinstance(obj, dict):
            for k, v in obj.items():
                key_norm = str(k).lower()
                if key_norm in self.POSTAL_KEYS and isinstance(v, str):
                    p = self._find_postal_in_text(v)
                    if p:
                        found['postals'].add(p)
                if key_norm in self.PROVINCE_KEYS and isinstance(v, str):
                    found['province_candidates'].add(v.strip())
                if isinstance(v, str):
                    p = self._find_postal_in_text(v)
                    if p:
                        found['postals'].add(p)
                # Recursión
                self._recursive_search(v, found)
        elif isinstance(obj, (list, tuple)):
            for item in obj:
                self._recursive_search(item, found)
        elif isinstance(obj, str):
            p = self._find_postal_in_text(obj)
            if p:
                found['postals'].add(p)
        # Otros tipos ignorados

    def extract(self, nominatim_json: Any) -> Tuple[str, str]:
        """
        Devuelve (postal, provincia)
        - postal: primer CP de 5 dígitos encontrado (string) o "".
        - provincia: nombre de provincia (según PROVINCIAS_ES) O "".
        """
        found = {'postals': set(), 'province_candidates': set()}

        if isinstance(nominatim_json, list):
            for item in nominatim_json:
                self._recursive_search(item, found)
        else:
            self._recursive_search(nominatim_json, found)

        # 1) Priorizar postal y derivar provincia por prefijo
        postal = ""
        provincia = ""

        if found['postals']:
            # Ordenar para determinismo; elegir el menor lexicograficamente
            postal = sorted(found["postals"])[0]
            pref = postal[:2]
            if pref in self.provincias_map:
                provincia = self.provincias_map[pref]
                return postal, provincia
            
        # 2) Si no se pudo deducir por CP, intentar con candidatos textuales
        if found["province_candidates"]:
            # Normalizar candidatos
            candidates_norm = {cand: self._norm(cand) for cand in found["province_candidates"]}
            # Buscar coincidencia exacta en nombre de provincias
            for orig, norm in candidates_norm.items():
                if norm in self.norm_to_original:
                    provincia = self.norm_to_original[norm]
                    return postal, provincia
            # Coincidencia difusa
            for orig, norm in candidates_norm.items():
                matches = difflib.get_close_matches(norm, self.provincias_nombre, n=1, cutoff=0.78)
                if matches:
                    provincia = self.norm_to_original[matches[0]]
                    return postal, provincia
                
        # 3) Fallback: buscar cualquier string en el JSON que coincida
        def _search_any_string(obj):
            if isinstance(obj, dict):
                for v in obj.values():
                    res = _search_any_string(v)
                    if res:
                        return res
            elif isinstance(obj, (list, tuple)):
                for it in obj:
                    res = _search_any_string(it)
                    if res:
                        return res
            elif isinstance(obj, str):
                norm = self._norm(obj)
                if norm in self.norm_to_original:
                    return self.norm_to_original[norm]
            return None
        
        fallback = _search_any_string(nominatim_json)
        if fallback:
            provincia = fallback

        return postal or "", provincia or ""

'''
Con esta página "distritopostal.es" podemos hacer la petición adjuntando
provincia y municipio y obtener el código postal.
Primero tenemos que codificar tanto el municipio como la provincia,
reemplazando los caracteres en blanco por guiones "-".
Busca en toda la página una combinación de 5 dígitos seguidos que,
normalmente, corresponde con el código postal.
Devuelve el primero valor encontrado.
'''
class DistritoPostal():
    def __init__(self):
        pass

    def buscar_cp_directo(municipio, provincia, pais="Espana"):
        # Codificamos los datos para usarlos en la url.
        municipio = municipio.replace(" ", "-").lower()
        provincia = provincia.replace(" ", "-").lower()

        if pais == "Espana":
            # Usamos esta página para buscar los códigos postales        
            url = f"https://distritopostal.es/{provincia}/{municipio}"
            re_findall = r"\b\d{5}\b"

        elif pais == "Portugal":
            url = f"https://www.codigo-postal.pt/?rua=&local={municipio}"
            re_findall = r"\b\d{4}\s*-\s*\d{3}\b"

        elif pais == "Francia":
            url = f"https://www.codes-postaux.org/sp/municipio-{municipio}.htm"
            re_findall = r"\b\d{5}\b"

        # Simulamos las cabeceras (User-Agent) de un navegador real.
        # Esto evita que el buscador detecte que eres un script de Python
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        }

        try:
            # Realizamos la descarga de la página de resultados
            respuesta = requests.get(url, headers=headers, timeout=10)

            if respuesta.status_code == 200:
                texto_completo_web = respuesta.text

                # Buscamos todos los números de 5 dígitos en el texto de la página
                codigos_encontrados = re.findall(re_findall, texto_completo_web)

                if codigos_encontrados:
                    return codigos_encontrados[0]
                else:
                    return "No se localizó ningún patrón de cp."
                
            else:
                return f"Error al buscar el código postal: {respuesta.status_code}"
            
        except Exception as e:
                return f"Error al buscar el código postal: {e}"
