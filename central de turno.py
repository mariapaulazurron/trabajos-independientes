import os
import sqlite3
from datetime import datetime
from tkinter import *
from tkinter import messagebox, ttk

NOMBRE_BD = "BD_Hospital.db"


def Base_de_Datos():
    # Se conecta a la base de datos y crea la tabla solo si no existe previa
    conexion = sqlite3.connect(NOMBRE_BD)
    cursor = conexion.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS TURNOS (
            ID_TURNO INTEGER PRIMARY KEY AUTOINCREMENT,
            NOMBRE TEXT,
            APELLIDO TEXT,
            FECHA_NAC TEXT,
            DIRECCION TEXT,
            TELEFONO TEXT,
            LOCALIDAD TEXT,
            OBRA_SOCIAL TEXT,
            PLAN TEXT,
            NUM_AFILIADO TEXT,
            ESPECIALIDAD TEXT,
            MEDICO TEXT,
            FECHA_TURNO TEXT,
            HORA_TURNO TEXT
        )
    """
    )
    conexion.commit()
    conexion.close()

    limpiar_campos()
    actualizar_tabla()
    messagebox.showinfo(
        "Conexión",
        "Conexión establecida exitosamente con la Base de Datos.",
    )


def Alta():
    nom = cuadroNombre.get()
    ape = cuadroApellido.get()
    fnac = cuadroFechaNac.get()
    dir_ = cuadroDireccion.get()
    tel = cuadroTelefono.get()
    loc = cuadroLocalidad.get()
    obs = comboObraSocial.get()
    pln = cuadroPlan.get()
    afi = cuadroAfiliado.get()
    esp = comboEspecialidad.get()
    med = comboMedico.get()

    dia = comboDia.get()
    mes = comboMes.get()
    anio = comboAnio.get()

    if not nom or not ape:
        messagebox.showwarning("Atención", "Por favor completa Nombre y Apellido.")
        return

    if not dia or not mes or not anio:
        messagebox.showwarning(
            "Atención", "Por favor selecciona una fecha de turno completa."
        )
        return

    ftur = f"{dia}/{mes}/{anio}"
    htur = comboHoraTurno.get()

    try:
        conexion = sqlite3.connect(NOMBRE_BD)
        cursor = conexion.cursor()
        cursor.execute(
            """INSERT INTO TURNOS VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                nom,
                ape,
                fnac,
                dir_,
                tel,
                loc,
                obs,
                pln,
                afi,
                esp,
                med,
                ftur,
                htur,
            ),
        )
        conexion.commit()

        id_generado = cursor.lastrowid
        conexion.close()

        messagebox.showinfo(
            "Registro", f"Se ha registrado un nuevo turno con ID #{id_generado}."
        )
        limpiar_campos()
        actualizar_tabla()
    except sqlite3.OperationalError:
        messagebox.showerror(
            "Error", "Primero debes presionar 'Conectar BD' para inicializar la base de datos."
        )


def Modificar():
    id_t = cuadroID.get()
    if not id_t:
        messagebox.showwarning(
            "Atención", "Haz doble clic en un turno de la lista para cargarlo y modificarlo."
        )
        return

    nom = cuadroNombre.get()
    ape = cuadroApellido.get()
    fnac = cuadroFechaNac.get()
    dir_ = cuadroDireccion.get()
    tel = cuadroTelefono.get()
    loc = cuadroLocalidad.get()
    obs = comboObraSocial.get()
    pln = cuadroPlan.get()
    afi = cuadroAfiliado.get()
    esp = comboEspecialidad.get()
    med = comboMedico.get()

    dia = comboDia.get()
    mes = comboMes.get()
    anio = comboAnio.get()

    if not dia or not mes or not anio:
        messagebox.showwarning(
            "Atención", "Por favor selecciona una fecha de turno completa."
        )
        return

    ftur = f"{dia}/{mes}/{anio}"
    htur = comboHoraTurno.get()

    try:
        conexion = sqlite3.connect(NOMBRE_BD)
        cursor = conexion.cursor()
        cursor.execute(
            """UPDATE TURNOS SET
            NOMBRE=?, APELLIDO=?, FECHA_NAC=?, DIRECCION=?, TELEFONO=?, LOCALIDAD=?,
            OBRA_SOCIAL=?, PLAN=?, NUM_AFILIADO=?, ESPECIALIDAD=?, MEDICO=?, FECHA_TURNO=?, HORA_TURNO=?
            WHERE ID_TURNO=?""",
            (
                nom,
                ape,
                fnac,
                dir_,
                tel,
                loc,
                obs,
                pln,
                afi,
                esp,
                med,
                ftur,
                htur,
                id_t,
            ),
        )
        conexion.commit()
        conexion.close()

        messagebox.showinfo("Modificación", f"El Turno ID #{id_t} ha sido modificado.")
        limpiar_campos()
        actualizar_tabla()
    except sqlite3.OperationalError:
        messagebox.showerror(
            "Error", "Primero debes presionar 'Conectar BD' para inicializar la base de datos."
        )


