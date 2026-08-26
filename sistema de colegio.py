import sqlite3
from typing import List, Optional
import tkinter as tk
from tkinter import ttk, messagebox


# ==========================================
# 1. BASE DE DATOS Y CAPA DE PERSISTENCIA
# ==========================================

class SchoolDatabaseManager:
    def __init__(self, db_name: str = "BD_Escuela.db"):
        self.db_name = db_name
        self._reset_database()
        self._create_tables()
        self._seed_initial_data()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        return conn

    def _reset_database(self) -> None:
        """Borra las tablas existentes para reiniciar toda la base de datos desde cero."""
        with self._get_connection() as conn:
            conn.executescript("""
            DROP TABLE IF EXISTS calificaciones;
            DROP TABLE IF EXISTS alumnos;
            DROP TABLE IF EXISTS cursos;
            """)

    def _create_tables(self) -> None:
        """Crea la estructura de tablas relacionales desde cero."""
        with self._get_connection() as conn:
            conn.executescript("""
            CREATE TABLE IF NOT EXISTS cursos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL UNIQUE
            );

            CREATE TABLE IF NOT EXISTS alumnos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                curso_id INTEGER NOT NULL,
                nombre TEXT NOT NULL,
                apellido TEXT NOT NULL,
                direccion TEXT,
                fecha_nacimiento TEXT,
                contacto TEXT,
                contacto_alt TEXT,
                email TEXT,
                FOREIGN KEY (curso_id) REFERENCES cursos (id)
            );

            CREATE TABLE IF NOT EXISTS calificaciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alumno_id INTEGER NOT NULL,
                materia TEXT NOT NULL,
                tp1 REAL DEFAULT 0.0,
                tp2 REAL DEFAULT 0.0,
                eval1 REAL DEFAULT 0.0,
                eval2 REAL DEFAULT 0.0,
                FOREIGN KEY (alumno_id) REFERENCES alumnos (id)
            );
            """)

    def _seed_initial_data(self) -> None:
        """Puebla desde cero los 7 años con divisiones (A, B, C, D). Total: 28 cursos."""
        with self._get_connection() as conn:
            divisiones = ["A", "B", "C", "D"]
            lista_cursos = []

            for año in range(1, 8):
                for div in divisiones:
                    lista_cursos.append((f"{año}° Año {div}",))

            conn.executemany(
                "INSERT INTO cursos (nombre) VALUES (?)",
                lista_cursos
            )

    def fetch_cursos(self) -> List[sqlite3.Row]:
        with self._get_connection() as conn:
            return conn.execute("SELECT * FROM cursos ORDER BY id").fetchall()

    def fetch_alumnos_by_curso(self, curso_id: int, query_text: str = "") -> List[sqlite3.Row]:
        with self._get_connection() as conn:
            if query_text:
                q = f"%{query_text}%"
                return conn.execute(
                    """SELECT id, apellido, nombre, email, contacto
                       FROM alumnos
                       WHERE curso_id = ? AND (nombre LIKE ? OR apellido LIKE ?)
                       ORDER BY apellido, nombre""",
                    (curso_id, q, q)
                ).fetchall()
            else:
                return conn.execute(
                    "SELECT id, apellido, nombre, email, contacto FROM alumnos WHERE curso_id = ? ORDER BY apellido, nombre",
                    (curso_id,)
                ).fetchall()

    def search_alumnos_global(self, query_text: str) -> List[sqlite3.Row]:
        """Busca alumnos en TODOS los cursos en tiempo real."""
        with self._get_connection() as conn:
            q = f"%{query_text}%"
            return conn.execute(
                """SELECT a.id, a.apellido, a.nombre, a.email, a.contacto, c.nombre as curso_nombre
                   FROM alumnos a
                   JOIN cursos c ON a.curso_id = c.id
                   WHERE a.nombre LIKE ? OR a.apellido LIKE ?
                   ORDER BY a.apellido, a.nombre""",
                (q, q)
            ).fetchall()

    def get_alumno_detail(self, alumno_id: int) -> Optional[sqlite3.Row]:
        with self._get_connection() as conn:
            return conn.execute("SELECT * FROM alumnos WHERE id = ?", (alumno_id,)).fetchone()

    def save_or_update_alumno(self, data: dict) -> int:
        with self._get_connection() as conn:
            if data.get("id"):
                query = """
                UPDATE alumnos SET curso_id=?, nombre=?, apellido=?, direccion=?,
                fecha_nacimiento=?, contacto=?, contacto_alt=?, email=? WHERE id=?
                """
                conn.execute(query, (
                    data["curso_id"], data["nombre"], data["apellido"], data["direccion"],
                    data["fecha_nacimiento"], data["contacto"], data["contacto_alt"], data["email"], data["id"]
                ))
                return data["id"]
            else:
                query = """
                INSERT INTO alumnos (curso_id, nombre, apellido, direccion, fecha_nacimiento, contacto, contacto_alt, email)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """
                cursor = conn.execute(query, (
                    data["curso_id"], data["nombre"], data["apellido"], data["direccion"],
                    data["fecha_nacimiento"], data["contacto"], data["contacto_alt"], data["email"]
                ))
                return cursor.lastrowid

    def delete_alumno(self, alumno_id: int) -> None:
        with self._get_connection() as conn:
            conn.execute("DELETE FROM calificaciones WHERE alumno_id = ?", (alumno_id,))
            conn.execute("DELETE FROM alumnos WHERE id = ?", (alumno_id,))

    def fetch_calificaciones(self, alumno_id: int) -> List[sqlite3.Row]:
        with self._get_connection() as conn:
            return conn.execute("SELECT * FROM calificaciones WHERE alumno_id = ?", (alumno_id,)).fetchall()

    def save_or_update_calificacion(self, alumno_id: int, materia: str, tp1: float, tp2: float, eval1: float, eval2: float) -> None:
        with self._get_connection() as conn:
            row = conn.execute("SELECT id FROM calificaciones WHERE alumno_id = ? AND materia = ?", (alumno_id, materia)).fetchone()
            if row:
                conn.execute(
                    "UPDATE calificaciones SET tp1=?, tp2=?, eval1=?, eval2=? WHERE id=?",
                    (tp1, tp2, eval1, eval2, row["id"])
                )
            else:
                conn.execute(
                    "INSERT INTO calificaciones (alumno_id, materia, tp1, tp2, eval1, eval2) VALUES (?, ?, ?, ?, ?, ?)",
                    (alumno_id, materia, tp1, tp2, eval1, eval2)
                )


