"""採点システムの定型処理を集約した共有モジュール（配布サンプル版）。

元リポジトリの packages/quiz/Runner.py から、OneDrive/SharePoint 経由の配布・
Excel COM 成績簿転記など「学校固有の運用」に依存する部分を取り除いたもの。
科目定義（weekN.py）→ PDF生成→スキャン採点→集計、という共通エンジンの本体はそのまま。

設計方針（元と同じ）:
- 週番号・タイトル・実施日（=シード）は課程ごとの config.xlsx で管理する
  （前期 = schedule_1st シート、後期 = schedule_2nd シート）。
- 科目メタ（クラス・年度・科目名）はフォルダ構成から導出する（config には持たない）。
    {sample_kit}/{コースフォルダ}/{年フォルダ}/config.xlsx
    例: SampleCourse/2026/config.xlsx
- 出力先はすべてこのリポジトリ内 `output/` 以下のローカルフォルダ（OneDrive等の外部同期なし）。
- 重い処理（torch/OpenCV）の進捗は log コールバック（既定 print）に流す。

このファイルを自分の科目に合わせて改造する場合、変更が必要になりやすいのは:
- COURSE_SUBJECTS（コースフォルダ名 → 表示用科目名）
- target_path()（出力先フォルダの構成）
くらいで、PDF生成・採点・集計のロジックはそのまま使い回せることが多い。
"""

from __future__ import annotations

import datetime as dt
import glob
import importlib.util
import os
import sys
from dataclasses import dataclass, field
from typing import Callable, List, Optional

import pandas as pd

# リポジトリルート（packages/quiz/Runner.py → 2 階層上 = sample_kit/）
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 生成物の置き場所（OneDrive の代わり）。すべてこのフォルダ配下に閉じる。
OUTPUT_ROOT = os.path.join(REPO_ROOT, "output")

# コースフォルダ名 → 科目名（日本語表示用）。英語フォルダ名からは導けないためここで対応付ける。
# 新しい科目を追加するときはここに 1 行足すだけでよい。
COURSE_SUBJECTS = {
    "SampleCourse": "梁のたわみ計算（サンプル科目）",
}

LogFn = Callable[[str], None]


def folder_to_year(year_folder: str) -> str:
    """年フォルダ（西暦）を令和表記に変換する（2026 → "R8"）。数値でなければそのまま返す。"""
    try:
        return f"R{int(year_folder) - 2018}"
    except (TypeError, ValueError):
        return str(year_folder)


def term_prefix(division: str) -> str:
    """division（"1st"/"2nd"）から学期表記（前期/後期）を返す。"""
    return "前期" if str(division).lower().startswith("1") else "後期"


# このモジュール自身（呼び出し元が参照を保持している）は破棄しない
_RELOAD_KEEP = {__name__, "packages.quiz.Runner"}


def reload_first_party(log: LogFn = None) -> int:
    """自作モジュール（packages.*）を sys.modules から破棄して次回 import で再読込させる。

    GUI のボタン操作ごとに先頭で呼ぶことで、weekN.py だけでなく Beam.py / Sheet.py 等の
    共有モジュールの編集も「アプリ再起動」なしで反映できる。整合性を保つため packages.*
    を一括で破棄する（中途半端に一部だけ新しくすると isinstance/issubclass が壊れるため）。
    Runner 自身は呼び出し元が参照を保持しているため破棄対象から除く。

    戻り値は破棄したモジュール数。
    """
    purged = [
        name for name in list(sys.modules)
        if (name == "packages" or name.startswith("packages."))
        and name not in _RELOAD_KEEP
    ]
    for name in purged:
        del sys.modules[name]
    if log:
        log(f"共有モジュール再読込: {len(purged)} 件を破棄（次回 import で最新を反映）")
    return len(purged)


# --------------------------------------------------------------------------- #
# データモデル
# --------------------------------------------------------------------------- #
@dataclass
class WeekEntry:
    weeknum: int
    module: str
    weektitle: str
    date: Optional[dt.date]
    division: str = "1st"  # 前期=1st / 後期=2nd（どの schedule シート由来か）
    append_pdf: str = ""   # 末尾添付 PDF のファイル名（空なら添付なし）

    @property
    def has_seed(self) -> bool:
        return self.date is not None

    @property
    def term(self) -> str:
        return term_prefix(self.division)


@dataclass
class Course:
    Class: str
    Year: str
    SubjectName: str
    config_path: str
    course_dir: str  # config.xlsx が置かれている絶対パス（例 …/2026）
    schedule: List[WeekEntry] = field(default_factory=list)

    @property
    def label(self) -> str:
        """GUI 科目ドロップダウン用の表示名。"""
        return f"{self.Class} {self.SubjectName} ({self.Year})"

    def week(self, weeknum: int, division: str = "1st") -> WeekEntry:
        for w in self.schedule:
            if w.weeknum == weeknum and w.division == division:
                return w
        raise KeyError(
            f"week {weeknum}（{division}）が config に存在しません: {self.config_path}"
        )


