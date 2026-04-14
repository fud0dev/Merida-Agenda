# 📅 Agenda Mérida — Noticias y Eventos en Tiempo Real

Una plataforma automatizada que centraliza toda la actualidad, cultura y ocio de la ciudad de **Mérida (Extremadura, España)**. El proyecto utiliza técnicas de web scraping para unificar 10 fuentes locales oficiales en una interfaz "Premium" moderna y siempre actualizada.

🔗 **Web en vivo:** [MeridaAgenda](https://fud0dev.github.io/AgendaMerida/)

---

## ✨ Características Destacadas

- **Multifuente Inteligente**: Agregador de noticias de 10 medios locales (Ayuntamiento, Hoy.es, El Periódico, Cadena SER, etc.).
- **Diseño Premium Light**: Una interfaz minimalista basada en tipografía clásica y elegancia moderna, con el escudo oficial de la ciudad.
- **Información Enriquecida**: No solo verás titulares; el sistema extrae entradillas y detalles de cada evento para que estés informado de un vistazo.
- **Deduplicación Automática**: Un avanzado motor de filtrado evita que veas la misma noticia repetida si aparece en varios periódicos.
- **Alta Frecuencia**: Gracias a GitHub Actions, la información se refresca **cada 2 horas**.

---

## 🛠️ Cómo funciona el proyecto

El proyecto se divide en tres piezas clave:

1.  **El Extractor (`scripts/fetch_events.py`)**: Un script en Python que recorre las 10 webs, analiza su HTML mediante `BeautifulSoup`, limpia los datos y los guarda en un archivo JSON.
2.  **La Automatización (`.github/workflows/events.yml`)**: Un "mayordomo" virtual en la nube de GitHub que se despierta cada 120 minutos, ejecuta el extractor y actualiza la web sin intervención humana.
3.  **La Interfaz (`docs/index.html`)**: Una Single Page Application (SPA) ultra rápida que lee el archivo generado y presenta la información con animaciones suaves y un buscador en tiempo real.

---

## 📅 Fuentes Integradas

El sistema vigila constantemente:
- Ayuntamiento de Mérida (Noticias y Agenda)
- El Periódico Extremadura
- Diario HOY
- Mérida Diario / Mérida Noticias / Mérida y Comarca
- La Crónica de Badajoz
- Cadena SER y Onda Cero Mérida

---

## 🚀 Despliegue propio

Si quieres tener tu propia versión:
1. Haz un **Fork** de este repositorio.
2. Sube los archivos a tu cuenta.
3. Activa **GitHub Pages** en `Settings > Pages` apuntando a la rama `main` y la carpeta `/docs`.
4. ¡Listo! El sistema empezará a trabajar solo.

---

## ⚖️ Aviso Legal e Intención
Este proyecto ha sido desarrollado por **[fud0dev](https://github.com/fud0dev)** con fines **estrictamente educativos** y de difusión cultural. Respeta los derechos de autor de las fuentes originales, sirviendo únicamente como un agregador de enlaces e información pública.

