import os
import json
import fnmatch
import re
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
        self.recent_projects = []
        self.all_project_paths = []
        self.source_files_map = {}
        self.gitignore_rules = []

        # Presets Configuration
        self.presets = {
            "ฟรอนต์เอนด์": {
                "ext": ".tsx, .jsx, .js, .html, .css, .scss",
                "ignore": "node_modules, .git, dist, build, .next"
            },
            "แบ็คเอนด์": {
                "ext": ".py, .sql, .env.example, .json, .yaml, .go, .php",
                "ignore": "__pycache__, .venv, .git, node_modules, vendor"
            },
            "ฟูลสแต็ก": {
                "ext": ".tsx, .ts, .py, .js, .sql, .html, .css, .json",
                "ignore": "node_modules, .venv, .git, dist, build"
            },
            "เอกสาร": {
                "ext": ".md, .txt, .pdf, .docx",
                "ignore": ".git, node_modules"
            }
        }

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
                    self.recent_projects = data.get("recent_projects", [])
                    
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
            "ignore_list": current_ignore_list,
            "recent_projects": self.recent_projects[:10]
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
        
        self.load_gitignore()
        project_files = {} # filename -> [list of full paths]
        
        for root, dirs, files in os.walk(self.project_root):
            dirs[:] = [d for d in dirs if not self.is_path_ignored(os.path.join(root, d), ignore_str)]
            for f in files:
                full_path = os.path.join(root, f)
                if self.is_path_ignored(full_path, ignore_str):
                    continue
                if f not in project_files: project_files[f] = []
                project_files[f].append(full_path)
        
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
                    logs.append(f"✅ อัปเดตแล้ว: {match['target']}")
                except Exception as e:
                    logs.append(f"❌ ล้มเหลว {match['target']}: {e}")
        return success_count, logs

    def get_ignores(self, ignore_str):
        """แปลงข้อความ Ignore เป็นรายการ"""
        return [x.strip() for x in ignore_str.split(",") if x.strip()]

    def load_gitignore(self):
        """โหลดกฎจากไฟล์ .gitignore"""
        self.gitignore_rules = []
        if not self.project_root:
            return
        
        gitignore_path = os.path.join(self.project_root, ".gitignore")
        if os.path.exists(gitignore_path):
            try:
                with open(gitignore_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith('#'):
                            continue
                        
                        negate = line.startswith('!')
                        if negate:
                            line = line[1:]
                        
                        # แปลง pattern เป็น regex อย่างง่าย
                        pattern = line
                        if pattern.endswith('/'):
                            pattern = pattern[:-1]
                        
                        try:
                            regex_str = fnmatch.translate(pattern)
                            self.gitignore_rules.append((re.compile(regex_str), negate))
                        except:
                            continue
            except Exception as e:
                print(f"Error loading .gitignore: {e}")

    def is_path_ignored(self, path, ignore_str):
        """ตรวจสอบว่า Path นี้ควรถูกข้ามหรือไม่ (เช็คทั้งรายการแมนนวลและ .gitignore)"""
        if not self.project_root:
            return False
            
        basename = os.path.basename(path)
        ignores = self.get_ignores(ignore_str)
        
        # 1. เช็คจากรายการแมนนวล
        if basename in ignores:
            return True
            
        # 2. เช็คจาก .gitignore
        try:
            rel_path = os.path.relpath(path, self.project_root).replace(os.sep, '/')
            if rel_path == '.': return False
            
            ignored = False
            for regex, negate in self.gitignore_rules:
                if regex.match(rel_path) or regex.match(basename):
                    ignored = not negate
            
            if ignored: return True
            
            # เช็คโฟลเดอร์แม่ด้วย (Recursive check for parents)
            parent = os.path.dirname(path)
            if parent != path and parent.startswith(self.project_root):
                if self.is_path_ignored(parent, ignore_str):
                    return True
        except:
            pass
            
        return False

    def scan_project_files(self, ignore_str):
        """สแกนไฟล์ทั้งหมดในโปรเจกต์เพื่อใช้ใน Map และ Smart Update"""
        if not self.project_root:
            return
        
        self.load_gitignore()
        all_paths = []
        for root, dirs, files in os.walk(self.project_root):
            # กรองโฟลเดอร์
            dirs[:] = [d for d in dirs if not self.is_path_ignored(os.path.join(root, d), ignore_str)]
            
            for f in files:
                full_path = os.path.join(root, f)
                if self.is_path_ignored(full_path, ignore_str):
                    continue
                all_paths.append(os.path.relpath(full_path, self.project_root))
        self.all_project_paths = sorted(all_paths)

    def merge_files(self, extensions_str, ignore_str, progress_callback=None):
        """รวมไฟล์ที่เลือกเข้าด้วยกัน"""
        exts = [x.strip().lower() if x.strip().startswith(".") else "." + x.strip().lower() 
                for x in extensions_str.split(",") if x.strip()]
        self.load_gitignore()
        
        file_list = []
        for p in self.selected_paths:
            if not os.path.exists(p): continue
            if os.path.isfile(p):
                if not self.is_path_ignored(p, ignore_str): file_list.append(p)
            elif os.path.isdir(p):
                for root, dirs, files in os.walk(p):
                    dirs[:] = [d for d in dirs if not self.is_path_ignored(os.path.join(root, d), ignore_str)]
                    for f in files:
                        full_f = os.path.join(root, f)
                        if self.is_path_ignored(full_f, ignore_str): continue
                        if not exts or os.path.splitext(f)[1].lower() in exts:
                            file_list.append(full_f)
        
        file_list = sorted(list(set(file_list)))
        if not file_list: return None, 0

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        out_name = f"merged_{timestamp}.txt"
        final_p = os.path.join(self.base_dir, out_name)
        
        total_files = len(file_list)
        with open(final_p, "w", encoding="utf-8") as out_f:
            out_f.write(f"# GROP_TXT MERGE REPORT\n# Generated: {datetime.now()}\n")
            for i, fp in enumerate(file_list):
                if progress_callback:
                    progress_callback(i + 1, total_files)
                
                rel = os.path.relpath(fp, self.project_root) if self.project_root else fp
                out_f.write(f"\n# --- START: {rel} ---\n")
                try:
                    with open(fp, "r", encoding="utf-8", errors="ignore") as in_f:
                        while True:
                            chunk = in_f.read(1024 * 1024) # 1MB chunk
                            if not chunk: break
                            out_f.write(chunk)
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

    def generate_json_template(self, raw_json):
        """แปลง JSON ขนาดใหญ่ให้เป็นเทมเพลตโครงสร้างที่สรุปแล้ว"""
        try:
            data = json.loads(raw_json)
            
            def simplify(obj):
                if isinstance(obj, dict):
                    new_obj = {}
                    for k, v in obj.items():
                        new_obj[k] = simplify(v)
                    return new_obj
                elif isinstance(obj, list):
                    if not obj:
                        return []
                    
                    # ถ้าเป็นรายการของ Object ที่มี 'type' ให้เก็บตัวอย่างของแต่ละ type
                    if all(isinstance(item, dict) and 'type' in item for item in obj if item is not None):
                        seen_types = set()
                        templates = []
                        for item in obj:
                            t = item.get('type')
                            if t not in seen_types:
                                templates.append(simplify(item))
                                seen_types.add(t)
                        return templates
                    
                    # ถ้าเป็นรายการทั่วไป ให้เก็บแค่ตัวแรกเป็นตัวอย่าง
                    return [simplify(obj[0])]
                else:
                    return obj

            template_data = simplify(data)
            return json.dumps(template_data, indent=2, ensure_ascii=False)
        except Exception as e:
            return f"Error: {str(e)}"
