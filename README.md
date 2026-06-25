# Tender Watch

Panel de seguimiento de licitaciones públicas para Winecta.

## Setup (una sola vez, ~15 minutos)

### 1. Crear el repositorio en GitHub

1. Ve a github.com y haz login
2. Haz clic en **New** (botón verde arriba a la izquierda)
3. Nombre: `tender-watch`
4. Selecciona **Private**
5. Haz clic en **Create repository**

### 2. Subir los archivos

En la página del repositorio vacío, haz clic en **uploading an existing file** y sube estos 4 archivos respetando la estructura:

```
tender-watch/
├── index.html
├── fetch_licitaciones.py
├── .github/
│   └── workflows/
│       └── fetch.yml
```

Para crear la carpeta `.github/workflows/`, en el campo de nombre del archivo escribe:
`.github/workflows/fetch.yml` — GitHub creará las carpetas automáticamente.

### 3. Activar GitHub Pages

1. Ve a **Settings** → **Pages**
2. Source: **Deploy from a branch**
3. Branch: `main` / carpeta `/ (root)`
4. Haz clic en **Save**

Tu panel estará disponible en: `https://daniellopez-win.github.io/tender-watch/`

> **Nota:** GitHub Pages en repositorios privados requiere plan GitHub Pro o Team. Si no tienes Pro, la alternativa es acceder al panel abriendo el archivo `index.html` directamente en el navegador tras clonar el repo, o usar Netlify con acceso privado (gratuito).

### 4. Ejecutar el workflow por primera vez

1. Ve a la pestaña **Actions**
2. Haz clic en **Actualizar licitaciones**
3. Haz clic en **Run workflow** → **Run workflow**

Esto generará el archivo `data/licitaciones.json` con las licitaciones actuales.

### 5. Automatización diaria

El workflow está configurado para ejecutarse automáticamente cada día a las 7:45 (hora española). No necesitas hacer nada más.

## Uso del panel

- **GO / NO-GO**: marca cada licitación con un clic
- **Nota**: añade el motivo o cualquier observación
- **Filtros**: filtra por estado o busca por texto libre
- Los estados y notas se guardan en tu navegador automáticamente

## Modificar palabras clave

Edita el archivo `fetch_licitaciones.py` y modifica la lista `KEYWORDS`.
