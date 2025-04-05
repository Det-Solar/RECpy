import customtkinter as ctk
import cv2
import numpy as np
import threading
import mss
import os
import time
from tkinter import filedialog, Toplevel, Canvas
import pyautogui

CURSOR_ENABLED_COLOR = "#119c7b"
CURSOR_DISABLED_COLOR = "#808080"

class RECpy:
    def __init__(self, master):
        self.master = master
        self.master.title("RECpy 1.3")
        self.master.geometry("250x250")
        self.master.resizable(False, False)
        
        self.is_recording = False
        self.is_paused = False
        self.output_file = ""
        self.low_quality = False
        self.potato_quality = False
        self.audio_on = False
        self.cursor_enabled = False
        self.selected_region = None

        font_path = os.path.join(os.path.dirname(__file__), "AgitProp.ttf")
        try:
            self.master.tk.call("font", "create", "AgitProp", "-family", "AgitProp", "-size", "16")
            self.custom_font = ("AgitProp", 16)
        except Exception as e:
            print(f"Warning: Font file not found or invalid. Using default font. ({e})")
            self.custom_font = ("Papyrus", 16)

        self.record_button = ctk.CTkButton(
            master, 
            text="▶", 
            command=self.start_recording, 
            fg_color="green", 
            hover_color="darkgreen", 
            font=self.custom_font
        )
        self.record_button.pack(pady=10)
        
        self.quality_button = ctk.CTkButton(
            master, 
            text="Quality: High", 
            command=self.toggle_quality, 
            fg_color="#a4133c", 
            hover_color="#800f2a", 
            font=self.custom_font
        )
        self.quality_button.pack(pady=10)

        self.audio_button = ctk.CTkButton(
            master,
            text="Audio: Off",
            command=self.toggle_audio,
            fg_color="#1a759f",
            hover_color="#134e6f",
            font=self.custom_font
        )
        self.audio_button.pack(pady=10)

        self.region_button = ctk.CTkButton(
            master,
            text="Select Region",
            command=self.select_region,
            fg_color="#6a0572",
            hover_color="#4a034e",
            font=self.custom_font
        )
        self.region_button.pack(pady=10)

        self.button_frame = ctk.CTkFrame(master, fg_color="transparent")
        self.button_frame.pack(pady=10)

        self.left_button = ctk.CTkButton(
            self.button_frame,
            text="L",
            command=None,
            fg_color="#808080",
            hover_color="#606060",
            font=self.custom_font,
            height=30,
            width=30
        )
        self.left_button.grid(row=0, column=0, padx=10)

        self.cursor_button = ctk.CTkButton(
            self.button_frame,
            text="➤",
            command=self.toggle_cursor,
            fg_color="#808080",
            hover_color="#606060",
            font=self.custom_font,
            height=30,
            width=30
        )
        self.cursor_button.grid(row=0, column=1, padx=10)

        self.right_button = ctk.CTkButton(
            self.button_frame,
            text="R",
            fg_color="#808080",
            hover_color="#606060",
            font=self.custom_font,
            height=30,
            width=30
        )
        self.right_button.grid(row=0, column=2, padx=10)

    def toggle_quality(self):
        if not self.low_quality and not self.potato_quality:
            self.low_quality = True
            self.potato_quality = False
            self.quality_button.configure(text="Quality: Low")
        elif self.low_quality:
            self.low_quality = False
            self.potato_quality = True
            self.quality_button.configure(text="Quality: Potato")
        else:
            self.low_quality = False
            self.potato_quality = False
            self.quality_button.configure(text="Quality: High")
    
    def toggle_audio(self):
        self.audio_on = not self.audio_on
        self.audio_button.configure(text="Audio: On" if self.audio_on else "Audio: Off")

    def select_region(self):
        region_window = Toplevel(self.master)
        region_window.attributes("-fullscreen", True)
        region_window.attributes("-alpha", 0.3)
        region_window.configure(bg="black")

        canvas = Canvas(region_window, bg="black", highlightthickness=0)
        canvas.pack(fill="both", expand=True)

        rect = None
        x_start, y_start = 0, 0

        def on_click(event):
            nonlocal x_start, y_start, rect
            x_start, y_start = event.x, event.y
            rect = canvas.create_rectangle(x_start, y_start, x_start, y_start, outline="red", width=2)

        def on_drag(event):
            nonlocal rect
            canvas.coords(rect, x_start, y_start, event.x, event.y)

        def on_release(event):
            nonlocal x_start, y_start
            x_end, y_end = event.x, event.y
            self.selected_region = (x_start, y_start, x_end - x_start, y_end - y_start)
            self.region_button.configure(text="Region: Selected")
            region_window.destroy()

        canvas.bind("<Button-1>", on_click)
        canvas.bind("<B1-Motion>", on_drag)
        canvas.bind("<ButtonRelease-1>", on_release)

    def toggle_cursor(self):
        self.cursor_enabled = not self.cursor_enabled
        if self.cursor_enabled:
            self.cursor_button.configure(fg_color=CURSOR_ENABLED_COLOR, hover_color="#0e7a62")
        else:
            self.cursor_button.configure(fg_color=CURSOR_DISABLED_COLOR, hover_color="#606060")

    def start_recording(self):
        self.output_file = filedialog.asksaveasfilename(defaultextension=".mp4", filetypes=[("MP4 files", "*.mp4"), ("AVI files", "*.avi")])
        if not self.output_file:
            return
        
        self.is_recording = True
        self.record_button.configure(text="⏺", fg_color="#db3a34", hover_color="darkred")
        
        self.master.withdraw()
        self.indicator_window()
        
        def countdown():
            for i in range(3, 0, -1):
                if self.indicator_button.winfo_exists():
                    self.indicator_button.configure(text=str(i))
                time.sleep(1)
            
            if self.indicator_button.winfo_exists():
                self.indicator_button.configure(text="⏺")
            
            threading.Thread(target=self.record_screen, daemon=True).start()
            threading.Thread(target=self.update_timer, daemon=True).start()
        
        threading.Thread(target=countdown, daemon=True).start()
        
    def indicator_window(self):
        self.indicator = ctk.CTkToplevel()
        self.indicator.geometry("60x120")
        self.indicator.overrideredirect(True)
        self.indicator.attributes("-topmost", True)
        self.indicator.attributes("-alpha", 0.4)
        self.indicator.attributes("-transparentcolor", self.indicator["bg"])

        self.indicator_button = ctk.CTkButton(
            self.indicator, 
            text="⏹", 
            fg_color="#881347", 
            hover_color="darkred", 
            font=self.custom_font, 
            height=50, 
            width=50
        )
        self.indicator_button.pack(pady=(5, 2))

        self.pause_button = ctk.CTkButton(
            self.indicator, 
            text="⏸", 
            fg_color="#084C61", 
            hover_color="#062f3d", 
            font=self.custom_font, 
            height=28, 
            width=50
        )
        self.pause_button.pack(pady=(2, 5))

        self.timer_frame = ctk.CTkFrame(
            self.indicator,
            fg_color="black",
            corner_radius=10,
            height=30,
            width=60
        )
        self.timer_frame.pack(pady=(5, 0))

        self.timer_label = ctk.CTkLabel(
            self.timer_frame,
            text="00:00",
            font=self.custom_font,
            fg_color="transparent"
        )
        self.timer_label.pack(padx=5, pady=5)

        self.indicator_button.bind("<Double-Button-1>", lambda event: self.stop_recording())
        self.pause_button.bind("<Double-Button-1>", lambda event: self.toggle_pause())
        self.indicator.bind("<Button-1>", self.start_move)
        self.indicator.bind("<B1-Motion>", self.on_move)

        self.x_offset = 0
        self.y_offset = 0

    def start_move(self, event):
        self.x_offset = event.x
        self.y_offset = event.y

    def on_move(self, event):
        x = self.indicator.winfo_x() + (event.x - self.x_offset)
        y = self.indicator.winfo_y() + (event.y - self.y_offset)
        self.indicator.geometry(f"60x120+{x}+{y}")

    def toggle_pause(self):
        self.is_paused = not self.is_paused
        self.pause_button.configure(text="▶" if self.is_paused else "⏸")
        
    def draw_cursor(self, frame, cursor_x, cursor_y, monitor):
        if not self.cursor_enabled:
            return

        cursor_x -= monitor["left"]
        cursor_y -= monitor["top"]

        original_width = monitor["width"]
        original_height = monitor["height"]
        resized_width = frame.shape[1]
        resized_height = frame.shape[0]

        cursor_x = int(cursor_x * (resized_width / original_width))
        cursor_y = int(cursor_y * (resized_height / original_height))

        if self.low_quality:
            cursor_radius = 6
        elif self.potato_quality:
            cursor_radius = 4
        else:
            cursor_radius = 8

        cursor_color = (5, 199, 147)
        cv2.circle(frame, (cursor_x, cursor_y), cursor_radius, cursor_color, -1)

    def record_screen(self):
        fps = 15
        frame_time = 1 / fps
        with mss.mss() as sct:
            monitor = {
                "left": self.selected_region[0] if self.selected_region else sct.monitors[1]["left"],
                "top": self.selected_region[1] if self.selected_region else sct.monitors[1]["top"],
                "width": self.selected_region[2] if self.selected_region else sct.monitors[1]["width"],
                "height": self.selected_region[3] if self.selected_region else sct.monitors[1]["height"],
            }
            width, height = monitor["width"], monitor["height"]

            if self.low_quality:
                width = max(2, (width // 3) * 2)
                height = max(2, (height // 3) * 2)
            elif self.potato_quality:
                width = max(2, (width // 6) * 2)
                height = max(2, (height // 6) * 2)

            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            out = cv2.VideoWriter(self.output_file, fourcc, fps, (width, height))

            last_frame_time = time.time()
            while self.is_recording:
                if self.is_paused:
                    time.sleep(0.1)
                    continue

                img = sct.grab(monitor)
                frame = np.array(img)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

                if self.low_quality or self.potato_quality:
                    frame = cv2.resize(frame, (width, height), interpolation=cv2.INTER_LINEAR)

                if self.cursor_enabled:
                    cursor_x, cursor_y = pyautogui.position()
                    self.draw_cursor(frame, cursor_x, cursor_y, monitor)

                out.write(frame)

                current_time = time.time()
                elapsed_time = current_time - last_frame_time
                sleep_time = frame_time - elapsed_time
                if sleep_time > 0:
                    time.sleep(sleep_time)
                last_frame_time = time.time()

            out.release()
        
    def stop_recording(self):
        self.is_recording = False
        self.indicator.destroy()
        self.master.deiconify()
        
        self.record_button.configure(text="▶", fg_color="green", hover_color="darkgreen")
        
        print(f"Recording saved: {self.output_file}")

    def update_timer(self):
        start_time = time.time()
        paused_time = 0
        last_pause_time = None

        while self.is_recording:
            if self.is_paused:
                if last_pause_time is None:
                    last_pause_time = time.time()
            else:
                if last_pause_time is not None:
                    paused_time += time.time() - last_pause_time
                    last_pause_time = None

                elapsed_time = int(time.time() - start_time - paused_time)
                minutes = elapsed_time // 60
                seconds = elapsed_time % 60
                self.timer_label.configure(text=f"{minutes:02}:{seconds:02}")

            time.sleep(1)

if __name__ == "__main__":
    root = ctk.CTk()
    
    icon_path = os.path.join(os.path.dirname(__file__), "pointRpy.ico")
    try:
        root.iconbitmap(icon_path)
    except Exception as e:
        print(f"Warning: Icon file not found or invalid. Using default icon. ({e})")
    
    app = RECpy(root)
    root.mainloop()
