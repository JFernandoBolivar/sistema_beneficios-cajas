from flask import Blueprint, render_template, request, redirect, url_for, session,make_response,flash
import MySQLdb.cursors
from datetime import datetime
from extensions import mysql
from weasyprint import HTML
import bcrypt
from src.utils.validators import sanitizar_busqueda

gestion_usuarios_bp = Blueprint('gestion_usuarios', __name__)


@gestion_usuarios_bp.route("/usuarios", methods=["GET"])
def usuarios():
    if 'loggedin' not in session:
        return redirect(url_for('auth.login'))
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    cedula = sanitizar_busqueda(request.args.get('cedula', ''))
    nombre = sanitizar_busqueda(request.args.get('nombre', ''))
    
    query = '''
        SELECT usuarios.C_I AS Cedula, COALESCE(personal.Name_Com, usuarios.username) AS Name_Com, 
               usuarios.username, personal.Location_Physical, personal.Location_Admin, usuarios.estado
        FROM usuarios
        LEFT JOIN personal ON usuarios.C_I = personal.Cedula
        WHERE 1=1
    '''
    params = []
    
    if cedula:
        query += ' AND usuarios.C_I LIKE %s'
        params.append(f'%{cedula}%')
    
    if nombre:
        query += ' AND COALESCE(personal.Name_Com, usuarios.username) LIKE %s'
        params.append(f'%{nombre}%')
    
    if not (cedula or nombre):
        query += ' ORDER BY COALESCE(personal.Name_Com, usuarios.username) ASC LIMIT 10'
    else:
        query += ' ORDER BY COALESCE(personal.Name_Com, usuarios.username) ASC LIMIT 50'
    
    cursor.execute(query, params if params else None)
    usuarios = cursor.fetchall()
    cursor.close()
    return render_template('usuarios/usuarios.html', usuarios=usuarios, cedula=cedula, nombre=nombre)


@gestion_usuarios_bp.route("/editar_usuario/<int:cedula>", methods=["GET", "POST"])
def editar_usuario(cedula):
    if 'loggedin' not in session:
        return redirect(url_for('auth.login'))
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password'].strip()
      
        
        if password:
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            cursor.execute('''
                UPDATE usuarios
                SET username = %s, Password = %s
                WHERE C_I = %s
            ''', (username, hashed_password, cedula))
        else:
            cursor.execute('''
                UPDATE usuarios
                SET username = %s
                WHERE C_I = %s
            ''', (username, cedula))
        
        
        mysql.connection.commit()
        cursor.close()
        flash("Usuario actualizado correctamente.", "success")
        return redirect(url_for('consultas.consult'))
    
    cursor.execute('''
        SELECT usuarios.C_I AS Cedula, personal.Name_Com, usuarios.username, 
               personal.Location_Physical, usuarios.Password, usuarios.estado
        FROM usuarios
        LEFT JOIN personal ON usuarios.C_I = personal.Cedula
        WHERE usuarios.C_I = %s
    ''', (cedula,))
    usuario = cursor.fetchone()
    cursor.close()
    
    return render_template('usuarios/editar_usuario.html', usuario=usuario)


@gestion_usuarios_bp.route("/suspender_usuario/<int:cedula>", methods=["POST"])
def suspender_usuario(cedula):
    if 'loggedin' not in session:
        return redirect(url_for('auth.login'))
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('UPDATE usuarios SET estado = %s WHERE C_I = %s', ('suspendido', cedula))
    mysql.connection.commit()
    
    cursor.execute('INSERT INTO user_history (cedula, Name_user, action, time_login) VALUES (%s, %s, %s, %s)', 
                  (session['cedula'], session['username'], f'Suspendio el usuario {cedula}', datetime.now()))
    mysql.connection.commit()
    cursor.close()
    return redirect(url_for('gestion_usuarios.usuarios'))


@gestion_usuarios_bp.route("/reactivar_usuario/<int:cedula>", methods=["POST"])
def reactivar_usuario(cedula):
    if 'loggedin' not in session:
        return redirect(url_for('auth.login'))
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('UPDATE usuarios SET estado = %s WHERE C_I = %s', ('activo', cedula))
    mysql.connection.commit()
    cursor.execute('INSERT INTO user_history (cedula, Name_user, action, time_login) VALUES (%s, %s, %s, %s)', 
                  (session['cedula'], session['username'], f'Reactivo el usuario {cedula}', datetime.now()))
    mysql.connection.commit()
    cursor.close()
    return redirect(url_for('gestion_usuarios.usuarios'))


@gestion_usuarios_bp.route("/reporte_usuarios", methods=["GET","POST"])
def reporte_usuarios():
    if 'loggedin' not in session:
        return redirect(url_for('auth.login'))
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    cedula = request.args.get('cedula', '').strip()
    fecha = request.args.get('fecha', '').strip()
    nombre = request.args.get('nombre', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    query = 'SELECT * FROM user_history WHERE 1=1'
    count_query = 'SELECT COUNT(*) as total FROM user_history WHERE 1=1'
    params = []
    
    if cedula:
        query += " AND cedula LIKE %s"
        count_query += " AND cedula LIKE %s"
        params.append(f"%{cedula}%")
    if fecha:
        query += " AND DATE(time_login) = %s"
        count_query += " AND DATE(time_login) = %s"
        params.append(fecha)
    if nombre:
        query += " AND Name_user LIKE %s"
        count_query += " AND Name_user LIKE %s"
        params.append(f"%{nombre}%")
    
    cursor.execute(count_query, params)
    total = cursor.fetchone()['total']
    
    query += " ORDER BY time_login DESC LIMIT %s OFFSET %s"
    offset = (page - 1) * per_page
    params.extend([per_page, offset])
    
    cursor.execute(query, params)
    historial = cursor.fetchall()
    cursor.close()
    
    total_pages = (total + per_page - 1) // per_page if total > 0 else 1
    
    return render_template('usuarios/reporte_usuarios.html', 
                           historial=historial,
                           cedula=cedula,
                           fecha=fecha,
                           nombre=nombre,
                           page=page,
                           total_pages=total_pages,
                           total=total)
