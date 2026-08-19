import sqlite3
from datetime import datetime
from tkinter import *
from tkinter import messagebox, ttk

NOMBRE_BD = "BD_BancoDB.db"
cliente_seleccionado_dni = None


def conectar_bd():
    """Crea las tablas necesarias si no existen."""
    try:
        conexion = sqlite3.connect(NOMBRE_BD)
        cursor = conexion.cursor()

        # Tabla Clientes
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

        # Tabla Movimientos de Cuenta
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

        # Tabla Tarjetas (Débito / Crédito)
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS TARJETAS (
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                DNI_ID INTEGER,
                TIPO_TARJETA VARCHAR(20),
                NUMERO_TARJETA VARCHAR(20),
                FECHA_VENC VARCHAR(10),
                LIMITE_CREDITO REAL,
                FOREIGN KEY (DNI_ID) REFERENCES CLIENTES(DNI_ID)
            )
        """
        )

        # Tabla Movimientos de Tarjetas (Consumos)
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS MOVIMIENTOS_TARJETAS (
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                ID_TARJETA INTEGER,
                CONCEPTO VARCHAR(100),
                MONTO REAL,
                FECHA VARCHAR(30),
                FOREIGN KEY (ID_TARJETA) REFERENCES TARJETAS(ID)
            )
        """
        )

        try:
            cursor.execute(
                "ALTER TABLE MOVIMIENTOS ADD COLUMN TIPO VARCHAR(20)"
            )
        except sqlite3.OperationalError:
            pass

        conexion.commit()
        conexion.close()
        mostrar_clientes()
    except Exception as e:
        messagebox.showerror(
            "Error BD", f"Error al inicializar la base de datos: {e}"
        )


def calcular_saldo(dni):
    """Calcula el saldo acumulado en cuenta de un cliente."""
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
    """Carga los datos y servicios del cliente seleccionado."""
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
        actualizar_combo_tarjetas(cliente_seleccionado_dni)
    except Exception as e:
        print(f"Error al seleccionar cliente: {e}")


def dar_de_alta_cliente():
    """Alta de nuevo cliente sin sobrescribir existentes."""
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
            messagebox.showerror(
                "Cliente Existente",
                f"El DNI {dni} ya se encuentra registrado.",
            )
            conexion.close()
            return

        cursor.execute(
            "INSERT INTO CLIENTES VALUES (?, ?, ?, ?, ?, ?, ?)",
            (dni, nombre, apellido, email, direccion, num_cuenta, alias),
        )
        conexion.commit()
        conexion.close()

        messagebox.showinfo(
            "Éxito", f"Cliente {nombre} {apellido} registrado."
        )
        limpiar_campos()
    except Exception as e:
        messagebox.showerror("Error BD", f"Error al dar de alta: {e}")


def modificar_cliente():
    """Modifica datos de un cliente existente."""
    dni_str = cuadroID.get().strip()
    if not dni_str or not dni_str.isdigit():
        messagebox.showwarning("DNI Inválido", "Ingrese un DNI válido.")
        return

    dni = int(dni_str)

    try:
        conexion = sqlite3.connect(NOMBRE_BD)
        cursor = conexion.cursor()
        cursor.execute(
            """
            UPDATE CLIENTES SET NOMBRE=?, APELLIDO=?, EMAIL=?, DIRECCION=?, NUM_CUENTA=?, ALIAS=?
            WHERE DNI_ID=?
        """,
            (
                cuadroNombre.get(),
                cuadroApellido.get(),
                cuadroEmail.get(),
                cuadroDireccion.get(),
                cuadroNumCuenta.get(),
                cuadroAlias.get(),
                dni,
            ),
        )
        conexion.commit()
        conexion.close()
        messagebox.showinfo("Actualizado", "Cliente actualizado.")
        limpiar_campos()
    except Exception as e:
        messagebox.showerror("Error BD", f"Error al modificar: {e}")