def Baja():
    id_t = cuadroID.get()
    if not id_t:
        messagebox.showwarning(
            "Atención", "Haz doble clic en un turno del listado para seleccionar y eliminar."
        )
        return

    if messagebox.askyesno("Confirmar", f"¿Eliminar el turno #{id_t}?"):
        try:
            conexion = sqlite3.connect(NOMBRE_BD)
            cursor = conexion.cursor()
            cursor.execute("DELETE FROM TURNOS WHERE ID_TURNO=?", (id_t,))
            conexion.commit()
            conexion.close()
            messagebox.showinfo("Eliminado", "El registro se ha eliminado exitosamente.")
            limpiar_campos()
            actualizar_tabla()
        except sqlite3.OperationalError:
            messagebox.showerror(
                "Error", "Primero debes presionar 'Conectar BD' para inicializar la base de datos."
            )


def limpiar_campos():
    cuadroID.config(state="normal")
    cuadroID.delete(0, END)
    cuadroID.config(state="readonly")

    cuadroNombre.delete(0, END)
    cuadroApellido.delete(0, END)
    cuadroFechaNac.delete(0, END)
    cuadroDireccion.delete(0, END)
    cuadroTelefono.delete(0, END)
    cuadroLocalidad.delete(0, END)
    comboObraSocial.set("")
    cuadroPlan.delete(0, END)
    cuadroAfiliado.delete(0, END)
    comboEspecialidad.set("")
    comboMedico.set("")
    comboDia.set("")
    comboMes.set("")
    comboAnio.set("")
    comboHoraTurno.set("")


def actualizar_tabla():
    for item in tabla_listado.get_children():
        tabla_listado.delete(item)

    try:
        conexion = sqlite3.connect(NOMBRE_BD)
        cursor = conexion.cursor()
        cursor.execute(
            "SELECT ID_TURNO, NOMBRE, APELLIDO, ESPECIALIDAD, FECHA_TURNO, HORA_TURNO FROM TURNOS"
        )
        filas = cursor.fetchall()
        for fila in filas:
            tabla_listado.insert("", END, values=fila)
        conexion.close()
    except sqlite3.OperationalError:
        pass


def al_hacer_doble_click(event):
    item_seleccionado = tabla_listado.focus()
    if not item_seleccionado:
        return

    valores = tabla_listado.item(item_seleccionado, "values")
    id_t = valores[0]

    try:
        conexion = sqlite3.connect(NOMBRE_BD)
        cursor = conexion.cursor()
        cursor.execute("SELECT * FROM TURNOS WHERE ID_TURNO=?", (id_t,))
        r = cursor.fetchone()
        conexion.close()

        if r:
            limpiar_campos()
            cuadroID.config(state="normal")
            cuadroID.insert(0, r[0])
            cuadroID.config(state="readonly")

            cuadroNombre.insert(0, r[1])
            cuadroApellido.insert(0, r[2])
            cuadroFechaNac.insert(0, r[3])
            cuadroDireccion.insert(0, r[4])
            cuadroTelefono.insert(0, r[5])
            cuadroLocalidad.insert(0, r[6])
            comboObraSocial.set(r[7])
            cuadroPlan.insert(0, r[8])
            cuadroAfiliado.insert(0, r[9])
            comboEspecialidad.set(r[10])
            comboMedico.set(r[11])

            if r[12] and "/" in r[12]:
                partes_fecha = r[12].split("/")
                if len(partes_fecha) == 3:
                    comboDia.set(partes_fecha[0])
                    comboMes.set(partes_fecha[1])
                    comboAnio.set(partes_fecha[2])

            comboHoraTurno.set(r[13])
    except sqlite3.OperationalError:
        messagebox.showerror(
            "Error", "Primero debes presionar 'Conectar BD' para inicializar la base de datos."
        )


