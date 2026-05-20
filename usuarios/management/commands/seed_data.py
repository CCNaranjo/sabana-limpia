"""
Comando Django para poblar la BD con datos de prueba.
Idempotente: no duplica datos si ya existen.

Uso:
    python manage.py seed_data
    python manage.py seed_data --limpiar   (borra reportes y usuarios de prueba antes)

Usuarios creados:
    Operadores  (3): Chía, Cajicá, Zipaquirá
    Ciudadanos  (3): Chía, Cajicá, Zipaquirá  ← uso general
    Ciudadano A    : muchos reportes           ← prueba insignias de reporte
    Ciudadano B    : muchos registros residuos ← prueba insignias de residuos
    Ciudadano C    : reportes en varios municipios ← prueba insignias territoriales
"""

import random
from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from reportes.models import Reporte
from residuos.models import RegistroResiduo

User = get_user_model()


# ── Operadores ────────────────────────────────────────────────────
OPERADORES = [
    {
        'email':      'operador_chia@sabanalimpia.co',
        'first_name': 'Carlos',
        'last_name':  'Mendoza',
        'municipio':  'Chia',
        'password':   'Operador2025!',
        'rol':        'operador',
        'is_staff':   True,
    },
    {
        'email':      'operador_cajica@sabanalimpia.co',
        'first_name': 'Laura',
        'last_name':  'Fonseca',
        'municipio':  'Cajica',
        'password':   'Operador2025!',
        'rol':        'operador',
        'is_staff':   True,
    },
    {
        'email':      'operador_zipaquira@sabanalimpia.co',
        'first_name': 'Andrés',
        'last_name':  'Torres',
        'municipio':  'Zipaquira',
        'password':   'Operador2025!',
        'rol':        'operador',
        'is_staff':   True,
    },
]

# ── Ciudadanos base ───────────────────────────────────────────────
CIUDADANOS = [
    {
        'email':      'ciudadano_chia@sabanalimpia.co',
        'first_name': 'María',
        'last_name':  'García',
        'municipio':  'Chia',
        'password':   'Ciudadano2025!',
        'rol':        'ciudadano',
    },
    {
        'email':      'ciudadano_cajica@sabanalimpia.co',
        'first_name': 'Jorge',
        'last_name':  'Rojas',
        'municipio':  'Cajica',
        'password':   'Ciudadano2025!',
        'rol':        'ciudadano',
    },
    {
        'email':      'ciudadano_zipaquira@sabanalimpia.co',
        'first_name': 'Ana',
        'last_name':  'Vargas',
        'municipio':  'Zipaquira',
        'password':   'Ciudadano2025!',
        'rol':        'ciudadano',
    },
]

# ── Ciudadanos especiales para prueba de insignias ────────────────
CIUDADANOS_GAMIFICACION = [
    {
        'email':      'reporter_activo@sabanalimpia.co',
        'first_name': 'Luis',
        'last_name':  'Ramírez',
        'municipio':  'Chia',
        'password':   'Test2025!',
        'rol':        'ciudadano',
        'tipo':       'muchos_reportes',   # Panoptes (30), Argos (15), Ojo (5)
    },
    {
        'email':      'reciclador_fiel@sabanalimpia.co',
        'first_name': 'Sofía',
        'last_name':  'Moreno',
        'municipio':  'Cajica',
        'password':   'Test2025!',
        'rol':        'ciudadano',
        'tipo':       'muchos_residuos',   # Gaia Perpetua (8 semanas)
    },
    {
        'email':      'guardian_regional@sabanalimpia.co',
        'first_name': 'David',
        'last_name':  'Castro',
        'municipio':  'Zipaquira',
        'password':   'Test2025!',
        'rol':        'ciudadano',
        'tipo':       'varios_municipios', # Atlas, Telamon (6 municipios)
    },
]

