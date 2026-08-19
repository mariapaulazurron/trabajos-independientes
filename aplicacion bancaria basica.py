import os
import sqlite3
from datetime import datetime
from tkinter import *
from tkinter import messagebox, ttk

NOMBRE_BD = "BD_BancoDB.db"
cliente_seleccionado_dni = None


def reiniciar_y_conectar_bd():
    """Elimina la BD vieja si existe y crea una nueva desde cero con la columna TIPO."""
    try:
        # Si la base de datos actual no tiene la estructura correcta, la borramos para crear una limpia
        conexion = sqlite3.connect(NOMBRE_BD)
        cursor = conexion.cursor()

        # Verificar si la columna TIPO existe
        cursor.execute("PRAGMA table_info(MOVIMIENTOS)")
        columnas = [col[1] for col in cursor.fetchall()]
        conexion.close()

        if "TIPO" not in columnas and os.path.exists(NOMBRE_BD):
            os.remove(NOMBRE_BD)
    except Exception:
        pass

    try:
        conexion = sqlite3.connect(NOMBRE_BD)
        cursor = conexion.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS CLIENTES (
                DNI_ID INTEGER PRIMARY KEY,
                NOMBRE VARCHAR(50),
                APELLIDO VARCHAR(50),
                EMAIL VARCHAR(100),
                DIRECCION VARCHAR(100),
                NUM_CUENTA VARCHAR(30),
                ALIAS VARCHAR(50)
            )
        """
        )

        # Nueva tabla de movimientos con la columna TIPO incluida explícitamente
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS MOVIMIENTOS (
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                DNI_ID INTEGER,
                TIPO VARCHAR(20),
                MONTO REAL,
                FECHA VARCHAR(30),
                FOREIGN KEY (DNI_ID) REFERENCES CLIENTES(DNI_ID)
            )
        """
        )

        conexion.commit()
        conexion.close()
        mostrar_clientes()
    except Exception as e:
        messagebox.showerror(
            "Error BD", f"Error al inicializar la base de datos: {e}"
        )


def calcular_saldo(dni):
    """Suma depósitos y resta retiros para un DNI."""
    try:
        conexion = sqlite3.connect(NOMBRE_BD)
        cursor = conexion.cursor()

        cursor.execute(
            "SELECT SUM(MONTO) FROM MOVIMIENTOS WHERE DNI_ID=? AND TIPO='Depósito'",
            (int(dni),),
        )
        res_dep = cursor.fetchone()[0]
        depositos = res_dep if res_dep is not None else 0.0

        cursor.execute(
            "SELECT SUM(MONTO) FROM MOVIMIENTOS WHERE DNI_ID=? AND TIPO='Retiro'",
            (int(dni),),
        )
        res_ret = cursor.fetchone()[0]
        retiros = res_ret if res_ret is not None else 0.0

        conexion.close()
        return depositos - retiros
    except Exception:
        return 0.0


def seleccionar_cliente(event=None):
    """Selecciona un cliente de la tabla y carga sus datos."""
    global cliente_seleccionado_dni
    try:
        seleccion = tabla_clientes.selection()
        if not seleccion:
            return

        item = tabla_clientes.item(seleccion[0])
        valores = item.get("values", [])

        if not valores:
            return

        cliente_seleccionado_dni = int(valores[0])
        nombre_completo = f"{valores[1]} {valores[2]}"

        cuadroID.delete(0, END)
        cuadroNombre.delete(0, END)
        cuadroApellido.delete(0, END)
        cuadroEmail.delete(0, END)
        cuadroDireccion.delete(0, END)
        cuadroNumCuenta.delete(0, END)
        cuadroAlias.delete(0, END)

        cuadroID.insert(0, str(valores[0]))
        cuadroNombre.insert(0, str(valores[1]))
        cuadroApellido.insert(0, str(valores[2]))
        cuadroEmail.insert(0, str(valores[3]))
        cuadroDireccion.insert(0, str(valores[4]))
        cuadroNumCuenta.insert(0, str(valores[5]))
        cuadroAlias.insert(0, str(valores[6]))

        lbl_cliente_activo.config(
            text=f"{nombre_completo} (DNI: {cliente_seleccionado_dni})",
            fg="#0d47a1",
        )

        saldo = calcular_saldo(cliente_seleccionado_dni)
        lbl_saldo_var.set(f"${saldo:.2f}")
        mostrar_historial_movimientos(cliente_seleccionado_dni)
    except Exception as e:
        print(f"Error al seleccionar cliente: {e}")


