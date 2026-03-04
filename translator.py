import tkinter as tk
from tkinter import ttk, messagebox
import threading
import urllib.request
import urllib.parse
import json
import re
import sys
import os

# ── 语言列表 ──────────────────────────────────────────────
LANGUAGES = {
    "自动检测": "auto",
    "中文 (简体)": "zh-CN",
    "中文 (繁体)": "zh-TW",
    "英语": "en",
    "日语": "ja",
    "韩语": "ko",
    "法语": "fr",
    "德语": "de",
    "西班牙语": "es",
    "俄语": "ru",
    "阿拉伯语": "ar",
    "葡萄牙语": "pt",
    "意大利语": "it",
    "荷兰语": "nl",
    "波兰语": "pl",
    "泰语": "th",
    "越南语": "vi",
    "印尼语": "id",
    "土耳其语": "tr",
}

LANG_NAMES = list(LANGUAGES.keys())


def google_translate(text: str, src: str, dst: str) -> str:
    """使用非官方 Google 翻译 API 翻译文本。"""
    if not text.strip():
        return ""
    url = (
        "https://translate.googleapis.com/translate_a/single"
        f"?client=gtx&sl={src}&tl={dst}&dt=t&q={urllib.parse.quote(text)}"
    )
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    # 拼接所有翻译片段
    result = "".join(
        part[0] for part in data[0] if part[0]
    )
    return result


