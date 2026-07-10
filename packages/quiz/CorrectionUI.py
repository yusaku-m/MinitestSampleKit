"""予測修正 GUI — predictions.csv の Corrected 列をクリック操作で修正する。

元リポジトリ Grading の 3-4ME_Strength_of_the_Material_Commons/correction_ui.py
（CorrectionWindow）を、このサンプルキットの複数の採点フロー（週次小テスト／
個別再テスト／QR一括採点）から共通で使えるよう、コンストラクタを
「base_dir（scan/・result/ を含むフォルダ）」ではなく「result_dir + scan_dirs」を
直接受け取る形に一般化した移植版。QR一括採点は result_dir（週ごと）と
scan_dir（学生横断で共有）が別ディレクトリになるため、この一般化が必要になる。

ビュー構成（ウィンドウ内 Notebook）:
  ラベル別 … 予測ラベル（1..9,0,blank ／ +,-,blank）ごとに切り出し画像サムネイルを
             一覧表示。誤予測をクリック → メニューで正しいラベルを選択 → 即 CSV 保存。
  シート別 … スキャン全体画像とその答案の予測結果を1シートずつ確認・修正できる。

predictions.csv 仕様（packages/quiz/Sheet.py get_answers_and_predict が生成）:
  number モード: 0-9 がそのまま、blank=10。plusminus モード: +=0, -=1, blank=2。
  再採点（Sheet.get_format_answers）は Corrected 列のみを読むため、修正後は
  GUI の「採点」を再実行すると反映される。Corrected は int で保存する
  （float/空文字が混ざると Sheet 側の数値比較・int(str(...)) が壊れる）。
"""

from __future__ import annotations

import datetime
import os
import tkinter as tk
import tkinter.font as tkfont
from tkinter import messagebox, ttk

import pandas as pd
from PIL import Image as PILImage
from PIL import ImageTk

# --- ラベル ⇔ CSV 値の対応 -------------------------------------------------
NUMBER_LABELS = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "blank"]
PM_LABELS = ["+", "-", "blank"]
_NUM_TO_VAL = {**{str(d): d for d in range(10)}, "blank": 10}
_PM_TO_VAL = {"+": 0, "-": 1, "blank": 2}


def labels_for(mode: str):
    return PM_LABELS if mode == "plusminus" else NUMBER_LABELS


def val_to_label(mode: str, val) -> str:
    try:
        v = int(float(val))
    except (TypeError, ValueError):
        return str(val)
    if mode == "plusminus":
        return {0: "+", 1: "-", 2: "blank"}.get(v, str(v))
    return "blank" if v == 10 else str(v)


def label_to_val(mode: str, label) -> int:
    t = str(label).strip()
    mapping = _PM_TO_VAL if mode == "plusminus" else _NUM_TO_VAL
    if t in mapping:
        return mapping[t]
    return int(float(t))


class ExternalChangeError(RuntimeError):
    """predictions.csv がロード後に外部（採点処理等）で変更された。"""


