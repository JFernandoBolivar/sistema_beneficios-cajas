from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify, flash, make_response
import MySQLdb.cursors
from datetime import datetime
from babel.dates import format_date
from weasyprint import HTML
from extensions import mysql
from src.utils.validators import sanitizar_busqueda
from src.utils.constants import LIMITE_MAXIMO_CONSULTAS

gestion_autorizados_bp = Blueprint('gestion_autorizados', __name__)

@gestion_autorizados_bp.route("/listado_autorizados", methods=["GET"])
def listado_autorizados():
    if 'loggedin' not in session:
        return redirect(url_for('auth.login'))
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    cedula_beneficiario = sanitizar_busqueda(request.args.get('cedula_beneficiario', ''))
    nombre_beneficiario = sanitizar_busqueda(request.args.get('nombre_beneficiario', ''))
    cedula_autorizado = sanitizar_busqueda(request.args.get('cedula_autorizado', ''))
    
    query = '''
        SELECT 
            p.Cedula AS Beneficiario_Cedula,
            p.Name_Com AS Beneficiario_Nombre,
            a.Cedula AS Autorizado_Cedula,
            a.Nombre AS Autorizado_Nombre
        FROM autorizados a
        JOIN personal p ON a.beneficiado = p.Cedula
        WHERE 1=1
    '''
    params = []
    
    if cedula_beneficiario:
        query += ' AND p.Cedula LIKE %s'
        params.append(f'%{cedula_beneficiario}%')
    
    if nombre_beneficiario:
        query += ' AND p.Name_Com LIKE %s'
        params.append(f'%{nombre_beneficiario}%')
    
    if cedula_autorizado:
        query += ' AND a.Cedula LIKE %s'
        params.append(f'%{cedula_autorizado}%')
    
    if not (cedula_beneficiario or nombre_beneficiario or cedula_autorizado):
        query += ' LIMIT 10'
    else:
        query += ' LIMIT 50'
    
    cursor.execute(query, params if params else None)
    registros = cursor.fetchall()
    
    cursor.execute('SELECT COUNT(*) AS total FROM autorizados')
    total_autorizados = cursor.fetchone()['total']
    cursor.close()
    
    return render_template('autorizados/listado_autorizados.html', 
                          registros=registros,
                          total_autorizados=total_autorizados,
                          cedula_beneficiario=cedula_beneficiario,
                          nombre_beneficiario=nombre_beneficiario,
                          cedula_autorizado=cedula_autorizado)

@gestion_autorizados_bp.route("/editar_autorizado/<int:beneficiado_cedula>", methods=["GET", "POST"])
def editar_autorizado(beneficiado_cedula):
    if 'loggedin' not in session:
        return redirect(url_for('auth.login'))
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    if request.method == "POST":
        nuevo_nombre = request.form['nuevo_nombre'].strip()
        nueva_cedula = request.form['nueva_cedula'].strip()
        
        # Actualizar el autorizado
        cursor.execute('''
            UPDATE autorizados
            SET Nombre = %s, Cedula = %s
            WHERE beneficiado = %s
        ''', (nuevo_nombre, nueva_cedula, beneficiado_cedula))
        
        mysql.connection.commit()
        cursor.close()
        return redirect(url_for('gestion_autorizados.listado_autorizados'))
    
    # Obtener el beneficiario y su autorizado
    cursor.execute('''
        SELECT 
            p.Cedula AS Beneficiario_Cedula,
            p.Name_Com AS Beneficiario_Nombre,
            a.Cedula AS Autorizado_Cedula,
            a.Nombre AS Autorizado_Nombre
        FROM personal p
        JOIN autorizados a ON p.Cedula = a.beneficiado
        WHERE a.beneficiado = %s
    ''', (beneficiado_cedula,))
    
    registro = cursor.fetchone()
    cursor.close()
    
    if not registro:
        flash("No se encontró el autorizado", "danger")
        return redirect(url_for('gestion_autorizados.listado_autorizados'))
    
    return render_template('autorizados/editar_autorizado.html', registro=registro)

