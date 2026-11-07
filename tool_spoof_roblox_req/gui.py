import os
import tkinter as tk
from tkinter import messagebox, simpledialog, Toplevel
import sys
from tkinter import ttk

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import create_user_agent, spoof_script

class HardwareConfigDialog(Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Hardware Configuration")
        self.geometry("400x450")
        self.resizable(False, False)

        self.hardware = {}

        # URL Entry
        tk.Label(self, text="RAM (MB):").grid(row=0, column=0, padx=10, pady=5, sticky="e")
        self.mem_entry = tk.Entry(self, width=20)
        self.mem_entry.insert(0, "1993")
        self.mem_entry.grid(row=0, column=1, padx=10, pady=5)

        # Native Resolution
        tk.Label(self, text="Native Res:").grid(row=1, column=0, padx=10, pady=5, sticky="e")
        self.native_entry = tk.Entry(self, width=20)
        self.native_entry.insert(0, "1280x720")
        self.native_entry.grid(row=1, column=1, padx=10, pady=5)

        # Viewport Resolution
        tk.Label(self, text="Viewport Res:").grid(row=2, column=0, padx=10, pady=5, sticky="e")
        self.viewport_entry = tk.Entry(self, width=20)
        self.viewport_entry.insert(0, "1280x720")
        self.viewport_entry.grid(row=2, column=1, padx=10, pady=5)

        # GUI Scaling
        tk.Label(self, text="GUI Scaling:").grid(row=3, column=0, padx=10, pady=5, sticky="e")
        self.gui_entry = tk.Entry(self, width=20)
        self.gui_entry.insert(0, "853x480")
        self.gui_entry.grid(row=3, column=1, padx=10, pady=5)

        # Android Model
        tk.Label(self, text="Android Model:").grid(row=4, column=0, padx=10, pady=5, sticky="e")
        self.model_entry = tk.Entry(self, width=20)
        self.model_entry.insert(0, "Samsung SM-A5560")
        self.model_entry.grid(row=4, column=1, padx=10, pady=5)

        # Android Version
        tk.Label(self, text="Android Version:").grid(row=5, column=0, padx=10, pady=5, sticky="e")
        self.version_entry = tk.Entry(self, width=20)
        self.version_entry.insert(0, "12")
        self.version_entry.grid(row=5, column=1, padx=10, pady=5)

        # OK Button
        tk.Button(self, text="OK", command=self.ok, bg="#4CAF50", fg="white",
                  font=("Arial", 10, "bold"), pady=10).grid(row=6, column=0, columnspan=2, pady=20)

    def ok(self):
        try:
            self.hardware = {
                "mem": self.mem_entry.get() + "MB",
                "native_res": self.native_entry.get(),
                "viewport_res": self.viewport_entry.get(),
                "gui_scaling": self.gui_entry.get(),
                "android_model": self.model_entry.get(),
                "android_ver": self.version_entry.get()
            }
            self.destroy()
        except:
            messagebox.showerror("Error", "Invalid input values")

class RobloxSpooferGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Roblox Request Spoofer")
        self.root.geometry("500x350")
        self.hardware_config = None

        # URL Entry
        tk.Label(root, text="URL:", font=("Arial", 10, "bold")).pack(pady=(10, 0))
        self.url_entry = tk.Entry(root, width=50)
        self.url_entry.pack(pady=5)

        # Roblox Type
        tk.Label(root, text="Type:", font=("Arial", 10, "bold")).pack(pady=(10, 0))
        self.type_var = tk.StringVar(value="global")
        frame_type = tk.Frame(root)
        frame_type.pack(pady=5)
        tk.Radiobutton(frame_type, text="Global", variable=self.type_var, value="global").pack(side="left", padx=10)
        tk.Radiobutton(frame_type, text="VN", variable=self.type_var, value="vn").pack(side="left", padx=10)

        # More Camouflage
        self.cam_var = tk.BooleanVar(value=False)
        tk.Checkbutton(root, text="More Camouflage", variable=self.cam_var).pack(pady=10)

        # Custom Hardware Config Button
        tk.Button(root, text="⚙️ Custom Hardware Config", command=self.open_hardware_dialog,
                  bg="#2196F3", fg="white", font=("Arial", 10)).pack(pady=5)

        # Start Button
        tk.Button(root, text="Start", command=self.start_spoofing, bg="#4CAF50", fg="white",
                  font=("Arial", 12, "bold"), pady=10).pack(fill="x", padx=20, pady=20)

    def open_hardware_dialog(self):
        if not self.hardware_config:
            dialog = HardwareConfigDialog(self.root)
            self.root.wait_window(dialog)
            if dialog.hardware:
                self.hardware_config = dialog.hardware

    def start_spoofing(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Warning", "Please enter a URL")
            return

        try:
            messagebox.showinfo("Starting", "Opening browser with spoofed headers...")
            spoof_script(
                url,
                roblox_type=self.type_var.get(),
                hardware=self.hardware_config
            )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = RobloxSpooferGUI(root)
    root.mainloop()