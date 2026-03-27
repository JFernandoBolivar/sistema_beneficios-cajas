
from flask import Blueprint, render_template, request, redirect, url_for, session, send_file, make_response
import MySQLdb.cursors
from datetime import datetime
from babel.dates import format_date
from weasyprint import HTML
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from openpyxl.drawing.image import Image
import os
from io import BytesIO
from extensions import mysql
from flask import current_app as app

reportes_bp = Blueprint('reportes', __name__)


@reportes_bp.route("/listado")
def listado():
    if 'loggedin' not in session:
        return redirect(url_for('auth.login'))
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    cursor.execute('''
    SELECT d.ID, d.Time_box, d.Staff_ID, d.Observation, d.Lunch,
           personal.Cedula, personal.Code, personal.Name_Com, personal.manually, 
           personal.Location_Admin, personal.Estatus, personal.ESTADOS, personal.Location_Physical, 
           staff.Name_Com AS Registrador_Name,
           autorizados.Nombre AS Nombre_autorizado, autorizados.Cedula AS Cedula_autorizado
    FROM delivery d
    JOIN personal ON d.Data_ID = personal.Cedula 
    LEFT JOIN usuarios ON d.Staff_ID = usuarios.C_I  
    LEFT JOIN personal AS staff ON usuarios.C_I = staff.Cedula  
    LEFT JOIN autorizados ON personal.Cedula = autorizados.beneficiado 
    ''')
    registros = cursor.fetchall()
       
    cursor.execute('SELECT COUNT(*) AS total_recibido FROM delivery')
    total_recibido = cursor.fetchone()['total_recibido']
    cursor.close()
    return render_template('consultas/tabla.html', registros=registros, total_recibido=total_recibido)


@reportes_bp.route("/listado_pdf", methods=["GET", "POST"])
def listado_pdf():
    if request.method == "POST":
        filtro = request.form.get('filtro_pdf', 'dia')
        usuario = session.get('username', 'Usuario')
        fecha_actual = datetime.now().strftime('%d/%m/%Y %H:%M')
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        registros = []
        total_recibido = 0

        if filtro == 'mes':
            mes = request.form.get('mes', '')
            if not mes:
                return render_template('reportes/tabla_pdf.html', registros=[], total_recibido=0, fecha='')
            anio, mes_num = mes.split('-')
            cursor.execute('''
                SELECT d.ID, d.Time_box, d.Staff_ID, d.Observation, d.Lunch,
                       personal.Cedula, personal.Name_Com, personal.manually, 
                       personal.Location_Admin, personal.Estatus, personal.ESTADOS, personal.Location_Physical,
                       autorizados.Nombre AS Nombre_autorizado, autorizados.Cedula AS Cedula_autorizado
                FROM delivery d
                JOIN personal ON d.Data_ID = personal.Cedula
                LEFT JOIN autorizados ON personal.ID = autorizados.beneficiado
                WHERE YEAR(d.Time_box) = %s AND MONTH(d.Time_box) = %s
            ''', (anio, mes_num))
            registros = cursor.fetchall()
            cursor.execute('SELECT COUNT(*) AS total_recibido FROM delivery WHERE YEAR(Time_box) = %s AND MONTH(Time_box) = %s', (anio, mes_num))
            total_recibido = cursor.fetchone()['total_recibido']
            fecha = mes
        else:
            fecha = request.form.get('fecha', '')
            if not fecha:
                return render_template('reportes/tabla_pdf.html', registros=[], total_recibido=0, fecha='')
            cursor.execute('''
                SELECT d.ID, d.Time_box, d.Staff_ID, d.Observation, d.Lunch,
                       personal.Cedula, personal.Name_Com, personal.manually, 
                       personal.Location_Admin, personal.Estatus, personal.ESTADOS, personal.Location_Physical,
                       autorizados.Nombre AS Nombre_autorizado, autorizados.Cedula AS Cedula_autorizado
                FROM delivery d
                JOIN personal ON d.Data_ID = personal.Cedula
                LEFT JOIN autorizados ON personal.ID = autorizados.beneficiado
                WHERE DATE(d.Time_box) = %s
            ''', (fecha,))
            registros = cursor.fetchall()
            cursor.execute('SELECT COUNT(*) AS total_recibido FROM delivery WHERE DATE(Time_box) = %s', (fecha,))
            total_recibido = cursor.fetchone()['total_recibido']

        cursor.close()
        rendered = render_template('reportes/tabla_pdf.html', registros=registros, total_recibido=total_recibido, fecha=fecha,usuario=usuario,fecha_actual=fecha_actual)
        pdf = HTML(string=rendered).write_pdf()

        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'inline; filename=listado.pdf'
        return response
    else:
        return render_template('reportes/tabla_pdf.html')




