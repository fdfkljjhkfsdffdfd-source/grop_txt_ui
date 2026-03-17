import os
import json
from datetime import datetime

class GropTxtEngine:
    """ส่วนจัดการ Logic และข้อมูล (Model)"""
    def __init__(self, base_dir="GROP_TXT"):
        self.base_dir = base_dir
        self.config_file = os.path.join(self.base_dir, "studio_config.json")
        os.makedirs(self.base_dir, exist_ok=True)
        
        # สถานะเริ่มต้น
        self.project_root = ""
        self.selected_paths = set()
        self.profiles = {"Default": {"root": "", "selected": []}}
        self.current_profile = "Default"
        self.history = []
        self.ignore_list = ".git, node_modules, .venv, __pycache__, dist, build"
        self.all_project_paths = []
        self.source_files_map = {}

    def load_config(self):
        """โหลดค่าคอนฟิกจากไฟล์ JSON"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.profiles = data.get("profiles", {"Default": {"root": "", "selected": []}})
                    self.current_profile = data.get("last_profile", "Default")
                    self.history = data.get("history", [])
                    self.ignore_list = data.get("ignore_list", self.ignore_list)
                    
                    prof_data = self.profiles.get(self.current_profile, {})
                    self.project_root = prof_data.get("root", "")
                    self.selected_paths = set(prof_data.get("selected", []))
            except Exception as e:
                print(f"Error loading config: {e}")

    def save_config(self, current_ignore_list):
        """บันทึกค่าคอนฟิกลงไฟล์ JSON"""
        self.profiles[self.current_profile] = {
            "root": self.project_root,
            "selected": list(self.selected_paths)
        }
        data = {
            "profiles": self.profiles,
            "last_profile": self.current_profile,
            "history": self.history[-50:],
            "ignore_list": current_ignore_list
        }
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def get_ignores(self, ignore_str):
        return [i.strip() for i in ignore_str.split(",") if i.strip()]

    def scan_project_files(self, ignore_str):
        """สแกนไฟล์ทั้งหมดในโปรเจกต์เพื่อทำ Project Map"""
        if not self.project_root: return []
        ignores = self.get_ignores(ignore_str)
        paths = []
        for root, dirs, files in os.walk(self.project_root):
            dirs[:] = [d for d in dirs if d not in ignores and not d.startswith('.')]
            for f in files:
                if f in ignores: continue
                rel_p = os.path.relpath(os.path.join(root, f), self.project_root)
                paths.append(rel_p.replace(os.sep, '/'))
        self.all_project_paths = sorted(paths)
        return self.all_project_paths

    def merge_files(self, extensions_str, ignore_str):
        """รวมไฟล์ที่เลือกเข้าด้วยกัน"""
        exts = [x.strip().lower() if x.strip().startswith(".") else "." + x.strip().lower() 
                for x in extensions_str.split(",") if x.strip()]
        ignores = self.get_ignores(ignore_str)
        
        file_list = []
        for p in self.selected_paths:
            if not os.path.exists(p): continue
            if os.path.isfile(p):
                if os.path.basename(p) not in ignores: file_list.append(p)
            elif os.path.isdir(p):
                for root, dirs, files in os.walk(p):
                    dirs[:] = [d for d in dirs if d not in ignores]
                    for f in files:
                        if f in ignores: continue
                        full_f = os.path.join(root, f)
                        if not exts or os.path.splitext(f)[1].lower() in exts:
                            file_list.append(full_f)
        
        file_list = sorted(list(set(file_list)))
        if not file_list: return None, 0

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        out_name = f"merged_{timestamp}.txt"
        final_p = os.path.join(self.base_dir, out_name)
        
        with open(final_p, "w", encoding="utf-8") as out_f:
            out_f.write(f"# GROP_TXT MERGE REPORT\n# Generated: {datetime.now()}\n")
            for fp in file_list:
                rel = os.path.relpath(fp, self.project_root) if self.project_root else fp
                out_f.write(f"\n# --- START: {rel} ---\n")
                try:
                    with open(fp, "r", encoding="utf-8", errors="ignore") as in_f:
                        out_f.write(in_f.read())
                except Exception as e:
                    out_f.write(f"\n[Error: {e}]\n")
        
        new_history = {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "profile": self.current_profile,
            "name": out_name,
            "path": os.path.abspath(final_p)
        }
        self.history.append(new_history)
        return final_p, len(file_list)