def registrar_movimiento():
    """Registra la transacción usando la nueva estructura con la columna TIPO."""
    global cliente_seleccionado_dni

    if cliente_seleccionado_dni is None:
        messagebox.showwarning(
            "Selección requerida",
            "Por favor haga clic en un cliente de la tabla superior.",
        )
        return

    dni = cliente_seleccionado_dni
    tipo = comboTipoMov.get()
    monto_str = cuadroMonto.get().strip()

    try:
        monto = float(monto_str.replace(",", "."))
        if monto <= 0:
            raise ValueError
    except ValueError:
        messagebox.showwarning(
            "Monto inválido", "Ingrese un monto numérico mayor a $0."
        )
        return

    if tipo == "Retiro":
        saldo_actual = calcular_saldo(dni)
        if monto > saldo_actual:
            messagebox.showerror(
                "Saldo Insuficiente",
                f"Fondos insuficientes.\nSaldo actual: ${saldo_actual:.2f}",
            )
            return

    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        conexion = sqlite3.connect(NOMBRE_BD)
        cursor = conexion.cursor()
        cursor.execute(
            """
            INSERT INTO MOVIMIENTOS (DNI_ID, TIPO, MONTO, FECHA)
            VALUES (?, ?, ?, ?)
        """,
            (int(dni), str(tipo), float(monto), str(fecha_actual)),
        )
        conexion.commit()
        conexion.close()

        messagebox.showinfo(
            "Éxito", f"{tipo} de ${monto:.2f} realizado correctamente."
        )
        cuadroMonto.delete(0, END)

        actualizar_pantalla_cliente(dni)
    except Exception as e:
        messagebox.showerror("Error BD", f"Error al guardar movimiento: {e}")


def alta_o_modificacion():
    """Registra un nuevo cliente o actualiza los datos."""
    dni_str = cuadroID.get().strip()
    nombre = cuadroNombre.get().strip()
    apellido = cuadroApellido.get().strip()
    email = cuadroEmail.get().strip()
    direccion = cuadroDireccion.get().strip()
    num_cuenta = cuadroNumCuenta.get().strip()
    alias = cuadroAlias.get().strip()

    if not dni_str or not nombre or not apellido:
        messagebox.showwarning(
            "Campos vacíos", "Complete al menos DNI, Nombre y Apellido."
        )
        return

    if not dni_str.isdigit():
        messagebox.showwarning("DNI Inválido", "El DNI debe ser numérico.")
        return

    dni = int(dni_str)

    try:
        conexion = sqlite3.connect(NOMBRE_BD)
        cursor = conexion.cursor()
        cursor.execute("SELECT * FROM CLIENTES WHERE DNI_ID=?", (dni,))

        if cursor.fetchone():
            cursor.execute(
                """
                UPDATE CLIENTES SET NOMBRE=?, APELLIDO=?, EMAIL=?, DIRECCION=?, NUM_CUENTA=?, ALIAS=?
                WHERE DNI_ID=?
            """,
                (nombre, apellido, email, direccion, num_cuenta, alias, dni),
            )
            messagebox.showinfo("Actualizado", f"Cliente DNI {dni} modificado.")
        else:
            cursor.execute(
                "INSERT INTO CLIENTES VALUES (?, ?, ?, ?, ?, ?, ?)",
                (dni, nombre, apellido, email, direccion, num_cuenta, alias),
            )
            messagebox.showinfo("Guardado", f"Cliente DNI {dni} registrado.")

        conexion.commit()
        conexion.close()
        limpiar_campos()
    except Exception as e:
        messagebox.showerror("Error BD", f"Error al guardar cliente: {e}")


