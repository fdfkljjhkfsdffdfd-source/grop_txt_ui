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
        paned = tk.PanedWindow(self.tab_explorer, orient=tk.HORIZONTAL, bg="#0f172a", bd=0)
        paned.pack(fill="both", expand=True)

        # Left: Tree
        left_frame = tk.Frame(paned, bg="#1e293b")
        paned.add(left_frame, width=400)

        ctrl_bar = tk.Frame(left_frame, bg="#334155", pady=5)
        ctrl_bar.pack(fill="x")
        
        self.prof_var = tk.StringVar()
        self.prof_cb = ttk.Combobox(ctrl_bar, textvariable=self.prof_var, state="readonly", width=15)
        self.prof_cb.pack(side="left", padx=5)
        
        tk.Button(ctrl_bar, text="📁 Open", command=self.controller.open_project, bg="#10b981", fg="white", bd=0).pack(side="right", padx=5)

        self.tree = ttk.Treeview(left_frame, selectmode="none")
        self.tree.pack(fill="both", expand=True)
        self.tree.heading("#0", text=" Project Structure", anchor="w")
        
        # Tags
        self.tree.tag_configure("checked", background="#064e3b", foreground="#10b981", font=("Segoe UI", 10, "bold"))
        self.tree.tag_configure("folder", foreground="#eab308")

        # Right: Config & Log
        right_frame = tk.Frame(paned, bg="#0f172a", padx=10)
        paned.add(right_frame)

        # Config Area
        cfg_box = tk.LabelFrame(right_frame, text=" Settings ", bg="#0f172a", fg="#38bdf8", padx=10, pady=10)
        cfg_box.pack(fill="x", pady=5)

        tk.Label(cfg_box, text="Extensions:", bg="#0f172a", fg="#94a3b8").pack(anchor="w")
        self.ext_entry = tk.Entry(cfg_box, bg="#1e293b", fg="white", bd=0)
        self.ext_entry.pack(fill="x", pady=2)
        self.ext_entry.insert(0, ".py, .js, .tsx, .html, .css")

        tk.Label(cfg_box, text="Ignore:", bg="#0f172a", fg="#94a3b8").pack(anchor="w", pady=(5,0))
        self.ignore_entry = tk.Entry(cfg_box, bg="#1e293b", fg="#f43f5e", bd=0)
        self.ignore_entry.pack(fill="x", pady=2)

        tk.Button(right_frame, text="⚡ SYNC & MERGE", command=self.controller.run_merge, bg="#10b981", fg="white", font=("Arial", 12, "bold"), bd=0, pady=10).pack(fill="x", pady=10)

        self.log_area = scrolledtext.ScrolledText(right_frame, bg="#000", fg="#10b981", font=("Consolas", 9), height=15)
        self.log_area.pack(fill="both", expand=True, pady=5)

    def _build_map_tab(self):
        container = tk.Frame(self.tab_map, bg="#1e293b", padx=15, pady=15)
        container.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.map_search = tk.Entry(container, bg="#0f172a", fg="white", bd=0, font=("Consolas", 11))
        self.map_search.pack(fill="x", pady=(0, 10))
        self.map_search.bind("<KeyRelease>", lambda e: self.controller.filter_map())

        self.map_display = scrolledtext.ScrolledText(container, bg="#0f172a", fg="#cbd5e1", font=("Consolas", 10), bd=0)
        self.map_display.pack(fill="both", expand=True)

    def _build_update_tab(self):
        container = tk.Frame(self.tab_update, bg="#1e293b", padx=15, pady=15)
        container.pack(fill="both", expand=True, padx=10, pady=10)
        
        tk.Button(container, text="📂 Select Source Files", command=self.controller.select_sources, bg="#38bdf8", fg="#0f172a", bd=0, padx=10, pady=5).pack(anchor="w")
        
        self.update_tree = ttk.Treeview(container, columns=("Source", "Target", "Status"), show="headings")
        self.update_tree.pack(fill="both", expand=True, pady=10)
        self.update_tree.heading("Source", text="Source File")
        self.update_tree.heading("Target", text="Project Path")
        self.update_tree.heading("Status", text="Status")

        tk.Button(container, text="⚡ APPLY OVERWRITE", command=self.controller.run_overwrite, bg="#ef4444", fg="white", font=("Arial", 10, "bold"), bd=0, pady=10).pack(fill="x")

    def _build_history_tab(self):
        container = tk.Frame(self.tab_history, bg="#1e293b", padx=15, pady=15)
        container.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.hist_tree = ttk.Treeview(container, columns=("Time", "Profile", "File"), show="headings")
        self.hist_tree.pack(fill="both", expand=True)
        self.hist_tree.heading("Time", text="Time")
        self.hist_tree.heading("Profile", text="Profile")
        self.hist_tree.heading("File", text="Filename")

    def log(self, msg):
        self.log_area.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n")
        self.log_area.see(tk.END)
