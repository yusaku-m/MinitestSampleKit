import os
import svgwrite
import io
from svglib.svglib import svg2rlg
from svglib.fonts import register_font as _svglib_register_font
import numpy as np
from reportlab.graphics.renderPDF import draw

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from .Equation import Equation

# 日本語フォントのパス解決
# 同梱した meiryo.ttc を最優先。無い環境向けにシステムの Meiryo へフォールバックする。
# これにより pixi 等どの環境でも図中の日本語が ■ にならない。
# 注意: Meiryo は Microsoft のプロプライエタリフォントで再配布は許諾されていない。
#       同梱ファイルを公開リポジトリにコミット／配布しないこと（ローカル利用のみ）。
_HERE = os.path.dirname(__file__)
_FONT_CANDIDATES = [
    os.path.join(_HERE, "fonts", "meiryo.ttc"),    # 同梱（クロスプラットフォーム）
    "c:/Windows/Fonts/meiryo.ttc",                 # Windows システム
]
FONT_PATH = next((p for p in _FONT_CANDIDATES if os.path.exists(p)), _FONT_CANDIDATES[0])

# ★★★ ここで一度だけフォントを登録する ★★★
# 'Meiryo' という名前で登録するため、SVG/Canvas 側の font_family 参照は変更不要。
#
# 注意: PDF中の日本語には 2 系統の描画経路があり、フォント解決機構が別々：
#   (a) ReportLab canvas 直接描画（Sheet.py の setFont('Meiryo', ...)）→ pdfmetrics の登録を参照
#   (b) svglib svg2rlg による図形描画（NameBox/Answer/CrossSection/Rod/Truss/Beam）
#       → svglib は独自の FontMap を持ち pdfmetrics を参照しない。別途登録が必須。
# さらに svglib は font-style:italic を別内部名(Meiryo-Italic)として解決するため、
# normal だけでなく italic 等も登録しないと斜体の日本語ラベルが化ける。
try:
    # (a) ReportLab canvas 用
    pdfmetrics.registerFont(TTFont('Meiryo', FONT_PATH))
    # (b) svglib svg2rlg 用（weight/style の全組合せを同一フォントに割り当て）
    for _w, _s in (('normal', 'normal'), ('normal', 'italic'),
                   ('bold', 'normal'), ('bold', 'italic')):
        _svglib_register_font('Meiryo', font_path=FONT_PATH, weight=_w, style=_s)
    print(f"日本語フォントを 'Meiryo' として登録しました: {FONT_PATH}")
except Exception as e:
    print(f"Meiryoフォントの登録に失敗しました: {e}")
    # フォントが見つからない、または破損している場合に備える

