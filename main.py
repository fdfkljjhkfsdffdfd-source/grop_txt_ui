import os
import sys
import threading
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog

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
        self.update_selection_display()

    def open_project(self):
        """เปิดโฟลเดอร์โปรเจกต์"""
        path = filedialog.askdirectory()
        if path:
            self.engine.project_root = os.path.normpath(path)
            self.engine.selected_paths = set()
            self.refresh_tree()
            self.engine.scan_project_files(self.ui.ignore_entry.get())
            self.filter_map()
            self.update_selection_display()
            self.ui.log(f"Project opened: {path}")

    def save_new_profile(self):
        name = simpledialog.askstring("Profile", "Name:")
        if self.engine.save_new_profile(name):
            self.ui.prof_cb['values'] = list(self.engine.profiles.keys())
            self.ui.prof_var.set(name)
            self.engine.save_config(self.ui.ignore_entry.get())
            self.ui.log(f"Profile '{name}' saved.")

    def delete_profile(self):
        name = self.ui.prof_var.get()
        if messagebox.askyesno("Confirm", f"Delete profile '{name}'?"):
            if self.engine.delete_profile(name):
                self._sync_engine_to_ui()
                self.ui.log(f"Profile '{name}' deleted.")

    def apply_batch(self):
        raw = self.ui.batch_text.get('1.0', tk.END).strip()
        count, not_found = self.engine.apply_batch_selection(raw)
        self._update_tree_visuals()
        self.update_selection_display()
        self.ui.log(f"Batch applied: {count} files selected.")
        if not_found:
            self.ui.log(f"⚠️ {len(not_found)} paths not found.")

    def clear_selection(self):
        if messagebox.askyesno("Confirm", "Clear all selected files?"):
            self.engine.selected_paths = set()
            self._update_tree_visuals()
            self.update_selection_display()
            self.ui.log("Selection cleared.")

    def update_selection_display(self):
        self.ui.selection_display.config(state="normal")
        self.ui.selection_display.delete('1.0', tk.END)
        sorted_paths = sorted(list(self.engine.selected_paths))
        if not sorted_paths:
            self.ui.selection_display.insert(tk.END, "(No files selected)")
        else:
            for p in sorted_paths:
                try:
                    rel = os.path.relpath(p, self.engine.project_root) if self.engine.project_root and p.startswith(self.engine.project_root) else p
                except: rel = p
                icon = "📁" if os.path.isdir(p) else "📄"
                self.ui.selection_display.insert(tk.END, f"{icon} {rel}\n")
        self.ui.selection_display.config(state="disabled")

    def refresh_tree(self):
        """รีเฟรชรายการไฟล์ใน Treeview"""
        for item in self.ui.tree.get_children(): self.ui.tree.delete(item)
        if not self.engine.project_root or not os.path.exists(self.engine.project_root): return
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
                
                if i in ignores:
                    self.ui.tree.insert(parent, "end", text=f"🚫 {i} (Ignored)", values=(full,), tags=("ignored",))
                else:
                    icon = "📂" if is_dir else "📄"
                    node = self.ui.tree.insert(parent, "end", text=f"{icon} {i}", values=(full,), tags=("folder" if is_dir else ""))
                    if is_dir: self.ui.tree.insert(node, "end", text="...")
        except: pass

    def on_tree_open(self, event):
        """เมื่อผู้ใช้กดขยายโฟลเดอร์"""
        node = self.ui.tree.focus()
        if not node: return
        values = self.ui.tree.item(node, "values")
        if not values: return
        path = values[0]
        if os.path.isdir(path):
            self._load_dir_lazy(path, node)
            self._update_tree_visuals()

    def on_tree_click(self, event):
        """เมื่อผู้ใช้คลิกเลือกไฟล์/โฟลเดอร์"""
        item = self.ui.tree.identify_row(event.y)
        if not item: return
        
        values = self.ui.tree.item(item, "values")
        if not values: return
        
        tags = self.ui.tree.item(item, "tags")
        if "ignored" in tags: return
        
        path = values[0]
        if path in self.engine.selected_paths:
            self._recursive_deselect(item)
        else:
            self._recursive_select(item)
            
        self._update_tree_visuals()
        self.update_selection_display()
        self.engine.save_config(self.ui.ignore_entry.get())

    def _recursive_select(self, node):
        values = self.ui.tree.item(node, "values")
        if not values: return
        
        path = values[0]
        if os.path.isdir(path):
            # สแกนไฟล์จริงในโฟลเดอร์
            ignores = self.engine.get_ignores(self.ui.ignore_entry.get())
            ext_str = self.ui.ext_entry.get()
            exts = [x.strip().lower() if x.strip().startswith(".") else "." + x.strip().lower() 
                   for x in ext_str.split(",") if x.strip()]
            
            for root, dirs, files in os.walk(path):
                dirs[:] = [d for d in dirs if d not in ignores and not d.startswith('.')]
                for f in files:
                    if any(f.lower().endswith(e) for e in exts) and f not in ignores:
                        self.engine.selected_paths.add(os.path.join(root, f))
            
            self.engine.selected_paths.add(path) # เพิ่มโฟลเดอร์เองด้วยเพื่อให้ UI แสดงผล
        else:
            tags = self.ui.tree.item(node, "tags")
            if "ignored" not in tags:
                self.engine.selected_paths.add(path)
        
        for child in self.ui.tree.get_children(node):
            self._recursive_select(child)

    def _recursive_deselect(self, node):
        values = self.ui.tree.item(node, "values")
        if not values: return
        
        path = values[0]
        if os.path.isdir(path):
            # ลบทุกอย่างที่ขึ้นต้นด้วย path นี้
            to_remove = [p for p in self.engine.selected_paths if p.startswith(path)]
            for p in to_remove:
                self.engine.selected_paths.remove(p)
        else:
            if path in self.engine.selected_paths:
                self.engine.selected_paths.remove(path)
                
        for child in self.ui.tree.get_children(node):
            self._recursive_deselect(child)

    def select_all(self):
        """เลือกไฟล์ทั้งหมดในโปรเจกต์"""
        if not self.engine.project_root: return
        self.engine.selected_paths.clear()
        
        ignores = self.engine.get_ignores(self.ui.ignore_entry.get())
        ext_str = self.ui.ext_entry.get()
        exts = [x.strip().lower() if x.strip().startswith(".") else "." + x.strip().lower() 
               for x in ext_str.split(",") if x.strip()]
        
        for root, dirs, files in os.walk(self.engine.project_root):
            dirs[:] = [d for d in dirs if d not in ignores and not d.startswith('.')]
            # เพิ่มโฟลเดอร์เข้า selection เพื่อให้ UI สวยงาม
            self.engine.selected_paths.add(root)
            for f in files:
                if any(f.lower().endswith(e) for e in exts) and f not in ignores:
                    self.engine.selected_paths.add(os.path.join(root, f))
        
        self._update_tree_visuals()
        self.ui.update_selection_preview(self.engine.selected_paths)

    def deselect_all(self):
        """ยกเลิกการเลือกทั้งหมด"""
        self.engine.selected_paths.clear()
        self._update_tree_visuals()
        self.ui.update_selection_preview(self.engine.selected_paths)

    def _update_tree_visuals(self):
        """อัปเดตการแสดงผล (สี/สัญลักษณ์) ของ Treeview"""
        exts_raw = self.ui.ext_entry.get().split(",")
        exts = [x.strip().lower() if x.strip().startswith(".") else "." + x.strip().lower() for x in exts_raw if x.strip()]
        for item in self.ui.tree.get_children():
            self._update_node_recursive(item, exts)

    def _update_node_recursive(self, node, exts):
        values = self.ui.tree.item(node, "values")
        if not values: return
        path = values[0]
        base = os.path.basename(path)
        is_dir = os.path.isdir(path)
        tags = list(self.ui.tree.item(node, "tags"))
        is_ignored = "ignored" in tags
        
        matches = True
        if not is_dir and not is_ignored:
            file_ext = os.path.splitext(path)[1].lower()
            matches = not exts or file_ext in exts
            
        prefix = "[✓] " if path in self.engine.selected_paths and not is_ignored else ""
        icon = "🚫" if is_ignored else ("📂" if is_dir else "📄")
        
        new_tags = ["folder"] if is_dir else []
        if is_ignored: new_tags.append("ignored")
        if not matches and not is_ignored: new_tags.append("dimmed")
        if path in self.engine.selected_paths and not is_ignored: new_tags.append("checked")
        
        self.ui.tree.item(node, text=f"{prefix}{icon} {base}" + (" (Ignored)" if is_ignored else ""), tags=tuple(new_tags))
        
        if self.ui.tree.item(node, "open"):
            for child in self.ui.tree.get_children(node):
                self._update_node_recursive(child, exts)

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

    def open_history_file(self):
        sel = self.ui.hist_tree.selection()
        if not sel: return
        idx = len(self.engine.history) - 1 - self.ui.hist_tree.index(sel[0])
        h = self.engine.history[idx]
        if os.path.exists(h["path"]):
            if sys.platform == 'win32': os.startfile(h["path"])
            else: subprocess.run(['open', h["path"]])

    def open_history_folder(self):
        sel = self.ui.hist_tree.selection()
        if not sel: return
        idx = len(self.engine.history) - 1 - self.ui.hist_tree.index(sel[0])
        h = self.engine.history[idx]
        folder = os.path.dirname(h["path"])
        if os.path.exists(folder):
            if sys.platform == 'win32': os.startfile(folder)
            else: subprocess.run(['open', folder])

    def clear_history(self):
        if messagebox.askyesno("Confirm", "Clear all history?"):
            self.engine.history = []
            self.update_history_ui()
            self.engine.save_config(self.ui.ignore_entry.get())

    def filter_map(self):
        """กรองข้อมูลใน Project Map"""
        query = self.ui.map_search.get().lower()
        if not self.engine.all_project_paths:
            self.engine.scan_project_files(self.ui.ignore_entry.get())
        
        filtered = [p for p in self.engine.all_project_paths if query in p.lower()]
        self.ui.map_display.config(state="normal")
        self.ui.map_display.delete('1.0', tk.END)
        self.ui.map_display.insert(tk.END, "\n".join(filtered))
        self.ui.map_display.config(state="disabled")

    def copy_map_paths(self):
        content = self.ui.map_display.get('1.0', tk.END).strip()
        if content:
            self.root.clipboard_clear()
            self.root.clipboard_append(content)
            self.ui.log("Copied map paths to clipboard.")

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
        matches = self.engine.get_smart_update_matches(self.ui.ignore_entry.get())
        
        self.current_matches = matches # Store for execution
        for m in matches:
            tag = "ready" if "✅" in m['status'] else ("missing" if "❌" in m['status'] else "warning")
            self.ui.update_tree.insert("", "end", values=(m['source'], m['target'], m['status']), tags=(tag,))

    def run_overwrite(self):
        """เขียนทับไฟล์ในโปรเจกต์ด้วยไฟล์ต้นทาง"""
        selected = self.ui.update_tree.selection()
        if not selected:
            items_to_process = self.current_matches
        else:
            items_to_process = [self.current_matches[self.ui.update_tree.index(i)] for i in selected]
            
        ready_items = [m for m in items_to_process if m['full_target']]
        if not ready_items:
            messagebox.showwarning("Warning", "No valid matches to update.")
            return
            
        if messagebox.askyesno("Confirm", f"Overwrite {len(ready_items)} files?"):
            count, logs = self.engine.execute_overwrite(ready_items)
            for log in logs: self.ui.log(log)
            messagebox.showinfo("Success", f"Updated {count} files.")
            self.refresh_update_matches()

    def on_profile_change(self, e):
        """เมื่อเปลี่ยน Profile"""
        self.engine.current_profile = self.ui.prof_var.get()
        self.engine.load_config()
        self._sync_engine_to_ui()

    def handle_drop(self, event):
        """จัดการการลากไฟล์มาวาง (Drag & Drop)"""
        raw_data = event.data
        if raw_data.startswith('{') and raw_data.endswith('}'): paths = [raw_data[1:-1]]
        else: paths = self.root.tk.splitlist(raw_data)
        
        for path in paths:
            clean = os.path.normpath(path)
            if os.path.isdir(clean):
                if not self.engine.project_root:
                    self.engine.project_root = clean
                    self.refresh_tree()
                elif clean.startswith(self.engine.project_root):
                    self.engine.selected_paths.add(clean)
            elif os.path.isfile(clean):
                if clean.startswith(self.engine.project_root):
                    self.engine.selected_paths.add(clean)
        
        self._update_tree_visuals()
        self.update_selection_display()
        self.engine.save_config(self.ui.ignore_entry.get())

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = GropTxtController()
    app.run()
