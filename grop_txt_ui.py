import tkinter as tk
from tkinter import scrolledtext, ttk
from datetime import datetime
import os

class ToolTip:
    """คลาสสำหรับแสดงคำแนะนำเมื่อเอาเมาส์ไปชี้ (Tooltip)"""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        self.widget.bind("<Enter>", self.show_tip)
        self.widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event=None):
        if self.tip_window or not self.text:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(1)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                      background="#334155", foreground="#f8fafc", relief=tk.SOLID, borderwidth=1,
                      font=("Segoe UI", 9), padx=8, pady=4)
        label.pack()

    def hide_tip(self, event=None):
        tw = self.tip_window
        self.tip_window = None
        if tw:
            tw.destroy()

class GropTxtUI:
    """ส่วนจัดการหน้าจอ (View) - PRO STUDIO DESIGN"""
    def __init__(self, root, controller):
        self.root = root
        self.controller = controller
        self.root.title("GROP_TXT PRO STUDIO")
        self.root.geometry("1400x950")
        self.root.configure(bg="#0f172a")
        
        # Colors
        self.CLR_BG = "#0f172a"
        self.CLR_SIDEBAR = "#1e293b"
        self.CLR_ACCENT = "#10b981"
        self.CLR_BORDER = "#334155"
        self.CLR_TEXT = "#f8fafc"
        self.CLR_MUTED = "#94a3b8"
        
        self._setup_styles()
        self._build_ui()

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        # Treeview
        style.configure("Treeview", 
                        background=self.CLR_SIDEBAR, 
                        foreground="#cbd5e1", 
                        fieldbackground=self.CLR_SIDEBAR, 
                        font=("Segoe UI", 10), 
                        borderwidth=0,
                        rowheight=32)
        style.map("Treeview", 
                  background=[('selected', "#334155")], 
                  foreground=[('selected', self.CLR_ACCENT)])
        style.configure("Treeview.Heading", 
                        background="#334155", 
                        foreground=self.CLR_MUTED, 
                        font=("Segoe UI", 9, "bold"),
                        borderwidth=0)

        # Notebook
        style.configure("TNotebook", background=self.CLR_BG, borderwidth=0)
        style.configure("TNotebook.Tab", 
                        padding=[24, 10], 
                        background=self.CLR_SIDEBAR, 
                        foreground=self.CLR_MUTED, 
                        font=("Segoe UI", 10, "bold"),
                        borderwidth=0)
        style.map("TNotebook.Tab", 
                  background=[('selected', self.CLR_BG)], 
                  foreground=[('selected', self.CLR_ACCENT)])

        # Progressbar
        style.configure("TProgressbar", 
                        thickness=10, 
                        background=self.CLR_ACCENT, 
                        troughcolor=self.CLR_BORDER, 
                        borderwidth=0)
        
        # Scrollbar
        style.configure("Vertical.TScrollbar", background=self.CLR_BORDER, troughcolor=self.CLR_SIDEBAR, borderwidth=0, arrowsize=12)

    def _build_ui(self):
        # 1. Header
        self.header = tk.Frame(self.root, bg=self.CLR_SIDEBAR, height=64, bd=0, highlightthickness=1, highlightbackground=self.CLR_BORDER)
        self.header.pack(side="top", fill="x")
        self.header.pack_propagate(False)
        
        logo_frame = tk.Frame(self.header, bg=self.CLR_SIDEBAR)
        logo_frame.pack(side="left", padx=24)
        
        tk.Label(logo_frame, text="GROP_TXT", bg=self.CLR_SIDEBAR, fg=self.CLR_TEXT, font=("Segoe UI", 16, "bold")).pack(side="left")
        tk.Label(logo_frame, text="PRO STUDIO", bg=self.CLR_SIDEBAR, fg=self.CLR_ACCENT, font=("Segoe UI", 16, "bold")).pack(side="left", padx=(5, 0))
        
        header_right = tk.Frame(self.header, bg=self.CLR_SIDEBAR)
        header_right.pack(side="right", padx=24)
        
        self.sys_status = tk.Label(header_right, text="● System Online", bg=self.CLR_SIDEBAR, fg=self.CLR_ACCENT, font=("Segoe UI", 9))
        self.sys_status.pack(side="left", padx=20)
        
        # 2. Footer
        self.footer = tk.Frame(self.root, bg=self.CLR_SIDEBAR, height=32, bd=0, highlightthickness=1, highlightbackground=self.CLR_BORDER)
        self.footer.pack(side="bottom", fill="x")
        self.footer.pack_propagate(False)
        self._build_footer()

        # 3. Body (Sidebar + Main)
        self.body = tk.Frame(self.root, bg=self.CLR_BG)
        self.body.pack(fill="both", expand=True)
        
        # Sidebar
        self.sidebar = tk.Frame(self.body, bg=self.CLR_SIDEBAR, width=300, bd=0, highlightthickness=1, highlightbackground=self.CLR_BORDER)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        self._build_sidebar()
        
        # Main Content
        self.main_content = tk.Frame(self.body, bg=self.CLR_BG)
        self.main_content.pack(side="left", fill="both", expand=True)
        
        self.notebook = ttk.Notebook(self.main_content)
        self.notebook.pack(fill="both", expand=True)
        
        # Tab 1: Explorer
        self.tab_explorer = tk.Frame(self.notebook, bg=self.CLR_BG)
        self.notebook.add(self.tab_explorer, text=" Explorer ")
        self._build_explorer_tab()
        
        # Tab 2: Project Map
        self.tab_map = tk.Frame(self.notebook, bg=self.CLR_BG)
        self.notebook.add(self.tab_map, text=" Project Map ")
        self._build_map_tab()
        
        # Tab 3: Smart Update
        self.tab_update = tk.Frame(self.notebook, bg=self.CLR_BG)
        self.notebook.add(self.tab_update, text=" Smart Update ")
        self._build_update_tab()
        
        # Tab 4: History
        self.tab_history = tk.Frame(self.notebook, bg=self.CLR_BG)
        self.notebook.add(self.tab_history, text=" History ")
        self._build_history_tab()

    def _build_sidebar(self):
        # Project Selector Section
        proj_sec = tk.Frame(self.sidebar, bg=self.CLR_SIDEBAR, padx=20, pady=20)
        proj_sec.pack(fill="x")
        
        tk.Label(proj_sec, text="PROJECT ENVIRONMENT", bg=self.CLR_SIDEBAR, fg=self.CLR_MUTED, font=("Segoe UI", 8, "bold")).pack(anchor="w", pady=(0, 8))
        
        self.prof_var = tk.StringVar()
        self.prof_cb = ttk.Combobox(proj_sec, textvariable=self.prof_var, state="readonly")
        self.prof_cb.pack(fill="x", pady=(0, 12))
        
        btn_frame = tk.Frame(proj_sec, bg=self.CLR_SIDEBAR)
        btn_frame.pack(fill="x")
        
        self.btn_save = tk.Button(btn_frame, text="SAVE", command=self.controller.save_new_profile, bg=self.CLR_ACCENT, fg=self.CLR_BG, font=("Segoe UI", 9, "bold"), bd=0, pady=8)
        self.btn_save.pack(side="left", fill="x", expand=True, padx=(0, 4))
        self._add_hover(self.btn_save, "#34d399", self.CLR_ACCENT)
        
        self.btn_del = tk.Button(btn_frame, text="DELETE", command=self.controller.delete_profile, bg="#ef4444", fg=self.CLR_TEXT, font=("Segoe UI", 9, "bold"), bd=0, pady=8)
        self.btn_del.pack(side="left", fill="x", expand=True, padx=(4, 0))
        self._add_hover(self.btn_del, "#f87171", "#ef4444")
        
        # Search & Tree Section
        tree_sec = tk.Frame(self.sidebar, bg=self.CLR_SIDEBAR, padx=10)
        tree_sec.pack(fill="both", expand=True)
        
        # Search
        search_frame = tk.Frame(tree_sec, bg=self.CLR_BG, padx=10, pady=6)
        search_frame.pack(fill="x", pady=(0, 10))
        tk.Label(search_frame, text="🔍", bg=self.CLR_BG, fg=self.CLR_MUTED).pack(side="left")
        self.tree_search = tk.Entry(search_frame, bg=self.CLR_BG, fg=self.CLR_TEXT, bd=0, font=("Segoe UI", 10), insertbackground="white")
        self.tree_search.pack(side="left", fill="x", expand=True, padx=6)
        self.tree_search.bind("<KeyRelease>", lambda e: self.controller.filter_tree())
        
        # Tree
        self.tree = ttk.Treeview(tree_sec, selectmode="none", show="tree")
        self.tree.pack(fill="both", expand=True)
        
        # Tags for tree
        self.tree.tag_configure("checked", foreground=self.CLR_ACCENT, font=("Segoe UI", 10, "bold"))
        self.tree.tag_configure("folder", foreground="#eab308")
        self.tree.tag_configure("ignored", foreground="#475569", font=("Segoe UI", 9, "italic"))
        self.tree.tag_configure("dimmed", foreground="#334155")

        # Open Folder Button at bottom of sidebar
        self.btn_open = tk.Button(self.sidebar, text="📁 OPEN PROJECT FOLDER", command=self.controller.open_project, bg=self.CLR_BORDER, fg=self.CLR_TEXT, font=("Segoe UI", 9, "bold"), bd=0, pady=12)
        self.btn_open.pack(side="bottom", fill="x", padx=20, pady=20)
        self._add_hover(self.btn_open, "#475569", self.CLR_BORDER)

        self.btn_recent = tk.Button(self.sidebar, text="🕒 RECENT PROJECTS", command=self.controller.show_recent_menu, bg=self.CLR_SIDEBAR, fg=self.CLR_MUTED, font=("Segoe UI", 8), bd=0, pady=5)
        self.btn_recent.pack(side="bottom", fill="x", padx=20)
        self._add_hover(self.btn_recent, self.CLR_BG, self.CLR_SIDEBAR)

    def _build_explorer_tab(self):
        container = tk.Frame(self.tab_explorer, bg=self.CLR_BG, padx=30, pady=30)
        container.pack(fill="both", expand=True)
        
        # 1. Batch Selection & Config
        batch_sec = tk.LabelFrame(container, text=" BATCH SELECTION & CONFIG ", bg=self.CLR_BG, fg=self.CLR_MUTED, font=("Segoe UI", 9, "bold"), padx=20, pady=20, bd=1, relief="solid", highlightthickness=1, highlightbackground=self.CLR_BORDER)
        batch_sec.pack(fill="x", pady=(0, 25))
        
        header_row = tk.Frame(batch_sec, bg=self.CLR_BG)
        header_row.pack(fill="x", pady=(0, 15))
        
        tk.Label(header_row, text="PASTE FILE PATHS (ONE PER LINE):", bg=self.CLR_BG, fg=self.CLR_MUTED, font=("Segoe UI", 8, "bold")).pack(side="left")
        
        btn_row = tk.Frame(header_row, bg=self.CLR_BG)
        btn_row.pack(side="right")
        
        self.btn_apply = tk.Button(btn_row, text="APPLY BATCH", command=self.controller.apply_batch, bg=self.CLR_ACCENT, fg=self.CLR_BG, font=("Segoe UI", 8, "bold"), bd=0, padx=15, pady=6)
        self.btn_apply.pack(side="left", padx=5)
        self._add_hover(self.btn_apply, "#34d399", self.CLR_ACCENT)
        
        self.btn_clear_batch = tk.Button(btn_row, text="CLEAR", command=lambda: self.batch_text.delete('1.0', tk.END), bg=self.CLR_BORDER, fg=self.CLR_TEXT, font=("Segoe UI", 8, "bold"), bd=0, padx=15, pady=6)
        self.btn_clear_batch.pack(side="left", padx=5)
        self._add_hover(self.btn_clear_batch, "#475569", self.CLR_BORDER)
        
        self.batch_text = scrolledtext.ScrolledText(batch_sec, height=6, bg=self.CLR_SIDEBAR, fg=self.CLR_ACCENT, font=("JetBrains Mono", 10), bd=0, highlightthickness=1, highlightbackground=self.CLR_BORDER)
        self.batch_text.pack(fill="x", pady=(0, 20))
        
        # Config row
        config_row = tk.Frame(batch_sec, bg=self.CLR_BG)
        config_row.pack(fill="x")
        
        # Quick Presets
        preset_frame = tk.Frame(config_row, bg=self.CLR_BG)
        preset_frame.pack(side="top", fill="x", pady=(0, 15))
        tk.Label(preset_frame, text="QUICK PRESETS:", bg=self.CLR_BG, fg=self.CLR_ACCENT, font=("Segoe UI", 8, "bold")).pack(side="left", padx=(0, 10))
        
        for name in ["Frontend", "Backend", "Full Stack", "Docs"]:
            btn = tk.Button(preset_frame, text=name, bg=self.CLR_BORDER, fg=self.CLR_TEXT, font=("Segoe UI", 8), bd=0, padx=10, pady=2, cursor="hand2",
                          command=lambda n=name: self.controller.apply_preset(n))
            btn.pack(side="left", padx=2)
            self._add_hover(btn, self.CLR_ACCENT, self.CLR_BORDER)

        # Extensions
        ext_frame = tk.Frame(config_row, bg=self.CLR_BG)
        ext_frame.pack(side="left", fill="x", expand=True)
        tk.Label(ext_frame, text="TARGET EXTENSIONS", bg=self.CLR_BG, fg=self.CLR_MUTED, font=("Segoe UI", 8, "bold")).pack(anchor="w")
        self.ext_entry = tk.Entry(ext_frame, bg=self.CLR_SIDEBAR, fg=self.CLR_TEXT, bd=0, font=("JetBrains Mono", 10), highlightthickness=1, highlightbackground=self.CLR_BORDER)
        self.ext_entry.pack(fill="x", pady=(6, 0), padx=(0, 15))
        self.ext_entry.insert(0, ".py, .js, .tsx, .html, .css, .md, .txt")
        
        # Ignore
        ign_frame = tk.Frame(config_row, bg=self.CLR_BG)
        ign_frame.pack(side="left", fill="x", expand=True)
        tk.Label(ign_frame, text="IGNORE LIST", bg=self.CLR_BG, fg="#ef4444", font=("Segoe UI", 8, "bold")).pack(anchor="w")
        self.ignore_entry = tk.Entry(ign_frame, bg=self.CLR_SIDEBAR, fg="#ef4444", bd=0, font=("JetBrains Mono", 10), highlightthickness=1, highlightbackground=self.CLR_BORDER)
        self.ignore_entry.pack(fill="x", pady=(6, 0))
        
        # 2. Selection Preview
        preview_sec = tk.LabelFrame(container, text=" CURRENT SELECTION PREVIEW ", bg=self.CLR_BG, fg=self.CLR_MUTED, font=("Segoe UI", 9, "bold"), padx=0, pady=0, bd=1, relief="solid")
        preview_sec.pack(fill="x", pady=(0, 25))
        
        preview_header = tk.Frame(preview_sec, bg=self.CLR_SIDEBAR, padx=20, pady=10)
        preview_header.pack(fill="x")
        
        tk.Label(preview_header, text="FILES SELECTED", bg=self.CLR_SIDEBAR, fg=self.CLR_MUTED, font=("Segoe UI", 8, "bold")).pack(side="left")
        
        prev_btn_row = tk.Frame(preview_header, bg=self.CLR_SIDEBAR)
        prev_btn_row.pack(side="right")
        
        tk.Button(prev_btn_row, text="SELECT ALL", command=self.controller.select_all, bg=self.CLR_SIDEBAR, fg=self.CLR_ACCENT, font=("Segoe UI", 8, "bold"), bd=0, cursor="hand2").pack(side="left", padx=10)
        tk.Button(prev_btn_row, text="DESELECT ALL", command=self.controller.deselect_all, bg=self.CLR_SIDEBAR, fg="#ef4444", font=("Segoe UI", 8, "bold"), bd=0, cursor="hand2").pack(side="left", padx=10)
        
        self.selection_display = scrolledtext.ScrolledText(preview_sec, height=8, bg="#020617", fg=self.CLR_ACCENT, font=("JetBrains Mono", 9), bd=0, padx=20, pady=15)
        self.selection_display.pack(fill="x")
        self.selection_display.config(state="disabled")
        
        # 3. Merge Button
        self.merge_status = tk.Label(container, text="Ready to Merge", bg=self.CLR_BG, fg=self.CLR_MUTED, font=("Segoe UI", 9))
        self.merge_status.pack(anchor="w", pady=(0, 5))
        
        self.progress = ttk.Progressbar(container, orient="horizontal", mode="determinate")
        self.progress.pack(fill="x", pady=(0, 15))
        
        self.btn_merge = tk.Button(container, text="SYNC & MERGE (ULTRA STREAM)", command=self.controller.run_merge, bg=self.CLR_ACCENT, fg=self.CLR_BG, font=("Segoe UI", 12, "bold"), bd=0, pady=18)
        self.btn_merge.pack(fill="x", pady=(0, 25))
        self._add_hover(self.btn_merge, "#34d399", self.CLR_ACCENT)
        
        # 4. Activity Log
        log_sec = tk.Frame(container, bg=self.CLR_BG, bd=1, relief="solid", highlightthickness=1, highlightbackground=self.CLR_BORDER)
        log_sec.pack(fill="both", expand=True)
        
        log_header = tk.Frame(log_sec, bg=self.CLR_SIDEBAR, padx=20, pady=10)
        log_header.pack(fill="x")
        
        tk.Label(log_header, text="ACTIVITY LOG", bg=self.CLR_SIDEBAR, fg=self.CLR_MUTED, font=("Segoe UI", 8, "bold")).pack(side="left")
        tk.Button(log_header, text="CLEAR LOG", command=lambda: self.log_area.delete('1.0', tk.END), bg=self.CLR_SIDEBAR, fg=self.CLR_MUTED, font=("Segoe UI", 8), bd=0, cursor="hand2").pack(side="right")
        
        self.log_area = scrolledtext.ScrolledText(log_sec, bg="#000000", fg=self.CLR_ACCENT, font=("JetBrains Mono", 9), bd=0, padx=20, pady=15)
        self.log_area.pack(fill="both", expand=True)

    def _build_map_tab(self):
        container = tk.Frame(self.tab_map, bg=self.CLR_BG, padx=30, pady=30)
        container.pack(fill="both", expand=True)
        
        ctrl = tk.Frame(container, bg=self.CLR_BG)
        ctrl.pack(fill="x", pady=(0, 20))
        
        tk.Label(ctrl, text="🔍 FILTER PATHS:", bg=self.CLR_BG, fg=self.CLR_ACCENT, font=("Segoe UI", 10, "bold")).pack(side="left")
        self.map_search = tk.Entry(ctrl, bg=self.CLR_SIDEBAR, fg=self.CLR_TEXT, bd=0, font=("JetBrains Mono", 11), width=40, highlightthickness=1, highlightbackground=self.CLR_BORDER)
        self.map_search.pack(side="left", padx=20)
        self.map_search.bind("<KeyRelease>", lambda e: self.controller.filter_map())
        
        tk.Button(ctrl, text="📋 COPY ALL", command=self.controller.copy_map_paths, bg=self.CLR_ACCENT, fg=self.CLR_BG, font=("Segoe UI", 9, "bold"), bd=0, padx=20, pady=8).pack(side="right")

        self.map_display = scrolledtext.ScrolledText(container, bg=self.CLR_SIDEBAR, fg="#cbd5e1", font=("JetBrains Mono", 10), bd=0, padx=20, pady=20, highlightthickness=1, highlightbackground=self.CLR_BORDER)
        self.map_display.pack(fill="both", expand=True)

    def _build_update_tab(self):
        container = tk.Frame(self.tab_update, bg=self.CLR_BG, padx=30, pady=30)
        container.pack(fill="both", expand=True)
        
        header = tk.Frame(container, bg=self.CLR_BG)
        header.pack(fill="x", pady=(0, 20))
        
        tk.Button(header, text="📂 SELECT SOURCE FILES", command=self.controller.select_sources, bg=self.CLR_ACCENT, fg=self.CLR_BG, font=("Segoe UI", 9, "bold"), bd=0, padx=20, pady=8).pack(side="left")
        tk.Button(header, text="🔄 REFRESH", command=self.controller.refresh_update_matches, bg=self.CLR_BORDER, fg=self.CLR_TEXT, font=("Segoe UI", 9), bd=0, padx=20, pady=8).pack(side="right")
        
        self.update_tree = ttk.Treeview(container, columns=("Source", "Target", "Status"), show="headings", height=15)
        self.update_tree.pack(fill="both", expand=True, pady=15)
        self.update_tree.heading("Source", text="Source File")
        self.update_tree.heading("Target", text="Project Path")
        self.update_tree.heading("Status", text="Status")
        
        self.update_tree.tag_configure("ready", foreground=self.CLR_ACCENT)
        self.update_tree.tag_configure("missing", foreground="#ef4444")
        self.update_tree.tag_configure("warning", foreground="#eab308")

        tk.Button(container, text="⚡ EXECUTE SMART OVERWRITE", command=self.controller.run_overwrite, bg="#ef4444", fg=self.CLR_TEXT, font=("Segoe UI", 11, "bold"), bd=0, pady=15).pack(fill="x")

    def _build_history_tab(self):
        container = tk.Frame(self.tab_history, bg=self.CLR_BG, padx=30, pady=30)
        container.pack(fill="both", expand=True)
        
        self.hist_tree = ttk.Treeview(container, columns=("Time", "Profile", "File"), show="headings", height=15)
        self.hist_tree.pack(fill="both", expand=True)
        self.hist_tree.heading("Time", text="Time")
        self.hist_tree.heading("Profile", text="Profile")
        self.hist_tree.heading("File", text="Filename")
        
        btn_frame = tk.Frame(container, bg=self.CLR_BG, pady=20)
        btn_frame.pack(fill="x")
        tk.Button(btn_frame, text="📂 OPEN FILE", command=self.controller.open_history_file, bg=self.CLR_ACCENT, fg=self.CLR_BG, font=("Segoe UI", 10, "bold"), bd=0, padx=25, pady=10).pack(side="left", padx=8)
        tk.Button(btn_frame, text="🔍 SHOW FOLDER", command=self.controller.open_history_folder, bg=self.CLR_BORDER, fg=self.CLR_TEXT, font=("Segoe UI", 10, "bold"), bd=0, padx=25, pady=10).pack(side="left", padx=8)
        tk.Button(btn_frame, text="🗑️ CLEAR HISTORY", command=self.controller.clear_history, bg="#ef4444", fg=self.CLR_TEXT, font=("Segoe UI", 10, "bold"), bd=0, padx=25, pady=10).pack(side="right", padx=8)

    def _build_footer(self):
        left_foot = tk.Frame(self.footer, bg=self.CLR_SIDEBAR)
        left_foot.pack(side="left", padx=20)
        
        tk.Label(left_foot, text="Project:", bg=self.CLR_SIDEBAR, fg=self.CLR_MUTED, font=("Segoe UI", 8)).pack(side="left")
        self.status_label = tk.Label(left_foot, text="None", bg=self.CLR_SIDEBAR, fg=self.CLR_TEXT, font=("Segoe UI", 8, "bold"))
        self.status_label.pack(side="left", padx=(5, 20))
        
        tk.Label(left_foot, text="Profile:", bg=self.CLR_SIDEBAR, fg=self.CLR_MUTED, font=("Segoe UI", 8)).pack(side="left")
        self.profile_label = tk.Label(left_foot, text="Default", bg=self.CLR_SIDEBAR, fg=self.CLR_TEXT, font=("Segoe UI", 8, "bold"))
        self.profile_label.pack(side="left", padx=(5, 0))
        
        right_foot = tk.Frame(self.footer, bg=self.CLR_SIDEBAR)
        right_foot.pack(side="right", padx=20)
        
        self.selection_label = tk.Label(right_foot, text="Selected: 0 files", bg=self.CLR_SIDEBAR, fg=self.CLR_ACCENT, font=("Segoe UI", 8, "bold"))
        self.selection_label.pack(side="left", padx=20)
        
        tk.Label(right_foot, text="UTF-8", bg=self.CLR_SIDEBAR, fg=self.CLR_MUTED, font=("Segoe UI", 8)).pack(side="left", padx=10)
        tk.Label(right_foot, text="v2.6.1-PRO", bg=self.CLR_SIDEBAR, fg=self.CLR_MUTED, font=("Segoe UI", 8)).pack(side="left", padx=10)

    def log(self, msg):
        self.log_area.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n")
        self.log_area.see(tk.END)

    def _add_hover(self, widget, hover_bg, normal_bg):
        """เพิ่มเอฟเฟกต์เมื่อเอาเมาส์ไปชี้ปุ่ม"""
        widget.bind("<Enter>", lambda e: widget.config(bg=hover_bg))
        widget.bind("<Leave>", lambda e: widget.config(bg=normal_bg))

    def update_selection_preview(self, selected_paths):
        """อัปเดตรายการไฟล์ที่เลือกในช่อง Preview"""
        self.selection_display.config(state="normal")
        self.selection_display.delete('1.0', tk.END)
        
        sorted_paths = sorted(list(selected_paths))
        if not sorted_paths:
            self.selection_display.insert(tk.END, "(No files selected)")
        else:
            # นับจำนวนไฟล์ (ไม่รวมโฟลเดอร์)
            files_count = sum(1 for p in sorted_paths if os.path.isfile(p))
            self.selection_display.insert(tk.END, f"Selected: {files_count} files\n" + "-"*40 + "\n")
            
            for i, p in enumerate(sorted_paths, 1):
                try:
                    root = self.controller.engine.project_root
                    rel = os.path.relpath(p, root) if root and p.startswith(root) else p
                except: rel = p
                
                idx = str(i).zfill(2)
                self.selection_display.insert(tk.END, f"{idx}  {rel}\n")
            
        self.selection_display.config(state="disabled")
        self.selection_display.see(tk.END)
