import os
import re
import sys
import json
import shutil
import queue
import threading
import subprocess
import tempfile
import urllib.request
import zipfile
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

APP_TITLE = "Web2APK"
TOOLS_URL = "https://dl.google.com/android/repository/commandlinetools-win-13114758_latest.zip"
DEFAULT_SDK = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "Android" / "Sdk"

def resource_dir():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent

DATA_DIR = Path(os.environ.get("APPDATA", str(Path.home()))) / "Web2APK"
DATA_DIR.mkdir(parents=True, exist_ok=True)
SETTINGS_FILE = DATA_DIR / "settings.json"
WORK_ROOT = DATA_DIR / "workspaces"
WORK_ROOT.mkdir(parents=True, exist_ok=True)

def run_hidden(cmd, cwd=None, env=None, stdin_text=None):
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    return subprocess.Popen(
        cmd, cwd=cwd, env=env, stdin=subprocess.PIPE if stdin_text is not None else None,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8",
        errors="replace", creationflags=flags
    )

class Web2APK(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1050x760")
        self.minsize(900, 650)
        self.q = queue.Queue()
        self.worker = None
        self.cancel_requested = False
        self.settings = self.load_settings()

        self.project = tk.StringVar(value=self.settings.get("project", ""))
        self.icon = tk.StringVar(value=self.settings.get("icon", ""))
        self.output = tk.StringVar(value=self.settings.get("output", str(Path.home() / "Desktop")))
        self.app_name = tk.StringVar(value=self.settings.get("app_name", "My App"))
        self.package = tk.StringVar(value=self.settings.get("package", "com.example.myapp"))
        self.version_name = tk.StringVar(value=self.settings.get("version_name", "1.0.0"))
        self.version_code = tk.StringVar(value=str(self.settings.get("version_code", 1)))
        self.apk_name = tk.StringVar(value=self.settings.get("apk_name", "MyApp.apk"))
        self.status = tk.StringVar(value="Ready")
        self.env_java = tk.StringVar(value="Not checked")
        self.env_node = tk.StringVar(value="Not checked")
        self.env_sdk = tk.StringVar(value="Not checked")

        self.make_ui()
        self.after(100, self.poll_queue)
        self.after(300, self.scan_environment)

    def load_settings(self):
        try:
            return json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def save_settings(self):
        d = {
            "project": self.project.get(), "icon": self.icon.get(), "output": self.output.get(),
            "app_name": self.app_name.get(), "package": self.package.get(),
            "version_name": self.version_name.get(), "version_code": self.version_code.get(),
            "apk_name": self.apk_name.get()
        }
        SETTINGS_FILE.write_text(json.dumps(d, indent=2), encoding="utf-8")

    def make_ui(self):
        style = ttk.Style(self)
        try:
            style.theme_use("vista")
        except Exception:
            pass

        outer = ttk.Frame(self, padding=18)
        outer.pack(fill="both", expand=True)

        title = ttk.Label(outer, text="Web2APK", font=("Segoe UI", 22, "bold"))
        title.pack(anchor="w")
        ttk.Label(outer, text="Turn a complete HTML/CSS/JavaScript project into an Android APK.",
                  font=("Segoe UI", 10)).pack(anchor="w", pady=(0, 14))

        top = ttk.LabelFrame(outer, text="Web Project", padding=12)
        top.pack(fill="x")
        row = ttk.Frame(top); row.pack(fill="x")
        ttk.Entry(row, textvariable=self.project).pack(side="left", fill="x", expand=True)
        ttk.Button(row, text="Select Folder", command=self.pick_project).pack(side="left", padx=(8,0))
        self.project_info = ttk.Label(top, text="Choose a folder containing index.html.")
        self.project_info.pack(anchor="w", pady=(8,0))

        middle = ttk.Frame(outer)
        middle.pack(fill="x", pady=12)
        left = ttk.LabelFrame(middle, text="App Settings", padding=12)
        left.pack(side="left", fill="both", expand=True, padx=(0,6))
        right = ttk.LabelFrame(middle, text="Icon & Output", padding=12)
        right.pack(side="left", fill="both", expand=True, padx=(6,0))

        fields = [
            ("App name", self.app_name),
            ("Package ID", self.package),
            ("Version name", self.version_name),
            ("Version code", self.version_code),
            ("APK filename", self.apk_name),
        ]
        for i,(lab,var) in enumerate(fields):
            ttk.Label(left, text=lab).grid(row=i, column=0, sticky="w", pady=5)
            ttk.Entry(left, textvariable=var).grid(row=i, column=1, sticky="ew", padx=(10,0), pady=5)
        left.columnconfigure(1, weight=1)

        ttk.Label(right, text="App icon (PNG/JPG)").grid(row=0,column=0,sticky="w")
        ir = ttk.Frame(right); ir.grid(row=1,column=0,sticky="ew",pady=(4,12))
        ttk.Entry(ir,textvariable=self.icon).pack(side="left",fill="x",expand=True)
        ttk.Button(ir,text="Choose",command=self.pick_icon).pack(side="left",padx=(8,0))

        ttk.Label(right, text="APK output folder").grid(row=2,column=0,sticky="w")
        orow = ttk.Frame(right); orow.grid(row=3,column=0,sticky="ew",pady=(4,12))
        ttk.Entry(orow,textvariable=self.output).pack(side="left",fill="x",expand=True)
        ttk.Button(orow,text="Choose",command=self.pick_output).pack(side="left",padx=(8,0))
        ttk.Label(right, text="Recommended icon: square 1024 × 1024 PNG.\nThe whole selected web project is packaged, not only index.html.",
                  justify="left").grid(row=4,column=0,sticky="w")
        right.columnconfigure(0, weight=1)

        envbox = ttk.LabelFrame(outer, text="Build Environment", padding=10)
        envbox.pack(fill="x")
        er = ttk.Frame(envbox); er.pack(fill="x")
        ttk.Label(er,text="Java:").grid(row=0,column=0,sticky="w"); ttk.Label(er,textvariable=self.env_java).grid(row=0,column=1,sticky="w",padx=(6,20))
        ttk.Label(er,text="Node:").grid(row=0,column=2,sticky="w"); ttk.Label(er,textvariable=self.env_node).grid(row=0,column=3,sticky="w",padx=(6,20))
        ttk.Label(er,text="Android SDK:").grid(row=0,column=4,sticky="w"); ttk.Label(er,textvariable=self.env_sdk).grid(row=0,column=5,sticky="w",padx=(6,20))
        ttk.Button(er,text="Recheck",command=self.scan_environment).grid(row=0,column=6,padx=(8,0))

        actions = ttk.Frame(outer); actions.pack(fill="x", pady=(12,8))
        self.build_btn = ttk.Button(actions,text="BUILD APK",command=self.start_build)
        self.build_btn.pack(side="left")
        self.cancel_btn = ttk.Button(actions,text="Cancel",command=self.cancel_build,state="disabled")
        self.cancel_btn.pack(side="left",padx=8)
        ttk.Button(actions,text="Open Output",command=self.open_output).pack(side="left")
        ttk.Label(actions,textvariable=self.status).pack(side="right")
        self.progress = ttk.Progressbar(outer, mode="indeterminate")
        self.progress.pack(fill="x", pady=(0,8))

        logbox = ttk.LabelFrame(outer,text="Build Log",padding=6)
        logbox.pack(fill="both",expand=True)
        self.log = tk.Text(logbox, height=15, bg="#111318", fg="#e7e7e7", insertbackground="white",
                           font=("Consolas", 9), wrap="word")
        sb = ttk.Scrollbar(logbox,command=self.log.yview)
        self.log.configure(yscrollcommand=sb.set)
        self.log.pack(side="left",fill="both",expand=True)
        sb.pack(side="right",fill="y")

    def pick_project(self):
        p = filedialog.askdirectory(title="Select web project folder")
        if p:
            self.project.set(p); self.inspect_project()

    def inspect_project(self):
        p = Path(self.project.get())
        if not p.exists():
            self.project_info.config(text="Folder not found."); return
        idx = p / "index.html"
        count = sum(1 for x in p.rglob("*") if x.is_file())
        self.project_info.config(text=("✓ index.html found" if idx.exists() else "✗ index.html missing") + f"   •   {count} files")

    def pick_icon(self):
        p = filedialog.askopenfilename(title="Choose app icon", filetypes=[("Images","*.png *.jpg *.jpeg"),("All files","*.*")])
        if p: self.icon.set(p)

    def pick_output(self):
        p = filedialog.askdirectory(title="Choose APK output folder")
        if p: self.output.set(p)

    def open_output(self):
        p = Path(self.output.get())
        p.mkdir(parents=True, exist_ok=True)
        os.startfile(str(p))

    def write_log(self, s):
        self.q.put(("log", s))

    def set_status(self, s):
        self.q.put(("status", s))

    def poll_queue(self):
        try:
            while True:
                kind, value = self.q.get_nowait()
                if kind == "log":
                    self.log.insert("end", value.rstrip()+"\n"); self.log.see("end")
                elif kind == "status": self.status.set(value)
                elif kind == "done": self.finish_build(value)
                elif kind == "env":
                    self.env_java.set(value[0]); self.env_node.set(value[1]); self.env_sdk.set(value[2])
        except queue.Empty:
            pass
        self.after(100, self.poll_queue)

    def scan_environment(self):
        def scan():
            java = self.find_java()
            node = shutil.which("node")
            sdkman = DEFAULT_SDK / "cmdline-tools" / "latest" / "bin" / "sdkmanager.bat"
            self.q.put(("env", ("Ready" if java else "Missing", "Ready" if node else "Missing",
                                "Ready" if sdkman.exists() else "Will install")))
        threading.Thread(target=scan,daemon=True).start()

    def find_java(self):
        candidates = []
        if os.environ.get("JAVA_HOME"): candidates.append(Path(os.environ["JAVA_HOME"]))
        for base in [Path(r"C:\Program Files\Eclipse Adoptium"), Path(r"C:\Program Files\Java"),
                     Path(r"C:\Program Files\Microsoft"), Path(r"C:\Program Files\Amazon Corretto")]:
            if base.exists():
                candidates += sorted([p for p in base.glob("jdk*") if p.is_dir()], reverse=True)
        for p in candidates:
            if (p/"bin"/"java.exe").exists() and (p/"bin"/"javac.exe").exists(): return p
        return None

    def validate(self):
        p = Path(self.project.get())
        if not p.is_dir() or not (p/"index.html").exists():
            return "Select a web project folder containing index.html."
        if not self.app_name.get().strip(): return "App name is required."
        pkg = self.package.get().strip()
        if not re.fullmatch(r"[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+", pkg):
            return "Package ID must look like com.example.myapp and use lowercase letters/numbers/underscores."
        try:
            if int(self.version_code.get()) < 1: raise ValueError
        except ValueError: return "Version code must be a positive integer."
        if not self.apk_name.get().lower().endswith(".apk"): return "APK filename must end in .apk."
        if self.icon.get() and not Path(self.icon.get()).is_file(): return "Selected icon file does not exist."
        return None

    def start_build(self):
        err = self.validate()
        if err:
            messagebox.showerror(APP_TITLE, err); return
        self.save_settings()
        self.log.delete("1.0","end")
        self.cancel_requested = False
        self.build_btn.config(state="disabled"); self.cancel_btn.config(state="normal")
        self.progress.start(10); self.status.set("Building...")
        self.worker = threading.Thread(target=self.build,daemon=True); self.worker.start()

    def cancel_build(self):
        self.cancel_requested = True
        self.set_status("Cancel requested...")

    def finish_build(self, result):
        self.progress.stop()
        self.build_btn.config(state="normal"); self.cancel_btn.config(state="disabled")
        ok, payload = result
        if ok:
            self.status.set("Build successful")
            messagebox.showinfo(APP_TITLE, f"APK created successfully:\n\n{payload}")
            try: subprocess.Popen(["explorer.exe", "/select,", str(payload)])
            except Exception: pass
        else:
            self.status.set("Build failed")
            messagebox.showerror(APP_TITLE, payload)

    def execute(self, cmd, cwd, env, stdin_text=None):
        if self.cancel_requested: raise RuntimeError("Build cancelled.")
        shown = subprocess.list2cmdline([str(x) for x in cmd])
        self.write_log("> " + shown)
        p = run_hidden([str(x) for x in cmd], cwd=str(cwd), env=env, stdin_text=stdin_text)
        if stdin_text is not None:
            try: p.stdin.write(stdin_text); p.stdin.close()
            except Exception: pass
        for line in iter(p.stdout.readline, ""):
            self.write_log(line.rstrip())
            if self.cancel_requested:
                try: p.terminate()
                except Exception: pass
                raise RuntimeError("Build cancelled.")
        rc = p.wait()
        if rc != 0: raise RuntimeError(f"Command failed with exit code {rc}.")
        return rc

    def ensure_sdk(self, sdk, env):
        sdkmanager = sdk/"cmdline-tools"/"latest"/"bin"/"sdkmanager.bat"
        if not sdkmanager.exists():
            self.set_status("Installing Android SDK tools...")
            self.write_log("Android command-line tools are not installed. Downloading...")
            sdk.mkdir(parents=True, exist_ok=True)
            z = Path(tempfile.gettempdir())/"web2apk-tools.zip"
            ex = Path(tempfile.gettempdir())/"web2apk-tools-extract"
            if z.exists(): z.unlink()
            if ex.exists(): shutil.rmtree(ex)
            urllib.request.urlretrieve(TOOLS_URL, z)
            with zipfile.ZipFile(z) as f: f.extractall(ex)
            latest = sdk/"cmdline-tools"/"latest"
            if latest.exists(): shutil.rmtree(latest)
            latest.mkdir(parents=True)
            src = ex/"cmdline-tools"
            for item in src.iterdir():
                dest = latest/item.name
                if item.is_dir(): shutil.copytree(item,dest)
                else: shutil.copy2(item,dest)
            z.unlink(missing_ok=True); shutil.rmtree(ex,ignore_errors=True)

        yes = "y\n"*100
        self.set_status("Configuring Android SDK...")
        self.execute([sdkmanager, f"--sdk_root={sdk}", "--licenses"], resource_dir(), env, yes)
        self.execute([sdkmanager, f"--sdk_root={sdk}", "platform-tools", "platforms;android-35", "build-tools;35.0.0"], resource_dir(), env)
        return sdkmanager

    def build(self):
        try:
            project = Path(self.project.get()).resolve()
            package = self.package.get().strip()
            workspace = WORK_ROOT / re.sub(r"[^A-Za-z0-9_.-]","_",package)
            if workspace.exists(): shutil.rmtree(workspace)
            workspace.mkdir(parents=True)

            self.set_status("Preparing project...")
            self.write_log(f"Web project: {project}")
            self.write_log(f"Workspace: {workspace}")

            www = workspace/"www"
            shutil.copytree(project,www)

            package_json = {
                "name":"web2apk-build",
                "version":"1.0.0",
                "private":True,
                "dependencies":{"@capacitor/core":"latest","@capacitor/android":"latest"},
                "devDependencies":{"@capacitor/cli":"latest"}
            }
            (workspace/"package.json").write_text(json.dumps(package_json,indent=2),encoding="utf-8")
            cap = {"appId":package,"appName":self.app_name.get().strip(),"webDir":"www"}
            (workspace/"capacitor.config.json").write_text(json.dumps(cap,indent=2),encoding="utf-8")

            java = self.find_java()
            if not java: raise RuntimeError("A full Java JDK was not found. Install JDK 21 and try again.")
            if not shutil.which("node") or not shutil.which("npm"):
                raise RuntimeError("Node.js/npm was not found. Install Node.js and try again.")

            env = os.environ.copy()
            env["JAVA_HOME"] = str(java)
            env["PATH"] = str(java/"bin") + os.pathsep + env.get("PATH","")
            sdk = DEFAULT_SDK
            env["ANDROID_HOME"] = str(sdk); env["ANDROID_SDK_ROOT"] = str(sdk)
            env["PATH"] = str(sdk/"platform-tools")+os.pathsep+str(sdk/"cmdline-tools"/"latest"/"bin")+os.pathsep+env["PATH"]

            self.set_status("Installing Capacitor dependencies...")
            self.execute(["npm.cmd","install"],workspace,env)
            self.ensure_sdk(sdk,env)

            self.set_status("Creating Android project...")
            self.execute(["npx.cmd","cap","add","android"],workspace,env)

            # local.properties
            (workspace/"android"/"local.properties").write_text("sdk.dir="+str(sdk).replace("\\","\\\\")+"\n",encoding="utf-8")

            self.set_status("Syncing web project...")
            self.execute(["npx.cmd","cap","sync","android"],workspace,env)

            # versions
            gradle = workspace/"android"/"app"/"build.gradle"
            s = gradle.read_text(encoding="utf-8")
            s = re.sub(r"versionCode\s+\d+", f"versionCode {int(self.version_code.get())}", s)
            s = re.sub(r'versionName\s+"[^"]*"', f'versionName "{self.version_name.get().strip()}"', s)
            gradle.write_text(s,encoding="utf-8")

            # app label
            strings = workspace/"android"/"app"/"src"/"main"/"res"/"values"/"strings.xml"
            if strings.exists():
                s = strings.read_text(encoding="utf-8")
                escaped = (self.app_name.get().replace("&","&amp;").replace("<","&lt;").replace(">","&gt;"))
                s = re.sub(r'(<string name="app_name">).*?(</string>)', r'\1'+escaped+r'\2', s)
                strings.write_text(s,encoding="utf-8")

            # icon
            if self.icon.get():
                self.set_status("Generating launcher icons...")
                from PIL import Image
                img = Image.open(self.icon.get()).convert("RGBA")
                sizes = {"mipmap-mdpi":48,"mipmap-hdpi":72,"mipmap-xhdpi":96,"mipmap-xxhdpi":144,"mipmap-xxxhdpi":192}
                res = workspace/"android"/"app"/"src"/"main"/"res"
                for folder,size in sizes.items():
                    d=res/folder; d.mkdir(parents=True,exist_ok=True)
                    out=img.resize((size,size),Image.Resampling.LANCZOS)
                    out.save(d/"ic_launcher.png"); out.save(d/"ic_launcher_round.png")
                for f in [res/"mipmap-anydpi-v26"/"ic_launcher.xml",res/"mipmap-anydpi-v26"/"ic_launcher_round.xml"]:
                    f.unlink(missing_ok=True)

            self.set_status("Building APK...")
            self.execute(["gradlew.bat","assembleDebug"],workspace/"android",env)

            built = workspace/"android"/"app"/"build"/"outputs"/"apk"/"debug"/"app-debug.apk"
            if not built.exists(): raise RuntimeError("Gradle completed but app-debug.apk was not found.")
            outdir=Path(self.output.get()); outdir.mkdir(parents=True,exist_ok=True)
            target=outdir/self.apk_name.get().strip()
            shutil.copy2(built,target)
            self.write_log(f"APK created: {target}")
            self.q.put(("done",(True,target)))
        except Exception as e:
            self.write_log("ERROR: "+str(e))
            self.q.put(("done",(False,str(e))))

if __name__ == "__main__":
    Web2APK().mainloop()