def dar_de_baja_cliente():
    """Elimina cliente, movimientos y tarjetas asociadas."""
    dni_str = cuadroID.get().strip()
    if not dni_str or not dni_str.isdigit():
        messagebox.showwarning(
            "Selección requerida", "Seleccione o ingrese un DNI válido."
        )
        return

    dni = int(dni_str)
    if not messagebox.askyesno(
        "Confirmar Baja",
        f"¿Desea dar de baja al cliente DNI {dni} y eliminar todos sus productos?",
    ):
        return

    try:
        conexion = sqlite3.connect(NOMBRE_BD)
        cursor = conexion.cursor()

        cursor.execute(
            "DELETE FROM MOVIMIENTOS_TARJETAS WHERE ID_TARJETA IN (SELECT ID FROM TARJETAS WHERE DNI_ID=?)",
            (dni,),
        )
        cursor.execute("DELETE FROM TARJETAS WHERE DNI_ID=?", (dni,))
        cursor.execute("DELETE FROM MOVIMIENTOS WHERE DNI_ID=?", (dni,))
        cursor.execute("DELETE FROM CLIENTES WHERE DNI_ID=?", (dni,))

        conexion.commit()
        conexion.close()

        messagebox.showinfo(
            "Baja Completa", "Cliente y productos eliminados con éxito."
        )
        limpiar_campos()
    except Exception as e:
        messagebox.showerror("Error BD", f"Error al dar de baja: {e}")


def registrar_movimiento():
    """Registra depósito o retiro en cuenta corriente/caja de ahorro."""
    if cliente_seleccionado_dni is None:
        messagebox.showwarning(
            "Selección requerida", "Seleccione un cliente de la tabla."
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
            "Monto inválido", "Ingrese un monto mayor a $0."
        )
        return

    if tipo == "Retiro" and monto > calcular_saldo(dni):
        messagebox.showerror("Saldo Insuficiente", "Fondos insuficientes.")
        return

    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        conexion = sqlite3.connect(NOMBRE_BD)
        cursor = conexion.cursor()
        cursor.execute(
            "INSERT INTO MOVIMIENTOS (DNI_ID, TIPO, MONTO, FECHA) VALUES (?, ?, ?, ?)",
            (int(dni), str(tipo), float(monto), str(fecha_actual)),
        )
        conexion.commit()
        conexion.close()

        cuadroMonto.delete(0, END)
        actualizar_pantalla_cliente(dni)
    except Exception as e:
        messagebox.showerror("Error BD", f"Error al registrar movimiento: {e}")


def asociar_tarjeta():
    """Registra una nueva tarjeta de crédito o débito para el cliente."""
    if cliente_seleccionado_dni is None:
        messagebox.showwarning(
            "Selección requerida", "Seleccione un cliente de la tabla."
        )
        return

    tipo = comboTipoTarjeta.get()
    num = cuadroNumTarjeta.get().strip()
    venc = cuadroVencTarjeta.get().strip()
    limite_str = cuadroLimiteTarjeta.get().strip()

    if not num or not venc:
        messagebox.showwarning(
            "Campos Incompletos", "Complete número y vencimiento de tarjeta."
        )
        return

    try:
        limite = float(limite_str) if tipo == "Crédito" and limite_str else 0.0
    except ValueError:
        messagebox.showwarning(
            "Límite Inválido", "Ingrese un valor numérico para el límite."
        )
        return

    try:
        conexion = sqlite3.connect(NOMBRE_BD)
        cursor = conexion.cursor()
        cursor.execute(
            """
            INSERT INTO TARJETAS (DNI_ID, TIPO_TARJETA, NUMERO_TARJETA, FECHA_VENC, LIMITE_CREDITO)
            VALUES (?, ?, ?, ?, ?)
        """,
            (cliente_seleccionado_dni, tipo, num, venc, limite),
        )
        conexion.commit()
        conexion.close()

        messagebox.showinfo(
            "Tarjeta Registrada", f"Tarjeta de {tipo} añadida con éxito."
        )
        cuadroNumTarjeta.delete(0, END)
        cuadroVencTarjeta.delete(0, END)
        cuadroLimiteTarjeta.delete(0, END)
        actualizar_combo_tarjetas(cliente_seleccionado_dni)
    except Exception as e:
        messagebox.showerror("Error BD", f"Error al asociar tarjeta: {e}")


