"""
Módulo de utilidades del sistema.
"""
from .constants import (
    ESTATUS_MAP,
    TIPO_NOMINA_CHOICES,
    ESTADOS_VENEZUELA,
    MSG_ERROR_CEDULA_INVALIDA,
    MSG_ERROR_CEDULA_DUPLICADA,
    MSG_ERROR_AUTORIZADO_DUPLICADO,
)
from .validators import (
    validar_cedula,
    sanitizar_busqueda,
    sanitizar_cedula_busqueda,
    login_required,
    limitar_resultados,
    formatear_fecha_sql,
    formatear_mes_sql,
)
