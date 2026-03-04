import tkinter as tk
from tkinter import ttk
import threading
import urllib.request
import urllib.parse
import json

try:
    from pynput import keyboard as pynk
    HAS_HOTKEY = True
except ImportError:
    HAS_HOTKEY = False

LANGUAGES = {
    "自动": "auto",
    "中文": "zh-CN",
    "English": "en",
    "日本語": "ja",
    "한국어": "ko",
    "Français": "fr",
    "Deutsch": "de",
    "Español": "es",
    "Русский": "ru",
    "العربية": "ar",
}


def google_translate(text: str, src: str, dst: str) -> str:
    if not text.strip():
        return ""
    url = (
        "https://translate.googleapis.com/translate_a/single"
        f"?client=gtx&sl={src}&tl={dst}&dt=t&q={urllib.parse.quote(text)}"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10) as r:
        data = json.loads(r.read().decode())
    return "".join(p[0] for p in data[0] if p[0])


# ── 翻译面板 ────────────────────────────────────────────────────────────────
class TranslatorPanel(tk.Toplevel):
    W, H = 400, 460

    def __init__(self, master):
        super().__init__(master)
        self.overrideredirect(True)
        self.wm_attributes("-topmost", True)
        self.configure(bg="#1e1e2e")
        self.geometry(f"{self.W}x{self.H}")
        self._tx = self._ty = 0
        self._after_id = None
        self._busy = False
        self._build()
        self._style()

    # ── 定位 ──────────────────────────────────────────────────────────────
    def place_near(self, bx: int, by: int, ball: int):
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = max(10, min(bx - self.W + ball, sw - self.W - 10))
        y = max(10, min(by - self.H - 8, sh - self.H - 60))
        self.geometry(f"+{x}+{y}")
        self.deiconify()
        self.lift()
        self.focus_force()

    # ── 构建 UI ───────────────────────────────────────────────────────────
    def _build(self):
        # 标题栏（可拖拽）
        bar = tk.Frame(self, bg="#11111b", height=38)
        bar.pack(fill="x")
        bar.pack_propagate(False)
        bar.bind("<ButtonPress-1>", lambda e: setattr(self, "_tx", e.x) or setattr(self, "_ty", e.y))
        bar.bind("<B1-Motion>", lambda e: self.geometry(
            f"+{self.winfo_x()+e.x-self._tx}+{self.winfo_y()+e.y-self._ty}"))

        tk.Label(bar, text="  ✦ 快速翻译", bg="#11111b", fg="#cdd6f4",
                 font=("Segoe UI", 10, "bold")).pack(side="left")

        x_lbl = tk.Label(bar, text="  ✕  ", bg="#11111b", fg="#585b70",
                         font=("Segoe UI", 13), cursor="hand2")
        x_lbl.pack(side="right")
        x_lbl.bind("<Button-1>", lambda e: self.withdraw())
        x_lbl.bind("<Enter>", lambda e: x_lbl.config(fg="#f38ba8", bg="#2a1a1e"))
        x_lbl.bind("<Leave>", lambda e: x_lbl.config(fg="#585b70", bg="#11111b"))

        # 语言栏
        lbar = tk.Frame(self, bg="#1e1e2e")
        lbar.pack(fill="x", padx=14, pady=(10, 4))

        langs = list(LANGUAGES.keys())
        self.src_var = tk.StringVar(value="自动")
        ttk.Combobox(lbar, textvariable=self.src_var, values=langs,
                     state="readonly", width=9,
                     font=("Segoe UI", 10)).pack(side="left")

        sw_lbl = tk.Label(lbar, text=" ⇄ ", bg="#1e1e2e", fg="#89b4fa",
                          font=("Segoe UI", 13), cursor="hand2")
        sw_lbl.pack(side="left", padx=4)
        sw_lbl.bind("<Button-1>", self._swap)

        self.dst_var = tk.StringVar(value="中文")
        ttk.Combobox(lbar, textvariable=self.dst_var, values=langs[1:],
                     state="readonly", width=9,
                     font=("Segoe UI", 10)).pack(side="left")

        tk.Frame(self, bg="#313244", height=1).pack(fill="x", padx=14)

        # 输入框
        tk.Label(self, text="输入文本", bg="#1e1e2e", fg="#585b70",
                 font=("Segoe UI", 8)).pack(anchor="w", padx=16, pady=(8, 2))
        self.inp = tk.Text(self, height=6, wrap="word", relief="flat", bd=0,
                           bg="#313244", fg="#cdd6f4", insertbackground="#89b4fa",
                           font=("Segoe UI", 10), padx=10, pady=8, undo=True)
        self.inp.pack(fill="x", padx=14)
        self.inp.bind("<KeyRelease>", self._on_key)
        self.inp.bind("<Control-Return>", lambda e: self._translate())

        tk.Frame(self, bg="#313244", height=1).pack(fill="x", padx=14, pady=(8, 0))

        # 输出框
        tk.Label(self, text="翻译结果", bg="#1e1e2e", fg="#585b70",
                 font=("Segoe UI", 8)).pack(anchor="w", padx=16, pady=(8, 2))
        self.out = tk.Text(self, height=6, wrap="word", relief="flat", bd=0,
                           bg="#1e1e2e", fg="#a6e3a1",
                           font=("Segoe UI", 10), padx=14, pady=8, state="disabled")
        self.out.pack(fill="both", expand=True)

        # 底栏
        bot = tk.Frame(self, bg="#11111b", pady=7)
        bot.pack(fill="x", side="bottom")

        for txt, cmd, color in [
            ("翻译 Ctrl+↵", self._translate, "#89b4fa"),
            ("清空", self._clear, "#313244"),
            ("复制", self._copy, "#313244"),
        ]:
            b = tk.Button(bot, text=txt, command=cmd, bg=color,
                          fg="#1e1e2e" if color == "#89b4fa" else "#cdd6f4",
                          font=("Segoe UI", 9, "bold" if color == "#89b4fa" else "normal"),
                          bd=0, padx=10, pady=4, cursor="hand2",
                          activebackground="#74c7ec" if color == "#89b4fa" else "#45475a",
                          activeforeground="#1e1e2e" if color == "#89b4fa" else "#cdd6f4")
            b.pack(side="left", padx=(10 if txt.startswith("翻") else 4, 0))

        self.status = tk.StringVar(
            value="Ctrl+Shift+Space 呼出" if HAS_HOTKEY else "快捷键不可用（需安装 pynput）"
        )
        tk.Label(bot, textvariable=self.status, bg="#11111b", fg="#45475a",
                 font=("Segoe UI", 8)).pack(side="right", padx=10)

    def _style(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure("TCombobox", fieldbackground="#313244", background="#313244",
                    foreground="#cdd6f4", arrowcolor="#89b4fa",
                    bordercolor="#45475a", selectbackground="#45475a",
                    selectforeground="#cdd6f4")
        s.map("TCombobox", fieldbackground=[("readonly", "#313244")])

    # ── 操作 ──────────────────────────────────────────────────────────────
    def _swap(self, _=None):
        s, d = self.src_var.get(), self.dst_var.get()
        if s != "自动":
            self.src_var.set(d)
            self.dst_var.set(s)

    def _on_key(self, _=None):
        if self._after_id:
            self.after_cancel(self._after_id)
        self._after_id = self.after(700, self._translate)

    def _set_out(self, text: str):
        self.out.config(state="normal")
        self.out.delete("1.0", "end")
        self.out.insert("1.0", text)
        self.out.config(state="disabled")

    def _clear(self):
        self.inp.delete("1.0", "end")
        self._set_out("")
        self.status.set("已清空")

    def _copy(self):
        r = self.out.get("1.0", "end").strip()
        if r:
            self.clipboard_clear()
            self.clipboard_append(r)
            self.status.set("已复制 ✓")

    def _translate(self):
        if self._busy:
            return
        text = self.inp.get("1.0", "end").strip()
        if not text:
            return
        src = LANGUAGES[self.src_var.get()]
        dst = LANGUAGES.get(self.dst_var.get(), "zh-CN")
        self._busy = True
        self.status.set("翻译中…")
        threading.Thread(target=self._work, args=(text, src, dst), daemon=True).start()

    def _work(self, text, src, dst):
        try:
            r = google_translate(text, src, dst)
            self.after(0, self._done, r)
        except Exception as e:
            self.after(0, self._done, f"[失败] {e}\n\n请检查网络或代理。")

    def _done(self, result: str):
        self._set_out(result)
        self.status.set("完成 ✓")
        self._busy = False


# ── 悬浮球 ──────────────────────────────────────────────────────────────────
class FloatingBall(tk.Tk):
    SIZE = 58

    def __init__(self):
        super().__init__()
        self.overrideredirect(True)
        self.wm_attributes("-topmost", True)
        self.wm_attributes("-transparentcolor", "#000001")
        self.configure(bg="#000001")

        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        x, y = sw - self.SIZE - 20, sh - self.SIZE - 70
        self.geometry(f"{self.SIZE}x{self.SIZE}+{x}+{y}")

        self.cv = tk.Canvas(self, width=self.SIZE, height=self.SIZE,
                            bg="#000001", highlightthickness=0)
        self.cv.pack()
        self._draw("#89b4fa")

        self._panel: TranslatorPanel | None = None
        self._moved = False
        self._px = self._py = 0

        self.cv.bind("<ButtonPress-1>", self._press)
        self.cv.bind("<B1-Motion>", self._drag)
        self.cv.bind("<ButtonRelease-1>", self._release)
        self.cv.bind("<Enter>", lambda e: self._draw("#74c7ec"))
        self.cv.bind("<Leave>", lambda e: self._draw("#89b4fa"))

        if HAS_HOTKEY:
            threading.Thread(target=self._hotkey_loop, daemon=True).start()

    def _draw(self, color: str):
        s = self.SIZE
        self.cv.delete("all")
        self.cv.create_oval(2, 2, s - 2, s - 2,
                            fill=color, outline="#cdd6f4", width=1.5)
        self.cv.create_text(s // 2, s // 2, text="译",
                            fill="#1e1e2e", font=("Segoe UI", 22, "bold"))

    def _press(self, e):
        self._px, self._py = e.x, e.y
        self._moved = False

    def _drag(self, e):
        dx, dy = e.x - self._px, e.y - self._py
        if abs(dx) > 4 or abs(dy) > 4:
            self._moved = True
        self.geometry(f"+{self.winfo_x()+dx}+{self.winfo_y()+dy}")

    def _release(self, e):
        if not self._moved:
            self.after(0, self.toggle)

    def toggle(self):
        if self._panel and self._panel.winfo_exists():
            if self._panel.winfo_viewable():
                self._panel.withdraw()
            else:
                self._panel.place_near(self.winfo_x(), self.winfo_y(), self.SIZE)
        else:
            self._panel = TranslatorPanel(self)
            self._panel.place_near(self.winfo_x(), self.winfo_y(), self.SIZE)

    def _hotkey_loop(self):
        with pynk.GlobalHotKeys({"<ctrl>+<shift>+<space>": lambda: self.after(0, self.toggle)}):
            pass  # blocks forever


if __name__ == "__main__":
    if not HAS_HOTKEY:
        import subprocess, sys
        subprocess.run([sys.executable, "-m", "pip", "install", "pynput", "-q"])
    FloatingBall().mainloop()