# ── 主窗口 ────────────────────────────────────────────────
class TranslatorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("✦ 快速翻译")
        self.geometry("720x500")
        self.minsize(600, 420)
        self.configure(bg="#1e1e2e")
        self._translating = False
        self._after_id = None
        self._build_ui()
        self._apply_style()
        # Ctrl+Enter 触发翻译
        self.bind("<Control-Return>", lambda e: self._translate())
        # 窗口置顶快捷键 Ctrl+T
        self.bind("<Control-t>", self._toggle_topmost)

    # ── UI 构建 ───────────────────────────────────────────
    def _build_ui(self):
        # ── 顶部工具栏 ───────────────────────────────────
        top = tk.Frame(self, bg="#1e1e2e", pady=6)
        top.pack(fill="x", padx=12)

        # 源语言
        tk.Label(top, text="从", bg="#1e1e2e", fg="#cdd6f4",
                 font=("Segoe UI", 10)).pack(side="left")
        self.src_var = tk.StringVar(value="自动检测")
        self.src_cb = ttk.Combobox(
            top, textvariable=self.src_var,
            values=LANG_NAMES, state="readonly", width=14,
            font=("Segoe UI", 10)
        )
        self.src_cb.pack(side="left", padx=(4, 8))

        # 互换按钮
        swap_btn = tk.Button(
            top, text="⇄", bg="#313244", fg="#cdd6f4",
            font=("Segoe UI", 12), bd=0, padx=6, pady=2,
            activebackground="#45475a", activeforeground="#cdd6f4",
            cursor="hand2", command=self._swap_languages
        )
        swap_btn.pack(side="left", padx=4)

        # 目标语言
        tk.Label(top, text="翻译为", bg="#1e1e2e", fg="#cdd6f4",
                 font=("Segoe UI", 10)).pack(side="left", padx=(8, 4))
        self.dst_var = tk.StringVar(value="中文 (简体)")
        self.dst_cb = ttk.Combobox(
            top, textvariable=self.dst_var,
            values=LANG_NAMES[1:], state="readonly", width=14,
            font=("Segoe UI", 10)
        )
        self.dst_cb.pack(side="left", padx=(0, 8))

        # 置顶按钮
        self.topmost_var = tk.BooleanVar(value=False)
        self.pin_btn = tk.Button(
            top, text="📌 置顶", bg="#313244", fg="#cdd6f4",
            font=("Segoe UI", 9), bd=0, padx=8, pady=3,
            activebackground="#45475a", activeforeground="#cdd6f4",
            cursor="hand2", command=self._toggle_topmost
        )
        self.pin_btn.pack(side="right")

        # ── 文本区域 ──────────────────────────────────────
        pane = tk.PanedWindow(
            self, orient="horizontal", bg="#1e1e2e",
            sashwidth=6, sashrelief="flat"
        )
        pane.pack(fill="both", expand=True, padx=12, pady=(0, 6))

        # 输入框
        left_frame = tk.Frame(pane, bg="#1e1e2e")
        pane.add(left_frame, minsize=200)
        tk.Label(
            left_frame, text="输入文本", bg="#1e1e2e",
            fg="#a6adc8", font=("Segoe UI", 9)
        ).pack(anchor="w")
        self.input_text = tk.Text(
            left_frame, wrap="word", font=("Segoe UI", 11),
            bg="#313244", fg="#cdd6f4", insertbackground="#cdd6f4",
            relief="flat", bd=0, padx=8, pady=8,
            undo=True
        )
        self.input_text.pack(fill="both", expand=True)
        self.input_text.bind("<KeyRelease>", self._on_keyrelease)

        # 输出框
        right_frame = tk.Frame(pane, bg="#1e1e2e")
        pane.add(right_frame, minsize=200)
        tk.Label(
            right_frame, text="翻译结果", bg="#1e1e2e",
            fg="#a6adc8", font=("Segoe UI", 9)
        ).pack(anchor="w")
        self.output_text = tk.Text(
            right_frame, wrap="word", font=("Segoe UI", 11),
            bg="#1e1e2e", fg="#a6e3a1", insertbackground="#cdd6f4",
            relief="flat", bd=0, padx=8, pady=8,
            state="disabled"
        )
        self.output_text.pack(fill="both", expand=True)

        # ── 底部工具栏 ───────────────────────────────────
        bot = tk.Frame(self, bg="#1e1e2e", pady=6)
        bot.pack(fill="x", padx=12)

        self.translate_btn = tk.Button(
            bot, text="翻  译  (Ctrl+Enter)",
            bg="#89b4fa", fg="#1e1e2e",
            font=("Segoe UI", 10, "bold"), bd=0,
            padx=16, pady=6, cursor="hand2",
            activebackground="#74c7ec", activeforeground="#1e1e2e",
            command=self._translate
        )
        self.translate_btn.pack(side="left")

        self.clear_btn = tk.Button(
            bot, text="清空", bg="#313244", fg="#cdd6f4",
            font=("Segoe UI", 10), bd=0, padx=12, pady=6,
            activebackground="#45475a", activeforeground="#cdd6f4",
            cursor="hand2", command=self._clear
        )
        self.clear_btn.pack(side="left", padx=8)

        self.copy_btn = tk.Button(
            bot, text="复制结果", bg="#313244", fg="#cdd6f4",
            font=("Segoe UI", 10), bd=0, padx=12, pady=6,
            activebackground="#45475a", activeforeground="#cdd6f4",
            cursor="hand2", command=self._copy_result
        )
        self.copy_btn.pack(side="left")

        self.status_var = tk.StringVar(value="就绪 · 支持 Ctrl+Enter 翻译")
        tk.Label(
            bot, textvariable=self.status_var,
            bg="#1e1e2e", fg="#6c7086", font=("Segoe UI", 9)
        ).pack(side="right")

        # 自动翻译开关
        self.auto_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            bot, text="自动翻译", variable=self.auto_var,
            bg="#1e1e2e", fg="#a6adc8",
            activebackground="#1e1e2e", activeforeground="#cdd6f4",
            selectcolor="#313244", font=("Segoe UI", 9)
        ).pack(side="right", padx=8)

    def _apply_style(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(
            "TCombobox",
            fieldbackground="#313244", background="#313244",
            foreground="#cdd6f4", arrowcolor="#cdd6f4",
            bordercolor="#45475a", darkcolor="#313244",
            lightcolor="#313244", selectbackground="#45475a",
            selectforeground="#cdd6f4"
        )
        style.map("TCombobox", fieldbackground=[("readonly", "#313244")])

    # ── 事件处理 ─────────────────────────────────────────
    def _on_keyrelease(self, event=None):
        if not self.auto_var.get():
            return
        if self._after_id:
            self.after_cancel(self._after_id)
        self._after_id = self.after(800, self._translate)

    def _swap_languages(self):
        src = self.src_var.get()
        dst = self.dst_var.get()
        if src == "自动检测":
            return
        self.src_var.set(dst)
        self.dst_var.set(src)

    def _toggle_topmost(self, event=None):
        new = not self.topmost_var.get()
        self.topmost_var.set(new)
        self.wm_attributes("-topmost", new)
        self.pin_btn.configure(
            bg="#89b4fa" if new else "#313244",
            fg="#1e1e2e" if new else "#cdd6f4"
        )

    def _clear(self):
        self.input_text.delete("1.0", "end")
        self._set_output("")
        self.status_var.set("已清空")

    def _copy_result(self):
        result = self.output_text.get("1.0", "end").strip()
        if result:
            self.clipboard_clear()
            self.clipboard_append(result)
            self.status_var.set("已复制到剪贴板 ✓")

    def _set_output(self, text: str):
        self.output_text.configure(state="normal")
        self.output_text.delete("1.0", "end")
        self.output_text.insert("1.0", text)
        self.output_text.configure(state="disabled")

    def _translate(self, event=None):
        if self._translating:
            return
        text = self.input_text.get("1.0", "end").strip()
        if not text:
            return
        src = LANGUAGES[self.src_var.get()]
        dst = LANGUAGES.get(self.dst_var.get(), "zh-CN")
        self._translating = True
        self.status_var.set("翻译中…")
        self.translate_btn.configure(state="disabled")
        threading.Thread(
            target=self._do_translate,
            args=(text, src, dst),
            daemon=True
        ).start()

    def _do_translate(self, text, src, dst):
        try:
            result = google_translate(text, src, dst)
            self.after(0, self._on_success, result)
        except Exception as e:
            self.after(0, self._on_error, str(e))

    def _on_success(self, result: str):
        self._set_output(result)
        self.status_var.set("翻译完成 ✓")
        self.translate_btn.configure(state="normal")
        self._translating = False

    def _on_error(self, msg: str):
        self._set_output(f"[翻译失败]\n{msg}\n\n请检查网络连接或代理设置。")
        self.status_var.set("翻译失败 ✗")
        self.translate_btn.configure(state="normal")
        self._translating = False


if __name__ == "__main__":
    app = TranslatorApp()
    app.mainloop()