# ── Reportes base: 5 por municipio = 15 ──────────────────────────
# Coordenadas reales verificadas:
#   Chía centro histórico:     4.8618, -73.9254
#   La Caro (peaje):           4.7785, -73.9802
#   Parque principal Chía:     4.8620, -73.9260
#   Barrio Sabana (norte):     4.8790, -73.9185
#   Zona veredal Tíquiza:      4.8952, -73.9048
#   Acequia Río Frío:          4.8503, -73.9398
#   Cajicá centro:             4.9181, -74.0243
#   Zipaquirá centro:          5.0226, -74.0060

REPORTES_SEMILLA = {
    'Chia': [
        {
            'titulo':      'Escombros en vía principal — Peaje La Caro',
            'descripcion': 'Acumulación de escombros de construcción sobre la vía '
                           'principal cerca al peaje La Caro. Obstruye un carril.',
            'categoria':   'escombros',
            'latitud':      4.7785,
            'longitud':   -73.9802,
            'estado':      'resuelto',
        },
        {
            'titulo':      'Basura orgánica sin recolectar — Parque Principal Chía',
            'descripcion': 'Bolsas de basura orgánica sin recolectar desde hace 4 días '
                           'en el parque principal. Genera mal olor y atrae vectores.',
            'categoria':   'organicos',
            'latitud':      4.8620,
            'longitud':   -73.9260,
            'estado':      'en_gestion',
        },
        {
            'titulo':      'Punto ilegal de residuos — Barrio Sabana Norte',
            'descripcion': 'Residentes del barrio acumulan residuos en el andén de '
                           'la esquina. El camión de basura no recoge en este punto.',
            'categoria':   'residuos_solidos',
            'latitud':      4.8790,
            'longitud':   -73.9185,
            'estado':      'pendiente',
        },
        {
            'titulo':      'RAEE abandonados — Camino veredal hacia Tíquiza',
            'descripcion': 'Televisores y computadores viejos tirados en el borde '
                           'del camino veredal. Riesgo de lixiviados.',
            'categoria':   'raee',
            'latitud':      4.8952,
            'longitud':   -73.9048,
            'estado':      'pendiente',
        },
        {
            'titulo':      'Residuos peligrosos en acequia del Río Frío',
            'descripcion': 'Recipientes con líquido de color amarillo junto a la '
                           'acequia. Posible riesgo de contaminación hídrica.',
            'categoria':   'residuos_peligrosos',
            'latitud':      4.8503,
            'longitud':   -73.9398,
            'estado':      'en_gestion',
        },
    ],
    'Cajica': [
        {
            'titulo':      'Escombros frente al Parque Los Cerezos',
            'descripcion': 'Obra sin terminar dejó escombros en el andén. '
                           'Dificulta el paso de peatones y personas en silla de ruedas.',
            'categoria':   'escombros',
            'latitud':      4.9205,
            'longitud':   -74.0278,
            'estado':      'resuelto',
        },
        {
            'titulo':      'Acumulación crónica — Vía Cajicá-Zipaquirá km 3',
            'descripcion': 'Punto crónico de disposición de bolsas en el kilómetro 3 '
                           'de la vía. Se repite cada fin de semana.',
            'categoria':   'residuos_solidos',
            'latitud':      4.9320,
            'longitud':   -74.0195,
            'estado':      'resuelto',
        },
        {
            'titulo':      'Quema de residuos — Vereda Canelón',
            'descripcion': 'Humo negro visible desde la vía principal. Pobladores '
                           'queman residuos al no tener ruta de recolección en la vereda.',
            'categoria':   'residuos_peligrosos',
            'latitud':      4.9075,
            'longitud':   -74.0385,
            'estado':      'en_gestion',
        },
        {
            'titulo':      'Electrodomésticos abandonados — Calle 5 urbana',
            'descripcion': 'Nevera y lavadora tiradas en el andén de la calle 5. '
                           'Llevan más de una semana sin ser recogidas.',
            'categoria':   'raee',
            'latitud':      4.9181,
            'longitud':   -74.0243,
            'estado':      'pendiente',
        },
        {
            'titulo':      'Residuos orgánicos en zona industrial norte',
            'descripcion': 'Desperdicios de alimentos acumulados en el andén de '
                           'la zona industrial norte de Cajicá.',
            'categoria':   'organicos',
            'latitud':      4.9248,
            'longitud':   -74.0210,
            'estado':      'pendiente',
        },
    ],
    'Zipaquira': [
        {
            'titulo':      'Basura en acceso a la Catedral de Sal',
            'descripcion': 'Turistas dejan residuos en la vía de acceso principal. '
                           'Zona de alto flujo peatonal, impacto en imagen turística.',
            'categoria':   'residuos_solidos',
            'latitud':      5.0253,
            'longitud':   -74.0048,
            'estado':      'resuelto',
        },
        {
            'titulo':      'Escombros en centro histórico — Calle 6 con Carrera 8',
            'descripcion': 'Materiales de remodelación abandonados en la calle 6 con '
                           'carrera 8. Deteriora la imagen del centro histórico.',
            'categoria':   'escombros',
            'latitud':      5.0218,
            'longitud':   -74.0068,
            'estado':      'en_gestion',
        },
        {
            'titulo':      'Punto ilegal — Parque La Independencia norte',
            'descripcion': 'El costado norte del parque se usa como basurero '
                           'improvisado los fines de semana.',
            'categoria':   'residuos_solidos',
            'latitud':      5.0226,
            'longitud':   -74.0060,
            'estado':      'pendiente',
        },
        {
            'titulo':      'RAEE en vía a Nemocón — km 2',
            'descripcion': 'Monitores y baterías tiradas en el borde de la '
                           'carretera hacia Nemocón en el kilómetro 2.',
            'categoria':   'raee',
            'latitud':      5.0312,
            'longitud':   -74.0015,
            'estado':      'pendiente',
        },
        {
            'titulo':      'Residuos peligrosos en quebrada El Rincón',
            'descripcion': 'Bidones con sustancias desconocidas cerca a la quebrada. '
                           'Posible contaminación hídrica inmediata.',
            'categoria':   'residuos_peligrosos',
            'latitud':      5.0198,
            'longitud':   -74.0085,
            'estado':      'en_gestion',
        },
    ],
}

