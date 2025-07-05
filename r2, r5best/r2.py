import os
import shutil
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import psutil
from datetime import datetime
from PIL import Image, ImageTk
import magic  # For file type detection
import hashlib
import logging
import webbrowser
from collections import defaultdict
import pickle
import time

class ProfessionalRecoveryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("DataRescue Pro")
        self.root.geometry("1400x900")
        self.setup_logging()
        
        # Modern color scheme
        self.bg_color = "#2d2d2d"
        self.fg_color = "#e0e0e0"
        self.accent_color = "#4a90e2"
        self.secondary_color = "#3a3a3a"
        self.error_color = "#e74c3c"
        self.success_color = "#2ecc71"
        
        self.root.configure(bg=self.bg_color)
        
        # State variables
        self.selected_drive = tk.StringVar()
        self.selected_category = tk.StringVar(value="[All Files]")
        self.recover_mode = tk.StringVar(value="Standard Recovery")
        self.deep_scan = tk.BooleanVar(value=True)
        self.full_scan = tk.BooleanVar()
        self.find_lost = tk.BooleanVar(value=True)
        self.show_preview_var = tk.BooleanVar(value=True)
        self.select_all_var = tk.BooleanVar()
        self.dark_mode = tk.BooleanVar(value=True)
        
        # File tracking
        self.files = []
        self.file_signatures = {}
        self.recovery_history = []
        self.scan_stats = {"total_files": 0, "recoverable": 0, "damaged": 0}
        
        # Thread control
        self.stop_scan = False
        self.scan_thread = None
        self.is_scanning = False
        self.scan_progress = tk.DoubleVar(value=0.0)
        self.scan_status = tk.StringVar(value="Ready")
        
        # Initialize UI
        self.style_ui()
        self.build_gui()
        self.load_file_signatures()
        
        # Bind keyboard shortcuts
        self.root.bind("<F1>", self.show_help)
        self.root.bind("<Control-s>", lambda e: self.save_file_list())
        self.root.bind("<Control-r>", lambda e: self.start_scan())
        
    def setup_logging(self):
        logging.basicConfig(
            filename='data_rescue.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger()
        
    def style_ui(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        # Main style configurations
        style.configure('.', 
                      background=self.bg_color,
                      foreground=self.fg_color,
                      fieldbackground=self.secondary_color)
        
        # Treeview styles
        style.configure('Treeview',
                        background=self.secondary_color,
                        foreground=self.fg_color,
                        fieldbackground=self.secondary_color,
                        rowheight=28,
                        font=('Segoe UI', 10))
        
        style.configure('Treeview.Heading',
                       font=('Segoe UI', 10, 'bold'),
                       background=self.accent_color,
                       foreground='white',
                       relief='flat')
        
        style.map('Treeview',
                 background=[('selected', self.accent_color)],
                 foreground=[('selected', 'white')])
        
        # Button styles
        style.configure('TButton',
                       font=('Segoe UI', 10),
                       padding=6,
                       width=12,
                       background=self.accent_color,
                       foreground='white',
                       relief='flat')
        
        style.map('TButton',
                 background=[('active', '#5ba8d6'), ('disabled', '#3a3a3a')],
                 foreground=[('disabled', '#7a7a7a')])
        
        # Label styles
        style.configure('TLabel',
                       background=self.bg_color,
                       foreground=self.fg_color,
                       font=('Segoe UI', 10))
        
        # Entry/Combobox styles
        style.configure('TEntry',
                       fieldbackground=self.secondary_color,
                       foreground=self.fg_color)
        
        style.configure('TCombobox',
                       fieldbackground=self.secondary_color,
                       foreground=self.fg_color)
        
        # Progress bar
        style.configure('Horizontal.TProgressbar',
                       thickness=20,
                       background=self.accent_color,
                       troughcolor=self.secondary_color)
        
        # Notebook style for tabs
        style.configure('TNotebook',
                       background=self.bg_color,
                       borderwidth=0)
        
        style.configure('TNotebook.Tab',
                       background=self.secondary_color,
                       foreground=self.fg_color,
                       padding=[10, 5],
                       font=('Segoe UI', 9, 'bold'))
        
        style.map('TNotebook.Tab',
                 background=[('selected', self.accent_color)],
                 foreground=[('selected', 'white')])
    
    def build_gui(self):
        self.create_menu()
        self.build_header()
        self.build_main_panels()
        self.build_sidebar()
        self.build_status_bar()
        
    def create_menu(self):
        menubar = tk.Menu(self.root)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="New Recovery", command=self.reset_app)
        file_menu.add_command(label="Save Scan Results", command=self.save_scan_results)
        file_menu.add_command(label="Load Scan Results", command=self.load_scan_results)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        
        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label="Select All", command=self.select_all_files)
        edit_menu.add_command(label="Clear Selection", command=self.clear_selection)
        edit_menu.add_separator()
        edit_menu.add_command(label="Filter Options", command=self.show_filter_dialog)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_checkbutton(label="Dark Mode", variable=self.dark_mode, command=self.toggle_dark_mode)
        view_menu.add_checkbutton(label="Show Preview", variable=self.show_preview_var)
        view_menu.add_command(label="Customize Columns", command=self.customize_columns)
        menubar.add_cascade(label="View", menu=view_menu)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="User Guide", command=self.show_user_guide)
        help_menu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)
        
        self.root.config(menu=menubar)
    
    def build_header(self):
        header_frame = ttk.Frame(self.root)
        header_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        # Logo and title
        logo_label = ttk.Label(header_frame, text="DataRescue Pro", font=('Segoe UI', 16, 'bold'))
        logo_label.pack(side="left")
        
        # Drive selection
        drive_frame = ttk.Frame(header_frame)
        drive_frame.pack(side="right", fill="x", expand=True)
        
        ttk.Label(drive_frame, text="Select Drive:").pack(side="left", padx=5)
        self.drive_combobox = ttk.Combobox(drive_frame, textvariable=self.selected_drive, state="readonly", width=15)
        self.drive_combobox.pack(side="left", padx=5)
        self.populate_drives()
        
        # Scan button
        self.scan_btn = ttk.Button(drive_frame, text="Start Scan", command=self.start_scan)
        self.scan_btn.pack(side="left", padx=5)
        
        # Stop button
        self.stop_btn = ttk.Button(drive_frame, text="Stop", command=self.cancel_scan, state="disabled")
        self.stop_btn.pack(side="left", padx=5)
    
    def build_main_panels(self):
        main_panel = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_panel.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Left panel - File browser
        left_panel = ttk.Frame(main_panel)
        main_panel.add(left_panel, weight=3)
        
        # File table with scrollbars
        self.file_table_frame = ttk.Frame(left_panel)
        self.file_table_frame.pack(fill="both", expand=True)
        
        self.file_table_scroll_y = ttk.Scrollbar(self.file_table_frame)
        self.file_table_scroll_y.pack(side="right", fill="y")
        
        self.file_table_scroll_x = ttk.Scrollbar(self.file_table_frame, orient="horizontal")
        self.file_table_scroll_x.pack(side="bottom", fill="x")
        
        self.file_table = ttk.Treeview(
            self.file_table_frame,
            columns=("File Name", "Path", "Size", "Status", "Type", "Modified", "Preview"),
            yscrollcommand=self.file_table_scroll_y.set,
            xscrollcommand=self.file_table_scroll_x.set,
            selectmode="extended"
        )
        
        self.file_table.pack(fill="both", expand=True)
        
        self.file_table_scroll_y.config(command=self.file_table.yview)
        self.file_table_scroll_x.config(command=self.file_table.xview)
        
        # Configure columns
        self.file_table.heading("#0", text="ID")
        self.file_table.column("#0", width=40, stretch=False)
        
        columns = {
            "File Name": 200,
            "Path": 300,
            "Size": 80,
            "Status": 100,
            "Type": 120,
            "Modified": 120,
            "Preview": 150
        }
        
        for col, width in columns.items():
            self.file_table.heading(col, text=col)
            self.file_table.column(col, width=width, anchor="w")
        
        # Right panel - Preview and details
        right_panel = ttk.PanedWindow(main_panel, orient=tk.VERTICAL)
        main_panel.add(right_panel, weight=1)
        
        # Preview panel
        preview_frame = ttk.LabelFrame(right_panel, text="File Preview", padding=10)
        right_panel.add(preview_frame)
        
        self.preview_canvas = tk.Canvas(preview_frame, bg=self.secondary_color, height=200)
        self.preview_canvas.pack(fill="both", expand=True)
        
        self.preview_text = scrolledtext.ScrolledText(
            preview_frame,
            wrap=tk.WORD,
            bg=self.secondary_color,
            fg=self.fg_color,
            font=('Consolas', 9)
        )
        
        # Details panel
        details_frame = ttk.LabelFrame(right_panel, text="File Details", padding=10)
        right_panel.add(details_frame)
        
        self.details_text = scrolledtext.ScrolledText(
            details_frame,
            wrap=tk.WORD,
            bg=self.secondary_color,
            fg=self.fg_color,
            font=('Consolas', 9),
            height=10
        )
        self.details_text.pack(fill="both", expand=True)
        
        # Bind events
        self.file_table.bind("<<TreeviewSelect>>", self.on_file_select)
    
    def build_sidebar(self):
        sidebar = ttk.Frame(self.root)
        sidebar.pack(fill="x", padx=10, pady=(0, 5))
        
        # Recovery options
        recovery_frame = ttk.LabelFrame(sidebar, text="Recovery Options", padding=10)
        recovery_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(recovery_frame, text="Recovery Mode:").grid(row=0, column=0, sticky="w")
        recovery_modes = ttk.Combobox(
            recovery_frame,
            textvariable=self.recover_mode,
            values=[
                "Standard Recovery",
                "Recover with Folder Structure",
                "Recover with Metadata",
                "Raw Recovery (Advanced)"
            ],
            state="readonly"
        )
        recovery_modes.grid(row=0, column=1, sticky="ew", pady=5)
        
        # File type filter
        ttk.Label(recovery_frame, text="File Type:").grid(row=1, column=0, sticky="w")
        file_types = ttk.Combobox(
            recovery_frame,
            textvariable=self.selected_category,
            values=[
                "[All Files]",
                "[Pictures]",
                "[Documents]",
                "[Audio]",
                "[Video]",
                "[Archives]",
                "[Database]",
                "[Executables]",
                "[Custom Filter]"
            ],
            state="readonly"
        )
        file_types.grid(row=1, column=1, sticky="ew", pady=5)
        
        # Scan options
        options_frame = ttk.LabelFrame(sidebar, text="Scan Options", padding=10)
        options_frame.pack(fill="x")
        
        ttk.Checkbutton(options_frame, text="Deep Scan", variable=self.deep_scan).grid(row=0, column=0, sticky="w", pady=2)
        ttk.Checkbutton(options_frame, text="Full Scan", variable=self.full_scan).grid(row=1, column=0, sticky="w", pady=2)
        ttk.Checkbutton(options_frame, text="Find Lost Files", variable=self.find_lost).grid(row=2, column=0, sticky="w", pady=2)
        ttk.Checkbutton(options_frame, text="Verify File Integrity", variable=self.find_lost).grid(row=3, column=0, sticky="w", pady=2)
        
        # Action buttons
        action_frame = ttk.Frame(sidebar)
        action_frame.pack(fill="x", pady=(10, 0))
        
        ttk.Button(action_frame, text="Recover Selected", command=self.recover_files).pack(side="left", fill="x", expand=True, padx=2)
        ttk.Button(action_frame, text="Save List", command=self.save_file_list).pack(side="left", fill="x", expand=True, padx=2)
        ttk.Button(action_frame, text="Clear Results", command=self.clear_results).pack(side="left", fill="x", expand=True, padx=2)
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(
            sidebar,
            variable=self.scan_progress,
            maximum=100,
            style='Horizontal.TProgressbar'
        )
        self.progress_bar.pack(fill="x", pady=(10, 0))
        
        ttk.Label(sidebar, textvariable=self.scan_status).pack()
    
    def build_status_bar(self):
        status_bar = ttk.Frame(self.root, height=25)
        status_bar.pack(fill="x", padx=10, pady=(0, 10))
        
        self.status_label = ttk.Label(
            status_bar,
            text="Ready",
            relief="sunken",
            anchor="w",
            font=('Segoe UI', 9)
        )
        self.status_label.pack(fill="x")
        
        self.stats_label = ttk.Label(
            status_bar,
            text="Files: 0 | Recoverable: 0 | Damaged: 0",
            relief="sunken",
            anchor="e",
            font=('Segoe UI', 9)
        )
        self.stats_label.pack(fill="x")
    
    def populate_drives(self):
        drives = []
        for part in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(part.mountpoint)
                drive_info = f"{part.device} ({usage.free / (1024**3):.1f}GB free)"
                drives.append((part.device, drive_info))
            except:
                continue
        
        self.drive_combobox['values'] = [d[1] for d in drives]
        self.drive_map = {d[1]: d[0] for d in drives}
        
        if drives:
            self.drive_combobox.current(0)
            self.selected_drive.set(self.drive_map[drives[0][1]])
    
    def start_scan(self):
        drive = self.selected_drive.get()
        if not drive:
            messagebox.showerror("Error", "Please select a drive to scan")
            return
        
        # Reset UI for new scan
        self.reset_scan_ui()
        self.scan_status.set("Scanning...")
        self.status_label.config(text=f"Scanning {drive}...")
        
        # Start scan in background thread
        self.scan_thread = threading.Thread(
            target=self.perform_scan,
            args=(drive,),
            daemon=True
        )
        self.scan_thread.start()
    
    def perform_scan(self, drive):
        try:
            self.is_scanning = True
            self.stop_scan = False
            
            # Initialize scan statistics
            self.scan_stats = {"total_files": 0, "recoverable": 0, "damaged": 0}
            
            # Get file type filters
            file_types = self.get_file_types()
            
            # Walk through directory structure
            for root, dirs, files in os.walk(drive):
                if self.stop_scan:
                    break
                
                # Update status
                self.scan_status.set(f"Scanning: {root}")
                
                for filename in files:
                    if self.stop_scan:
                        break
                    
                    filepath = os.path.join(root, filename)
                    
                    try:
                        # Get file info
                        file_stat = os.stat(filepath)
                        file_size = file_stat.st_size
                        modified = datetime.fromtimestamp(file_stat.st_mtime)
                        
                        # Check if file matches selected types
                        file_ext = os.path.splitext(filename)[1].lower()
                        if file_types and file_ext not in file_types:
                            continue
                        
                        # Check file integrity
                        status = self.check_file_integrity(filepath, file_ext)
                        
                        # Add to file list
                        file_type = magic.from_file(filepath, mime=True)
                        
                        self.files.append({
                            "name": filename,
                            "path": filepath,
                            "size": file_size,
                            "status": status,
                            "type": file_type,
                            "modified": modified,
                            "folder": root
                        })
                        
                        # Update statistics
                        self.scan_stats["total_files"] += 1
                        if status == "Good":
                            self.scan_stats["recoverable"] += 1
                        else:
                            self.scan_stats["damaged"] += 1
                        
                        # Update UI periodically
                        if self.scan_stats["total_files"] % 100 == 0:
                            self.update_scan_ui()
                    
                    except Exception as e:
                        self.logger.error(f"Error scanning {filepath}: {str(e)}")
                        continue
            
            # Final UI update
            self.update_scan_ui()
            self.scan_status.set("Scan completed")
            self.status_label.config(text=f"Scan completed. Found {self.scan_stats['total_files']} files")
            
        except Exception as e:
            self.logger.error(f"Scan error: {str(e)}")
            self.scan_status.set("Scan failed")
            self.status_label.config(text=f"Scan failed: {str(e)}")
        finally:
            self.is_scanning = False
            self.stop_scan = False
            self.scan_btn.config(state="normal")
            self.stop_btn.config(state="disabled")
    
    def update_scan_ui(self):
        # Update progress bar
        self.scan_progress.set((self.scan_stats["total_files"] % 1000) / 10)
        
        # Update statistics label
        self.stats_label.config(
            text=f"Files: {self.scan_stats['total_files']} | "
                 f"Recoverable: {self.scan_stats['recoverable']} | "
                 f"Damaged: {self.scan_stats['damaged']}"
        )
        
        # Update file table periodically to prevent UI freeze
        if self.scan_stats["total_files"] % 500 == 0:
            self.update_file_table()
    
    def update_file_table(self):
        self.file_table.delete(*self.file_table.get_children())
        
        for idx, file_info in enumerate(self.files[-500:], 1):  # Show last 500 files
            self.file_table.insert(
                "",
                "end",
                iid=idx,
                text=str(idx),
                values=(
                    file_info["name"],
                    file_info["path"],
                    self.format_size(file_info["size"]),
                    file_info["status"],
                    file_info["type"],
                    file_info["modified"].strftime("%Y-%m-%d %H:%M"),
                    "Available" if file_info["status"] == "Good" else "Corrupted"
                ),
                tags=(file_info["status"],)
            )
        
        # Configure tag colors
        self.file_table.tag_configure("Good", foreground="green")
        self.file_table.tag_configure("Damaged", foreground="red")
        self.file_table.tag_configure("Corrupted", foreground="orange")
    
    def check_file_integrity(self, filepath, file_ext):
        try:
            # Check basic readability
            with open(filepath, 'rb') as f:
                header = f.read(512)
                
                # Check against known file signatures
                if file_ext in self.file_signatures:
                    expected_sig = self.file_signatures[file_ext]
                    if not header.startswith(expected_sig):
                        return "Damaged"
                
                # Additional checks based on file type
                if file_ext in ['.jpg', '.jpeg', '.png']:
                    try:
                        Image.open(filepath).verify()
                    except:
                        return "Corrupted"
                
                return "Good"
        except:
            return "Damaged"
    
    def get_file_types(self):
        file_type_map = {
            "[All Files]": None,
            "[Pictures]": ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'],
            "[Documents]": ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt', '.rtf'],
            "[Audio]": ['.mp3', '.wav', '.aac', '.flac', '.ogg', '.wma'],
            "[Video]": ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv'],
            "[Archives]": ['.zip', '.rar', '.7z', '.tar', '.gz'],
            "[Database]": ['.db', '.sqlite', '.mdb', '.accdb'],
            "[Executables]": ['.exe', '.dll', '.msi', '.bat']
        }
        
        selected = self.selected_category.get()
        return file_type_map.get(selected, None)
    
    def format_size(self, size):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} TB"
    
    def on_file_select(self, event):
        selected = self.file_table.selection()
        if not selected or not self.show_preview_var.get():
            return
        
        # Get first selected file
        item = self.file_table.item(selected[0])
        filepath = item['values'][1]
        file_type = item['values'][4]
        
        # Clear previous preview
        self.preview_canvas.delete("all")
        self.preview_text.delete(1.0, tk.END)
        
        try:
            # Show image preview
            if file_type.startswith('image/'):
                img = Image.open(filepath)
                img.thumbnail((400, 400))
                img_tk = ImageTk.PhotoImage(img)
                
                self.preview_canvas.create_image(
                    200, 200,
                    image=img_tk,
                    anchor="center"
                )
                self.preview_canvas.image = img_tk
            
            # Show text preview
            elif file_type.startswith('text/') or file_type in ['application/pdf', 'application/json']:
                with open(filepath, 'r', errors='ignore') as f:
                    content = f.read(2000)
                self.preview_text.insert(1.0, content)
                self.preview_text.pack(fill="both", expand=True)
            
            # Show hex preview for binaries
            else:
                with open(filepath, 'rb') as f:
                    content = f.read(512)
                hex_dump = ' '.join(f'{byte:02x}' for byte in content)
                self.preview_text.insert(1.0, hex_dump)
                self.preview_text.pack(fill="both", expand=True)
        
        except Exception as e:
            self.preview_text.insert(1.0, f"Preview not available: {str(e)}")
            self.preview_text.pack(fill="both", expand=True)
        
        # Update file details
        self.update_file_details(item)
    
    def update_file_details(self, item):
        self.details_text.delete(1.0, tk.END)
        
        details = [
            f"File Name: {item['values'][0]}",
            f"Path: {item['values'][1]}",
            f"Size: {item['values'][2]}",
            f"Status: {item['values'][3]}",
            f"Type: {item['values'][4]}",
            f"Modified: {item['values'][5]}",
            "\nMetadata:",
            f"- MD5: {self.calculate_hash(item['values'][1], 'md5')}",
            f"- SHA1: {self.calculate_hash(item['values'][1], 'sha1')}",
            f"- File Attributes: {self.get_file_attributes(item['values'][1])}"
        ]
        
        self.details_text.insert(1.0, '\n'.join(details))
    
    def calculate_hash(self, filepath, algorithm='md5'):
        try:
            hash_func = getattr(hashlib, algorithm)()
            with open(filepath, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    hash_func.update(chunk)
            return hash_func.hexdigest()
        except:
            return "N/A"
    
    def get_file_attributes(self, filepath):
        try:
            attrs = []
            if os.access(filepath, os.R_OK): attrs.append("Readable")
            if os.access(filepath, os.W_OK): attrs.append("Writable")
            if os.access(filepath, os.X_OK): attrs.append("Executable")
            return ', '.join(attrs) if attrs else "No special attributes"
        except:
            return "Unknown"
    
    def recover_files(self):
        selected_items = self.file_table.selection()
        if not selected_items:
            messagebox.showwarning("Warning", "Please select files to recover")
            return
        
        # Ask for destination folder
        dest_folder = filedialog.askdirectory(title="Select Recovery Destination")
        if not dest_folder:
            return
        
        # Check write permissions
        if not os.access(dest_folder, os.W_OK):
            messagebox.showerror("Error", "No write permission in destination folder")
            return
        
        # Start recovery
        recovery_thread = threading.Thread(
            target=self.perform_recovery,
            args=(selected_items, dest_folder),
            daemon=True
        )
        recovery_thread.start()
    
    def perform_recovery(self, selected_items, dest_folder):
        total = len(selected_items)
        success = 0
        errors = 0
        
        self.scan_status.set("Recovering files...")
        self.status_label.config(text=f"Recovering {total} files...")
        
        for i, item_id in enumerate(selected_items, 1):
            if self.stop_scan:
                break
            
            item = self.file_table.item(item_id)
            filepath = item['values'][1]
            filename = item['values'][0]
            status = item['values'][3]
            
            try:
                # Skip damaged files unless forced
                if status != "Good" and not messagebox.askyesno(
                    "Warning",
                    f"File {filename} appears to be {status.lower()}. Attempt recovery anyway?"
                ):
                    errors += 1
                    continue
                
                # Handle different recovery modes
                recovery_mode = self.recover_mode.get()
                
                if recovery_mode == "Standard Recovery":
                    dest_path = os.path.join(dest_folder, filename)
                    shutil.copy2(filepath, dest_path)
                
                elif recovery_mode == "Recover with Folder Structure":
                    rel_path = os.path.relpath(filepath, self.selected_drive.get())
                    dest_path = os.path.join(dest_folder, rel_path)
                    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                    shutil.copy2(filepath, dest_path)
                
                elif recovery_mode == "Recover with Metadata":
                    dest_path = os.path.join(dest_folder, filename)
                    shutil.copy2(filepath, dest_path)
                    # TODO: Add metadata restoration
                
                elif recovery_mode == "Raw Recovery (Advanced)":
                    # TODO: Implement raw recovery from disk sectors
                    pass
                
                success += 1
                self.logger.info(f"Recovered {filepath} to {dest_path}")
            
            except Exception as e:
                errors += 1
                self.logger.error(f"Failed to recover {filepath}: {str(e)}")
            
            # Update progress
            self.scan_progress.set((i / total) * 100)
            self.scan_status.set(f"Recovered {i} of {total} files")
        
        # Show completion message
        self.scan_status.set("Recovery completed")
        self.status_label.config(
            text=f"Recovery completed: {success} succeeded, {errors} failed"
        )
        messagebox.showinfo(
            "Recovery Complete",
            f"Successfully recovered {success} files\n{errors} files could not be recovered"
        )
    
    def save_file_list(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        
        if not filepath:
            return
        
        try:
            with open(filepath, 'w') as f:
                # Write header
                f.write("File Name,Path,Size,Status,Type,Modified,Preview\n")
                
                # Write data
                for item in self.file_table.get_children():
                    values = self.file_table.item(item)['values']
                    f.write(','.join(str(v) for v in values) + '\n')
            
            messagebox.showinfo("Success", "File list saved successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file list: {str(e)}")
    
    def save_scan_results(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".dsr",
            filetypes=[("DataRescue Scan", "*.dsr"), ("All Files", "*.*")]
        )
        
        if not filepath:
            return
        
        try:
            with open(filepath, 'wb') as f:
                pickle.dump({
                    'files': self.files,
                    'scan_stats': self.scan_stats,
                    'drive': self.selected_drive.get(),
                    'timestamp': datetime.now()
                }, f)
            
            messagebox.showinfo("Success", "Scan results saved successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save scan results: {str(e)}")
    
    def load_scan_results(self):
        filepath = filedialog.askopenfilename(
            filetypes=[("DataRescue Scan", "*.dsr"), ("All Files", "*.*")]
        )
        
        if not filepath:
            return
        
        try:
            with open(filepath, 'rb') as f:
                data = pickle.load(f)
            
            self.files = data['files']
            self.scan_stats = data['scan_stats']
            self.selected_drive.set(data['drive'])
            
            self.update_file_table()
            self.stats_label.config(
                text=f"Files: {self.scan_stats['total_files']} | "
                     f"Recoverable: {self.scan_stats['recoverable']} | "
                     f"Damaged: {self.scan_stats['damaged']}"
            )
            
            messagebox.showinfo("Success", "Scan results loaded successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load scan results: {str(e)}")
    
    def reset_scan_ui(self):
        self.file_table.delete(*self.file_table.get_children())
        self.files = []
        self.scan_stats = {"total_files": 0, "recoverable": 0, "damaged": 0}
        self.scan_progress.set(0)
        self.stats_label.config(text="Files: 0 | Recoverable: 0 | Damaged: 0")
        self.scan_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
    
    def cancel_scan(self):
        self.stop_scan = True
        self.scan_status.set("Scan cancelled")
        self.status_label.config(text="Scan cancelled by user")
        self.scan_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
    
    def reset_app(self):
        if messagebox.askyesno("Confirm", "Reset all scan results?"):
            self.reset_scan_ui()
            self.selected_drive.set("")
            self.selected_category.set("[All Files]")
            self.recover_mode.set("Standard Recovery")
            self.scan_status.set("Ready")
            self.status_label.config(text="Ready")
    
    def clear_results(self):
        self.file_table.delete(*self.file_table.get_children())
        self.scan_status.set("Ready")
        self.status_label.config(text="Ready")
    
    def select_all_files(self):
        self.file_table.selection_set(self.file_table.get_children())
    
    def clear_selection(self):
        self.file_table.selection_remove(self.file_table.selection())
    
    def toggle_dark_mode(self):
        if self.dark_mode.get():
            self.bg_color = "#2d2d2d"
            self.fg_color = "#e0e0e0"
            self.secondary_color = "#3a3a3a"
        else:
            self.bg_color = "#f0f0f0"
            self.fg_color = "#333333"
            self.secondary_color = "#ffffff"
        
        self.style_ui()
        self.root.configure(bg=self.bg_color)
    
    def show_filter_dialog(self):
        filter_dialog = tk.Toplevel(self.root)
        filter_dialog.title("Advanced Filter Options")
        filter_dialog.geometry("400x300")
        
        # TODO: Implement advanced filter options
    
    def customize_columns(self):
        # TODO: Implement column customization
        pass
    
    def show_user_guide(self):
        webbrowser.open("https://example.com/datarecovery-guide")
    
    def show_about(self):
        about_dialog = tk.Toplevel(self.root)
        about_dialog.title("About DataRescue Pro")
        about_dialog.geometry("400x300")
        
        ttk.Label(about_dialog, text="DataRescue Pro\nVersion 2.0\n\nProfessional Data Recovery Tool").pack(pady=20)
        ttk.Label(about_dialog, text="© 2023 Data Recovery Solutions").pack(pady=10)
    
    def load_file_signatures(self):
        # Common file signatures (magic numbers)
        self.file_signatures = {
            '.pdf': b'%PDF-',
            '.jpg': b'\xFF\xD8\xFF',
            '.png': b'\x89PNG',
            '.gif': b'GIF89a',
            '.zip': b'PK\x03\x04',
            '.exe': b'MZ',
            '.mp3': b'ID3',
            '.mp4': b'\x00\x00\x00\x18ftyp',
            '.doc': b'\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1',
            '.docx': b'PK\x03\x04'
        }
    
    def show_help(self, event=None):
        help_dialog = tk.Toplevel(self.root)
        help_dialog.title("Help - Keyboard Shortcuts")
        help_dialog.geometry("500x400")
        
        help_text = scrolledtext.ScrolledText(
            help_dialog,
            wrap=tk.WORD,
            font=('Consolas', 10)
        )
        help_text.pack(fill="both", expand=True)
        
        shortcuts = [
            ("F1", "Show this help dialog"),
            ("Ctrl+S", "Save file list"),
            ("Ctrl+R", "Start scan"),
            ("Ctrl+Q", "Quit application"),
            ("Ctrl+A", "Select all files"),
            ("Esc", "Cancel current operation")
        ]
        
        help_text.insert(tk.END, "Keyboard Shortcuts:\n\n")
        for shortcut, desc in shortcuts:
            help_text.insert(tk.END, f"{shortcut:<10} {desc}\n")
        
        help_text.config(state="disabled")

if __name__ == '__main__':
    root = tk.Tk()
    app = ProfessionalRecoveryApp(root)
    root.mainloop()