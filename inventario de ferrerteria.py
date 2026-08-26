import sqlite3
from dataclasses import dataclass
from typing import List, Optional
import tkinter as tk
from tkinter import ttk, messagebox


# ==========================================
# 1. MODELO DE DATOS Y CAPA DE PERSISTENCIA
# ==========================================

@dataclass
class Product:
    description: str
    supplier: str
    price: float
    stock: int
    min_stock: int
    comments: str
    code_id: Optional[int] = None


class DatabaseManager:
    def __init__(self, db_name: str = "BD_Hierros.db"):
        self.db_name = db_name
        self._create_table()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        return conn

    def _create_table(self) -> None:
        """Inicialización idempotente del esquema."""
        query = """
        CREATE TABLE IF NOT EXISTS stock (
            codigo_id INTEGER PRIMARY KEY AUTOINCREMENT,
            descripcion TEXT NOT NULL,
            proveedor TEXT NOT NULL,
            precio_unitario REAL NOT NULL DEFAULT 0.0,
            stock INTEGER NOT NULL DEFAULT 0,
            stock_minimo INTEGER NOT NULL DEFAULT 0,
            comentarios TEXT
        );
        """
        with self._get_connection() as conn:
            conn.execute(query)

    def save_or_update(self, product: Product) -> None:
        """Crea o actualiza un registro basándose en su ID."""
        with self._get_connection() as conn:
            if product.code_id:
                query = """
                UPDATE stock
                SET descripcion=?, proveedor=?, precio_unitario=?, stock=?, stock_minimo=?, comentarios=?
                WHERE codigo_id=?
                """
                conn.execute(query, (
                    product.description, product.supplier, product.price,
                    product.stock, product.min_stock, product.comments, product.code_id
                ))
            else:
                query = """
                INSERT INTO stock (descripcion, proveedor, precio_unitario, stock, stock_minimo, comentarios)
                VALUES (?, ?, ?, ?, ?, ?)
                """
                conn.execute(query, (
                    product.description, product.supplier, product.price,
                    product.stock, product.min_stock, product.comments
                ))

    def fetch_all(self) -> List[sqlite3.Row]:
        query = "SELECT * FROM stock ORDER BY codigo_id DESC"
        with self._get_connection() as conn:
            return conn.execute(query).fetchall()

    def delete(self, code_id: int) -> bool:
        query = "DELETE FROM stock WHERE codigo_id = ?"
        with self._get_connection() as conn:
            cursor = conn.execute(query, (code_id,))
            return cursor.rowcount > 0


# ==========================================
# 2. INTERFAZ GRÁFICA DE USUARIO (GUI)
# ==========================================