def actualizar_combo_tarjetas(dni):
    """Carga en el combo desplegable las tarjetas del cliente activo."""
    try:
        conexion = sqlite3.connect(NOMBRE_BD)
        cursor = conexion.cursor()
        cursor.execute(
            "SELECT ID, TIPO_TARJETA, NUMERO_TARJETA FROM TARJETAS WHERE DNI_ID=?",
            (dni,),
        )
        tarjetas = cursor.fetchall()
        conexion.close()

        opciones = [
            f"ID:{t[0]} - {t[1]} (**** {t[2][-4:] if len(t[2])>=4 else t[2]})"
            for t in tarjetas
        ]
        comboTarjetasCliente["values"] = opciones

        if opciones:
            comboTarjetasCliente.current(0)
            cargar_movimientos_tarjeta_seleccionada()
        else:
            comboTarjetasCliente.set("")
            for fila in tabla_mov_tarjetas.get_children():
                tabla_mov_tarjetas.delete(fila)
    except Exception as e:
        print(f"Error al actualizar tarjetas: {e}")


def registrar_movimiento_tarjeta():
    """Guarda una compra/consumo en la tarjeta seleccionada."""
    tarjeta_str = comboTarjetasCliente.get()
    if not tarjeta_str:
        messagebox.showwarning(
            "Selección Requerida",
            "Seleccione una tarjeta activa para registrar consumo.",
        )
        return

    id_tarjeta = int(tarjeta_str.split("-")[0].replace("ID:", "").strip())
    concepto = cuadroConceptoTarjeta.get().strip()
    monto_str = cuadroMontoTarjeta.get().strip()

    if not concepto or not monto_str:
        messagebox.showwarning(
            "Campos Incompletos", "Ingrese el concepto y el monto del consumo."
        )
        return

    try:
        monto = float(monto_str.replace(",", "."))
    except ValueError:
        messagebox.showwarning("Monto Inválido", "Ingrese un monto válido.")
        return

    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        conexion = sqlite3.connect(NOMBRE_BD)
        cursor = conexion.cursor()
        cursor.execute(
            """
            INSERT INTO MOVIMIENTOS_TARJETAS (ID_TARJETA, CONCEPTO, MONTO, FECHA)
            VALUES (?, ?, ?, ?)
        """,
            (id_tarjeta, concepto, monto, fecha_actual),
        )
        conexion.commit()
        conexion.close()

        messagebox.showinfo("Éxito", "Consumo registrado correctamente.")
        cuadroConceptoTarjeta.delete(0, END)
        cuadroMontoTarjeta.delete(0, END)
        cargar_movimientos_tarjeta_seleccionada()
    except Exception as e:
        messagebox.showerror("Error BD", f"Error al guardar consumo: {e}")


def cargar_movimientos_tarjeta_seleccionada(event=None):
    """Muestra los consumos en la tabla según la tarjeta elegida."""
    for fila in tabla_mov_tarjetas.get_children():
        tabla_mov_tarjetas.delete(fila)

    tarjeta_str = comboTarjetasCliente.get()
    if not tarjeta_str:
        return

    try:
        id_tarjeta = int(tarjeta_str.split("-")[0].replace("ID:", "").strip())
        conexion = sqlite3.connect(NOMBRE_BD)
        cursor = conexion.cursor()
        cursor.execute(
            "SELECT ID, CONCEPTO, MONTO, FECHA FROM MOVIMIENTOS_TARJETAS WHERE ID_TARJETA=? ORDER BY ID DESC",
            (id_tarjeta,),
        )
        movs = cursor.fetchall()
        conexion.close()

        for m in movs:
            tabla_mov_tarjetas.insert(
                "", END, values=(m[0], m[1], f"${float(m[2]):.2f}", m[3])
            )
    except Exception as e:
        print(f"Error al cargar consumos: {e}")


