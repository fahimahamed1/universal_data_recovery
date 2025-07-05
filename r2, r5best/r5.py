import os
import shutil
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import psutil
from datetime import datetime
from PIL import Image, ImageTk
import magic
import hashlib
import logging
import webbrowser
import pickle
import time
import platform
import subprocess
import humanize
from tkinter.font import Font

class DataRescueProX:
    def __init__(self, root):
        self.root = root
        self.root.title("DataRescue Pro X - Enhanced")
        self.root.geometry("1400x900")
        self.setup_logging()
        
        # Set window icon
        self.set_window_icon()
            
        # Initialize application state
        self.initialize_state()
        
        # Setup UI
        self.setup_styles()
        self.build_ui()
        
        # Load resources
        self.load_file_signatures()
        self.populate_drives()
        
        # Set initial state
        self.update_ui_state()

    def set_window_icon(self):
        """Set window icon with fallback"""
        try:
            self.root.iconbitmap("icon.ico")
        except:
            try:
                img = Image.new('RGB', (1, 1))
                img.save('temp.ico')
                self.root.iconbitmap('temp.ico')
                os.remove('temp.ico')
            except:
                pass

    def initialize_state(self):
        """Initialize all application state variables"""
        # UI state
        self.is_scanning = False
        self.stop_scan = False
        self.scan_thread = None
        self.current_scan_path = ""
        self.scan_paused = False
        
        # Settings
        self.settings = {
            "theme": "light",
            "show_preview": True,
            "scan_depth": 2,
            "max_file_size": 1024 * 1024 * 500,  # 500MB
            "recovery_folder": os.path.expanduser("~/Documents/Recovered_Files"),
            "developer": "Risha Tech Solutions",
            "version": "3.1 Enhanced"
        }
        
        # Data collections
        self.drive_map = {}
        self.files = []
        self.file_signatures = {}
        self.recovery_history = []
        
        # Statistics
        self.scan_stats = {
            "total_files": 0,
            "recoverable": 0,
            "damaged": 0,
            "scanned_bytes": 0,
            "start_time": None,
            "end_time": None
        }
        
        # UI variables
        self.selected_drive = tk.StringVar()
        self.selected_category = tk.StringVar(value="[All Files]")
        self.recover_mode = tk.StringVar(value="Standard Recovery")
        self.deep_scan = tk.BooleanVar(value=True)
        self.full_scan = tk.BooleanVar()
        self.find_lost = tk.BooleanVar(value=True)
        self.show_preview_var = tk.BooleanVar(value=self.settings["show_preview"])
        self.select_all_var = tk.BooleanVar()
        self.theme_var = tk.StringVar(value=self.settings["theme"])
        
        # Progress tracking
        self.scan_progress = tk.DoubleVar(value=0.0)
        self.scan_status = tk.StringVar(value="Ready")
        self.status_text = tk.StringVar(value="Ready to scan")
        self.stats_text = tk.StringVar(value="Files: 0 | Recoverable: 0 | Damaged: 0")

    def setup_logging(self):
        """Configure logging for the application"""
        logging.basicConfig(
            filename='data_rescue_x.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            filemode='w'
        )
        self.logger = logging.getLogger()
        self.logger.addHandler(logging.StreamHandler())

    def setup_styles(self):
        """Configure UI styles and themes"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Modern color scheme - Professional Blue
        self.colors = {
            "light": {
                "bg": "#ffffff",
                "fg": "#333333",
                "secondary": "#f0f5ff",
                "accent": "#2c6fbb",
                "accent2": "#3a8de0",
                "error": "#e74c3c",
                "success": "#27ae60",
                "warning": "#f39c12",
                "header": "#e0ebff",
                "highlight": "#cce0ff",
                "button": "#2c6fbb",
                "button_hover": "#3a8de0",
                "button_active": "#1a5a9a"
            },
            "dark": {
                "bg": "#2d2d2d",
                "fg": "#e0e0e0",
                "secondary": "#3a3a3a",
                "accent": "#3a8de0",
                "accent2": "#2c6fbb",
                "error": "#e74c3c",
                "success": "#27ae60",
                "warning": "#f39c12",
                "header": "#1a1a1a",
                "highlight": "#4a4a4a",
                "button": "#3a8de0",
                "button_hover": "#2c6fbb",
                "button_active": "#1a5a9a"
            }
        }
        
        self.update_styles()

    def update_styles(self):
        """Update styles based on current theme"""
        theme = self.settings["theme"]
        colors = self.colors[theme]
        
        style = ttk.Style()
        
        # Main styles
        style.configure('.', 
                      background=colors["bg"],
                      foreground=colors["fg"],
                      fieldbackground=colors["secondary"],
                      font=('Segoe UI', 10))
        
        # Treeview styles with checkboxes
        style.configure('Treeview',
                      background=colors["secondary"],
                      foreground=colors["fg"],
                      fieldbackground=colors["secondary"],
                      rowheight=28,
                      font=('Segoe UI', 10))
        
        style.configure('Treeview.Heading',
                     font=('Segoe UI', 10, 'bold'),
                     background=colors["accent"],
                     foreground='white',
                     relief='flat')
        
        style.map('Treeview',
                background=[('selected', colors["accent"])],
                foreground=[('selected', 'white')])
        
        # Enhanced button styles
        style.configure('TButton',
                      font=('Segoe UI', 10, 'bold'),
                      padding=8,
                      width=14,
                      background=colors["button"],
                      foreground='white',
                      relief='flat',
                      bordercolor=colors["accent2"])
        
        style.map('TButton',
                background=[('active', colors["button_active"]), 
                          ('disabled', colors["secondary"]),
                          ('hover', colors["button_hover"])],
                foreground=[('disabled', '#7a7a7a')])
        
        # Accent button style
        style.configure('Accent.TButton',
                      background=colors["success"],
                      foreground='white')
        
        style.map('Accent.TButton',
                background=[('active', '#1e8449'), 
                          ('disabled', colors["secondary"]),
                          ('hover', '#2ecc71')])
        
        # Warning button style
        style.configure('Warning.TButton',
                      background=colors["warning"],
                      foreground='white')
        
        # Other widget styles
        style.configure('TLabel',
                      background=colors["bg"],
                      foreground=colors["fg"],
                      font=('Segoe UI', 10))
        
        style.configure('TEntry',
                      fieldbackground=colors["secondary"],
                      foreground=colors["fg"],
                      bordercolor=colors["accent2"])
        
        style.configure('TCombobox',
                      fieldbackground=colors["secondary"],
                      foreground=colors["fg"])
        
        style.configure('Horizontal.TProgressbar',
                      thickness=24,
                      background=colors["accent"],
                      troughcolor=colors["secondary"],
                      bordercolor=colors["accent2"])
        
        style.configure('TNotebook',
                      background=colors["bg"],
                      borderwidth=0)
        
        style.configure('TNotebook.Tab',
                      background=colors["secondary"],
                      foreground=colors["fg"],
                      padding=[12, 4],
                      font=('Segoe UI', 9, 'bold'))
        
        style.map('TNotebook.Tab',
                background=[('selected', colors["accent"])],
                foreground=[('selected', 'white')])
        
        # Update root window background
        self.root.configure(bg=colors["bg"])
        
        # Custom font for headings
        self.heading_font = Font(family='Segoe UI', size=12, weight='bold')

    def build_ui(self):
        """Build the main application UI"""
        self.create_menu()
        self.build_header()
        self.build_main_panels()
        self.build_sidebar()
        self.build_status_bar()
        
        # Set initial focus
        self.drive_combobox.focus_set()

    def create_menu(self):
        """Create the main menu bar"""
        menubar = tk.Menu(self.root)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="New Recovery", command=self.reset_app)
        file_menu.add_command(label="Save Scan Results", command=self.save_scan_results)
        file_menu.add_command(label="Load Scan Results", command=self.load_scan_results)
        file_menu.add_separator()
        file_menu.add_command(label="Preferences", command=self.show_preferences)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit_app)
        menubar.add_cascade(label="File", menu=file_menu)
        
        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label="Select All", command=self.select_all_files)
        edit_menu.add_command(label="Clear Selection", command=self.clear_selection)
        edit_menu.add_separator()
        edit_menu.add_command(label="Advanced Filters", command=self.show_filter_dialog)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_radiobutton(label="Light Theme", variable=self.theme_var, 
                                 value="light", command=self.toggle_theme)
        view_menu.add_radiobutton(label="Dark Theme", variable=self.theme_var,
                                 value="dark", command=self.toggle_theme)
        view_menu.add_checkbutton(label="Show Preview", variable=self.show_preview_var,
                                command=self.toggle_preview)
        menubar.add_cascade(label="View", menu=view_menu)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="User Guide", command=self.show_user_guide)
        help_menu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)
        
        self.root.config(menu=menubar)

    def build_header(self):
        """Build the header section with enhanced buttons"""
        colors = self.colors[self.settings["theme"]]
        
        header_frame = ttk.Frame(self.root, style='TFrame')
        header_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        # Logo and title
        logo_frame = ttk.Frame(header_frame)
        logo_frame.pack(side="left", fill="y")
        
        self.logo_label = ttk.Label(
            logo_frame,
            text="DRX",
            font=('Segoe UI', 18, 'bold'),
            foreground=colors["accent"],
            background=colors["bg"]
        )
        self.logo_label.pack(side="left", padx=5)
        
        title_label = ttk.Label(
            logo_frame,
            text="DataRescue Pro X",
            font=self.heading_font,
            foreground=colors["fg"],
            background=colors["bg"]
        )
        title_label.pack(side="left", padx=5)
        
        # Drive selection frame
        drive_frame = ttk.Frame(header_frame, style='TFrame')
        drive_frame.pack(side="right", fill="x", expand=True)
        
        ttk.Label(drive_frame, text="Select Drive:").pack(side="left", padx=5)
        self.drive_combobox = ttk.Combobox(
            drive_frame,
            textvariable=self.selected_drive, 
            state="readonly", 
            width=25
        )
        self.drive_combobox.pack(side="left", padx=5)
        
        # Enhanced scan button with state management
        self.scan_btn = ttk.Button(
            drive_frame, 
            text="Start Scan", 
            command=self.start_scan,
            style='Accent.TButton'
        )
        self.scan_btn.pack(side="left", padx=5)
        
        # Stop button with warning style
        self.stop_btn = ttk.Button(
            drive_frame, 
            text="Stop Scan", 
            command=self.cancel_scan, 
            state="disabled",
            style='Warning.TButton'
        )
        self.stop_btn.pack(side="left", padx=5)
        
        # Pause/Resume button
        self.pause_btn = ttk.Button(
            drive_frame,
            text="Pause",
            command=self.toggle_pause_scan,
            state="disabled"
        )
        self.pause_btn.pack(side="left", padx=5)
        
        # Refresh drives button
        refresh_btn = ttk.Button(
            drive_frame,
            text="Refresh",
            command=self.populate_drives
        )
        refresh_btn.pack(side="left", padx=5)

    def build_main_panels(self):
        """Build the main content panels with checkbox treeview"""
        main_panel = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_panel.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Left panel - File browser (70% width)
        left_panel = ttk.Frame(main_panel)
        main_panel.add(left_panel, weight=7)
        
        # File table with scrollbars and checkboxes
        self.file_table_frame = ttk.Frame(left_panel)
        self.file_table_frame.pack(fill="both", expand=True)
        
        # Vertical scrollbar
        self.file_table_scroll_y = ttk.Scrollbar(self.file_table_frame)
        self.file_table_scroll_y.pack(side="right", fill="y")
        
        # Horizontal scrollbar
        self.file_table_scroll_x = ttk.Scrollbar(
            self.file_table_frame, 
            orient="horizontal"
        )
        self.file_table_scroll_x.pack(side="bottom", fill="x")
        
        # Create the file table with checkboxes
        self.create_file_table_with_checkboxes()
        
        # Right panel - Preview and details (30% width)
        right_panel = ttk.PanedWindow(main_panel, orient=tk.VERTICAL)
        main_panel.add(right_panel, weight=3)
        
        # Preview panel
        self.build_preview_panel(right_panel)
        
        # Details panel
        self.build_details_panel(right_panel)

    def create_file_table_with_checkboxes(self):
        """Create the main file table with checkboxes"""
        columns = {
            "Selected": 80,  # Checkbox column
            "File Name": 250,
            "Path": 300,
            "Size": 100,
            "Status": 80,
            "Type": 120,
            "Modified": 120
        }
        
        self.file_table = ttk.Treeview(
            self.file_table_frame,
            columns=list(columns.keys()),
            yscrollcommand=self.file_table_scroll_y.set,
            xscrollcommand=self.file_table_scroll_x.set,
            selectmode="extended",
            height=20,
            show="headings"  # Hide the default tree column
        )
        
        self.file_table.pack(fill="both", expand=True)
        
        # Configure scrollbars
        self.file_table_scroll_y.config(command=self.file_table.yview)
        self.file_table_scroll_x.config(command=self.file_table.xview)
        
        # Configure columns
        for col, width in columns.items():
            self.file_table.heading(col, text=col, anchor="w")
            self.file_table.column(col, width=width, anchor="w", stretch=False)
        
        # Configure tags for different statuses
        self.file_table.tag_configure("Good", foreground="green")
        self.file_table.tag_configure("Damaged", foreground="orange")
        self.file_table.tag_configure("Corrupted", foreground="red")
        
        # Add checkboxes to the first column
        self.file_table.heading("Selected", text="", anchor="center")
        self.file_table.column("Selected", width=30, anchor="center", stretch=False)
        
        # Bind events
        self.file_table.bind("<Button-1>", self.on_treeview_click)
        self.file_table.bind("<<TreeviewSelect>>", self.on_file_select)
        self.file_table.bind("<Double-1>", self.on_file_double_click)

    def on_treeview_click(self, event):
        """Handle checkbox clicks in the treeview"""
        region = self.file_table.identify("region", event.x, event.y)
        column = self.file_table.identify_column(event.x)
        
        if region == "cell" and column == "#1":  # Checkbox column
            item = self.file_table.identify_row(event.y)
            current_values = self.file_table.item(item, 'values')
            
            # Toggle the checkbox state
            new_state = "☑" if current_values[0] == "☐" else "☐"
            new_values = list(current_values)
            new_values[0] = new_state
            self.file_table.item(item, values=new_values)

    def build_preview_panel(self, parent):
        """Build the file preview panel"""
        colors = self.colors[self.settings["theme"]]
        
        preview_frame = ttk.LabelFrame(parent, text="File Preview", padding=10)
        parent.add(preview_frame)
        
        # Canvas for image previews
        self.preview_canvas = tk.Canvas(
            preview_frame, 
            bg=colors["secondary"],
            height=200,
            highlightthickness=0
        )
        self.preview_canvas.pack(fill="both", expand=True)
        
        # Text widget for text/hex previews
        self.preview_text = scrolledtext.ScrolledText(
            preview_frame,
            wrap=tk.WORD,
            bg=colors["secondary"],
            fg=colors["fg"],
            font=('Consolas', 9),
            height=10,
            padx=5,
            pady=5
        )
        
        # Label for when no preview is available
        self.preview_label = ttk.Label(
            preview_frame,
            text="No preview available",
            font=('Segoe UI', 10),
            anchor="center",
            background=colors["secondary"]
        )
        self.preview_label.pack(fill="both", expand=True)

    def build_details_panel(self, parent):
        """Build the file details panel"""
        colors = self.colors[self.settings["theme"]]
        
        details_frame = ttk.LabelFrame(parent, text="File Details", padding=10)
        parent.add(details_frame)
        
        # Text widget for detailed file information
        self.details_text = scrolledtext.ScrolledText(
            details_frame,
            wrap=tk.WORD,
            bg=colors["secondary"],
            fg=colors["fg"],
            font=('Consolas', 9),
            height=10,
            padx=5,
            pady=5
        )
        self.details_text.pack(fill="both", expand=True)
        
        # Insert initial message
        self.details_text.insert(
            tk.END,
            "Select a file to view detailed information"
        )
        self.details_text.config(state="disabled")

    def build_sidebar(self):
        """Build the sidebar with options and actions"""
        colors = self.colors[self.settings["theme"]]
        
        sidebar = ttk.Frame(self.root)
        sidebar.pack(fill="x", padx=10, pady=(0, 5))
        
        # Recovery options
        recovery_frame = ttk.LabelFrame(sidebar, text="Recovery Options", padding=10)
        recovery_frame.pack(fill="x", pady=(0, 10))
        
        # Recovery mode selection
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
            state="readonly",
            width=25
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
                "[Executables]"
            ],
            state="readonly",
            width=25
        )
        file_types.grid(row=1, column=1, sticky="ew", pady=5)
        
        # Action buttons
        action_frame = ttk.Frame(sidebar)
        action_frame.pack(fill="x", pady=(10, 0))
        
        ttk.Button(
            action_frame, 
            text="Recover Selected", 
            command=self.recover_selected_files,
            style='Accent.TButton'
        ).pack(side="left", fill="x", expand=True, padx=2)
        
        ttk.Button(
            action_frame, 
            text="Save List", 
            command=self.save_file_list
        ).pack(side="left", fill="x", expand=True, padx=2)
        
        ttk.Button(
            action_frame, 
            text="Clear Results", 
            command=self.clear_results
        ).pack(side="left", fill="x", expand=True, padx=2)
        
        # Progress bar
        self.progress_frame = ttk.Frame(sidebar)
        self.progress_frame.pack(fill="x", pady=(10, 0))
        
        self.progress_bar = ttk.Progressbar(
            self.progress_frame,
            variable=self.scan_progress,
            maximum=100,
            style='Horizontal.TProgressbar'
        )
        self.progress_bar.pack(fill="x", expand=True)
        
        self.progress_label = ttk.Label(
            self.progress_frame,
            textvariable=self.scan_status,
            font=('Segoe UI', 9),
            anchor="w"
        )
        self.progress_label.pack(fill="x")

    def build_status_bar(self):
        """Build the status bar at the bottom of the window"""
        colors = self.colors[self.settings["theme"]]
        
        status_bar = ttk.Frame(self.root, height=25)
        status_bar.pack(fill="x", padx=10, pady=(0, 10))
        
        # Status label
        self.status_label = ttk.Label(
            status_bar,
            textvariable=self.status_text,
            relief="sunken",
            anchor="w",
            font=('Segoe UI', 9),
            background=colors["secondary"]
        )
        self.status_label.pack(side="left", fill="x", expand=True, padx=2)
        
        # Statistics label
        self.stats_label = ttk.Label(
            status_bar,
            textvariable=self.stats_text,
            relief="sunken",
            anchor="e",
            font=('Segoe UI', 9),
            background=colors["secondary"]
        )
        self.stats_label.pack(side="right", fill="x", padx=2)
        
        # Developer credit
        dev_label = ttk.Label(
            status_bar,
            text=f"Developed by {self.settings['developer']}",
            font=('Segoe UI', 8),
            foreground="#666666"
        )
        dev_label.pack(side="right", padx=10)

    def populate_drives(self):
        """Populate the drive selection combobox with available drives"""
        try:
            drives = []
            self.drive_map = {}
            
            for part in psutil.disk_partitions():
                try:
                    if 'cdrom' in part.opts or part.fstype == '':
                        continue
                        
                    try:
                        usage = psutil.disk_usage(part.mountpoint)
                        free_gb = usage.free / (1024**3)
                        drive_info = f"{part.device} ({free_gb:.1f}GB free)"
                    except:
                        drive_info = f"{part.device} (Unknown free space)"
                    
                    drives.append(drive_info)
                    self.drive_map[drive_info] = part.mountpoint
                    
                except Exception as e:
                    self.logger.error(f"Error processing drive {part.device}: {str(e)}")
                    continue
            
            self.drive_combobox['values'] = drives
            
            if drives:
                self.drive_combobox.current(0)
                self.selected_drive.set(drives[0])
            else:
                messagebox.showwarning("No Drives", "No usable drives found")
                
        except Exception as e:
            self.logger.error(f"Error in populate_drives: {str(e)}")
            messagebox.showerror("Error", f"Failed to list drives: {str(e)}")

    def start_scan(self):
        """Start the file scanning process"""
        drive_display = self.selected_drive.get()
        if not drive_display:
            messagebox.showerror("Error", "Please select a drive to scan")
            return
        
        try:
            drive_path = self.drive_map[drive_display]
        except KeyError:
            messagebox.showerror("Error", "Invalid drive selection")
            return
        
        if not os.path.exists(drive_path):
            messagebox.showerror("Error", f"Drive path {drive_path} does not exist")
            return
        
        if self.is_scanning:
            messagebox.showwarning("Warning", "Scan already in progress")
            return
        
        # Reset UI for new scan
        self.reset_scan_ui()
        self.scan_status.set("Initializing scan...")
        self.status_text.set(f"Preparing to scan {drive_path}...")
        self.current_scan_path = drive_path
        self.root.update_idletasks()
        
        try:
            # Start scan in background thread
            self.scan_thread = threading.Thread(
                target=self.perform_scan,
                args=(drive_path,),
                daemon=True
            )
            self.is_scanning = True
            self.stop_scan = False
            self.scan_paused = False
            self.scan_thread.start()
            
            # Update button states
            self.scan_btn.config(state="disabled")
            self.stop_btn.config(state="normal")
            self.pause_btn.config(state="normal")
            
            # Start monitoring thread
            self.monitor_scan_thread()
            
        except Exception as e:
            self.logger.error(f"Failed to start scan: {str(e)}")
            messagebox.showerror("Error", f"Failed to start scan: {str(e)}")
            self.reset_scan_ui()

    def toggle_pause_scan(self):
        """Toggle pause/resume for the current scan"""
        if not self.is_scanning:
            return
            
        self.scan_paused = not self.scan_paused
        if self.scan_paused:
            self.pause_btn.config(text="Resume")
            self.scan_status.set("Scan paused")
            self.status_text.set("Scan paused - click Resume to continue")
        else:
            self.pause_btn.config(text="Pause")
            self.scan_status.set("Resuming scan...")
            self.status_text.set(f"Resuming scan of {self.current_scan_path}...")
        
        self.root.update_idletasks()

    def monitor_scan_thread(self):
        """Monitor the scan thread and update UI accordingly"""
        if self.is_scanning and self.scan_thread.is_alive():
            # Schedule the next check
            self.root.after(1000, self.monitor_scan_thread)
        else:
            # Scan completed or failed
            self.is_scanning = False
            self.scan_btn.config(state="normal")
            self.stop_btn.config(state="disabled")
            self.pause_btn.config(state="disabled")
            self.pause_btn.config(text="Pause")

    def perform_scan(self, drive_path):
        """Perform the actual file scanning"""
        try:
            self.logger.info(f"Starting scan of {drive_path}")
            self.scan_stats["start_time"] = datetime.now()
            self.scan_stats["total_files"] = 0
            self.scan_stats["recoverable"] = 0
            self.scan_stats["damaged"] = 0
            self.scan_stats["scanned_bytes"] = 0
            self.files = []
            
            file_types = self.get_file_types()
            file_count = 0
            last_ui_update = time.time()
            
            for root, dirs, files in os.walk(drive_path):
                if self.stop_scan:
                    self.logger.info("Scan stopped by user")
                    break
                    
                # Handle pause state
                while self.scan_paused and not self.stop_scan:
                    time.sleep(0.5)
                    continue
                    
                current_time = time.time()
                
                # Update UI periodically
                if current_time - last_ui_update > 2 or file_count % 500 == 0:
                    self.scan_status.set(f"Scanning: {root}")
                    self.status_text.set(f"Found {file_count} files...")
                    self.scan_progress.set(min(99, (file_count % 1000) / 10))
                    last_ui_update = current_time
                    self.root.update_idletasks()
                
                for filename in files:
                    if self.stop_scan:
                        break
                        
                    # Handle pause state
                    while self.scan_paused and not self.stop_scan:
                        time.sleep(0.5)
                        continue
                        
                    filepath = os.path.join(root, filename)
                    file_count += 1
                    
                    try:
                        file_stat = os.stat(filepath)
                        file_size = file_stat.st_size
                        modified = datetime.fromtimestamp(file_stat.st_mtime)
                        
                        if file_size > self.settings["max_file_size"]:
                            continue
                        
                        file_ext = os.path.splitext(filename)[1].lower()
                        if file_types and file_ext not in file_types:
                            continue
                        
                        status = self.check_file_integrity(filepath, file_ext)
                        
                        try:
                            file_type = magic.from_file(filepath, mime=True)
                        except:
                            file_type = "unknown"
                        
                        self.files.append({
                            "name": filename,
                            "path": filepath,
                            "size": file_size,
                            "status": status,
                            "type": file_type,
                            "modified": modified,
                            "folder": root
                        })
                        
                        self.scan_stats["total_files"] += 1
                        self.scan_stats["scanned_bytes"] += file_size
                        
                        if status == "Good":
                            self.scan_stats["recoverable"] += 1
                        else:
                            self.scan_stats["damaged"] += 1
                        
                    except Exception as e:
                        self.logger.error(f"Error scanning {filepath}: {str(e)}")
                        continue
            
            # Final update
            self.scan_stats["end_time"] = datetime.now()
            scan_duration = (self.scan_stats["end_time"] - self.scan_stats["start_time"]).total_seconds()
            
            self.scan_status.set("Scan completed")
            self.status_text.set(
                f"Scan completed. Found {file_count} files in {humanize.naturaldelta(scan_duration)}"
            )
            self.scan_progress.set(100)
            self.update_file_table()
            self.update_stats_display()
            
        except Exception as e:
            self.logger.error(f"Scan error: {str(e)}")
            self.scan_status.set("Scan failed")
            self.status_text.set(f"Scan failed: {str(e)}")
        finally:
            self.is_scanning = False
            self.stop_scan = False
            self.scan_btn.config(state="normal")
            self.stop_btn.config(state="disabled")
            self.pause_btn.config(state="disabled")

    def update_file_table(self):
        """Update the file table with the scanned files"""
        self.file_table.delete(*self.file_table.get_children())
        
        for idx, file_info in enumerate(self.files, 1):
            status = file_info["status"]
            size_mb = file_info["size"] / (1024 * 1024)
            
            self.file_table.insert(
                "",
                "end",
                iid=str(idx),
                values=(
                    "☐",  # Checkbox state
                    file_info["name"],
                    file_info["path"],
                    f"{size_mb:.2f} MB",
                    status,
                    file_info["type"],
                    file_info["modified"].strftime("%Y-%m-%d %H:%M")
                ),
                tags=(status,)
            )
        
        self.update_stats_display()

    def cancel_scan(self):
        """Cancel the current scan operation"""
        if self.is_scanning:
            self.stop_scan = True
            self.scan_status.set("Cancelling scan...")
            self.status_text.set("Waiting for scan to stop...")
            self.scan_btn.config(state="disabled")
            self.stop_btn.config(state="disabled")
            self.pause_btn.config(state="disabled")

    def recover_selected_files(self):
        """Recover files selected with checkboxes"""
        selected_files = []
        for item in self.file_table.get_children():
            values = self.file_table.item(item, 'values')
            if values and values[0] == "☑":  # Checked items
                selected_files.append(item)
        
        if not selected_files:
            messagebox.showwarning("Warning", "Please select files to recover (check the boxes)")
            return
        
        self.recover_files(selected_files)

    def recover_files(self, selected_items):
        """Recover selected files"""
        dest_folder = filedialog.askdirectory(
            title="Select Recovery Destination",
            initialdir=self.settings["recovery_folder"]
        )
        if not dest_folder:
            return
        
        if not os.access(dest_folder, os.W_OK):
            messagebox.showerror("Error", "No write permission in destination folder")
            return
        
        self.settings["recovery_folder"] = dest_folder
        
        recovery_thread = threading.Thread(
            target=self.perform_recovery,
            args=(selected_items, dest_folder),
            daemon=True
        )
        recovery_thread.start()

    def perform_recovery(self, selected_items, dest_folder):
        """Perform the actual file recovery"""
        total = len(selected_items)
        success = 0
        errors = 0
        
        self.scan_status.set("Recovering files...")
        self.status_text.set(f"Recovering {total} files...")
        self.scan_progress.set(0)
        self.root.update_idletasks()
        
        for i, item_id in enumerate(selected_items, 1):
            item = self.file_table.item(item_id)
            filepath = item['values'][2]  # Path is in third column
            filename = item['values'][1]
            status = item['values'][4]
            
            try:
                if status != "Good":
                    if not messagebox.askyesno(
                        "Warning",
                        f"File {filename} appears to be {status.lower()}. Attempt recovery anyway?"
                    ):
                        errors += 1
                        continue
                
                recovery_mode = self.recover_mode.get()
                
                if recovery_mode == "Standard Recovery":
                    dest_path = os.path.join(dest_folder, filename)
                    dest_path = self.get_unique_filename(dest_path)
                    shutil.copy2(filepath, dest_path)
                
                elif recovery_mode == "Recover with Folder Structure":
                    rel_path = os.path.relpath(filepath, self.current_scan_path)
                    dest_path = os.path.join(dest_folder, rel_path)
                    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                    dest_path = self.get_unique_filename(dest_path)
                    shutil.copy2(filepath, dest_path)
                
                success += 1
                self.logger.info(f"Recovered {filepath} to {dest_path}")
            
            except Exception as e:
                errors += 1
                self.logger.error(f"Failed to recover {filepath}: {str(e)}")
            
            # Update progress
            self.scan_progress.set((i / total) * 100)
            self.scan_status.set(f"Recovered {i} of {total} files")
            self.root.update_idletasks()
        
        # Show completion message
        self.scan_status.set("Recovery completed")
        self.status_text.set(
            f"Recovery completed: {success} succeeded, {errors} failed"
        )
        messagebox.showinfo(
            "Recovery Complete",
            f"Successfully recovered {success} files\n{errors} files could not be recovered"
        )

    def reset_scan_ui(self):
        """Reset the UI for a new scan"""
        self.file_table.delete(*self.file_table.get_children())
        self.files = []
        self.scan_stats = {
            "total_files": 0,
            "recoverable": 0,
            "damaged": 0,
            "scanned_bytes": 0,
            "start_time": None,
            "end_time": None
        }
        self.scan_progress.set(0)
        self.update_stats_display()
        self.scan_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.pause_btn.config(state="disabled")
        self.scan_status.set("Ready")
        self.status_text.set("Ready to scan")
        
        # Clear preview and details
        self.preview_canvas.delete("all")
        self.preview_text.pack_forget()
        self.preview_label.pack(fill="both", expand=True)
        self.preview_label.config(text="No preview available")
        
        self.details_text.config(state="normal")
        self.details_text.delete(1.0, tk.END)
        self.details_text.insert(tk.END, "Select a file to view detailed information")
        self.details_text.config(state="disabled")

    def reset_app(self):
        """Reset the application to initial state"""
        if messagebox.askyesno("Confirm", "Reset all scan results and settings?"):
            self.initialize_state()
            self.update_ui_state()
            self.reset_scan_ui()
            self.populate_drives()

    def clear_results(self):
        """Clear the current scan results"""
        if messagebox.askyesno("Confirm", "Clear all scan results?"):
            self.reset_scan_ui()

    def select_all_files(self):
        """Select all files in the file table"""
        for item in self.file_table.get_children():
            current_values = list(self.file_table.item(item, 'values'))
            current_values[0] = "☑"  # First column is checkbox
            self.file_table.item(item, values=current_values)

    def clear_selection(self):
        """Clear the current file selection"""
        for item in self.file_table.get_children():
            current_values = list(self.file_table.item(item, 'values'))
            current_values[0] = "☐"  # First column is checkbox
            self.file_table.item(item, values=current_values)

    def toggle_theme(self):
        """Toggle between light and dark theme"""
        self.settings["theme"] = self.theme_var.get()
        self.update_styles()
        self.update_ui_state()

    def toggle_preview(self):
        """Toggle file preview display"""
        self.settings["show_preview"] = self.show_preview_var.get()
        if not self.settings["show_preview"]:
            self.preview_canvas.pack_forget()
            self.preview_text.pack_forget()
            self.preview_label.pack_forget()

    def update_ui_state(self):
        """Update the UI state based on current settings"""
        theme = self.settings["theme"]
        colors = self.colors[theme]
        
        self.preview_canvas.config(bg=colors["secondary"])
        self.preview_text.config(
            bg=colors["secondary"],
            fg=colors["fg"]
        )
        self.details_text.config(
            bg=colors["secondary"],
            fg=colors["fg"]
        )
        
        self.preview_label.config(
            foreground=colors["fg"],
            background=colors["secondary"]
        )
        
        self.status_label.config(background=colors["secondary"])
        self.stats_label.config(background=colors["secondary"])
        
        self.logo_label.config(
            foreground=colors["accent"],
            background=colors["bg"]
        )

    def show_preferences(self):
        """Show the preferences dialog"""
        pref_dialog = tk.Toplevel(self.root)
        pref_dialog.title("Preferences")
        pref_dialog.geometry("500x400")
        
        # TODO: Implement preferences dialog

    def show_filter_dialog(self):
        """Show the advanced filter dialog"""
        filter_dialog = tk.Toplevel(self.root)
        filter_dialog.title("Advanced Filters")
        filter_dialog.geometry("500x400")
        
        # TODO: Implement advanced filter dialog

    def show_user_guide(self):
        """Open the user guide in a web browser"""
        webbrowser.open("https://example.com/datarecovery-guide")

    def show_about(self):
        """Show the about dialog"""
        about_dialog = tk.Toplevel(self.root)
        about_dialog.title("About DataRescue Pro X")
        about_dialog.geometry("500x400")
        
        try:
            about_dialog.iconbitmap("icon.ico")
        except:
            pass
        
        header_frame = ttk.Frame(about_dialog)
        header_frame.pack(fill="x", pady=20)
        
        ttk.Label(
            header_frame,
            text="DataRescue Pro X",
            font=('Segoe UI', 18, 'bold'),
            foreground=self.colors[self.settings["theme"]]["accent"]
        ).pack()
        
        ttk.Label(
            header_frame,
            text=f"Version {self.settings['version']}",
            font=('Segoe UI', 10)
        ).pack()
        
        content_frame = ttk.Frame(about_dialog)
        content_frame.pack(fill="x", padx=20, pady=10)
        
        ttk.Label(
            content_frame,
            text="Professional Data Recovery Solution",
            font=('Segoe UI', 11)
        ).pack(pady=5)
        
        ttk.Label(
            content_frame,
            text=f"\nDeveloped by {self.settings['developer']}",
            font=('Segoe UI', 9, 'italic')
        ).pack(pady=10)
        
        ttk.Button(
            about_dialog,
            text="OK",
            command=about_dialog.destroy,
            width=10
        ).pack(pady=20)

    def quit_app(self):
        """Quit the application"""
        if self.is_scanning:
            if messagebox.askyesno(
                "Confirm",
                "A scan is in progress. Are you sure you want to quit?"
            ):
                self.stop_scan = True
                self.root.after(100, self.root.destroy)
        else:
            self.root.destroy()

    def load_file_signatures(self):
        """Load known file signatures (magic numbers)"""
        self.file_signatures = {
            '.pdf': b'%PDF-',
            '.jpg': b'\xFF\xD8\xFF',
            '.jpeg': b'\xFF\xD8\xFF',
            '.png': b'\x89PNG',
            '.gif': b'GIF89a',
            '.zip': b'PK\x03\x04',
            '.exe': b'MZ',
            '.mp3': b'ID3',
            '.mp4': b'\x00\x00\x00\x18ftyp',
            '.doc': b'\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1',
            '.docx': b'PK\x03\x04',
            '.xlsx': b'PK\x03\x04',
            '.pptx': b'PK\x03\x04',
            '.rar': b'Rar!\x1A\x07\x00',
            '.7z': b'7z\xBC\xAF\x27\x1C',
            '.gz': b'\x1F\x8B\x08',
            '.tar': b'ustar',
            '.bmp': b'BM',
            '.tiff': b'II*\x00' if platform.system() == 'Windows' else b'MM\x00*',
            '.wav': b'RIFF',
            '.avi': b'RIFF',
            '.mdb': b'\x00\x01\x00\x00Standard Jet DB',
            '.sqlite': b'SQLite format 3'
        }

    def on_file_select(self, event):
        """Handle file selection event"""
        if not self.show_preview_var.get():
            return
            
        selected = self.file_table.selection()
        if not selected:
            return
            
        item = self.file_table.item(selected[0])
        filepath = item['values'][2]  # Path is third column now
        file_type = item['values'][5]  # Type is sixth column now
        
        self.update_preview(filepath, file_type)
        self.update_file_details(item)

    def update_preview(self, filepath, file_type):
        """Update the preview panel based on file type"""
        self.preview_canvas.delete("all")
        self.preview_text.pack_forget()
        self.preview_label.pack_forget()
        
        try:
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
                self.preview_canvas.pack(fill="both", expand=True)
            
            elif file_type.startswith('text/') or file_type in ['application/pdf', 'application/json']:
                try:
                    with open(filepath, 'r', errors='ignore') as f:
                        content = f.read(2000)
                    self.preview_text.delete(1.0, tk.END)
                    self.preview_text.insert(1.0, content)
                    self.preview_text.pack(fill="both", expand=True)
                except:
                    self.preview_label.config(text="Text preview not available")
                    self.preview_label.pack(fill="both", expand=True)
            
            else:
                try:
                    with open(filepath, 'rb') as f:
                        content = f.read(512)
                    hex_dump = ' '.join(f'{byte:02x}' for byte in content)
                    self.preview_text.delete(1.0, tk.END)
                    self.preview_text.insert(1.0, hex_dump)
                    self.preview_text.pack(fill="both", expand=True)
                except:
                    self.preview_label.config(text="Binary preview not available")
                    self.preview_label.pack(fill="both", expand=True)
        
        except Exception as e:
            self.preview_label.config(text=f"Preview error: {str(e)}")
            self.preview_label.pack(fill="both", expand=True)

    def update_file_details(self, item):
        """Update the file details panel"""
        self.details_text.config(state="normal")
        self.details_text.delete(1.0, tk.END)
        
        filepath = item['values'][2]  # Path is third column now
        file_size = float(item['values'][3].split()[0]) * 1024 * 1024
        
        details = [
            f"File Name: {item['values'][1]}",
            f"Path: {filepath}",
            f"Size: {humanize.naturalsize(file_size)}",
            f"Status: {item['values'][4]}",
            f"Type: {item['values'][5]}",
            f"Modified: {item['values'][6]}",
            "\nMetadata:",
            f"- MD5: {self.calculate_hash(filepath, 'md5')}",
            f"- SHA1: {self.calculate_hash(filepath, 'sha1')}",
            f"- File Attributes: {self.get_file_attributes(filepath)}",
            f"- Created: {self.get_file_creation_time(filepath)}"
        ]
        
        self.details_text.insert(1.0, '\n'.join(details))
        self.details_text.config(state="disabled")

    def calculate_hash(self, filepath, algorithm='md5'):
        """Calculate file hash using specified algorithm"""
        try:
            hash_func = getattr(hashlib, algorithm)()
            with open(filepath, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    hash_func.update(chunk)
            return hash_func.hexdigest()
        except:
            return "N/A"

    def get_file_attributes(self, filepath):
        """Get file attributes as a string"""
        try:
            attrs = []
            if os.access(filepath, os.R_OK): attrs.append("Readable")
            if os.access(filepath, os.W_OK): attrs.append("Writable")
            if os.access(filepath, os.X_OK): attrs.append("Executable")
            return ', '.join(attrs) if attrs else "No special attributes"
        except:
            return "Unknown"

    def get_file_creation_time(self, filepath):
        """Get file creation time"""
        try:
            if platform.system() == 'Windows':
                creation_time = os.path.getctime(filepath)
            else:
                stat = os.stat(filepath)
                creation_time = stat.st_birthtime
            return datetime.fromtimestamp(creation_time).strftime("%Y-%m-%d %H:%M")
        except:
            return "Unknown"

    def get_file_types(self):
        """Get the file extensions to scan based on selected category"""
        file_type_map = {
            "[All Files]": None,
            "[Pictures]": ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.svg'],
            "[Documents]": ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt', '.rtf', '.odt', '.ods'],
            "[Audio]": ['.mp3', '.wav', '.aac', '.flac', '.ogg', '.wma', '.m4a'],
            "[Video]": ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.m4v', '.webm'],
            "[Archives]": ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz'],
            "[Database]": ['.db', '.sqlite', '.mdb', '.accdb', '.sql', '.dbf'],
            "[Executables]": ['.exe', '.dll', '.msi', '.bat', '.sh', '.app', '.apk']
        }
        
        selected = self.selected_category.get()
        return file_type_map.get(selected, None)

    def check_file_integrity(self, filepath, file_ext):
        """Check the integrity of a file"""
        try:
            if not os.path.isfile(filepath):
                return "Corrupted"
            
            if file_ext in self.file_signatures:
                with open(filepath, 'rb') as f:
                    header = f.read(len(self.file_signatures[file_ext]))
                    if not header.startswith(self.file_signatures[file_ext]):
                        return "Damaged"
            
            if file_ext in ['.jpg', '.jpeg', '.png']:
                try:
                    with Image.open(filepath) as img:
                        img.verify()
                except:
                    return "Damaged"
            
            return "Good"
        except:
            return "Corrupted"

    def get_unique_filename(self, path):
        """Generate a unique filename if the destination exists"""
        if not os.path.exists(path):
            return path
            
        base, ext = os.path.splitext(path)
        counter = 1
        
        while True:
            new_path = f"{base}_{counter}{ext}"
            if not os.path.exists(new_path):
                return new_path
            counter += 1

    def save_file_list(self):
        """Save the current file list to a file"""
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("Text Files", "*.txt"), ("All Files", "*.*")],
            initialdir=self.settings["recovery_folder"]
        )
        
        if not filepath:
            return
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("Selected,File Name,Path,Size,Status,Type,Modified\n")
                
                for item in self.file_table.get_children():
                    values = self.file_table.item(item)['values']
                    f.write(','.join(f'"{v}"' for v in values) + '\n')
            
            messagebox.showinfo("Success", "File list saved successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file list: {str(e)}")

    def save_scan_results(self):
        """Save the current scan results to a file"""
        filepath = filedialog.asksaveasfilename(
            defaultextension=".dsr",
            filetypes=[("DataRescue Scan", "*.dsr"), ("All Files", "*.*")],
            initialdir=self.settings["recovery_folder"]
        )
        
        if not filepath:
            return
        
        try:
            with open(filepath, 'wb') as f:
                pickle.dump({
                    'files': self.files,
                    'scan_stats': self.scan_stats,
                    'drive': self.current_scan_path,
                    'timestamp': datetime.now(),
                    'settings': self.settings
                }, f)
            
            messagebox.showinfo("Success", "Scan results saved successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save scan results: {str(e)}")

    def load_scan_results(self):
        """Load scan results from a file"""
        filepath = filedialog.askopenfilename(
            filetypes=[("DataRescue Scan", "*.dsr"), ("All Files", "*.*")],
            initialdir=self.settings["recovery_folder"]
        )
        
        if not filepath:
            return
        
        try:
            with open(filepath, 'rb') as f:
                data = pickle.load(f)
            
            self.files = data['files']
            self.scan_stats = data['scan_stats']
            self.current_scan_path = data['drive']
            
            self.update_file_table()
            self.update_stats_display()
            
            for display, path in self.drive_map.items():
                if path == self.current_scan_path:
                    self.selected_drive.set(display)
                    break
            
            messagebox.showinfo("Success", "Scan results loaded successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load scan results: {str(e)}")

    def on_file_double_click(self, event):
        """Handle double-click on a file"""
        selected = self.file_table.selection()
        if not selected:
            return
            
        item = self.file_table.item(selected[0])
        filepath = item['values'][2]  # Path is third column now
        
        try:
            if platform.system() == 'Windows':
                os.startfile(filepath)
            elif platform.system() == 'Darwin':
                subprocess.run(['open', filepath])
            else:
                subprocess.run(['xdg-open', filepath])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open file: {str(e)}")

    def update_stats_display(self):
        """Update the statistics display"""
        self.stats_text.set(
            f"Files: {humanize.intcomma(self.scan_stats['total_files'])} | "
            f"Recoverable: {humanize.intcomma(self.scan_stats['recoverable'])} | "
            f"Damaged: {humanize.intcomma(self.scan_stats['damaged'])}"
        )

if __name__ == '__main__':
    root = tk.Tk()
    app = DataRescueProX(root)
    root.protocol("WM_DELETE_WINDOW", app.quit_app)
    root.mainloop()