# ── Reportes extra por municipio para ciudadano con muchos reportes ──
# 30 reportes en Chía (distinto título cada uno) → activa Panoptes
REPORTES_MUCHOS = [
    {
        'titulo':    f'Reporte de prueba #{i:02d} — Chía',
        'descripcion': f'Punto de disposición ilegal documentado en recorrido de campo '
                       f'número {i}. Requiere atención municipal.',
        'categoria':  random.choice(['residuos_solidos', 'escombros', 'organicos', 'raee']),
        'latitud':    round(4.8618 + random.uniform(-0.025, 0.025), 4),
        'longitud':   round(-73.9254 + random.uniform(-0.020, 0.020), 4),
        'municipio':  'Chia',
        'estado':     random.choice(['pendiente', 'en_gestion', 'resuelto']),
    }
    for i in range(1, 31)   # 30 reportes
]

# ── Reportes en 6 municipios distintos → activa Telamon ───────────
REPORTES_MULTIMUNICIPIOS = [
    {
        'titulo':     'Escombros — Sopó Centro',
        'descripcion':'Punto de escombros en el centro de Sopó.',
        'categoria':  'escombros',
        'latitud':     4.9118,
        'longitud':  -73.9408,
        'municipio':  'Sopo',
        'estado':     'pendiente',
    },
    {
        'titulo':     'Basura — Tocancipá Zona Industrial',
        'descripcion':'Residuos sólidos en zona industrial de Tocancipá.',
        'categoria':  'residuos_solidos',
        'latitud':     4.9660,
        'longitud':  -73.9110,
        'municipio':  'Tocancipa',
        'estado':     'pendiente',
    },
    {
        'titulo':     'RAEE — Gachancipá vía principal',
        'descripcion':'Equipos electrónicos abandonados en vía principal.',
        'categoria':  'raee',
        'latitud':     4.9780,
        'longitud':  -73.8980,
        'municipio':  'Gachancipa',
        'estado':     'pendiente',
    },
    {
        'titulo':     'Orgánicos — Cogua mercado',
        'descripcion':'Residuos orgánicos sin recolectar en el mercado de Cogua.',
        'categoria':  'organicos',
        'latitud':     5.0685,
        'longitud':  -73.9755,
        'municipio':  'Cogua',
        'estado':     'pendiente',
    },
    {
        'titulo':     'Peligrosos — Tabio quebrada',
        'descripcion':'Bidones en quebrada rural de Tabio.',
        'categoria':  'residuos_peligrosos',
        'latitud':     4.9140,
        'longitud':  -74.0960,
        'municipio':  'Tabio',
        'estado':     'pendiente',
    },
    {
        'titulo':     'Escombros — Nemocón vía secundaria',
        'descripcion':'Escombros en vía secundaria de Nemocón.',
        'categoria':  'escombros',
        'latitud':     5.0730,
        'longitud':  -73.8790,
        'municipio':  'Nemocon',
        'estado':     'pendiente',
    },
]


