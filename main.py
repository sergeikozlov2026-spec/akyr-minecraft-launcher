import os, sys, threading, subprocess, traceback
from pathlib import Path
import tkinter as tk
from tkinter import messagebox

APP_NAME = "AKYR Client"
VERSION = "1.21.4"
BG = "#0b0d12"
PANEL = "#131722"
ACCENT = "#8b5cf6"
TEXT = "#f4f5fb"
MUTED = "#9299ad"
GREEN = "#51e3a4"

def app_home():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent

def external_app_dir():
    return app_home() / "app"

def minecraft_dir():
    appdata = os.environ.get("APPDATA")
    if appdata:
        return Path(appdata) / ".minecraft"
    return Path.home() / ".minecraft"

def load_launcher_lib():
    try:
        import minecraft_launcher_lib
        return minecraft_launcher_lib
    except ImportError:
        return None

class AkyrApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.geometry("860x570")
        self.minsize(760, 510)
        self.configure(bg=BG)
        self.busy = False
        self.status_text = tk.StringVar(value="Готов к запуску")
        self.progress_val = 0.0
        self.cancelled = False

        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", padx=30, pady=(22, 18))
        tk.Label(top, text="AKYR", bg=BG, fg=TEXT, font=("Arial", 26, "bold")).pack(side="left")
        tk.Label(top, text=f"CLIENT  /  MINECRAFT {VERSION}", bg=BG, fg=MUTED,
                 font=("Arial", 10, "bold")).pack(side="left", padx=14, pady=(8,0))
        tk.Label(top, text="● READY", bg=BG, fg=GREEN, font=("Arial", 10, "bold")).pack(side="right", pady=8)

        hero = tk.Frame(self, bg=PANEL, highlightbackground="#242b3b", highlightthickness=1)
        hero.pack(fill="both", expand=True, padx=30, pady=(0, 15))
        tk.Label(hero, text="ТВОЯ ИГРА.\nТВОЙ СТИЛЬ.", bg=PANEL, fg=TEXT,
                 font=("Arial", 32, "bold"), justify="center").pack(pady=(35, 8))
        tk.Label(hero, text="Первый запуск скачает необходимые файлы игры", bg=PANEL, fg=MUTED,
                 font=("Arial", 12)).pack(pady=(0, 20))

        self.nickname = tk.StringVar(value="")
        nickrow = tk.Frame(hero, bg=PANEL)
        nickrow.pack(pady=(0, 14))
        tk.Label(nickrow, text="Ник для офлайн-режима:", bg=PANEL, fg=MUTED,
                 font=("Arial", 10)).pack(side="left", padx=(0,10))
        self.nick_entry = tk.Entry(nickrow, textvariable=self.nickname, width=18, bg="#202637",
                                   fg=TEXT, insertbackground=TEXT, relief="flat",
                                   font=("Arial", 11))
        self.nick_entry.pack(side="left", ipady=7)

        self.play = tk.Button(hero, text="▶   ИГРАТЬ", command=self.start_play,
                              bg=ACCENT, fg="white", activebackground="#7443df",
                              activeforeground="white", relief="flat", bd=0,
                              font=("Arial", 15, "bold"), cursor="hand2", width=23, height=2)
        self.play.pack(pady=(0, 13))
        self.canvas = tk.Canvas(hero, width=360, height=8, bg="#292f40", highlightthickness=0)
        self.canvas.pack(pady=(0, 9))
        self.status = tk.Label(hero, textvariable=self.status_text, bg=PANEL, fg=MUTED, font=("Arial", 11))
        self.status.pack(pady=(0, 20))

        bottom = tk.Frame(self, bg=BG)
        bottom.pack(fill="x", padx=30, pady=(0, 15))
        tk.Label(bottom, text="AKYR CLIENT", bg=BG, fg="#555d70", font=("Arial", 9, "bold")).pack(side="left")
        tk.Button(bottom, text="ОТКРЫТЬ ПАПКУ ИГРЫ", command=self.open_game_folder, bg="#1a2030",
                  fg=TEXT, activebackground="#272f42", activeforeground=TEXT, relief="flat",
                  bd=0, padx=14, pady=8, cursor="hand2").pack(side="right")

    def set_status(self, msg, color=MUTED):
        self.after(0, lambda: self.status.config(fg=color))
        self.after(0, lambda: self.status_text.set(msg))

    def set_progress(self, value):
        value = max(0.0, min(1.0, float(value)))
        def draw():
            self.canvas.delete("all")
            self.canvas.create_rectangle(0, 0, 360*value, 8, fill=ACCENT, width=0)
        self.after(0, draw)

    def open_game_folder(self):
        path = minecraft_dir()
        path.mkdir(parents=True, exist_ok=True)
        if sys.platform == "win32":
            os.startfile(str(path))
        else:
            messagebox.showinfo(APP_NAME, str(path))

    def start_play(self):
        if self.busy: return
        nickname = self.nickname.get().strip()
        if not nickname:
            messagebox.showwarning(APP_NAME, "Введи ник для офлайн-режима. Для официальных серверов нужна авторизация Microsoft.")
            self.nick_entry.focus_set()
            return
        if not nickname.replace("_", "").isalnum() or len(nickname) > 16:
            messagebox.showwarning(APP_NAME, "Ник должен содержать 1–16 букв, цифр или подчёркиваний.")
            return
        self.busy = True
        self.play.config(state="disabled", text="ЗАПУСК...")
        self.nick_entry.config(state="disabled")
        self.set_progress(0)
        self.set_status("Подготовка запуска…", TEXT)
        threading.Thread(target=self.launch_game, args=(nickname,), daemon=True).start()

    def launch_game(self, nickname):
        try:
            lib = load_launcher_lib()
            if lib is None:
                self.set_status("Установка компонентов запуска…", TEXT)
                self.set_progress(0.04)
                cmd = [sys.executable, "-m", "pip", "install", "--user", "minecraft-launcher-lib"]
                proc = subprocess.run(cmd, capture_output=True, text=True)
                if proc.returncode != 0:
                    raise RuntimeError("Не удалось установить компонент запуска. Проверь интернет и попробуй снова.\n" + proc.stderr[-1200:])
                # Frozen builds should bundle dependencies; pip won't help from a frozen executable.
                lib = load_launcher_lib()
                if lib is None:
                    raise RuntimeError("Компонент запуска не найден. Для EXE нужно включить minecraft-launcher-lib при сборке.")
            mcdir = minecraft_dir()
            mcdir.mkdir(parents=True, exist_ok=True)
            version_id = VERSION
            versions = lib.utils.get_installed_versions(str(mcdir))
            installed = any(v.get("id") == version_id for v in versions)
            if not installed:
                self.set_status("Скачиваю Minecraft " + VERSION + "…", TEXT)
                self.set_progress(0.12)
                def callback(stage):
                    total = stage.get("total", 0) or 0
                    current = stage.get("current", 0) or 0
                    if total:
                        self.set_progress(0.12 + 0.68 * current / total)
                    name = stage.get("type", "Файлы")
                    self.set_status("Скачивание: " + str(name), TEXT)
                options = {"setStatus": lambda s: self.set_status(str(s), TEXT),
                           "setProgress": lambda a,b: self.set_progress(0.12 + 0.68*(a/b if b else 0))}
                try:
                    lib.install.install_minecraft_version(version_id, str(mcdir), callback=options)
                except TypeError:
                    lib.install.install_minecraft_version(version_id, str(mcdir))
            self.set_status("Подготавливаю запуск…", TEXT)
            self.set_progress(0.86)
            options = {
                "username": nickname,
                "uuid": "00000000-0000-0000-0000-000000000000",
                "token": "",
                "gameDirectory": str(mcdir),
                "launcherName": "AKYR Client",
                "launcherVersion": "1.0",
            }
            command = lib.command.get_minecraft_command(version_id, str(mcdir), options)
            self.set_progress(0.96)
            self.set_status("Запускаю Minecraft…", GREEN)
            subprocess.Popen(command, cwd=str(mcdir))
            self.set_progress(1.0)
            self.set_status("Minecraft запущен", GREEN)
        except Exception as exc:
            detail = str(exc)
            self.after(0, lambda d=detail: messagebox.showerror(APP_NAME, "Не удалось запустить Minecraft.\n\n" + d))
            self.set_status("Ошибка запуска", "#ff7373")
        finally:
            self.after(0, self.reset_controls)

    def reset_controls(self):
        self.busy = False
        self.play.config(state="normal", text="▶   ИГРАТЬ")
        self.nick_entry.config(state="normal")

if __name__ == "__main__":
    AkyrApp().mainloop()