# ==========================================
# 2. VENTANA DETALLE / EDICIÓN DE ALUMNO
# ==========================================

class StudentDetailDialog(tk.Toplevel):
    def __init__(self, parent, db_manager: SchoolDatabaseManager, alumno_id: Optional[int] = None, current_curso_id: Optional[int] = None):
        super().__init__(parent)
        self.db = db_manager
        self.alumno_id = alumno_id
        self.current_curso_id = current_curso_id

        self.title("Ficha del Alumno" if alumno_id else "Nuevo Alumno")
        self.geometry("750x550")
        self.grab_set()

        self._create_widgets()
        if self.alumno_id:
            self._load_alumno_data()
            self._load_calificaciones()

    def _create_widgets(self):
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Tab 1: Datos Personales
        tab_personal = ttk.Frame(notebook, padding=15)
        notebook.add(tab_personal, text="Datos Personales")

        self.var_nombre = tk.StringVar()
        self.var_apellido = tk.StringVar()
        self.var_direccion = tk.StringVar()
        self.var_fnac = tk.StringVar()
        self.var_contacto = tk.StringVar()
        self.var_contacto_alt = tk.StringVar()
        self.var_email = tk.StringVar()
        self.var_curso = tk.StringVar()

        self.cursos_dict = {row["nombre"]: row["id"] for row in self.db.fetch_cursos()}

        ttk.Label(tab_personal, text="Curso (1° a 7° y Div):").grid(row=0, column=0, sticky="w", pady=5)
        self.cb_curso = ttk.Combobox(
            tab_personal,
            values=list(self.cursos_dict.keys()),
            textvariable=self.var_curso,
            state="readonly",
            width=22
        )
        self.cb_curso.grid(row=0, column=1, sticky="w", pady=5)

        if self.current_curso_id:
            for k, v in self.cursos_dict.items():
                if v == self.current_curso_id:
                    self.var_curso.set(k)

        ttk.Label(tab_personal, text="Nombre:").grid(row=1, column=0, sticky="w", pady=5)
        ttk.Entry(tab_personal, textvariable=self.var_nombre).grid(row=1, column=1, sticky="ew", pady=5)

        ttk.Label(tab_personal, text="Apellido:").grid(row=1, column=2, sticky="w", padx=(10, 0), pady=5)
        ttk.Entry(tab_personal, textvariable=self.var_apellido).grid(row=1, column=3, sticky="ew", pady=5)

        ttk.Label(tab_personal, text="Dirección:").grid(row=2, column=0, sticky="w", pady=5)
        ttk.Entry(tab_personal, textvariable=self.var_direccion).grid(row=2, column=1, columnspan=3, sticky="ew", pady=5)

        ttk.Label(tab_personal, text="F. Nacimiento:").grid(row=3, column=0, sticky="w", pady=5)
        ttk.Entry(tab_personal, textvariable=self.var_fnac).grid(row=3, column=1, sticky="ew", pady=5)

        ttk.Label(tab_personal, text="Correo Electrónico:").grid(row=3, column=2, sticky="w", padx=(10, 0), pady=5)
        ttk.Entry(tab_personal, textvariable=self.var_email).grid(row=3, column=3, sticky="ew", pady=5)

        ttk.Label(tab_personal, text="Teléfono Contacto:").grid(row=4, column=0, sticky="w", pady=5)
        ttk.Entry(tab_personal, textvariable=self.var_contacto).grid(row=4, column=1, sticky="ew", pady=5)

        ttk.Label(tab_personal, text="Contacto Alternativo:").grid(row=4, column=2, sticky="w", padx=(10, 0), pady=5)
        ttk.Entry(tab_personal, textvariable=self.var_contacto_alt).grid(row=4, column=3, sticky="ew", pady=5)

        ttk.Button(tab_personal, text="Guardar Datos", command=self.on_save_personal).grid(row=5, column=3, sticky="e", pady=15)

        # Tab 2: Calificaciones y Materias
        tab_notas = ttk.Frame(notebook, padding=15)
        notebook.add(tab_notas, text="Materias y Calificaciones")

        frame_materia = ttk.LabelFrame(tab_notas, text=" Cargar/Editar Calificación ", padding=10)
        frame_materia.pack(fill=tk.X, pady=(0, 10))

        self.var_materia = tk.StringVar()
        self.var_tp1 = tk.StringVar(value="0")
        self.var_tp2 = tk.StringVar(value="0")
        self.var_eval1 = tk.StringVar(value="0")
        self.var_eval2 = tk.StringVar(value="0")

        ttk.Label(frame_materia, text="Materia:").grid(row=0, column=0, sticky="w")
        ttk.Entry(frame_materia, textvariable=self.var_materia, width=15).grid(row=0, column=1, padx=5)

        ttk.Label(frame_materia, text="TP1:").grid(row=0, column=2, sticky="w")
        ttk.Entry(frame_materia, textvariable=self.var_tp1, width=5).grid(row=0, column=3, padx=5)

        ttk.Label(frame_materia, text="TP2:").grid(row=0, column=4, sticky="w")
        ttk.Entry(frame_materia, textvariable=self.var_tp2, width=5).grid(row=0, column=5, padx=5)

        ttk.Label(frame_materia, text="Eval 1:").grid(row=1, column=0, sticky="w", pady=5)
        ttk.Entry(frame_materia, textvariable=self.var_eval1, width=5).grid(row=1, column=1, sticky="w", padx=5)

        ttk.Label(frame_materia, text="Eval 2:").grid(row=1, column=2, sticky="w")
        ttk.Entry(frame_materia, textvariable=self.var_eval2, width=5).grid(row=1, column=3, padx=5)

        ttk.Button(frame_materia, text="Guardar Nota", command=self.on_save_nota).grid(row=1, column=4, columnspan=2, sticky="e")

        cols = ("materia", "tp1", "tp2", "eval1", "eval2", "prom_trimestral", "nota_final")
        self.tree_notas = ttk.Treeview(tab_notas, columns=cols, show="headings", height=8)
        self.tree_notas.heading("materia", text="Materia")
        self.tree_notas.heading("tp1", text="TP 1")
        self.tree_notas.heading("tp2", text="TP 2")
        self.tree_notas.heading("eval1", text="Eval 1")
        self.tree_notas.heading("eval2", text="Eval 2")
        self.tree_notas.heading("prom_trimestral", text="Prom. Trimestral")
        self.tree_notas.heading("nota_final", text="Nota Final")

        for c in cols:
            self.tree_notas.column(c, anchor="center" if c != "materia" else "w", width=90)

        self.tree_notas.pack(fill=tk.BOTH, expand=True)
        self.tree_notas.bind("<<TreeviewSelect>>", self.on_select_materia)

    def _load_alumno_data(self):
        data = self.db.get_alumno_detail(self.alumno_id)
        if data:
            self.var_nombre.set(data["nombre"])
            self.var_apellido.set(data["apellido"])
            self.var_direccion.set(data["direccion"] or "")
            self.var_fnac.set(data["fecha_nacimiento"] or "")
            self.var_contacto.set(data["contacto"] or "")
            self.var_contacto_alt.set(data["contacto_alt"] or "")
            self.var_email.set(data["email"] or "")

            for k, v in self.cursos_dict.items():
                if v == data["curso_id"]:
                    self.var_curso.set(k)

    def _load_calificaciones(self):
        for item in self.tree_notas.get_children():
            self.tree_notas.delete(item)

        if not self.alumno_id:
            return

        rows = self.db.fetch_calificaciones(self.alumno_id)
        for r in rows:
            tp1, tp2 = r["tp1"], r["tp2"]
            ev1, ev2 = r["eval1"], r["eval2"]

            prom_tp = (tp1 + tp2) / 2.0
            nota_final = (prom_tp + ev1 + ev2) / 3.0

            self.tree_notas.insert("", tk.END, values=(
                r["materia"], f"{tp1:.1f}", f"{tp2:.1f}", f"{ev1:.1f}", f"{ev2:.1f}",
                f"{prom_tp:.2f}", f"{nota_final:.2f}"
            ))

    def on_save_personal(self):
        if not self.var_nombre.get() or not self.var_apellido.get() or not self.var_curso.get():
            messagebox.showwarning("Atención", "Nombre, Apellido y Curso son obligatorios.")
            return

        data = {
            "id": self.alumno_id,
            "curso_id": self.cursos_dict[self.var_curso.get()],
            "nombre": self.var_nombre.get().strip(),
            "apellido": self.var_apellido.get().strip(),
            "direccion": self.var_direccion.get().strip(),
            "fecha_nacimiento": self.var_fnac.get().strip(),
            "contacto": self.var_contacto.get().strip(),
            "contacto_alt": self.var_contacto_alt.get().strip(),
            "email": self.var_email.get().strip(),
        }

        self.alumno_id = self.db.save_or_update_alumno(data)
        messagebox.showinfo("Éxito", "Datos personales guardados.")
        self.master.refresh_alumnos()

    def on_save_nota(self):
        if not self.alumno_id:
            messagebox.showwarning("Atención", "Primero guarde los datos personales del alumno.")
            return

        materia = self.var_materia.get().strip()
        if not materia:
            messagebox.showwarning("Atención", "Ingrese el nombre de la materia.")
            return

        try:
            # Convierte comas a puntos para admitir ambos formatos decimales
            tp1 = float(self.var_tp1.get().replace(",", "."))
            tp2 = float(self.var_tp2.get().replace(",", "."))
            ev1 = float(self.var_eval1.get().replace(",", "."))
            ev2 = float(self.var_eval2.get().replace(",", "."))

            # Validación de rango numérico (permite 0 como valor por defecto)
            notas = [tp1, tp2, ev1, ev2]
            for nota in notas:
                if nota < 0 or nota > 10:
                    messagebox.showwarning("Nota fuera de rango", "Las calificaciones deben estar entre 1 y 10.")
                    return

            self.db.save_or_update_calificacion(self.alumno_id, materia, tp1, tp2, ev1, ev2)
            self._load_calificaciones()

            self.var_materia.set("")
            self.var_tp1.set("0")
            self.var_tp2.set("0")
            self.var_eval1.set("0")
            self.var_eval2.set("0")

        except ValueError:
            messagebox.showerror("Error de formato", "Ingrese únicamente valores numéricos (ejemplo: 8 o 7.5).")

    def on_select_materia(self, event):
        selected = self.tree_notas.selection()
        if selected:
            val = self.tree_notas.item(selected[0])["values"]
            self.var_materia.set(val[0])
            self.var_tp1.set(val[1])
            self.var_tp2.set(val[2])
            self.var_eval1.set(val[3])
            self.var_eval2.set(val[4])