@reportes_bp.route("/reporte")
def reporte():
    if 'loggedin' not in session:
        return redirect(url_for('auth.login'))

    mes = request.args.get('mes')
    anio = request.args.get('anio')

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    query = '''
        SELECT DATE(time_login) as fecha,
           SUM(CASE WHEN action LIKE 'Marco como entregado%%' AND Estatus = 1 THEN 1 ELSE 0 END) as total_activos,
           SUM(CASE WHEN action LIKE 'Marco como entregado%%' AND Estatus = 2 THEN 1 ELSE 0 END) as total_pasivos,
           SUM(CASE WHEN action LIKE 'Marco como entregado%%' AND Estatus IN (9, 11) THEN 1 ELSE 0 END) as total_comision_vencida,
           SUM(CASE WHEN action LIKE 'Marco como entregado%%' AND Estatus = 10 THEN 1 ELSE 0 END) as total_comision_vigente,
           SUM(CASE WHEN action LIKE 'Marco como entregado%%' AND typeNomina = 'JUBILADO EMPLEADO' THEN 1 ELSE 0 END) as total_jubilado_empleado,
           SUM(CASE WHEN action LIKE 'Marco como entregado%%' AND typeNomina = 'JUBILADO EXTINTA DISIP' THEN 1 ELSE 0 END) as total_jubilado_extinto_disip,
           SUM(CASE WHEN action LIKE 'Marco como entregado%%' AND typeNomina = 'JUBILADO OBRERO' THEN 1 ELSE 0 END) as total_jubilado_obrero,
           SUM(CASE WHEN action LIKE 'Marco como entregado%%' AND typeNomina = 'JUBILADO POLICIA METROPOLITANO (ADMI)' THEN 1 ELSE 0 END) as total_policia_metropolitano_admi,
           SUM(CASE WHEN action LIKE 'Marco como entregado%%' AND typeNomina = 'PENSIONADO INCAP VIUDA EXTINTA DISIP' THEN 1 ELSE 0 END) as total_pensionado_incap_viuda_extinto_disip,
           SUM(CASE WHEN action LIKE 'Marco como entregado%%' AND typeNomina = 'PENSIONADO INCAPACIDAD EMPLEADO' THEN 1 ELSE 0 END) as total_pensionado_incapacidad_empleado,
           SUM(CASE WHEN action LIKE 'Marco como entregado%%' AND typeNomina = 'PENSIONADO SOBREVIVIENTE' THEN 1 ELSE 0 END) as total_sobreviviente,
           SUM(CASE WHEN action LIKE 'Marco como entregado%%' AND typeNomina = 'PENSIONADOS MENORES EXTINTA DISIP' THEN 1 ELSE 0 END) as total_pensionado_menores_extinto_disip,
           SUM(CASE WHEN action LIKE 'Marco como entregado%%' THEN 1 ELSE 0 END) as total_entregas
        FROM user_history
    '''
    params = []
    where = ""
    if mes and anio:
        where = " WHERE MONTH(time_login) = %s AND YEAR(time_login) = %s"
        params.extend([mes, anio])
    query += where + " GROUP BY DATE(time_login)"

    if params:
        cursor.execute(query, params)
    else:
        cursor.execute(query)
    reportes = cursor.fetchall()

    apoyo_query = "SELECT DATE(Fecha) as fecha, SUM(cantidad) as total_apoyo FROM apoyo"
    apoyo_params = []
    if mes and anio:
        apoyo_query += " WHERE MONTH(Fecha) = %s AND YEAR(Fecha) = %s"
        apoyo_params.extend([mes, anio])
    apoyo_query += " GROUP BY DATE(Fecha)"
    if apoyo_params:
        cursor.execute(apoyo_query, apoyo_params)
    else:
        cursor.execute(apoyo_query)
    apoyos = cursor.fetchall()

    apoyo_dict = {str(a['fecha']): a['total_apoyo'] or 0 for a in apoyos}

    for reporte in reportes:
        fecha_str = str(reporte['fecha'])
        reporte['total_apoyo'] = apoyo_dict.get(fecha_str, 0)
        reporte['total_entregas_con_apoyo'] = reporte['total_entregas'] + reporte['total_apoyo']

    reportes = [r for r in reportes if r['total_entregas'] > 0 or r['total_apoyo'] > 0]

    total_entregas = sum(reporte['total_entregas'] for reporte in reportes)
    total_activos = sum(reporte['total_activos'] for reporte in reportes)
    total_pasivos = sum(reporte['total_pasivos'] for reporte in reportes)
    total_comision_vencida = sum(reporte['total_comision_vencida'] for reporte in reportes)
    total_comision_vigente = sum(reporte['total_comision_vigente'] for reporte in reportes)
    total_jubilado_empleado = sum(reporte['total_jubilado_empleado'] for reporte in reportes)
    total_jubilado_extinto_disip = sum(reporte['total_jubilado_extinto_disip'] for reporte in reportes)
    total_jubilado_obrero = sum(reporte['total_jubilado_obrero'] for reporte in reportes)
    total_policia_metropolitano_admi = sum(reporte['total_policia_metropolitano_admi'] for reporte in reportes)
    total_pensionado_incap_viuda_extinto_disip = sum(reporte['total_pensionado_incap_viuda_extinto_disip'] for reporte in reportes)
    total_pensionado_incapacidad_empleado = sum(reporte['total_pensionado_incapacidad_empleado'] for reporte in reportes)
    total_sobreviviente = sum(reporte['total_sobreviviente'] for reporte in reportes)
    total_pensionado_menores_extinto_disip = sum(reporte['total_pensionado_menores_extinto_disip'] for reporte in reportes) 
    total_apoyo = sum(reporte.get('total_apoyo', 0) for reporte in reportes)
    total_entregas_con_apoyo = sum(reporte['total_entregas_con_apoyo'] for reporte in reportes)
    cursor.close()

    for reporte in reportes:
        fecha = reporte['fecha']
        reporte['fecha_formateada'] = format_date(fecha, format='full', locale='es_ES')

    return render_template(
        'reportes/reporte.html',
        reportes=reportes,
        total_entregas=total_entregas,
        total_activos=total_activos,
        total_pasivos=total_pasivos,
        total_comision_vencida=total_comision_vencida,
        total_comision_vigente=total_comision_vigente,
        total_apoyo=total_apoyo,
        total_jubilado_empleado=total_jubilado_empleado,
        total_jubilado_extinto_disip=total_jubilado_extinto_disip,
        total_jubilado_obrero=total_jubilado_obrero,
        total_policia_metropolitano_admi=total_policia_metropolitano_admi,
        total_pensionado_incap_viuda_extinto_disip=total_pensionado_incap_viuda_extinto_disip,
        total_pensionado_incapacidad_empleado=total_pensionado_incapacidad_empleado,
        total_sobreviviente=total_sobreviviente,
        total_pensionado_menores_extinto_disip=total_pensionado_menores_extinto_disip,  
        total_entregas_con_apoyo=total_entregas_con_apoyo,
        mes=mes,
        anio=anio
    )


