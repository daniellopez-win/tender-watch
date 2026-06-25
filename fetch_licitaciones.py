import urllib.request
import json
import os
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

# Palabras clave para filtrar localmente
KEYWORDS = [
    "aplicación móvil", "aplicacion movil",
    "app móvil", "app movil",
    "plataforma digital",
    "desarrollo web",
    "software gestión", "software gestion",
    "portal web",
    "sistema informático", "sistema informatico",
    "gestión académica", "gestion academica",
    "formación online", "formacion online",
    "gestión entradas", "gestion entradas",
    "aplicación web", "aplicacion web",
    "plataforma online",
    "transformación digital", "transformacion digital",
    "ERP",
]

# URL oficial del feed Atom de PLACE (últimas licitaciones, máx 500 por página)
FEED_URL = "https://contrataciondelestado.es/sindicacion/sindicacion_643/licitacionesPerfilesContratanteCompleto3.atom"

ATOM = "http://www.w3.org/2005/Atom"

def fetch_feed(url):
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 TenderWatch/1.0",
                "Accept": "application/atom+xml, application/xml, */*",
            }
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"  Error descargando feed: {e}")
        return None

def parsear_entry(entry):
    """Extrae los campos básicos de una entry del Atom."""
    def txt(tag):
        el = entry.find(f"{{{ATOM}}}{tag}")
        return el.text.strip() if el is not None and el.text else ""

    titulo = txt("title")
    enlace = ""
    link = entry.find(f"{{{ATOM}}}link")
    if link is not None:
        enlace = link.get("href", "")

    id_entry = txt("id") or titulo
    updated = txt("updated")[:10] if txt("updated") else ""

    # El summary contiene XML CODICE con los datos del contrato
    organismo = ""
    importe = ""
    plazo = ""
    cpv = ""

    summary = entry.find(f"{{{ATOM}}}summary")
    if summary is not None:
        # Primero intentar el texto del summary
        raw = summary.text or ""
        # Buscar en el contenido XML embebido
        try:
            # A veces el contenido viene como CDATA o texto plano con XML
            if raw.strip().startswith("<"):
                inner = ET.fromstring(raw)
                # Organismo — varios posibles tags
                for xpath in [
                    ".//{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}PartyName/{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}Name",
                    ".//{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}Name",
                ]:
                    el = inner.find(xpath)
                    if el is not None and el.text:
                        organismo = el.text.strip()
                        break
                # Importe
                for xpath in [
                    ".//{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}TaxExclusiveAmount",
                    ".//{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}LineExtensionAmount",
                ]:
                    el = inner.find(xpath)
                    if el is not None and el.text:
                        importe = el.text.strip()
                        break
                # Fecha límite
                for xpath in [
                    ".//{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}EndDate",
                ]:
                    el = inner.find(xpath)
                    if el is not None and el.text:
                        plazo = el.text.strip()[:10]
                        break
                # CPV
                for xpath in [
                    ".//{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}ItemClassificationCode",
                ]:
                    el = inner.find(xpath)
                    if el is not None and el.text:
                        cpv = el.text.strip()
                        break
        except Exception:
            pass

    return {
        "id": id_entry,
        "titulo": titulo,
        "organismo": organismo,
        "importe": importe,
        "plazo": plazo,
        "cpv": cpv,
        "enlace": enlace or "https://contrataciondelestado.es",
        "fechaPublicacion": updated,
        "_kw": "",
    }

def titulo_contiene_keyword(titulo):
    t = titulo.lower()
    for kw in KEYWORDS:
        if kw.lower() in t:
            return kw
    return None

def main():
    fecha_limite = datetime.now() - timedelta(days=10)
    print(f"Descargando feed PLACE (últimas licitaciones)...")

    resultados = []
    vistos = set()
    paginas = 0
    url = FEED_URL

    while url and paginas < 5:
        paginas += 1
        print(f"  Página {paginas}: {url[:80]}...")
        xml_content = fetch_feed(url)
        if not xml_content:
            break

        try:
            root = ET.fromstring(xml_content)
        except Exception as e:
            print(f"  Error parseando XML: {e}")
            break

        entries = root.findall(f"{{{ATOM}}}entry")
        print(f"  {len(entries)} entradas en esta página")

        entradas_antiguas = 0
        for entry in entries:
            item = parsear_entry(entry)

            # Filtrar por fecha (últimos 10 días)
            if item["fechaPublicacion"]:
                try:
                    fecha_pub = datetime.strptime(item["fechaPublicacion"], "%Y-%m-%d")
                    if fecha_pub < fecha_limite:
                        entradas_antiguas += 1
                        continue
                except:
                    pass

            # Filtrar por keyword en título
            kw_match = titulo_contiene_keyword(item["titulo"])
            if not kw_match:
                continue

            item["_kw"] = kw_match

            if item["id"] not in vistos:
                vistos.add(item["id"])
                resultados.append(item)

        # Si todas las entradas son antiguas, parar la paginación
        if entradas_antiguas == len(entries):
            print("  Todas las entradas son antiguas, parando.")
            break

        # Siguiente página
        url = None
        for link in root.findall(f"{{{ATOM}}}link"):
            if link.get("rel") == "next":
                url = link.get("href")
                break

    output = {
        "actualizado": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "total": len(resultados),
        "licitaciones": resultados,
    }

    os.makedirs("data", exist_ok=True)
    with open("data/licitaciones.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n✓ {len(resultados)} licitaciones relevantes guardadas en data/licitaciones.json")

if __name__ == "__main__":
    main()
