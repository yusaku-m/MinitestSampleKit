"""ランダム問題生成 × 自動採点 サンプルGUI（Tkinter）。

科目・週を選んで「演習PDF生成 / 小テストPDF生成 / 採点」を実行できる、
grading_app.py の考え方を最小構成で再現したデモアプリ。

再テストタブでは、出席番号と受験回数を指定して個別シードの再テストPDFを生成・採点できる
（同じ学生の1回目・2回目で別の数値・条件の問題になることを確認できる）。

起動方法:
    pixi run python sample_gui.py
"""
from __future__ import annotations

import os
import queue
import sys
import threading
import tkinter as tk
from tkinter import messagebox, ttk

_REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

import packages.quiz.Runner as R


class _TeeQueue:
    """print() の内容をキュー経由で GUI ログへ流すためのラッパー。"""

    def __init__(self, q: "queue.Queue[str]"):
        self._q = q

    def __call__(self, msg: str) -> None:
        self._q.put(str(msg))


class SampleGradingApp:
    UI_SCALE = 1.3

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("ランダム問題生成 × 自動採点 サンプルGUI")
        self.log_queue: "queue.Queue[str]" = queue.Queue()
        self.courses: list[R.Course] = []
        self.busy = False

        self._build_widgets()
        self._reload_courses()
        self.root.after(100, self._drain_log_queue)

    # ------------------------------------------------------------------ #
    # UI構築
    # ------------------------------------------------------------------ #
    def _build_widgets(self):
        pad = 6
        top = ttk.Frame(self.root)
        top.pack(fill="x", padx=pad, pady=pad)

        ttk.Label(top, text="科目:").grid(row=0, column=0, sticky="w")
        self.course_var = tk.StringVar()
        self.course_combo = ttk.Combobox(top, textvariable=self.course_var, state="readonly", width=45)
        self.course_combo.grid(row=0, column=1, padx=pad)
        self.course_combo.bind("<<ComboboxSelected>>", lambda e: self._refresh_weeks())

        ttk.Label(top, text="週:").grid(row=0, column=2, sticky="w")
        self.week_var = tk.StringVar()
        self.week_combo = ttk.Combobox(top, textvariable=self.week_var, state="readonly", width=30)
        self.week_combo.grid(row=0, column=3, padx=pad)

        self.reload_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            top, text="共有モジュールを毎回再読込", variable=self.reload_var
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(pad, 0))

        nb = ttk.Notebook(self.root)
        nb.pack(fill="x", padx=pad, pady=pad)

        # --- 週次タブ ---
        weekly = ttk.Frame(nb)
        nb.add(weekly, text="週次小テスト")
        btns = ttk.Frame(weekly)
        btns.pack(fill="x", pady=pad)
        ttk.Button(btns, text="演習PDF生成", command=self._on_exercises).pack(side="left", padx=pad)
        ttk.Button(btns, text="小テストPDF生成", command=self._on_minitest).pack(side="left", padx=pad)
        ttk.Button(btns, text="採点", command=self._on_grade).pack(side="left", padx=pad)
        ttk.Button(btns, text="返却PDF生成", command=self._on_export).pack(side="left", padx=pad)

        # --- 再テストタブ ---
        retry = ttk.Frame(nb)
        nb.add(retry, text="個別再テスト")
        rtop = ttk.Frame(retry)
        rtop.pack(fill="x", pady=pad)
        ttk.Label(rtop, text="出席番号:").pack(side="left")
        self.student_var = tk.StringVar(value="1")
        ttk.Entry(rtop, textvariable=self.student_var, width=6).pack(side="left", padx=pad)
        ttk.Label(rtop, text="受験回数:").pack(side="left")
        self.attempt_var = tk.StringVar(value="1")
        ttk.Entry(rtop, textvariable=self.attempt_var, width=6).pack(side="left", padx=pad)
        ttk.Button(rtop, text="再テストPDF生成", command=self._on_retry_generate).pack(side="left", padx=pad)
        ttk.Button(rtop, text="再テスト採点", command=self._on_retry_grade).pack(side="left", padx=pad)

        # --- ログ ---
        log_frame = ttk.Frame(self.root)
        log_frame.pack(fill="both", expand=True, padx=pad, pady=pad)
        self.log_text = tk.Text(log_frame, height=20, wrap="word")
        self.log_text.pack(side="left", fill="both", expand=True)
        scroll = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        scroll.pack(side="right", fill="y")
        self.log_text.config(yscrollcommand=scroll.set)

    # ------------------------------------------------------------------ #
    # データ読み込み
    # ------------------------------------------------------------------ #
    def _reload_courses(self):
        self.courses = R.discover_configs()
        self.course_combo["values"] = [c.label for c in self.courses]
        if self.courses:
            self.course_combo.current(0)
            self._refresh_weeks()

    def _current_course(self) -> R.Course:
        idx = self.course_combo.current()
        return self.courses[idx]

    def _refresh_weeks(self):
        course = self._current_course()
        labels = [f"{R.weekstr_for(course, w)}　{w.weektitle}" for w in course.schedule]
        self.week_combo["values"] = labels
        if labels:
            self.week_combo.current(0)

    def _current_week(self) -> R.WeekEntry:
        course = self._current_course()
        idx = self.week_combo.current()
        return course.schedule[idx]

    # ------------------------------------------------------------------ #
    # ログ
    # ------------------------------------------------------------------ #
    def _log(self, msg: str) -> None:
        self.log_queue.put(str(msg))

    def _drain_log_queue(self):
        try:
            while True:
                msg = self.log_queue.get_nowait()
                self.log_text.insert("end", msg + "\n")
                self.log_text.see("end")
        except queue.Empty:
            pass
        self.root.after(100, self._drain_log_queue)

    # ------------------------------------------------------------------ #
    # 実行制御（バックグラウンドスレッド）
    # ------------------------------------------------------------------ #
    def _run_in_thread(self, fn, *args):
        if self.busy:
            messagebox.showinfo("実行中", "他の処理が完了するまでお待ちください。")
            return
        if self.reload_var.get():
            R.reload_first_party(log=self._log)

        def worker():
            self.busy = True
            try:
                fn(*args)
            except Exception as e:  # noqa: BLE001
                self._log(f"エラー: {e}")
            finally:
                self.busy = False

        threading.Thread(target=worker, daemon=True).start()

    # ------------------------------------------------------------------ #
    # 週次小テスト タブの処理
    # ------------------------------------------------------------------ #
    def _on_exercises(self):
        course, week = self._current_course(), self._current_week()
        self._run_in_thread(R.generate_exercises_pdf, course, week, None, self._log)

    def _on_minitest(self):
        course, week = self._current_course(), self._current_week()
        self._run_in_thread(R.generate_minitest_pdf, course, week, None, self._log)

    def _on_grade(self):
        course, week = self._current_course(), self._current_week()

        def task():
            sheets = R.grade_minitest(course, week, log=self._log)
            self._last_sheets = sheets
            if sheets:
                diag = R.aggregate_scores(sheets)
                self._log(R.format_diagnostics(diag))
            else:
                self._log(
                    "採点対象の画像がありません。scan フォルダに *.jpg を置いてから"
                    "再実行してください。"
                )

        self._run_in_thread(task)

    def _on_export(self):
        course, week = self._current_course(), self._current_week()

        def task():
            sheets = getattr(self, "_last_sheets", None)
            if not sheets:
                self._log("先に「採点」を実行してください。")
                return
            R.export_return_pdfs(course, week, sheets, log=self._log)

        self._run_in_thread(task)

    # ------------------------------------------------------------------ #
    # 個別再テスト タブの処理
    # ------------------------------------------------------------------ #
    def _on_retry_generate(self):
        course, week = self._current_course(), self._current_week()
        try:
            student = int(self.student_var.get())
            attempt = int(self.attempt_var.get())
        except ValueError:
            messagebox.showerror("入力エラー", "出席番号・受験回数は整数で入力してください。")
            return
        self._run_in_thread(R.generate_retry_pdf, course, week, student, attempt, None, self._log)

    def _on_retry_grade(self):
        course, week = self._current_course(), self._current_week()
        try:
            student = int(self.student_var.get())
            attempt = int(self.attempt_var.get())
        except ValueError:
            messagebox.showerror("入力エラー", "出席番号・受験回数は整数で入力してください。")
            return

        def task():
            sheets = R.grade_retry(course, week, student, attempt, log=self._log)
            if sheets:
                self._log(f"再テスト採点結果: {sheets[0].score} 点")
            else:
                self._log(
                    "採点対象の画像がありません。retry/{番号}_{回数}/scan に"
                    " *.jpg を置いてから再実行してください。"
                )

        self._run_in_thread(task)


def main():
    root = tk.Tk()
    app = SampleGradingApp(root)
    root.geometry("900x650")
    root.mainloop()


if __name__ == "__main__":
    main()
