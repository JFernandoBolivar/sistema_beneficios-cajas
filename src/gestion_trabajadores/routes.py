"""
Rutas para la gestión de trabajadores/beneficiarios.
Módulo para registro de nuevos trabajadores, listado de entregas y reportes.
"""
from flask import Blueprint, render_template, request, redirect, url_for, session, make_response
import MySQLdb.cursors
from datetime import datetime
from extensions import mysql
from weasyprint import HTML
from src.utils.validators import (
    validar_cedula, sanitizar_busqueda, sanitizar_cedula_busqueda,
    formatear_fecha_sql, formatear_mes_sql, limitar_resultados
)
from src.utils.constants import (
    ESTATUS_MAP, TIPO_NOMINA_CHOICES, MSG_ERROR_CEDULA_INVALIDA,
    MSG_ERROR_CEDULA_DUPLICADA, MSG_ERROR_AUTORIZADO_DUPLICADO,
    LIMITE_MAXIMO_CONSULTAS
)

gestion_trabajadores_bp = Blueprint('gestion_trabajadores', __name__)


@gestion_trabajadores_bp.route("/reporte_personal", methods=["GET","POST"])
def reporte_personal():
    """
    Muestra el reporte de entregas de beneficios a trabajadores.
    Soporta filtros por cédula, fecha, mes, estatus y tipo de nómina.
    """
    if 'loggedin' not in session:
        return redirect(url_for('auth.login'))
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    cedula = sanitizar_busqueda(request.args.get('cedula', ''))
    fecha = formatear_fecha_sql(request.args.get('fecha', ''))
    mes_raw = request.args.get('mes', '')
    estatus = sanitizar_busqueda(request.args.get('estatus', ''))
    tipo_nomina = sanitizar_busqueda(request.args.get('tipo_nomina', ''))
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    query = '''
        SELECT * FROM user_history
        WHERE cedula_personal IS NOT NULL AND cedula_personal != ''
          AND Name_personal IS NOT NULL AND Name_personal != ''
    '''
    count_query = '''
        SELECT COUNT(*) as total FROM user_history
        WHERE cedula_personal IS NOT NULL AND cedula_personal != ''
          AND Name_personal IS NOT NULL AND Name_personal != ''
    '''
    params = []
    
    if cedula:
        query += " AND cedula_personal LIKE %s"
        count_query += " AND cedula_personal LIKE %s"
        params.append(f"%{cedula}%")
    if fecha:
        query += " AND DATE(time_login) = %s"
        count_query += " AND DATE(time_login) = %s"
        params.append(fecha)
    if mes_raw:
        anio, mes_num = formatear_mes_sql(mes_raw)
        if anio and mes_num:
            query += " AND YEAR(time_login) = %s AND MONTH(time_login) = %s"
            count_query += " AND YEAR(time_login) = %s AND MONTH(time_login) = %s"
            params.extend([anio, mes_num])
    if estatus:
        status_map = {
            'activo': 1,
            'pasivo': 2,
            'vigente': 10,
            'vencida': [9, 11]
        }
        if estatus.lower() in status_map:
            status_value = status_map[estatus.lower()]
            if isinstance(status_value, list):
                placeholders = ','.join(['%s'] * len(status_value))
                query += f" AND Estatus IN ({placeholders})"
                count_query += f" AND Estatus IN ({placeholders})"
                params.extend(status_value)
            else:
                query += " AND Estatus = %s"
                count_query += " AND Estatus = %s"
                params.append(status_value)
    if tipo_nomina:
        query += " AND typeNomina = %s"
        count_query += " AND typeNomina = %s"
        params.append(tipo_nomina)
    
    cursor.execute(count_query, params)
    total = cursor.fetchone()['total']
    
    query += " ORDER BY time_login DESC LIMIT %s OFFSET %s"
    offset = (page - 1) * per_page
    params.extend([per_page, offset])
    
    cursor.execute(query, params)
    historial = cursor.fetchall()
    cursor.close()
    
    total_pages = (total + per_page - 1) // per_page if total > 0 else 1
    
    return render_template('trabajadores/reporte_entregados.html', 
                           historial=historial,
                           cedula=cedula,
                           fecha=fecha,
                           mes=mes_raw,
                           estatus=estatus,
                           tipo_nomina=tipo_nomina,
                           page=page,
                           total_pages=total_pages,
                           total=total)