def mostrar_clientes():
    """Actualiza la tabla principal de clientes."""
    for fila in tabla_clientes.get_children():
        tabla_clientes.delete(fila)
    try:
        conexion = sqlite3.connect(NOMBRE_BD)
        cursor = conexion.cursor()
        cursor.execute("SELECT * FROM CLIENTES ORDER BY DNI_ID ASC")
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
        print(f"Error al mostrar clientes: {e}")


def mostrar_historial_movimientos(dni):
    """Muestra movimientos de la cuenta bancaria del cliente."""
    for fila in tabla_movimientos.get_children():
        tabla_movimientos.delete(fila)
    try:
        conexion = sqlite3.connect(NOMBRE_BD)
        cursor = conexion.cursor()
        cursor.execute(
            "SELECT ID, TIPO, MONTO, FECHA FROM MOVIMIENTOS WHERE DNI_ID=? ORDER BY ID DESC",
            (int(dni),),
        )
        for fila in cursor.fetchall():
            tabla_movimientos.insert(
                "",
                END,
                values=(
                    fila[0],
                    fila[1] or "-",
                    f"${float(fila[2]):.2f}",
                    fila[3],
                ),
            )
        conexion.close()
    except Exception as e:
        print(f"Error al mostrar movimientos: {e}")


def actualizar_pantalla_cliente(dni):
    """Refresca datos manteniendo el foco en el cliente actual."""
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
    """Filtra la lista de clientes."""
    termino = cuadroBuscar.get().strip()
    for fila in tabla_clientes.get_children():
        tabla_clientes.delete(fila)
    try:
        conexion = sqlite3.connect(NOMBRE_BD)
        cursor = conexion.cursor()
        cursor.execute(
            "SELECT * FROM CLIENTES WHERE NOMBRE LIKE ? OR APELLIDO LIKE ? OR CAST(DNI_ID AS TEXT) LIKE ? ORDER BY DNI_ID ASC",
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
        print(f"Error al buscar: {e}")


def limpiar_campos():
    """Limpia los campos y resetea las vistas."""
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

    cuadroNumTarjeta.delete(0, END)
    cuadroVencTarjeta.delete(0, END)
    cuadroLimiteTarjeta.delete(0, END)
    cuadroConceptoTarjeta.delete(0, END)
    cuadroMontoTarjeta.delete(0, END)

    lbl_cliente_activo.config(
        text="Ninguno (Seleccione de la tabla)", fg="gray"
    )
    lbl_saldo_var.set("$0.00")

    for fila in tabla_movimientos.get_children():
        tabla_movimientos.delete(fila)
    for fila in tabla_mov_tarjetas.get_children():
        tabla_mov_tarjetas.delete(fila)

    comboTarjetasCliente.set("")
    mostrar_clientes()


def salir():
    if messagebox.askquestion("Salir", "¿Desea cerrar la aplicación?") == "yes":
        root.destroy()


# --- INTERFAZ GRÁFICA TKINTER ---

root = Tk()
root.title("Sistema Bancario Unificado")
root.geometry("1060x820")

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
    text="Panel de Gestión Bancaria e Integral",
    font=("Helvetica", 16, "bold"),
).pack(pady=10)

# Formulario Clientes
frame_cli = LabelFrame(
    scrollable_frame, text=" Datos del Cliente ", font=("Helvetica", 10, "bold")
)
frame_cli.pack(fill=X, padx=15, pady=5)

Label(frame_cli, text="DNI / ID:").grid(
    row=0, column=0, sticky="e", padx=5, pady=3
)
cuadroID = Entry(frame_cli, width=22)
cuadroID.grid(row=0, column=1, padx=5, pady=3)

