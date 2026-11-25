"""NUKKIKKI — 누끼 따는 원숭이 🐵 단독 GUI 프로그램
이미지 드래그(또는 폴더 선택) → 누끼 → 선택한 크기의 투명 webp로 저장.
기본 저장 경로는 다운로드 폴더, 톱니바퀴(⚙)에서 변경 가능 (설정은 ~/.nukki_gui.json에 기억).
사용법: python nukki_gui.py
"""

import json
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog

from PIL import Image
from tkinterdnd2 import DND_FILES, TkinterDnD

EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
SIZES = ["400x400", "800x800", "1200x630", "1920x1080"]
MAX_SHOW = 8
CONFIG_PATH = Path.home() / ".nukki_gui.json"

BG = "#f5f5f5"
ACCENT = "#2e7d32"


def load_output_dir() -> Path:
    try:
        return Path(json.loads(CONFIG_PATH.read_text(encoding="utf-8"))["output_dir"])
    except Exception:
        return Path.home() / "Downloads"


def save_output_dir(p: Path):
    CONFIG_PATH.write_text(json.dumps({"output_dir": str(p)}, ensure_ascii=False), encoding="utf-8")


def resource_path(name: str) -> Path:
    # PyInstaller exe 안에 묶인 파일은 임시 해제 폴더(_MEIPASS)에서 찾아야 함
    return Path(getattr(sys, "_MEIPASS", Path(__file__).parent)) / name