@gestion_trabajadores_bp.route("/reporte_personalPDF", methods=["GET", "POST"])
def reporte_personalPDF():
    """
    Genera PDF del reporte de entregas de beneficios.
    """
    if 'loggedin' not in session:
        return redirect(url_for('auth.login'))

    cedula = sanitizar_busqueda(request.args.get('cedula', ''))
    fecha = formatear_fecha_sql(request.args.get('fecha', ''))
    mes_raw = request.args.get('mes', '')
    estatus = sanitizar_busqueda(request.args.get('estatus', ''))
    tipo_nomina = request.args.getlist('tipo_nomina')
    usuario = session.get('username', 'Usuario')
    fecha_actual = datetime.now().strftime('%d/%m/%Y %H:%M')
     
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    query = '''
        SELECT * FROM user_history
        WHERE cedula_personal IS NOT NULL AND cedula_personal != ''
          AND Name_personal IS NOT NULL AND Name_personal != ''
    '''
    params = []

    if cedula:
        query += " AND cedula_personal LIKE %s"
        params.append(f"%{cedula}%")
    if fecha:
        query += " AND DATE(time_login) = %s"
        params.append(fecha)
    if mes_raw:
        anio, mes_num = formatear_mes_sql(mes_raw)
        if anio and mes_num:
            query += " AND YEAR(time_login) = %s AND MONTH(time_login) = %s"
            params.extend([anio, mes_num])

    if estatus:
        status_map = {
            'activo': 1,
            'pasivo': 2,
            'vigente': 10,
            'vencida': [9, 11]
        }
        if estatus.lower() in status_map:
            status_value = status_map[estatus.lower()]
            if isinstance(status_value, list):
                placeholders = ','.join(['%s'] * len(status_value))
                query += f" AND Estatus IN ({placeholders})"
                params.extend(status_value)
            else:
                query += " AND Estatus = %s"
                params.append(status_value)

    tipo_nomina_limpio = [sanitizar_busqueda(t) for t in tipo_nomina if sanitizar_busqueda(t)]
    if tipo_nomina_limpio:
        placeholders = ','.join(['%s'] * len(tipo_nomina_limpio))
        query += f" AND typeNomina IN ({placeholders})"
        params.extend(tipo_nomina_limpio)

    cursor.execute(query, params)
    historial = cursor.fetchall()
    cursor.close()

    if request.args.get('pdf') == '1':
        rendered = render_template(
            'trabajadores/reporte_entregados_pdf.html',
            historial=historial,
            cedula=cedula,
            fecha=fecha,
            mes=mes_raw,
            estatus=estatus,
            usuario=usuario,
            fecha_actual=fecha_actual
        )
        pdf = HTML(string=rendered).write_pdf()
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'inline; filename=reporte_personal.pdf'
        return response

    return render_template(
        'trabajadores/reporte_entregados_pdf.html',
        historial=historial,
        cedula=cedula,
        fecha=fecha,
        mes=mes_raw,
        estatus=estatus,
        usuario=usuario,
        fecha_actual=fecha_actual
    )


