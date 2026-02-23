import customtkinter as ctk
import pyaudio
import wave
import threading
import os
import time
from datetime import datetime
from tkinter import messagebox

class RecorderFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        # Audio Configuration
        self.chunk = 1024
        self.sample_format = pyaudio.paInt16
        self.channels = 1
        self.rate = 44100
        
        self.is_recording = False
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.frames = []
        
        # State
        self.recording_start_time = None
        self.current_file_size = 0
        self.max_file_size = 80 * 1024 * 1024
        self.save_path = os.getenv("WATCH_DIRECTORY", r"C:\Users\ferna\OneDrive\Documentos\Gravacoes Som Audio Recorder Free")
        os.makedirs(self.save_path, exist_ok=True)

        self.setup_ui()
        self.populate_devices()

    def setup_ui(self):
        # Grid layout
        self.grid_columnconfigure(0, weight=1)
        
        # Device Selection
        self.device_label = ctk.CTkLabel(self, text="Dispositivo de Entrada:", font=ctk.CTkFont(size=14, weight="bold"))
        self.device_label.grid(row=0, column=0, padx=20, pady=(20, 5), sticky="w")
        
        self.device_combo = ctk.CTkComboBox(self, width=400)
        self.device_combo.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="ew")

        # Status
        self.status_frame = ctk.CTkFrame(self)
        self.status_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        
        self.status_label = ctk.CTkLabel(self.status_frame, text="Parado", text_color="red", font=ctk.CTkFont(size=24, weight="bold"))
        self.status_label.pack(pady=20)
        
        self.time_label = ctk.CTkLabel(self.status_frame, text="00:00:00", font=ctk.CTkFont(size=30))
        self.time_label.pack(pady=5)
        
        self.size_label = ctk.CTkLabel(self.status_frame, text="0.00 MB", font=ctk.CTkFont(size=12))
        self.size_label.pack(pady=(0, 20))

        # Controls
        self.record_button = ctk.CTkButton(
            self, 
            text="Iniciar Gravação", 
            command=self.toggle_recording,
            font=ctk.CTkFont(size=16, weight="bold"),
            height=50,
            fg_color="green",
            hover_color="darkgreen"
        )
        self.record_button.grid(row=3, column=0, padx=20, pady=40, sticky="ew")
        
        # Last File Info
        self.file_label = ctk.CTkLabel(self, text="Último arquivo: Nenhum", text_color="gray")
        self.file_label.grid(row=4, column=0, padx=20, pady=10)

    def populate_devices(self):
        self.devices = []
        device_names = []
        default_index = 0
        
        for i in range(self.audio.get_device_count()):
            device_info = self.audio.get_device_info_by_index(i)
            if device_info['maxInputChannels'] > 0:
                name = device_info['name']
                self.devices.append((i, name))
                device_names.append(name)
                if 'USB' in name:
                    default_index = len(device_names) - 1
                    
        self.device_combo.configure(values=device_names)
        if device_names:
            self.device_combo.set(device_names[default_index])

    def get_selected_device_index(self):
        selected_name = self.device_combo.get()
        for idx, name in self.devices:
            if name == selected_name:
                return idx
        return None

    def toggle_recording(self):
        if self.is_recording:
            self.stop_recording()
        else:
            self.start_recording()

    def start_recording(self):
        device_index = self.get_selected_device_index()
        if device_index is None:
            messagebox.showerror("Erro", "Selecione um dispositivo!")
            return

        try:
            self.stream = self.audio.open(
                format=self.sample_format,
                channels=self.channels,
                rate=self.rate,
                frames_per_buffer=self.chunk,
                input=True,
                input_device_index=device_index
            )
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao abrir dispositivo: {e}")
            return

        self.is_recording = True
        self.frames = []
        self.recording_start_time = time.time()
        
        # UI Updates
        self.record_button.configure(text="Parar Gravação", fg_color="red", hover_color="darkred")
        self.status_label.configure(text="Gravando...", text_color="green")
        self.device_combo.configure(state="disabled")
        
        # Threads
        threading.Thread(target=self.record_loop, daemon=True).start()
        threading.Thread(target=self.update_ui_loop, daemon=True).start()

    def stop_recording(self):
        self.is_recording = False
        # UI Updates
        self.record_button.configure(text="Iniciar Gravação", fg_color="green", hover_color="darkgreen")
        self.status_label.configure(text="Parado", text_color="red")
        self.device_combo.configure(state="normal")

    def record_loop(self):
        while self.is_recording:
            try:
                data = self.stream.read(self.chunk)
                self.frames.append(data)
            except Exception as e:
                print(f"Error recording: {e}")
                self.is_recording = False
                break
        
        self.stream.stop_stream()
        self.stream.close()
        self.save_recording()

    def save_recording(self):
        if not self.frames:
            return
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        filename = f"gravacao-fernando_{timestamp}.wav"
        filepath = os.path.join(self.save_path, filename)
        
        wf = wave.open(filepath, 'wb')
        wf.setnchannels(self.channels)
        wf.setsampwidth(self.audio.get_sample_size(self.sample_format))
        wf.setframerate(self.rate)
        wf.writeframes(b''.join(self.frames))
        wf.close()
        
        self.file_label.configure(text=f"Salvo em: {filename}")

    def update_ui_loop(self):
        while self.is_recording:
            elapsed = time.time() - self.recording_start_time
            hours = int(elapsed // 3600)
            minutes = int((elapsed % 3600) // 60)
            seconds = int(elapsed % 60)
            
            size_bytes = len(b''.join(self.frames))
            size_mb = size_bytes / (1024 * 1024)
            
            self.time_label.configure(text=f"{hours:02d}:{minutes:02d}:{seconds:02d}")
            self.size_label.configure(text=f"{size_mb:.2f} MB")
            
            time.sleep(0.5)

    def destroy(self):
        self.audio.terminate()
        super().destroy()
