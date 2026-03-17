import tkinter as tk
from tkinter import scrolledtext, ttk
from datetime import datetime

class GropTxtUI:
    """ส่วนจัดการหน้าจอ (View)"""
    def __init__(self, root, controller):
        self.root = root
        self.controller = controller
        self.root.title("GROP_TXT Pro Studio v2.6.1")
        self.root.geometry("1300x900")
        self.root.configure(bg="#0f172a")
        
        self._setup_styles()
        self._build_ui()

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Treeview", background="#1e293b", foreground="#cbd5e1", fieldbackground="#1e293b", font=("Segoe UI", 10))
        style.configure("TNotebook", background="#0f172a", borderwidth=0)
        style.configure("TNotebook.Tab", padding=[20, 8], background="#1e293b", foreground="#94a3b8")
        style.map("TNotebook.Tab", background=[('selected', '#38bdf8')], foreground=[('selected', '#0f172a')])

    def _build_ui(self):
        # Header
        header = tk.Frame(self.root, bg="#0f172a", height=60)
        header.pack(fill="x")
        tk.Label(header, text="GROP_TXT PRO STUDIO", bg="#0f172a", fg="#38bdf8", font=("Segoe UI", 20, "bold")).pack(side="left", padx=20, pady=10)

        # Tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=15, pady=10)

        # Tab 1: Explorer
        self.tab_explorer = tk.Frame(self.notebook, bg="#0f172a")
        self.notebook.add(self.tab_explorer, text=" 📂 Explorer ")
        self._build_explorer_tab()

        # Tab 2: Project Map
        self.tab_map = tk.Frame(self.notebook, bg="#0f172a")
        self.notebook.add(self.tab_map, text=" 🗺️ Project Map ")
        self._build_map_tab()

        # Tab 3: Smart Update
        self.tab_update = tk.Frame(self.notebook, bg="#0f172a")
        self.notebook.add(self.tab_update, text=" 🛠️ Smart Update ")
        self._build_update_tab()

        # Tab 4: History
        self.tab_history = tk.Frame(self.notebook, bg="#0f172a")
        self.notebook.add(self.tab_history, text=" 🕒 History ")
        self._build_history_tab()

    def _build_explorer_tab(self):
        paned = tk.PanedWindow(self.tab_explorer, orient=tk.HORIZONTAL, bg="#0f172a", bd=0, sashwidth=4)
        paned.pack(fill="both", expand=True)

        # Left: Tree
        left_frame = tk.Frame(paned, bg="#1e293b")
        paned.add(left_frame, width=450)

        ctrl_bar = tk.Frame(left_frame, bg="#334155", pady=5)
        ctrl_bar.pack(fill="x")
        
        self.prof_var = tk.StringVar()
        self.prof_cb = ttk.Combobox(ctrl_bar, textvariable=self.prof_var, state="readonly", width=15)
        self.prof_cb.pack(side="left", padx=10)
        
        tk.Button(ctrl_bar, text="💾 Save", command=self.controller.save_new_profile, bg="#38bdf8", fg="#0f172a", font=("Arial", 8, "bold"), bd=0, padx=8).pack(side="left", padx=2)
        tk.Button(ctrl_bar, text="🗑️ Del", command=self.controller.delete_profile, bg="#ef4444", fg="white", font=("Arial", 8, "bold"), bd=0, padx=8).pack(side="left", padx=2)
        tk.Button(ctrl_bar, text="📁 Open", command=self.controller.open_project, bg="#10b981", fg="white", font=("Arial", 8, "bold"), bd=0, padx=8).pack(side="right", padx=10)

        self.tree = ttk.Treeview(left_frame, selectmode="none")
        self.tree.pack(fill="both", expand=True)
        self.tree.heading("#0", text=" Project Files (✓ = Selected)", anchor="w")
        
        # Tags
        self.tree.tag_configure("checked", background="#064e3b", foreground="#10b981", font=("Segoe UI", 10, "bold"))
        self.tree.tag_configure("folder", foreground="#eab308")
        self.tree.tag_configure("partial", foreground="#38bdf8")
        self.tree.tag_configure("dimmed", foreground="#475569")
        self.tree.tag_configure("ignored", foreground="#475569", font=("Segoe UI", 9, "italic"))

        # Right: Config & Log
        right_frame = tk.Frame(paned, bg="#0f172a", padx=10)
        paned.add(right_frame)

        # Batch Selection
        batch_frame = tk.LabelFrame(right_frame, text=" Batch Selection & Config ", bg="#0f172a", fg="#38bdf8", font=("Arial", 10, "bold"), padx=15, pady=10)
        batch_frame.pack(fill="x", pady=5)

        tk.Label(batch_frame, text="Paste File Paths (one per line):", bg="#0f172a", fg="#38bdf8", font=("Arial", 9, "bold")).pack(anchor="w")
        self.batch_text = scrolledtext.ScrolledText(batch_frame, height=5, bg="#1e293b", fg="#10b981", font=("Consolas", 10), bd=0)
        self.batch_text.pack(fill="x", pady=5)
        
        batch_btn_frame = tk.Frame(batch_frame, bg="#0f172a")
        batch_btn_frame.pack(fill="x")
        tk.Button(batch_btn_frame, text="✨ Apply Batch", command=self.controller.apply_batch, bg="#38bdf8", fg="#0f172a", font=("Arial", 9, "bold"), bd=0, padx=10).pack(side="left")
        tk.Button(batch_btn_frame, text="🧹 Clear", command=lambda: self.batch_text.delete('1.0', tk.END), bg="#334155", fg="white", font=("Arial", 9), bd=0, padx=10).pack(side="left", padx=10)

        # Config Area
        cfg_grid = tk.Frame(batch_frame, bg="#0f172a")
        cfg_grid.pack(fill="x", pady=10)

        tk.Label(cfg_grid, text="Extensions:", bg="#0f172a", fg="#94a3b8").grid(row=0, column=0, sticky="w")
        self.ext_entry = tk.Entry(cfg_grid, bg="#1e293b", fg="white", bd=0, font=("Consolas", 10))
        self.ext_entry.grid(row=0, column=1, sticky="ew", padx=(10, 0))
        self.ext_entry.insert(0, ".py, .js, .tsx, .html, .css, .md, .txt")

        tk.Label(cfg_grid, text="Ignore List:", bg="#0f172a", fg="#94a3b8").grid(row=1, column=0, sticky="w", pady=(5,0))
        self.ignore_entry = tk.Entry(cfg_grid, bg="#1e293b", fg="#f43f5e", bd=0, font=("Consolas", 10))
        self.ignore_entry.grid(row=1, column=1, sticky="ew", padx=(10, 0), pady=(5,0))
        cfg_grid.columnconfigure(1, weight=1)

        # Selection Preview
        preview_frame = tk.LabelFrame(right_frame, text=" Current Selection Preview ", bg="#0f172a", fg="#10b981", font=("Arial", 10, "bold"), padx=15, pady=10)
        preview_frame.pack(fill="x", pady=5)
        
        tk.Button(preview_frame, text="✅ Select All", command=self.controller.select_all, bg="#10b981", fg="white", font=("Arial", 8, "bold"), bd=0, padx=8).pack(side="left", padx=2)
        tk.Button(preview_frame, text="❌ Deselect All", command=self.controller.deselect_all, bg="#ef4444", fg="white", font=("Arial", 8, "bold"), bd=0, padx=8).pack(side="left", padx=2)
        tk.Button(preview_frame, text="🗑️ Clear All", command=self.controller.clear_selection, bg="#64748b", fg="white", font=("Arial", 8, "bold"), bd=0, padx=8).pack(side="right")
        
        self.selection_display = scrolledtext.ScrolledText(preview_frame, height=6, bg="#020617", fg="#38bdf8", font=("Consolas", 9), bd=0)
        self.selection_display.pack(fill="x", pady=5)
        self.selection_display.config(state="disabled")

        tk.Button(right_frame, text="⚡ SYNC & MERGE (ULTRA STREAM)", command=self.controller.run_merge, bg="#10b981", fg="white", font=("Arial", 12, "bold"), bd=0, pady=12).pack(fill="x", pady=10)

        self.log_area = scrolledtext.ScrolledText(right_frame, bg="#000", fg="#10b981", font=("Consolas", 9), height=10)
        self.log_area.pack(fill="both", expand=True, pady=5)

    def _build_map_tab(self):
        container = tk.Frame(self.tab_map, bg="#1e293b", padx=20, pady=20)
        container.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctrl = tk.Frame(container, bg="#1e293b")
        ctrl.pack(fill="x", pady=(0, 15))
        
        tk.Label(ctrl, text="🔍 Filter Paths:", bg="#1e293b", fg="#38bdf8", font=("Arial", 10, "bold")).pack(side="left")
        self.map_search = tk.Entry(ctrl, bg="#0f172a", fg="white", bd=0, font=("Consolas", 11), width=40)
        self.map_search.pack(side="left", padx=15)
        self.map_search.bind("<KeyRelease>", lambda e: self.controller.filter_map())
        
        tk.Button(ctrl, text="📋 Copy All", command=self.controller.copy_map_paths, bg="#10b981", fg="white", font=("Arial", 9, "bold"), bd=0, padx=15).pack(side="right")

        self.map_display = scrolledtext.ScrolledText(container, bg="#0f172a", fg="#cbd5e1", font=("Consolas", 10), bd=0, padx=10, pady=10)
        self.map_display.pack(fill="both", expand=True)

    def _build_update_tab(self):
        container = tk.Frame(self.tab_update, bg="#1e293b", padx=20, pady=20)
        container.pack(fill="both", expand=True, padx=20, pady=20)
        
        header = tk.Frame(container, bg="#1e293b")
        header.pack(fill="x", pady=(0, 15))
        
        tk.Button(header, text="📂 Select Source Files", command=self.controller.select_sources, bg="#38bdf8", fg="#0f172a", font=("Arial", 9, "bold"), bd=0, padx=15, pady=5).pack(side="left")
        tk.Button(header, text="🔄 Refresh", command=self.controller.refresh_update_matches, bg="#334155", fg="white", font=("Arial", 9), bd=0, padx=15, pady=5).pack(side="right")
        
        self.update_tree = ttk.Treeview(container, columns=("Source", "Target", "Status"), show="headings", height=15)
        self.update_tree.pack(fill="both", expand=True, pady=10)
        self.update_tree.heading("Source", text="Source File")
        self.update_tree.heading("Target", text="Project Path")
        self.update_tree.heading("Status", text="Status")
        
        self.update_tree.tag_configure("ready", foreground="#10b981")
        self.update_tree.tag_configure("missing", foreground="#ef4444")
        self.update_tree.tag_configure("warning", foreground="#eab308")

        tk.Button(container, text="⚡ EXECUTE SMART OVERWRITE", command=self.controller.run_overwrite, bg="#ef4444", fg="white", font=("Arial", 11, "bold"), bd=0, pady=12).pack(fill="x")

    def _build_history_tab(self):
        container = tk.Frame(self.tab_history, bg="#1e293b", padx=20, pady=20)
        container.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.hist_tree = ttk.Treeview(container, columns=("Time", "Profile", "File"), show="headings", height=15)
        self.hist_tree.pack(fill="both", expand=True)
        self.hist_tree.heading("Time", text="Time")
        self.hist_tree.heading("Profile", text="Profile")
        self.hist_tree.heading("File", text="Filename")
        
        btn_frame = tk.Frame(container, bg="#1e293b", pady=15)
        btn_frame.pack(fill="x")
        tk.Button(btn_frame, text="📂 Open File", command=self.controller.open_history_file, bg="#38bdf8", fg="#0f172a", font=("Arial", 10, "bold"), bd=0, padx=20, pady=8).pack(side="left", padx=5)
        tk.Button(btn_frame, text="🔍 Show Folder", command=self.controller.open_history_folder, bg="#64748b", fg="white", font=("Arial", 10, "bold"), bd=0, padx=20, pady=8).pack(side="left", padx=5)
        tk.Button(btn_frame, text="🗑️ Clear History", command=self.controller.clear_history, bg="#ef4444", fg="white", font=("Arial", 10, "bold"), bd=0, padx=20, pady=8).pack(side="right", padx=5)

    def log(self, msg):
        self.log_area.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n")
        self.log_area.see(tk.END)
