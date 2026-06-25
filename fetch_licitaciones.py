import urllib.request
import urllib.parse
import json
import os
import xml.etree.ElementTree as ET
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
    "ERP formación",
    "formación online",
    "aplicacion movil",
    "gestión entradas",
]

NS = {
    'atom': 'http://www.w3.org/2005/Atom',
    'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
    'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2',
    'efac': 'http://data.europa.eu/p27/eforms-ubl-extension-aggregate-components/1',
    'efbc': 'http://data.europa.eu/p27/eforms-ubl-extension-basic-components/1',
}

def fecha_hace_dias(n):
    d = datetime.now() - timedelta(days=n)
    return d.strftime("%Y%m%d")

def texto(el, tag):
    if el is None:
        return ""
    found = el.find(tag, NS)
    return found.text.strip() if found is not None and found.text else ""

def buscar_atom(keyword):
    kw_encoded = urllib.parse.quote(keyword)
    fecha = fecha_hace_dias(10)
    url = (
        f"https://contrataciondelestado.es/sindicacion/sindicacion_1044/licitacionesPerfilesContratanteCompleto3.atom"
        f"?keyword={kw_encoded}&fechaPublicacionDesde={fecha}"
    )
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 TenderWatch/1.0",
                "Accept": "application/atom+xml, application/xml, */*"
            }
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            content = resp.read().decode("utf-8", errors="replace")
            return content
    except Exception as e:
        print(f"  Error feed '{keyword}': {e}")
        return None

def parsear_atom(xml_content, keyword):
    resultados = []
    try:
        root = ET.fromstring(xml_content)
        # Namespace del atom
        entries = root.findall('{http://www.w3.org/2005/Atom}entry')
        for entry in entries:
            titulo = ""
            enlace = ""
            organismo = ""
            importe = ""
            plazo = ""
            cpv = ""
            fecha_pub = ""
            expediente = ""

            # Título
            t = entry.find('{http://www.w3.org/2005/Atom}title')
            titulo = t.text.strip() if t is not None and t.text else ""

            # Enlace
            link = entry.find('{http://www.w3.org/2005/Atom}link')
            if link is not None:
                enlace = link.get('href', '')

            # ID / expediente
            id_el = entry.find('{http://www.w3.org/2005/Atom}id')
            expediente = id_el.text.strip() if id_el is not None and id_el.text else titulo

            # Fecha publicación
            pub = entry.find('{http://www.w3.org/2005/Atom}published')
            if pub is not None and pub.text:
                fecha_pub = pub.text[:10]

            # Summary puede contener XML embebido con datos del contrato
            summary = entry.find('{http://www.w3.org/2005/Atom}summary')
            if summary is not None and summary.text:
                # Intentar parsear el XML del summary
                try:
                    inner = ET.fromstring(summary.text)
                    # Organismo
                    for tag in ['.//cac:PartyName/cbc:Name', './/cbc:Name']:
                        el = inner.find(tag, NS)
                        if el is not None and el.text:
                            organismo = el.text.strip()
                            break
                    # Importe
                    for tag in ['.//cbc:TaxExclusiveAmount', './/cbc:LineExtensionAmount', './/cbc:Amount']:
                        el = inner.find(tag, NS)
                        if el is not None and el.text:
                            importe = el.text.strip()
                            break
                    # Fecha límite
                    for tag in ['.//cbc:EndDate', './/cbc:SubmissionDueDate']:
                        el = inner.find(tag, NS)
                        if el is not None and el.text:
                            plazo = el.text.strip()[:10]
                            break
                    # CPV
                    for tag in ['.//cbc:ItemClassificationCode', './/cbc:ID[@schemeName="CPV"]']:
                        el = inner.find(tag, NS)
                        if el is not None and el.text:
                            cpv = el.text.strip()
                            break
                except:
                    pass

            # Extraer organismo del título si no se encontró
            if not organismo and ' - ' in titulo:
                partes = titulo.split(' - ')
                if len(partes) > 1:
                    organismo = partes[-1].strip()
                    titulo = ' - '.join(partes[:-1]).strip()

            if titulo:
                resultados.append({
                    "id": expediente or titulo,
                    "titulo": titulo,
                    "organismo": organismo,
                    "importe": importe,
                    "plazo": plazo,
                    "cpv": cpv,
                    "enlace": enlace or "https://contrataciondelestado.es",
                    "fechaPublicacion": fecha_pub,
                    "_kw": keyword,
                })
    except Exception as e:
        print(f"  Error parseando XML: {e}")
    return resultados

def main():
    print(f"Buscando licitaciones (últimos 10 días)...")
    resultados = []
    vistos = set()

    for kw in KEYWORDS:
        print(f"  -> {kw}")
        xml_content = buscar_atom(kw)
        if xml_content:
            items = parsear_atom(xml_content, kw)
            print(f"     {len(items)} resultados")
            for item in items:
                id_item = item["id"]
                if id_item not in vistos:
                    vistos.add(id_item)
                    resultados.append(item)

    output = {
        "actualizado": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "total": len(resultados),
        "licitaciones": resultados,
    }

    os.makedirs("data", exist_ok=True)
    with open("data/licitaciones.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\nTotal guardadas: {len(resultados)} licitaciones en data/licitaciones.json")

if __name__ == "__main__":
    main()