@reportes_bp.route("/reporte_pdf", methods=["GET", "POST"])
def reporte_pdf():
    usuario = session.get('username', 'Usuario')
    fecha_actual = datetime.now().strftime('%d/%m/%Y %H:%M')
    mes_raw = request.args.get('mes') 
    mes = None
    anio = None

    if mes_raw and '-' in mes_raw:
        try:
            anio, mes = mes_raw.split('-')
            mes = int(mes)
            anio = int(anio)
        except Exception:
            mes = None
            anio = None
    elif mes_raw and mes_raw.isdigit():
        mes = int(mes_raw)

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    query = '''
        SELECT DATE(time_login) as fecha,
               SUM(CASE WHEN action LIKE 'Marco como entregado%%' AND Estatus = 1 THEN 1 ELSE 0 END) as total_activos,
               SUM(CASE WHEN action LIKE 'Marco como entregado%%' AND Estatus = 2 THEN 1 ELSE 0 END) as total_pasivos,
               SUM(CASE WHEN action LIKE 'Marco como entregado%%' AND Estatus = 10 THEN 1 ELSE 0 END) as total_comision_vigente,
               SUM(CASE WHEN action LIKE 'Marco como entregado%%' AND Estatus IN (9, 11) THEN 1 ELSE 0 END) as total_comision_vencida,
               SUM(CASE WHEN action LIKE 'Marco como entregado%%' AND typeNomina = 'JUBILADO EMPLEADO' THEN 1 ELSE 0 END) as total_jubilado_empleado,
               SUM(CASE WHEN action LIKE 'Marco como entregado%%' AND typeNomina = 'JUBILADO EXTINTA DISIP' THEN 1 ELSE 0 END) as total_jubilado_extinto_disip,
               SUM(CASE WHEN action LIKE 'Marco como entregado%%' AND typeNomina = 'JUBILADO OBRERO' THEN 1 ELSE 0 END) as total_jubilado_obrero,
               SUM(CASE WHEN action LIKE 'Marco como entregado%%' AND typeNomina = 'JUBILADO POLICIA METROPOLITANO (ADMI)' THEN 1 ELSE 0 END) as total_policia_metropolitano_admi,
               SUM(CASE WHEN action LIKE 'Marco como entregado%%' AND typeNomina = 'PENSIONADO INCAP VIUDA EXTINTA DISIP' THEN 1 ELSE 0 END) as total_pensionado_incap_viuda_extinto_disip,
               SUM(CASE WHEN action LIKE 'Marco como entregado%%' AND typeNomina = 'PENSIONADO INCAPACIDAD EMPLEADO' THEN 1 ELSE 0 END) as total_pensionado_incapacidad_empleado,
               SUM(CASE WHEN action LIKE 'Marco como entregado%%' AND typeNomina = 'PENSIONADO SOBREVIVIENTE' THEN 1 ELSE 0 END) as total_sobreviviente,
               SUM(CASE WHEN action LIKE 'Marco como entregado%%' AND typeNomina = 'PENSIONADO MENOR EXTINTA DISIP' THEN 1 ELSE 0 END) as total_pensionado_menores_extinto_disip,
               SUM(CASE WHEN action LIKE 'Marco como entregado%%' THEN 1 ELSE 0 END) as total_entregas
        FROM user_history
    '''
    params = []
    if mes and anio:
        query += " WHERE MONTH(time_login) = %s AND YEAR(time_login) = %s"
        params.extend([mes, anio])
    query += " GROUP BY DATE(time_login)"

    if params:
        cursor.execute(query, params)
    else:
        cursor.execute(query)
    reportes = cursor.fetchall()

    apoyo_query = "SELECT DATE(Fecha) as fecha, SUM(cantidad) as total_apoyo FROM apoyo"
    apoyo_params = []
    if mes and anio:
        apoyo_query += " WHERE MONTH(Fecha) = %s AND YEAR(Fecha) = %s"
        apoyo_params.extend([mes, anio])
    apoyo_query += " GROUP BY DATE(Fecha)"
    if apoyo_params:
        cursor.execute(apoyo_query, apoyo_params)
    else:
        cursor.execute(apoyo_query)
    apoyos = cursor.fetchall()

    apoyo_dict = {str(a['fecha']): a['total_apoyo'] or 0 for a in apoyos}

    for reporte in reportes:
        fecha_str = str(reporte['fecha'])
        reporte['total_apoyo'] = apoyo_dict.get(fecha_str, 0)
        reporte['total_entregas_con_apoyo'] = reporte['total_entregas'] + reporte['total_apoyo']

    reportes = [r for r in reportes if r['total_entregas'] > 0 or r['total_apoyo'] > 0]

    total_entregas = sum(r['total_entregas'] for r in reportes)
    total_activos = sum(r['total_activos'] for r in reportes)
    total_pasivos = sum(r['total_pasivos'] for r in reportes)
    total_comision_vigente = sum(r['total_comision_vigente'] for r in reportes)
    total_comision_vencida = sum(r['total_comision_vencida'] for r in reportes)
    total_jubilado_empleado = sum(reporte['total_jubilado_empleado'] for reporte in reportes)
    total_jubilado_extinto_disip = sum(reporte['total_jubilado_extinto_disip'] for reporte in reportes)
    total_jubilado_obrero = sum(reporte['total_jubilado_obrero'] for reporte in reportes)
    total_policia_metropolitano_admi = sum(reporte['total_policia_metropolitano_admi'] for reporte in reportes)
    total_pensionado_incap_viuda_extinto_disip = sum(reporte['total_pensionado_incap_viuda_extinto_disip'] for reporte in reportes)
    total_pensionado_incapacidad_empleado = sum(reporte['total_pensionado_incapacidad_empleado'] for reporte in reportes)
    total_sobreviviente = sum(reporte['total_sobreviviente'] for reporte in reportes)
    total_pensionado_menores_extinto_disip = sum(reporte['total_pensionado_menores_extinto_disip'] for reporte in reportes)
    total_apoyo = sum(r.get('total_apoyo', 0) for r in reportes)
    total_entregas_con_apoyo = sum(r['total_entregas_con_apoyo'] for r in reportes)

    cursor.close()

    for reporte in reportes:
        fecha = reporte['fecha']
        reporte['fecha_formateada'] = format_date(fecha, format='full', locale='es_ES')

    rendered = render_template(
        'reportes/reporte_pdf.html',
        reportes=reportes,
        total_entregas=total_entregas,
        total_activos=total_activos,
        total_pasivos=total_pasivos,
        total_comision_vigente=total_comision_vigente,
        total_comision_vencida=total_comision_vencida,
        total_jubilado_empleado=total_jubilado_empleado,
        total_jubilado_extinto_disip=total_jubilado_extinto_disip,
        total_jubilado_obrero=total_jubilado_obrero,
        total_policia_metropolitano_admi=total_policia_metropolitano_admi,
        total_pensionado_incap_viuda_extinto_disip=total_pensionado_incap_viuda_extinto_disip,
        total_pensionado_incapacidad_empleado=total_pensionado_incapacidad_empleado,
        total_sobreviviente=total_sobreviviente,
        total_pensionado_menores_extinto_disip=total_pensionado_menores_extinto_disip, 
        total_apoyo=total_apoyo,
        total_entregas_con_apoyo=total_entregas_con_apoyo,
        usuario=usuario,
        fecha_actual=fecha_actual,
        mes=mes,
        anio=anio
    )
    pdf = HTML(string=rendered).write_pdf()

    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=reporte.pdf'
    return response