@gestion_trabajadores_bp.route("/nuevoEmpActivo", methods=["GET", "POST"])
def NuevoUserActivo():
    """
    Registra un nuevo trabajador activo en el sistema.
    Valida formato de cédula y verifica duplicados.
    """
    if 'loggedin' not in session:
        return redirect(url_for('auth.login'))
    
    if request.method == "POST":
        cedula = request.form.get('cedula', '').strip()
        nombreCompleto = sanitizar_busqueda(request.form.get('nombreCompleto', ''))
        unidadFisica = sanitizar_busqueda(request.form.get('unidadFisica', ''))
        unidadAdmin = sanitizar_busqueda(request.form.get('unidadAdmin', ''))
        observacion = sanitizar_busqueda(request.form.get('observacion', ''))
        CIFamiliar = sanitizar_cedula_busqueda(request.form.get('cedula-family', ''))
        Nombre_Familiar = sanitizar_busqueda(request.form.get('Nombre_Familiar', ''))
        CodigoCarnet = sanitizar_busqueda(request.form.get('CodigoCarnet', ''))
        
        es_valida, msg_error = validar_cedula(cedula)
        if not es_valida:
            return render_template("trabajadores/nuevo_trabajador_activo.html", error=msg_error)
        
        estatus = 1
        cedula_personal = session['cedula']
        lunch = 1 if 'lunch' in request.form else 0
        horaEntrega = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        try:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM personal WHERE Cedula = %s', (cedula,))
            existing_user = cursor.fetchone()
            
            if existing_user:
                cursor.close()
                return render_template("trabajadores/nuevo_trabajador_activo.html", error=MSG_ERROR_CEDULA_DUPLICADA)

            if CIFamiliar and Nombre_Familiar:
                cursor.execute('SELECT * FROM autorizados WHERE Cedula = %s AND beneficiado = %s', 
                             (CIFamiliar, cedula))
                if cursor.fetchone():
                    cursor.close()
                    return render_template("trabajadores/nuevo_trabajador_activo.html", error=MSG_ERROR_AUTORIZADO_DUPLICADO)

            cursor.execute('''
                INSERT INTO personal (Cedula, Name_Com, Code, Location_Physical, Location_Admin, manually, Estatus) 
                VALUES (%s, %s, %s, %s, %s, 1, %s)
            ''', (cedula, nombreCompleto, CodigoCarnet, unidadFisica, unidadAdmin, estatus))
            mysql.connection.commit()
            
            cursor.execute('''
                INSERT INTO user_history 
                (cedula, Name_user,Estatus,Observation, action, time_login) 
                VALUES (%s, %s, %s,%s, %s,%s)
            ''', (
                session['cedula'], 
                session['username'],
                estatus,
                observacion,
                f'Registro un personal activo con cédula {cedula}', 
                datetime.now()
            ))
            mysql.connection.commit()

            if CIFamiliar and Nombre_Familiar:
                cursor.execute('''
                    INSERT INTO autorizados (beneficiado, Nombre, Cedula)
                    VALUES (%s, %s, %s)
                ''', (cedula, Nombre_Familiar, CIFamiliar))
                mysql.connection.commit()

            entregado = 1 if 'entregado' in request.form else 0

            if entregado:
                cursor.execute('''
                    INSERT INTO delivery (Time_box, Data_ID, Staff_ID, Observation, Lunch) 
                    VALUES (%s, %s, %s, %s, %s)
                ''', (horaEntrega, cedula, cedula_personal, observacion, lunch))
                mysql.connection.commit()
            
                cursor.execute('''
                    INSERT INTO user_history 
                    (cedula, Name_user, cedula_personal, Name_personal,Name_autorizado, Cedula_autorizado,Estatus,Observation, action, time_login) 
                    VALUES (%s, %s, %s, %s, %s,%s, %s, %s,%s,%s)
                ''', (
                    session['cedula'], 
                    session['username'],
                    cedula,  
                    nombreCompleto, 
                    Nombre_Familiar,
                    CIFamiliar if CIFamiliar else None,
                    estatus,
                    observacion,
                    f'Marco como entregado el beneficio a {cedula}', 
                    datetime.now()
                ))
                mysql.connection.commit()
            
            cursor.close()
            return render_template("trabajadores/nuevo_trabajador_activo.html", success="Registro exitoso.")  
        except Exception as e:
            return render_template("trabajadores/nuevo_trabajador_activo.html", error=f"Error en el registro: {str(e)}")
    
    return render_template("trabajadores/nuevo_trabajador_activo.html")