class Figure(svgwrite.Drawing):
    def __init__(self, name = "buf_figure", size=(162, 100), rotation_angle=0):
        """
        Svgwriteを敬称した図形クラス
        """
        super().__init__(name + '.svg', profile='full', size=size)

        self._rotation_angle = rotation_angle
        self._equations = []

    def line(self, start=(0, 0), end=(0, 0), **kwargs):
        start = (float(start[0]), float(start[1]))
        end = (float(end[0]), float(end[1]))
        if 'stroke_width' in kwargs: kwargs['stroke_width'] = float(kwargs['stroke_width'])
        return svgwrite.shapes.Line(start=start, end=end, **kwargs)

    def rect(self, insert=(0, 0), size=(1, 1), **kwargs):
        insert = (float(insert[0]), float(insert[1]))
        size = (float(size[0]), float(size[1]))
        if 'stroke_width' in kwargs: kwargs['stroke_width'] = float(kwargs['stroke_width'])
        return svgwrite.shapes.Rect(insert=insert, size=size, **kwargs)

    def circle(self, center=(0, 0), r=1, **kwargs):
        center = (float(center[0]), float(center[1]))
        r = float(r)
        if 'stroke_width' in kwargs: kwargs['stroke_width'] = float(kwargs['stroke_width'])
        return svgwrite.shapes.Circle(center=center, r=r, **kwargs)

    def polygon(self, points, **kwargs):
        points = [(float(p[0]), float(p[1])) for p in points]
        return svgwrite.shapes.Polygon(points=points, **kwargs)

    def polygon(self, points=[], **kwargs):
        points = [(float(p[0]), float(p[1])) for p in points]
        if 'stroke_width' in kwargs: kwargs['stroke_width'] = float(kwargs['stroke_width'])
        return svgwrite.shapes.Polygon(points=points, **kwargs)

    def text(self, text, insert=(0, 0), **kwargs):
        insert = (float(insert[0]), float(insert[1]))
        if 'font_size' in kwargs: kwargs['font_size'] = float(kwargs['font_size'])
        return svgwrite.text.Text(text=text, insert=insert, **kwargs)

    @property
    def width(self):
        return self.attribs.get('width')

    @property
    def height(self):
        return self.attribs.get('height')
    
    def embed_to_pdf(self, pdf_canvas, x, y, rotation_angle=0, 
                     rotation_center_x=None, rotation_center_y=None):
        """
        pdf_canvasに図形を埋め込む
        """
        #デバッグ用の枠線の描画
        #self.add(self.rect(insert=(0, 0), size=(self.width, self.height), fill="none", stroke="red", stroke_width=0.5))

        # 数式の背景を描画（インクBBoxの実寸に合わせ、embed_to_pdfと同じアンカー規則で配置）
        for eq, position, fill, valign, halign in self._equations:
            # eq.width/height へのアクセスが generate_figure() を兼ねる（fill="none"でも省略不可）
            w = eq.width
            h = eq.height
            bx = position[0] - w / 2 if halign == "center" else position[0]
            if valign == "center":
                by = position[1] - h / 2
            elif valign == "baseline":
                by = position[1] - h + eq.baseline
            else:  # bottom（アンカー=インク下端。SVGはy下向き）
                by = position[1] - h
            self.add(self.rect(insert=(bx, by), size=(w, h), fill=fill))



        svg_buffer = io.BytesIO()
        svg_buffer.write(self.tostring().encode('utf-8'))
        svg_buffer.seek(0)  # 読み取り位置をリセット
        svg = svg2rlg(svg_buffer)

        if rotation_angle == 0:
            rotation_angle = self._rotation_angle  # 回転角度を0-359度に正規化

        # Drawingオブジェクトの幅と高さを取得（回転中心の計算に使用）
        drawing_width = svg.width 
        drawing_height = svg.height

        # 1. 現在のキャンバスの状態を保存（重要：変換を元に戻すため）
        pdf_canvas.saveState()

        # 2. 回転中心を決定
        # 回転中心が指定されていない場合、埋め込み座標(x,y)を基準とした図形の中心を使用
        if rotation_center_x is None:
            rotation_center_x = x + drawing_width / 2
        if rotation_center_y is None:
            rotation_center_y = y + drawing_height / 2

        # 3. キャンバスの原点を回転中心に移動
        # これにより、以降の回転や描画は、この新しい原点を基準に行われる
        pdf_canvas.translate(rotation_center_x, rotation_center_y)

        # 4. キャンバスを回転
        pdf_canvas.rotate(rotation_angle)

        # 5. 図形を新しい（回転済みの）原点に対して描画
        # draw関数は、pdf_canvasの現在の原点に対して相対的な位置にsvgを配置する
        # 元々(x, y)に置くはずだった図形の左下隅が、回転中心を基準にどれだけオフセットされているかを計算
        # 新しい原点が(rotation_center_x, rotation_center_y)になっているので、
        # 図形を元々の左下隅の相対位置 (x - rotation_center_x, y - rotation_center_y) に描画する
        draw_x = round(x - rotation_center_x, 3)
        draw_y = round(y - rotation_center_y, 3)
        #print(draw_x, draw_y)

        draw(svg, pdf_canvas, draw_x, draw_y)

        # 6. キャンバスの状態を元に戻す（重要：以降の描画に影響を与えないため）
        pdf_canvas.restoreState()

        # 図形内の数式を描画
        for eq, position, fill, valign, halign in self._equations:
            #print(f"{eq}, x{x}, y{y}, rotation_center_x{rotation_center_x}, rotation_center_y{rotation_center_y}, position{position}")

            eq.embed_to_pdf(pdf_canvas, x + position[0], y + drawing_height - position[1], valign=valign, halign=halign)

    def draw_rectangle_from_center(self, insert_center, size, fill="none", stroke = "none", stroke_width=1):
        """
        中心座標から矩形を描画する
        insert_center: 矩形の中心座標 (x, y)
        size: 矩形のサイズ (width, height)
        color: 線の色
        fill_color: 塗りつぶしの色
        stroke_width: 線の太さ
        """
        insert = (float(insert_center[0] - size[0] / 2), float(insert_center[1] - size[1] / 2))
        size = (float(size[0]), float(size[1]))
        self.add(self.rect(insert=insert, size=size, stroke=stroke, fill=fill, stroke_width=stroke_width))

    def draw_triangle(self, top_point, size, color="black", fill_color=None, stroke_width=1):
        """
        三角形を描画する
        p1, p2, p3: 三角形の頂点座標 (x, y)
        color: 線の色
        fill_color: 塗りつぶしの色
        stroke_width: 線の太さ
        """

        p2 = (float(top_point[0] - size / 2), float(top_point[1] + size * np.sqrt(3) / 2))
        p3 = (float(top_point[0] + size / 2), float(top_point[1] + size * np.sqrt(3) / 2))
        top_point = (float(top_point[0]), float(top_point[1]))

        points = [top_point, p2, p3]
        #角は丸めた三角形を描画
        self.add(self.polygon(points, fill=fill_color, stroke=color, stroke_width=stroke_width, stroke_linejoin="round"))

    def draw_arrow(self, start, end, color="black", stroke_width=0.75, size=5, 
                   arrow_type="both"):
        
        """
        startからendへの矢印を描画する
        arrow_type: "both" or "start" or "end"
        """
        start = (float(start[0]), float(start[1]))
        end = (float(end[0]), float(end[1]))

        self.add(self.line(start, end, stroke=color, stroke_width=stroke_width, stroke_linecap="round"))
        #startからendへのベクトル
        vec = np.array(end) - np.array(start)
        #30度回転
        vec1 = np.array([vec[0]*np.cos(np.pi/6)-vec[1]*np.sin(np.pi/6), 
                         vec[0]*np.sin(np.pi/6)+vec[1]*np.cos(np.pi/6)])
        vec2 = np.array([vec[0]*np.cos(-np.pi/6)-vec[1]*np.sin(-np.pi/6), 
                         vec[0]*np.sin(-np.pi/6)+vec[1]*np.cos(-np.pi/6)])

        vec1 = vec1 / np.linalg.norm(vec1) * size
        vec2 = vec2 / np.linalg.norm(vec2) * size

        #vec1の長さがvecより長い場合は伸ばして描画
        if np.linalg.norm(vec1)*2 > np.linalg.norm(vec):
            self.add(self.line((float(start[0] - vec[0]/ np.linalg.norm(vec1) * size * 1.5), float(start[1] - vec[1]/ np.linalg.norm(vec1) * size * 1.5)), 
                               (float(end[0] + vec[0]/ np.linalg.norm(vec1) * size * 1.5), float(end[1] + vec[1]/ np.linalg.norm(vec1) * size * 1.5)), 
                               stroke=color, stroke_width=stroke_width, stroke_linecap="round"))
        if arrow_type == "start" or arrow_type == "both":
            self.add(self.line(start, (float(start[0] + vec1[0]), float(start[1] + vec1[1])), stroke=color, stroke_width=stroke_width, stroke_linecap="round"))
            self.add(self.line(start, (float(start[0] + vec2[0]), float(start[1] + vec2[1])), stroke=color, stroke_width=stroke_width, stroke_linecap="round"))
        if arrow_type == "end"  or arrow_type == "both":
            self.add(self.line(end, (float(end[0] - vec1[0]), float(end[1] - vec1[1])), stroke=color, stroke_width=stroke_width, stroke_linecap="round"))
            self.add(self.line(end, (float(end[0] - vec2[0]), float(end[1] - vec2[1])), stroke=color, stroke_width=stroke_width, stroke_linecap="round"))

    def draw_force(self, start, end, color="black", stroke_width=3, size=5):
        start = (float(start[0]), float(start[1]))
        end = (float(end[0]), float(end[1]))
        
        self.add(self.line(start, end, stroke=color, stroke_width=stroke_width, stroke_linecap="round"))
        #startからendへのベクトル
        vec = np.array(end) - np.array(start)
        #30度回転
        vec1 = np.array([vec[0]*np.cos(np.pi/6)-vec[1]*np.sin(np.pi/6), 
                         vec[0]*np.sin(np.pi/6)+vec[1]*np.cos(np.pi/6)])
        vec2 = np.array([vec[0]*np.cos(-np.pi/6)-vec[1]*np.sin(-np.pi/6), 
                         vec[0]*np.sin(-np.pi/6)+vec[1]*np.cos(-np.pi/6)])

        vec1 = vec1 / np.linalg.norm(vec1) * size
        vec2 = vec2 / np.linalg.norm(vec2) * size

        self.add(self.line(end, (float(end[0] - vec1[0]), float(end[1] - vec1[1])), stroke=color, stroke_width=stroke_width, stroke_linecap="round"))
        self.add(self.line(end, (float(end[0] - vec2[0]), float(end[1] - vec2[1])), stroke=color, stroke_width=stroke_width, stroke_linecap="round"))
    
    def draw_moment(self, center, radius, direction = "CCW", angle_range = (30, 330), color = "black", stroke_width = 3, aspect_ratio=1.0):
        """
        モーメントを描画する。
        angle_range: 角度で指定°
        aspect_ratio: x軸方向の半径倍率 (radius_x = radius * aspect_ratio, radius_y = radius)
        """
        R_y = float(radius)
        R_x = float(radius * aspect_ratio)
        center = (float(center[0]), float(center[1]))

        # 角度 0度は下(Y+)、90度は右(X+)
        # CCW: thetaが増える (0 -> 90 -> 180 ...)
        # CW: thetaが減る (0 -> -90 -> -180 ...)

        def get_point(angle_deg):
            rad = np.radians(angle_deg)
            return (center[0] + R_x * np.sin(rad), center[1] + R_y * np.cos(rad))

        # 角度差の計算 (常に反時計回りの角度差を基準とする)
        angle_diff = (angle_range[1] - angle_range[0]) % 360
        

        # セグメント数 (ユーザーの要望により分割数を増やす)
        num_segments = 4
        step_diff = angle_diff / num_segments

        # SVG sweep-flag: 1 for CW, 0 for CCW.
        sweep_flag = 1 if direction == "CW" else 0

        # 開始点の設定
        start_angle = angle_range[0] if direction == "CCW" else angle_range[1]
        target_angle = angle_range[1] if direction == "CCW" else angle_range[0]
        
        start_p = get_point(start_angle)
        path_data = 'M {x1} {y1} '.format(x1=float(start_p[0]), y1=float(start_p[1]))

        # 各セグメントの描画
        current_angle = start_angle
        for i in range(num_segments):
            if direction == "CCW":
                next_angle = start_angle + step_diff * (i + 1)
            else:
                next_angle = start_angle - step_diff * (i + 1)

            next_p = get_point(next_angle)

            # 各セグメントは 360/4 = 90度以下なので large_arc_flag は常に 0
            path_data += 'A {rx} {ry} 0 0 {sweep_flag} {x2} {y2} '.format(
                rx = R_x,  ry = R_y, sweep_flag = sweep_flag, x2 = float(next_p[0]), y2 = float(next_p[1]))

            current_angle = next_angle

        # Path要素の追加
        arc_path = self.path(
            d=path_data,
            fill='none',       # 塗りつぶしなし
            stroke=color,     # 線の色を黒に
            stroke_width=stroke_width,
            stroke_linecap="round"  # 線の端を丸くする
        )
        self.add(arc_path)

        # 矢印の描画
        # 矢印の位置（常に本来の終点）
        ta = target_angle + 5 if direction == "CCW" else target_angle - 5
        tip = get_point(ta)
        rad = np.radians(ta)


        # 接線ベクトル (dx/dtheta, dy/dtheta)
        # x = cx + Rx * sin(theta), y = cy + Ry * cos(theta)
        # dx/dtheta = Rx * cos(theta), dy/dtheta = -Ry * sin(theta)
        tx = R_x * np.cos(rad)
        ty = -R_y * np.sin(rad)

        if direction == "CW":
            tx, ty = -tx, -ty

        # 正規化
        norm = np.sqrt(tx**2 + ty**2)
        tx /= norm
        ty /= norm

        # 法線ベクトル
        nx, ny = -ty, tx

        arrow_size = stroke_width * 3
        p1 = tip
        p2 = (tip[0] - tx * arrow_size + nx * arrow_size * 0.6, 
              tip[1] - ty * arrow_size + ny * arrow_size * 0.6)
        p3 = (tip[0] - tx * arrow_size - nx * arrow_size * 0.6, 
              tip[1] - ty * arrow_size - ny * arrow_size * 0.6)

        self.add(self.polygon([p1, p2, p3], fill=color, stroke=color, stroke_width=1, stroke_linejoin="round"))

    def draw_distributed_load(self, beam_leftend, beam_rightend, base_magnitude, load_range = (0,1), function="1", color="black", stroke_width=0.75, arrow_size=5):
        """
        startからendへの分布荷重を描画する
        magnitude: 分布荷重の大きさ (N/m)
        """
        import sympy as sp

        length = float(beam_rightend[0] - beam_leftend[0])
        start_pos = float(beam_leftend[0] + load_range[0] * length)
        end_pos = float(beam_leftend[0] + load_range[1] * length)

        num_arrows = int(15 * (load_range[1] - load_range[0]))  # 矢印の数

        local_magnitudes = []; X = []
        for i in range(num_arrows + 1):
            X.append(start_pos + (end_pos - start_pos) * i / num_arrows)
            # 荷重関数に基づく矢印の大きさを計算
            relative_position = (X[-1] - beam_leftend[0]) / length

            #print(base_magnitude, function, relative_position)
            dict = {sp.symbols('x'): relative_position, sp.symbols('L'): 1}
            local_magnitudes.append(float(base_magnitude * sp.sympify(function).subs(dict).evalf()))

        for i in range(num_arrows + 1):
            local_magnitude = float(local_magnitudes[i])
            xi = float(X[i])

            # 矢印の向きを決定（下向き）
            start_point = (float(xi), float(beam_leftend[1]) - local_magnitude)
            end_point = (float(xi), float(beam_leftend[1]))
            #print(start_point, end_point)
            
            if local_magnitude > arrow_size:
                self.draw_force(start_point, end_point, color=color, stroke_width=stroke_width, size=arrow_size)

            if i > 0:
                xi_prev = float(X[i-1])
                mag_prev = float(local_magnitudes[i-1])
                self.add(self.line((float(xi_prev), float(beam_leftend[1]) - mag_prev), (float(xi), float(beam_leftend[1]) - local_magnitude), stroke=color, stroke_width=stroke_width, stroke_linecap="round"))

    def draw_fixed_end(self, rod_center, width, height, color="black", rotate_angle=0, pitch=5):
        """
        固定支点を描画する
        rotate_angle:回転角度，0の時は棒材下側を固定する。
        """
        rod_center = (float(rod_center[0]), float(rod_center[1]))
        width = float(width)
        height = float(height)

        left_top = (rod_center[0] - width / 2, rod_center[1])
        right_top = (rod_center[0] + width / 2, rod_center[1])
        left_bottom = (rod_center[0] - width / 2, rod_center[1] + height)
        right_bottom = (rod_center[0] + width / 2, rod_center[1] + height)

        self.add(self.line(left_top, right_top, stroke_width=2, stroke = color, stroke_linecap="round", 
                           transform=f'rotate({rotate_angle} {rod_center[0]} {rod_center[1]})'))
        #回転行列を適用
        left_top = self.rotate_point(left_top, rod_center, rotate_angle)
        right_top = self.rotate_point(right_top, rod_center, rotate_angle)
        left_bottom = self.rotate_point(left_bottom, rod_center, rotate_angle)
        right_bottom = self.rotate_point(right_bottom, rod_center, rotate_angle)

        x = min(left_top[0], right_top[0], left_bottom[0], right_bottom[0]) - float(self.width)
        y = min(left_top[1], right_top[1], left_bottom[1], right_bottom[1]) - float(self.height)

        x_e = max(left_top[0], right_top[0], left_bottom[0], right_bottom[0])
        y_e = max(left_top[1], right_top[1], left_bottom[0], right_bottom[1])

        line_length = max(x_e - x + width, y_e - y + height)

        if x_e - x < y_e - y:
            y = y - height*10; y_e = y_e  + height * 10
            e = y_e; t = y
            xscan = False; yscan = True
        else:
            x = x - width*10; x_e = x_e  + width*10
            e = x_e; t = x
            xscan = True; yscan = False



        #print(f"lefttop:{left_top}, righttop:{right_top}, leftbottom:{left_bottom}, rightbottom:{right_bottom}")

        while t < e:
            start = (float(x), float(y)); end = (float(x + line_length), float(y + line_length))
            intersections = []
            intersections.append(self.intersection(start,end,left_bottom, right_bottom))
            intersections.append(self.intersection(start,end,left_top, right_top))
            intersections.append(self.intersection(start,end,left_top, left_bottom))
            intersections.append(self.intersection(start,end,right_top, right_bottom))

            # intersectionsの中でNone以外のものを抽出
            #print(intersections)

            intersections = [i for i in intersections if i is not None]
            #print(f"start:{start}, end:{end}")
            #print(intersections)
            #self.add(self.line(left_bottom, right_bottom, stroke_width=0.2, stroke = "red", stroke_linecap="round"))
            #self.add(self.line(left_top, right_top, stroke_width=1, stroke = "blue", stroke_linecap="round"))
            #self.add(self.line(left_top, left_bottom, stroke_width=0.2, stroke = "red", stroke_linecap="round"))
            #self.add(self.line(right_top, right_bottom, stroke_width=0.2, stroke = "red", stroke_linecap="round"))    

            #print(f"{len(intersections)} intersections found")

            if len(intersections) > 1:
                intersections = np.array(intersections)
                
                x1 = np.min(intersections[:,0])
                y1 = np.min(intersections[:,1])
                x2 = np.max(intersections[:,0])
                y2 = np.max(intersections[:,1])

                self.add(self.line((float(x1), float(y1)), (float(x2), float(y2)), stroke_width=0.75, stroke = color, stroke_linecap="round"))
            else:
                #self.add(self.line(start, end, stroke_width=0.2, stroke = "red", stroke_linecap="round"))
                pass

            t += pitch
            if xscan:
                x += pitch
            if yscan:
                y += pitch
    
    def draw_fixed_support(self, rod_center, width, height, color="black", rotate_angle=0, pitch=5):
        """
        別名として実装
        """
        self.draw_fixed_end(rod_center, width, height, color, rotate_angle, pitch)

    def rotate_point(self, point, center, angle):
        x = float(point[0] - center[0])
        y = float(point[1] - center[1])
        angle = np.radians(angle)
        x_new = x * np.cos(angle) - y * np.sin(angle)
        y_new = x * np.sin(angle) + y * np.cos(angle)
        return (float(x_new + center[0]), float(y_new + center[1]))

    def intersection(self, s1, e1, s2, e2):
        """
        s,eの２つの(x,y)で与えられた直線が交点を返す
        """

        def slope(s, e):
            if float(e[0]) == float(s[0]):
                return float('inf')
            else:
                return (float(e[1])-float(s[1])) / (float(e[0])-float(s[0]))
        
        def intercept(s,e):
            return float(s[1]) - slope(s,e) * float(s[0])
        
        def intersection(line1, line2):
            s1, e1 = line1
            s2, e2 = line2

            if slope(s1, e1) == slope(s2, e2):
                return None
            
            elif slope(s1, e1) == float('inf'):
                x = s1[0]
                y = slope(s2, e2) * x + intercept(s2, e2)
            
            elif slope(s2, e2) == float('inf'):
                x = s2[0]
                y = slope(s1, e1) * x + intercept(s1, e1)
            
            else:
                x = (intercept(s2, e2) - intercept(s1, e1)) / (slope(s1, e1) - slope(s2, e2))
                y = slope(s1, e1) * x + intercept(s1, e1)
            
            return (float(x), float(y))

        res = intersection((s1, e1), (s2, e2))
        if res is None:
            return None
        (x,y) = res
        
        # 交点が両方の線分の範囲内にあるか確認
        if x >= min(float(s1[0]), float(e1[0]))-0.01 and x <= max(float(s1[0]), float(e1[0]))+0.01 and \
           x >= min(float(s2[0]), float(e2[0]))-0.01 and x <= max(float(s2[0]), float(e2[0]))+0.01 and \
           y >= min(float(s1[1]), float(e1[1]))-0.01 and y <= max(float(s1[1]), float(e1[1]))+0.01 and \
           y >= min(float(s2[1]), float(e2[1]))-0.01 and y <= max(float(s2[1]), float(e2[1]))+0.01:
            return (x, y)
        else:
            #print(f"({x},{y}) is outside Intersection not found for lines {s1}-{e1} and {s2}-{e2}")
            return None
            
    def draw_pin_support(self, rod_center, size, color="white", rotate_angle=0, delta=True, circle=True):
        """
        ピン支持を描画する
        rod_center: 支点の中心座標(x,y)
        size: 支点のサイズ
        rotate_angle:回転角度，0の時は棒材下側を固定する。
        """
        rod_center = (float(rod_center[0]), float(rod_center[1]))
        size = float(size)

        #支点の中心を頂点とする三角形を描画
        if delta:
            self.draw_triangle(top_point=rod_center, size=size*3.5, color="black", fill_color=color, stroke_width=1.5)

        if circle:
            #支点の中心に半径sizeの円を描画
            self.add(self.circle(center=rod_center, r=size, fill=color, stroke="black", stroke_width=1.5))
    
    def draw_roller_support(self, rod_center, size, color="white", rotate_angle=0):
        """
        ローラー支持を描画する
        rod_center: 支点の中心座標(x,y)
        size: 支点のサイズ
        rotate_angle:回転角度，0の時は棒材下側を固定する。
        """
        rod_center = (float(rod_center[0]), float(rod_center[1]))
        size = float(size)

        #支点の中心を頂点とする三角形を描画
        self.draw_triangle(top_point=rod_center, size=size*3.5, color="black", fill_color=color, stroke_width=1.5)
        # 支点の下に三角形幅と同じ幅の線を描画
        left = (float(rod_center[0] - size*1.75), float(rod_center[1] + size*4))
        right = (float(rod_center[0] + size*1.75), float(rod_center[1] + size*4))
        self.add(self.line(left, right, stroke="black", stroke_width=1.5, stroke_linecap="round"))
        
    def draw_equation(self, equation, position, fontsize=10, color="black", fill="none", valign="center", halign="center"):
        """
        数式を描画する
        equation: 数式の文字列
        position: 数式の挿入位置 (x, y)
        fontsize: フォントサイズ
        color: フォントカラー
        fill: 背景色
        """

        #print(f"Draw equation: {equation} at {position} with fontsize {fontsize}, color {color}, fill {fill}")
        eq = Equation(equation, fontsize=fontsize, color=color)
        position = (float(position[0]), float(position[1]))
        self._equations.append((eq, position, fill, valign, halign))
        
