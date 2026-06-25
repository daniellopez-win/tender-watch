import urllib.request
import urllib.parse
import json
import os
from datetime import datetime, timedelta

KEYWORDS = [
    "aplicación móvil",
    "app móvil",
    "plataforma digital",
    "desarrollo web",
    "software gestión",
    "portal web",
    "sistema informático",
    "gestión académica",
    "ERP",
    "formación online",
    "aplicacion movil",
    "gestion entradas",
]

def fecha_hace_10_dias():
    d = datetime.now() - timedelta(days=10)
    return d.strftime("%d-%m-%Y")

def buscar_keyword(keyword, fecha_desde):
    kw_encoded = urllib.parse.quote(keyword)
    url = (
        f"https://contrataciondelestado.es/wps/wcm/connect/PLACE_es/Site/area/docAccinter"
        f"?page=1&pageSize=20&keyword={kw_encoded}"
        f"&fechaPublicacionDesde={fecha_desde}&tipoBusqueda=1&_type=json"
    )
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "TenderWatch/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("licitaciones") or data.get("contratos") or data.get("results") or []
    except Exception as e:
        print(f"  Error en '{keyword}': {e}")
        return []

def main():
    fecha = fecha_hace_10_dias()
    print(f"Buscando licitaciones desde {fecha}...")
    
    resultados = []
    vistos = set()

    for kw in KEYWORDS:
        print(f"  Keyword: {kw}")
        items = buscar_keyword(kw, fecha)
        for item in items:
            id_item = (
                item.get("expediente")
                or item.get("id")
                or item.get("numero")
                or (str(item.get("titulo", "")) + str(item.get("organismo", "")))
            )
            if id_item and id_item not in vistos:
                vistos.add(id_item)
                resultados.append({
                    "id": id_item,
                    "titulo": item.get("titulo") or item.get("nombre") or "",
                    "organismo": item.get("organismo") or item.get("entidad") or item.get("organoContratacion") or "",
                    "importe": item.get("importe") or item.get("presupuestoBase") or item.get("importeConIva") or "",
                    "plazo": item.get("plazo") or item.get("fechaLimiteOferta") or item.get("fechaFin") or "",
                    "cpv": item.get("cpv") or item.get("codigoCPV") or "",
                    "enlace": item.get("enlace") or item.get("url") or item.get("urlContratacion") or "https://contrataciondelestado.es",
                    "fechaPublicacion": item.get("fechaPublicacion") or item.get("fecha") or "",
                    "_kw": kw,
                })

    output = {
        "actualizado": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "total": len(resultados),
        "licitaciones": resultados,
    }

    os.makedirs("data", exist_ok=True)
    with open("data/licitaciones.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"Guardadas {len(resultados)} licitaciones en data/licitaciones.json")

if __name__ == "__main__":
    main()