@reportes_bp.route("/nomina")
def nomina_personal():
    if 'loggedin' not in session:
        return redirect(url_for('auth.login'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM personal')
    nomina_raw = cursor.fetchall()
    cursor.close()

    tipos_vistos = set()
    nomina_filtrada = []

    for n in nomina_raw:
        if n['typeNomina'] and n['typeNomina'] not in tipos_vistos:
            tipos_vistos.add(n['typeNomina'])
            nomina_filtrada.append(n)

    return render_template(
        'db/nomina.html',
        nomina=nomina_filtrada
    )


@reportes_bp.route("/suspender_nomina/<path:typeNomina>", methods=["POST"])
def suspender_nomina(typeNomina):
    if 'loggedin' not in session:
        return redirect(url_for('auth.login'))
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('UPDATE personal SET autorizacion = %s WHERE typeNomina = %s', (False, typeNomina))
    mysql.connection.commit()
    
    cursor.execute('INSERT INTO user_history (cedula, Name_user, action, time_login) VALUES (%s, %s, %s, %s)', 
                  (session['cedula'], session['username'], f'Suspendio la entrega a la nomina {typeNomina}', datetime.now()))
    mysql.connection.commit()
    cursor.close()
    return redirect(url_for('reportes.nomina_personal'))


@reportes_bp.route("/activar_nomina/<path:typeNomina>", methods=["POST"])
def activar_nomina(typeNomina):
    if 'loggedin' not in session:
        return redirect(url_for('auth.login'))
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('UPDATE personal SET autorizacion = %s WHERE typeNomina = %s', (True, typeNomina))
    mysql.connection.commit()
    
    cursor.execute('INSERT INTO user_history (cedula, Name_user, action, time_login) VALUES (%s, %s, %s, %s)', 
                  (session['cedula'], session['username'], f'Activo la entrega a la nomina {typeNomina}', datetime.now()))
    mysql.connection.commit()
    cursor.close()
    return redirect(url_for('reportes.nomina_personal'))
