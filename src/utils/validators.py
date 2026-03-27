"""
Utilidades de validación y sanitización.
"""
import re
from functools import wraps
from flask import session, redirect, url_for, request
from src.utils.constants import (
    REGEX_CEDULA, MIN_CEDULA_LENGTH, MAX_CEDULA_LENGTH,
 LIMITE_MAXIMO_CONSULTAS
)


def validar_cedula(cedula):
    """
    Valida que la cédula tenga el formato venezolano (V/E + 7-8 dígitos).
    
    Args:
        cedula: String con la cédula a validar
        
    Returns:
        tuple: (bool, str) - (es_válida, mensaje_error)
    """
    if not cedula:
        return False
    
    cedula = cedula.strip()
    
    if not re.match(REGEX_CEDULA, cedula):
        return False
    
    return True, ""


def sanitizar_busqueda(texto):
    """
    Sanitiza texto de búsqueda para prevenir SQL injection básico.
    Elimina caracteres peligrosos y recorta espacios.
    
    Args:
        texto: String a sanitizar
        
    Returns:
        str: Texto sanitizado
    """
    if not texto:
        return ""
    
    texto = texto.strip()
    
    caracteres_peligrosos = ["'", '"', ';', '--', '/*', '*/', 'xp_', 'sp_', 'exec', 'execute']
    texto_lower = texto.lower()
    
    for char in caracteres_peligrosos:
        if char in texto_lower:
            return ""
    
    return texto


def sanitizar_cedula_busqueda(cedula):
    """
    Sanitiza cédula para búsqueda, permitiendo solo números y letras V/E.
    
    Args:
        cedula: String con la cédula
        
    Returns:
        str: Cédula sanitizada o string vacío si es inválida
    """
    if not cedula:
        return ""
    
    cedula = cedula.strip().upper()
    
    resultado = re.sub(r'[ 0-9]', '', cedula)
    
    return resultado


def login_required(f):
    """
    Decorador para verificar que el usuario esté autenticado.
    Redirige a login si no hay sesión activa.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'loggedin' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def limitar_resultados(limite_param, limite_maximo=LIMITE_MAXIMO_CONSULTAS):
    """
    Limita el número de resultados permitidos.
    
    Args:
        limite_param: Límite solicitado por el usuario
        limite_maximo: Límite máximo permitido
        
    Returns:
        int: Límite a usar (entre 1 y limite_maximo)
    """
    try:
        limite = int(limite_param)
        if limite < 1:
            return limite_maximo
        return min(limite, limite_maximo)
    except (TypeError, ValueError):
        return limite_maximo


def formatear_fecha_sql(fecha):
    """
    Valida y formatea fecha para consultas SQL.
    
    Args:
        fecha: String en formato YYYY-MM-DD
        
    Returns:
        str: Fecha formateada o empty string si es inválida
    """
    if not fecha:
        return ""
    
    fecha = fecha.strip()
    
    if re.match(r'^\d{4}-\d{2}-\d{2}$', fecha):
        return fecha
    
    return ""


def formatear_mes_sql(mes):
    """
    Valida y formatea mes para consultas SQL.
    
    Args:
        mes: String en formato YYYY-MM
        
    Returns:
        tuple: (año, mes) o (None, None) si es inválido
    """
    if not mes:
        return None, None
    
    mes = mes.strip()
    
    if re.match(r'^\d{4}-\d{2}$', mes):
        partes = mes.split('-')
        return partes[0], partes[1]
    
    return None, None
