import sqlite3

def connect_to_database():
    """Conectar a la base de datos (se crea si no existe)."""
    conn = sqlite3.connect('mi_base_de_datos.db')
    return conn

def create_table():
    """Crear la tabla de usuarios si no existe."""
    conn = connect_to_database()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            email TEXT NOT NULL,
            contraseña TEXT NOT NULL,
            telefono TEXT NOT NULL,
            direccion TEXT NOT NULL,
            fecha_nacimiento TEXT NOT NULL,
            dni TEXT NOT NULL
        )
    ''')
    
    conn.commit()
    conn.close()

def insert_user(nombre, email, contraseña, telefono, direccion, fecha_nacimiento, dni):
    """Insertar un nuevo usuario en la base de datos."""
    conn = connect_to_database()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO usuarios (nombre, email, contraseña, telefono, direccion, fecha_nacimiento, dni)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (nombre, email, contraseña, telefono, direccion, fecha_nacimiento, dni))
    
    conn.commit()
    conn.close()

def fetch_users():
    """Obtener todos los usuarios de la base de datos."""
    conn = connect_to_database()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM usuarios')
    users = cursor.fetchall()
    
    conn.close()
    return users