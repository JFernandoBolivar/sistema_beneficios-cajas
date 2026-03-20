"""
Constantes del sistema de beneficios.
Contiene definiciones de estatus, tipos de nómina y configuraciones.
"""

ESTATUS_CHOICES = [
    (1, 'Activo'),
    (2, 'Pasivo'),
    (3, 'Suspendido por trámites'),
    (4, 'Suspendido'),
    (5, 'Fuera del país'),
    (6, 'Fallecido'),
    (7, 'Requiere confirmación'),
    (8, 'Requiere verificar'),
    (9, 'Comisión de Servicio Vencida'),
    (10, 'Comisión de Servicio Vigente'),
    (11, 'Comisión Vencida'),
]

ESTATUS_MAP = {
    1: 'Activo',
    2: 'Pasivo',
    3: 'Suspendido por trámites administrativos',
    4: 'Suspendido',
    5: 'Fuera del país',
    6: 'Fallecido',
    7: 'Se requiere confirmación',
    8: 'Se requiere verificar',
    9: 'Comisión de Servicio Vencida',
    10: 'Comisión de Servicio Vigente',
    11: 'Comisión Vencida',
}

TIPO_NOMINA_CHOICES = [
    'JUBILADO EMPLEADO',
    'JUBILADO EXTINTA DISIP',
    'JUBILADO OBRERO',
    'JUBILADO POLICIA METROPOLITANO (ADMI)',
    'PENSIONADO INCAP/VIUDA EXTINTA DISIP',
    'PENSIONADO INCAPACIDAD EMPLEADO',
    'PENSIONADO SOBREVIVIENTE',
    'PENSIONADOS MENORES EXTINTA DISIP',
]

ESTADOS_VENEZUELA = [
    'DISTRITO CAPITAL', 'AMAZONAS', 'ANZOÁTEGUI', 'APURE', 'ARAGUA',
    'BARINAS', 'BOLÍVAR', 'CARABOBO', 'COJEDES', 'DELTA AMACURO',
    'FALCÓN', 'GUÁRICO', 'LARA', 'MÉRIDA', 'MIRANDA', 'MONAGAS',
    'NUEVA ESPARTA', 'PORTUGUESA', 'SUCRE', 'TÁCHIRA', 'TRUJILLO',
    'VARGAS', 'YARACUY', 'ZULIA'
]

LIMITE_RESULTADOS_PAGINA = 50
LIMITE_RESULTADOS_POR_DEFECTO = 10
LIMITE_MAXIMO_CONSULTAS = 500

REGEX_CEDULA = r'^[VEve][0-9]{7,8}$'
MIN_CEDULA_LENGTH = 7
MAX_CEDULA_LENGTH = 8

MSG_ERROR_CEDULA_INVALIDA = 'La cédula debe tener el formato V12345678 o E12345678'
MSG_ERROR_CEDULA_DUPLICADA = 'Esta cédula ya está registrada'
MSG_ERROR_AUTORIZADO_DUPLICADO = 'Este autorizado ya está registrado para este beneficiario'