# --------------------------------------------------------------------------- #
# config 読み込み
# --------------------------------------------------------------------------- #
def _meta_from_path(config_path: str):
    """config.xlsx のパスから (Class, Year, SubjectName, course_dir) を導出する。"""
    course_dir = os.path.dirname(config_path)        # …/SampleCourse/2026
    year_folder = os.path.basename(course_dir)       # 2026
    course_folder = os.path.basename(os.path.dirname(course_dir))  # SampleCourse
    Class = course_folder.split("_")[0]
    Year = folder_to_year(year_folder)
    SubjectName = COURSE_SUBJECTS.get(course_folder, course_folder)
    return Class, Year, SubjectName, course_dir


def _division_of_sheet(sheet_name: str) -> Optional[str]:
    """シート名から division を判定。schedule 系でなければ None。"""
    name = sheet_name.strip().lower()
    if name in ("schedule", "schedule_1st", "1st"):
        return "1st"
    if name in ("schedule_2nd", "2nd"):
        return "2nd"
    if name.startswith("schedule_"):
        return name.split("_", 1)[1]
    return None


def load_course_config(config_path: str) -> Course:
    """config.xlsx（schedule_1st / schedule_2nd シート）を読んで Course を返す。"""
    config_path = os.path.abspath(config_path)
    Class, Year, SubjectName, course_dir = _meta_from_path(config_path)

    sheets = pd.read_excel(config_path, sheet_name=None)  # 全シート
    schedule: List[WeekEntry] = []
    for sheet_name, df in sheets.items():
        division = _division_of_sheet(sheet_name)
        if division is None or df.empty:
            continue
        for _, row in df.iterrows():
            if pd.isna(row.get("weeknum")):
                continue
            d = row.get("date")
            if pd.isna(d):
                date = None
            elif isinstance(d, dt.datetime):
                date = d.date()
            elif isinstance(d, dt.date):
                date = d
            else:
                date = pd.to_datetime(d).date()
            append_pdf = "" if pd.isna(row.get("append_pdf")) else str(row["append_pdf"])
            schedule.append(
                WeekEntry(
                    weeknum=int(row["weeknum"]),
                    module=str(row["module"]),
                    weektitle=str(row["weektitle"]),
                    date=date,
                    division=division,
                    append_pdf=append_pdf,
                )
            )
    # 前期→後期、各内で週番号順
    schedule.sort(key=lambda w: (0 if w.division == "1st" else 1, w.weeknum))

    return Course(
        Class=Class,
        Year=Year,
        SubjectName=SubjectName,
        config_path=config_path,
        course_dir=course_dir,
        schedule=schedule,
    )


def discover_configs(repo_root: str = REPO_ROOT) -> List[Course]:
    """sample_kit 内の */20*/config.xlsx を検出し Course のリストを返す。"""
    paths = glob.glob(os.path.join(repo_root, "*", "20*", "config.xlsx"))
    courses = []
    for p in sorted(paths):
        if os.path.basename(p).startswith("~$"):  # Excel のロックファイルを無視
            continue
        try:
            courses.append(load_course_config(p))
        except Exception as e:  # 壊れた config は飛ばして他を表示
            print(f"[Runner] config 読み込み失敗: {p}: {e}")
    return courses


# --------------------------------------------------------------------------- #
# パス・シード・週文字列
# --------------------------------------------------------------------------- #
def target_path(course: Course, root: Optional[str] = None) -> str:
    """講義成果物の出力先 output/{Class}_{SubjectName}/{Year} を返す（ローカル固定）。

    元実装は OneDrive の同期フォルダを機種ごとに探索していたが、配布サンプルでは
    「学校のクラウド同期に依存しないローカルフォルダ」に単純化している。実運用に
    合わせて置き換える場合は、この関数だけを書き換えればよい。
    """
    if root is None:
        root = OUTPUT_ROOT
    path = os.path.join(root, f"{course.Class}_{course.SubjectName}", course.Year)
    os.makedirs(path, exist_ok=True)
    return path


def minitest_dir(tpath: str, course: Course, week: WeekEntry) -> str:
    """その週の小テスト作業ディレクトリ …/minitest/{division}/weekNN を返す。"""
    return os.path.join(
        tpath, "minitest", week.division, f"week{week.weeknum:02d}"
    )


def ensure_scan_dir(tpath: str, course: Course, week: WeekEntry) -> str:
    """weekNN/scan を作成して scan ディレクトリのパスを返す。"""
    scan = os.path.join(minitest_dir(tpath, course, week), "scan")
    os.makedirs(scan, exist_ok=True)
    return scan


def seed_for(week: WeekEntry) -> int:
    """実施日（date）から YYYYMMDD のシード整数を導出する。"""
    if week.date is None:
        raise ValueError(
            f"{week.term}{week.weeknum}週 の date が未設定です。config.xlsx を確認してください。"
        )
    return int(week.date.strftime("%Y%m%d"))


def retry_dir_for(
    tpath: str, course: Course, week: WeekEntry, student_number: int, attempt: int = 1,
) -> str:
    """個別再テストの作業ディレクトリ …/retry/{番号}_{回数} を返す（scan/result の親）。"""
    return os.path.join(
        minitest_dir(tpath, course, week), "retry", f"{student_number:02d}_{attempt:02d}"
    )