@gestion_trabajadores_bp.route("/nuevoEmpPasivo", methods=["GET", "POST"])
def NuevoUserPasivo():
    """
    Registra un nuevo trabajador pasivo (jubilado/pensionado) en el sistema.
    Valida formato de cédula y verifica duplicados.
    """
    if 'loggedin' not in session:
        return redirect(url_for('auth.login'))
    
    if request.method == "POST":
        cedula = request.form.get('cedula', '').strip()
        nombreCompleto = sanitizar_busqueda(request.form.get('nombreCompleto', ''))
        observacion = sanitizar_busqueda(request.form.get('observacion', ''))
        CIFamiliar = sanitizar_cedula_busqueda(request.form.get('cedula-family', ''))
        Nombre_Familiar = sanitizar_busqueda(request.form.get('Nombre_Familiar', ''))
        CodigoCarnet = sanitizar_busqueda(request.form.get('CodigoCarnet', ''))
        type_nomina = sanitizar_busqueda(request.form.get('type_nomina', ''))
        estado = sanitizar_busqueda(request.form.get('estado', ''))
        
        es_valida, msg_error = validar_cedula(cedula)
        if not es_valida:
            return render_template("trabajadores/nuevo_trabajador_pasivo.html", error=msg_error)
        
        estatus = 2
        cedula_personal = session['cedula']
        lunch = 1 if 'lunch' in request.form else 0
        horaEntrega = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        try:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM personal WHERE Cedula = %s', (cedula,))
            existing_user = cursor.fetchone()
           
            if existing_user:
                cursor.close()
                return render_template("trabajadores/nuevo_trabajador_pasivo.html", error=MSG_ERROR_CEDULA_DUPLICADA)

            if CIFamiliar and Nombre_Familiar:
                cursor.execute('SELECT * FROM autorizados WHERE Cedula = %s AND beneficiado = %s', 
                             (CIFamiliar, cedula))
                if cursor.fetchone():
                    cursor.close()
                    return render_template("trabajadores/nuevo_trabajador_pasivo.html", error=MSG_ERROR_AUTORIZADO_DUPLICADO)

            cursor.execute('''
                INSERT INTO personal (Cedula, Name_Com, Code, manually, Estatus,autorizacion,typeNomina, ESTADOS) 
                VALUES (%s, %s, %s, 1, %s,%s,%s, %s)
            ''', (cedula, nombreCompleto, CodigoCarnet, estatus, True, type_nomina, estado))
            mysql.connection.commit()

            cursor.execute('''
                INSERT INTO user_history 
                (cedula, Name_user,Estatus,typeNomina,Observation, action, time_login) 
                VALUES (%s, %s, %s,%s, %s, %s, %s)
            ''', (
                session['cedula'], 
                session['username'],
                estatus,
                type_nomina,
                observacion,
                f'Registro un personal pasivo con cédula {cedula}', 
                datetime.now()
            ))
            mysql.connection.commit()
            
            if CIFamiliar and Nombre_Familiar:
                cursor.execute('''
                    INSERT INTO autorizados (beneficiado, Nombre, Cedula)
                    VALUES (%s, %s, %s)
                ''', (cedula, Nombre_Familiar, CIFamiliar))
                mysql.connection.commit()
            
            entregado = 1 if 'entregado' in request.form else 0

            if entregado:
                cursor.execute('''
                    INSERT INTO delivery (Time_box, Data_ID, Staff_ID, Observation, Lunch) 
                    VALUES (%s, %s, %s, %s, %s)
                ''', (horaEntrega, cedula, cedula_personal, observacion, lunch))
                mysql.connection.commit()
            
                cursor.execute('''
                    INSERT INTO user_history 
                    (cedula, Name_user, cedula_personal, Name_personal,Name_autorizado, Cedula_autorizado,Estatus,typeNomina,Observation, action, time_login) 
                    VALUES (%s, %s, %s, %s, %s, %s,%s, %s, %s,%s,%s)
                ''', (
                    session['cedula'], 
                    session['username'],
                    cedula,  
                    nombreCompleto, 
                    Nombre_Familiar,
                    CIFamiliar if CIFamiliar else None,
                    estatus,
                    type_nomina,
                    observacion,
                    f'Marco como entregado el beneficio a {cedula}', 
                    datetime.now()
                ))
                mysql.connection.commit()
            
            cursor.close()
            return render_template("trabajadores/nuevo_trabajador_pasivo.html", success="Registro exitoso.")  
        except Exception as e:
            return render_template("trabajadores/nuevo_trabajador_pasivo.html", error=f"Error en el registro: {str(e)}")
    
    return render_template("trabajadores/nuevo_trabajador_pasivo.html")