def Salir():
    salir = messagebox.askquestion("Salir", "¿Seguro quieres salir?")
    if salir == "yes":
        root.destroy()


# --- INTERFAZ GRÁFICA ---
root = Tk()
root.title("Central de Turnos - Hospital")
root.geometry("880x700")

titulo = Label(
    root, text="Gestión de Turnos Hospitalarios", font=("Helvetica", 16, "bold")
)
titulo.pack(pady=10)

frameCampos = Frame(root)
frameCampos.pack(pady=5)

# Fila 0: ID Autoincrementable (Solo lectura)
Label(frameCampos, text="ID Turno:").grid(row=0, column=0, sticky="e", padx=5, pady=3)
cuadroID = Entry(frameCampos, state="readonly", width=10)
cuadroID.grid(row=0, column=1, sticky="w", padx=5, pady=3)

# Fila 1: Datos Paciente
Label(frameCampos, text="Nombre:").grid(row=1, column=0, sticky="e", padx=5, pady=3)
cuadroNombre = Entry(frameCampos, width=25)
cuadroNombre.grid(row=1, column=1, padx=5, pady=3)

Label(frameCampos, text="Apellido:").grid(row=1, column=2, sticky="e", padx=5, pady=3)
cuadroApellido = Entry(frameCampos, width=25)
cuadroApellido.grid(row=1, column=3, padx=5, pady=3)

# Fila 2
Label(frameCampos, text="Fecha Nac. (DD/MM/AAAA):").grid(
    row=2, column=0, sticky="e", padx=5, pady=3
)
cuadroFechaNac = Entry(frameCampos, width=25)
cuadroFechaNac.grid(row=2, column=1, padx=5, pady=3)

Label(frameCampos, text="Dirección:").grid(
    row=2, column=2, sticky="e", padx=5, pady=3
)
cuadroDireccion = Entry(frameCampos, width=25)
cuadroDireccion.grid(row=2, column=3, padx=5, pady=3)

# Fila 3
Label(frameCampos, text="Teléfono:").grid(row=3, column=0, sticky="e", padx=5, pady=3)
cuadroTelefono = Entry(frameCampos, width=25)
cuadroTelefono.grid(row=3, column=1, padx=5, pady=3)

Label(frameCampos, text="Localidad:").grid(
    row=3, column=2, sticky="e", padx=5, pady=3
)
cuadroLocalidad = Entry(frameCampos, width=25)
cuadroLocalidad.grid(row=3, column=3, padx=5, pady=3)

# Fila 4: Cobertura
Label(frameCampos, text="Obra Social:").grid(
    row=4, column=0, sticky="e", padx=5, pady=3
)
comboObraSocial = ttk.Combobox(
    frameCampos,
    values=["Particular", "OSDE", "Swiss Medical", "PAMI", "IOMA"],
    width=22,
    state="readonly",
)
comboObraSocial.grid(row=4, column=1, padx=5, pady=3)

Label(frameCampos, text="Plan:").grid(row=4, column=2, sticky="e", padx=5, pady=3)
cuadroPlan = Entry(frameCampos, width=25)
cuadroPlan.grid(row=4, column=3, padx=5, pady=3)

# Fila 5
Label(frameCampos, text="N° Afiliado:").grid(
    row=5, column=0, sticky="e", padx=5, pady=3
)
cuadroAfiliado = Entry(frameCampos, width=25)
cuadroAfiliado.grid(row=5, column=1, padx=5, pady=3)

