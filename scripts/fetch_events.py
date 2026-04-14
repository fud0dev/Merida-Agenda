#!/usr/bin/env python3
"""
fetch_events.py — Obtiene información de Mérida (Extremadura, España)
Fuentes solicitadas por el usuario:
  1. El Periódico Extremadura (Mérida)
  2. Hoy.es (Mérida)
  3. Mérida y Comarca
  4. Mérida Diario
  5. Mérida.es (Noticias)
  6. Mérida Noticias
  7. La Crónica de Badajoz (Mérida)
  8. Cadena SER (Mérida)
  9. Onda Cero (Mérida)
  10. Mérida.es (Agenda)
"""

import json
import logging
import sys
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9",
    "Referer": "https://www.google.com/",
}
TIMEOUT = 20
OUTPUT_PATH = Path(__file__).parent.parent / "docs" / "events.json"

# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def get_page(url):
    """Realiza una petición GET con headers para evitar bloqueos."""
    try:
        session = requests.Session()
        resp = session.get(url, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        log.warning(f"Error al obtener {url}: {e}")
        return None

def parse_date(raw: str) -> str | None:
    """Intenta parsear una cadena de fecha a ISO-8601 (YYYY-MM-DD)."""
    if not raw:
        return None
    
    # Normalización básica
    raw_lower = raw.strip().lower()
    today = datetime.now()
    
    # Manejo de fechas relativas comunes en noticias
    if "hoy" in raw_lower or "hace" in raw_lower or "minuto" in raw_lower or "segundo" in raw_lower:
        return today.strftime("%Y-%m-%d")
    if "ayer" in raw_lower:
        return (today - timedelta(days=1)).strftime("%Y-%m-%d")

    # Mapeo de meses en español
    meses = {
        "enero": "01", "febrero": "02", "marzo": "03", "abril": "04",
        "mayo": "05", "junio": "06", "julio": "07", "agosto": "08",
        "septiembre": "09", "octubre": "10", "noviembre": "11", "diciembre": "12",
        "ene": "01", "feb": "02", "mar": "03", "abr": "04", "may": "05", "jun": "06",
        "jul": "07", "ago": "08", "sep": "09", "oct": "10", "nov": "11", "dic": "12"
    }
    
    # Reemplazar meses por números
    for mes, num in meses.items():
        raw_lower = raw_lower.replace(mes, num)
    
    # Intentar capturar patrones comunes de fecha (DD/MM/YYYY, DD-MM-YYYY, YYYY-MM-DD)
    m_iso = re.search(r"(\d{4})-(\d{2})-(\d{2})", raw_lower)
    if m_iso:
        return m_iso.group(0)
        
    m_es = re.search(r"(\d{1,2})[ /-](\d{2})[ /-](\d{4})", raw_lower)
    if m_es:
        return f"{m_es.group(3)}-{m_es.group(2)}-{int(m_es.group(1)):02d}"

    # Intento con strptime para formatos estándar
    formats = [
        "%Y-%m-%dT%H:%M:%S",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%Y-%m-%d"
    ]
    for fmt in formats:
        try:
            return datetime.strptime(raw_lower[:10], fmt[:10]).strftime("%Y-%m-%d")
        except:
            pass
            
    return None

def is_valid_item(item):
    """Filtros para evitar ruido (categorías, botones, etc)."""
    title = item.get("title", "")
    url = item.get("url", "")
    desc = item.get("description", "")
    date = item.get("date", "")
    
    if not title or not url:
        return False
    
    # Ignorar títulos que son solo categorías o muy genéricos
    junk_titles = ["Mérida", "Extremadura", "Opinión", "Deportes", "Cultura", "Vídeos", "Local", "Nacional", "Internacional"]
    if title.strip() in junk_titles:
        return False
        
    # Si es muy corto, probablemente sea un título de sección
    if len(title) < 12:
        return False
        
    # Si no tiene fecha NI tiene descripción, comprobamos que el título sea largo
    # (las noticias reales suelen tener títulos descriptivos largos)
    if not date and not desc and len(title) < 25:
        return False
        
    return True

# ──────────────────────────────────────────────
# Scraper Genérico
# ──────────────────────────────────────────────

def fetch_source(name, url, selectors):
    """Extrae información de una fuente usando selectores CSS."""
    log.info(f"Scraping [{name}]...")
    html = get_page(url)
    if not html:
        return []

    soup = BeautifulSoup(html, "lxml")
    results = []
    
    # Selectores de items más comunes
    item_selector = selectors.get("item", "article, .post, .entry, .news-item")
    items = soup.select(item_selector)
    
    # Selectores de títulos más comunes
    title_selectors = selectors.get("title", "h1, h2, h3, h4, .title, .entry-title, .event-title")
    
    # Selectores de descripción más comunes
    desc_selectors = selectors.get("description", "p, .entry-content p, .entry-summary, .post-content, .td-excerpt, .summary")
    
    for entry in items[:25]:
        try:
            # Título inteligente
            title_tag = entry.select_one(title_selectors)
            title = title_tag.get_text(strip=True) if title_tag else ""
            
            # Buscar versión extendida en atributos 'title' de los enlaces
            # Muchas webs cortan el texto visible con "..." pero dejan el completo en el atributo title
            link_tags = entry.find_all("a", title=True)
            for link in link_tags:
                attr_title = link.get("title", "").strip()
                if len(attr_title) > len(title):
                    title = attr_title
                    break
            
            # Enlace
            link_tag = entry.find("a", href=True)
            if not link_tag and entry.name == "a":
                link_tag = entry
            
            href = link_tag.get("href") if link_tag else None
            if href:
                href = urljoin(url, href)
            
            # Fecha
            date = None
            date_selector = selectors.get("date", "time, .date, .entry-date, .fecha")
            date_tag = entry.select_one(date_selector)
            if date_tag:
                raw_date = date_tag.get("datetime") or date_tag.get("content") or date_tag.get_text(strip=True)
                date = parse_date(raw_date)

            # Descripción
            description = ""
            desc_tag = entry.select_one(desc_selectors)
            if desc_tag:
                # Si el selector devolvió TODO el contenido, tomamos el primer párrafo o recortamos
                description = desc_tag.get_text(" ", strip=True)
                # Limpiamos ruido común
                for noise in ["Siguenos en", "Sigue leyendo", "Comparte esta", "Leer Más"]:
                    if noise in description:
                        description = description.split(noise)[0].strip()
                
                if len(description) > 300:
                    description = description[:297] + "..."

            item_data = {
                "title": title,
                "description": description,
                "date": date or "",
                "url": href,
                "source": name,
                "location": "Mérida"
            }

            if is_valid_item(item_data):
                results.append(item_data)
        except Exception as e:
            log.debug(f"Error procesando item en {name}: {e}")
            
    log.info(f"[{name}] {len(results)} items encontrados.")
    return results

# ──────────────────────────────────────────────
# Fuentes y Selectores
# ──────────────────────────────────────────────

SOURCES = [
    {
        "name": "El Periódico Extremadura",
        "url": "https://www.elperiodicoextremadura.com/merida/",
        "selectors": {
            "item": "article",
            "title": "h2, h3, .title",
            "description": ".lead, .article-excerpt, .description, .ep-article-description"
        }
    },
    {
        "name": "Hoy.es",
        "url": "https://www.hoy.es/merida/",
        "selectors": {
            "item": "article, .v-card",
            "title": "h2, h3, .title, .v-a-t",
            "description": ".v-a-sub-t, .v-a-cro-t, .summary, .lead, .v-content p"
        }
    },
    {
        "name": "Mérida y Comarca",
        "url": "https://meridaycomarca.com/",
        "selectors": {
            "item": "article, .post, .entry",
            "title": "h2, h3, .entry-title",
            "description": ".entry-content p, .post-content p"
        }
    },
    {
        "name": "Mérida Diario",
        "url": "https://www.meridadiario.com/",
        "selectors": {
            "item": "article, .post, .td-block-span12, .td-animation-stack-type0",
            "title": "h2, h3, .entry-title",
            "description": ".td-excerpt, .entry-content p"
        }
    },
    {
        "name": "Ayuntamiento - Noticias",
        "url": "https://merida.es/category/noticias/",
        "selectors": {
            "item": "article, .post, .et_pb_post",
            "title": "h2, h3, .entry-title",
            "description": ".entry-content, .post-content, .entry-summary, p"
        }
    },
    {
        "name": "Mérida Noticias",
        "url": "https://meridanoticias.com/",
        "selectors": {
            "item": "article, .post",
            "title": "h2, h3, .entry-title",
            "description": ".post-content, .entry-content, .entry-summary, p"
        }
    },
    {
        "name": "La Crónica de Badajoz",
        "url": "https://www.lacronicabadajoz.com/merida/",
        "selectors": {
            "item": "article, .ft-layout-grid-flex__row",
            "title": "h2, h3, .title",
            "description": ".lead, .description, p"
        }
    },
    {
        "name": "Cadena SER Mérida",
        "url": "https://cadenaser.com/ser-merida/",
        "selectors": {
            "item": "article, .c-list-article",
            "title": "h2, .c-list-article__title, .title",
            "description": ".c-list-article__excerpt, .lead"
        }
    },
    {
        "name": "Onda Cero Mérida",
        "url": "https://www.ondacero.es/emisoras/extremadura/merida/",
        "selectors": {
            "item": "article, .teaser",
            "title": "h2, .teaser__title, .title",
            "description": ".teaser__text, .teaser__lead"
        }
    },
    {
        "name": "Ayuntamiento - Agenda",
        "url": "https://merida.es/agenda/",
        "selectors": {
            "item": "article, .evento, .calendar-list__event, .tribe-events-calendar-list__event",
            "title": "h2, h3, h4, .title, .event-title",
            "description": ".tribe-events-calendar-list__event-description p, .entry-content p"
        }
    }
]

# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────

def dedup(items: list[dict]) -> list[dict]:
    """Elimina duplicados por título y URL."""
    seen_titles = set()
    seen_urls = set()
    result = []
    for item in items:
        title = item.get("title", "").lower().strip()
        url = item.get("url", "").strip()
        if title not in seen_titles and url not in seen_urls:
            seen_titles.add(title)
            seen_urls.add(url)
            result.append(item)
    return result

def main():
    log.info("=== Inicio de obtención de Agenda/Noticias Mérida ===")
    all_items = []

    for src in SOURCES:
        try:
            items = fetch_source(src["name"], src["url"], src["selectors"])
            all_items.extend(items)
        except Exception as e:
            log.error(f"Error en fuente {src['name']}: {e}")

    log.info(f"Total bruto: {len(all_items)} items.")

    # Deduplicar
    all_items = dedup(all_items)
    log.info(f"Tras deduplicar: {len(all_items)}.")

    # Fecha de hoy para comparaciones
    today_dt = datetime.now()
    today_str = today_dt.strftime("%Y-%m-%d")

    # Procesar fechas y filtrar
    processed_items = []
    for item in all_items:
        # Si no tiene fecha, asumimos que es de HOY (especialmente para noticias)
        if not item.get("date"):
            item["date"] = today_str
            
        # Filtro: Solo hoy y pasado (evitamos el ruido de "19 abr" que confundía al usuario)
        if item["date"] <= today_str:
            processed_items.append(item)

    # Ordenar por fecha descendente (LO MÁS NUEVO ARRIBA)
    processed_items.sort(key=lambda x: x.get("date", "0000-00-00"), reverse=True)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "count": len(processed_items),
        "events": processed_items,
    }
    OUTPUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info(f"=== Guardado en {OUTPUT_PATH} ({len(processed_items)} items) ===")

if __name__ == "__main__":
    main()
