import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk

# --- 1. BASE DE DATOS Y LÓGICA DE NEGOCIO ---


def inicializar_db():
    conexion = sqlite3.connect("inmobiliaria.db")
    cursor = conexion.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS propiedades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            direccion TEXT NOT NULL,
            localidad TEXT,
            entre_calles TEXT,
            piso TEXT,
            depto TEXT,
            tipo TEXT NOT NULL,
            ambientes INTEGER NOT NULL,
            precio REAL NOT NULL,
            estado TEXT NOT NULL,
            descripcion TEXT,
            prop_nombre TEXT,
            prop_apellido TEXT,
            prop_dni TEXT,
            prop_telefono TEXT,
            prop_direccion TEXT,
            inq_nombre TEXT,
            inq_dni TEXT,
            inq_telefono TEXT,
            tipo_garantia TEXT,
            garantia_detalle TEXT
        )
    """
    )
    conexion.commit()

    cursor.execute("PRAGMA table_info(propiedades)")
    columnas_existentes = [col[1] for col in cursor.fetchall()]

    columnas_requeridas = [
        ("localidad", "TEXT"),
        ("entre_calles", "TEXT"),
        ("piso", "TEXT"),
        ("depto", "TEXT"),
        ("descripcion", "TEXT"),
        ("prop_nombre", "TEXT"),
        ("prop_apellido", "TEXT"),
        ("prop_dni", "TEXT"),
        ("prop_telefono", "TEXT"),
        ("prop_direccion", "TEXT"),
        ("inq_nombre", "TEXT"),
        ("inq_dni", "TEXT"),
        ("inq_telefono", "TEXT"),
        ("tipo_garantia", "TEXT"),
        ("garantia_detalle", "TEXT"),
    ]

    for col_nombre, col_tipo in columnas_requeridas:
        if col_nombre not in columnas_existentes:
            cursor.execute(
                f"ALTER TABLE propiedades ADD COLUMN {col_nombre} {col_tipo}"
            )

    conexion.commit()
    conexion.close()


def agregar_propiedad_db(datos):
    conexion = sqlite3.connect("inmobiliaria.db")
    cursor = conexion.cursor()
    cursor.execute(
        """
        INSERT INTO propiedades (
            direccion, localidad, entre_calles, piso, depto, tipo, ambientes, precio, estado, descripcion,
            prop_nombre, prop_apellido, prop_dni, prop_telefono, prop_direccion,
            inq_nombre, inq_dni, inq_telefono,
            tipo_garantia, garantia_detalle
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        datos,
    )
    conexion.commit()
    conexion.close()


def obtener_propiedades_resumen_db(filtro="Todos"):
    conexion = sqlite3.connect("inmobiliaria.db")
    cursor = conexion.cursor()

    query = "SELECT id, direccion, localidad, piso, depto, tipo, ambientes, precio, estado FROM propiedades"

    if filtro == "Solo Disponibles":
        query += " WHERE estado IN ('Venta', 'Alquiler')"
        cursor.execute(query)
    elif filtro != "Todos":
        query += " WHERE estado = ?"
        cursor.execute(query, (filtro,))
    else:
        cursor.execute(query)

    filas = cursor.fetchall()
    conexion.close()
    return filas


def obtener_propiedad_completa_db(prop_id):
    conexion = sqlite3.connect("inmobiliaria.db")
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM propiedades WHERE id = ?", (prop_id,))
    fila = cursor.fetchone()
    conexion.close()
    return fila


def actualizar_estado_db(prop_id, nuevo_estado):
    conexion = sqlite3.connect("inmobiliaria.db")
    cursor = conexion.cursor()
    cursor.execute(
        "UPDATE propiedades SET estado = ? WHERE id = ?",
        (nuevo_estado, prop_id),
    )
    conexion.commit()
    conexion.close()


def eliminar_propiedad_db(prop_id):
    conexion = sqlite3.connect("inmobiliaria.db")
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM propiedades WHERE id = ?", (prop_id,))
    conexion.commit()
    conexion.close()


# --- 2. INTERFAZ GRÁFICA (TKINTER) ---