def fit_to_canvas(img: Image.Image, w: int, h: int) -> Image.Image:
    # 구도 유지: 이미지 통째로 비율 축소 후 중앙 배치 (재배치·크롭 없음)
    scale = min(w / img.width, h / img.height)
    nw, nh = round(img.width * scale), round(img.height * scale)
    img = img.resize((nw, nh), Image.LANCZOS)
    canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    canvas.paste(img, ((w - nw) // 2, (h - nh) // 2))
    return canvas


class App(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()
        self.title("NUKKIKKI")
        self.geometry("440x560")
        self.resizable(False, False)
        self.configure(bg=BG)
        icon = resource_path("nukkikki.png")
        if icon.exists():
            self._icon_img = tk.PhotoImage(file=str(icon))
            self.iconphoto(True, self._icon_img)

        self.files: list[Path] = []
        self.output_dir = load_output_dir()
        self.remover = None
        self.stop_flag = threading.Event()
        self.running = False

        self._build_ui()

    def _build_ui(self):
        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", padx=12, pady=(10, 6))
        tk.Button(top, text="⚙ 설정", relief="groove", command=self.open_settings).pack(side="left")
        tk.Button(top, text="비우기", relief="groove", command=self.clear_files).pack(side="right", padx=(6, 0))
        tk.Button(top, text="폴더 선택", relief="groove", command=self.pick_folder).pack(side="right")

        self.drop_label = tk.Label(
            self, text="이미지를 여기로 드래그하세요\n(폴더째 끌어와도 됩니다)",
            bg="white", fg="#888888", relief="groove", bd=2, justify="left",
        )
        self.drop_label.pack(fill="both", expand=True, padx=12, pady=6)
        self.drop_label.drop_target_register(DND_FILES)
        self.drop_label.dnd_bind("<<Drop>>", self.on_drop)

        size_frame = tk.Frame(self, bg=BG)
        size_frame.pack(fill="x", padx=12, pady=6)
        tk.Label(size_frame, text="크기", bg=BG).pack(side="left", padx=(0, 8))
        self.size_var = tk.StringVar(value=SIZES[0])
        for s in SIZES:
            tk.Radiobutton(size_frame, text=s, value=s, variable=self.size_var,
                           indicatoron=0, width=9, pady=4).pack(side="left", padx=2)

        btn_frame = tk.Frame(self, bg=BG)
        btn_frame.pack(fill="x", padx=12, pady=6)
        self.run_btn = tk.Button(btn_frame, text="실행", width=18, pady=6,
                                 bg=ACCENT, fg="white", activebackground="#1b5e20",
                                 command=self.start)
        self.run_btn.pack(side="left")
        self.stop_btn = tk.Button(btn_frame, text="정지", width=18, pady=6,
                                  state="disabled", command=self.stop)
        self.stop_btn.pack(side="right")

        self.status = tk.Label(self, text=f"저장 경로: {self.output_dir}", bg=BG,
                               fg="#555555", anchor="w")
        self.status.pack(fill="x", padx=12, pady=(0, 10))

    # ---------- 파일 추가 ----------
    def on_drop(self, event):
        for raw in self.tk.splitlist(event.data):
            p = Path(raw)
            if p.is_dir():
                self.add_files(sorted(x for x in p.iterdir() if x.suffix.lower() in EXTS))
            elif p.suffix.lower() in EXTS:
                self.add_files([p])
        self.refresh_list()

    def pick_folder(self):
        folder = filedialog.askdirectory(title="이미지 폴더 선택")
        if folder:
            p = Path(folder)
            self.add_files(sorted(x for x in p.iterdir() if x.suffix.lower() in EXTS))
            self.refresh_list()

    def add_files(self, paths):
        for p in paths:
            if p not in self.files:
                self.files.append(p)

    def clear_files(self):
        if self.running:
            return
        self.files.clear()
        self.refresh_list()

    def refresh_list(self):
        if not self.files:
            self.drop_label.config(text="이미지를 여기로 드래그하세요\n(폴더째 끌어와도 됩니다)",
                                   fg="#888888", justify="left")
            return
        names = [p.name for p in self.files[:MAX_SHOW]]
        extra = len(self.files) - MAX_SHOW
        text = f"총 {len(self.files)}개\n\n" + "\n".join(names)
        if extra > 0:
            text += f"\n외 {extra}개"
        self.drop_label.config(text=text, fg="#222222", justify="left")

    # ---------- 실행/정지 ----------
    def start(self):
        if self.running or not self.files:
            if not self.files:
                self.set_status("이미지를 먼저 넣어주세요")
            return
        self.running = True
        self.stop_flag.clear()
        self.run_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        threading.Thread(target=self.worker, daemon=True).start()

    def stop(self):
        self.stop_flag.set()
        self.set_status("정지 요청됨 — 현재 이미지까지 처리 후 멈춥니다")

    def worker(self):
        try:
            if self.remover is None:
                self.set_status("모델 로딩 중... (첫 실행은 시간이 걸립니다)")
                from transparent_background import Remover
                self.remover = Remover(mode="base")

            w, h = map(int, self.size_var.get().split("x"))
            out_dir = self.output_dir
            out_dir.mkdir(parents=True, exist_ok=True)

            files = list(self.files)
            done = 0
            for i, p in enumerate(files, 1):
                if self.stop_flag.is_set():
                    self.set_status(f"정지됨: {done}/{len(files)}개 완료 → {out_dir}")
                    break
                self.set_status(f"[{i}/{len(files)}] {p.name} 처리 중...")
                try:
                    img = Image.open(p).convert("RGB")
                    img = self.remover.process(img, type="rgba")
                    img = fit_to_canvas(img.convert("RGBA"), w, h)
                    img.save(out_dir / f"{p.stem}.webp", "WEBP")
                    done += 1
                except Exception as e:
                    self.set_status(f"[{i}/{len(files)}] {p.name} 실패: {e}")
            else:
                self.set_status(f"완료: {done}/{len(files)}개 → {out_dir}")
        except Exception as e:
            self.set_status(f"오류: {e}")
        finally:
            self.running = False
            self.after(0, lambda: (self.run_btn.config(state="normal"),
                                   self.stop_btn.config(state="disabled")))

    def set_status(self, text):
        self.after(0, lambda: self.status.config(text=text))

    # ---------- 설정 ----------
    def open_settings(self):
        win = tk.Toplevel(self)
        win.title("설정")
        win.geometry("360x150")
        win.resizable(False, False)
        win.configure(bg=BG)
        win.transient(self)
        win.grab_set()

        tk.Label(win, text="누끼 파일 저장 경로", bg=BG, anchor="w").pack(fill="x", padx=14, pady=(12, 4))
        path_label = tk.Label(win, text=str(self.output_dir), bg="white", relief="groove",
                              anchor="w", padx=6, pady=4, wraplength=320)
        path_label.pack(fill="x", padx=14)

        def change():
            folder = filedialog.askdirectory(title="저장 폴더 선택", parent=win)
            if folder:
                self.output_dir = Path(folder)
                save_output_dir(self.output_dir)
                path_label.config(text=str(self.output_dir))
                self.set_status(f"저장 경로: {self.output_dir}")

        def reset():
            self.output_dir = Path.home() / "Downloads"
            save_output_dir(self.output_dir)
            path_label.config(text=str(self.output_dir))
            self.set_status(f"저장 경로: {self.output_dir}")

        btns = tk.Frame(win, bg=BG)
        btns.pack(fill="x", padx=14, pady=10)
        tk.Button(btns, text="경로 변경", command=change).pack(side="left")
        tk.Button(btns, text="기본값 (다운로드 폴더)", command=reset).pack(side="left", padx=8)
        tk.Button(btns, text="닫기", command=win.destroy).pack(side="right")


def selftest(src: Path, dst: Path):
    # exe 빌드 검증용: 창 없이 누끼 1장 처리 (실패 시 같은 폴더에 selftest_error.txt 기록)
    try:
        from transparent_background import Remover
        remover = Remover(mode="base")
        img = Image.open(src).convert("RGB")
        img = remover.process(img, type="rgba")
        fit_to_canvas(img.convert("RGBA"), 400, 400).save(dst, "WEBP")
        sys.exit(0)
    except Exception:
        import traceback
        (dst.parent / "selftest_error.txt").write_text(traceback.format_exc(), encoding="utf-8")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "--selftest":
        selftest(Path(sys.argv[2]), Path(sys.argv[3]))
    App().mainloop()
