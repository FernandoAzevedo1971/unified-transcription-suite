import customtkinter as ctk
import os
import threading
import time
from tkinter import filedialog
from tkinterdnd2 import DND_FILES
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from .services import AssemblyAIService, DeepgramService

class AudioFileHandler(FileSystemEventHandler):
    def __init__(self, callback):
        self.callback = callback

    def on_created(self, event):
        if not event.is_directory:
            self.handle_event(event.src_path)

    def on_moved(self, event):
        if not event.is_directory:
            self.handle_event(event.dest_path)

    def handle_event(self, filepath):
        ext = os.path.splitext(filepath)[1].lower()
        if ext in ['.mp3', '.wav', '.m4a', '.flac', '.ogg']:
            # Wait a moment for file write to complete (especially for large files)
            time.sleep(2)
            self.callback(filepath)

class TranscriberFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.services = {
            "AssemblyAI": None,
            "Deepgram": None
        }
        
        # Configuration
        self.watch_directory = os.getenv("WATCH_DIRECTORY", r"C:\Users\ferna\OneDrive\Documentos\Gravacoes Som Audio Recorder Free")
        
        self.setup_ui()
        self.init_services()
        
        # Start monitoring in a separate thread to ensure UI is ready
        self.after(1000, self.start_monitor)

    def init_services(self):
        aai_key = os.getenv("ASSEMBLYAI_API_KEY")
        dg_key = os.getenv("DEEPGRAM_API_KEY")
        
        if aai_key:
            self.services["AssemblyAI"] = AssemblyAIService(aai_key)
        if dg_key:
            self.services["Deepgram"] = DeepgramService(dg_key)

    def setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        
        # Service Selection
        self.service_frame = ctk.CTkFrame(self)
        self.service_frame.grid(row=0, column=0, padx=20, pady=10, sticky="ew")
        
        ctk.CTkLabel(self.service_frame, text="Serviço:").pack(side="left", padx=10)
        self.service_combo = ctk.CTkComboBox(self.service_frame, values=["AssemblyAI", "Deepgram"])
        self.service_combo.pack(side="left", padx=10)
        
        # File Selection / Status
        self.file_frame = ctk.CTkFrame(self)
        self.file_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        
        self.btn_select = ctk.CTkButton(self.file_frame, text="Selecionar", width=100, command=self.select_file)
        self.btn_select.pack(side="left", padx=10, pady=10)
        
        self.lbl_status = ctk.CTkLabel(self.file_frame, text="Iniciando monitoramento...", text_color="gray")
        self.lbl_status.pack(side="left", padx=10, fill="x", expand=True)
        
        # Text Area
        self.textbox = ctk.CTkTextbox(self, font=ctk.CTkFont(size=14))
        self.textbox.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")
        
        # Buttons
        self.btn_frame = ctk.CTkFrame(self)
        self.btn_frame.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        
        ctk.CTkButton(self.btn_frame, text="Copiar", command=self.copy_text).pack(side="right", padx=10, pady=10)
        ctk.CTkButton(self.btn_frame, text="Limpar", fg_color="gray", command=self.clear_text).pack(side="left", padx=10, pady=10)

        # Drag and Drop
        self.dnd_frame = self
        self.dnd_frame.drop_target_register(DND_FILES)
        self.dnd_frame.dnd_bind('<<Drop>>', self.on_drop)

    def start_monitor(self):
        if not os.path.exists(self.watch_directory):
            try:
                os.makedirs(self.watch_directory, exist_ok=True)
            except Exception as e:
                self.lbl_status.configure(text=f"Erro ao criar pasta: {e}", text_color="red")
                return

        self.event_handler = AudioFileHandler(self.process_file_thread)
        self.observer = Observer()
        self.observer.schedule(self.event_handler, self.watch_directory, recursive=False)
        threading.Thread(target=self.observer.start, daemon=True).start()
        
        folder_name = os.path.basename(self.watch_directory)
        self.lbl_status.configure(text=f"Monitorando: ...\\{folder_name}", text_color="blue")

    def on_drop(self, event):
        filepath = event.data
        if filepath.startswith('{') and filepath.endswith('}'):
            filepath = filepath[1:-1]
        self.process_file_thread(filepath)

    def select_file(self):
        filepath = filedialog.askopenfilename(filetypes=[("Audio", "*.mp3 *.wav *.m4a *.ogg *.flac")])
        if filepath:
            self.process_file_thread(filepath)

    def process_file_thread(self, filepath):
        service_name = self.service_combo.get()
        if not self.services.get(service_name):
            self.lbl_status.configure(text=f"ERRO: API Key para {service_name} ausente!", text_color="red")
            return
            
        filename = os.path.basename(filepath)
        self.lbl_status.configure(text=f"Processando {filename}...", text_color="#FF8C00")
        threading.Thread(target=self.process_file, args=(filepath, service_name), daemon=True).start()

    def process_file(self, filepath, service_name):
        try:
            service = self.services[service_name]
            text = service.transcribe(filepath)
            
            self.lbl_status.configure(text="Transcrição concluída!", text_color="green")
            self.textbox.insert("end", f"\n--- {os.path.basename(filepath)} ({service_name}) ---\n")
            self.textbox.insert("end", text + "\n")
            self.textbox.see("end")
        except Exception as e:
            self.lbl_status.configure(text=f"Erro: {str(e)}", text_color="red")

    def copy_text(self):
        self.clipboard_clear()
        self.clipboard_append(self.textbox.get("0.0", "end"))

    def clear_text(self):
        self.textbox.delete("0.0", "end")