def mostrar_clientes():
    """Visualiza la lista de clientes."""
    for fila in tabla_clientes.get_children():
        tabla_clientes.delete(fila)

    try:
        conexion = sqlite3.connect(NOMBRE_BD)
        cursor = conexion.cursor()
        cursor.execute("SELECT * FROM CLIENTES ORDER BY DNI_ID ASC")
        registros = cursor.fetchall()
        conexion.close()

        for fila in registros:
            saldo = calcular_saldo(fila[0])
            tabla_clientes.insert(
                "",
                END,
                values=(
                    fila[0],
                    fila[1],
                    fila[2],
                    fila[3],
                    fila[4],
                    fila[5],
                    fila[6],
                    f"${saldo:.2f}",
                ),
            )
    except Exception as e:
        print(f"Error al cargar clientes: {e}")


def mostrar_historial_movimientos(dni):
    """Muestra el historial incluyendo la columna TIPO."""
    for fila in tabla_movimientos.get_children():
        tabla_movimientos.delete(fila)

    try:
        conexion = sqlite3.connect(NOMBRE_BD)
        cursor = conexion.cursor()
        cursor.execute(
            "SELECT ID, TIPO, MONTO, FECHA FROM MOVIMIENTOS WHERE DNI_ID=? ORDER BY ID DESC",
            (int(dni),),
        )
        registros = cursor.fetchall()
        conexion.close()

        for fila in registros:
            tabla_movimientos.insert(
                "",
                END,
                values=(
                    fila[0],
                    fila[1],
                    f"${float(fila[2]):.2f}",
                    fila[3],
                ),
            )
    except Exception as e:
        print(f"Error al cargar historial: {e}")


def actualizar_pantalla_cliente(dni):
    """Actualiza la pantalla manteniendo al cliente activo."""
    saldo = calcular_saldo(dni)
    lbl_saldo_var.set(f"${saldo:.2f}")
    mostrar_historial_movimientos(dni)

    tabla_clientes.unbind("<<TreeviewSelect>>")
    mostrar_clientes()

    for item in tabla_clientes.get_children():
        vals = tabla_clientes.item(item).get("values", [])
        if vals and int(vals[0]) == int(dni):
            tabla_clientes.selection_set(item)
            tabla_clientes.focus(item)
            break

    tabla_clientes.bind("<<TreeviewSelect>>", seleccionar_cliente)


def buscar_en_tiempo_real(event=None):
    """Filtra clientes."""
    termino = cuadroBuscar.get().strip()

    for fila in tabla_clientes.get_children():
        tabla_clientes.delete(fila)

    try:
        conexion = sqlite3.connect(NOMBRE_BD)
        cursor = conexion.cursor()
        cursor.execute(
            """
            SELECT * FROM CLIENTES
            WHERE NOMBRE LIKE ? OR APELLIDO LIKE ? OR CAST(DNI_ID AS TEXT) LIKE ?
            ORDER BY DNI_ID ASC
        """,
            (f"%{termino}%", f"%{termino}%", f"%{termino}%"),
        )

        for fila in cursor.fetchall():
            saldo = calcular_saldo(fila[0])
            tabla_clientes.insert(
                "",
                END,
                values=(
                    fila[0],
                    fila[1],
                    fila[2],
                    fila[3],
                    fila[4],
                    fila[5],
                    fila[6],
                    f"${saldo:.2f}",
                ),
            )
        conexion.close()
    except Exception as e:
        print(f"Error en búsqueda: {e}")


def limpiar_campos():
    """Resetea formulario."""
    global cliente_seleccionado_dni
    cliente_seleccionado_dni = None

    cuadroID.delete(0, END)
    cuadroNombre.delete(0, END)
    cuadroApellido.delete(0, END)
    cuadroEmail.delete(0, END)
    cuadroDireccion.delete(0, END)
    cuadroNumCuenta.delete(0, END)
    cuadroAlias.delete(0, END)
    cuadroMonto.delete(0, END)
    cuadroBuscar.delete(0, END)
    lbl_cliente_activo.config(
        text="Ninguno (Seleccione de la tabla)", fg="gray"
    )
    lbl_saldo_var.set("$0.00")

    for fila in tabla_movimientos.get_children():
        tabla_movimientos.delete(fila)

    mostrar_clientes()