@gestion_autorizados_bp.route("/reporte_entregas_usuario", methods=["GET", "POST"])
def reporte_entregas_usuario():
    if 'loggedin' not in session:
        return redirect(url_for('auth.login'))
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    cedula = sanitizar_busqueda(request.args.get('cedula', ''))
    nombre = sanitizar_busqueda(request.args.get('nombre', ''))
    fecha = sanitizar_busqueda(request.args.get('fecha', ''))
    
    query = '''
        SELECT 
            u.C_I AS Staff_ID, 
            DATE(d.Time_box) as fecha, 
            COUNT(*) as total_entregas,
            p.Name_Com AS staff_name
        FROM delivery d
        LEFT JOIN usuarios u ON d.Staff_ID = u.C_I
        LEFT JOIN personal p ON u.C_I = p.Cedula
        WHERE 1=1
    '''
    params = []
    
    if cedula:
        query += ' AND u.C_I LIKE %s'
        params.append(f'%{cedula}%')
    
    if nombre:
        query += ' AND p.Name_Com LIKE %s'
        params.append(f'%{nombre}%')
    
    if fecha:
        query += ' AND DATE(d.Time_box) = %s'
        params.append(fecha)
    
    query += ' GROUP BY u.C_I, DATE(d.Time_box)'
    
    if not (cedula or nombre or fecha):
        query += ' ORDER BY fecha DESC LIMIT 10'
    else:
        query += ' ORDER BY fecha DESC LIMIT 50'
    
    cursor.execute(query, params if params else None)
    reportes = cursor.fetchall()
    cursor.close()
    
    for reporte in reportes:
        reporte['fecha_formateada'] = format_date(reporte['fecha'], format='full', locale='es_ES')
    
    return render_template('autorizados/reporte_entregas_usuario.html', 
                         reportes=reportes,
                         cedula=cedula,
                         nombre=nombre,
                         fecha=fecha)

@gestion_autorizados_bp.route("/reporte_entregas_usuario_pdf", methods=["GET", "POST"])
def reporte_entregas_usuario_pdf():
    if 'loggedin' not in session:
        return redirect(url_for('auth.login'))
    
    fecha = request.form.get('fecha', None)
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    if fecha:
        cursor.execute('''
            SELECT 
                u.C_I AS Staff_ID, 
                DATE(d.Time_box) as fecha, 
                COUNT(*) as total_entregas,
                p.Name_Com AS staff_name
            FROM delivery d
            LEFT JOIN usuarios u ON d.Staff_ID = u.C_I
            LEFT JOIN personal p ON u.C_I = p.Cedula
            WHERE DATE(d.Time_box) = %s
            GROUP BY u.C_I, DATE(d.Time_box)
        ''', (fecha,))
    else:
        cursor.execute('''
            SELECT 
                u.C_I AS Staff_ID, 
                DATE(d.Time_box) as fecha, 
                COUNT(*) as total_entregas,
                p.Name_Com AS staff_name
            FROM delivery d
            LEFT JOIN usuarios u ON d.Staff_ID = u.C_I
            LEFT JOIN personal p ON u.C_I = p.Cedula
            GROUP BY u.C_I, DATE(d.Time_box)
        ''')
    
    reportes = cursor.fetchall()
    cursor.close()
    
    dias = {
        'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miércoles',
        'Thursday': 'Jueves', 'Friday': 'Viernes', 'Saturday': 'Sábado',
        'Sunday': 'Domingo'
    }
    meses = {
        'January': 'enero', 'February': 'febrero', 'March': 'marzo',
        'April': 'abril', 'May': 'mayo', 'June': 'junio',
        'July': 'julio', 'August': 'agosto', 'September': 'septiembre',
        'October': 'octubre', 'November': 'noviembre', 'December': 'diciembre'
    }
    
    for reporte in reportes:
        fecha_rep = reporte['fecha']
        fecha_str = fecha_rep.strftime('%A, %d de %B de %Y')
        
        for eng, esp in dias.items():
            fecha_str = fecha_str.replace(eng, esp)
        for eng, esp in meses.items():
            fecha_str = fecha_str.replace(eng, esp)
        
        reporte['fecha_formateada'] = fecha_str
    
    usuario = session.get('username', 'Usuario')
    fecha_actual = datetime.now().strftime('%d/%m/%Y %H:%M')
    
    if request.args.get('pdf') == '1':
        rendered = render_template(
            'autorizados/reporte_entregas_usuario_pdf.html',
            reportes=reportes,
            fecha=fecha,
            usuario=usuario,
            fecha_actual=fecha_actual
        )
        pdf = HTML(string=rendered).write_pdf()
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'inline; filename=reporte_entregas_usuario.pdf'
        return response
    
    return render_template('autorizados/reporte_entregas_usuario.html', reportes=reportes, fecha=fecha)