Label(frame_cli, text="Nº Cuenta:").grid(
    row=0, column=2, sticky="e", padx=5, pady=3
)
cuadroNumCuenta = Entry(frame_cli, width=22)
cuadroNumCuenta.grid(row=0, column=3, padx=5, pady=3)

Label(frame_cli, text="Nombre:").grid(
    row=1, column=0, sticky="e", padx=5, pady=3
)
cuadroNombre = Entry(frame_cli, width=22)
cuadroNombre.grid(row=1, column=1, padx=5, pady=3)

Label(frame_cli, text="Alias:").grid(
    row=1, column=2, sticky="e", padx=5, pady=3
)
cuadroAlias = Entry(frame_cli, width=22)
cuadroAlias.grid(row=1, column=3, padx=5, pady=3)

Label(frame_cli, text="Apellido:").grid(
    row=2, column=0, sticky="e", padx=5, pady=3
)
cuadroApellido = Entry(frame_cli, width=22)
cuadroApellido.grid(row=2, column=1, padx=5, pady=3)

Label(frame_cli, text="Email:").grid(
    row=2, column=2, sticky="e", padx=5, pady=3
)
cuadroEmail = Entry(frame_cli, width=22)
cuadroEmail.grid(row=2, column=3, padx=5, pady=3)

Label(frame_cli, text="Dirección:").grid(
    row=3, column=0, sticky="e", padx=5, pady=3
)
cuadroDireccion = Entry(frame_cli, width=22)
cuadroDireccion.grid(row=3, column=1, padx=5, pady=3)

# Botones Clientes
frame_btn_cli = Frame(scrollable_frame)
frame_btn_cli.pack(pady=5)

Button(
    frame_btn_cli,
    text="Dar de Alta",
    command=dar_de_alta_cliente,
    bg="#e8f5e9",
    width=14,
).grid(row=0, column=0, padx=4)
Button(
    frame_btn_cli, text="Modificar", command=modificar_cliente, width=14
).grid(row=0, column=1, padx=4)
Button(
    frame_btn_cli,
    text="Dar de Baja",
    command=dar_de_baja_cliente,
    bg="#ffebee",
    fg="#c62828",
    width=14,
).grid(row=0, column=2, padx=4)
Button(
    frame_btn_cli,
    text="Limpiar Selección",
    command=limpiar_campos,
    width=14,
).grid(row=0, column=3, padx=4)
Button(frame_btn_cli, text="Salir", command=salir, width=10).grid(
    row=0, column=4, padx=4
)

# Buscador y Tabla Clientes
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
    frame_tabla_cli, columns=columnas_cli, show="headings", height=4
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

# Movimientos de Cuenta
frame_ops = LabelFrame(
    scrollable_frame,
    text=" Transacciones en Cuenta ",
    font=("Helvetica", 10, "bold"),
    fg="#0d47a1",
)
frame_ops.pack(fill=X, padx=15, pady=5)

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

# Historial de Cuenta
frame_tabla_mov = LabelFrame(
    scrollable_frame,
    text=" Historial de Cuenta Bancaria ",
    font=("Helvetica", 10, "bold"),
)
frame_tabla_mov.pack(fill=X, padx=15, pady=5)

