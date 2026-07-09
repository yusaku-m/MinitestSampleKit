"""SampleCourse/2026/config.xlsx を生成するスクリプト。

config.xlsx は「週番号・使う問題定義モジュール・実施日（=シード）」を管理する
スケジュール表。日付を変えるだけで小テストの問題が変わる（シードが変わるため）。
このスクリプトは初期サンプルデータを作るためのものなので、実際に使うときは
Excel で直接 config.xlsx を編集して構わない（このスクリプトは再実行しなくてよい）。

実行方法（sample_kit ルートで）:
    pixi run python SampleCourse/make_config.py
"""
import os
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "2026", "config.xlsx")

schedule_1st = pd.DataFrame([
    {"weeknum": 1, "module": "week1", "weektitle": "片持ち梁+集中荷重",
     "date": "2026-04-13", "append_pdf": ""},
    {"weeknum": 2, "module": "week2", "weektitle": "単純支持梁+分布荷重",
     "date": "2026-04-20", "append_pdf": ""},
    {"weeknum": 3, "module": "week3", "weektitle": "張り出し梁+集中荷重",
     "date": "2026-04-27", "append_pdf": ""},
])

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with pd.ExcelWriter(OUT, engine="openpyxl") as writer:
    schedule_1st.to_excel(writer, sheet_name="schedule_1st", index=False)

print(f"生成しました: {OUT}")