def retry_batch_result_dir_for(tpath: str, course: Course, week: WeekEntry) -> str:
    """QR一括採点の結果ディレクトリ …/retry_batch_result を返す（週ごと、scan は共有）。"""
    return os.path.join(minitest_dir(tpath, course, week), "retry_batch_result")


def retry_seed_for(student_number: int, attempt: int = 1) -> int:
    """再テスト用のシード。出席番号と受験回数から個人ごとに一意のシードを作る。

    同じ問題が学生間で使い回されないよう「出席番号2桁 + 受験回数2桁」を連結する
    （例: 出席番号14番の1回目 → 1401）。日付ベースの seed_for と衝突しない値域。
    """
    return int(f"{student_number:02d}{attempt:02d}")


def _retry_metadata(course: Course, week: WeekEntry, student_number: int, seed: int, page_count: int = 1) -> dict:
    """再テストPDFのQRに埋め込む/採点時に読み取ったQRから再構築するメタデータ。

    Sheet._draw_qr / Sheet.read_qr は "class:s:w:d:seed:p" の6フィールド固定形式を前提とする
    （元リポジトリ Grading と同じ dict キー契約をそのまま利用）。元リポジトリの "d" は再/追の
    区分だが、本サンプルには再テストしかないため学期（前期=0/後期=1）に読み替えて使う。
    """
    return {
        "class": course.Class,
        "s": student_number,
        "w": week.weeknum,
        "d": 0 if week.division == "1st" else 1,
        "seed": seed,
        "p": page_count,
    }


def weekstr_for(course: Course, week: WeekEntry) -> str:
    return f"{week.term}{week.weeknum}週"


