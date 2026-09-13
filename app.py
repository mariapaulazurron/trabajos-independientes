from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

# Función para obtener los usuarios de la base de datos
def fetch_users():
    conn = sqlite3.connect('mi_base_de_datos.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM usuarios')
    users = cursor.fetchall()
    conn.close()
    return users

# Función para insertar un nuevo usuario en la base de datos
def insert_user(nombre, edad, email, telefono, dni):
    conn = sqlite3.connect('mi_base_de_datos.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO usuarios (nombre, edad, email, telefono, dni) VALUES (?, ?, ?, ?, ?)', (nombre, edad, email, telefono, dni))
    conn.commit()
    conn.close()

# Ruta para la página de inicio
@app.route('/')
def index():
    return render_template('index.html')

# Ruta para el registro de usuarios
@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form['nombre']
        edad = request.form['edad']
        email = request.form['email']
        telefono = request.form['telefono']
        dni = request.form['dni']
        insert_user(nombre, edad, email, telefono, dni)  # Inserta el usuario
    return render_template('registro.html')

# Ruta para mostrar usuarios registrados
@app.route('/usuarios')
def lista_usuarios():
    usuarios = fetch_users()  # Obtiene la lista de usuarios
    return render_template('usuarios.html', usuarios=usuarios)  # Pasa los usuarios a la plantilla

# Rutas adicionales
@app.route('/inicio')
def inicio():
    return render_template('inicio.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/bancoestella')
def bancoestella():
    return render_template('Bancoestella.html')

@app.route('/bancos')
def bancos():
    return render_template('bancos.html')

@app.route('/contraseñaestella')
def contraseñaestella():
    return render_template('contraseñaestella.html')

@app.route('/contraseñaindex')
def contraseñaindex():
    return render_template('contraseñaindex.html')

@app.route('/formulario')
def formulario():
    return render_template('formulario.html')

@app.route('/operaciones')
def operaciones():
    usuario = {
        'alias': 'Usuario123',
        'caja_ahorro': '123456789',
        'cbu': '20-12345678-9',
        'saldo': ''
    }
    return render_template('operaciones.html', usuario=usuario)

if __name__ == '__main__':
    app.run(debug=True)