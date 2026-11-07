import os
import tkinter as tk
from tkinter import messagebox, simpledialog
import sys

# Add parent directory to path to import main module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import create_user_agent, spoof_script

class RobloxSpooferGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Roblox Request Spoofer")
        self.root.geometry("500x400")

        # URL Entry
        tk.Label(root, text="URL:", font=("Arial", 10, "bold")).pack(pady=(10, 0))
        self.url_entry = tk.Entry(root, width=50)
        self.url_entry.pack(pady=5)

        # Roblox Type
        tk.Label(root, text="Type:", font=("Arial", 10, "bold")).pack(pady=(10, 0))
        self.type_var = tk.StringVar(value="global")
        tk.Radiobutton(root, text="Global", variable=self.type_var, value="global").pack(anchor="w", padx=20)
        tk.Radiobutton(root, text="VN", variable=self.type_var, value="vn").pack(anchor="w", padx=20)

        # More Camouflage
        self.cam_var = tk.BooleanVar(value=False)
        tk.Checkbutton(root, text="More Camouflage", variable=self.cam_var).pack(pady=10)

        # Start Button
        tk.Button(root, text="Start", command=self.start_spoofing, bg="#4CAF50", fg="white",
                  font=("Arial", 12, "bold"), pady=10).pack(fill="x", padx=20, pady=20)

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
                more_camouflage=self.cam_var.get()
            )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = RobloxSpooferGUI(root)
    root.mainloop()