@gestion_trabajadores_bp.route("/listado_de_apoyo")
def listado_de_apoyo():
    """
    Muestra el listado de entregas de apoyo.
    """
    if 'loggedin' not in session:
        return redirect(url_for('auth.login'))
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    cedula = sanitizar_busqueda(request.args.get('cedula', ''))
    nombre = sanitizar_busqueda(request.args.get('nombre', ''))
    fecha = formatear_fecha_sql(request.args.get('fecha', ''))

    query = 'SELECT * FROM apoyo WHERE 1=1'
    params = []

    if cedula:
        query += ' AND CI_autorizado LIKE %s'
        params.append(f'%{cedula}%')

    if nombre:
        query += ' AND Nombre_autorizado LIKE %s'
        params.append(f'%{nombre}%')

    if fecha:
        query += ' AND DATE(Fecha) = %s'
        params.append(fecha)

    if not (cedula or nombre or fecha):
        query += ' ORDER BY Fecha DESC LIMIT 10'
    else:
        query += ' ORDER BY Fecha DESC LIMIT 50'

    cursor.execute(query, params)
    registros = cursor.fetchall()

    cursor.execute('SELECT IFNULL(SUM(cantidad), 0) AS total_cantidad FROM apoyo')
    total_cantidad = cursor.fetchone()['total_cantidad']

    cursor.close()
    return render_template(
        'trabajadores/listado_apoyo.html',
        registros=registros,
        total_cantidad=total_cantidad,
        cedula=cedula,
        nombre=nombre,
        fecha=fecha
    )


@gestion_trabajadores_bp.route("/listado_apoyo_pdf")
def listado_apoyo_pdf():
    """
    Genera PDF del listado de entregas de apoyo.
    """
    if 'loggedin' not in session:
        return redirect(url_for('auth.login'))
    
    mes_raw = request.args.get('mes', '')
    usuario = session.get('username', 'Usuario')
    fecha_actual = datetime.now().strftime('%d/%m/%Y %H:%M')
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    if mes_raw:
        anio, mes_num = formatear_mes_sql(mes_raw)
        if anio and mes_num:
            cursor.execute('SELECT * FROM apoyo WHERE YEAR(Fecha) = %s AND MONTH(Fecha) = %s', (anio, mes_num))
            registros = cursor.fetchall()
            cursor.execute('SELECT IFNULL(SUM(cantidad), 0) AS total_cantidad FROM apoyo WHERE YEAR(Fecha) = %s AND MONTH(Fecha) = %s', (anio, mes_num))
            total_cantidad = cursor.fetchone()['total_cantidad']
        else:
            cursor.execute('SELECT * FROM apoyo')
            registros = cursor.fetchall()
            cursor.execute('SELECT IFNULL(SUM(cantidad), 0) AS total_cantidad FROM apoyo')
            total_cantidad = cursor.fetchone()['total_cantidad']
    else:
        cursor.execute('SELECT * FROM apoyo')
        registros = cursor.fetchall()
        cursor.execute('SELECT IFNULL(SUM(cantidad), 0) AS total_cantidad FROM apoyo')
        total_cantidad = cursor.fetchone()['total_cantidad']

    cursor.close()

    rendered = render_template(
        'reportes/listado_apoyo_pdf.html',
        registros=registros,
        total_cantidad=total_cantidad,
        mes=mes_raw,
        usuario=usuario,
        fecha_actual=fecha_actual
    )
    pdf = HTML(string=rendered).write_pdf()

    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=listado_apoyo.pdf'
    return response