# Fila 6: Asignación de Turno
Label(frameCampos, text="Especialidad:").grid(
    row=6, column=0, sticky="e", padx=5, pady=3
)
comboEspecialidad = ttk.Combobox(
    frameCampos,
    values=[
        "Pediatría",
        "Traumatología",
        "Cardiología",
        "Dermatología",
        "Clínica Médica",
    ],
    width=22,
    state="readonly",
)
comboEspecialidad.grid(row=6, column=1, padx=5, pady=3)

Label(frameCampos, text="Médico:").grid(row=6, column=2, sticky="e", padx=5, pady=3)
comboMedico = ttk.Combobox(
    frameCampos,
    values=[
        "Dr. Gómez",
        "Dra. Rodríguez",
        "Dr. Fernández",
        "Dra. López",
        "Dr. Pérez",
    ],
    width=23,
    state="readonly",
)
comboMedico.grid(row=6, column=3, padx=5, pady=3)

# Fila 7: Fecha (Día/Mes/Año desplegables)
Label(frameCampos, text="Fecha Turno (D/M/A):").grid(
    row=7, column=0, sticky="e", padx=5, pady=3
)

frameFecha = Frame(frameCampos)
frameFecha.grid(row=7, column=1, sticky="w", padx=5, pady=3)

dias = [f"{i:02d}" for i in range(1, 32)]
meses = [f"{i:02d}" for i in range(1, 13)]
anio_actual = datetime.now().year
anios = [str(a) for a in range(anio_actual, anio_actual + 2)]

comboDia = ttk.Combobox(frameFecha, values=dias, width=3, state="readonly")
comboDia.pack(side="left", padx=1)

comboMes = ttk.Combobox(frameFecha, values=meses, width=3, state="readonly")
comboMes.pack(side="left", padx=1)

comboAnio = ttk.Combobox(frameFecha, values=anios, width=5, state="readonly")
comboAnio.pack(side="left", padx=1)

# Fila 7: Horario
Label(frameCampos, text="Hora Turno:").grid(
    row=7, column=2, sticky="e", padx=5, pady=3
)
comboHoraTurno = ttk.Combobox(
    frameCampos,
    values=[
        "08:00",
        "08:30",
        "09:00",
        "09:30",
        "10:00",
        "10:30",
        "11:00",
        "14:00",
        "14:30",
        "15:00",
    ],
    width=23,
    state="readonly",
)
comboHoraTurno.grid(row=7, column=3, padx=5, pady=3)

# Botones
frameBotones = Frame(root)
frameBotones.pack(pady=10)

Button(frameBotones, text="Conectar BD", command=Base_de_Datos).grid(
    row=0, column=0, padx=5
)
Button(frameBotones, text="Alta", command=Alta).grid(row=0, column=1, padx=5)
Button(frameBotones, text="Modificar", command=Modificar).grid(
    row=0, column=2, padx=5
)
Button(frameBotones, text="Baja", command=Baja).grid(row=0, column=3, padx=5)
Button(frameBotones, text="Limpiar Campos", command=limpiar_campos).grid(
    row=0, column=4, padx=5
)
Button(frameBotones, text="Salir", command=Salir).grid(row=0, column=5, padx=5)

# Listado Tabla (Treeview)
frameTabla = Frame(root)
frameTabla.pack(pady=10, fill="both", expand=True, padx=20)

columnas = ("ID", "Nombre", "Apellido", "Especialidad", "Fecha", "Hora")
tabla_listado = ttk.Treeview(
    frameTabla, columns=columnas, show="headings", height=8
)

for col in columnas:
    tabla_listado.heading(col, text=col)
    tabla_listado.column(col, width=110, anchor="center")

scrollbar = Scrollbar(frameTabla, orient="vertical", command=tabla_listado.yview)
tabla_listado.configure(yscrollcommand=scrollbar.set)

tabla_listado.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

# Evento Doble Clic
tabla_listado.bind("<Double-1>", al_hacer_doble_click)

root.mainloop()