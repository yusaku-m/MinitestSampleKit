import svgwrite
import io
from svglib.svglib import svg2rlg
import numpy as np
from reportlab.graphics.renderPDF import draw

import sympy 
import matplotlib.pyplot as plt

# LaTeXの使用を有効にする (モジュールレベルで一度だけ設定)
plt.rcParams['text.usetex'] = True
plt.rcParams['font.family'] = 'serif'
plt.rcParams['text.latex.preamble'] = r'\usepackage{amsmath}'

# レンダリング済み数式のキャッシュ
_EQUATION_CACHE = {}
# バージョン確認用（ノートブック側で from packages.quiz.Equation import _EQ_VERSION; print(_EQ_VERSION) で確認）
_EQ_VERSION = "inline-math-2026-06-30"

class Equation():
    def __init__(self, text, fontsize = 13, color="black", name = "buf_figure", size=(162, 100)):
        """
        Svgwriteを敬称した数式クラス
        """        
        E_symbol = sympy.Symbol("E", real=True, positive=True) # 縦弾性係数
        r_symbol = sympy.Symbol('r', real=True, positive=True) # 半径
        R_symbol = sympy.Symbol('R', real=True, positive=True) # 半径
        N_symbol = sympy.Symbol('N', real=True, positive=True) # 回転数

        eprime_symbol = sympy.Symbol("varepsilon", real=True) # ひずみ
        DeltaL_symbol = sympy.Symbol(r"\Delta L", real=True, positive=True) # 長さの変化量
        DeltaT_symbol = sympy.Symbol("\Delta T", real=True) # 温度差
        DeltaT_1_symbol = sympy.Symbol(r"\Delta T_1", real=True) # 温度差
        DeltaT_2_symbol = sympy.Symbol(r"\Delta T_2", real=True) # 温度差

        dr_simbol = sympy.Symbol("dr", real=True, positive=True) # 半径の変化量

        symbol_map = {
            "E": E_symbol,
            "r": r_symbol,
            "R": R_symbol,
            "N": N_symbol,
            "varepsilon'": eprime_symbol,
            "DeltaL": DeltaL_symbol, # キーを"Delta L"に合わせる
            "DeltaT_1": DeltaT_1_symbol, # キーを"Delta T_1"に合わせる
            "DeltaT_2": DeltaT_2_symbol, # キーを"Delta T_2"に合わせる
            "DeltaT": DeltaT_symbol, # 一般的なDelta Tも追加
            "dr": dr_simbol,
        }

        if "sqrt" in text:
            #print(f"before equation: {text}")
            pass

        try:
            if text in symbol_map:
                # 直接シンボル名である場合は、対応するシンボルオブジェクトを割り当てる
                self._equation = symbol_map[text]
                self._equation = sympy.sympify(text, 
                                                locals=symbol_map,
                                                evaluate=False)

            else:
                # それ以外の場合は、通常通りsympy.sympifyを使って式を解析する
                self._equation = sympy.sympify(text, 
                                                locals=symbol_map,
                                                evaluate=False)
        except:
            # エラーが発生した場合、そのまま文字列として扱う
            self._equation = text

        if "Integral(" not in text:
            pass
            #self._equation = sympy.simplify(self._equation)
        #self._equation = sympy.factor(self._equation)
        
            
        self._text = text
        self._figure = None
        self._name = name
        self._height = None
        self._width = None
        self._x0 = None  # フォームBBox左下のx（インク左端）
        self._y0 = None  # フォームBBox左下のy（インク下端）
        self._baseline = None  # フォーム原点からベースラインまでの高さ[pt]
        self._fontsize = fontsize
        self._color = color
        self._dpi = None

    def __str__(self):
        """
        数式を文字列で返す
        """
        return self._text

    @property
    def equation(self):
        """
        数式を返す
        """
        return self._equation

    @property
    def figure(self):
        if self._figure is None:
            self.generate_figure()
        return self._figure

    @property
    def width(self):
        if self._width is None:
            self.generate_figure()
        return self._width - self._x0

    @property
    def height(self):
        if self._height is None:
            self.generate_figure()
        return self._height - self._y0
    
    @property
    def dpi(self):
        if self._dpi is None:
            self.generate_figure()
        return self._dpi

    @property
    def baseline(self):
        if self._baseline is None:
            self.generate_figure()
        return self._baseline

    def embed_to_pdf(self, pdf_canvas, x, y, valign="bottom", halign="left"):
        """
        pdf_canvasに図形を埋め込む
        """
        
        from pdfrw.toreportlab import makerl

        # フォーム未生成のまま呼ばれても落ちないように生成を保証する。
        # None を makerl に渡すと pdfrw 内部で AssertionError: None になり原因が追えない。
        if self._figure is None:
            self.generate_figure()
        if self._figure is None:
            raise RuntimeError(f"数式のPDFフォーム生成に失敗しました: {self._text!r}")

        # 4. reportlabのCanvasに登録し、フォーム名を取得
        form_name = makerl(pdf_canvas, self._figure)

        # 6. 描画基点 (tx, ty) を計算する。
        #    フォーム座標系でインク（数式）は左下 (self._x0, self._y0)〜
        #    右上 (self._width, self._height) を占める。doForm はフォーム原点を
        #    (tx, ty) に置くので、インクの基準点をアンカー (x, y) に一致させる。
        #    （以前は固定値 offset=(3,10) で近似していたため、内部余白とずれて
        #      数式が少し左下にずれていた。実BBoxから正確に求める。）
        x0, y0 = self._x0, self._y0
        x1, y1 = self._width, self._height

        # 既定: インク左下をアンカーに一致
        tx = x - x0
        ty = y - y0

        if halign == "center":
            tx = x - (x0 + x1) / 2
        if valign == "center":
            ty = y - (y0 + y1) / 2
        elif valign == "baseline":
            # 数式のベースラインをアンカー y に合わせる（インライン数式向け）
            ty = y - self._baseline

        # 7. (tx, ty) にフォーム原点を移動して描画
        pdf_canvas.saveState()
        pdf_canvas.translate(tx, ty)
        pdf_canvas.doForm(form_name)
        pdf_canvas.restoreState()
        
        # x,yの位置に小さい赤●を描画（デバッグ用）
        #pdf_canvas.setFillColorRGB(1, 0, 0)
        #pdf_canvas.circle(x, y, 2, fill=1)
        #pdf_canvas.setFillColorRGB(0, 0, 0)
        


    def generate_figure(self):
        
        if isinstance(self._equation, str):
            eq_latex = self._equation
        else:
            eq_latex = sympy.latex(self._equation)

        fontsize = self._fontsize

        if isinstance(self._equation, sympy.Symbol):
            latex_str = f"${eq_latex}$"  # 単純な変数の場合はそのまま（inline math）
        else:
            latex_str = fr"$\displaystyle {eq_latex}$"  # 複雑な式の場合は \displaystyle を付加（inline math）

        # キャッシュキーの作成 (LaTeX文字列, フォントサイズ, 色)
        cache_key = (latex_str, fontsize, self._color)
        if cache_key in _EQUATION_CACHE:
            cached_data = _EQUATION_CACHE[cache_key]
            self._figure = cached_data['figure']
            self._width = cached_data['width']
            self._height = cached_data['height']
            self._x0 = cached_data['x0']
            self._y0 = cached_data['y0']
            self._baseline = cached_data['baseline']
            self._dpi = cached_data['dpi']
            return

        # 試しにFigureとAxesを作成（ここではfigsizeは仮の値）
        # plt.subplots() は qtagg 等の対話バックエンドで Qt/GDI リソースを確保するため、
        # GUI アプリ内で大量生成するとリソース不足になる。Figure() + FigureCanvasAgg で
        # バックエンドに依存しない Agg レンダラを直接使うことで回避する。
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_agg import FigureCanvasAgg as _Agg

        fig = Figure(figsize=(5, 2))
        _canvas_measure = _Agg(fig)
        ax = fig.add_subplot(111)
        #print(f"eq: {latex_str}")
        text_obj = ax.text(0, 0.5, latex_str, fontsize=fontsize)
        ax.axis('off')

        # 一度描画処理を行い、テキストのbboxを取得
        _canvas_measure.draw()
        bbox = text_obj.get_window_extent(renderer=_canvas_measure.get_renderer())

        # bboxの幅と高さ（ピクセル単位）を取得
        bbox_width_px = bbox.width
        bbox_height_px = bbox.height

        # DPI（dots per inch）を取得
        dpi = fig.dpi
        self._dpi = dpi

        # bboxの幅と高さをインチ単位に変換し余白を加える。
        # inline mathでは bbox_height_px が極小（10-15px 程度）になるため、
        # 最小高さを設けて fig_dynamic のレイアウトが破綻しないようにする。
        width_inches = (bbox_width_px / dpi) + 0.2
        height_inches = max((bbox_height_px / dpi) + 0.3, 0.6)

        # 新しいfigsizeでFigureとAxesを再作成
        fig_dynamic = Figure(figsize=(width_inches, height_inches))
        ax_dynamic = fig_dynamic.add_subplot(111)

        txt_dynamic = ax_dynamic.text(-0.07, 0.5, latex_str, fontsize=fontsize, color=self._color)
        ax_dynamic.axis('off')
        fig_dynamic.tight_layout()
        
        # 保存用にバッファを使用
        import io
        from pdfrw import PdfReader
        from pdfrw.buildxobj import pagexobj

        # 実際に描画されたインク（数式の黒画素）の範囲を検出し、その範囲だけで
        # PDF を保存する。matplotlib の bbox_inches='tight' はテキストの論理box
        # （display math の上下余白や descent 領域）を含むため、可視インクとずれて
        # 数式が縦方向にずれる。ここでは alpha チャンネルからインク矩形を求めて
        # ぴったりトリミングし、フォーム BBox = 可視インク矩形 に一致させる。
        from matplotlib.transforms import Bbox
        from matplotlib.backends.backend_agg import FigureCanvasAgg
        # 背景を透明にしてからラスタライズしないと、Agg バッファの背景が不透明白で
        # 埋まり、インク検出が全面 true になってトリミングが効かない。
        fig_dynamic.patch.set_alpha(0.0)
        ax_dynamic.patch.set_alpha(0.0)
        # バックエンドに依存せず Agg でラスタライズしてインク範囲を取得する
        agg_canvas = FigureCanvasAgg(fig_dynamic)
        agg_canvas.draw()
        rgba = np.asarray(agg_canvas.buffer_rgba())
        fig_dpi = fig_dynamic.get_dpi()
        ink_ys, ink_xs = np.where(rgba[:, :, 3] > 2)

        pdf_buffer = io.BytesIO()
        self._baseline = 0.0
        if len(ink_xs) == 0:
            # インクが無い（空式）場合は従来どおり
            fig_dynamic.savefig(pdf_buffer, format='pdf', transparent=True,
                                bbox_inches='tight', pad_inches=0)
        else:
            img_h, img_w = rgba.shape[0], rgba.shape[1]
            # アンチエイリアス端 + ラスタ/ベクタ差異を吸収するため 4px のマージンを付ける
            MARGIN = 4
            r0 = max(ink_ys.min() - MARGIN, 0)
            r1 = min(ink_ys.max() + MARGIN, img_h - 1)
            c0 = max(ink_xs.min() - MARGIN, 0)
            c1 = min(ink_xs.max() + MARGIN, img_w - 1)
            # ピクセル範囲 → インチ範囲（matplotlib は左下原点）
            x0_in = c0 / fig_dpi
            x1_in = (c1 + 1) / fig_dpi
            y0_in = (img_h - 1 - r1) / fig_dpi
            y1_in = (img_h - r0) / fig_dpi
            ink_bbox = Bbox.from_extents(x0_in, y0_in, x1_in, y1_in)
            fig_dynamic.savefig(pdf_buffer, format='pdf', transparent=True,
                                bbox_inches=ink_bbox, pad_inches=0)

            # 数式のベースライン位置（フォーム原点=保存BBox左下からの高さ[pt]）を求める。
            # ベースラインを周囲テキストのベースラインに合わせて配置するために使う。
            try:
                renderer = agg_canvas.get_renderer()
                ext = txt_dynamic.get_window_extent(renderer=renderer)  # 表示px(下原点)
                _, _, desc_px = renderer.get_text_width_height_descent(
                    latex_str, txt_dynamic.get_fontproperties(), 'TeX')
                baseline_disp = ext.y0 + desc_px           # ベースラインの表示y(下原点)
                form_origin_disp = img_h - 1 - r1          # 保存BBox下端の表示y
                self._baseline = max((baseline_disp - form_origin_disp) / fig_dpi * 72.0, 0.0)
            except Exception:
                self._baseline = 0.0
        pdf_buffer.seek(0)

        # Figure() で作成しているため plt.close() は不要（plt のグローバル管理外）

        # 2. pdfrwでPDFバッファを読み込み、ページを取得
        try:
            pdf_reader = PdfReader(pdf_buffer)
            if not pdf_reader.pages:
                print(f"エラー: Matplotlibが空のPDFを生成しました。数式: {self._text!r}")
                return
            pdf_page = pdf_reader.pages[0]
        except Exception as e:
            print(f"pdfrwエラー: {e}。バッファサイズ: {len(pdf_buffer.getvalue())}。数式: {self._text!r}")
            return

        # 3. ページをForm XObjectに変換
        page_form = pagexobj(pdf_page)

        self._figure = page_form

        # 5. 描画するPDFの幅と高さをポイント単位で取得 (BBoxから)
        #    BBox = [x0, y0, x1, y1]。pad_inches=0 によりインク左下が (x0, y0)、
        #    右上が (x1, y1) になる。x0/y0 は embed_to_pdf の基準点に使う。
        bbox_coords = [float(b) for b in page_form.BBox]
        self._x0 = bbox_coords[0]
        self._y0 = bbox_coords[1]
        self._width = bbox_coords[2]
        self._height = bbox_coords[3]

        # キャッシュに保存
        _EQUATION_CACHE[cache_key] = {
            'figure': self._figure,
            'width': self._width,
            'height': self._height,
            'x0': self._x0,
            'y0': self._y0,
            'baseline': self._baseline,
            'dpi': self._dpi
        }


if __name__ == "__main__":
    
    eq = "P/A"
    test = Equation(eq)