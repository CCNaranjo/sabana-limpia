# 🌿 SabanaLimpia — Plan de Desarrollo MVP

> **Proyecto:** Portal ciudadano de gestión de residuos sólidos — Sabana Centro, Cundinamarca
> **Stack:** Django 4.2 LTS + PostgreSQL + Django Templates + Vanilla JS + Leaflet.js (CDN)
> **Duración:** 3 semanas | **Metodología:** Kanban
> **Entregas de evidencia:** Lunes y Viernes de cada semana
> **Repositorio:** marcar tareas completadas con `[x]` en este archivo

---

## 📋 Índice

1. [Contexto del Proyecto](#1-contexto-del-proyecto)
2. [Arquitectura General](#2-arquitectura-general)
3. [Modelos de Datos](#3-modelos-de-datos)
4. [Rutas URL](#4-rutas-url)
5. [Tareas por Prioridad](#5-tareas-por-prioridad)
   - [Prioridad 1 — Bloqueantes](#-prioridad-1--bloqueantes-sin-esto-nada-funciona)
   - [Prioridad 2 — Flujo Ciudadano](#-prioridad-2--flujo-ciudadano-valor-core-del-mvp)
   - [Prioridad 3 — Flujo Operador](#-prioridad-3--flujo-operador-gestión-institucional)
   - [Prioridad 4 — Valor Agregado](#-prioridad-4--valor-agregado-pulido-final)
6. [Estructura de Carpetas](#6-estructura-de-carpetas)
7. [Comandos de Referencia Rápida](#7-comandos-de-referencia-rápida)
8. [Variables de Entorno](#8-variables-de-entorno)
9. [Criterios de Aceptación](#9-criterios-de-aceptación-por-historia)

---

## 1. Contexto del Proyecto

### Problema que resuelve
Los ciudadanos de Sabana Centro no tienen canal digital para reportar puntos de disposición ilegal de residuos ni para registrar sus hábitos domésticos de manejo. Las alcaldías no tienen datos estructurados para tomar decisiones. El informe CVSCC 2024 documenta que menos del 30 % de los ciudadanos ha usado algún canal digital para reportar un problema ambiental.

### Qué construimos
Una plataforma web con dos flujos principales:
- **Ciudadano:** reporta un punto crítico de basura (foto + GPS + categoría) o registra los residuos que generó en su hogar esa semana.
- **Operador municipal:** ve el mapa de reportes activos, cambia el estado de cada reporte y agrega notas de gestión visibles para el ciudadano.

### Por qué Django Templates y no React
Django incluye un motor de plantillas HTML propio. Esto significa que el frontend (HTML, CSS, JS) vive **dentro del mismo proyecto Django**, sin necesidad de un segundo framework separado. El navegador recibe páginas HTML completas generadas por el servidor. Para interactividad puntual (mapa, gráficas) se usan librerías cargadas desde CDN, sin instalación adicional.

**Resultado:** un solo proyecto, una sola carpeta, una sola tecnología. Exactamente lo que el profesor indicó.

### Usuarios del sistema
| Rol | Qué puede hacer |
|-----|----------------|
| `ciudadano` | Crear reportes públicos, registrar residuos domésticos, ver estado de sus reportes |
| `operador` | Ver todos los reportes de su municipio, cambiar estado, agregar nota de gestión |
| `admin` | Todo lo anterior + gestión de usuarios desde el panel `/admin/` de Django |

### Municipios incluidos en el MVP
Chía, Cajicá, Zipaquirá, Cogua, Tausa, Sopó, Tocancipá, Gachancipá, Nemocón, Supatá, Tabio.

---

## 2. Arquitectura General

```
┌──────────────────────────────────────────────────────┐
│               NAVEGADOR / CELULAR                    │
│     HTML generado por Django Templates               │
│     Vanilla JS + Leaflet.js (CDN) + Chart.js (CDN)  │
└───────────────────────┬──────────────────────────────┘
                        │ HTTP (formularios POST / AJAX)
┌───────────────────────▼──────────────────────────────┐
│               DJANGO 4.2 LTS  :8000                  │
│                                                       │
│  ┌─────────────┐ ┌──────────────┐ ┌───────────────┐  │
│  │  usuarios/  │ │  reportes/   │ │   residuos/   │  │
│  │  Auth + BD  │ │  CRUD + mapa │ │   Doméstico   │  │
│  └─────────────┘ └──────────────┘ └───────────────┘  │
│                                                       │
│  ┌────────────────────────────────────────────────┐  │
│  │      Django ORM  →  PostgreSQL  :5432          │  │
│  └────────────────────────────────────────────────┘  │
│                                                       │
│  ┌────────────────────────────────────────────────┐  │
│  │  /templates/  HTML   |   /static/  CSS + JS    │  │
│  │  /media/reportes/    imágenes subidas           │  │
│  └────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────┘
```

**Decisión de arquitectura para el profesor:** La base de datos PostgreSQL, el backend Django y el frontend (templates HTML) viven en el mismo proyecto y en el mismo servidor. No se usan APIs externas de terceros. Las imágenes se guardan en `/media/` local. El JS interactivo (mapa, gráficas) se carga desde CDN público gratuito.

---

## 3. Modelos de Datos

### `usuarios.CustomUser`
```
id              AutoField (PK)
username        CharField (se usa el email como username)
email           EmailField  — único
password        CharField   — hash automático Django
rol             CharField   — choices: ciudadano | operador | admin
municipio       CharField   — choices: los 11 municipios de Sabana Centro
fecha_registro  DateTimeField (auto al crear)
activo          BooleanField (default True)
```

### `reportes.Reporte`
```
id              AutoField (PK)
usuario         ForeignKey → CustomUser
titulo          CharField(120)
descripcion     TextField
categoria       CharField — choices:
                  residuos_solidos | escombros | residuos_peligrosos
                  raee | organicos | otro
latitud         FloatField
longitud        FloatField
foto            ImageField  — sube a /media/reportes/
estado          CharField — choices: pendiente | en_gestion | resuelto | rechazado
                  default: pendiente
municipio       CharField
nota_operador   TextField   — null=True, blank=True
operador        ForeignKey → CustomUser — null=True, blank=True
created_at      DateTimeField (auto al crear)
updated_at      DateTimeField (auto al modificar)
```

### `residuos.RegistroResiduo`
```
id                  AutoField (PK)
usuario             ForeignKey → CustomUser
semana              DateField  — lunes de la semana registrada
municipio           CharField
organico_kg         FloatField (default 0)
reciclable_kg       FloatField (default 0)
no_reciclable_kg    FloatField (default 0)
especial_kg         FloatField (default 0)
peligroso_kg        FloatField (default 0)
observaciones       TextField  — null=True, blank=True
created_at          DateTimeField (auto al crear)

Restricción: unique_together = ('usuario', 'semana')
→ Un ciudadano solo puede tener un registro por semana
```

---

## 4. Rutas URL

Todas las rutas viven en Django. El navegador navega entre páginas HTML completas.

```
/                           → Landing page (pública)
/auth/registro/             → Formulario registro ciudadano
/auth/login/                → Formulario login
/auth/logout/               → Cierra sesión y redirige a /

/reportes/nuevo/            → Formulario nuevo reporte     [ciudadano]
/reportes/mis-reportes/     → Lista reportes del usuario   [ciudadano]
/reportes/mapa/             → Mapa público de puntos       [público]

/residuos/nuevo/            → Formulario registro semanal  [ciudadano]
/residuos/mis-registros/    → Historial personal           [ciudadano]
/residuos/estadisticas/     → Estadísticas por municipio   [público]

/panel/                     → Panel operador — lista       [operador]
/panel/reporte/<id>/        → Detalle y cambio de estado   [operador]

/admin/                     → Panel admin Django           [admin]

/api/reportes/mapa/         → JSON con lat/lng para Leaflet [público]
/api/residuos/estadisticas/ → JSON para Chart.js            [público]
```

> Las dos rutas `/api/` devuelven JSON y son consumidas por Vanilla JS en el navegador.
> Todas las demás devuelven HTML completo desde Django Templates.

---

## 5. Tareas por Prioridad

> Las tareas están ordenadas de mayor a menor prioridad.
> No avanzar al siguiente bloque hasta completar el anterior.
> Usar `[x]` para marcar como completada en GitHub.

---

### 🔴 Prioridad 1 — Bloqueantes (sin esto, nada funciona)

> **Evidencia Lunes S1:** Repositorio creado, entorno configurado, modelos y migraciones aplicadas, servidor corriendo sin errores.
> **Evidencia Viernes S1:** Auth funcionando (registro + login + sesión), reporte creado y visible en `/admin/`, residuo registrado en BD.

---

- [X] **T-01 — Crear repositorio en GitHub**
  Crear repositorio privado con nombre `sabana-limpia`. Agregar a ambos colaboradores con rol de escritura. Inicializar con un `README.md` vacío.

- [X] **T-02 — Crear `.gitignore`**
  Agregar un `.gitignore` adecuado para proyectos Python/Django. Debe ignorar: `venv/`, `__pycache__/`, `*.pyc`, `.env`, `media/`, `db.sqlite3`. Usar gitignore.io con el término `django`.

- [X] **T-03 — Crear entorno virtual Python e instalar dependencias**
  Crear el entorno virtual con `python -m venv venv` y activarlo. Instalar: `django==4.2.*`, `psycopg2-binary`, `Pillow`, `python-decouple`. Generar `requirements.txt` con `pip freeze > requirements.txt`.

- [X] **T-04 — Crear proyecto Django y apps**
  Ejecutar `django-admin startproject config .` en la raíz del repositorio. Luego crear las tres apps: `python manage.py startapp usuarios`, `python manage.py startapp reportes`, `python manage.py startapp residuos`.

- [X] **T-05 — Crear base de datos PostgreSQL local**
  Abrir psql y ejecutar: `CREATE DATABASE sabanalimpia;`, `CREATE USER sabana_user WITH PASSWORD 'sabana_pass';`, `GRANT ALL PRIVILEGES ON DATABASE sabanalimpia TO sabana_user;`. Verificar conexión con `psql -U sabana_user -d sabanalimpia`.

- [X] **T-06 — Crear archivo `.env` con variables de entorno**
  Crear el archivo `.env` en la raíz del proyecto con todas las variables definidas en la sección [Variables de Entorno](#8-variables-de-entorno). Confirmar que el archivo está en `.gitignore` antes de hacer cualquier commit.

- [X] **T-07 — Configurar `settings.py`**
  Leer las variables de `.env` con `python-decouple`. Agregar todas las apps al `INSTALLED_APPS`. Configurar `DATABASES` apuntando a PostgreSQL. Definir `AUTH_USER_MODEL = 'usuarios.CustomUser'`. Configurar `MEDIA_ROOT` y `MEDIA_URL`. Configurar `TEMPLATES` para que Django encuentre la carpeta `templates/`. Configurar `STATICFILES_DIRS` para la carpeta `static/`.

- [X] **T-08 — Crear modelo `CustomUser` y migración**
  En `usuarios/models.py` crear la clase `CustomUser` heredando de `AbstractUser`. Agregar los campos `rol` (choices: ciudadano, operador, admin) y `municipio` (choices con los 11 municipios). Configurar `USERNAME_FIELD = 'email'` y `REQUIRED_FIELDS = ['username']`. Ejecutar `makemigrations usuarios` y `migrate`.

- [X] **T-09 — Configurar `config/urls.py` principal**
  Incluir las rutas de cada app (`usuarios.urls`, `reportes.urls`, `residuos.urls`). Habilitar el panel `/admin/`. Agregar las rutas de `MEDIA_URL` para servir imágenes en desarrollo con `static()`.

- [X] **T-10 — Crear vistas y templates de registro y login**
  En `usuarios/views.py` crear `RegistroView` y `LoginView` usando el sistema de autenticación de Django (`authenticate`, `login`, `logout`). Crear los templates `templates/usuarios/registro.html` y `templates/usuarios/login.html` con formularios HTML básicos. Validar: email único, contraseña mínimo 8 caracteres, municipio seleccionado.

- [X] **T-11 — Crear `LoginRequired` y decoradores de rol**
  En `usuarios/decorators.py` crear dos decoradores: `@login_required` (ya incluido en Django) para rutas que requieren sesión activa, y un decorador propio `@rol_requerido('operador')` que redirige a `/` si el usuario no tiene el rol correcto. Estos se usarán en todas las vistas protegidas.

- [X] **T-12 — Crear modelo `Reporte` y migración**
  En `reportes/models.py` crear el modelo `Reporte` con todos los campos definidos en la sección [Modelos de Datos](#3-modelos-de-datos). Registrar en `reportes/admin.py` con filtros por `estado`, `municipio` y `categoria`. Ejecutar `makemigrations reportes` y `migrate`.

- [X] **T-13 — Crear modelo `RegistroResiduo` y migración**
  En `residuos/models.py` crear el modelo `RegistroResiduo` con todos los campos definidos en la sección [Modelos de Datos](#3-modelos-de-datos). Agregar `unique_together = ('usuario', 'semana')` en la clase `Meta`. Registrar en `residuos/admin.py`. Ejecutar `makemigrations residuos` y `migrate`.

- [X] **T-14 — Crear superusuario y verificar admin**
  Ejecutar `python manage.py createsuperuser`. Acceder a `http://localhost:8000/admin/` y verificar que los modelos `CustomUser`, `Reporte` y `RegistroResiduo` aparecen correctamente con sus campos y filtros.

- [X] **T-15 — Crear template base (`base.html`)**
  Crear `templates/base.html` que todos los demás templates heredarán con `{% extends 'base.html' %}`. Debe incluir: barra de navegación con el logo "SabanaLimpia", links según rol del usuario (`{% if user.rol == 'operador' %}`), bloque `{% block content %}`, carga de Leaflet.js y Chart.js desde CDN, y CSS base de la aplicación desde `static/css/main.css`.

- [X] **T-16 — Verificar flujo completo de autenticación**
  Probar el ciclo completo en el navegador: registro de ciudadano → login → acceso a `/reportes/nuevo/` → logout → verificar que `/reportes/nuevo/` redirige a `/auth/login/` sin sesión. Este es el checkpoint de Semana 1.

---

### 🟠 Prioridad 2 — Flujo Ciudadano (valor core del MVP)

> **Evidencia Lunes S2:** Formulario de reporte funcional con foto y coordenadas. Formulario de residuos domésticos funcional.
> **Evidencia Viernes S2:** Mis reportes con badges de estado visibles. Mapa Leaflet con puntos reales del sistema.

---

- [ ] **T-17 — Crear formulario de nuevo reporte (template + vista)**
  Crear `templates/reportes/nuevo_reporte.html` con los campos: título, descripción, categoría (select), foto (input file), y un botón "Usar mi ubicación" que llama a `navigator.geolocation.getCurrentPosition()` en Vanilla JS y rellena dos campos ocultos `latitud` y `longitud`. Mostrar preview de la foto seleccionada antes de enviar. La vista en `reportes/views.py` recibe el POST, guarda la imagen en `/media/reportes/` y crea el objeto `Reporte` con `usuario=request.user` y `estado='pendiente'`.

- [ ] **T-18 — Comprimir foto en el cliente antes de subir**
  En `static/js/reporte.js` escribir una función con `canvas` de HTML5 que lee el archivo de foto seleccionado, lo redibuja en un canvas a máximo 1200px de ancho y lo exporta con calidad 0.8. Reemplazar el archivo en el input antes del envío del formulario. Esto garantiza que ninguna imagen supere 2 MB sin depender de librerías externas.

- [ ] **T-19 — Página "Mis Reportes"**
  Crear `templates/reportes/mis_reportes.html` y la vista correspondiente que hace `Reporte.objects.filter(usuario=request.user).order_by('-created_at')`. Mostrar tarjetas con: foto miniatura, título, categoría, municipio, fecha, badge de estado con color (pendiente=gris, en_gestion=amarillo, resuelto=verde, rechazado=rojo), y nota del operador si existe. Solo accesible con sesión activa.

- [ ] **T-20 — Crear formulario de registro de residuos domésticos**
  Crear `templates/residuos/nuevo_registro.html` con campos numéricos (kg) para cada tipo: orgánico, reciclable, no reciclable, especial, peligroso. Mostrar el rango de la semana actual (lunes a domingo) en el encabezado. Incluir texto de ayuda por cada tipo (ej: "Reciclable: papel, cartón, plástico limpio, vidrio"). La vista calcula automáticamente el lunes de la semana actual como campo `semana`. Si ya existe un registro para esa semana, mostrar el existente en lugar del formulario vacío.

- [ ] **T-21 — Página "Mis Registros" de residuos**
  Crear `templates/residuos/mis_registros.html` y la vista que lista todos los `RegistroResiduo` del usuario logueado ordenados por semana descendente. Mostrar una tabla simple con: semana, kg por tipo, total general y observaciones. Solo accesible con sesión activa.

- [ ] **T-22 — Página de confirmación post-reporte**
  Después de enviar un reporte exitosamente, redirigir a una página `templates/reportes/confirmacion.html` que muestra el número de reporte asignado, el estado inicial (Pendiente), y un botón para "Ver mis reportes" y otro para "Reportar otro problema". Esto cierra el ciclo de retroalimentación inmediata al ciudadano (criterio HU-01).

---

### 🟡 Prioridad 3 — Flujo Operador (gestión institucional)

> **Evidencia Lunes S3:** Panel operador con lista de reportes y filtros funcionando.
> **Evidencia Viernes S3:** Cambio de estado funcional con notificación por email visible en consola.

---

- [ ] **T-23 — Endpoint JSON para el mapa (`/api/reportes/mapa/`)**
  Crear una vista en `reportes/views.py` que devuelve `JsonResponse` con la lista de reportes: solo los campos `id`, `latitud`, `longitud`, `categoria`, `estado`, `municipio` y `titulo`. Sin autenticación requerida. Este endpoint es consumido por Leaflet.js en el navegador mediante `fetch()`.

- [ ] **T-24 — Página del mapa público de puntos críticos**
  Crear `templates/reportes/mapa.html`. Cargar Leaflet.js desde CDN. Inicializar el mapa centrado en Sabana Centro (`lat: 4.96, lng: -74.04, zoom: 11`) con tiles de OpenStreetMap (gratuitos, sin API key). Al cargar la página, hacer `fetch('/api/reportes/mapa/')` y agregar un marcador por cada reporte con color según categoría usando `L.circleMarker`. Al hacer click en un marcador, mostrar popup con título, estado y municipio. Agregar selectores HTML (filtros locales en JS) por municipio, categoría y estado.

- [ ] **T-25 — Panel del operador — lista de reportes**
  Crear `templates/panel/lista_reportes.html` y la vista protegida con `@rol_requerido('operador')`. La vista filtra `Reporte.objects.filter(municipio=request.user.municipio)` para que cada operador solo vea su municipio. Mostrar tabla con: ID, ciudadano, categoría, fecha, estado (badge), y botón "Gestionar" que lleva a `/panel/reporte/<id>/`.

- [ ] **T-26 — Vista de detalle y cambio de estado (operador)**
  Crear `templates/panel/detalle_reporte.html` y la vista protegida. Mostrar todos los datos del reporte: foto, descripción, coordenadas, historial de estados. Incluir formulario POST con: select de nuevo estado (En gestión / Resuelto / Rechazado) y textarea para nota de gestión (obligatoria si el estado es Resuelto o Rechazado). Al guardar, actualizar `estado`, `nota_operador`, `operador` y `updated_at` en la BD. Redirigir al panel con mensaje de éxito.

- [ ] **T-27 — Filtros en el panel del operador**
  Agregar filtros GET al panel del operador: por estado (`?estado=pendiente`) y por categoría (`?categoria=escombros`). La vista lee los parámetros con `request.GET.get()` y aplica `.filter()` adicionales al queryset. Los selects de filtro en el template mantienen su valor seleccionado al recargar la página.

- [ ] **T-28 — Notificaciones por email al cambiar estado**
  En `reportes/signals.py` crear un signal `post_save` sobre el modelo `Reporte`. Cuando el campo `estado` cambia, enviar un email al `reporte.usuario.email` con: número de reporte, nuevo estado y nota del operador si existe. En desarrollo, configurar `EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'` en `settings.py` para que el email se imprima en la consola de Django en lugar de enviarse realmente. Conectar el signal en `reportes/apps.py` dentro del método `ready()`.

- [ ] **T-29 — Endpoint JSON para estadísticas (`/api/residuos/estadisticas/`)**
  Crear una vista en `residuos/views.py` que devuelve `JsonResponse` con los totales agrupados por municipio usando `values('municipio').annotate(total_organico=Sum('organico_kg'), ...)` de Django ORM. Sin autenticación requerida. Este endpoint es consumido por Chart.js en el navegador.

- [ ] **T-30 — Página de estadísticas públicas**
  Crear `templates/residuos/estadisticas.html`. Cargar Chart.js desde CDN. Al cargar la página, hacer `fetch('/api/residuos/estadisticas/')` y renderizar: una gráfica de barras apiladas con kg por tipo de residuo por municipio, y un contador de reportes activos (pendiente + en_gestion) por municipio obtenido con una segunda consulta a la vista de reportes. Todo sin autenticación.

---

### 🔵 Prioridad 4 — Valor Agregado (pulido final)

> Completar solo si las prioridades 1, 2 y 3 están finalizadas y hay tiempo disponible.

---

- [ ] **T-31 — Landing page pública**
  Crear `templates/landing.html` como página de inicio en `/`. Incluir: nombre y descripción del proyecto, tres bloques de propuesta de valor (Reporta / Registra / Transforma), contador de reportes recibidos (consulta directa en la vista con `Reporte.objects.count()`), y botones de llamada a la acción hacia `/auth/registro/` y `/reportes/mapa/`.

- [ ] **T-32 — CSS y estilos visuales**
  Crear `static/css/main.css` con la identidad visual del proyecto: paleta verde (#1A5C2A principal, #2D8A45 secundario), tipografía sans-serif limpia, badges de estado con colores consistentes en todo el sitio, tarjetas con sombra suave para los reportes, y diseño responsivo básico con media queries para móvil. El objetivo es que se vea profesional sin usar frameworks CSS externos.

- [ ] **T-33 — Completar panel admin Django**
  Asegurar que `usuarios/admin.py`, `reportes/admin.py` y `residuos/admin.py` están completos con: campos de lista (`list_display`), filtros laterales (`list_filter`), búsqueda (`search_fields`) y acciones en lote. Crear desde el admin: 3 ciudadanos de prueba en municipios distintos, 2 operadores (uno para Chía, uno para Cajicá) y al menos 10 reportes de ejemplo con coordenadas reales de Sabana Centro.

- [ ] **T-34 — Ejecutar y documentar plan de pruebas PT-01 a PT-06**
  Ejecutar cada prueba del plan, tomar captura de pantalla del resultado y guardarlas en una carpeta `docs/pruebas/` en el repositorio. Documentar en `docs/PRUEBAS.md` el resultado de cada prueba (pasó / falló / observaciones).

  | ID | Prueba | Condición |
  |----|--------|-----------|
  | PT-01 | Envío de reporte completo con foto y GPS | Usuario ciudadano logueado, foto < 2 MB → reporte en BD con estado `pendiente` |
  | PT-02 | Actualización de estado por operador | Operador logueado → cambia estado a `en_gestion` → email visible en consola Django |
  | PT-03 | Registro de residuos domésticos | Ciudadano logueado → formulario enviado → datos en estadísticas públicas |
  | PT-04 | Endpoint protegido sin sesión | GET `/reportes/mis-reportes/` sin sesión → redirige a `/auth/login/` |
  | PT-05 | Acceso cruzado de roles | Usuario `ciudadano` intenta acceder a `/panel/` → redirige a `/` con mensaje de error |
  | PT-06 | Mapa con múltiples reportes | Al menos 5 reportes en BD → mapa carga, todos los markers visibles, filtros funcionan |

- [ ] **T-35 — Revisión final antes de entregar**
  Verificar: no hay credenciales hardcodeadas en el código (solo en `.env`), `.env` no está en el repositorio, `DEBUG=False` en `.env` de pruebas, todas las migraciones están aplicadas, `requirements.txt` está actualizado, carpeta `media/` está en `.gitignore` (las imágenes no van al repo), el servidor corre limpio con `python manage.py runserver` sin warnings.

- [ ] **T-36 — Crear `README.md` con instrucciones de instalación**
  Documentar en el `README.md` del repositorio los pasos exactos para que cualquier persona clone el proyecto y lo levante en local: clonar repo, crear entorno virtual, instalar dependencias, crear `.env`, crear BD, ejecutar migraciones, crear superusuario y correr servidor.

---

## 6. Estructura de Carpetas

```
sabana-limpia/
│
├── .env                          ← Variables de entorno (NO commitear)
├── .gitignore
├── README.md
├── requirements.txt
├── manage.py
│
├── config/                       ← Configuración Django
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── usuarios/                     ← App: auth y usuarios
│   ├── migrations/
│   ├── admin.py
│   ├── apps.py
│   ├── decorators.py             ← @rol_requerido(rol)
│   ├── models.py                 ← CustomUser
│   ├── urls.py
│   └── views.py                  ← registro, login, logout
│
├── reportes/                     ← App: puntos críticos
│   ├── migrations/
│   ├── admin.py
│   ├── apps.py
│   ├── models.py                 ← Reporte
│   ├── signals.py                ← Notificación email al cambiar estado
│   ├── urls.py
│   └── views.py                  ← CRUD + JSON mapa
│
├── residuos/                     ← App: registro doméstico
│   ├── migrations/
│   ├── admin.py
│   ├── apps.py
│   ├── models.py                 ← RegistroResiduo
│   ├── urls.py
│   └── views.py                  ← CRUD + JSON estadísticas
│
├── templates/                    ← HTML generado por Django
│   ├── base.html                 ← Template padre (navbar, CDN, bloque content)
│   ├── landing.html
│   ├── usuarios/
│   │   ├── login.html
│   │   └── registro.html
│   ├── reportes/
│   │   ├── nuevo_reporte.html
│   │   ├── mis_reportes.html
│   │   ├── confirmacion.html
│   │   └── mapa.html
│   ├── residuos/
│   │   ├── nuevo_registro.html
│   │   ├── mis_registros.html
│   │   └── estadisticas.html
│   └── panel/
│       ├── lista_reportes.html
│       └── detalle_reporte.html
│
├── static/                       ← CSS y JS propios del proyecto
│   ├── css/
│   │   └── main.css
│   └── js/
│       └── reporte.js            ← Geoloc + compresión de foto
│
└── media/                        ← Imágenes subidas (generado en runtime)
    └── reportes/                 ← NO commitear al repositorio
```

---

## 7. Comandos de Referencia Rápida

```bash
# ── Entorno virtual ──────────────────────────────────────
python -m venv venv
source venv/bin/activate        # Mac / Linux
venv\Scripts\activate           # Windows
deactivate                      # Salir del entorno

# ── Instalación ──────────────────────────────────────────
pip install django==4.2.* psycopg2-binary Pillow python-decouple
pip freeze > requirements.txt
pip install -r requirements.txt   # Para el compañero al clonar

# ── Django diario ────────────────────────────────────────
python manage.py runserver        # Iniciar servidor en :8000
python manage.py makemigrations   # Crear migraciones tras cambiar modelos
python manage.py migrate          # Aplicar migraciones a la BD
python manage.py createsuperuser  # Crear usuario admin
python manage.py shell            # Shell interactivo de Django (útil para probar queries)
python manage.py test             # Correr todos los tests

# ── PostgreSQL ───────────────────────────────────────────
psql -U postgres                  # Entrar a psql
\l                                # Listar bases de datos
\c sabanalimpia                   # Conectar a la BD del proyecto
\dt                               # Listar tablas
\q                                # Salir

# ── Git ──────────────────────────────────────────────────
git status
git add .
git commit -m "feat(reportes): agregar formulario nuevo reporte"
git push origin main
```

---

## 8. Variables de Entorno

### Archivo `.env` — en la raíz del proyecto, junto a `manage.py`

```env
# Django
SECRET_KEY=generar-con-el-comando-de-abajo
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Base de datos PostgreSQL local
DB_NAME=sabanalimpia
DB_USER=sabana_user
DB_PASSWORD=sabana_pass
DB_HOST=localhost
DB_PORT=5432

# Email (en desarrollo imprime en consola, sin cuenta real)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

**Cómo generar el SECRET_KEY:**
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

**Cómo leer `.env` en `settings.py` con python-decouple:**
```python
from decouple import config

SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', cast=bool)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT'),
    }
}
```

> ⚠️ El archivo `.env` **nunca** debe subirse al repositorio. Confirmar que está en `.gitignore` antes del primer commit.

---

## 9. Criterios de Aceptación por Historia

| ID | Historia de usuario | Criterio mínimo para marcar como LISTO |
|----|---------------------|----------------------------------------|
| HU-01 | Reporte ciudadano | Formulario enviado en ≤ 3 pasos, foto comprimida < 2 MB, reporte visible en BD con estado `pendiente`, página de confirmación con número de reporte |
| HU-02 | Consultar estado de reporte | Lista "Mis Reportes" carga correctamente, badge de estado visible con color correcto, nota del operador visible si existe |
| HU-03 | Mapa interactivo | Mapa carga en < 3 s en local, todos los markers de BD visibles, filtros por municipio/estado/categoría funcionan sin errores |
| HU-04 | Panel operador — gestión | Operador puede cambiar estado y agregar nota, cambio reflejado en la tabla al volver al panel |
| HU-05 | Registro doméstico | Formulario enviado correctamente, datos aparecen en la página de estadísticas públicas |
| HU-06 | Estadísticas domésticas | Gráfica de barras y contadores renderizan con datos reales de la BD |
| HU-07 | Notificación cambio de estado | Email visible en consola de Django al cambiar el estado de cualquier reporte |
| HU-08 | Landing page | Página pública carga sin sesión, contador de reportes actualizado, botones de acción funcionan |

---

## 📌 Notas para el equipo

- **División de trabajo sugerida:** Un desarrollador toma las apps de backend (`usuarios`, `reportes`, `residuos` — modelos, vistas, signals) y el otro toma los templates HTML y el JS estático. La coordinación principal ocurre en T-16 (auth completo) y T-23 (endpoint JSON para el mapa), donde ambas partes se conectan.
- **Orden estricto de Prioridad 1:** No comenzar ninguna tarea de Prioridad 2 hasta tener T-16 completado y verificado. Todo el sistema depende de que la autenticación funcione correctamente.
- **Commits descriptivos:** Un commit por tarea completada. Formato sugerido: `feat(app): descripción corta` para funcionalidades nuevas, `fix(app): descripción` para correcciones. Ejemplo: `feat(reportes): agregar compresión de foto en cliente`.
- **Panel admin para pruebas:** Usar `/admin/` de Django para crear datos de prueba (usuarios, reportes, registros) durante el desarrollo. Es más rápido que llenar formularios manualmente.
- **Kanban en GitHub Projects:** Crear un tablero con columnas: Por hacer / En progreso / Revisión / Listo. Cada tarea T-XX es una tarjeta. Mover las tarjetas al empezar y al terminar cada tarea.

---

*Documento generado para el proyecto SabanaLimpia — Facultad de Ingeniería, Universidad de Cundinamarca. Mayo 2025.*