class InmobiliariaApp:

    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Gestión Inmobiliaria")
        self.root.geometry("1020x820")

        # --- CONTENEDOR 1: LISTADO PRINCIPAL (PRIORITARIO) ---
        frame_listado = tk.LabelFrame(
            self.root,
            text=" 🏢 Listado de Propiedades ",
            padx=10,
            pady=8,
            font=("Arial", 10, "bold"),
        )
        frame_listado.pack(fill="both", expand=True, padx=15, pady=(10, 5))

        # BARRA DE FILTROS Y AYUDA
        frame_controles = tk.Frame(frame_listado)
        frame_controles.pack(fill="x", pady=(0, 5))

        tk.Label(
            frame_controles,
            text="Filtrar por Estado:",
            font=("Arial", 9, "bold"),
        ).pack(side=tk.LEFT, padx=(0, 5))

        self.combo_filtro = ttk.Combobox(
            frame_controles,
            values=[
                "Todos",
                "Solo Disponibles",
                "Venta",
                "Alquiler",
                "Reservado",
                "Vendido",
                "Alquilado",
            ],
            state="readonly",
            width=18,
        )
        self.combo_filtro.set("Todos")
        self.combo_filtro.pack(side=tk.LEFT, padx=5)
        self.combo_filtro.bind(
            "<<ComboboxSelected>>", lambda e: self.cargar_datos()
        )

        lbl_instruccion = tk.Label(
            frame_controles,
            text="💡 Haz DOBLE CLIC en una fila para ver todos sus datos específicos.",
            fg="#1565C0",
            font=("Arial", 9, "bold"),
        )
        lbl_instruccion.pack(side=tk.RIGHT, padx=5)

        # TABLA DE VISUALIZACIÓN
        frame_tabla = tk.Frame(frame_listado)
        frame_tabla.pack(fill="both", expand=True, pady=5)

        columnas = (
            "id",
            "direccion_completa",
            "localidad",
            "tipo",
            "ambientes",
            "precio",
            "estado",
        )
        self.tabla = ttk.Treeview(
            frame_tabla, columns=columnas, show="headings"
        )

        self.tabla.heading("id", text="ID")
        self.tabla.heading("direccion_completa", text="Dirección")
        self.tabla.heading("localidad", text="Localidad")
        self.tabla.heading("tipo", text="Tipo")
        self.tabla.heading("ambientes", text="Amb")
        self.tabla.heading("precio", text="Precio")
        self.tabla.heading("estado", text="Estado")

        self.tabla.column("id", width=40, anchor="center")
        self.tabla.column("direccion_completa", width=250)
        self.tabla.column("localidad", width=120)
        self.tabla.column("tipo", width=90, anchor="center")
        self.tabla.column("ambientes", width=45, anchor="center")
        self.tabla.column("precio", width=120, anchor="e")
        self.tabla.column("estado", width=100, anchor="center")

        scrollbar_tabla = ttk.Scrollbar(
            frame_tabla, orient="vertical", command=self.tabla.yview
        )
        self.tabla.configure(yscrollcommand=scrollbar_tabla.set)

        self.tabla.pack(side=tk.LEFT, fill="both", expand=True)
        scrollbar_tabla.pack(side=tk.RIGHT, fill="y")

        self.tabla.bind("<Double-1>", self.abrir_ficha_completa)

        # BARRAS DE ACCIONES RÁPIDAS (ESTADOS)
        frame_acciones = ttk.Frame(frame_listado)
        frame_acciones.pack(fill="x", pady=(5, 0))

        tk.Label(
            frame_acciones, text="Cambiar Estado:", font=("Arial", 9, "bold")
        ).pack(side=tk.LEFT, padx=(0, 5))

        btn_venta = ttk.Button(
            frame_acciones,
            text="Marcar 'En Venta'",
            command=lambda: self.gestionar_seleccionado("Venta"),
        )
        btn_venta.pack(side=tk.LEFT, padx=3)

        btn_alquiler = ttk.Button(
            frame_acciones,
            text="Marcar 'En Alquiler'",
            command=lambda: self.gestionar_seleccionado("Alquiler"),
        )
        btn_alquiler.pack(side=tk.LEFT, padx=3)

        btn_reservado = ttk.Button(
            frame_acciones,
            text="Marcar 'Reservado'",
            command=lambda: self.gestionar_seleccionado("Reservado"),
        )
        btn_reservado.pack(side=tk.LEFT, padx=3)

        btn_vendido = ttk.Button(
            frame_acciones,
            text="Marcar 'Vendido'",
            command=lambda: self.gestionar_seleccionado("Vendido"),
        )
        btn_vendido.pack(side=tk.LEFT, padx=3)

        btn_alquilado = ttk.Button(
            frame_acciones,
            text="Marcar 'Alquilado'",
            command=lambda: self.gestionar_seleccionado("Alquilado"),
        )
        btn_alquilado.pack(side=tk.LEFT, padx=3)

        btn_eliminar = ttk.Button(
            frame_acciones,
            text="Eliminar Inmueble",
            command=lambda: self.gestionar_seleccionado("Eliminar"),
        )
        btn_eliminar.pack(side=tk.RIGHT, padx=3)

        # --- CONTENEDOR 2: FORMULARIO DE REGISTRO ---
        frame_ficha = tk.LabelFrame(
            self.root,
            text=" ➕ Registrar Nueva Propiedad ",
            padx=10,
            pady=5,
            font=("Arial", 10, "bold"),
        )
        frame_ficha.pack(fill="x", padx=15, pady=(5, 10))

        # SECCIÓN INMUEBLE
        tk.Label(frame_ficha, text="Calle/Dirección:").grid(
            row=0, column=0, sticky="w"
        )
        self.entry_direccion = tk.Entry(frame_ficha, width=22)
        self.entry_direccion.grid(row=0, column=1, sticky="w", pady=2)

        tk.Label(frame_ficha, text="Localidad:").grid(
            row=0, column=2, sticky="w", padx=(10, 0)
        )
        self.entry_localidad = tk.Entry(frame_ficha, width=18)
        self.entry_localidad.grid(row=0, column=3, sticky="w", pady=2)

        tk.Label(frame_ficha, text="Entre calles:").grid(
            row=0, column=4, sticky="w", padx=(10, 0)
        )
        self.entry_entre_calles = tk.Entry(frame_ficha, width=20)
        self.entry_entre_calles.grid(row=0, column=5, sticky="w", pady=2)

        tk.Label(frame_ficha, text="Tipo Inmueble:").grid(
            row=1, column=0, sticky="w"
        )
        self.combo_tipo = ttk.Combobox(
            frame_ficha,
            values=["Casa", "Departamento", "PH", "Terreno", "Local"],
            state="readonly",
            width=15,
        )
        self.combo_tipo.grid(row=1, column=1, sticky="w", pady=2)
        self.combo_tipo.current(0)
        self.combo_tipo.bind(
            "<<ComboboxSelected>>", self.actualizar_campos_tipo
        )

        tk.Label(frame_ficha, text="Piso:").grid(
            row=1, column=2, sticky="w", padx=(10, 0)
        )
        self.entry_piso = tk.Entry(frame_ficha, width=8)
        self.entry_piso.grid(row=1, column=3, sticky="w", pady=2)

        tk.Label(frame_ficha, text="Depto:").grid(
            row=1, column=4, sticky="w", padx=(10, 0)
        )
        self.entry_depto = tk.Entry(frame_ficha, width=8)
        self.entry_depto.grid(row=1, column=5, sticky="w", pady=2)

        tk.Label(frame_ficha, text="Ambientes:").grid(
            row=2, column=0, sticky="w"
        )
        self.entry_ambientes = tk.Entry(frame_ficha, width=8)
        self.entry_ambientes.grid(row=2, column=1, sticky="w", pady=2)

        tk.Label(frame_ficha, text="Estado:").grid(
            row=2, column=2, sticky="w", padx=(10, 0)
        )
        self.combo_estado = ttk.Combobox(
            frame_ficha,
            values=["Venta", "Alquiler", "Reservado", "Vendido", "Alquilado"],
            state="readonly",
            width=12,
        )
        self.combo_estado.grid(row=2, column=3, sticky="w", pady=2)
        self.combo_estado.current(0)
        self.combo_estado.bind(
            "<<ComboboxSelected>>", self.actualizar_label_precio
        )

        self.lbl_precio = tk.Label(
            frame_ficha,
            text="Precio (USD):",
            font=("Arial", 9, "bold"),
            fg="#2E7D32",
        )
        self.lbl_precio.grid(row=2, column=4, sticky="w", padx=(10, 0))
        self.entry_precio = tk.Entry(frame_ficha, width=15)
        self.entry_precio.grid(row=2, column=5, sticky="w", pady=2)

        tk.Label(frame_ficha, text="Descripción:").grid(
            row=3, column=0, sticky="nw", pady=2
        )
        self.txt_descripcion = tk.Text(frame_ficha, width=70, height=2)
        self.txt_descripcion.grid(
            row=3, column=1, columnspan=5, sticky="w", pady=2
        )

        # DATOS DE PROPIETARIO E INQUILINO SIMPLIFICADOS EN REGISTRO
        ttk.Separator(frame_ficha, orient="horizontal").grid(
            row=4, column=0, columnspan=6, sticky="ew", pady=4
        )

        tk.Label(
            frame_ficha,
            text="Propietario -> Nombre:",
            font=("Arial", 8, "bold"),
        ).grid(row=5, column=0, sticky="w")
        self.entry_prop_nombre = tk.Entry(frame_ficha, width=18)
        self.entry_prop_nombre.grid(row=5, column=1, sticky="w")

        tk.Label(frame_ficha, text="Apellido:").grid(
            row=5, column=2, sticky="w", padx=(10, 0)
        )
        self.entry_prop_apellido = tk.Entry(frame_ficha, width=15)
        self.entry_prop_apellido.grid(row=5, column=3, sticky="w")

        tk.Label(frame_ficha, text="Tel/Contacto:").grid(
            row=5, column=4, sticky="w", padx=(10, 0)
        )
        self.entry_prop_telefono = tk.Entry(frame_ficha, width=15)
        self.entry_prop_telefono.grid(row=5, column=5, sticky="w")

        # CAMPOS ADICIONALES OCULTOS DE SOPORTE DB
        self.entry_prop_dni = tk.Entry(frame_ficha)
        self.entry_prop_direccion = tk.Entry(frame_ficha)
        self.entry_inq_nombre = tk.Entry(frame_ficha)
        self.entry_inq_dni = tk.Entry(frame_ficha)
        self.entry_inq_telefono = tk.Entry(frame_ficha)
        self.combo_garantia = ttk.Combobox(
            frame_ficha,
            values=["Ninguna", "Garantía Propietaria", "Seguro de Caución"],
        )
        self.combo_garantia.set("Ninguna")
        self.entry_garantia_detalle = tk.Entry(frame_ficha)

        btn_guardar = tk.Button(
            frame_ficha,
            text=" Registrar Propiedad ",
            bg="#2196F3",
            fg="white",
            font=("Arial", 9, "bold"),
            command=self.guardar_propiedad,
        )
        btn_guardar.grid(row=6, column=0, columnspan=6, pady=6)

        self.actualizar_campos_tipo()
        self.cargar_datos()

    def actualizar_label_precio(self, event=None):
        estado = self.combo_estado.get()
        if estado in ["Alquiler", "Alquilado"]:
            self.lbl_precio.config(
                text="Precio/Mes ($):", fg="#E65100"
            )  # Pesos para Alquiler
        else:
            self.lbl_precio.config(
                text="Precio (USD):", fg="#2E7D32"
            )  # Dólares para Venta/Reserva

    def actualizar_campos_tipo(self, event=None):
        tipo = self.combo_tipo.get()
        if tipo == "Departamento":
            self.entry_piso.config(state="normal")
            self.entry_depto.config(state="normal")
        elif tipo == "PH":
            self.entry_piso.delete(0, tk.END)
            self.entry_piso.config(state="disabled")
            self.entry_depto.config(state="normal")
        else:
            self.entry_piso.delete(0, tk.END)
            self.entry_depto.delete(0, tk.END)
            self.entry_piso.config(state="disabled")
            self.entry_depto.config(state="disabled")

    def guardar_propiedad(self):
        direccion = self.entry_direccion.get().strip()
        tipo = self.combo_tipo.get()
        ambientes = self.entry_ambientes.get().strip()
        precio_str = self.entry_precio.get().strip()

        if not direccion or not ambientes or not precio_str:
            messagebox.showwarning(
                "Atención", "Dirección, Ambientes y Precio son obligatorios."
            )
            return

        try:
            ambientes = int(ambientes)
            precio = float(precio_str.replace(",", "."))
        except ValueError:
            messagebox.showerror(
                "Error",
                "Ambientes debe ser un número entero y Precio un número válido.",
            )
            return

        datos = (
            direccion,
            self.entry_localidad.get().strip(),
            self.entry_entre_calles.get().strip(),
            self.entry_piso.get().strip()
            if self.entry_piso["state"] == "normal"
            else "",
            self.entry_depto.get().strip()
            if self.entry_depto["state"] == "normal"
            else "",
            tipo,
            ambientes,
            precio,
            self.combo_estado.get(),
            self.txt_descripcion.get("1.0", tk.END).strip(),
            self.entry_prop_nombre.get().strip(),
            self.entry_prop_apellido.get().strip(),
            self.entry_prop_dni.get().strip(),
            self.entry_prop_telefono.get().strip(),
            self.entry_prop_direccion.get().strip(),
            self.entry_inq_nombre.get().strip(),
            self.entry_inq_dni.get().strip(),
            self.entry_inq_telefono.get().strip(),
            self.combo_garantia.get(),
            self.entry_garantia_detalle.get().strip(),
        )

        try:
            agregar_propiedad_db(datos)
            messagebox.showinfo("Éxito", "Propiedad registrada correctamente.")
            self.limpiar_formulario()
            self.cargar_datos()
        except Exception as e:
            messagebox.showerror(
                "Error de Base de Datos",
                f"No se pudo guardar la propiedad: {str(e)}",
            )

    def limpiar_formulario(self):
        self.entry_direccion.delete(0, tk.END)
        self.entry_localidad.delete(0, tk.END)
        self.entry_entre_calles.delete(0, tk.END)
        self.entry_piso.delete(0, tk.END)
        self.entry_depto.delete(0, tk.END)
        self.entry_ambientes.delete(0, tk.END)
        self.entry_precio.delete(0, tk.END)
        self.txt_descripcion.delete("1.0", tk.END)
        self.entry_prop_nombre.delete(0, tk.END)
        self.entry_prop_apellido.delete(0, tk.END)
        self.entry_prop_telefono.delete(0, tk.END)
        self.actualizar_campos_tipo()
        self.actualizar_label_precio()

    def cargar_datos(self):
        try:
            for item in self.tabla.get_children():
                self.tabla.delete(item)

            filtro = self.combo_filtro.get()
            registros = obtener_propiedades_resumen_db(filtro)

            for row in registros:
                id_p, dir_p, loc, piso, depto, tipo, amb, precio, estado = row

                ubicacion = dir_p if dir_p else ""
                if piso and depto:
                    ubicacion += f" {piso}° '{depto}'"
                elif depto:
                    ubicacion += f" Depto {depto}"

                # Formateo de Moneda según tipo de operación
                if estado in ["Alquiler", "Alquilado"]:
                    precio_fmt = f"$ {precio:,.2f}/mes"
                else:
                    precio_fmt = f"USD {precio:,.2f}"

                self.tabla.insert(
                    "",
                    tk.END,
                    values=(
                        id_p,
                        ubicacion,
                        loc if loc else "-",
                        tipo,
                        amb,
                        precio_fmt,
                        estado,
                    ),
                )
        except Exception as e:
            messagebox.showerror(
                "Error", f"Ocurrió un error al cargar el listado: {str(e)}"
            )

    def gestionar_seleccionado(self, accion):
        seleccion = self.tabla.selection()
        if not seleccion:
            messagebox.showwarning(
                "Atención",
                "Por favor, seleccioná una propiedad de la lista primero.",
            )
            return

        item = self.tabla.item(seleccion[0])
        id_inmueble = item["values"][0]

        try:
            if accion in [
                "Venta",
                "Alquiler",
                "Reservado",
                "Vendido",
                "Alquilado",
            ]:
                actualizar_estado_db(id_inmueble, accion)
                messagebox.showinfo(
                    "Éxito", f"Estado actualizado a '{accion}' correctamente."
                )
            elif accion == "Eliminar":
                confirmar = messagebox.askyesno(
                    "Confirmar Eliminación",
                    f"¿Seguro que deseas eliminar definitivamente el inmueble ID {id_inmueble}?",
                )
                if confirmar:
                    eliminar_propiedad_db(id_inmueble)
                    messagebox.showinfo(
                        "Éxito", "Inmueble eliminado correctamente."
                    )

            self.cargar_datos()
        except Exception as e:
            messagebox.showerror(
                "Error", f"No se pudo completar la operación: {str(e)}"
            )

    def abrir_ficha_completa(self, event):
        item_seleccionado = self.tabla.selection()
        if not item_seleccionado:
            return

        try:
            prop_id = self.tabla.item(item_seleccionado)["values"][0]
            p = obtener_propiedad_completa_db(prop_id)

            if not p:
                messagebox.showerror(
                    "Error", "No se encontraron los datos de la propiedad."
                )
                return

            # Ventana desplegable específica
            win = tk.Toplevel(self.root)
            win.title(f"Ficha Completa Especifica - Propiedad #{p[0]}")
            win.geometry("540x660")
            win.configure(bg="#F4F6F9")
            win.grab_set()

            canvas = tk.Canvas(win, bg="#F4F6F9", highlightthickness=0)
            scrollbar = ttk.Scrollbar(
                win, orient="vertical", command=canvas.yview
            )
            scrollable_frame = tk.Frame(canvas, bg="#F4F6F9")

            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
            )
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)

            canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
            scrollbar.pack(side="right", fill="y")

            def crear_tarjeta(titulo, color_borde, campos):
                card = tk.LabelFrame(
                    scrollable_frame,
                    text=f" {titulo} ",
                    font=("Arial", 10, "bold"),
                    fg=color_borde,
                    bg="white",
                    bd=1,
                    relief="solid",
                    padx=10,
                    pady=8,
                )
                card.pack(fill="x", expand=True, pady=6)

                for i, (campo, valor) in enumerate(campos):
                    val_txt = str(valor).strip() if valor else "-"
                    lbl_key = tk.Label(
                        card,
                        text=f"{campo}:",
                        font=("Arial", 9, "bold"),
                        bg="white",
                        fg="#444",
                        anchor="w",
                    )
                    lbl_key.grid(row=i, column=0, sticky="nw", pady=2)

                    lbl_val = tk.Label(
                        card,
                        text=val_txt,
                        font=("Arial", 9),
                        bg="white",
                        fg="#111",
                        anchor="w",
                        justify="left",
                        wraplength=340,
                    )
                    lbl_val.grid(
                        row=i, column=1, sticky="w", pady=2, padx=(10, 0)
                    )

            ubica = p[1] if p[1] else ""
            if p[4] and p[5]:
                ubica += f" Piso {p[4]}° Depto '{p[5]}'"
            elif p[5]:
                ubica += f" Depto {p[5]}"

            # Moneda según estado de la propiedad
            precio_val = p[8] if p[8] is not None else 0.0
            if p[9] in ["Alquiler", "Alquilado"]:
                precio_mostrar = f"$ {precio_val:,.2f} / mes (AR$)"
            else:
                precio_mostrar = f"USD {precio_val:,.2f} (Dólares)"

            datos_inmueble = [
                ("Dirección", ubica),
                ("Localidad", p[2]),
                ("Entre Calles", p[3]),
                ("Tipo Inmueble", p[6]),
                ("Ambientes", p[7]),
                ("Valor / Precio", precio_mostrar),
                ("Estado Operación", p[9]),
                ("Descripción / Notas", p[10]),
            ]
            crear_tarjeta(
                "📍 DATOS ESPECÍFICOS DEL INMUEBLE", "#1565C0", datos_inmueble
            )

            nombre_prop = f"{p[11]} {p[12]}".strip()
            datos_prop = [
                ("Nombre Completo", nombre_prop if nombre_prop else "-"),
                ("DNI", p[13]),
                ("Teléfono", p[14]),
                ("Dirección Particular", p[15]),
            ]
            crear_tarjeta("👤 DATOS DEL PROPIETARIO", "#2E7D32", datos_prop)

            datos_inq = [
                ("Nombre Inquilino", p[16]),
                ("DNI Inquilino", p[17]),
                ("Teléfono Contacto", p[18]),
            ]
            crear_tarjeta(
                "🔑 DATOS DEL INQUILINO (SI APLICA)", "#E65100", datos_inq
            )

            datos_garantia = [
                ("Tipo de Garantía", p[19]),
                ("Detalles / Compañía", p[20]),
            ]
            crear_tarjeta("🛡️ GARANTÍA Y CAUCIÓN", "#6A1B9A", datos_garantia)

            btn_cerrar = tk.Button(
                scrollable_frame,
                text="Cerrar Ficha",
                command=win.destroy,
                bg="#757575",
                fg="white",
                font=("Arial", 9, "bold"),
                width=15,
            )
            btn_cerrar.pack(pady=10)

        except Exception as e:
            messagebox.showerror(
                "Error", f"No se pudo abrir la ficha detallada: {str(e)}"
            )


# --- 3. EJECUCIÓN DEL SISTEMA ---
if __name__ == "__main__":
    try:
        inicializar_db()
        root = tk.Tk()
        app = InmobiliariaApp(root)
        root.mainloop()
    except Exception as e:
        print(f"Error fatal al iniciar la aplicación: {e}")