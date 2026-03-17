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

    def save_new_profile(self, name):
        """สร้างโปรไฟล์ใหม่"""
        if name:
            self.profiles[name] = {
                "root": self.project_root,
                "selected": list(self.selected_paths)
            }
            self.current_profile = name
            return True
        return False

    def delete_profile(self, name):
        """ลบโปรไฟล์"""
        if name != "Default" and name in self.profiles:
            del self.profiles[name]
            self.current_profile = "Default"
            prof_data = self.profiles.get(self.current_profile, {})
            self.project_root = prof_data.get("root", "")
            self.selected_paths = set(prof_data.get("selected", []))
            return True
        return False

    def apply_batch_selection(self, raw_text):
        """ใช้การเลือกแบบ Batch จากรายการเส้นทางไฟล์"""
        if not self.project_root:
            return 0, []
        
        lines = [line.strip() for line in raw_text.split('\n') if line.strip()]
        found_count = 0
        not_found = []
        
        for line in lines:
            p = line.replace('/', os.sep).replace('\\', os.sep)
            target_p = os.path.normpath(p if os.path.isabs(p) else os.path.join(self.project_root, p))
            if os.path.exists(target_p):
                self.selected_paths.add(target_p)
                found_count += 1
            else:
                not_found.append(line)
        return found_count, not_found

    def get_smart_update_matches(self, ignore_str):
        """ค้นหาไฟล์ในโปรเจกต์ที่ชื่อตรงกับไฟล์ต้นทางที่เลือกไว้"""
        if not self.project_root:
            return []
        
        ignores = self.get_ignores(ignore_str)
        project_files = {} # filename -> [list of full paths]
        
        for root, dirs, files in os.walk(self.project_root):
            dirs[:] = [d for d in dirs if d not in ignores and not d.startswith('.')]
            for f in files:
                if f in ignores: continue
                if f not in project_files: project_files[f] = []
                project_files[f].append(os.path.join(root, f))
        
        matches = []
        for fname, src_path in self.source_files_map.items():
            targets = project_files.get(fname, [])
            if not targets:
                matches.append({"source": fname, "target": "---", "status": "❌ Not Found", "full_target": None})
            else:
                for t in targets:
                    rel_target = os.path.relpath(t, self.project_root)
                    status = "✅ Ready" if len(targets) == 1 else "⚠️ Multiple Matches"
                    matches.append({"source": fname, "target": rel_target, "status": status, "full_target": t})
        return matches

    def execute_overwrite(self, matches_to_apply):
        """ดำเนินการเขียนทับไฟล์"""
        success_count = 0
        logs = []
        for match in matches_to_apply:
            src_path = self.source_files_map.get(match['source'])
            target_path = match['full_target']
            
            if src_path and os.path.exists(src_path) and target_path and os.path.exists(target_path):
                try:
                    with open(src_path, 'r', encoding='utf-8', errors='ignore') as f_src:
                        content = f_src.read()
                    with open(target_path, 'w', encoding='utf-8') as f_dest:
                        f_dest.write(content)
                    success_count += 1
                    logs.append(f"✅ Updated: {match['target']}")
                except Exception as e:
                    logs.append(f"❌ Failed {match['target']}: {e}")
        return success_count, logs

    def get_ignores(self, ignore_str):
        """แปลงข้อความ Ignore เป็นรายการ"""
        return [x.strip() for x in ignore_str.split(",") if x.strip()]

    def scan_project_files(self, ignore_str):
        """สแกนไฟล์ทั้งหมดในโปรเจกต์เพื่อใช้ใน Map และ Smart Update"""
        if not self.project_root:
            return
        
        ignores = self.get_ignores(ignore_str)
        all_paths = []
        for root, dirs, files in os.walk(self.project_root):
            dirs[:] = [d for d in dirs if d not in ignores and not d.startswith('.')]
            for f in files:
                if f in ignores: continue
                all_paths.append(os.path.relpath(os.path.join(root, f), self.project_root))
        self.all_project_paths = sorted(all_paths)

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