def salir():
    if messagebox.askquestion("Salir", "¿Desea cerrar la aplicación?") == "yes":
        root.destroy()


# --- INTERFAZ GRÁFICA ---

root = Tk()
root.title("Gestión Bancaria - Base de Datos Actualizada")
root.geometry("1020x760")

main_canvas = Canvas(root)
scrollbar_main = ttk.Scrollbar(
    root, orient=VERTICAL, command=main_canvas.yview
)
scrollable_frame = Frame(main_canvas)

scrollable_frame.bind(
    "<Configure>",
    lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all")),
)
main_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
main_canvas.configure(yscrollcommand=scrollbar_main.set)

main_canvas.pack(side=LEFT, fill=BOTH, expand=True)
scrollbar_main.pack(side=RIGHT, fill=Y)

Label(
    scrollable_frame,
    text="Panel de Gestión Bancaria",
    font=("Helvetica", 16, "bold"),
).pack(pady=10)

# Formulario Cliente
frame_manga = LabelFrame(
    scrollable_frame, text=" Datos del Cliente ", font=("Helvetica", 10, "bold")
)
frame_manga.pack(fill=X, padx=15, pady=5)

Label(frame_manga, text="DNI / ID:").grid(
    row=0, column=0, sticky="e", padx=5, pady=3
)
cuadroID = Entry(frame_manga, width=22)
cuadroID.grid(row=0, column=1, padx=5, pady=3)

Label(frame_manga, text="Nº Cuenta:").grid(
    row=0, column=2, sticky="e", padx=5, pady=3
)
cuadroNumCuenta = Entry(frame_manga, width=22)
cuadroNumCuenta.grid(row=0, column=3, padx=5, pady=3)

Label(frame_manga, text="Nombre:").grid(
    row=1, column=0, sticky="e", padx=5, pady=3
)
cuadroNombre = Entry(frame_manga, width=22)
cuadroNombre.grid(row=1, column=1, padx=5, pady=3)

Label(frame_manga, text="Alias:").grid(
    row=1, column=2, sticky="e", padx=5, pady=3
)
cuadroAlias = Entry(frame_manga, width=22)
cuadroAlias.grid(row=1, column=3, padx=5, pady=3)

Label(frame_manga, text="Apellido:").grid(
    row=2, column=0, sticky="e", padx=5, pady=3
)
cuadroApellido = Entry(frame_manga, width=22)
cuadroApellido.grid(row=2, column=1, padx=5, pady=3)

Label(frame_manga, text="Email:").grid(
    row=2, column=2, sticky="e", padx=5, pady=3
)
cuadroEmail = Entry(frame_manga, width=22)
cuadroEmail.grid(row=2, column=3, padx=5, pady=3)

Label(frame_manga, text="Dirección:").grid(
    row=3, column=0, sticky="e", padx=5, pady=3
)
cuadroDireccion = Entry(frame_manga, width=22)
cuadroDireccion.grid(row=3, column=1, padx=5, pady=3)

frame_btn_cliente = Frame(scrollable_frame)
frame_btn_cliente.pack(pady=5)

Button(
    frame_btn_cliente,
    text="Guardar / Modificar",
    command=alta_o_modificacion,
    width=16,
).grid(row=0, column=0, padx=5)
Button(
    frame_btn_cliente,
    text="Limpiar Selección",
    command=limpiar_campos,
    width=16,
).grid(row=0, column=1, padx=5)
Button(frame_btn_cliente, text="Salir", command=salir, width=12).grid(
    row=0, column=2, padx=5
)

# Tabla de Selección de Clientes
frame_busqueda = Frame(scrollable_frame)
frame_busqueda.pack(fill=X, padx=15, pady=(10, 2))

Label(
    frame_busqueda, text="🔍 Buscar Cliente:", font=("Helvetica", 9, "bold")
).pack(side=LEFT, padx=(0, 5))
cuadroBuscar = Entry(frame_busqueda)
cuadroBuscar.pack(side=LEFT, fill=X, expand=True, padx=5)
cuadroBuscar.bind("<KeyRelease>", buscar_en_tiempo_real)

