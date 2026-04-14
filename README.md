# 📅 Mérida Agenda

Agenda de eventos automática para **Mérida (Extremadura, España)**,
publicada en GitHub Pages y actualizada cada 6 horas mediante GitHub Actions.

🔗 **Web:** `https://fud0dev.github.io/merida-agenda/`

---

## Estructura

```
.github/workflows/events.yml   ← Workflow de GitHub Actions
scripts/fetch_events.py        ← Script de obtención de eventos
docs/index.html                ← Página estática
docs/events.json               ← Datos generados automáticamente
```

## Fuentes de datos

1. **Eventbrite** — Búsqueda pública de eventos en Mérida
2. **Ayuntamiento de Mérida** — Agenda cultural oficial
3. **Turismo de Extremadura** — Portal regional
4. **Cultura Extremadura (Junta)** — Agenda institucional

## Setup en GitHub

1. Sube este repositorio a `pachexyz/merida-agenda`
2. Ve a **Settings → Pages** y configura:
   - Source: `Deploy from a branch`
   - Branch: `main`, carpeta: `/docs`
3. El workflow se ejecutará automáticamente cada 6 horas.
4. Para ejecución manual: **Actions → Fetch Mérida Events → Run workflow**

## Desarrollo local

```bash
pip install requests beautifulsoup4 lxml
python scripts/fetch_events.py
# Abre docs/index.html en el navegador
```

## Licencia

MIT
