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
        self.ui.tree.bind("<Button-3>", self.show_context_menu)
        self.ui.tree.bind("<<TreeviewOpen>>", self.on_tree_open)
        self.ui.prof_cb.bind("<<ComboboxSelected>>", self.on_profile_change)
        
        # Keyboard Shortcuts
        self.root.bind("<Control-o>", lambda e: self.open_project())
        self.root.bind("<Control-s>", lambda e: self.run_merge())
        self.root.bind("<Control-l>", lambda e: self.ui.log_area.delete('1.0', tk.END))
        self.root.bind("<Control-f>", lambda e: self.ui.tree_search.focus_set())
        
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
        self.ui.update_selection_preview(self.engine.selected_paths)
        self._update_status_bar()

    def _update_status_bar(self):
        """อัปเดต Status Bar"""
        root_name = os.path.basename(self.engine.project_root) if self.engine.project_root else "None"
        self.ui.status_label.config(text=root_name)
        self.ui.profile_label.config(text=self.engine.current_profile)
        
        files_count = sum(1 for p in self.engine.selected_paths if os.path.isfile(p))
        self.ui.selection_label.config(text=f"เลือกแล้ว: {files_count} ไฟล์")

    def open_project(self):
        """เปิดโฟลเดอร์โปรเจกต์"""
        path = filedialog.askdirectory()
        if path:
            self.load_project(path)

    def load_project(self, path):
        """โหลดโปรเจกต์จาก Path ที่กำหนด"""
        path = os.path.normpath(path)
        if os.path.exists(path):
            self.engine.project_root = path
            self.engine.load_gitignore() # โหลด .gitignore ทันทีที่เปิดโปรเจกต์
            self.engine.selected_paths = set()
            self.refresh_tree()
            self.engine.scan_project_files(self.ui.ignore_entry.get())
            self.filter_map()
            self.ui.update_selection_preview(self.engine.selected_paths)
            self._update_status_bar()
            self.ui.log(f"เปิดโปรเจกต์แล้ว: {path}")
            self.update_recent_projects(path)

    def update_recent_projects(self, path):
        """อัปเดตรายการโปรเจกต์ล่าสุด"""
        if path in self.engine.recent_projects:
            self.engine.recent_projects.remove(path)
        self.engine.recent_projects.insert(0, path)
        self.engine.recent_projects = self.engine.recent_projects[:10]
        self.engine.save_config(self.ui.ignore_entry.get())

    def show_recent_menu(self):
        """แสดงเมนูโปรเจกต์ล่าสุด"""
        menu = tk.Menu(self.root, tearoff=0, bg="#1e293b", fg="#cbd5e1", activebackground="#38bdf8", activeforeground="#0f172a")
        if not self.engine.recent_projects:
            menu.add_command(label="(ไม่มีโปรเจกต์ล่าสุด)", state="disabled")
        else:
            for p in self.engine.recent_projects:
                # ใช้ default argument ใน lambda เพื่อป้องกันปัญหา closure
                menu.add_command(label=p, command=lambda path=p: self.load_project(path))
        
        x = self.ui.btn_recent.winfo_rootx()
        y = self.ui.btn_recent.winfo_rooty() + self.ui.btn_recent.winfo_height()
        menu.post(x, y)

    def save_new_profile(self):
        name = simpledialog.askstring("โปรไฟล์", "ชื่อ:")
        if self.engine.save_new_profile(name):
            self.ui.prof_cb['values'] = list(self.engine.profiles.keys())
            self.ui.prof_var.set(name)
            self.engine.save_config(self.ui.ignore_entry.get())
            self.ui.log(f"บันทึกโปรไฟล์ '{name}' แล้ว")

    def delete_profile(self):
        name = self.ui.prof_var.get()
        if messagebox.askyesno("ยืนยัน", f"ลบโปรไฟล์ '{name}' หรือไม่?"):
            if self.engine.delete_profile(name):
                self._sync_engine_to_ui()
                self.ui.log(f"ลบโปรไฟล์ '{name}' แล้ว")

    def apply_batch(self):
        raw = self.ui.batch_text.get('1.0', tk.END).strip()
        count, not_found = self.engine.apply_batch_selection(raw)
        self._update_tree_visuals()
        self.ui.update_selection_preview(self.engine.selected_paths)
        self._update_status_bar()
        self.ui.log(f"ใช้การเลือกแบบกลุ่มแล้ว: เลือก {count} ไฟล์")
        if not_found:
            self.ui.log(f"⚠️ ไม่พบ {len(not_found)} เส้นทาง")

    def clear_selection(self):
        if messagebox.askyesno("ยืนยัน", "ล้างไฟล์ที่เลือกทั้งหมดหรือไม่?"):
            self.engine.selected_paths = set()
            self._update_tree_visuals()
            self.ui.update_selection_preview(self.engine.selected_paths)
            self._update_status_bar()
            self.ui.log("ล้างการเลือกแล้ว")

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
            ignore_str = self.ui.ignore_entry.get()
            items = sorted(os.listdir(path))
            for i in items:
                full = os.path.join(path, i)
                is_dir = os.path.isdir(full)
                if i.startswith(".") and i != ".git" and i != ".gitignore": continue
                
                if self.engine.is_path_ignored(full, ignore_str):
                    self.ui.tree.insert(parent, "end", text=f"🚫 {i} (ข้าม)", values=(full,), tags=("ignored",))
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
        self.ui.update_selection_preview(self.engine.selected_paths)
        self.engine.save_config(self.ui.ignore_entry.get())

    def _recursive_select(self, node):
        values = self.ui.tree.item(node, "values")
        if not values: return
        
        path = values[0]
        ignore_str = self.ui.ignore_entry.get()
        if os.path.isdir(path):
            # สแกนไฟล์จริงในโฟลเดอร์
            ext_str = self.ui.ext_entry.get()
            exts = [x.strip().lower() if x.strip().startswith(".") else "." + x.strip().lower() 
                   for x in ext_str.split(",") if x.strip()]
            
            for root, dirs, files in os.walk(path):
                dirs[:] = [d for d in dirs if not self.engine.is_path_ignored(os.path.join(root, d), ignore_str)]
                has_matching_file = False
                for f in files:
                    full_f = os.path.join(root, f)
                    if any(f.lower().endswith(e) for e in exts) and not self.engine.is_path_ignored(full_f, ignore_str):
                        self.engine.selected_paths.add(full_f)
                        has_matching_file = True
                
                if has_matching_file:
                    self.engine.selected_paths.add(root)
            
            # ไม่ต้องเพิ่ม path (folder) เองถ้าไม่มีไฟล์ข้างใน
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
        
        ignore_str = self.ui.ignore_entry.get()
        ext_str = self.ui.ext_entry.get()
        exts = [x.strip().lower() if x.strip().startswith(".") else "." + x.strip().lower() 
               for x in ext_str.split(",") if x.strip()]
        
        for root, dirs, files in os.walk(self.engine.project_root):
            dirs[:] = [d for d in dirs if not self.engine.is_path_ignored(os.path.join(root, d), ignore_str)]
            
            # ตรวจสอบว่ามีไฟล์ที่ตรงตาม Extension ในโฟลเดอร์นี้หรือไม่
            has_matching_file = False
            for f in files:
                full_f = os.path.join(root, f)
                if any(f.lower().endswith(e) for e in exts) and not self.engine.is_path_ignored(full_f, ignore_str):
                    self.engine.selected_paths.add(full_f)
                    has_matching_file = True
            
            # เพิ่มโฟลเดอร์เข้า selection เฉพาะถ้ามีไฟล์ที่ตรงเงื่อนไข (เพื่อให้ UI แสดงเครื่องหมายถูก)
            if has_matching_file:
                self.engine.selected_paths.add(root)
        
        self._update_tree_visuals()
        self.ui.update_selection_preview(self.engine.selected_paths)
        self._update_status_bar()

    def deselect_all(self):
        """ยกเลิกการเลือกทั้งหมด"""
        self.engine.selected_paths.clear()
        self._update_tree_visuals()
        self.ui.update_selection_preview(self.engine.selected_paths)
        self._update_status_bar()

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
        
        self.ui.tree.item(node, text=f"{prefix}{icon} {base}" + (" (ข้าม)" if is_ignored else ""), tags=tuple(new_tags))
        
        if self.ui.tree.item(node, "open"):
            for child in self.ui.tree.get_children(node):
                self._update_node_recursive(child, exts)

    def run_merge(self):
        """เริ่มกระบวนการรวมไฟล์"""
        if not self.engine.selected_paths:
            messagebox.showwarning("คำเตือน", "กรุณาเลือกไฟล์ก่อน!")
            return
        
        def update_progress(current, total):
            percent = (current / total) * 100
            self.root.after(0, lambda: self.ui.progress.config(value=percent))
            self.root.after(0, lambda: self.ui.merge_status.config(text=f"กำลังรวมไฟล์... {current}/{total} ไฟล์"))

        def task():
            self.ui.log("🚀 กำลังเริ่มกระบวนการรวมไฟล์...")
            self.root.after(0, lambda: self.ui.progress.config(value=0))
            
            path, count = self.engine.merge_files(
                self.ui.ext_entry.get(), 
                self.ui.ignore_entry.get(),
                progress_callback=update_progress
            )
            
            if path:
                self.ui.log(f"✅ สำเร็จ! รวม {count} ไฟล์เข้ากับ {os.path.basename(path)}")
                self.root.after(0, self.update_history_ui)
                self.root.after(0, lambda: self.ui.progress.config(value=100))
                self.root.after(0, lambda: self.ui.merge_status.config(text="รวมไฟล์เสร็จสมบูรณ์!"))
                self.root.after(0, self._update_status_bar)
                
                if messagebox.askyesno("สำเร็จ", f"รวม {count} ไฟล์แล้ว\nต้องการเปิดไฟล์เอาต์พุตหรือไม่?"):
                    if sys.platform == 'win32': os.startfile(path)
                    else: subprocess.run(['open', path])
            else:
                self.ui.log("❌ การรวมไฟล์ล้มเหลวหรือไม่พบไฟล์")
                self.root.after(0, lambda: self.ui.progress.config(value=0))
                self.root.after(0, self._update_status_bar)
                
            self.engine.save_config(self.ui.ignore_entry.get())

        threading.Thread(target=task, daemon=True).start()

    def filter_tree(self):
        """กรองรายการใน Treeview ตามคำค้นหา"""
        query = self.ui.tree_search.get().lower()
        self._filter_node_recursive("", query)

    def apply_preset(self, name):
        """ใช้การตั้งค่าจาก Preset ที่เลือก"""
        preset = self.engine.presets.get(name)
        if not preset:
            return
            
        # 1. อัปเดต UI Fields
        self.ui.ext_entry.delete(0, tk.END)
        self.ui.ext_entry.insert(0, preset['ext'])
        self.ui.ignore_entry.delete(0, tk.END)
        self.ui.ignore_entry.insert(0, preset['ignore'])
        
        # 2. สั่ง Scan และ Select All ที่ตรงเงื่อนไขอัตโนมัติ
        if self.engine.project_root:
            self.ui.log(f"กำลังใช้พรีเซ็ต: {name}...")
            self.engine.scan_project_files(preset['ignore'])
            self.select_all() # ติ๊กเลือกไฟล์ทั้งหมดที่ตรงตาม Extension ใหม่
            self.refresh_tree()
            self.ui.log(f"ใช้พรีเซ็ต '{name}' แล้ว เลือกไฟล์ที่ตรงกันแล้ว")
        else:
            self.ui.log(f"โหลดพรีเซ็ต '{name}' แล้ว เปิดโปรเจกต์เพื่อดูผลลัพธ์")

    def _filter_node_recursive(self, parent, query):
        """ซ่อน/แสดง Node ตามคำค้นหา"""
        has_visible_child = False
        for child in self.ui.tree.get_children(parent):
            # ตรวจสอบลูกก่อน (Recursive)
            child_visible = self._filter_node_recursive(child, query)
            
            # ตรวจสอบตัวเอง
            text = self.ui.tree.item(child, "text").lower()
            self_visible = query in text
            
            tags = list(self.ui.tree.item(child, "tags"))
            if self_visible or child_visible:
                if "dimmed" in tags: tags.remove("dimmed")
                has_visible_child = True
            else:
                if "dimmed" not in tags: tags.append("dimmed")
            
            self.ui.tree.item(child, tags=tuple(tags))
        
        return has_visible_child

    def show_context_menu(self, event):
        """แสดงเมนูคลิกขวาบน Treeview"""
        item = self.ui.tree.identify_row(event.y)
        if not item: return
        
        self.ui.tree.selection_set(item)
        values = self.ui.tree.item(item, "values")
        if not values: return
        path = values[0]

        menu = tk.Menu(self.root, tearoff=0, bg="#1e293b", fg="#cbd5e1", activebackground="#38bdf8", activeforeground="#0f172a")
        menu.add_command(label="📂 เปิดใน Explorer", command=lambda: self.open_in_explorer(path))
        menu.add_command(label="📋 คัดลอกเส้นทาง", command=lambda: self.copy_path(path))
        menu.add_separator()
        if path in self.engine.selected_paths:
            menu.add_command(label="❌ ยกเลิกการเลือก", command=lambda: self._recursive_deselect(item))
        else:
            menu.add_command(label="✅ เลือก", command=lambda: self._recursive_select(item))
            
        menu.post(event.x_root, event.y_root)

    def open_in_explorer(self, path):
        """เปิดไฟล์/โฟลเดอร์ใน File Explorer"""
        if os.path.exists(path):
            if sys.platform == 'win32':
                subprocess.run(['explorer', '/select,', os.path.normpath(path)])
            else:
                subprocess.run(['open', '-R', path])

    def copy_path(self, path):
        """คัดลอก Path ไปยัง Clipboard"""
        self.root.clipboard_clear()
        self.root.clipboard_append(path)
        self.ui.log(f"คัดลอกเส้นทางแล้ว: {path}")

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
        if messagebox.askyesno("ยืนยัน", "ล้างประวัติทั้งหมดหรือไม่?"):
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
            self.ui.log("คัดลอกเส้นทางแผนผังไปยังคลิปบอร์ดแล้ว")

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
            messagebox.showwarning("คำเตือน", "ไม่มีไฟล์ที่ตรงกันสำหรับการอัปเดต")
            return
            
        if messagebox.askyesno("ยืนยัน", f"เขียนทับ {len(ready_items)} ไฟล์หรือไม่?"):
            count, logs = self.engine.execute_overwrite(ready_items)
            for log in logs: self.ui.log(log)
            messagebox.showinfo("สำเร็จ", f"อัปเดต {count} ไฟล์แล้ว")
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
        self.ui.update_selection_preview(self.engine.selected_paths)
        self.engine.save_config(self.ui.ignore_entry.get())

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = GropTxtController()
    app.run()
