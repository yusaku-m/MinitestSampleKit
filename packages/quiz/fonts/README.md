# フォントについて

図中の日本語文字（応力・断面寸法などの図の注記）は `Meiryo` フォントで描画されます。

- Windows なら通常 `C:\Windows\Fonts\meiryo.ttc` が標準搭載されているため、**多くの場合は何もしなくても動きます**
  （`Figure.py` がシステムの Meiryo に自動フォールバックします）。
- Meiryo が無い環境（Linux/Mac 等）や、別のライセンスフリーな日本語フォントを使いたい場合は、
  このフォルダに `meiryo.ttc` という名前でフォントファイルを置いてください（`Figure.py` がまずここを探します）。
  - 例: IPAex ゴシック（`ipaexg.ttf`）を使う場合は `packages/quiz/Figure.py` の `_FONT_CANDIDATES` に
    パスを追加し、登録名を `'Meiryo'` のまま使う（各図形の `font_family='Meiryo'` 参照を変更不要にするため）。
- Microsoft 製フォント（Meiryo等）は再配布不可のため、このリポジトリにフォント実体は含めていません。