class InventoryApp(tk.Tk):
    def __init__(self, db_manager: DatabaseManager):
        super().__init__()
        self.db = db_manager
        self.title("Sistema de Gestión de Inventario - Ferretería")
        self.geometry("850x600")
        self.style = ttk.Style(self)
        self.style.theme_use("clam")

        self._create_widgets()
        self.refresh_table()

    def _create_widgets(self) -> None:
        # Contenedor Principal
        main_frame = ttk.Frame(self, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- FORMULARIO ---
        form_frame = ttk.LabelFrame(main_frame, text=" Datos del Producto ", padding="10")
        form_frame.pack(fill=tk.X, pady=(0, 10))

        # Variables Tkinter
        self.var_id = tk.StringVar()
        self.var_desc = tk.StringVar()
        self.var_prov = tk.StringVar()
        self.var_price = tk.StringVar()
        self.var_stock = tk.StringVar()
        self.var_min_stock = tk.StringVar()

        # Inputs en Grid
        ttk.Label(form_frame, text="ID:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(form_frame, textvariable=self.var_id, state="readonly", width=10).grid(row=0, column=1, sticky="w", padx=5)

        ttk.Label(form_frame, text="Descripción:").grid(row=0, column=2, sticky="w", padx=5)
        ttk.Entry(form_frame, textvariable=self.var_desc, width=30).grid(row=0, column=3, sticky="w", padx=5)

        ttk.Label(form_frame, text="Proveedor:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(form_frame, textvariable=self.var_prov, width=20).grid(row=1, column=1, sticky="w", padx=5)

        ttk.Label(form_frame, text="Precio ($):").grid(row=1, column=2, sticky="w", padx=5)
        ttk.Entry(form_frame, textvariable=self.var_price, width=15).grid(row=1, column=3, sticky="w", padx=5)

        ttk.Label(form_frame, text="Stock Actual:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(form_frame, textvariable=self.var_stock, width=10).grid(row=2, column=1, sticky="w", padx=5)

        ttk.Label(form_frame, text="Stock Mínimo:").grid(row=2, column=2, sticky="w", padx=5)
        ttk.Entry(form_frame, textvariable=self.var_min_stock, width=10).grid(row=2, column=3, sticky="w", padx=5)

        ttk.Label(form_frame, text="Comentarios:").grid(row=3, column=0, sticky="nw", padx=5, pady=5)
        self.txt_comments = tk.Text(form_frame, height=3, width=40)
        self.txt_comments.grid(row=3, column=1, columnspan=3, sticky="w", padx=5, pady=5)

        # --- BOTONES DE ACCIÓN ---
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=5)

        ttk.Button(btn_frame, text="Guardar / Actualizar", command=self.on_save).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Limpiar Formulario", command=self.clear_form).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Eliminar Seleccionado", command=self.on_delete).pack(side=tk.LEFT, padx=5)

        # --- TABLA TREEVIEW ---
        table_frame = ttk.Frame(main_frame)
        table_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        columns = ("id", "desc", "prov", "price", "stock", "min_stock")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")

        self.tree.heading("id", text="ID")
        self.tree.heading("desc", text="Descripción")
        self.tree.heading("prov", text="Proveedor")
        self.tree.heading("price", text="Precio")
        self.tree.heading("stock", text="Stock")
        self.tree.heading("min_stock", text="Stock Mín.")

        self.tree.column("id", width=40, anchor="center")
        self.tree.column("desc", width=200)
        self.tree.column("prov", width=120)
        self.tree.column("price", width=80, anchor="e")
        self.tree.column("stock", width=60, anchor="center")
        self.tree.column("min_stock", width=70, anchor="center")

        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

    # --- LÓGICA DE CONTROLADORES ---

    def refresh_table(self) -> None:
        """Recarga la lista completa desde la BD."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        for row in self.db.fetch_all():
            self.tree.insert("", tk.END, values=(
                row["codigo_id"], row["descripcion"], row["proveedor"],
                f"${row['precio_unitario']:.2f}", row["stock"], row["stock_minimo"]
            ))

    def on_save(self) -> None:
        """Valida y guarda los datos ingresados."""
        try:
            desc = self.var_desc.get().strip()
            prov = self.var_prov.get().strip()
            if not desc or not prov:
                messagebox.showwarning("Atención", "Descripción y Proveedor son obligatorios.")
                return

            product = Product(
                code_id=int(self.var_id.get()) if self.var_id.get() else None,
                description=desc,
                supplier=prov,
                price=float(self.var_price.get() or 0.0),
                stock=int(self.var_stock.get() or 0),
                min_stock=int(self.var_min_stock.get() or 0),
                comments=self.txt_comments.get("1.0", tk.END).strip()
            )

            self.db.save_or_update(product)
            self.refresh_table()
            self.clear_form()
            messagebox.showinfo("Éxito", "Operación realizada correctamente.")

        except ValueError:
            messagebox.showerror("Error de entrada", "Asegúrese de ingresar números válidos en Precio y Stock.")

    def on_tree_select(self, event) -> None:
        """Carga los datos del elemento seleccionado en la tabla hacia el formulario."""
        selected = self.tree.selection()
        if not selected:
            return

        item = self.tree.item(selected[0])
        code_id = item["values"][0]

        # Obtener datos completos desde la BD para incluir comentarios
        with self.db._get_connection() as conn:
            row = conn.execute("SELECT * FROM stock WHERE codigo_id = ?", (code_id,)).fetchone()

        if row:
            self.clear_form()
            self.var_id.set(row["codigo_id"])
            self.var_desc.set(row["descripcion"])
            self.var_prov.set(row["proveedor"])
            self.var_price.set(row["precio_unitario"])
            self.var_stock.set(row["stock"])
            self.var_min_stock.set(row["stock_minimo"])
            self.txt_comments.insert("1.0", row["comentarios"] or "")

    def on_delete(self) -> None:
        code_id = self.var_id.get()
        if not code_id:
            messagebox.showwarning("Selección requerida", "Seleccione un registro de la lista para eliminar.")
            return

        if messagebox.askyesno("Confirmar", f"¿Eliminar el registro ID {code_id}?"):
            if self.db.delete(int(code_id)):
                self.refresh_table()
                self.clear_form()
                messagebox.showinfo("Éxito", "Registro eliminado.")

    def clear_form(self) -> None:
        self.var_id.set("")
        self.var_desc.set("")
        self.var_prov.set("")
        self.var_price.set("")
        self.var_stock.set("")
        self.var_min_stock.set("")
        self.txt_comments.delete("1.0", tk.END)


if __name__ == "__main__":
    db = DatabaseManager()
    app = InventoryApp(db)
    app.mainloop()
