# Gráficas de Energía — Django + Supabase + Render

Proyecto Django que permite cargar un Excel con consumos de energía
(Activa, Reactiva, Capacitiva, Penalizada, Factor) por hora y por día, y
genera automáticamente:

1. **Hora vs Energía** — línea de tiempo con el promedio de cada hora, una serie por tipo.
2. **Día vs Energía** — barras agrupadas con el total diario, una serie por tipo.
3. **Total** — diagrama (barras + torta) con el total acumulado por tipo de energía.

Cada carga se guarda bajo un **nombre** que tú eliges (ej: "Cliente 1082527 - Junio 2026"),
y queda almacenada permanentemente en la base de datos para volver a consultarla.

## Estructura esperada del Excel

| FECHA | Id de Cliente | Tipo de Energía | Hora: 1 | ... | Hora: 24 | TOTAL |
|---|---|---|---|---|---|---|
| 2025-06-01 | 1082527 | Activa | 17.19 | ... | 16.73 | 575.52 |

`Tipo de Energía` puede ser: Activa, Reactiva, Capacitiva, Penalizada, Factor.

## 1. Poner en marcha en local

```bash
python -m venv .venv
source .venv/bin/activate    # en Windows: .venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# edita .env: pon tu DATABASE_URL de Supabase (o déjalo vacío para usar sqlite local)

python manage.py migrate
python manage.py createsuperuser   # opcional, para entrar a /admin/
python manage.py runserver
```

Abre http://127.0.0.1:8000

## 2. Configurar Supabase

1. Crea un proyecto en https://supabase.com
2. Ve a **Project Settings > Database > Connection string > URI**
3. Copia la cadena en modo **Transaction pooler** (puerto 6543) — es la recomendada
   para apps con muchas conexiones cortas como esta.
4. Pégala como `DATABASE_URL` en tu `.env` (local) y en las variables de entorno de Render.
5. Corre `python manage.py migrate` una vez para crear las tablas en Supabase.

No necesitas crear las tablas manualmente en el editor de Supabase: las migraciones
de Django (`ConjuntoGraficas` y `RegistroEnergia`) las crean por ti.

## 3. Desplegar en Render

**Opción A — con `render.yaml` (Blueprint):**
1. Sube este proyecto a un repo de GitHub.
2. En Render: **New > Blueprint**, selecciona el repo. Render leerá `render.yaml`.
3. Cuando pida `DATABASE_URL`, pega la connection string de Supabase.
4. Deploy.

**Opción B — manual:**
1. **New > Web Service**, conecta el repo.
2. Build Command: `./build.sh`
3. Start Command: `gunicorn energia_project.wsgi`
4. Agrega variables de entorno: `SECRET_KEY`, `DEBUG=False`, `DATABASE_URL`, `ALLOWED_HOSTS=.onrender.com`

## Estructura del proyecto

```
energia_project/       # settings, urls, wsgi
graficas/               # app principal
  models.py             # ConjuntoGraficas, RegistroEnergia
  forms.py              # formulario de carga (nombre + archivo)
  views.py              # parseo del Excel + cálculo de series para las 3 gráficas
  templates/graficas/    # upload.html, lista.html, detalle.html
templates/base.html      # layout con Bootstrap
requirements.txt
build.sh / Procfile / render.yaml   # despliegue en Render
```

## Notas técnicas

- El parseo usa `pandas` + `openpyxl` para leer el `.xlsx`.
- Las 24 horas se guardan como `JSONField` (una lista), no como 24 columnas —
  así es más fácil consultarlas y no hay que migrar el modelo si cambia el rango de horas.
- Las gráficas se renderizan en el navegador con **Chart.js** (vía CDN), a partir
  de series calculadas en `views.py` y pasadas como JSON al template.
- "Factor" es el factor de potencia (escala 0–1), distinto en magnitud a las
  demás energías (kWh); en el diagrama de Total puede verse "aplastado" frente
  a las otras series — si quieres, se puede separar en su propio eje o gráfica.

## Posibles mejoras futuras

- Autenticación de usuarios (para que cada quien vea solo sus conjuntos).
- Filtro por rango de fechas o por cliente dentro del detalle.
- Exportar cada conjunto de vuelta a Excel/PDF.
- Comparar dos conjuntos de gráficas lado a lado.