# --- データモデル -----------------------------------------------------------
class PredictionStore:
    """predictions.csv のラッパー。ディスク I/O はここに集約する。

    result_dir: predictions.csv と image/raw/ を含むフォルダ。
    scan_dirs : シート別ビューでスキャン全体画像を探すフォルダの候補（先勝ち）。
    """

    DERIVED = ["scan_filename", "mode", "pred_num", "conf", "is_split", "is_corrected"]

    def __init__(self, result_dir: str, scan_dirs=()):
        self.result_dir = result_dir
        self.csv_path = os.path.join(result_dir, "predictions.csv")
        self.raw_img_dir = os.path.join(result_dir, "image", "raw")
        self.scan_dirs = list(scan_dirs)
        self.df: pd.DataFrame | None = None
        self._mtime: float | None = None
        self._thumb_cache: dict = {}
        self._placeholders: dict = {}

    # --- 読み書き ---
    def load(self):
        df = pd.read_csv(self.csv_path, encoding="utf-8-sig")
        df["mode"] = df["Predict_Mode"].astype(str).str.strip().str.lower()
        # Corrected を int64 に正規化（NaN/空文字→Predicted、文字列ラベルは値へ変換）。
        # Sheet.get_format_answers は Corrected を数値比較・str() するため float や
        # 空文字が混ざると採点が壊れる。
        corrected = []
        for corr, pred, m in zip(df["Corrected"], df["Predicted"], df["mode"]):
            if pd.isna(corr) or str(corr).strip() == "":
                corr = pred
            try:
                corrected.append(int(float(corr)))
                continue
            except (TypeError, ValueError):
                pass
            try:
                corrected.append(label_to_val(m, corr))
            except (TypeError, ValueError):
                corrected.append(int(float(pred)))
        df["Corrected"] = pd.array(corrected, dtype="int64")

        df["scan_filename"] = df["Source_path"].map(
            lambda x: os.path.basename(str(x).replace("\\", "/"))
        )
        vote_cols = [c for c in df.columns if str(c).startswith("Votes_for_")]
        votes = df[vote_cols].apply(pd.to_numeric, errors="coerce").fillna(0)
        total = votes.sum(axis=1)
        mx = votes.max(axis=1)
        df["conf"] = (mx / total.where(total > 0) * 100).fillna(0.0)
        df["is_split"] = mx < total
        df["pred_num"] = pd.to_numeric(df["Predicted"], errors="coerce")
        df["is_corrected"] = df["Corrected"] != df["pred_num"]
        self.df = df
        try:
            self._mtime = os.path.getmtime(self.csv_path)
        except OSError:
            self._mtime = None

    def check_external_change(self):
        if self._mtime is None:
            return
        try:
            cur = os.path.getmtime(self.csv_path)
        except OSError:
            return
        if abs(cur - self._mtime) > 1e-6:
            raise ExternalChangeError(self.csv_path)

    def save(self):
        self.check_external_change()
        out = self.df.drop(columns=[c for c in self.DERIVED if c in self.df.columns])
        tmp = self.csv_path + ".tmp"
        out.to_csv(tmp, index=False, encoding="utf-8-sig")
        os.replace(tmp, self.csv_path)
        self._mtime = os.path.getmtime(self.csv_path)

    def set_corrected(self, idx, value: int):
        self.check_external_change()  # 変更前に検出（df を汚さない）
        self.df.at[idx, "Corrected"] = int(value)
        self.df.at[idx, "is_corrected"] = (
            self.df.at[idx, "Corrected"] != self.df.at[idx, "pred_num"]
        )
        self.save()

    # --- 参照系 ---
    def sheets(self):
        """[(出席番号, 表示名, ファイル名)] を出席番号順で返す。"""
        entries = []
        for fname in self.df["scan_filename"].unique():
            sub = self.df[self.df["scan_filename"] == fname]

            def digit(i):
                row = sub[(sub["Question_Number"] == 0) & (sub["Image_Index"] == i)]
                if row.empty:
                    return 0
                v = int(row.iloc[0]["Corrected"])
                return 0 if v == 10 else v

            no = digit(0) * 10 + digit(1)
            entries.append((no, f"{no:02d}_{fname}", fname))
        entries.sort(key=lambda t: (t[0], t[2]))
        return entries

    def rows_for_sheet(self, fname: str) -> pd.DataFrame:
        return self.df[self.df["scan_filename"] == fname]

    def label_groups(self):
        """{(mode, ラベル): [df index, ...]}。票割れ・低確信度が先頭に来る。"""
        groups = {("number", lab): [] for lab in NUMBER_LABELS}
        groups.update({("plusminus", lab): [] for lab in PM_LABELS})
        order = self.df.sort_values(
            by=["is_split", "conf"], ascending=[False, True]
        ).index
        for idx in order:
            m = self.df.at[idx, "mode"]
            lab = val_to_label(m, self.df.at[idx, "Corrected"])
            groups.setdefault((m, lab), []).append(idx)
        return groups

    # --- 画像 ---
    def thumb(self, idx, size: int):
        img_id = int(self.df.at[idx, "ID"])
        key = (img_id, size)
        if key in self._thumb_cache:
            return self._thumb_cache[key]
        path = os.path.join(self.raw_img_dir, f"{img_id}.jpg")
        try:
            with PILImage.open(path) as im:
                im = im.convert("RGB")
                im.thumbnail((size, size), PILImage.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(im)
        except Exception:
            photo = self._placeholder(size)
        self._thumb_cache[key] = photo
        return photo

    def _placeholder(self, size: int):
        if size not in self._placeholders:
            self._placeholders[size] = ImageTk.PhotoImage(
                PILImage.new("RGB", (size, size), "#c0c0c0")
            )
        return self._placeholders[size]

    def crop_image(self, idx, target: int = 300):
        """拡大表示用。raw 画像を長辺 target px へ拡大して返す（None = 画像なし）。"""
        img_id = int(self.df.at[idx, "ID"])
        path = os.path.join(self.raw_img_dir, f"{img_id}.jpg")
        try:
            with PILImage.open(path) as im:
                im = im.convert("RGB")
                f = target / max(im.size)
                im = im.resize(
                    (max(1, int(im.width * f)), max(1, int(im.height * f))),
                    PILImage.Resampling.LANCZOS,
                )
                return ImageTk.PhotoImage(im)
        except Exception:
            return None

    def resolve_scan_image(self, fname: str):
        for d in self.scan_dirs:
            path = os.path.join(d, fname)
            if os.path.exists(path):
                return path
        return None

    def clear_image_cache(self):
        self._thumb_cache.clear()
        self._placeholders.clear()


# --- ラベル別グリッド --------------------------------------------------------
class LabelGridView(ttk.Frame):
    """予測ラベルごとにサムネイルを並べ、クリック → メニューで修正するビュー。

    多数枚でも軽いよう、ウィジェットではなく単一 Canvas に create_image で
    描画し、after() で 60 件ずつ逐次構築する。修正してもその場ではグループを
    組み替えない（見失い防止）— 緑枠＋新ラベルのオーバーレイで示し、
    「再構築」で組み替える。
    """

    BATCH = 60

    def __init__(self, master, owner: "CorrectionWindow"):
        super().__init__(master)
        self.owner = owner
        self.store = owner.store
        self.thumb_size = int(52 * owner.ui_scale)
        self._cell_w = self.thumb_size + 16
        self._cell_h = self.thumb_size + 34
        base = tkfont.nametofont("TkDefaultFont")
        self._bold_font = base.copy()
        self._bold_font.configure(weight="bold")
        size = base.cget("size")
        sign = 1 if size >= 0 else -1
        self._caption_font = base.copy()
        self._caption_font.configure(size=sign * max(7, int(abs(size) * 0.75)))

        bar = ttk.Frame(self)
        bar.pack(fill="x", pady=(0, 4))
        ttk.Button(
            bar, text="再構築（修正をグループへ反映）", command=self.rebuild
        ).pack(side="left")
        self.info = ttk.Label(bar, text="", anchor="e")
        self.info.pack(side="right")

        wrap = ttk.Frame(self)
        wrap.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(wrap, background="#fafafa", highlightthickness=0)
        sb = ttk.Scrollbar(wrap, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<Configure>", self._on_resize)

        self._item_to_idx = {}
        self._cell_items = {}
        self._pending = []
        self._pos = 0
        self._cursor = None
        self._build_job = None
        self._resize_job = None
        self._cols = None

    # --- 構築 ---
    def rebuild(self):
        if self._build_job:
            self.after_cancel(self._build_job)
            self._build_job = None
        self.canvas.delete("all")
        self._item_to_idx.clear()
        self._cell_items.clear()
        width = self.canvas.winfo_width()
        if width < 60:  # まだレイアウトされていない
            self._build_job = self.after(100, self.rebuild)
            return
        self._cols = max(1, (width - 12) // self._cell_w)

        groups = self.store.label_groups()
        df = self.store.df
        tasks = []
        for sec, mode, labs in (("数字", "number", NUMBER_LABELS),
                                ("符号", "plusminus", PM_LABELS)):
            for lab in labs:
                idxs = groups.get((mode, lab), [])
                nsplit = sum(1 for i in idxs if df.at[i, "is_split"])
                header = f"{sec}「{lab}」 — {len(idxs)} 枚"
                if nsplit:
                    header += f"（⚠ {nsplit}）"
                tasks.append(("header", header))
                tasks.extend(("cell", i) for i in idxs)
        self._pending = tasks
        self._pos = 0
        header_h = self._bold_font.metrics("linespace") + 10
        self._cursor = {"y": 8, "col": 0, "header_h": header_h}
        self.info.config(text=f"全 {len(df)} 枚")
        self._process_batch()

    def _process_batch(self):
        self._build_job = None
        c = self._cursor
        n = 0
        while self._pos < len(self._pending) and n < self.BATCH:
            kind, payload = self._pending[self._pos]
            self._pos += 1
            n += 1
            if kind == "header":
                if c["col"]:
                    c["y"] += self._cell_h
                    c["col"] = 0
                c["y"] += 6
                self.canvas.create_text(
                    8, c["y"], anchor="nw", text=payload, font=self._bold_font
                )
                c["y"] += c["header_h"]
            else:
                self._create_cell(payload, c)
        y_end = c["y"] + (self._cell_h if c["col"] else 0) + 20
        self.canvas.configure(scrollregion=(0, 0, self.canvas.winfo_width(), y_end))
        if self._pos < len(self._pending):
            self._build_job = self.after(1, self._process_batch)

    def _create_cell(self, idx, c):
        df = self.store.df
        x = 8 + c["col"] * self._cell_w
        y = c["y"]
        box = self.thumb_size + 6
        rect = self.canvas.create_rectangle(
            x, y, x + box, y + box, outline="#bbbbbb", width=1, fill="#ffffff"
        )
        img = self.canvas.create_image(
            x + box / 2, y + box / 2, image=self.store.thumb(idx, self.thumb_size)
        )
        is_q0 = int(df.at[idx, "Question_Number"]) == 0
        caption = ("出 " if is_q0 else "") + f"{df.at[idx, 'conf']:.0f}%"
        cap = self.canvas.create_text(
            x + box / 2, y + box + 2, anchor="n", text=caption,
            font=self._caption_font,
            fill="#c62828" if df.at[idx, "is_split"] else "#777777",
        )
        for item in (rect, img, cap):
            self._item_to_idx[item] = idx
        self._cell_items[idx] = {"rect": rect, "x": x, "y": y, "overlay": None}
        self._mark_cell(idx)  # 修正済み・票割れの枠色を初期反映
        c["col"] += 1
        if c["col"] >= self._cols:
            c["col"] = 0
            c["y"] += self._cell_h

    # --- 表示更新 ---
    def _mark_cell(self, idx):
        info = self._cell_items.get(idx)
        if not info:
            return
        df = self.store.df
        if df.at[idx, "is_corrected"]:
            outline, width = "#2e8b57", 3
        elif df.at[idx, "is_split"]:
            outline, width = "#d9534f", 2
        else:
            outline, width = "#bbbbbb", 1
        self.canvas.itemconfigure(info["rect"], outline=outline, width=width)
        if df.at[idx, "is_corrected"]:
            lab = val_to_label(df.at[idx, "mode"], df.at[idx, "Corrected"])
            if info["overlay"] is None:
                info["overlay"] = self.canvas.create_text(
                    info["x"] + 4, info["y"] + 3, anchor="nw", text=lab,
                    fill="#1565c0", font=self._bold_font,
                )
                self._item_to_idx[info["overlay"]] = idx
            else:
                self.canvas.itemconfigure(info["overlay"], text=lab)
        elif info["overlay"] is not None:
            self._item_to_idx.pop(info["overlay"], None)
            self.canvas.delete(info["overlay"])
            info["overlay"] = None

    def refresh_marks(self):
        """（シート別ビューでの修正を）枠色・オーバーレイにだけ反映する。"""
        for idx in list(self._cell_items):
            self._mark_cell(idx)

    # --- イベント ---
    def _on_click(self, event):
        item = self.canvas.find_withtag("current")
        if not item:
            return
        idx = self._item_to_idx.get(item[0])
        if idx is None:
            return
        self.owner.post_label_menu(
            event.x_root, event.y_root, idx, on_done=lambda: self._mark_cell(idx)
        )

    def _on_resize(self, event):
        if self._cols is None:
            return
        new_cols = max(1, (event.width - 12) // self._cell_w)
        if new_cols != self._cols:
            if self._resize_job:
                self.after_cancel(self._resize_job)
            self._resize_job = self.after(250, self.rebuild)


# --- シート別ビュー ----------------------------------------------------------
class SheetView(ttk.Frame):
    """シートごとにスキャン全体画像＋回答行リストを表示するビュー。

    修正はラベルメニュー（クリック選択）で行う。
    """

    def __init__(self, master, owner: "CorrectionWindow"):
        super().__init__(master)
        self.owner = owner
        self.store = owner.store
        self.row_thumb = int(56 * owner.ui_scale)
        self.populated = False
        self.entries = []
        self.index = 0
        self._orig_img = None
        self._scan_photo = None
        self._scan_job = None

        bar = ttk.Frame(self)
        bar.pack(fill="x", pady=(0, 4))
        ttk.Button(bar, text="◀ 前へ", command=self.prev_sheet).pack(side="left")
        self.combo = ttk.Combobox(bar, state="readonly", width=40)
        self.combo.pack(side="left", padx=6)
        self.combo.bind("<<ComboboxSelected>>", self._on_combo)
        ttk.Button(bar, text="次へ ▶", command=self.next_sheet).pack(side="left")
        self.page_lbl = ttk.Label(bar, text="")
        self.page_lbl.pack(side="left", padx=10)

        paned = ttk.PanedWindow(self, orient="horizontal")
        paned.pack(fill="both", expand=True)
        self.left_frame = tk.Frame(paned, background="#808080")
        paned.add(self.left_frame, weight=3)
        self.scan_lbl = tk.Label(self.left_frame, background="#808080",
                                 foreground="#ffffff")
        self.scan_lbl.pack(fill="both", expand=True)
        self.left_frame.bind("<Configure>", self._on_left_resize)

        right = ttk.Frame(paned)
        paned.add(right, weight=2)
        self.rows_canvas = tk.Canvas(right, highlightthickness=0)
        sb = ttk.Scrollbar(right, orient="vertical", command=self.rows_canvas.yview)
        self.rows_canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.rows_canvas.pack(side="left", fill="both", expand=True)
        self.rows_frame = tk.Frame(self.rows_canvas)
        self._rows_win = self.rows_canvas.create_window(
            (0, 0), window=self.rows_frame, anchor="nw"
        )
        self.rows_frame.bind(
            "<Configure>",
            lambda e: self.rows_canvas.configure(
                scrollregion=self.rows_canvas.bbox("all")
            ),
        )
        self.rows_canvas.bind(
            "<Configure>",
            lambda e: self.rows_canvas.itemconfigure(self._rows_win, width=e.width),
        )

    # --- 構築・更新 ---
    def rebuild(self, select_fname: str | None = None):
        self.entries = self.store.sheets()
        self.combo.configure(values=[e[1] for e in self.entries])
        if not self.entries:
            self.populated = True
            self.combo.set("")
            self.page_lbl.config(text="0 / 0")
            for w in self.rows_frame.winfo_children():
                w.destroy()
            return
        idx = 0
        if select_fname is not None:
            for i, e in enumerate(self.entries):
                if e[2] == select_fname:
                    idx = i
                    break
        else:
            idx = min(self.index, len(self.entries) - 1)
        self.populated = True
        self.show_sheet(idx)

    def refresh(self):
        """（ラベル別ビューでの修正を）現在シートの表示に反映する。"""
        if not self.populated or not self.entries:
            return
        frac = self.rows_canvas.yview()[0]
        self.rebuild(select_fname=self.entries[self.index][2])
        self.rows_canvas.yview_moveto(frac)

    def show_sheet(self, i: int):
        self.index = i
        no, label, fname = self.entries[i]
        self.page_lbl.config(text=f"{i + 1} / {len(self.entries)}")
        self.combo.set(label)

        path = self.store.resolve_scan_image(fname)
        if path:
            try:
                with PILImage.open(path) as im:
                    self._orig_img = im.convert("RGB")
            except Exception:
                self._orig_img = None
        else:
            self._orig_img = None
        self._refresh_scan()

        for w in self.rows_frame.winfo_children():
            w.destroy()
        for idx, row in self.store.rows_for_sheet(fname).iterrows():
            self._build_row(idx, row)
        self.rows_canvas.yview_moveto(0)

    def _build_row(self, idx, row):
        split = bool(row["is_split"])
        corrected = bool(row["is_corrected"])
        bg = "#e8f5e9" if corrected else ("#ffe6e6" if split else "#ffffff")
        f = tk.Frame(self.rows_frame, bd=1, relief="solid", background=bg)
        f.pack(fill="x", padx=4, pady=2)

        photo = self.store.thumb(idx, self.row_thumb)
        img_lbl = tk.Label(f, image=photo, background=bg)
        img_lbl.image = photo
        img_lbl.pack(side="left", padx=4, pady=2)

        qn = int(row["Question_Number"])
        pred_lab = val_to_label(row["mode"], row["Predicted"])
        head = "出席番号" if qn == 0 else f"Q{qn}-{int(row['Answer_Number'])}"
        info = (f"ID:{int(row['ID'])}  {head}  [{int(row['Image_Index'])}]\n"
                f"{row['mode']}  Pred: {pred_lab}（{row['conf']:.0f}%）")
        tk.Label(f, text=info, justify="left", background=bg).pack(
            side="left", padx=4
        )

        cur_lab = val_to_label(row["mode"], row["Corrected"])
        btn = ttk.Button(f, text=cur_lab, width=6)
        btn.configure(
            command=lambda b=btn, i=idx: self.owner.post_label_menu(
                b.winfo_rootx(), b.winfo_rooty() + b.winfo_height(), i,
                on_done=self._after_correct,
            )
        )
        btn.pack(side="left", padx=8)
        if split:
            tk.Label(f, text="⚠", background=bg, foreground="#c62828").pack(
                side="left"
            )

    def _after_correct(self):
        # 出席番号の修正でソート順・表示名が変わり得るため、シート一覧から作り直す
        if not self.entries:
            return
        frac = self.rows_canvas.yview()[0]
        self.rebuild(select_fname=self.entries[self.index][2])
        self.rows_canvas.yview_moveto(frac)

    # --- スキャン画像 ---
    def _refresh_scan(self):
        if self._orig_img is None:
            fname = self.entries[self.index][2] if self.entries else ""
            self.scan_lbl.config(
                image="", text=f"スキャン画像が見つかりません\n{fname}"
            )
            self._scan_photo = None
            return
        w = self.left_frame.winfo_width()
        h = self.left_frame.winfo_height()
        if w < 10:
            w = 600
        if h < 10:
            h = 700
        im = self._orig_img.copy()
        im.thumbnail((w, h), PILImage.Resampling.LANCZOS)
        self._scan_photo = ImageTk.PhotoImage(im)
        self.scan_lbl.config(image=self._scan_photo, text="")

    def _on_left_resize(self, _event):
        if self._scan_job:
            self.after_cancel(self._scan_job)
        self._scan_job = self.after(150, self._refresh_scan)

    # --- ナビゲーション ---
    def _on_combo(self, _event=None):
        i = self.combo.current()
        if 0 <= i < len(self.entries):
            self.show_sheet(i)

    def prev_sheet(self, _event=None):
        if self.entries and self.index > 0:
            self.show_sheet(self.index - 1)

    def next_sheet(self, _event=None):
        if self.entries and self.index < len(self.entries) - 1:
            self.show_sheet(self.index + 1)


# --- メインウィンドウ --------------------------------------------------------
class CorrectionWindow(tk.Toplevel):
    """予測修正ウィンドウ。

    生成後に self.ok を確認すること（predictions.csv が無い・読めない場合は
    ダイアログを出して自壊し ok=False のままになる）。

    result_dir: predictions.csv と image/raw/ を含むフォルダ（採点処理の result_dir と同じ）。
    scan_dirs : シート別ビューでスキャン全体画像を探すフォルダの候補（先勝ち、複数可）。
    """

    def __init__(self, master, result_dir: str, scan_dirs=(), title: str = "予測修正",
                 ui_scale: float = 1.5, log=None, on_close=None):
        super().__init__(master)
        self.ok = False
        self.ui_scale = ui_scale
        self.log = log or (lambda s: None)
        self._close_cb = on_close
        self.withdraw()  # 読込失敗時にチラつかないよう一旦隠す

        self.store = PredictionStore(result_dir, scan_dirs)
        if not os.path.exists(self.store.csv_path):
            messagebox.showinfo(
                "予測結果なし",
                "predictions.csv が見つかりません。先に採点を実行してください。\n"
                f"{self.store.csv_path}",
                parent=master,
            )
            self.destroy()
            return
        try:
            self.store.load()
        except Exception as e:
            messagebox.showerror(
                "読込エラー", f"predictions.csv の読込に失敗しました:\n{e}",
                parent=master,
            )
            self.destroy()
            return

        self.ok = True
        self.title(title)
        self.geometry(f"{int(1100 * ui_scale)}x{int(680 * ui_scale)}")
        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.bind("<MouseWheel>", self._on_wheel)
        self.bind("<Left>", lambda e: self._nav_key(-1))
        self.bind("<Right>", lambda e: self._nav_key(1))
        self.deiconify()

    # --- UI ---
    def _build_ui(self):
        toolbar = ttk.Frame(self, padding=(8, 6))
        toolbar.pack(fill="x")
        ttk.Button(toolbar, text="再読込", command=self.reload).pack(side="left")
        self.status = ttk.Label(toolbar, text=self.store.csv_path, anchor="e")
        self.status.pack(side="right", fill="x", expand=True)

        ttk.Label(
            self,
            text="修正は自動保存されます。修正後はメイン画面で再度「採点」を実行すると反映されます。",
            foreground="#666666",
        ).pack(fill="x", padx=10)

        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True, padx=8, pady=8)
        self.grid_view = LabelGridView(self.nb, self)
        self.nb.add(self.grid_view, text="ラベル別")
        self.sheet_view = SheetView(self.nb, self)
        self.nb.add(self.sheet_view, text="シート別")
        self.nb.bind("<<NotebookTabChanged>>", self._on_tab_changed)
        self.grid_view.rebuild()

    def _on_tab_changed(self, _event=None):
        tab = self.nb.select()
        if tab == str(self.sheet_view):
            if not self.sheet_view.populated:
                self.sheet_view.rebuild()  # 初回は遅延構築
            else:
                self.sheet_view.refresh()
        else:
            self.grid_view.refresh_marks()

    # --- 修正の適用（両ビュー共通） ---
    def post_label_menu(self, x_root: int, y_root: int, idx, on_done=None):
        mode = self.store.df.at[idx, "mode"]
        cur = val_to_label(mode, self.store.df.at[idx, "Corrected"])
        menu = tk.Menu(self, tearoff=0)
        var = tk.StringVar(value=cur)
        for lab in labels_for(mode):
            menu.add_radiobutton(
                label=lab, variable=var, value=lab,
                command=lambda l=lab: self.apply_correction(idx, l, on_done),
            )
        menu.add_separator()
        menu.add_command(label="拡大表示", command=lambda: self.show_zoom(idx))
        menu.tk_popup(x_root, y_root)

    def apply_correction(self, idx, label: str, on_done=None) -> bool:
        mode = self.store.df.at[idx, "mode"]
        value = label_to_val(mode, label)
        if int(self.store.df.at[idx, "Corrected"]) == value:
            return True  # 現在値と同じ（メニューを閉じるためのクリック等）→ 書き込まない
        try:
            self.store.set_corrected(idx, value)
        except ExternalChangeError:
            if messagebox.askyesno(
                "外部変更",
                "predictions.csv が他の処理（採点など）で変更されています。\n"
                "再読込しますか？（今回の修正は破棄されます）",
                parent=self,
            ):
                self.reload()
            return False
        except Exception as e:
            messagebox.showerror("保存エラー", f"保存に失敗しました:\n{e}", parent=self)
            return False
        self.status.config(
            text=f"{self.store.csv_path}  保存済 {datetime.datetime.now():%H:%M:%S}"
        )
        if on_done:
            on_done()
        return True

    def show_zoom(self, idx):
        df = self.store.df
        top = tk.Toplevel(self)
        top.title(f"拡大表示 — ID {int(df.at[idx, 'ID'])}")
        photo = self.store.crop_image(idx, target=int(240 * self.ui_scale))
        if photo is None:
            ttk.Label(top, text="画像ファイルが見つかりません").pack(padx=20, pady=20)
        else:
            lbl = ttk.Label(top, image=photo)
            lbl.image = photo  # GC 防止
            lbl.pack(padx=10, pady=10)
        mode = df.at[idx, "mode"]
        info = (
            f"{mode}  Pred: {val_to_label(mode, df.at[idx, 'Predicted'])}"
            f"（{df.at[idx, 'conf']:.0f}%）  "
            f"現在値: {val_to_label(mode, df.at[idx, 'Corrected'])}"
        )
        ttk.Label(top, text=info).pack(padx=10, pady=(0, 10))
        top.bind("<Button-1>", lambda e: top.destroy())

    # --- ツールバー操作 ---
    def reload(self):
        try:
            self.store.load()
        except Exception as e:
            messagebox.showerror("読込エラー", f"再読込に失敗しました:\n{e}", parent=self)
            return
        self.grid_view.rebuild()
        if self.sheet_view.populated:
            self.sheet_view.rebuild()
        self.status.config(text=f"{self.store.csv_path}  再読込済")

    # --- イベント ---
    def _on_wheel(self, event):
        units = int(-event.delta / 120)
        if self.nb.select() == str(self.sheet_view):
            self.sheet_view.rows_canvas.yview_scroll(units, "units")
        else:
            self.grid_view.canvas.yview_scroll(units, "units")

    def _nav_key(self, step: int):
        if self.nb.select() != str(self.sheet_view):
            return
        if step < 0:
            self.sheet_view.prev_sheet()
        else:
            self.sheet_view.next_sheet()

    def _on_close(self):
        self.store.clear_image_cache()
        if self._close_cb:
            try:
                self._close_cb()
            except Exception:
                pass
        self.destroy()
