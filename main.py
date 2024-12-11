import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import pytesseract

pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"

class OCRApp:
    def __init__(self, root):
        self.root = root
        self.root.title("OCR Ruso")
        
        # Variables
        self.img = None
        self.img_tk = None
        self.img_scale = 1.0
        self.selection_start = None
        self.selecciones = []
        self.dibujados = []
        self.undo_stack = []
        self.redo_stack = []
        
        # Configuración de la ventana principal
        self.root.configure(bg='#f0f0f0')
        
        # Frame principal con grid
        self.root.grid_rowconfigure(0, weight=0)  # Fila de botones
        self.root.grid_rowconfigure(1, weight=1)  # Fila del canvas
        self.root.grid_columnconfigure(0, weight=1)
        
        # Frame para botones usando grid
        button_frame = ttk.Frame(root)
        button_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        
        # Configurar columnas del frame de botones para que sean responsivas
        for i in range(5):  # 5 columnas para 5 botones
            button_frame.grid_columnconfigure(i, weight=1)
        
        # Estilo de botones
        style = ttk.Style()
        style.configure('Custom.TButton', padding=5)
        
        # Botones centrados y con expansión
        self.load_btn = ttk.Button(
            button_frame, 
            text="Cargar Imagen",
            command=self.cargar_imagen,
            style='Custom.TButton'
        )
        self.load_btn.grid(row=0, column=0, padx=5, sticky="ew")
        
        self.ocr_btn = ttk.Button(
            button_frame,
            text="Realizar OCR",
            command=self.realizar_ocr,
            style='Custom.TButton'
        )
        self.ocr_btn.grid(row=0, column=1, padx=5, sticky="ew")
        
        self.undo_btn = ttk.Button(
            button_frame,
            text="Deshacer",
            command=self.deshacer,
            style='Custom.TButton'
        )
        self.undo_btn.grid(row=0, column=2, padx=5, sticky="ew")
        
        self.redo_btn = ttk.Button(
            button_frame,
            text="Rehacer",
            command=self.rehacer,
            style='Custom.TButton'
        )
        self.redo_btn.grid(row=0, column=3, padx=5, sticky="ew")
        
        self.clear_btn = ttk.Button(
            button_frame,
            text="Limpiar Todo",
            command=self.reiniciar_selecciones,
            style='Custom.TButton'
        )
        self.clear_btn.grid(row=0, column=4, padx=5, sticky="ew")
        
        # Frame para el canvas y scrollbars usando grid
        canvas_frame = ttk.Frame(root)
        canvas_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        
        # Configurar el grid del frame del canvas
        canvas_frame.grid_rowconfigure(0, weight=1)
        canvas_frame.grid_columnconfigure(0, weight=1)
        
        # Canvas con borde y fondo gris claro
        self.canvas = tk.Canvas(canvas_frame, bg="#e0e0e0", bd=2, relief="sunken")
        self.canvas.grid(row=0, column=0, sticky="nsew")
        
        # Scrollbars
        scroll_y = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)
        scroll_y.grid(row=0, column=1, sticky="ns")
        
        scroll_x = ttk.Scrollbar(canvas_frame, orient="horizontal", command=self.canvas.xview)
        scroll_x.grid(row=1, column=0, sticky="ew")
        
        self.canvas.configure(xscrollcommand=scroll_x.set, yscrollcommand=scroll_y.set)
        
        # Bindings
        self.canvas.bind("<ButtonPress-1>", self.iniciar_seleccion)
        self.canvas.bind("<ButtonRelease-1>", self.finalizar_seleccion)
        self.root.bind("<Control-z>", lambda e: self.deshacer())
        self.root.bind("<Control-y>", lambda e: self.rehacer())

    def cargar_imagen(self):
        """Permite al usuario cargar una imagen y mostrarla en el lienzo."""
        ruta_imagen = filedialog.askopenfilename(
            title="Selecciona una imagen",
            filetypes=[("Archivos de imagen", "*.png;*.jpg;*.jpeg;*.bmp;*.tiff"), ("Todos los archivos", "*.*")]
        )
        if not ruta_imagen:
            return

        try:
            self.img = Image.open(ruta_imagen)
            self.img_tk = ImageTk.PhotoImage(self.img)

            self.img_scale = 1.0

            self.canvas.config(scrollregion=(0, 0, self.img.width, self.img.height))
            self.canvas_id = self.canvas.create_image(0, 0, anchor="nw", image=self.img_tk)
            self.reiniciar_selecciones()

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar la imagen:\n{e}")

    def realizar_ocr(self):
        """Realiza OCR en todas las regiones seleccionadas."""
        if self.img is None:
            messagebox.showerror("Error", "Primero debes cargar una imagen.")
            return

        if not self.selecciones:
            messagebox.showerror("Error", "No has seleccionado ninguna región.")
            return

        texto_final = ""
        for idx, (x1, y1, x2, y2) in enumerate(self.selecciones):
            recorte = self.img.crop((x1, y1, x2, y2))
            texto = pytesseract.image_to_string(recorte, lang="rus")
            texto_final += f"Selección {idx + 1}:\n{texto}\n{'-' * 40}\n"

        text_window = tk.Toplevel(self.root)
        text_window.title("Texto Detectado")
        text_area = tk.Text(text_window, wrap="word", font=("Arial", 12))
        text_area.insert("1.0", texto_final)
        text_area.pack(expand=True, fill="both")

    def iniciar_seleccion(self, event):
        """Inicia la selección del área con el cursor."""
        self.selection_start = self.ajustar_coordenadas(event.x, event.y)

    def finalizar_seleccion(self, event):
        """Finaliza la selección del área con el cursor y la almacena."""
        x1, y1 = self.selection_start
        x2, y2 = self.ajustar_coordenadas(event.x, event.y)

        seleccion = (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
        self.selecciones.append(seleccion)
        self.undo_stack.append(("add", seleccion))
        self.redo_stack.clear()

        idx = len(self.selecciones)
        rect_id = self.canvas.create_rectangle(
            seleccion[0] * self.img_scale,
            seleccion[1] * self.img_scale,
            seleccion[2] * self.img_scale,
            seleccion[3] * self.img_scale,
            outline="red",
            width=2,
        )
        text_id = self.canvas.create_text(
            seleccion[0] * self.img_scale + 10,
            seleccion[1] * self.img_scale + 10,
            text=str(idx),
            fill="white",
            font=("Arial", 12, "bold"),
        )
        self.dibujados.append((rect_id, text_id))

    def ajustar_coordenadas(self, x, y):
        """Ajusta las coordenadas del evento en función del desplazamiento y la escala."""
        x_scroll, y_scroll = self.canvas.xview(), self.canvas.yview()
        x_offset = x_scroll[0] * self.img.width
        y_offset = y_scroll[0] * self.img.height

        return int((x / self.img_scale) + x_offset), int((y / self.img_scale) + y_offset)

    def deshacer(self):
        """Deshace la última acción."""
        if not self.undo_stack:
            return

        action, data = self.undo_stack.pop()
        if action == "add":
            self.selecciones.pop()
            rect_id, text_id = self.dibujados.pop()
            self.canvas.delete(rect_id)
            self.canvas.delete(text_id)

    def rehacer(self):
        """Rehace la última acción deshecha."""
        if not self.redo_stack:
            return

        action, data = self.redo_stack.pop()
        if action == "add":
            self.selecciones.append(data)
            rect_id = self.canvas.create_rectangle(
                data[0] * self.img_scale,
                data[1] * self.img_scale,
                data[2] * self.img_scale,
                data[3] * self.img_scale,
                outline="red",
                width=2,
            )
            text_id = self.canvas.create_text(
                data[0] * self.img_scale + 10,
                data[1] * self.img_scale + 10,
                text=str(len(self.selecciones)),
                fill="white",
                font=("Arial", 12, "bold"),
            )
            self.dibujados.append((rect_id, text_id))

    def reiniciar_selecciones(self):
        """Reinicia las selecciones y las pilas de acciones."""
        self.selecciones = []
        self.dibujados = []
        self.undo_stack = []
        self.redo_stack = []
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor="nw", image=self.img_tk)

root = tk.Tk()
app = OCRApp(root)
root.mainloop()