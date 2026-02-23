import customtkinter as ctk
import os
from dotenv import load_dotenv
from modules.recorder import RecorderFrame
from modules.transcriber import TranscriberFrame

# Load environment variables
load_dotenv(override=True)

from tkinterdnd2 import TkinterDnD

class UnifiedApp(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self):
        super().__init__()
        self.TkdndVersion = TkinterDnD._require(self)

        # Window Setup
        self.title("Unified Transcription Suite")
        self.geometry("900x700")
        
        # Theme
        ctk.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
        ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

        # Grid Layout
        self.grid_columnconfigure(0, weight=1)  # 1/3
        self.grid_columnconfigure(1, weight=2)  # 2/3
        self.grid_rowconfigure(0, weight=1)

        # Recorder Frame (Left - 1/3)
        self.recorder_frame = RecorderFrame(self)
        self.recorder_frame.grid(row=0, column=0, padx=(20, 10), pady=20, sticky="nsew")

        # Transcriber Frame (Right - 2/3)
        self.transcriber_frame = TranscriberFrame(self)
        self.transcriber_frame.grid(row=0, column=1, padx=(10, 20), pady=20, sticky="nsew")

if __name__ == "__main__":
    app = UnifiedApp()
    app.mainloop()