@gestion_trabajadores_bp.route("/listado_no_registrado")
def listado_no_registrado():
    """
    Muestra el listado de trabajadores que no han recibido el beneficio.
    Por defecto limita a 10 registros. Si hay busqueda por cedula o nombre, limita a 50.
    """
    if 'loggedin' not in session:
        return redirect(url_for('auth.login'))
    
    cedula = sanitizar_busqueda(request.args.get('cedula', ''))
    nombre = sanitizar_busqueda(request.args.get('nombre', ''))
    limite = 50 if (cedula or nombre) else 10
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    query = '''
        SELECT personal.Cedula, personal.Name_Com, 
               personal.Estatus, personal.ESTADOS, personal.Code, personal.Location_Admin, personal.typeNomina
        FROM personal
        LEFT JOIN delivery ON personal.Cedula = delivery.Data_ID
        WHERE delivery.ID IS NULL
    '''
    count_query = '''
        SELECT COUNT(*) AS total_no_entregados
        FROM personal
        LEFT JOIN delivery ON personal.Cedula = delivery.Data_ID
        WHERE delivery.ID IS NULL
    '''
    params = []
    
    if cedula:
        query += " AND personal.Cedula LIKE %s"
        count_query += " AND personal.Cedula LIKE %s"
        params.append(f"%{cedula}%")
    
    if nombre:
        query += " AND personal.Name_Com LIKE %s"
        count_query += " AND personal.Name_Com LIKE %s"
        params.append(f"%{nombre}%")
    
    query += f" ORDER BY personal.Name_Com ASC LIMIT {limite}"
    
    cursor.execute(count_query, params)
    total_no_entregados = cursor.fetchone()['total_no_entregados']
    
    cursor.execute(query, params)
    registros = cursor.fetchall()
    cursor.close()
    return render_template('trabajadores/listado_no_registrado.html', registros=registros, total_no_entregados=total_no_entregados)


@gestion_trabajadores_bp.route("/listado_no_regist_pdf", methods=["GET", "POST"])
def listado_no_regist_pdf():
    """
    Genera PDF del listado de trabajadores que no recibieron el beneficio.
    """
    filtro = sanitizar_busqueda(request.args.get('filtro', 'todos'))
    tipos_nomina = [sanitizar_busqueda(t) for t in request.args.getlist('tipo_nomina')]
    usuario = session.get('username', 'Usuario')
    fecha_actual = datetime.now().strftime('%d/%m/%Y %H:%M')
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    query = '''
        SELECT personal.Cedula, personal.Name_Com, personal.Location_Physical, 
               personal.Location_Admin, personal.Code, personal.Estatus, 
               personal.ESTADOS, personal.typeNomina
        FROM personal
        LEFT JOIN delivery ON personal.Cedula = delivery.Data_ID
        WHERE delivery.ID IS NULL
    '''
    
    filtros_estatus = {
        'activos': 'personal.Estatus = 1',
        'pasivos': 'personal.Estatus = 2',
        'fuera_pais': 'personal.Estatus = 5',
        'fallecidos': 'personal.Estatus = 6',
        'requiere_confirmacion': 'personal.Estatus = 7',
        'suspendidos_tramite': 'personal.Estatus = 3',
        'comision_vigente': 'personal.Estatus = 10',
        'comision_vencida': 'personal.Estatus = 9'
    }
    
    params = []
    
    if filtro in filtros_estatus:
        query += f' AND {filtros_estatus[filtro]}'
    
    tipos_nomina_validos = [t for t in tipos_nomina if t]
    if tipos_nomina_validos:
        placeholders = ','.join(['%s'] * len(tipos_nomina_validos))
        query += f" AND personal.typeNomina IN ({placeholders})"
        params.extend(tipos_nomina_validos)
    
    cursor.execute(query, params if params else None)
    registros = cursor.fetchall()
    
    count_query = '''
        SELECT COUNT(*) AS total_no_entregados
        FROM personal
        LEFT JOIN delivery ON personal.Cedula = delivery.Data_ID
        WHERE delivery.ID IS NULL
    '''
    
    count_params = []
    
    if filtro in filtros_estatus:
        count_query += f' AND {filtros_estatus[filtro]}'
    
    if tipos_nomina_validos:
        placeholders = ','.join(['%s'] * len(tipos_nomina_validos))
        count_query += f" AND personal.typeNomina IN ({placeholders})"
        count_params.extend(tipos_nomina_validos)
    
    cursor.execute(count_query, count_params if count_params else None)
    total_no_entregados = cursor.fetchone()['total_no_entregados']
    cursor.close()
    
    rendered = render_template(
        'reportes/reporte_no_entregados_pdf.html',
        registros=registros,
        total_no_entregados=total_no_entregados,
        filtro=filtro,
        tipo_nomina_seleccionados=tipos_nomina_validos,
        usuario=usuario,
        fecha_actual=fecha_actual
    )
    
    pdf = HTML(string=rendered).write_pdf()
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=listado.pdf'
    return response