class Command(BaseCommand):
    help = 'Pobla la BD con usuarios, reportes y residuos de prueba (idempotente).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limpiar',
            action='store_true',
            help='Elimina los datos de prueba antes de volver a crearlos.',
        )

    def handle(self, *args, **options):
        if options['limpiar']:
            self._limpiar()

        self._crear_usuarios(OPERADORES, 'operadores')
        self._crear_usuarios(CIUDADANOS, 'ciudadanos base')
        self._crear_usuarios(CIUDADANOS_GAMIFICACION, 'ciudadanos de gamificación')
        self._crear_reportes_base()
        self._crear_reportes_gamificacion()
        self._crear_registros_residuos()

        self.stdout.write(self.style.SUCCESS('\n✅ Seeder completado exitosamente.'))
        self._imprimir_credenciales()

    # ────────────────────────────────────────────────────────────────────────
    # Helpers privados
    # ────────────────────────────────────────────────────────────────────────

    def _limpiar(self):
        todos = OPERADORES + CIUDADANOS + CIUDADANOS_GAMIFICACION
        emails = [u['email'] for u in todos]
        n_reportes = Reporte.objects.filter(usuario__email__in=emails).count()
        n_residuos = RegistroResiduo.objects.filter(usuario__email__in=emails).count()
        Reporte.objects.filter(usuario__email__in=emails).delete()
        RegistroResiduo.objects.filter(usuario__email__in=emails).delete()
        n_users, _ = User.objects.filter(email__in=emails).delete()
        self.stdout.write(
            self.style.WARNING(
                f'🧹 Eliminados: {n_users} usuarios, '
                f'{n_reportes} reportes, {n_residuos} registros de residuos.'
            )
        )

    def _crear_usuarios(self, lista, label):
        self.stdout.write(f'\n── Creando {label}…')
        for datos in lista:
            # Generar username desde email si no viene en los datos
            username = datos.get('username') or datos['email'].split('@')[0]
            user, creado = User.objects.get_or_create(
                email=datos['email'],
                defaults={
                    'username':   username,
                    'first_name': datos['first_name'],
                    'last_name':  datos['last_name'],
                    'municipio':  datos['municipio'],
                    'rol':        datos['rol'],
                    'is_staff':   datos.get('is_staff', False),
                    'is_active':  True,
                },
            )
            if creado:
                user.set_password(datos['password'])
                user.save()
                self.stdout.write(f'  ✔ {datos["email"]} ({datos["municipio"]})')
            else:
                self.stdout.write(f'  ⚠ Ya existe: {datos["email"]} — omitido.')

    def _crear_reportes_base(self):
        """15 reportes base distribuidos en Chía, Cajicá y Zipaquirá."""
        self.stdout.write('\n── Creando reportes base (15)…')

        ciudadanos_map = self._get_ciudadanos_map(CIUDADANOS)
        operadores_map = self._get_ciudadanos_map(OPERADORES)
        foto_existente = self._get_foto_existente()
        total = 0

        for municipio, lista in REPORTES_SEMILLA.items():
            ciudadano = ciudadanos_map.get(municipio)
            operador  = operadores_map.get(municipio)

            if not ciudadano:
                self.stdout.write(
                    self.style.WARNING(f'  ⚠ Sin ciudadano para {municipio} — saltando.')
                )
                continue

            for r in lista:
                if self._reporte_existe(r['titulo'], municipio):
                    self.stdout.write(f'  ⚠ Ya existe: "{r["titulo"]}" — omitido.')
                    continue

                reporte = Reporte(
                    usuario     = ciudadano,
                    titulo      = r['titulo'],
                    descripcion = r['descripcion'],
                    categoria   = r['categoria'],
                    latitud     = r['latitud'],
                    longitud    = r['longitud'],
                    municipio   = municipio,
                    estado      = r['estado'],
                    operador    = operador if r['estado'] in ('resuelto', 'en_gestion') else None,
                    nota_operador=(
                        'Punto intervenido por cuadrilla municipal.'
                        if r['estado'] == 'resuelto' else None
                    ),
                )
                if foto_existente:
                    reporte.foto = foto_existente
                reporte.save()

                self.stdout.write(
                    f'  ✔ [{municipio:10s}] {r["titulo"][:45]} — {r["estado"]}'
                )
                total += 1

        self.stdout.write(f'\n  📊 {total} reportes base creados.')

    def _crear_reportes_gamificacion(self):
        """
        Reportes para los tres ciudadanos especiales de gamificación:
          - reporter_activo   → 30 reportes en Chía      (activa Panoptes)
          - guardian_regional → 6 municipios distintos   (activa Telamon)
          - reciclador_fiel   → solo residuos (ver _crear_registros_residuos)
        """
        self.stdout.write('\n── Creando reportes de gamificación…')
        foto_existente = self._get_foto_existente()

        # Ciudad activo: 30 reportes
        reporter = User.objects.filter(email='reporter_activo@sabanalimpia.co').first()
        if reporter:
            total = 0
            for r in REPORTES_MUCHOS:
                if self._reporte_existe(r['titulo'], r['municipio']):
                    continue
                reporte = Reporte(
                    usuario     = reporter,
                    titulo      = r['titulo'],
                    descripcion = r['descripcion'],
                    categoria   = r['categoria'],
                    latitud     = r['latitud'],
                    longitud    = r['longitud'],
                    municipio   = r['municipio'],
                    estado      = r['estado'],
                )
                if foto_existente:
                    reporte.foto = foto_existente
                reporte.save()
                total += 1
            self.stdout.write(f'  ✔ reporter_activo: {total} reportes en Chía')

        # Guardian regional: 6 municipios distintos
        guardian = User.objects.filter(email='guardian_regional@sabanalimpia.co').first()
        if guardian:
            total = 0
            for r in REPORTES_MULTIMUNICIPIOS:
                if self._reporte_existe(r['titulo'], r['municipio']):
                    continue
                reporte = Reporte(
                    usuario     = guardian,
                    titulo      = r['titulo'],
                    descripcion = r['descripcion'],
                    categoria   = r['categoria'],
                    latitud     = r['latitud'],
                    longitud    = r['longitud'],
                    municipio   = r['municipio'],
                    estado      = r['estado'],
                )
                if foto_existente:
                    reporte.foto = foto_existente
                reporte.save()
                total += 1
            self.stdout.write(f'  ✔ guardian_regional: {total} reportes en 6 municipios')

    def _crear_registros_residuos(self):
        """
        Residuos para todos los ciudadanos:
          - Base: 4 semanas por ciudadano
          - reciclador_fiel: 8 semanas (activa Gaia Perpetua)
        """
        self.stdout.write('\n── Creando registros de residuos…')
        hoy          = date.today()
        lunes_actual = hoy - timedelta(days=hoy.weekday())

        # Ciudadanos base: 4 semanas
        for datos in CIUDADANOS:
            user = User.objects.filter(email=datos['email']).first()
            if not user:
                continue
            self._crear_semanas_residuos(user, lunes_actual, semanas=4)

        # Reciclador fiel: 8 semanas consecutivas
        reciclador = User.objects.filter(email='reciclador_fiel@sabanalimpia.co').first()
        if reciclador:
            self._crear_semanas_residuos(reciclador, lunes_actual, semanas=8)
            self.stdout.write('  ✔ reciclador_fiel: 8 semanas consecutivas')

    def _crear_semanas_residuos(self, user, lunes_actual, semanas=4):
        for i in range(semanas):
            semana = lunes_actual - timedelta(weeks=i)
            if RegistroResiduo.objects.filter(usuario=user, semana=semana).exists():
                continue
            RegistroResiduo.objects.create(
                usuario          = user,
                semana           = semana,
                municipio        = user.municipio,
                organico_kg      = round(random.uniform(1.5, 4.5), 2),
                reciclable_kg    = round(random.uniform(0.5, 2.5), 2),
                no_reciclable_kg = round(random.uniform(1.0, 3.5), 2),
                especial_kg      = round(random.uniform(0.0, 0.5), 2),
                peligroso_kg     = round(random.uniform(0.0, 0.2), 2),
            )
            self.stdout.write(f'  ✔ Residuos semana {semana} — {user.email}')

    # ── Utilidades ───────────────────────────────────────────────────────────

    def _get_ciudadanos_map(self, lista):
        """Devuelve dict municipio → User para la lista dada."""
        return {
            u.municipio: u
            for u in User.objects.filter(email__in=[d['email'] for d in lista])
        }

    def _get_foto_existente(self):
        """Reutiliza la primera foto en BD para no romper el ImageField."""
        return (
            Reporte.objects.exclude(foto='').values_list('foto', flat=True).first()
        )

    def _reporte_existe(self, titulo, municipio):
        return Reporte.objects.filter(titulo=titulo, municipio=municipio).exists()

    def _imprimir_credenciales(self):
        linea = '─' * 72
        self.stdout.write(f'\n{linea}')
        self.stdout.write('📋  CREDENCIALES DE PRUEBA')
        self.stdout.write(linea)
        filas = [
            ('Operador',   'operador_chia@sabanalimpia.co',          'Operador2025!',  'Chía'),
            ('Operador',   'operador_cajica@sabanalimpia.co',         'Operador2025!',  'Cajicá'),
            ('Operador',   'operador_zipaquira@sabanalimpia.co',      'Operador2025!',  'Zipaquirá'),
            ('Ciudadano',  'ciudadano_chia@sabanalimpia.co',          'Ciudadano2025!', 'Chía'),
            ('Ciudadano',  'ciudadano_cajica@sabanalimpia.co',        'Ciudadano2025!', 'Cajicá'),
            ('Ciudadano',  'ciudadano_zipaquira@sabanalimpia.co',     'Ciudadano2025!', 'Zipaquirá'),
            ('🎮 Reporter','reporter_activo@sabanalimpia.co',         'Test2025!',      'Chía — 30 reportes'),
            ('🎮 Recicla', 'reciclador_fiel@sabanalimpia.co',         'Test2025!',      'Cajicá — 8 semanas'),
            ('🎮 Guardian','guardian_regional@sabanalimpia.co',       'Test2025!',      'Zipaquirá — 6 muns'),
        ]
        for rol, email, pwd, nota in filas:
            self.stdout.write(f'  {rol:12s} | {email:45s} | {pwd:15s} | {nota}')
        self.stdout.write(linea)