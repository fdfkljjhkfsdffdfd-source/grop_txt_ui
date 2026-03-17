import os
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox

# ตรวจสอบการรองรับ Drag and Drop
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    HAS_DND = True
except ImportError:
    HAS_DND = False

from grop_txt_engine import GropTxtEngine
from grop_txt_ui import GropTxtUI

class GropTxtController:
    """ส่วนเชื่อมต่อ Logic และ UI (Controller)"""
    def __init__(self):
        self.root = TkinterDnD.Tk() if HAS_DND else tk.Tk()
        self.engine = GropTxtEngine()
        self.ui = GropTxtUI(self.root, self)
        
        # เริ่มต้นข้อมูล
        self.engine.load_config()
        self._sync_engine_to_ui()
        
        # ผูกเหตุการณ์ (Event Binding)
        self.ui.tree.bind("<Button-1>", self.on_tree_click)
        self.ui.tree.bind("<<TreeviewOpen>>", self.on_tree_open)
        self.ui.prof_cb.bind("<<ComboboxSelected>>", self.on_profile_change)
        
        if HAS_DND:
            self.ui.root.drop_target_register(DND_FILES)
            self.ui.root.dnd_bind('<<Drop>>', self.handle_drop)

    def _sync_engine_to_ui(self):
        """ซิงค์ข้อมูลจาก Engine มาแสดงผลที่ UI"""
        self.ui.ignore_entry.delete(0, tk.END)
        self.ui.ignore_entry.insert(0, self.engine.ignore_list)
        self.ui.prof_cb['values'] = list(self.engine.profiles.keys())
        self.ui.prof_var.set(self.engine.current_profile)
        self.refresh_tree()
        self.update_history_ui()

    def open_project(self):
        """เปิดโฟลเดอร์โปรเจกต์"""
        path = filedialog.askdirectory()
        if path:
            self.engine.project_root = os.path.normpath(path)
            self.engine.selected_paths = set()
            self.refresh_tree()
            self.engine.scan_project_files(self.ui.ignore_entry.get())
            self.filter_map()
            self.ui.log(f"Project opened: {path}")

    def refresh_tree(self):
        """รีเฟรชรายการไฟล์ใน Treeview"""
        for item in self.ui.tree.get_children(): self.ui.tree.delete(item)
        if not self.engine.project_root: return
        root_node = self.ui.tree.insert("", "end", text=f"📦 {os.path.basename(self.engine.project_root)}", open=True, values=(self.engine.project_root,))
        self._load_dir_lazy(self.engine.project_root, root_node)
        self._update_tree_visuals()

    def _load_dir_lazy(self, path, parent):
        """โหลดรายการไฟล์แบบ Lazy Loading"""
        try:
            for child in self.ui.tree.get_children(parent): self.ui.tree.delete(child)
            ignores = self.engine.get_ignores(self.ui.ignore_entry.get())
            items = sorted(os.listdir(path))
            for i in items:
                full = os.path.join(path, i)
                is_dir = os.path.isdir(full)
                if i.startswith(".") and i != ".git": continue
                if i in ignores: continue
                
                icon = "📂" if is_dir else "📄"
                node = self.ui.tree.insert(parent, "end", text=f"{icon} {i}", values=(full,), tags=("folder" if is_dir else ""))
                if is_dir: self.ui.tree.insert(node, "end", text="...")
        except: pass

    def on_tree_open(self, event):
        """เมื่อผู้ใช้กดขยายโฟลเดอร์"""
        node = self.ui.tree.focus()
        path = self.ui.tree.item(node, "values")[0]
        if os.path.isdir(path):
            self._load_dir_lazy(path, node)
            self._update_tree_visuals()

    def on_tree_click(self, event):
        """เมื่อผู้ใช้คลิกเลือกไฟล์/โฟลเดอร์"""
        item = self.ui.tree.identify_row(event.y)
        if not item: return
        path = self.ui.tree.item(item, "values")[0]
        
        if path in self.engine.selected_paths:
            self.engine.selected_paths.remove(path)
        else:
            self.engine.selected_paths.add(path)
            
        self._update_tree_visuals()
        self.engine.save_config(self.ui.ignore_entry.get())

    def _update_tree_visuals(self):
        """อัปเดตการแสดงผล (สี/สัญลักษณ์) ของ Treeview"""
        for item in self.ui.tree.get_children():
            self._update_node_recursive(item)

    def _update_node_recursive(self, node):
        path = self.ui.tree.item(node, "values")[0]
        base = os.path.basename(path)
        is_dir = os.path.isdir(path)
        
        prefix = "[✓] " if path in self.engine.selected_paths else ""
        icon = "📂" if is_dir else "📄"
        
        tags = ("checked",) if path in self.engine.selected_paths else ("folder" if is_dir else "")
        self.ui.tree.item(node, text=f"{prefix}{icon} {base}", tags=tags)
        
        for child in self.ui.tree.get_children(node):
            self._update_node_recursive(child)

    def run_merge(self):
        """เริ่มกระบวนการรวมไฟล์"""
        if not self.engine.selected_paths:
            messagebox.showwarning("Warning", "Please select files first!")
            return
        
        def task():
            self.ui.log("🚀 Starting Merge Process...")
            path, count = self.engine.merge_files(self.ui.ext_entry.get(), self.ui.ignore_entry.get())
            if path:
                self.ui.log(f"✅ Success! Merged {count} files into {os.path.basename(path)}")
                self.root.after(0, self.update_history_ui)
                if sys.platform == 'win32': os.startfile(path)
            self.engine.save_config(self.ui.ignore_entry.get())

        threading.Thread(target=task, daemon=True).start()

    def update_history_ui(self):
        """อัปเดตตารางประวัติการทำงาน"""
        for item in self.ui.hist_tree.get_children(): self.ui.hist_tree.delete(item)
        for h in reversed(self.engine.history):
            self.ui.hist_tree.insert("", "end", values=(h["time"], h["profile"], h["name"]))

    def filter_map(self):
        """กรองข้อมูลใน Project Map"""
        query = self.ui.map_search.get().lower()
        if not self.engine.all_project_paths:
            self.engine.scan_project_files(self.ui.ignore_entry.get())
        
        filtered = [p for p in self.engine.all_project_paths if query in p.lower()]
        self.ui.map_display.delete('1.0', tk.END)
        self.ui.map_display.insert(tk.END, "\n".join(filtered))

    def select_sources(self):
        """เลือกไฟล์ต้นทางสำหรับ Smart Update"""
        files = filedialog.askopenfilenames()
        if files:
            for f in files:
                self.engine.source_files_map[os.path.basename(f)] = f
            self.refresh_update_matches()

    def refresh_update_matches(self):
        """รีเฟรชรายการไฟล์ที่ตรงกันใน Smart Update"""
        for item in self.ui.update_tree.get_children(): self.ui.update_tree.delete(item)
        ignores = self.engine.get_ignores(self.ui.ignore_entry.get())
        project_files = {}
        for root, dirs, files in os.walk(self.engine.project_root):
            dirs[:] = [d for d in dirs if d not in ignores]
            for f in files:
                project_files[f] = os.path.join(root, f)
        
        for name, src_path in self.engine.source_files_map.items():
            target = project_files.get(name, "❌ Not Found")
            status = "✅ Ready" if target != "❌ Not Found" else "⚠️ Missing"
            self.ui.update_tree.insert("", "end", values=(name, target, status))

    def run_overwrite(self):
        """เขียนทับไฟล์ในโปรเจกต์ด้วยไฟล์ต้นทาง"""
        # สามารถเพิ่ม Logic การเขียนทับได้ที่นี่
        pass

    def on_profile_change(self, e):
        """เมื่อเปลี่ยน Profile"""
        self.engine.current_profile = self.ui.prof_var.get()
        self.engine.load_config()
        self._sync_engine_to_ui()

    def handle_drop(self, event):
        """จัดการการลากไฟล์มาวาง (Drag & Drop)"""
        pass

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = GropTxtController()
    app.run()