columnas_mov = ("ID Transacción", "Tipo", "Monto", "Fecha y Hora")
tabla_movimientos = ttk.Treeview(
    frame_tabla_mov, columns=columnas_mov, show="headings", height=4
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

# Módulo de Tarjetas y Consumos
frame_tarjetas = LabelFrame(
    scrollable_frame,
    text=" Módulo de Tarjetas y Consumos ",
    font=("Helvetica", 10, "bold"),
    fg="#2e7d32",
)
frame_tarjetas.pack(fill=X, padx=15, pady=10)

# Emisión de tarjeta
frame_alta_t = Frame(frame_tarjetas)
frame_alta_t.pack(fill=X, padx=5, pady=5)

Label(frame_alta_t, text="Tipo:").grid(row=0, column=0, padx=3, pady=2)
comboTipoTarjeta = ttk.Combobox(
    frame_alta_t, values=["Débito", "Crédito"], state="readonly", width=10
)
comboTipoTarjeta.set("Débito")
comboTipoTarjeta.grid(row=0, column=1, padx=3, pady=2)

Label(frame_alta_t, text="Nº Tarjeta:").grid(
    row=0, column=2, padx=3, pady=2
)
cuadroNumTarjeta = Entry(frame_alta_t, width=18)
cuadroNumTarjeta.grid(row=0, column=3, padx=3, pady=2)

Label(frame_alta_t, text="Venc (MM/AA):").grid(
    row=0, column=4, padx=3, pady=2
)
cuadroVencTarjeta = Entry(frame_alta_t, width=8)
cuadroVencTarjeta.grid(row=0, column=5, padx=3, pady=2)

Label(frame_alta_t, text="Límite Cred ($):").grid(
    row=0, column=6, padx=3, pady=2
)
cuadroLimiteTarjeta = Entry(frame_alta_t, width=10)
cuadroLimiteTarjeta.grid(row=0, column=7, padx=3, pady=2)

Button(
    frame_alta_t,
    text="Emitir Tarjeta",
    command=asociar_tarjeta,
    bg="#e8f5e9",
    font=("Helvetica", 8, "bold"),
).grid(row=0, column=8, padx=10, pady=2)

ttk.Separator(frame_tarjetas, orient=HORIZONTAL).pack(
    fill=X, padx=5, pady=5
)

# Transacciones con Tarjeta
frame_ops_t = Frame(frame_tarjetas)
frame_ops_t.pack(fill=X, padx=5, pady=5)

Label(
    frame_ops_t, text="Tarjeta Activa:", font=("Helvetica", 9, "bold")
).grid(row=0, column=0, padx=3, pady=2)
comboTarjetasCliente = ttk.Combobox(frame_ops_t, state="readonly", width=30)
comboTarjetasCliente.grid(row=0, column=1, padx=3, pady=2)
comboTarjetasCliente.bind(
    "<<ComboboxSelected>>", cargar_movimientos_tarjeta_seleccionada
)

Label(frame_ops_t, text="Concepto:").grid(row=0, column=2, padx=3, pady=2)
cuadroConceptoTarjeta = Entry(frame_ops_t, width=18)
cuadroConceptoTarjeta.grid(row=0, column=3, padx=3, pady=2)

Label(frame_ops_t, text="Monto ($):").grid(row=0, column=4, padx=3, pady=2)
cuadroMontoTarjeta = Entry(frame_ops_t, width=10)
cuadroMontoTarjeta.grid(row=0, column=5, padx=3, pady=2)

Button(
    frame_ops_t,
    text="Registrar Consumo",
    command=registrar_movimiento_tarjeta,
    bg="#fff3e0",
    font=("Helvetica", 8, "bold"),
).grid(row=0, column=6, padx=10, pady=2)

# Tabla Consumos Tarjeta
frame_tabla_tar_mov = Frame(frame_tarjetas)
frame_tabla_tar_mov.pack(fill=X, padx=5, pady=5)

columnas_t_mov = ("ID Mov", "Concepto / Detalle", "Monto", "Fecha y Hora")
tabla_mov_tarjetas = ttk.Treeview(
    frame_tabla_tar_mov, columns=columnas_t_mov, show="headings", height=4
)
for col in columnas_t_mov:
    tabla_mov_tarjetas.heading(col, text=col)
    tabla_mov_tarjetas.column(col, anchor="center", width=200)

scroll_t_mov = ttk.Scrollbar(
    frame_tabla_tar_mov, orient=VERTICAL, command=tabla_mov_tarjetas.yview
)
tabla_mov_tarjetas.configure(yscroll=scroll_t_mov.set)
tabla_mov_tarjetas.pack(side=LEFT, fill=BOTH, expand=True)
scroll_t_mov.pack(side=RIGHT, fill=Y)

# Iniciar aplicación
conectar_bd()
root.mainloop()