frame_tabla_cli = Frame(scrollable_frame)
frame_tabla_cli.pack(fill=X, padx=15, pady=5)

columnas_cli = (
    "DNI",
    "Nombre",
    "Apellido",
    "Email",
    "Dirección",
    "Nº Cuenta",
    "Alias",
    "Saldo Actual",
)
tabla_clientes = ttk.Treeview(
    frame_tabla_cli, columns=columnas_cli, show="headings", height=5
)

for col in columnas_cli:
    tabla_clientes.heading(col, text=col)
    tabla_clientes.column(col, anchor="center", width=115)

tabla_clientes.bind("<<TreeviewSelect>>", seleccionar_cliente)
scroll_cli = ttk.Scrollbar(
    frame_tabla_cli, orient=VERTICAL, command=tabla_clientes.yview
)
tabla_clientes.configure(yscroll=scroll_cli.set)

tabla_clientes.pack(side=LEFT, fill=BOTH, expand=True)
scroll_cli.pack(side=RIGHT, fill=Y)

# Área de Operaciones
frame_ops = LabelFrame(
    scrollable_frame,
    text=" Transacciones sobre el Cliente Seleccionado ",
    font=("Helvetica", 10, "bold"),
    fg="#0d47a1",
)
frame_ops.pack(fill=X, padx=15, pady=10)

Label(frame_ops, text="Cliente Activo:").grid(
    row=0, column=0, padx=5, pady=5, sticky="e"
)
lbl_cliente_activo = Label(
    frame_ops,
    text="Ninguno (Seleccione de la tabla)",
    font=("Helvetica", 9, "italic"),
    fg="gray",
)
lbl_cliente_activo.grid(
    row=0, column=1, columnspan=2, padx=5, pady=5, sticky="w"
)

Label(frame_ops, text="Tipo:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
comboTipoMov = ttk.Combobox(
    frame_ops, values=["Depósito", "Retiro"], state="readonly", width=10
)
comboTipoMov.set("Depósito")
comboTipoMov.grid(row=1, column=1, padx=5, pady=5)

Label(frame_ops, text="Monto ($):").grid(
    row=1, column=2, padx=5, pady=5, sticky="e"
)
cuadroMonto = Entry(frame_ops, width=12)
cuadroMonto.grid(row=1, column=3, padx=5, pady=5)

Button(
    frame_ops,
    text="Procesar Transacción",
    command=registrar_movimiento,
    bg="#e1f5fe",
    font=("Helvetica", 9, "bold"),
).grid(row=1, column=4, padx=10, pady=5)

Label(frame_ops, text="Saldo Disponible:", font=("Helvetica", 9, "bold")).grid(
    row=1, column=5, padx=(10, 2)
)
lbl_saldo_var = StringVar(value="$0.00")
Label(
    frame_ops,
    textvariable=lbl_saldo_var,
    font=("Helvetica", 11, "bold"),
    fg="green",
).grid(row=1, column=6, padx=5)

# Historial de Movimientos
frame_tabla_mov = LabelFrame(
    scrollable_frame,
    text=" Historial del Cliente Seleccionado ",
    font=("Helvetica", 10, "bold"),
)
frame_tabla_mov.pack(fill=X, padx=15, pady=5)

columnas_mov = ("ID Transacción", "Tipo", "Monto", "Fecha y Hora")
tabla_movimientos = ttk.Treeview(
    frame_tabla_mov, columns=columnas_mov, show="headings", height=5
)

for col in columnas_mov:
    tabla_movimientos.heading(col, text=col)
    tabla_movimientos.column(col, anchor="center", width=200)

scroll_mov = ttk.Scrollbar(
    frame_tabla_mov, orient=VERTICAL, command=tabla_movimientos.yview
)
tabla_movimientos.configure(yscroll=scroll_mov.set)

tabla_movimientos.pack(side=LEFT, fill=BOTH, expand=True)
scroll_mov.pack(side=RIGHT, fill=Y)

# Inicializar Base de Datos con verificación automática
reiniciar_y_conectar_bd()

root.mainloop()