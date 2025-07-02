import os
import shutil
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import psutil
from datetime import datetime
from PIL import Image, ImageTk
import time

class RecoveryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Puran File Recovery")
        self.root.geometry("1250x800")
        self.root.configure(bg="#f0f8ff")

        self.selected_drive = tk.StringVar()
        self.selected_category = tk.StringVar(value="[All Files]")
        self.recover_mode = tk.StringVar(value="Just Recover")
        self.deep_scan = tk.BooleanVar()
        self.full_scan = tk.BooleanVar()
        self.find_lost = tk.BooleanVar()
        self.custom_list = tk.BooleanVar()
        self.show_preview_var = tk.BooleanVar(value=True)
        self.select_all_var = tk.BooleanVar()

        self.files = []
        self.stop_scan = False
        self.scan_thread = None

        # New features
        self.is_scanning = False
        self.scan_progress = tk.DoubleVar(value=0.0)  # To track progress
        self.log_list = []

        self.style_ui()
        self.build_gui()

    def style_ui(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="#ffffff", foreground="#000000", fieldbackground="#ffffff", rowheight=28)
        style.configure("Treeview.Heading", font=("Arial", 11, "bold"), background="#add8e6")
        style.configure("TButton", font=("Arial", 10))
        style.configure("TLabel", background="#f0f8ff", font=("Arial", 10))
        style.configure("TCheckbutton", background="#f0f8ff", font=("Arial", 10))
        style.configure("TCombobox", font=("Arial", 10))

    def build_gui(self):
        self.build_drive_table()
        self.build_controls()
        self.build_split_layout()
        self.build_footer()

    def build_drive_table(self):
        columns = ("Drive", "File System", "Total Space", "Free Space")
        self.drive_table = ttk.Treeview(self.root, columns=columns, show="headings", height=4)
        for col in columns:
            self.drive_table.heading(col, text=col)
            self.drive_table.column(col, anchor="center")
        self.drive_table.pack(fill="x", padx=5, pady=(5, 0))
        self.populate_drive_info()

    def populate_drive_info(self):
        self.drive_table.delete(*self.drive_table.get_children())
        for part in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(part.mountpoint)
                total = f"{usage.total / (1024 ** 3):.2f} GB"
                free = f"{usage.free / (1024 ** 3):.2f} GB"
                self.drive_table.insert("", "end", values=(part.device, part.fstype, total, free))
            except:
                self.drive_table.insert("", "end", values=(part.device, part.fstype, "-", "-"))

    def build_controls(self):
        control_frame = tk.Frame(self.root, bg="#f0f8ff")
        control_frame.pack(fill="x", padx=5, pady=5)

        self.scan_btn = ttk.Button(control_frame, text="Scan", command=self.start_scan, width=12)
        self.scan_btn.grid(row=0, column=0, padx=5)

        self.stop_btn = ttk.Button(control_frame, text="Stop", command=self.cancel_scan, width=12)
        self.stop_btn.grid(row=0, column=1, padx=5)

        ttk.Label(control_frame, text="Recover Mode:").grid(row=0, column=2, padx=5)
        recover_menu = ttk.Combobox(control_frame, textvariable=self.recover_mode, state="readonly", width=30)
        recover_menu['values'] = ["Just Recover", "Recover with Folder Structure", "Recover with Custom Size"]
        recover_menu.grid(row=0, column=3, padx=5)

        category_menu = ttk.Combobox(control_frame, textvariable=self.selected_category, state="readonly", width=20)
        category_menu['values'] = ["[Pictures]", "[Music]", "[Documents]", "[Videos]", "[Compressed]", "[All Files]"]
        category_menu.grid(row=0, column=4, padx=5)

        ttk.Checkbutton(control_frame, text="Deep Scan", variable=self.deep_scan).grid(row=0, column=5, padx=2)
        ttk.Checkbutton(control_frame, text="Full Scan", variable=self.full_scan).grid(row=0, column=6, padx=2)
        ttk.Checkbutton(control_frame, text="Find lost files", variable=self.find_lost).grid(row=0, column=7, padx=2)
        ttk.Checkbutton(control_frame, text="Custom List", variable=self.custom_list).grid(row=0, column=8, padx=2)

        ttk.Button(control_frame, text="Recover Files", command=self.recover_files, width=15).grid(row=0, column=9, padx=10)

        # Progress Bar for scanning
        self.progress_bar = ttk.Progressbar(self.root, variable=self.scan_progress, maximum=100)
        self.progress_bar.pack(fill="x", padx=5, pady=5)

    def build_split_layout(self):
        self.split_frame = tk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.split_frame.pack(fill="both", expand=True, padx=5, pady=5)

        self.folder_tree = ttk.Treeview(self.split_frame)
        self.folder_tree.heading("#0", text="Folders")
        self.folder_tree.bind("<<TreeviewSelect>>", self.filter_by_folder)
        self.split_frame.add(self.folder_tree, width=280)

        self.file_table = ttk.Treeview(self.split_frame, columns=("File Name", "File Path", "File Size", "Condition"), show="headings")
        for col in ("File Name", "File Path", "File Size", "Condition"):
            self.file_table.heading(col, text=col)
            self.file_table.column(col, anchor="w")
        self.split_frame.add(self.file_table)
        self.file_table.bind("<<TreeviewSelect>>", self.on_file_select)

        self.preview_label = tk.Label(self.root, text="No Preview Available", font=("Arial", 11), bg="#f0f8ff")
        self.preview_label.pack(fill="x")

        preview_frame = tk.Frame(self.root, bg="#f0f8ff")
        preview_frame.pack(fill="x", padx=5)
        ttk.Checkbutton(preview_frame, text="Show Preview", variable=self.show_preview_var).pack(side="left")

    def build_footer(self):
        bottom = tk.Frame(self.root, bg="#f0f8ff")
        bottom.pack(fill="x", padx=5, pady=3)
        ttk.Checkbutton(bottom, text="Select All", variable=self.select_all_var, command=self.toggle_select_all).pack(side="left")
        ttk.Button(bottom, text="Save List", command=self.save_file_list).pack(side="right")

    def start_scan(self):
        if not self.drive_table.selection():
            messagebox.showerror("Error", "Please select a drive.")
            return
        selected = self.drive_table.item(self.drive_table.selection()[0])["values"][0]
        self.selected_drive.set(selected)

        # Disable scan button, enable stop button, and change button colors
        self.scan_btn.config(state="disabled", text="Scanning...", style="TButton")
        self.stop_btn.config(state="normal", text="Stop Scanning", style="TButton")

        self.stop_scan = False
        self.folder_tree.delete(*self.folder_tree.get_children())
        self.file_table.delete(*self.file_table.get_children())
        self.scan_progress.set(0)  # Reset progress
        self.scan_thread = threading.Thread(target=self.scan_drive)
        self.scan_thread.start()

    def cancel_scan(self):
        self.stop_scan = True
        self.stop_btn.config(state="disabled", text="Stopped", style="TButton")
        self.scan_btn.config(state="normal", text="Scan", style="TButton")

    def scan_drive(self):
        drive = self.selected_drive.get()
        exts = {
            "[Pictures]": [".jpg", ".jpeg", ".png", ".bmp", ".gif"],
            "[Music]": [".mp3", ".wav", ".aac"],
            "[Documents]": [".txt", ".doc", ".docx", ".pdf"],
            "[Videos]": [".mp4", ".mkv", ".avi"],
            "[Compressed]": [".zip", ".rar", ".7z"],
            "[All Files]": None
        }
        selected_exts = exts.get(self.selected_category.get(), None)
        self.files = []
        total_files = 0
        for root_dir, _, files in os.walk(drive):
            if self.stop_scan:
                break
            folder_node = self.folder_tree.insert("", "end", text=root_dir, values=[root_dir], open=False)
            total_files += len(files)
            for idx, file in enumerate(files):
                if self.stop_scan:
                    break
                if selected_exts and not any(file.lower().endswith(ext) for ext in selected_exts):
                    continue
                path = os.path.join(root_dir, file)
                size = self.get_file_size(path)
                self.files.append((file, path, size, "Good", root_dir))
                self.file_table.insert("", "end", values=(file, path, size, "Good"))

                # Update progress
                self.scan_progress.set((idx + 1) / total_files * 100)
                self.root.update_idletasks()
                
            # Simulate delay
            time.sleep(0.1)

    def filter_by_folder(self, event):
        selection = self.folder_tree.selection()
        if not selection:
            return
        folder = self.folder_tree.item(selection[0])["text"]
        self.file_table.delete(*self.file_table.get_children())
        for file, path, size, cond, fldr in self.files:
            if fldr == folder:
                self.file_table.insert("", "end", values=(file, path, size, cond))

    def get_file_size(self, path):
        try:
            size = os.path.getsize(path)
            return f"{size / (1024 ** 2):.2f} MB"
        except:
            return "Unknown"

    def on_file_select(self, event):
        if not self.show_preview_var.get():
            return
        selected = self.file_table.focus()
        if not selected:
            return
        values = self.file_table.item(selected)['values']
        if not values:
            return
        path = values[1]
        if path.lower().endswith((".jpg", ".jpeg", ".png")):
            try:
                img = Image.open(path)
                img.thumbnail((200, 200))
                img_tk = ImageTk.PhotoImage(img)
                self.preview_label.config(image=img_tk, text="")
                self.preview_label.image = img_tk
            except:
                self.preview_label.config(text="Image preview failed", image="")
        elif path.lower().endswith(".txt"):
            try:
                with open(path, "r", errors="ignore") as f:
                    content = f.read(500)
                self.preview_label.config(text=content, image="")
            except:
                self.preview_label.config(text="Text preview failed", image="")
        else:
            self.preview_label.config(text="Preview not supported", image="")

    def toggle_select_all(self):
        for item in self.file_table.get_children():
            self.file_table.selection_add(item) if self.select_all_var.get() else self.file_table.selection_remove(item)

    def save_file_list(self):
        path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
        if not path:
            return
        with open(path, "w") as f:
            for item in self.file_table.selection():
                values = self.file_table.item(item)["values"]
                f.write("\t".join(map(str, values)) + "\n")
        messagebox.showinfo("Saved", "File list saved.")

    def recover_files(self):
        recovery_folder = filedialog.askdirectory(title="Select Recovery Folder")
        if not recovery_folder:
            return
        recovered = 0
        for item in self.file_table.selection():
            values = self.file_table.item(item)['values']
            path = values[1]
            try:
                if self.recover_mode.get() == "Recover with Folder Structure":
                    rel_path = os.path.relpath(path, self.selected_drive.get())
                    dest_path = os.path.join(recovery_folder, rel_path)
                    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                else:
                    dest_path = os.path.join(recovery_folder, os.path.basename(path))
                shutil.copy(path, dest_path)
                recovered += 1
            except Exception as e:
                print(f"Failed to recover {path}: {e}")
        messagebox.showinfo("Recovery Complete", f"Recovered {recovered} file(s).")

if __name__ == '__main__':
    root = tk.Tk()
    app = RecoveryApp(root)
    root.mainloop()