def import_week_module(course: Course, week: WeekEntry):
    """課程ディレクトリ配下の weekN.py を動的 import する。

    複数週・複数課程・前後期で同名クラス（Question1 等）が衝突しないよう、
    sys.modules には課程・学期固有の一意名で登録する。呼び出しのたびに weekN.py を
    再実行するので（モジュールをキャッシュしない）、GUI で編集後すぐ反映される。
    """
    if REPO_ROOT not in sys.path:
        sys.path.insert(0, REPO_ROOT)  # weekN.py 内の `import packages.*` を解決
    module_dir = os.path.join(course.course_dir, week.division)
    file_path = os.path.join(module_dir, f"{week.module}.py")
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"問題定義ファイルが見つかりません: {file_path}")

    unique_name = f"_runner_{course.Class}_{course.Year}_{week.division}_{week.module}"
    spec = importlib.util.spec_from_file_location(unique_name, file_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[unique_name] = mod
    spec.loader.exec_module(mod)
    _apply_week_corrections(mod, module_dir, week.module)
    return mod


def _apply_week_corrections(mod, module_dir: str, module_name: str) -> None:
    """{module}_corrections.py があれば apply(mod) を呼び出し、読み込んだモジュールに当てる。

    印刷済み小テストの問題文ミスなど、weekN.py 本体の一般ロジックを汚さずに特定シード
    限定で補正したいときの差し込み口（本サンプルでは使用例なし。使い方は
    仕様書.md / 元リポジトリの packages/CLAUDE.md を参照）。
    """
    corr_path = os.path.join(module_dir, f"{module_name}_corrections.py")
    if not os.path.exists(corr_path):
        return
    unique_name = f"_runner_corr_{module_name}_{id(mod)}"
    spec = importlib.util.spec_from_file_location(unique_name, corr_path)
    corr_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(corr_mod)
    if hasattr(corr_mod, "apply"):
        corr_mod.apply(mod)


# --------------------------------------------------------------------------- #
# PDF 生成
# --------------------------------------------------------------------------- #
def _sheet_cls():
    from packages.quiz.Sheet import Sheet
    return Sheet


def generate_exercises_pdf(
    course: Course, week: WeekEntry, tpath: Optional[str] = None, log: LogFn = print
) -> str:
    """演習問題 PDF（マーカー・解答欄なし。模範解答つき）を生成し、出力パスを返す。"""
    if tpath is None:
        tpath = target_path(course)
    Sheet = _sheet_cls()
    wmod = import_week_module(course, week)
    questions = wmod.Exercises()
    title = f"{course.SubjectName}　{weekstr_for(course, week)}　{week.weektitle} 演習問題"
    out = os.path.join(tpath, f"{week.weeknum:02d}演習_{week.weektitle}")
    log(f"演習生成: {title}")
    sh = Sheet(title, questions)
    sh.export_pdf(out, marker=False, answerbox=False, namebox=False)
    log(f"  → {out}.pdf")
    return out + ".pdf"


def generate_minitest_pdf(
    course: Course, week: WeekEntry, tpath: Optional[str] = None, log: LogFn = print
) -> str:
    """小テスト PDF（マーカー・解答欄あり、シードは実施日由来）を生成する。

    同じ week でも config.xlsx の date を変えれば、印刷するたびに別問題になる
    （実施日をシードにしているため）。
    """
    if tpath is None:
        tpath = target_path(course)
    Sheet = _sheet_cls()
    seed = seed_for(week)
    wmod = import_week_module(course, week)
    questions = wmod.MiniTest(seed=seed)
    title = f"{course.SubjectName}　{weekstr_for(course, week)}　{week.weektitle} 小テスト"
    out = os.path.join(tpath, f"{week.weeknum:02d}小テスト_{week.weektitle}")

    log(f"小テスト生成: {title}  (seed={seed})")
    scan_dir = ensure_scan_dir(tpath, course, week)
    log(f"  scan フォルダ作成: {scan_dir}")
    sh = Sheet(title, questions)
    sh.export_pdf(out)
    log(f"  → {out}.pdf")
    return out + ".pdf"


def generate_retry_pdf(
    course: Course, week: WeekEntry, student_number: int, attempt: int = 1,
    tpath: Optional[str] = None, log: LogFn = print,
) -> str:
    """特定の学生 1 名向けの再テスト PDF を生成する（個別シード）。

    小テストと同じ問題定義（weekN.py）を使うが、シードを実施日ではなく
    「出席番号×受験回数」にすることで、本人が一度見た問題とは別の数値・条件の
    問題を毎回作れる（再テストのたびに構造は同じでも本質的に別問題になる）。

    氏名欄に出席番号を事前印字し、QRコード（出席番号・週・seed・ページ数）を埋め込む。
    採点時は grade_retry_batch がこのQRを読み取るだけで学生・週・受験回を自動判定できる
    ため、スキャンをあらかじめ学生ごとに仕分けておく必要がない。
    """
    if tpath is None:
        tpath = target_path(course)
    Sheet = _sheet_cls()
    seed = retry_seed_for(student_number, attempt)
    wmod = import_week_module(course, week)
    questions = wmod.MiniTest(seed=seed)
    # 科目名（COURSE_SUBJECTS）は長くなりがちで、氏名欄横のQR・出席番号欄と
    # タイトル文字列が重なる（Sheet はタイトルを折り返さず1行で描画するため）。
    # 再テストは対象科目が自明なので科目名は省き、週・回のみで短く保つ。
    title = f"{weekstr_for(course, week)}　{week.weektitle}　再テスト（{attempt}回目）"
    retry_dir = retry_dir_for(tpath, course, week, student_number, attempt)
    os.makedirs(os.path.join(retry_dir, "scan"), exist_ok=True)
    out = os.path.join(retry_dir, f"retry_{student_number:02d}_{attempt:02d}")

    metadata = _retry_metadata(course, week, student_number, seed)
    sh = Sheet(title, questions, student_number=student_number, metadata=metadata)

    # 1回目: 仮キャンバスで実ページ数を計測（explanation を除いた、学生が提出する
    # 解答ページのみのページ数。save しないためディスクには書き出さない）
    temp = sh.export_pdf(out, save=False, pdf_canvas=None, explanation=False)
    metadata["p"] = temp.getPageNumber() - 1  # showPage() 呼び出しごとに +1 されるため -1

    log(f"再テスト生成: {title}  (seed={seed}, QRページ数={metadata['p']})")
    sh.export_pdf(out)
    log(f"  → {out}.pdf")
    log(f"  scan フォルダ: {os.path.join(retry_dir, 'scan')}")
    return out + ".pdf"


# --------------------------------------------------------------------------- #
# 採点
# --------------------------------------------------------------------------- #
def load_ai_models(device: str, log: LogFn = print):
    """数字認識・±符号認識の CNN を packages/models からロードする。

    ここにある .pth は実際に手書き解答で学習した本物の重み（デモ用に一部を抜粋）。
    複数モデルをアンサンブル（多数決）することで単一モデルより誤読を減らしている。
    """
    import torch
    from packages.AI import NumberNeuralNetwork, PlusMinusNeuralNetwork

    models_dir = os.path.join(REPO_ROOT, "packages", "models")

    number_nets = []
    for path in glob.glob(os.path.join(models_dir, "NumberModel*")):
        net = NumberNeuralNetwork().to(device)
        net.load_state_dict(torch.load(path, map_location=torch.device("cpu")))
        number_nets.append(net)

    plus_minus_nets = []
    for path in glob.glob(os.path.join(models_dir, "MarkModel*")):
        net = PlusMinusNeuralNetwork().to(device)
        net.load_state_dict(torch.load(path, map_location=torch.device("cpu")))
        plus_minus_nets.append(net)

    log(f"AI モデル読込: number={len(number_nets)} 個, plusminus={len(plus_minus_nets)} 個")
    return plus_minus_nets, number_nets


def _already_predicted(csv_path: str, img_path: str) -> bool:
    """predictions.csv に当該画像の予測が既に存在するか（ファイル名で照合）。"""
    if not os.path.exists(csv_path):
        return False
    try:
        df = pd.read_csv(csv_path, encoding="utf-8-sig")
        target = os.path.basename(img_path).lower()
        names = df["Source_path"].apply(lambda x: os.path.basename(str(x)).lower())
        return target in names.values
    except Exception:
        return False


def _digit_montage(sh, cols: int = 12, cell: int = 32):
    """採点シートの全解答セルを AI 入力と同じ白黒画像にして格子状に並べた画像を返す。

    Sheet.image_preprocess（大津の二値化＋センタリング）で AI に渡るのと同一の
    [1,1,H,W] テンソルを作り、その白黒画像をモンタージュする。AI 入力の可視化用。
    """
    import numpy as np
    import cv2

    if not getattr(sh, "answer_imgs", None):
        return None
    imgs = []
    for page in sh.answer_imgs:
        for cellimg in page:
            try:
                t = sh.image_preprocess(cellimg)
                a = t[0][0].detach().cpu().numpy()
            except Exception:
                continue
            a = (a * 255).clip(0, 255).astype("uint8")
            imgs.append(cv2.resize(a, (cell, cell), interpolation=cv2.INTER_NEAREST))
    if not imgs:
        return None
    rows = (len(imgs) + cols - 1) // cols
    canvas = np.zeros((rows * cell, cols * cell), dtype="uint8")
    for k, im in enumerate(imgs):
        r, c = divmod(k, cols)
        canvas[r * cell:(r + 1) * cell, c * cell:(c + 1) * cell] = im
    return canvas


def _grade_scans(
    scan_dir: str, result_dir: str, title: str, questions, log: LogFn = print,
    monitor: bool = False, image_callback=None, metadata: Optional[dict] = None,
):
    """scan_dir 内の *.jpg を採点する共通処理（小テスト・再テストの両方から使う）。

    metadata を渡すと（再テストのみ）、生成時に印字したQRが解答欄の四角形として
    誤検出されないようマスク処理が有効になる（Sheet.get_answerimg 参照）。
    小テスト（QRなし）では None のままでよい。
    """
    import torch

    Sheet = _sheet_cls()
    os.makedirs(result_dir, exist_ok=True)
    csv_path = os.path.join(result_dir, "predictions.csv")

    files = sorted(glob.glob(os.path.join(scan_dir, "*.jpg")))
    log(f"採点対象 {len(files)} 件: {scan_dir}")
    if not files:
        return []

    device = "cuda" if torch.cuda.is_available() else "cpu"
    plus_minus_nets, number_nets = None, None  # 遅延ロード

    sheets = []
    for i, img in enumerate(files):
        log(f"[{i + 1}/{len(files)}] {os.path.basename(img)}")
        sh = Sheet(title, questions, monitor=monitor, metadata=metadata)
        sh.path = img
        sh.read()
        sh.rotation()
        sh.aliment()
        sh.get_answerimg(namebox=True)

        if _already_predicted(csv_path, img):
            log("  predictions.csv に既存 → AI スキップ")
            sh.get_format_answers([], [], "cpu", result_dir=result_dir)
            ai_ran = False
        else:
            if plus_minus_nets is None:
                log(f"  AI 推論（device={device}）")
                plus_minus_nets, number_nets = load_ai_models(device, log=log)
            sh.get_format_answers(plus_minus_nets, number_nets, device, result_dir=result_dir)
            ai_ran = True

        sh.scoring()
        log(f"  出席番号={sh.student_number} 得点={sh.score}")

        if image_callback is not None:
            try:
                caption = f"番号{sh.student_number}　{sh.score} 点　({i + 1}/{len(files)})"
                if sh.sheet:
                    image_callback("scored", caption, sh.sheet[0].img)
                if ai_ran:
                    montage = _digit_montage(sh)
                    if montage is not None:
                        image_callback("digits", f"AI入力 白黒 番号{sh.student_number}", montage)
            except Exception as e:  # プレビュー失敗で採点を止めない
                log(f"  （プレビュー生成スキップ: {e}）")

        sheets.append(sh)

    return sheets


def grade_minitest(
    course: Course,
    week: WeekEntry,
    tpath: Optional[str] = None,
    log: LogFn = print,
    monitor: bool = False,
    image_callback=None,
):
    """weekNN/scan/*.jpg を採点して、採点済み Sheet のリストを返す。

    predictions.csv に既出の画像は AI 推論をスキップし、CSV の Corrected 列を
    使って採点する（誤認識修正フローを維持）。AI モデルは必要なときのみロード。
    """
    if tpath is None:
        tpath = target_path(course)
    seed = seed_for(week)
    wmod = import_week_module(course, week)
    questions = wmod.MiniTest(seed=seed)

    wdir = minitest_dir(tpath, course, week)
    scan_dir = os.path.join(wdir, "scan")
    result_dir = os.path.join(wdir, "result")
    return _grade_scans(
        scan_dir, result_dir, "小テスト", questions, log=log,
        monitor=monitor, image_callback=image_callback,
    )


def grade_retry(
    course: Course, week: WeekEntry, student_number: int, attempt: int = 1,
    tpath: Optional[str] = None, log: LogFn = print,
    monitor: bool = False, image_callback=None,
):
    """特定学生の再テストを採点する（generate_retry_pdf と対になる関数）。

    generate_retry_pdf が印字したのと同じQRメタデータをここでも再構築して渡すことで、
    QR領域が解答欄として誤検出されるのを防ぐ（Sheet.get_answerimg のマスク処理）。
    """
    if tpath is None:
        tpath = target_path(course)
    seed = retry_seed_for(student_number, attempt)
    wmod = import_week_module(course, week)
    questions = wmod.MiniTest(seed=seed)
    metadata = _retry_metadata(course, week, student_number, seed)

    retry_dir = retry_dir_for(tpath, course, week, student_number, attempt)
    scan_dir = os.path.join(retry_dir, "scan")
    result_dir = os.path.join(retry_dir, "result")
    return _grade_scans(
        scan_dir, result_dir, "再テスト", questions, log=log,
        monitor=monitor, image_callback=image_callback, metadata=metadata,
    )


def retry_batch_scan_dir(tpath: str) -> str:
    """QR一括採点用の共有スキャン置き場 …/minitest/retry_scan を作成して返す。

    学生・週を問わず、スキャンした画像をここへまとめて置くだけでよい
    （QRコードから出席番号・週・受験回を自動判定するため、事前の仕分けが不要）。
    """
    scan = os.path.join(tpath, "minitest", "retry_scan")
    os.makedirs(scan, exist_ok=True)
    return scan


def grade_retry_batch(
    course: Course, tpath: Optional[str] = None, log: LogFn = print,
    monitor: bool = False, image_callback=None,
):
    """共有スキャンフォルダ（retry_batch_scan_dir）内の画像をQRコードで自動判定して採点する。

    generate_retry_pdf が埋め込んだQR（出席番号・週・seed・ページ数）を読み取ることで、
    学生ごとにスキャンを仕分けたり、GUIで出席番号・受験回数を指定したりする必要がなくなる
    （元リポジトリ Grading の grading_app.py: grade_retry() と同じ考え方。Excel成績簿転記・
    SharePoint配布など学校固有の運用は対象外）。

    1件の採点エラーで全体を止めず、失敗は failed に集めて返す（呼び出し側で必ず提示すること）。
    Returns: (sheets, failed)
    """
    import torch

    if tpath is None:
        tpath = target_path(course)
    Sheet = _sheet_cls()
    scan_dir = retry_batch_scan_dir(tpath)

    all_files = sorted(glob.glob(os.path.join(scan_dir, "*.jpg")))
    log(f"スキャンフォルダ: {scan_dir}")
    log(f"スキャンファイル: {len(all_files)} 件")
    failed: List[dict] = []
    if not all_files:
        log("スキャンファイルが見つかりません。")
        return [], failed

    # QR読取（回転補正後に失敗したら回転前の生画像でも試す）
    page_qr = []
    for f in all_files:
        sh_tmp = Sheet("dummy", [], monitor=False)
        sh_tmp.path = [f]
        sh_tmp.read()
        sh_tmp.rotation()
        qr = sh_tmp.read_qr()
        if not qr:
            sh_raw = Sheet("dummy", [], monitor=False)
            sh_raw.path = [f]
            sh_raw.read()
            qr = sh_raw.read_qr()
            if qr:
                log(f"QR OK（回転前リトライ）: {os.path.basename(f)}")
        if qr:
            log(f"QR OK: 出席番号{qr['s']:02d} 週{qr['w']} seed={qr['seed']} ページ数={qr['p']}")
        page_qr.append(qr)

    # ページグループ構築: QR は1枚目にしか埋め込まれないため、QR の p（総ページ数）に
    # 従ってスキャン順で後続の無QR画像を続きページとみなす。続きページのはずの画像に
    # QR が検出された場合は別答案の1枚目とみなし、続きページとしては扱わない。
    exam_groups = []
    used = set()
    for i, f in enumerate(all_files):
        qr = page_qr[i]
        if qr is None:
            continue
        page_count = qr.get("p", 1) or 1
        files = [f]
        used.add(i)
        for k in range(1, page_count):
            j = i + k
            if j >= len(all_files):
                log(f"⚠ 続きページ不足: {os.path.basename(f)} の{k+1}/{page_count}枚目が見つかりません")
                break
            if page_qr[j] is not None:
                log(f"⚠ 続きページのはずが QR を検出: {os.path.basename(all_files[j])} "
                    f"→ 別の答案の1枚目とみなし、続きページとしては扱いません")
                break
            files.append(all_files[j])
            used.add(j)
            log(f"  続きページ認識: {os.path.basename(all_files[j])} ({k+1}/{page_count}枚目)")
        exam_groups.append({**qr, "files": files})

    for i, f in enumerate(all_files):
        if i not in used:
            log(f"QR読取失敗（手動処理が必要）: {os.path.basename(f)}")

    # 重複スキャン対策: 同一 (出席番号, 週, seed) の QR が複数回検出された場合は
    # 同じ1枚目を誤って複数回スキャンしたとみなし、2件目以降は無視する
    seen_keys = set()
    deduped_groups = []
    for group in exam_groups:
        key = (group["s"], group["w"], group["seed"])
        if key in seen_keys:
            log(f"⚠ 重複スキャンを検出（無視）: 出席番号{group['s']:02d} 週{group['w']} "
                f"seed={group['seed']} — {os.path.basename(group['files'][0])}")
            continue
        seen_keys.add(key)
        deduped_groups.append(group)
    exam_groups = deduped_groups

    log(f"{len(exam_groups)}/{len(all_files)} 件の答案を認識"
        f"（QR読取成功 {sum(1 for q in page_qr if q is not None)} 枚、続きページ含め {len(used)} 枚を使用）")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    plus_minus_nets, number_nets = None, None  # 遅延ロード

    sheets = []
    total = len(exam_groups)
    for i, group in enumerate(sorted(exam_groups, key=lambda g: (g["s"], g["w"]))):
        student_number, weeknum, seed = group["s"], group["w"], group["seed"]
        division = "1st" if group["d"] == 0 else "2nd"
        img_files = group["files"]

        try:
            week = course.week(weeknum, division)
        except KeyError as e:
            log(f"⚠ 週が特定できません（要手動確認）: 出席番号{student_number:02d} 週{weeknum} — {e}")
            failed.append({
                "student_number": student_number, "weeknum": weeknum,
                "files": [os.path.basename(f) for f in img_files], "reason": str(e),
            })
            continue

        wmod = import_week_module(course, week)
        questions = wmod.MiniTest(seed=seed)
        title = f"{weekstr_for(course, week)}　{week.weektitle}　再テスト"
        metadata = _retry_metadata(course, week, student_number, seed, page_count=len(img_files))

        result_dir = retry_batch_result_dir_for(tpath, course, week)
        os.makedirs(result_dir, exist_ok=True)

        log(f"[{i + 1}/{total}] 採点: 出席番号{student_number:02d} 週{weeknum} seed={seed}")
        try:
            sh = Sheet(title, questions, monitor=monitor, metadata=metadata)
            sh.path = img_files
            sh.read()
            sh.rotation()
            sh.aliment()
            sh.get_answerimg(namebox=True)

            if plus_minus_nets is None:
                log(f"  AI 推論（device={device}）")
                plus_minus_nets, number_nets = load_ai_models(device, log=log)
            sh.get_format_answers(plus_minus_nets, number_nets, device, result_dir=result_dir)
            sh.scoring()
        except Exception as e:  # noqa: BLE001 — 他の受験者の採点を続行するため広く捕捉
            import traceback
            log(f"‼ 採点エラー（他の受験者の採点は続行しますが、この受験者は未処理のまま"
                f"残ります）: 出席番号{student_number:02d} 週{weeknum} — {e}")
            log(traceback.format_exc())
            failed.append({
                "student_number": student_number, "weeknum": weeknum,
                "files": [os.path.basename(f) for f in img_files], "reason": str(e),
            })
            continue

        # 出席番号欄はQRと同じ値を事前印字しており、氏名欄のOCRは手書き数字用に
        # 学習したモデルで印字文字を読むため誤読しうる（冗長チェックに過ぎない）。
        # 学生の特定はQR側を正とする。
        if sh.student_number != student_number:
            log(f"  ⚠ 出席番号欄のOCR読み取り（{sh.student_number}）がQR（{student_number}）と"
                f"不一致 → QRの値を採用します")
            sh.student_number = student_number

        log(f"  → 出席番号={sh.student_number} 得点={sh.score}")

        if image_callback is not None:
            try:
                caption = f"番号{student_number:02d} 週{weeknum} {sh.score}点 ({i + 1}/{total})"
                if sh.sheet:
                    image_callback("scored", caption, sh.sheet[0].img)
            except Exception as e:  # プレビュー失敗で採点を止めない
                log(f"  （プレビュー生成スキップ: {e}）")

        sheets.append(sh)

    if failed:
        log(f"‼‼‼ {len(failed)} 名が未処理のまま残っています（要手動対応） ‼‼‼")
        for f in failed:
            log(f"  - 出席番号{f['student_number']:02d} 週{f['weeknum']}: {f['reason']}"
                f"（{', '.join(f['files'])}）")

    return sheets, failed


def aggregate_scores(sheets) -> dict:
    """出席番号順にスコアを集計し、エラーチェック診断を返す。

    重複しても例外で止めず、診断結果（duplicates / missing / unknown）として
    返して GUI 側で可視化する。

    返り値:
        scores    : list[(student_number, score)]（番号順、欠番は score=-1）
        duplicates: list[int]（重複した出席番号）
        missing   : list[int]（提出のない番号 = 欠番）
        unknown   : int（出席番号を読み取れなかった枚数 = student_number==99）
        max_number: int（提出のあった最大の出席番号）
    """
    by_number: dict = {}
    duplicates: List[int] = []
    unknown = 0
    for sh in sheets:
        n = sh.student_number
        if n == 99 or n is None:
            unknown += 1
            continue
        if n in by_number:
            if n not in duplicates:
                duplicates.append(n)
        else:
            by_number[n] = sh.score

    max_number = max(by_number) if by_number else 0
    scores = []
    missing: List[int] = []
    for n in range(1, max_number + 1):
        if n in by_number:
            scores.append((n, by_number[n]))
        else:
            scores.append((n, -1))
            missing.append(n)

    return {
        "scores": scores,
        "duplicates": sorted(duplicates),
        "missing": missing,
        "unknown": unknown,
        "max_number": max_number,
    }


def format_diagnostics(diag: dict) -> str:
    """aggregate_scores の診断を人が読みやすい複数行テキストに整形する。"""
    lines = ["--- 採点エラーチェック ---"]
    if diag["duplicates"]:
        lines.append("⚠ 出席番号の重複: " + ", ".join(str(n) for n in diag["duplicates"]))
    else:
        lines.append("出席番号の重複: なし")
    if diag["missing"]:
        lines.append("欠番（未提出）: " + ", ".join(str(n) for n in diag["missing"]))
    else:
        lines.append("欠番: なし")
    if diag["unknown"]:
        lines.append(f"⚠ 出席番号を読み取れなかった枚数: {diag['unknown']}")
    lines.append("--- 得点一覧（番号: 点）---")
    lines.append(
        "  ".join(f"{n}:{s if s != -1 else '-'}" for n, s in diag["scores"])
    )
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# 返却 PDF 生成
# --------------------------------------------------------------------------- #
def export_return_pdfs(
    course: Course, week: WeekEntry, sheets, tpath: Optional[str] = None,
    log: LogFn = print,
) -> str:
    """共通の解説 PDF と各生徒の返却 PDF を result ディレクトリに生成する。

    戻り値は result_dir。各生徒 PDF は result_dir/NN.pdf という命名。
    （元実装にあった SharePoint 配布・成績簿転記は本サンプルには含めない。
    それらは学校固有の運用に強く依存するため、仕様書.md の付録を参照して
    各自の環境向けに実装するのが良い。）
    """
    if tpath is None:
        tpath = target_path(course)
    if not sheets:
        log("採点済みシートがありません。先に採点を実行してください。")
        return ""
    result_dir = os.path.join(minitest_dir(tpath, course, week), "result")
    os.makedirs(result_dir, exist_ok=True)

    seed = seed_for(week)
    explanation_pdf = os.path.join(result_dir, f"explanation_seed{seed}.pdf")
    if not os.path.exists(explanation_pdf):
        log(f"共通解説 PDF を生成: {os.path.basename(explanation_pdf)}")
        sheets[0].export_explanation_pdf(explanation_pdf[:-4])

    for sh in sheets:
        out = os.path.join(result_dir, f"{sh.student_number:02d}")
        log(f"返却 PDF: 番号{sh.student_number}（{sh.score} 点）")
        sh.export_return_pdf(out, explanation_pdf=explanation_pdf)

    return result_dir


def export_retry_return_pdfs(
    course: Course, sheets, tpath: Optional[str] = None, log: LogFn = print,
) -> List[str]:
    """再テストの返却 PDF を生成する（grade_retry / grade_retry_batch どちらの結果にも使える）。

    週・出席番号・受験回を引数で受け取らず、各 Sheet.metadata（QRメタデータ、
    _retry_metadata 参照）から復元する。そのため個別再テスト・QR一括採点のどちらで
    採点した sheets を渡しても、そのまま同じ関数で返却 PDF を生成できる。
    出力先は generate_retry_pdf/grade_retry と同じ retry/{番号}_{回数}/result/。

    戻り値は生成した result ディレクトリの一覧（重複を除く）。
    """
    if tpath is None:
        tpath = target_path(course)
    if not sheets:
        log("採点済みシートがありません。先に再テスト採点を実行してください。")
        return []

    result_dirs: List[str] = []
    explanation_cache: dict = {}

    for sh in sheets:
        meta = sh.metadata
        if not meta:
            log(f"⚠ 番号{sh.student_number} は再テストのメタデータがないためスキップ（通常の小テストでは使えません）")
            continue

        weeknum = meta["w"]
        division = "1st" if meta.get("d", 0) == 0 else "2nd"
        seed = meta["seed"]
        attempt = seed % 100

        result_dir = os.path.join(
            tpath, "minitest", division, f"week{weeknum:02d}",
            "retry", f"{sh.student_number:02d}_{attempt:02d}", "result",
        )
        os.makedirs(result_dir, exist_ok=True)

        explanation_pdf = explanation_cache.get(seed)
        if explanation_pdf is None:
            explanation_pdf = os.path.join(result_dir, f"explanation_seed{seed}.pdf")
            if not os.path.exists(explanation_pdf):
                log(f"共通解説 PDF を生成: {os.path.basename(explanation_pdf)}")
                sh.export_explanation_pdf(explanation_pdf[:-4])
            explanation_cache[seed] = explanation_pdf

        out = os.path.join(result_dir, f"{sh.student_number:02d}_{attempt:02d}")
        log(f"返却 PDF: 番号{sh.student_number} 週{weeknum} 受験{attempt}回目（{sh.score} 点）")
        sh.export_return_pdf(out, explanation_pdf=explanation_pdf)

        if result_dir not in result_dirs:
            result_dirs.append(result_dir)

    return result_dirs