# ==========================================
# 3. INTERFAZ PRINCIPAL
# ==========================================

class SchoolApp(tk.Tk):
    def __init__(self, db_manager: SchoolDatabaseManager):
        super().__init__()
        self.db = db_manager
        self.title("Sistema de Gestión Escolar")
        self.geometry("900x520")
        self.style = ttk.Style(self)
        self.style.theme_use("clam")

        self._create_widgets()
        self._load_cursos()

    def _create_widgets(self):
        main_frame = ttk.Frame(self, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)

        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(top_frame, text="Curso Completo:", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=(0, 5))
        self.combo_cursos = ttk.Combobox(top_frame, state="readonly", width=18)
        self.combo_cursos.pack(side=tk.LEFT, padx=(0, 15))
        self.combo_cursos.bind("<<ComboboxSelected>>", self.on_curso_change)

        ttk.Label(top_frame, text="Año:").pack(side=tk.LEFT, padx=(0, 2))
        self.combo_ano = ttk.Combobox(top_frame, state="readonly", values=[f"{i}° Año" for i in range(1, 8)], width=8)
        self.combo_ano.pack(side=tk.LEFT, padx=(0, 10))
        self.combo_ano.bind("<<ComboboxSelected>>", self.on_filtro_change)

        ttk.Label(top_frame, text="División:").pack(side=tk.LEFT, padx=(0, 2))
        self.combo_div = ttk.Combobox(top_frame, state="readonly", values=["A", "B", "C", "D"], width=5)
        self.combo_div.pack(side=tk.LEFT, padx=(0, 10))
        self.combo_div.bind("<<ComboboxSelected>>", self.on_filtro_change)

        ttk.Button(top_frame, text="+ Agregar Alumno", command=self.on_add_alumno).pack(side=tk.RIGHT, padx=5)
        ttk.Button(top_frame, text="Eliminar Alumno", command=self.on_delete_alumno).pack(side=tk.RIGHT)

        search_frame = ttk.Frame(main_frame)
        search_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(search_frame, text="🔍 Buscar en tiempo real:", font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=(0, 5))
        self.var_search = tk.StringVar()
        self.entry_search = ttk.Entry(search_frame, textvariable=self.var_search, width=30)
        self.entry_search.pack(side=tk.LEFT, padx=(0, 10))
        self.entry_search.bind("<KeyRelease>", self.on_search_key_release)

        self.var_global_search = tk.BooleanVar(value=False)
        self.chk_global = ttk.Checkbutton(
            search_frame,
            text="Buscar en todos los cursos",
            variable=self.var_global_search,
            command=self.refresh_alumnos
        )
        self.chk_global.pack(side=tk.LEFT)

        table_frame = ttk.Frame(main_frame)
        table_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("id", "apellido", "nombre", "email", "contacto")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")

        self.tree.heading("id", text="ID")
        self.tree.heading("apellido", text="Apellido")
        self.tree.heading("nombre", text="Nombre")
        self.tree.heading("email", text="Email")
        self.tree.heading("contacto", text="Contacto")

        self.tree.column("id", width=40, anchor="center")
        self.tree.column("apellido", width=150)
        self.tree.column("nombre", width=150)
        self.tree.column("email", width=200)
        self.tree.column("contacto", width=120)

        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<Double-1>", self.on_double_click_alumno)

    def _load_cursos(self):
        cursos = self.db.fetch_cursos()
        self.cursos_map = {c["nombre"]: c["id"] for c in cursos}
        self.combo_cursos["values"] = list(self.cursos_map.keys())

        if self.cursos_map:
            self.combo_cursos.current(0)
            self._sync_filtros_desde_combo()
            self.refresh_alumnos()

    def _sync_filtros_desde_combo(self):
        nombre_curso = self.combo_cursos.get()
        if nombre_curso:
            partes = nombre_curso.split(" ")
            self.combo_ano.set(f"{partes[0]} {partes[1]}")
            self.combo_div.set(partes[2])

    def refresh_alumnos(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        search_text = self.var_search.get().strip()

        if self.var_global_search.get() and search_text:
            alumnos = self.db.search_alumnos_global(search_text)
            for row in alumnos:
                self.tree.insert("", tk.END, values=(
                    row["id"], row["apellido"], row["nombre"], row["email"], f"{row['contacto']} ({row['curso_nombre']})"
                ))
            return

        curso_nombre = self.combo_cursos.get()
        if not curso_nombre:
            return

        curso_id = self.cursos_map[curso_nombre]
        alumnos = self.db.fetch_alumnos_by_curso(curso_id, query_text=search_text)

        for row in alumnos:
            self.tree.insert("", tk.END, values=(
                row["id"], row["apellido"], row["nombre"], row["email"], row["contacto"]
            ))

    def on_search_key_release(self, event):
        self.refresh_alumnos()

    def on_curso_change(self, event):
        self._sync_filtros_desde_combo()
        self.refresh_alumnos()

    def on_filtro_change(self, event):
        ano = self.combo_ano.get()
        div = self.combo_div.get()
        if ano and div:
            target_curso = f"{ano} {div}"
            if target_curso in self.cursos_map:
                self.combo_cursos.set(target_curso)
                self.refresh_alumnos()

    def on_double_click_alumno(self, event):
        selected = self.tree.selection()
        if not selected:
            return

        alumno_id = self.tree.item(selected[0])["values"][0]
        StudentDetailDialog(self, self.db, alumno_id=alumno_id)

    def on_add_alumno(self):
        curso_nombre = self.combo_cursos.get()
        curso_id = self.cursos_map.get(curso_nombre)
        StudentDetailDialog(self, self.db, current_curso_id=curso_id)

    def on_delete_alumno(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Atención", "Seleccione un alumno para eliminar.")
            return

        alumno_id = self.tree.item(selected[0])["values"][0]
        if messagebox.askyesno("Confirmar", "¿Desea eliminar este alumno y todas sus calificaciones?"):
            self.db.delete_alumno(alumno_id)
            self.refresh_alumnos()


if __name__ == "__main__":
    db = SchoolDatabaseManager()
    app = SchoolApp(db)
    app.mainloop()