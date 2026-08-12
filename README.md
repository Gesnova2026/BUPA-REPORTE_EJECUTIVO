# Reporte Ejecutivo BUPA

Reporte HTML autocontenido (sin backend) del tablero Monday.com "BUPA" (id `9801038662`), publicado con GitHub Pages y refrescado automáticamente vía GitHub Actions.

## Estructura del repo

- `index.html` — el reporte publicado. Se regenera automáticamente; no lo edites a mano.
- `template.html` — la plantilla del reporte (todo el diseño, tablas, gráficos y lógica). El workflow reemplaza los marcadores `__STATIC_ITEMS_JSON__` y `__GENERATED_AT_ISO__` para producir `index.html`.
- `scripts/refresh_report.py` — script que consulta la API de Monday.com y regenera `index.html` a partir de `template.html`.
- `.github/workflows/refresh.yml` — workflow de GitHub Actions que corre el script en un horario y hace commit/push del `index.html` actualizado.

## Puesta en marcha (una sola vez)

1. **Sube este contenido a tu repo** en GitHub Enterprise (on-premise), en la rama por defecto (ej. `main`), manteniendo esta misma estructura de carpetas.

2. **Crea un token de API de Monday.com**:
   - En Monday: ícono de tu avatar (esquina inferior izquierda) → **Admin** → **API**, o **Perfil** → **Developers** → **My Access Tokens**.
   - Copia el token (empieza con `eyJ...`). Debe tener acceso de lectura al workspace "Novacash Transversal - Gesnova" / tablero BUPA.

3. **Agrega el token como secret del repo**:
   - En GitHub: **Settings** → **Secrets and variables** → **Actions** → **New repository secret**.
   - Nombre: `MONDAY_API_TOKEN`. Valor: el token que copiaste.

4. **Habilita GitHub Pages**:
   - **Settings** → **Pages**.
   - Source: rama `main`, carpeta `/ (root)`.
   - Guarda. GitHub te dará la URL pública del sitio (dentro de tu instancia on-premise).

5. **Configura el runner de Actions**:
   - GitHub Enterprise Server (on-premise) normalmente no trae runners hospedados por GitHub — necesitas un runner **self-hosted** registrado por tu administrador (**Settings** → **Actions** → **Runners** → **New self-hosted runner**).
   - Si tu instancia sí tiene runners hospedados habilitados (algunas empresas los configuran), puedes cambiar `runs-on: self-hosted` por `runs-on: ubuntu-latest` en `.github/workflows/refresh.yml`.

6. **Corre el workflow manualmente la primera vez** (no hace falta esperar la hora en punto):
   - **Actions** → **Refrescar Reporte BUPA** → **Run workflow**.
   - Si todo está bien configurado, el job va a hacer commit de un `index.html` actualizado con datos frescos de Monday.

## Frecuencia de actualización

Por defecto el workflow corre **cada 5 minutos** (`cron: "*/5 * * * *"`), el mínimo recomendado por GitHub. En momentos de alta carga la ejecución puede demorarse un poco más de lo programado — no es instantáneo por cada visita, pero se mantiene prácticamente al día. Para cambiar la frecuencia, edita la línea `cron` en `.github/workflows/refresh.yml` (formato estándar de cron, en UTC).

## Notas

- **Por qué no es 100% en vivo:** la API de Monday.com no permite llamadas directas desde el navegador (no tiene CORS habilitado), así que la página no puede consultar a Monday en el instante exacto en que alguien la abre. Por eso el refresco lo hace GitHub Actions cada 5 minutos y guarda el resultado como snapshot — es la forma seria de hacerlo sin exponer el token de Monday a quien consulta la página.
- El reporte es un snapshot: muestra los datos tal como estaban en la última corrida del workflow (el encabezado del reporte indica la fecha/hora de generación en hora de Chile).
- Si el workflow falla, revisa la pestaña **Actions** del repo para ver el error (token vencido, sin acceso al tablero, runner caído, etc.).
- Todo el diseño y la lógica de negocio (definición de "Completado", alcance de sprints, agrupaciones, etc.) vive en `template.html`. Si se necesitan cambios de diseño o de reglas de negocio, se edita `template.html`, no `index.html`.
