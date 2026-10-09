import sys
import os

def resource_path(relative_path):
    
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

import cv2
import mediapipe as mp
import threading
import time
import customtkinter as ctk
from PIL import Image, ImageTk
from main import GestureMouseEngine


ctk.set_appearance_mode("Dark")

class ModernVirtualMouseGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("NEXUS - AI Gesture Controller")
        self.geometry("960x650")
        self.configure(fg_color="#0F111A")  
        self.resizable(False, False)

        self.engine = GestureMouseEngine(model_path=resource_path('gesture_recognizer.task'))
        self.is_running = False
        self.cap = None
        self.thread = None
        self.iconbitmap(resource_path("icon.ico"))

        
        self.prev_frame_time = 0

        self.setup_ui()

    def setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=3)
        self.grid_rowconfigure(0, weight=1)

        
        self.sidebar = ctk.CTkFrame(self, fg_color="#1A1D24", corner_radius=20, border_width=1, border_color="#2A2E3D")
        self.sidebar.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        
        self.logo_label = ctk.CTkLabel(
            self.sidebar, 
            text="⚡ NEXUS AI", 
            font=ctk.CTkFont(family="Consolas", size=24, weight="bold"),
            text_color="#00E5FF"
        )
        self.logo_label.pack(padx=20, pady=(25, 2))

        self.subtitle_label = ctk.CTkLabel(
            self.sidebar, 
            text="Cybernetic Vision Engine", 
            font=ctk.CTkFont(size=11),
            text_color="#6C7289"
        )
        self.subtitle_label.pack(padx=20, pady=(0, 25))

        
        self.btn_toggle = ctk.CTkButton(
            self.sidebar, 
            text="START ENGINE", 
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#00E5FF", 
            text_color="#0F111A",
            hover_color="#00B0FF",
            height=48,
            corner_radius=12,
            command=self.toggle_engine
        )
        self.btn_toggle.pack(padx=20, pady=10, fill="x")

    
        self.status_card = ctk.CTkFrame(self.sidebar, fg_color="#12141C", corner_radius=14, border_width=1, border_color="#252936")
        self.status_card.pack(padx=20, pady=20, fill="x")

        self.status_title = ctk.CTkLabel(self.status_card, text="SYSTEM STATUS", font=ctk.CTkFont(size=10, weight="bold"), text_color="#6C7289")
        self.status_title.pack(padx=15, pady=(12, 2), anchor="w")

        self.status_text = ctk.CTkLabel(
            self.status_card, 
            text="OFFLINE", 
            font=ctk.CTkFont(family="Consolas", size=18, weight="bold"),
            text_color="#FF5252"
        )
        self.status_text.pack(padx=15, pady=(0, 12), anchor="w")

        
        self.guide_frame = ctk.CTkFrame(self.sidebar, fg_color="#12141C", corner_radius=14)
        self.guide_frame.pack(padx=20, pady=(10, 20), fill="both", expand=True)

        guide_html = (
            "🎯 GESTURE GUIDE\n\n"
            "☝️ Index Up\n"
            "   Move cursor around\n\n"
            "🤏 Index + Middle\n"
            "   Pinch together to click\n\n"
            "🖐️ 4 Fingers Up\n"
            "   Point up to scroll up\n\n"
            "👇 4 Fingers Down\n"
            "   Point down to scroll down\n\n"
        )
        
        self.guide_label = ctk.CTkLabel(
            self.guide_frame, 
            text=guide_html, 
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color="#A0A5B5",
            justify="left"
        )
        self.guide_label.pack(padx=12, pady=12, anchor="nw")


        self.video_frame = ctk.CTkFrame(self, fg_color="#1A1D24", corner_radius=20, border_width=1, border_color="#2A2E3D")
        self.video_frame.grid(row=0, column=1, padx=(0, 20), pady=20, sticky="nsew")

        self.video_label = ctk.CTkLabel(
            self.video_frame, 
            text="📷 CAMERA OFFLINE\n\nClick START ENGINE to initialize vision sensor", 
            font=ctk.CTkFont(size=14),
            text_color="#52586B"
        )
        self.video_label.pack(expand=True, fill="both", padx=15, pady=15)

    def toggle_engine(self):
        if not self.is_running:
            self.is_running = True
            self.btn_toggle.configure(text="STOP ENGINE", fg_color="#FF3366", hover_color="#D81B60", text_color="#FFFFFF")
            self.status_text.configure(text="INITIALIZING...", text_color="#00E5FF")
            
            self.thread = threading.Thread(target=self.run_mouse_loop, daemon=True)
            self.thread.start()
        else:
            self.is_running = False
            self.btn_toggle.configure(text="START ENGINE", fg_color="#00E5FF", hover_color="#00B0FF", text_color="#0F111A")
            self.status_text.configure(text="OFFLINE", text_color="#FF5252")
            self.video_label.configure(image="", text="📷 CAMERA OFFLINE\n\nClick START ENGINE to initialize vision sensor")

    def update_gui_state(self, img_tk, gesture_name):
        if self.is_running:
            self.video_label.configure(image=img_tk, text="")
            self.video_label.image = img_tk
            
        
            color_map = {
                "NAVIGATING": "#00E5FF",
                "CLICK": "#FFD600",
                "SCROLL UP": "#00E676",
                "SCROLL DOWN": "#FF9100",
                "PAUSED": "#FF1744"
            }
            active_color = color_map.get(gesture_name, "#00E5FF")
            self.status_text.configure(text=gesture_name, text_color=active_color)

    def run_mouse_loop(self):
        BaseOptions = mp.tasks.BaseOptions
        GestureRecognizer = mp.tasks.vision.GestureRecognizer
        GestureRecognizerOptions = mp.tasks.vision.GestureRecognizerOptions
        VisionRunningMode = mp.tasks.vision.RunningMode

        options = GestureRecognizerOptions(
            base_options=BaseOptions(model_asset_path=self.engine.model_path),
            running_mode=VisionRunningMode.VIDEO
        )

        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        try:
            with GestureRecognizer.create_from_options(options) as recognizer:
                while self.is_running and self.cap.isOpened():
                    success, frame = self.cap.read()
                    if not success or frame is None:
                        continue

                    
                    new_frame_time = time.time()
                    fps = int(1 / (new_frame_time - self.prev_frame_time)) if self.prev_frame_time > 0 else 0
                    self.prev_frame_time = new_frame_time

                    processed_frame, gesture_name = self.engine.process_frame(frame, recognizer)

                    
                    cv2.putText(processed_frame, f"FPS: {fps}", (540, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 229, 255), 2, cv2.LINE_AA)

                    
                    rgb_image = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
                    img = Image.fromarray(rgb_image)
                    img_tk = ImageTk.PhotoImage(image=img)

                
                    self.after(0, self.update_gui_state, img_tk, gesture_name)
        except Exception as e:
            print(f"Error in Vision Loop: {e}")
        finally:
            if self.cap and self.cap.isOpened():
                self.cap.release()

if __name__ == "__main__":
    app = ModernVirtualMouseGUI()
    app.mainloop()
