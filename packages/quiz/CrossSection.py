import numpy as np
import svgwrite

import matplotlib.pyplot as plt
import svgwrite.drawing
from sympy import symbols, latex
import sympy as sp

from .Figure import Figure

class CrossSection():
    """
    This class is used to define the cross section of part.
    """
    def __init__(self):
        self._area = 0
        self._figure = None
        self._name = None
        self._dimensions = None
        self._dimension_names = None
        self._diameter = None
        
        self._centroid = None # tuple (equation, value)
        self._explanation_centroid = None

        self._moment_of_inertia = None # tuple (equation, value)
        self._explanation_moment_of_inertia = None

        self._section_modulus = None # tuple ((equation_bottom, value_bottom), (equation_top, value_top))
        self._explanation_section_modulus = None

        self._width = None
        self._height = None
        self._thickness = None
        self._dx = None
        self._dy = None

    def __str__(self):
        return self._name
    
    @property
    def height(self):
        return self._height
    
    @property
    def width(self):
        return self._width
    
    @property
    def thickness(self):
        return self._thickness

    @property
    def area(self):
        """
        This method is used to get the area of the cross section.
        """
        if self._area == 0:
            self.get_area()

        return self._area
    
    @property
    def area_with_unit(self):
        """
        This method is used to get the area of the cross section with unit.
        """
        if self._area == 0:
            self.get_area()

        return f"{self._area:.0f} mm²"

    @property
    def si_area(self):
        """
        This method is used to get the area of the cross section in SI unit.
        """
        if self._area == 0:
            self.get_area()

        return self._area * 1e-6
    
    @property
    def centroid(self):
        """
        This method is used to get the centroid of the cross section.
        """
        if self._centroid is None:
            self.get_centroid()

        return self._centroid

    @property
    def explanation_centroid(self):
        """
        This method is used to get the explanation of the centroid of the cross section.
        """
        if self._explanation_centroid is None:
            self.get_centroid()

        return self._explanation_centroid

    @property
    def moment_of_inertia(self):
        """
        This method is used to get the inertia of the cross section.
        """
        if self._moment_of_inertia is None:
            self.get_moment_of_inertia()

        return self._moment_of_inertia
    
    @property
    def polar_moment_of_inertia(self):
        """
        This method is used to get the polar moment of inertia of the cross section.
        """
        return self.moment_of_inertia[1] * 2

    @property
    def si_moment_of_inertia(self):
        """
        This method is used to get the inertia of the cross section in SI unit.
        """
        if self._moment_of_inertia is None:
            self.get_moment_of_inertia()

        if hasattr(self._moment_of_inertia[1], "__len__"):
            return [i * 1e-12 for i in self._moment_of_inertia[1]]
        else:
            return [self._moment_of_inertia[1] * 1e-12]
    
    @property
    def explanation_moment_of_inertia(self):
        """
        This method is used to get the explanation of the inertia of the cross section.
        """
        if self._explanation_moment_of_inertia is None:
            self.get_moment_of_inertia()

        return self._explanation_moment_of_inertia

    @property
    def section_modulus(self):
        """
        This method is used to get the section modulus of the cross section.
        """
        if self._section_modulus is None:
            self.get_section_modulus()

        return self._section_modulus

    @property
    def explanation_section_modulus(self):
        """
        This method is used to get the explanation of the section modulus of the cross section.
        """
        if self._explanation_section_modulus is None:
            self.get_section_modulus()

        return self._explanation_section_modulus

    @property
    def figure(self):
        """
        This method is used to get the figure of the cross section.
        """
        if self._figure is None:
            self.generate_figure()

        return self._figure

    @property
    def dimensions(self):
        return self._dimensions
    
    @property
    def diameter(self):
        return self._diameter
    
    @property
    def si_diameter(self):
        return self._diameter * 1e-3
    
    @property
    def diameter_with_unit(self):
        return f"{self._diameter:.3g} mm"
    
    @property
    def x_diameter(self):
        return self._dx
    
    @property
    def y_diameter(self):
        return self._dy

    @property
    def dimension_names(self):
        return self._dimension_names

    def get_area(self):
        """
        This method is used to get the area of the cross section.
        """
        print("not difined get_area for this cross section")

    def get_inertia(self):
        """
        This method is used to get the inertia of the cross section.
        """
        print("not difined get_inertia for this cross section")

    def get_section_modulus(self):
        #print("Calculating section modulus")
        H = sp.symbols("H")
        eq1 = sp.simplify(self.moment_of_inertia[0] / (H - self.centroid[0]))
        eq2 = sp.simplify(self.moment_of_inertia[0] / (- self.centroid[0]))

        value1 = self.moment_of_inertia[1] / (self._height - self.centroid[1])
        value2 = self.moment_of_inertia[1] / (- self.centroid[1])

        self._explanation_section_modulus = []
        self._explanation_section_modulus.append("再下面に対応する断面係数$Z_1$は，")
        self._explanation_section_modulus.append(fr"$Z_1$ = $\frac{{I}}{{H-y_g}}$=${eq1}$={value1:.0f} mm³")
        self._explanation_section_modulus.append("再上面に対応する断面係数$Z_2$は，")
        self._explanation_section_modulus.append(fr"$Z_2$ = $\frac{{I}}{{-y_g}}$=${eq2}$={value2:.0f} mm³")

        self._section_modulus = ((eq1, value1), (eq2, value2))


    def get_centroid(self):
        """
        This method is used to get the centroid of the cross section.
        """
        print("not difined get_centroid for this cross section")
    
    def get_moment_of_inertia(self):
        """
        This method is used to get the moment of inertia of the cross section.
        """
        print("not difined get_moment_of_inertia for this cross section")

    def generate_figure(self):
        """
        This method is used to generate the figure of the cross section.
        """
        print("not difined generate_figure for this cross section")


class Circle(CrossSection):
    def __init__(self, diameter):
        """
        This class is used to define the cross section of a circle.
        """
        super().__init__()
        self._diameter = diameter
        self._radius = diameter / 2
        self._width = diameter
        self._height = diameter

        self._name = "円形"
        self._dimension_names = ["直径"]
        self._dimensions = [self._diameter, self._radius]

    def get_area(self):
        self._area = np.pi * self._radius ** 2

    def get_centroid(self):
        #print("Calculating centroid for Circle")
        import sympy as sp
        self._explanation_centroid = []
        self._explanation_centroid.append("仮に，座標軸の原点を円の中心とすると，任意の$y$に対する幅$b(y)$は，$r = D/2$（$r$は半径，$D$は直径）と置くと，")
        self._explanation_centroid.append("$x^2 + y^2$ = $r^2$")
        self._explanation_centroid.append("$x^2 = r^2 - y^2$")
        self._explanation_centroid.append(r"$x$ = $\pm \sqrt{r^2 - y^2}$")
        self._explanation_centroid.append("$x$の倍が幅となるので，")
        self._explanation_centroid.append(r"$b(y) = 2\sqrt{r^2 - y^2}$")
        self._explanation_centroid.append("よって，断面一次モーメント$\int_A y dA$は，")
        self._explanation_centroid.append(r"$\int_{-r}^{r} \int_{0}^{b(y)}y dx dy$")
        self._explanation_centroid.append(r"　=$\int_{-r}^{r} 2\sqrt{r^2 - y^2}\cdot y dy$")
        self._explanation_centroid.append(r"　=$\int_{-r}^{r} 2y(r^2 - y^2)^{\frac{1}{2}} dy$")
        self._explanation_centroid.append(r"ここで，$u = r^2 - y^2$とおくと，$du = -2y dy$となり，積分範囲も$u$の範囲に変化するので，")
        self._explanation_centroid.append(r"　=$\int_{0}^{0} -u^{1/2} du$=$0$")
        self._explanation_centroid.append("したがって，円の重心は中心に位置する。問題に合わせて，上端からの距離を求めると，")
        self._explanation_centroid.append(f"$y_g$ = $r$ =$D/2$")

        self._centroid = (sp.sympify("H/2"),self._radius)

    def get_moment_of_inertia(self):
        """
        楕円の断面二次モーメントを重心軸周りに計算します。

        """
        # X軸周りの断面二次モーメント (ryに関連)
        ix = np.pi * self._radius * self._radius**3 / 4

        self._explanation_moment_of_inertia = []
        self._explanation_moment_of_inertia.append("楕円の断面二次モーメント$I_z$は，直径（高さ）を$H$とすると，")
        self._explanation_moment_of_inertia.append(r"$I_z$ = $\int_{A}y^2dA$")
        self._explanation_moment_of_inertia.append(r"ここで，$zy$座標系を$r \theta$座標系に変換すると，$r^2 = z^2 + y^2$，$z = r\cos\theta$，$y = r\sin\theta$となるので，断面の半径を$R$とすると，")
        self._explanation_moment_of_inertia.append(r"$I_z$ = $\int_{0}^{2\pi}\int_{0}^{R} (r\sin\theta)^2 r dr d\theta$")
        self._explanation_moment_of_inertia.append(r"　=$\int_{0}^{2\pi}\sin^2\theta d\theta \int_{0}^{R} r^3 dr$")
        self._explanation_moment_of_inertia.append(r"　=$\left[\frac{\theta}{2} - \frac{\sin2\theta}{4}\right]_{0}^{2\pi} \cdot \left[\frac{r^4}{4}\right]_0^{R}$")
        self._explanation_moment_of_inertia.append(r"　=$\frac{\pi R^4}{4}$")
        self._explanation_moment_of_inertia.append("半径$R$を直径$H$で表すと，$R = H/2$なので，")
        self._explanation_moment_of_inertia.append(r"$I_z$ = $\frac{\pi (H/2)^4}{4}$ = $\frac{\pi H^4}{64}$")

        self._moment_of_inertia = (sp.sympify("pi*H^4/64"),ix)
    
    def generate_figure(self):
        
        radius = 30
        offset = (len(str(self._diameter))+1)*8.0/2
        max_r_off = max(radius, offset)
        
        # 左右に5pxの余白を持たせた動的な幅
        width_svg = max_r_off + radius + 10
        center_x = width_svg - radius - 5 # 右側に寄せる

        dwg = Figure(size=(width_svg, 100))

        dwg.add(dwg.circle(center=(center_x, 60), r= radius, stroke="black", fill="none", stroke_width=1.5))

        dwg.draw_arrow((center_x-radius, 20), (center_x+radius, 20))
        dwg.add(dwg.line((center_x-radius, 16), (center_x-radius, 60), stroke=svgwrite.rgb(0, 0, 0), stroke_width=0.75, stroke_linecap="round"))
        dwg.add(dwg.line((center_x+radius, 16), (center_x+radius, 60), stroke=svgwrite.rgb(0, 0, 0), stroke_width=0.75, stroke_linecap="round"))
        dwg.add(dwg.text(f'Φ{self._diameter}', insert=(center_x, 15), fill=svgwrite.rgb(0, 0, 0), style="font-style:italic;font-family:Meiryo;text-anchor:middle"))

        self._figure = dwg

class Ellipse(CrossSection):
    def __init__(self, dx, dy):
        """
        このクラスは楕円の断面積を定義するために使用されます。

        Args:
            dx (float): X軸方向の直径（長径または短径）
            dy (float): Y軸方向の直径（長径または短径）
        """
        super().__init__()
        if dx <= 0 or dy <= 0:
            raise ValueError("直径は正の値である必要があります。")

        self._dx = dx
        self._dy = dy
        self._rx = dx / 2
        self._ry = dy / 2
        self._name = "楕円形"
        # 長径と短径を区別して表示したい場合
        if dx >= dy:
             self._dimension_names = ["長径", "短径"]
        else:
             self._dimension_names = ["短径", "長径"] # X方向が短径、Y方向が長径の場合

        # self._dimensions には入力されたdx, dyをそのまま格納
        self._dimensions = [self._dx, self._dy]


    def get_area(self):
        """楕円の断面積を計算します。"""
        self._area = np.pi * self._rx * self._ry
        return self._area

    def get_centroid(self):
        #print("Calculating centroid for Ellipse")
        import sympy as sp
        self._explanation_centroid = []
        self._explanation_centroid.append("仮に，座標軸の原点を楕円の中心とすると，任意の$y$に対する幅$b(y)$は，$r_b$を横方向半径，$r_h$を縦方向半径と置くと，")
        self._explanation_centroid.append(r"$\frac{x^2}{r_b^2} + \frac{y^2}{r_h^2}$ = $1$")
        
        self._explanation_centroid.append(r"$\frac{x^2}{r_b^2}$ = $1 - \frac{y^2}{r_h^2}$")
        self._explanation_centroid.append(r"$x$ = $\pm r_b\sqrt{1 - \frac{y^2}{r_h^2}}$")
        self._explanation_centroid.append("$x$の倍が幅となるので，")
        self._explanation_centroid.append(r"$b(y) = 2 r_b\sqrt{1 - \frac{y^2}{r_h^2}}$")
        self._explanation_centroid.append("よって，断面一次モーメント$\int_A y dA$は，")
        self._explanation_centroid.append(r"$\int_{-r_h}^{r_h} \int_{0}^{b(y)}y dx dy$")
        self._explanation_centroid.append(r"　=$\int_{-r_h}^{r_h} 2 r_b\sqrt{1 - \frac{y^2}{r_h^2}}\cdot y dy$")
        self._explanation_centroid.append(r"　=$\int_{-r_h}^{r_h} 2 r_b y \left(1 - \frac{y^2}{r_h^2} \right)^{\frac{1}{2}} dy$")
        self._explanation_centroid.append(r"ここで，$u = 1 - \frac{y^2}{r_h^2}$とおくと，$du = -\frac{2y}{r_h^2} dy$となり，積分範囲も$u$の範囲に変化するので，")
        self._explanation_centroid.append(r"　=$\int_{0}^{0} -r_b r_h^2 u^{\frac{1}{2}} du$=$0$")
        self._explanation_centroid.append("したがって，楕円の重心は中心に位置する。問題に合わせて，上端からの距離を求めると，楕円の高さを$H$として，")
        self._explanation_centroid.append(f"$y_g$ = $r_h$ =$H/2$")
        
        self._centroid = (sp.sympify("H/2"),self._ry)



    def get_moment_of_inertia(self):
        """
        楕円の断面二次モーメントを重心軸周りに計算します。

        """
        # X軸周りの断面二次モーメント (ryに関連)
        ix = np.pi * self._rx * self._ry**3 / 4

        self._explanation_moment_of_inertia = []
        self._explanation_moment_of_inertia.append("楕円の断面二次モーメント$I_z$は，幅を$B$，高さを$H$とすると，")
        self._explanation_moment_of_inertia.append(r"$I_z$ = $\int_{-H/2}^{H/2}\int_{-B/2}^{B/2}y^2dzdy$")
        self._explanation_moment_of_inertia.append("ここで，$zy$座標系を$r \theta$座標系に変換すると，$r^2 = z^2 + y^2$，$z = r\cos \theta$，$y = r\sin\theta$となるので，断面の半径を$R$とすると，")
        self._explanation_moment_of_inertia.append(r"$I_z$ = $\int_{0}^{2\pi}\int_{0}^{R} (r\sin\theta)^2 r dr d\theta$")
        self._explanation_moment_of_inertia.append(r"　=$\int_{0}^{2\pi}\sin^2\theta d\theta \int_{0}^{R} r^3 dr$")
        self._explanation_moment_of_inertia.append(r"　=$\left[\frac{\theta}{2} - \frac{\sin2\theta}{4}\right]_{0}^{2\pi} \cdot \left[\frac{r^4}{4}\right]_0^{R}$")
        self._explanation_moment_of_inertia.append(r"　=$\frac{\pi R^4}{4}$")
        self._explanation_moment_of_inertia.append("半径$R$を直径$H$で表すと，$R = H/2$なので，")
        self._explanation_moment_of_inertia.append(r"$I_z$ = $\frac{\pi (H/2)^4}{4}$ = $\frac{\pi H^4}{64}$")

        self._moment_of_inertia = (sp.sympify("\pi H^4/64"),ix)

        

    def generate_figure(self):
        
        """寸法付きの楕円のSVG図を作成します。"""
        # 図の中央座標と描画サイズの設定
        center_x, center_y = 81, 40
        max_draw_radius = 20  # 描画上での最大半径の目標値
        
        dim_offset = 25       # 寸法線と図形の間隔
        text_offset = 5       # 寸法テキストと寸法線の間隔

        # 実際の半径を基に、描画上の半径を決定するためのスケールファクターを計算
        max_actual_radius = max(self._rx, self._ry)
        if max_actual_radius == 0:
             scale = 1
        else:
             scale = max_draw_radius / max_actual_radius

        draw_rx = self._rx * scale
        draw_ry = self._ry * scale

        # Figureオブジェクトの作成
        dwg = Figure() # 仮のFigureクラスを使用

        # 楕円の描画
        dwg.add(dwg.ellipse(center=(center_x, center_y), r=(draw_rx, draw_ry),
                            stroke="black", fill="none", stroke_width=1.5))

        # --- X軸方向（横方向）の寸法線とテキスト（dxを表示）---
        # 寸法線（矢印）のY座標
        arrow_y = center_y + draw_ry + dim_offset
        # 矢印の描画 (Figureクラスのdraw_arrowメソッドを使用)
        dwg.draw_arrow((center_x - draw_rx, arrow_y), (center_x + draw_rx, arrow_y))

        # 引き出し線の描画
        ext_line_length = dim_offset * 1.1 # 引き出し線は少し短くする
        dwg.add(dwg.line((center_x - draw_rx, center_y),
                         (center_x - draw_rx, center_y + draw_ry + ext_line_length),
                         stroke=svgwrite.rgb(0, 0, 0), stroke_width=0.75, stroke_linecap="round"))
        dwg.add(dwg.line((center_x + draw_rx, center_y),
                         (center_x + draw_rx, center_y + draw_ry + ext_line_length),
                         stroke=svgwrite.rgb(0, 0, 0), stroke_width=0.75, stroke_linecap="round"))

        # 寸法テキスト（長径または短径の表示）
        # テキストは矢印の上に、水平方向中央寄せで配置
        text_y = arrow_y - text_offset
        text_content_dx = f'{self._dx}' # 長径/短径: dx
        dwg.add(dwg.text(text_content_dx,
                         insert=(center_x, text_y),
                         fill=svgwrite.rgb(0, 0, 0),
                         style="font-style:italic;font-family:Meiryo; text-anchor:middle")) # text-anchor:middleで中央寄せ

        # --- Y軸方向（縦方向）の寸法線とテキスト（dyを表示）---
        # 寸法線（矢印）のX座標
        arrow_x = center_x + draw_rx + dim_offset
        # 矢印の描画 (Figureクラスのdraw_arrowメソッドを使用)
        dwg.draw_arrow((arrow_x, center_y - draw_ry), (arrow_x, center_y + draw_ry))
        # 引き出し線の描画
        dwg.add(dwg.line((center_x, center_y - draw_ry),
                         (center_x + draw_rx + ext_line_length, center_y - draw_ry),
                         stroke=svgwrite.rgb(0, 0, 0), stroke_width=0.75, stroke_linecap="round"))
        dwg.add(dwg.line((center_x, center_y + draw_ry),
                         (center_x + draw_rx + ext_line_length, center_y + draw_ry),
                         stroke=svgwrite.rgb(0, 0, 0), stroke_width=0.75, stroke_linecap="round"))

        # 寸法テキスト（短径または長径の表示）
        # テキストは矢印の右に、垂直方向中央寄せで配置し、90度回転させる
        text_x = arrow_x + text_offset
        text_content_dy = f'{self._dy}' # 短径/長径: dy
        dwg.add(dwg.text(text_content_dy,
                         insert=(text_x+6, center_y), # 回転の中心も指定
                         fill=svgwrite.rgb(0, 0, 0),
                         style="font-style:italic;font-family:Meiryo; text-anchor:start; alignment-baseline:middle", # startとmiddleで基準点を設定
                         transform=f"rotate(90 {text_x+6},{center_y-7})")) # 挿入点を中心に90度回転

        self._figure = dwg
        return self._figure # 生成したFigureオブジェクトを返す

class HalfEllipse(CrossSection):

    def __init__(self, dx, dy):
        """
        This class is used to define the cross section of a half ellipse.
        """
        super().__init__()
        self._dx = dx
        self._dy = dy
        self._rx = dx / 2
        self._ry = dy / 2
        self._name = "半楕円形"
        self._dimension_names = ["長径", "短径"]
        self._dimensions = [self._dx, self._dy]
    
    def get_area(self):

        self._area = np.pi * self._rx * self._ry / 2

    def get_centroid(self):

        #print("Calculating centroid for HalfEllipse")
        self._explanation_centroid = []
        self._explanation_centroid.append("まず，座標軸の原点を上端の中央に置き，下向きの$y$軸を定義すると，任意の$y$に対する幅$b(y)$は，横径を$B$，縦半径を$H$とすると，")
        self._explanation_centroid.append(r"$\frac{x^2}{(B/2)^2} + \frac{y^2}{H^2}$ = $1$")
        self._explanation_centroid.append(r"$\frac{x^2}{(B/2)^2}$ = $1 - \frac{y^2}{H^2}$")
        self._explanation_centroid.append(r"$x$ = $\pm \frac{B}{2}\sqrt{1 - \frac{y^2}{H^2}}$")
        self._explanation_centroid.append("$x$の倍が幅となるので，")
        self._explanation_centroid.append(r"$b(y) = B\sqrt{1 - \frac{y^2}{H^2}}$")
        self._explanation_centroid.append("半楕円の重心位置$y_g$は，その断面一次モーメント$\int_A y dA$は，")
        self._explanation_centroid.append(r"$\int_{0}^{H} \int_{0}^{b(y)} y dx dy$")
        self._explanation_centroid.append(r"　=$\int_{0}^{H} B \sqrt{1 - \frac{y^2}{H^2}} \cdot y dy$")
        self._explanation_centroid.append(r"ここで，$u = 1 - \frac{y^2}{H^2}$とおくと，$du = -\frac{2y}{H^2} dy$となり，積分範囲も$u$の範囲に変化するので，")
        self._explanation_centroid.append(r"　=$\int_{1}^{0} -\frac{B H^2}{2} u^{\frac{1}{2}} du$=$\left[\frac{B H^2}{3} u^{\frac{3}{2}}\right]_1^{0}$")
        self._explanation_centroid.append(r"　=$\frac{B H^2}{3}$")
        self._explanation_centroid.append("断面積$\int_A dA$を求めると，")
        self._explanation_centroid.append(r"$A$= $\int_{0}^{H} \int_{0}^{b(y)} dx dy$")
        self._explanation_centroid.append(r"　=$\int_{0}^{H} B \sqrt{1 - \frac{y^2}{H^2}} dy$")
        self._explanation_centroid.append(r"　=$\int_{0}^{H} B ({1 - \frac{y^2}{H^2}})^{\frac{1}{2}} dy$")
        self._explanation_centroid.append(r"　=$$")
        

        self._explanation_centroid.append("よって，重心の位置$y_g$は，")
        self._explanation_centroid.append(r"$y_g$ = $\frac{\int_A y dA}{\int_A dA}$ = $\frac{4BH^2/3}{\pi BH/2}$ = $\frac{4H}{3\pi}$")

        self._centroid = (sp.sympify("4*H/(3*pi)"), 4 * self._ry / (3 * np.pi))

    def get_moment_of_inertia(self):

        #print("Calculating moment of inertia for HalfEllipse")
        self._explanation_moment_of_inertia = []
        self._explanation_moment_of_inertia.append("半楕円の断面2次モーメント$I_z$は，幅を$B$，高さを$H$とすると，")
        self._explanation_moment_of_inertia.append(r"$I_z$ = $\int_{0}^{H}\int_{-B/2}^{B/2}y^2dzdy$")
        self._explanation_moment_of_inertia.append(r"　=$\int_{0}^{H} B y^2 dy$")
        self._explanation_moment_of_inertia.append(r"　=$B\left[\frac{y^3}{3}\right]_0^{H}$")
        self._explanation_moment_of_inertia.append(r"　=$\frac{B H^3}{3}$")
    
    def generate_figure(self):

        dwg = Figure()
        initial_size = 60
        B = self._dx
        H = self._dy / 2
        if B < H:
            height = initial_size
            width = B / H * initial_size
        else:
            width = initial_size
            height = H / B * initial_size
        
        #最上部に半円を閉じる直線を描画
        dwg.add(dwg.line((81 - width / 2, 95 - height), (81 + width / 2, 95 - height), stroke="black", stroke_width=1.5))
        #半円部分を描画
        dwg.add(dwg.path(d=f"M {81 - width / 2},{95 - height} A {width / 2},{height} 0 0,0 {81 + width / 2},{95 - height}", stroke="black", fill="none", stroke_width=1.5))
        
        #横の寸法線
        dwg.draw_arrow((81 - width / 2, 20), (81 + width / 2, 20))
        dwg.add(dwg.line((81 - width / 2, 17), (81 - width / 2, 95-height), stroke=svgwrite.rgb(0, 0, 0), stroke_width=0.75, stroke_linecap="round"))
        dwg.add(dwg.line((81 + width / 2, 17), (81 + width / 2, 95-height), stroke=svgwrite.rgb(0, 0, 0), stroke_width=0.75, stroke_linecap="round"))
        offset = len(str(self._dx)) * 8.0 / 2
        dwg.add(dwg.text(f'{self._dx}', insert=(81 - offset, 15), fill=svgwrite.rgb(0, 0, 0), style="font-style:italic;font-family:Meiryo"))

        #縦の寸法線（文字は半時計回りに90度回転）
        dwg.draw_arrow((33, (95 - height)), (33, 95))
        dwg.add(dwg.line((81, 95), (30, 95), stroke=svgwrite.rgb(0, 0, 0), stroke_width=0.75, stroke_linecap="round"))
        dwg.add(dwg.line((81, (95 - height)), (30, (95 - height)), stroke=svgwrite.rgb(0, 0, 0), stroke_width=0.75, stroke_linecap="round"))
        #　上下左右とも中央揃え
        dwg.add(dwg.text(f'{self._dy}', insert=(25, (95 - height / 2)), fill=svgwrite.rgb(0, 0, 0), style="font-style:italic;font-family:Meiryo;text-anchor:middle; alignment-baseline:middle", transform=f"rotate(-90 25,{95 - height / 2})"))

        self._figure = dwg
        

class Square(CrossSection):
    def __init__(self, width):
        """
        This class is used to define the cross section of a square.
        """
        super().__init__()
        self._width = width
        self._name = "正方形"
        self._dimension_names = ["幅"]
        self._dimensions = [self._width]

    def get_area(self):
        self._area = self._width ** 2

    def get_inertia(self):
        self._inertia = self._width ** 4 / 12
    
    def generate_figure(self):

        dwg = Figure()
        initial_size = 60
        if self._width < self._height:
            height = initial_size
            width = self._width / self._height * initial_size
        else:
            width = initial_size
            height = self._height / self._width * initial_size

        dwg.add(dwg.rect(insert=(81-width/2, (95-height)), size=(width, height), stroke="black", fill="none", stroke_width=1.5))

        #横の寸法線
        dwg.draw_arrow((81-width/2, 20), (81+width/2, 20))
        dwg.add(dwg.line((81-width/2, 17), (81-width/2, 95), stroke=svgwrite.rgb(0, 0, 0), stroke_width=0.75, stroke_linecap="round"))
        dwg.add(dwg.line((81+width/2, 17), (81+width/2, 95), stroke=svgwrite.rgb(0, 0, 0), stroke_width=0.75, stroke_linecap="round"))
        offset = len(str(self._width))*8.0/2
        dwg.add(dwg.text(f'{self._width}', insert=(81 - offset, 15), fill=svgwrite.rgb(0, 0, 0), style="font-style:italic;font-family:Meiryo"))

        #縦の寸法線
        dwg.draw_arrow((33, (95-height)), (33, 95))
        dwg.add(dwg.line((81, 95), (30, 95), stroke=svgwrite.rgb(0, 0, 0), stroke_width=0.75, stroke_linecap="round"))
        dwg.add(dwg.line((81, (95-height)), (30, (95-height)), stroke=svgwrite.rgb(0, 0, 0), stroke_width=0.75, stroke_linecap="round"))

class Rectangle(CrossSection):
    def __init__(self, width, height):
        """
        This class is used to define the cross section of a rectangle.
        """
        super().__init__()
        self._width = width
        self._height = height
        
        self._name = "矩形"
        self._dimensions = [self._width, self._height]
    
    def get_area(self):
        self._area = self._width * self._height
    
    def get_centroid(self):
        #print("Calculating centroid for Rectangle")
        import sympy as sp
        self._explanation_centroid = []
        self._explanation_centroid.append("座標軸の原点を長方形の上端として$y$軸を下向きに定義すると，断面一次モーメント$\int_A y dA$は，高さを$H$，幅を$B$として，")
        self._explanation_centroid.append(r"$\int_{0}^{H} \int_{0}^{B} y dx dy$")
        self._explanation_centroid.append(r"　=$\int_{0}^{H} By dy$")
        self._explanation_centroid.append(r"　=$\left[\frac{By^2}{2}\right]_0^{H}$")
        self._explanation_centroid.append(r"　=$\frac{BH^2}{2}$")
        self._explanation_centroid.append("断面積$A$を求めると，")
        self._explanation_centroid.append(r"$A$= $\int_{0}^{H} \int_{0}^{B} dx dy$")
        self._explanation_centroid.append(r"　=$\int_{0}^{H} B dy$")
        self._explanation_centroid.append(r"　=$\left[By\right]_0^{H}$")
        self._explanation_centroid.append(r"　=$BH$")
        self._explanation_centroid.append("よって，重心の位置$y_g$は，")
        self._explanation_centroid.append(r"$y_g$ = $\frac{\int_A y dA}{A}$ = $\frac{BH^2/2}{BH}$ = $H/2$")
        
        self._centroid = (sp.sympify("H/2"), self._height / 2)

    def get_moment_of_inertia(self):
        #print("Calculating moment of inertia for Rectangle")
        self._explanation_moment_of_inertia = []
        self._explanation_moment_of_inertia.append("矩形の断面二次モーメント$I_z$は，定義式により，")
        self._explanation_moment_of_inertia.append(r"$I_z$ = $\int_{A} y^2 dA$")
        self._explanation_moment_of_inertia.append("ここで，高さを$H$，幅を$B$として，横方向の領域を図心原点から変換し，")
        self._explanation_moment_of_inertia.append(r"　=$\int_{\frac{-H}{2}}^{\frac{H}{2}} \int_{0}^{B} y^2 dx dy$")
        self._explanation_moment_of_inertia.append(r"　=$\int_{\frac{-H}{2}}^{\frac{H}{2}} B y^2 dy$")
        self._explanation_moment_of_inertia.append(r"　=$\left[\frac{B y^3}{3}\right]_{\frac{-H}{2}}^{\frac{H}{2}}$")
        self._explanation_moment_of_inertia.append(r"　=$\frac{B H^3}{12}$")
        
        self._moment_of_inertia = (sp.sympify("B*H^3/12"), self._width * self._height ** 3 / 12)
    

    def generate_figure(self):

        initial_size = 60
        if self._width < self._height:
            height = initial_size
            width = self._width / self._height * initial_size
        else:
            width = initial_size
            height = self._height / self._width * initial_size

        padding = 5
        dim_v_x = 20 # 縦寸法線のX座標
        shape_left_x = 40
        center_x = shape_left_x + width / 2
        width_svg = shape_left_x + width + padding
        
        dwg = Figure(size=(width_svg, 100))

        dwg.add(dwg.rect(insert=(shape_left_x, (95-height)), size=(width, height), stroke="black", fill="none", stroke_width=1.5))

        #横の寸法線
        dwg.draw_arrow((shape_left_x, 20), (shape_left_x+width, 20))
        dwg.add(dwg.line((shape_left_x, 17), (shape_left_x, 95), stroke=svgwrite.rgb(0, 0, 0), stroke_width=0.75, stroke_linecap="round"))
        dwg.add(dwg.line((shape_left_x+width, 17), (shape_left_x+width, 95), stroke=svgwrite.rgb(0, 0, 0), stroke_width=0.75, stroke_linecap="round"))
        dwg.add(dwg.text(f'{self._width}', insert=(center_x, 15), fill=svgwrite.rgb(0, 0, 0), style="font-style:italic;font-family:Meiryo;text-anchor:middle"))

        #縦の寸法線
        dwg.draw_arrow((dim_v_x, (95-height)), (dim_v_x, 95))
        dwg.add(dwg.line((shape_left_x, 95), (dim_v_x-3, 95), stroke=svgwrite.rgb(0, 0, 0), stroke_width=0.75, stroke_linecap="round"))
        dwg.add(dwg.line((shape_left_x, (95-height)), (dim_v_x-3, (95-height)), stroke=svgwrite.rgb(0, 0, 0), stroke_width=0.75, stroke_linecap="round"))
        
        text = dwg.text(str(self._height), insert=(dim_v_x-3, (95-height/2)), fill=svgwrite.rgb(0, 0, 0), style="font-style:italic;font-family:Meiryo;text-anchor:middle")
        text.rotate(270, center=(dim_v_x-3, (95-height/2)))
        dwg.add(text)

        self._figure = dwg

class Triangle(CrossSection):
    def __init__(self, base, height):
        """
        This class is used to define the cross section of a triangle.
        """
        super().__init__()
        self._base = base
        self._width = base
        self._height = height

        self._name = "三角形"
        self._dimensions = [self._base, self._height]
    
    def get_area(self):
        self._area = self._base * self._height / 2
    
    def get_centroid(self):
        #print("Calculating centroid for Triangle")
        import sympy as sp
        self._explanation_centroid = []
        self._explanation_centroid.append("座標軸の原点を上端の三角形の頂点として$y$軸を下向きに定義すると，断面一次モーメント$\int_A y dA$は，底辺を$B$，高さを$H$として，")
        self._explanation_centroid.append(r"$\int_{0}^{H} \int_{0}^{\frac{B}{H}y} y dx dy$")
        self._explanation_centroid.append(r"　=$\int_{0}^{H} \frac{B}{H}y^2 dy$")
        self._explanation_centroid.append(r"　=$\left[\frac{B}{H} \cdot \frac{y^3}{3}\right]_0^{H}$")
        self._explanation_centroid.append(r"　=$\frac{BH^2}{3}$")
        self._explanation_centroid.append("断面積$A$を求めると，")
        self._explanation_centroid.append(r"$A$= $\int_{0}^{H} \int_{0}^{\frac{B}{H}y} dx dy$")
        self._explanation_centroid.append(r"　=$\int_{0}^{H} \frac{B}{H}y dy$")
        self._explanation_centroid.append(r"　=$\left[\frac{B}{H} \cdot \frac{y^2}{2}\right]_0^{H}$")
        self._explanation_centroid.append(r"　=$\frac{BH}{2}$")
        self._explanation_centroid.append("よって，重心の位置$y_g$は，")
        self._explanation_centroid.append(r"$y_g$ = $\frac{\int_A y dA}{\int_A dA}$ = $\frac{BH^2/3}{BH/2}$ = $\frac{2H}{3}$")
        self._centroid = (sp.sympify("2*H/3") ,2* self._height / 3)

    def get_moment_of_inertia(self):
        
        #print("Calculating moment of inertia for Triangle")

        self._explanation_moment_of_inertia = []

        self._explanation_moment_of_inertia.append("三角形の断面二次モーメント$I_z$は，定義式により，")
        self._explanation_moment_of_inertia.append(r"$I_z$ = $\int_{A} y^2 dA$")
        self._explanation_moment_of_inertia.append("ここで，高さを$H$，幅を$B$として，領域をy軸に沿うように変換し，")
        self._explanation_moment_of_inertia.append(r"　=$\int_{\frac{-2H}{3}}^{\frac{H}{3}} \int_{0}^{b(y)} y^2 dx dy$")
        self._explanation_moment_of_inertia.append(r"ここで，任意の$y$に対する幅$b(y)$は，")
        self._explanation_moment_of_inertia.append(r"$b(y) = \frac{B}{H}y + \frac{2B}{3}$")
        self._explanation_moment_of_inertia.append(r"　=$\int_{\frac{-2H}{3}}^{\frac{H}{3}} \left(\frac{B}{H}y + \frac{2B}{3}\right) y^2 dy$")
        self._explanation_moment_of_inertia.append(r"　=$B \int_{\frac{-2H}{3}}^{\frac{H}{3}} \left(\frac{y^3}{H} + \frac{2y^2}{3}\right) dy$")
        self._explanation_moment_of_inertia.append(r"　=$B \left[\frac{y^4}{4H} + \frac{2y^3}{9}\right]_{\frac{-2H}{3}}^{\frac{H}{3}}$")
        self._explanation_moment_of_inertia.append(r"　=$\frac{BH^3}{36}$")
        
        self._moment_of_inertia = (sp.sympify("B*H^3/36"), self._width * self._height ** 3 / 36)

    def generate_figure(self):
        initial_size = 60
        if self._base < self._height:
            height = initial_size
            base = self._base / self._height * initial_size
        else:
            base = initial_size
            height = self._height / self._base * initial_size

        padding = 5
        dim_v_x = 20 # 縦寸法線のX座標
        shape_left_x = 40
        center_x = shape_left_x + base / 2
        width_svg = shape_left_x + base + padding
        bottom = 95
        
        dwg = Figure(size=(width_svg, 100))

        points = [(shape_left_x, bottom), (shape_left_x + base, bottom), (center_x, bottom - height)]
        dwg.add(dwg.polygon(points=points, stroke="black", fill="none", stroke_width=1.5))

        #横の寸法線
        dwg.draw_arrow((shape_left_x, 20), (shape_left_x + base, 20))
        dwg.add(dwg.line((shape_left_x, 17), (shape_left_x, bottom), stroke=svgwrite.rgb(0, 0, 0), stroke_width=0.75, stroke_linecap="round"))
        dwg.add(dwg.line((shape_left_x + base, 17), (shape_left_x + base, bottom), stroke=svgwrite.rgb(0, 0, 0), stroke_width=0.75, stroke_linecap="round"))
        dwg.add(dwg.text(f"{self._base}", insert=(center_x, 15), fill=svgwrite.rgb(0, 0, 0), style="font-style:italic;font-family:Meiryo;text-anchor:middle"))

        #縦の寸法線
        dwg.draw_arrow((dim_v_x, bottom - height), (dim_v_x, bottom))
        dwg.add(dwg.line((center_x, bottom), (dim_v_x - 3, bottom), stroke=svgwrite.rgb(0, 0, 0), stroke_width=0.75, stroke_linecap="round"))
        dwg.add(dwg.line((center_x, bottom - height), (dim_v_x - 3, bottom - height), stroke=svgwrite.rgb(0, 0, 0), stroke_width=0.75, stroke_linecap="round"))
        
        text = dwg.text(str(self._height), insert=(dim_v_x - 3, bottom - height / 2), fill=svgwrite.rgb(0, 0, 0), style="font-style:italic;font-family:Meiryo;text-anchor:middle")
        text.rotate(270, center=(dim_v_x - 3, bottom - height / 2)) 
        dwg.add(text)
        self._figure = dwg


class HollowCircle(CrossSection):
    def __init__(self, outer_diameter, inner_diameter):
        """
        This class is used to define the cross section of a hollow circle.
        """
        super().__init__()
        self._outer_diameter = outer_diameter
        self._inner_diameter = inner_diameter
        self._outer_radius = outer_diameter / 2
        self._inner_radius = inner_diameter / 2

        self._name = "中空円形"
        self._dimensions = [self._outer_diameter, self._inner_diameter]
    
    @property
    def outer_diameter(self):
        return self._outer_diameter
    
    @property
    def inner_diameter(self):
        return self._inner_diameter

    def get_area(self):
        self._area = np.pi * (self._outer_radius ** 2 - self._inner_radius ** 2)
    
    def get_centroid(self):
        #print("Calculating centroid for HollowCircle")
        import sympy as sp
        self._explanation_centroid = []
        self._explanation_centroid.append("上下対象な断面の重心は中心に位置するが，ここでは丁寧に計算する。全体の円の直径を$D_o$，内側の円の直径を$D_i$とする。")
        self._explanation_centroid.append("断面の上端を原点として，$y$軸を下向きに定義し，該当の図形を大きな円から小さな円を引いた形状と考えると，断面一次モーメント$\sum_{i=1}^{n} y_{gi}  A_{i}$は，")
        self._explanation_centroid.append(r"$\sum_{i=1}^{n} y_{gi}  A_{i}$ = $ \frac{H}{2} \cdot \frac{\pi {D_o}^2}{4} - \frac{H}{2}  \cdot \frac{\pi {D_i}^2}{4}$")
        self._explanation_centroid.append(r"　=$\frac{\pi H}{8}({D_o}^2 - {D_i}^2)$")
        self._explanation_centroid.append("断面積$\sum_{i=1}^{n} A_i$を求めると，")
        self._explanation_centroid.append(r"$\sum_{i=1}^{n} A_i$= $\frac{\pi {D_o}^2}{4} - \frac{\pi {D_i}^2}{4}$")
        self._explanation_centroid.append(r"　=$\frac{\pi}{4}({D_o}^2 - {D_i}^2)$")
        self._explanation_centroid.append("よって，重心の位置$y_g$は，")
        self._explanation_centroid.append(r"$y_g$ = $\frac{\sum_{i=1}^{n} y_{gi}  A_{i}}{\sum_{i=1}^{n} A_i}$ = $\frac{\frac{\pi H}{8}({D_o}^2 - {D_i}^2)}{\frac{\pi}{4}({D_o}^2 - {D_i}^2)}$ = $H/2$")
        self._centroid = (sp.sympify("H/2"), self._outer_radius)

    def get_moment_of_inertia(self):
        import sympy as sp
        val = np.pi * (self._outer_radius ** 4 - self._inner_radius ** 4) / 4
        self._moment_of_inertia = (sp.sympify("pi*(Do^4-Di^4)/64"), val)
    
    def generate_figure(self):

        radius = 33
        padding = 5
        dim_v_x1 = 20 # 外部円寸法
        dim_v_x2 = 38 # 内部円寸法
        shape_left_x = 55
        center_x = shape_left_x + radius
        width_svg = center_x + radius + padding

        dwg = Figure(size=(width_svg, 120)) # 少し高さを広げる
        inner_r = self._inner_radius/self._outer_radius * radius
        dwg.add(dwg.circle(center=(center_x, 60), r= radius, stroke="black", fill="none", stroke_width=1.5))
        dwg.add(dwg.circle(center=(center_x, 60), r= inner_r, stroke="black", fill="none", stroke_width=1.5))

        #外部円の寸法線
        dwg.draw_arrow((dim_v_x1, 60-radius), (dim_v_x1, 60+radius))
        dwg.add(dwg.line((center_x, 60-radius), (dim_v_x1-3, 60-radius), stroke=svgwrite.rgb(0, 0, 0), stroke_width=0.75, stroke_linecap="round"))
        dwg.add(dwg.line((center_x, 60+radius), (dim_v_x1-3, 60+radius), stroke=svgwrite.rgb(0, 0, 0), stroke_width=0.75, stroke_linecap="round"))
        
        text = dwg.text(f"Φ{self._outer_diameter}", insert=(dim_v_x1-3, 60), fill=svgwrite.rgb(0, 0, 0), style="font-style:italic;font-family:Meiryo;text-anchor:middle")
        text.rotate(270, center=(dim_v_x1-3, 60))
        dwg.add(text)
        
        #内部円の寸法線
        dwg.draw_arrow((dim_v_x2, 60-inner_r), (dim_v_x2, 60+inner_r))
        dwg.add(dwg.line((center_x, 60-inner_r), (dim_v_x2-3, 60-inner_r), stroke=svgwrite.rgb(0, 0, 0), stroke_width=0.75, stroke_linecap="round"))
        dwg.add(dwg.line((center_x, 60+inner_r), (dim_v_x2-3, 60+inner_r), stroke=svgwrite.rgb(0, 0, 0), stroke_width=0.75, stroke_linecap="round"))
        
        text = dwg.text(f"Φ{self._inner_diameter}", insert=(dim_v_x2-3, 60), fill=svgwrite.rgb(0, 0, 0), style="font-style:italic;font-family:Meiryo;text-anchor:middle")
        text.rotate(270, center=(dim_v_x2-3, 60))
        dwg.add(text)

        self._figure = dwg

class HollowRectangle(CrossSection):
    def __init__(self, outer_width, outer_height, inner_width, inner_height):
        """
        This class is used to define the cross section of a hollow rectangle.
        """
        super().__init__()
        self._outer_width = outer_width
        self._outer_height = outer_height
        self._inner_width = inner_width
        self._inner_height = inner_height
        self._width = outer_width
        self._height = outer_height

        self._name = "中空矩形"
        self._dimensions = [self._outer_width, self._outer_height, self._inner_width, self._inner_height]

    def get_area(self):
        self._area = (self._outer_width * self._outer_height - self._inner_width * self._inner_height)

    def get_centroid(self):
        self._explanation_centroid = []
        self._explanation_centroid.append("上下左右対象な断面の重心は中心に位置するが，ここでは丁寧に計算する。全体の矩形から内側の矩形を引いた形状と考えると，断面一次モーメント$\sum_{i=1}^{n} y_{gi}  A_{i}$は，")
        self._explanation_centroid.append(r"$\sum_{i=1}^{n} y_{gi}  A_{i}$ = $ \frac{H}{2} \cdot B H - \frac{H}{2}  \cdot b h$")
        self._explanation_centroid.append(r"　=$\frac{H}{2}(B H - b h)$")
        self._explanation_centroid.append("断面積$\sum_{i=1}^{n} A_i$を求めると，")
        self._explanation_centroid.append(r"$\sum_{i=1}^{n} A_i$= $B H - b h$")
        self._explanation_centroid.append("よって，重心の位置$y_g$は，")
        self._explanation_centroid.append(r"$y_g$ = $\frac{\sum_{i=1}^{n} y_{gi}  A_{i}}{\sum_{i=1}^{n} A_i}$ = $\frac{\frac{H}{2}(B H - b h)}{B H - b h}$ = $H/2$")
        self._centroid = (sp.sympify("H/2"), self._outer_height / 2)

    def get_moment_of_inertia(self):

        #print("Calculating moment of inertia for HollowRectangle")
        self._explanation_moment_of_inertia = []
        self._explanation_moment_of_inertia.append("外側の，幅$B$，高さ$H$の矩形の断面二次モーメントは，")
        self._explanation_moment_of_inertia.append(r"$I_{z1}$ = $\frac{B H^3}{12}$")
        self._explanation_moment_of_inertia.append("内側の，幅$b$，高さ$h$の矩形の断面二次モーメントは，")
        self._explanation_moment_of_inertia.append(r"$I_{z2}$ = $\frac{b h^3}{12}$")
        self._explanation_moment_of_inertia.append("よって，中空矩形の断面二次モーメント$I_z$は，")
        self._explanation_moment_of_inertia.append(r"$I_z$ = $(I_{z1} + A_1 d_1^2) - (I_{z2} + A_2 d_2^2)$")
        self._explanation_moment_of_inertia.append("ここで，$A_1$，$A_2$はそれぞれ外側と内側の矩形の断面積，$d_1$，$d_2$はそれぞれ外側と内側の矩形の重心から中空矩形の重心までの距離で，")
        self._explanation_moment_of_inertia.append("　$d_1 = d_2 = 0$")
        self._explanation_moment_of_inertia.append("　$A_1 = B H$，$A_2 = b h$")
        self._explanation_moment_of_inertia.append("よって，上下対象断面の断面二次モーメントは，単純に互いの断面二次モーメントの差として求められ，")
        self._explanation_moment_of_inertia.append(r"$I_z$ = $\frac{B H^3}{12} - \frac{b h^3}{12}$= $\frac{1}{12}(B H^3 - b h^3)$")

        B, H, t, yg = sp.symbols('B H t yg')
        Iy = (B*t**3/12 + B*t*(t/2 - yg)**2 + t*(H - t)**3/12 + t*(H - t)*(t + (H + t)/2 - yg)**2)
        Iy = Iy.subs(yg, (B*t + H**2 - t**2)/(2*(B + H - t)))
        Iy_simplified = Iy #sp.simplify(Iy)
        self._moment_of_inertia = (sp.symbols("I_z"), Iy_simplified.subs({B: self._width, H: self._height, t: self._thickness}).evalf())


        self._inertia = (self._outer_width * self._outer_height ** 3 - self._inner_width * self._inner_height ** 3) / 12


    def generate_figure(self):

        initial_size = 45
        if self._outer_width < self._outer_height:
            height = initial_size
            width = self._outer_width / self._outer_height * initial_size
        else:
            width = initial_size
            height = self._outer_height / self._outer_width * initial_size

        padding = 5
        dim_v_x1 = 15 # 外部
        dim_v_x2 = 33 # 内部
        shape_left_x = 50
        center_x = shape_left_x + width / 2
        width_svg = shape_left_x + width + padding
        
        dwg = Figure(size=(width_svg, 100))

        dwg.add(dwg.rect(insert=(shape_left_x, (95-height)), size=(width, height), stroke="black", fill="none", stroke_width=1.5))

        inner_width = self._inner_width / self._outer_width * width
        inner_height = self._inner_height / self._outer_height * height
        dwg.add(dwg.rect(insert=(center_x-inner_width/2, (95-height/2-inner_height/2)), size=(inner_width, inner_height), stroke="black", fill="none", stroke_width=1.5))

        #外部矩形の寸法線（横）
        dwg.draw_arrow((shape_left_x, 20), (shape_left_x+width, 20))
        dwg.add(dwg.line((shape_left_x, 17), (shape_left_x, 95), stroke=svgwrite.rgb(0, 0, 0), stroke_width=0.75, stroke_linecap="round"))
        dwg.add(dwg.line((shape_left_x+width, 17), (shape_left_x+width, 95), stroke=svgwrite.rgb(0, 0, 0), stroke_width=0.75, stroke_linecap="round"))
        dwg.add(dwg.text(f'{self._outer_width}', insert=(center_x, 15), fill=svgwrite.rgb(0, 0, 0), style="font-family:Meiryo;text-anchor:middle", font_style="italic"))

        #外部矩形の寸法線(縦)
        dwg.draw_arrow((dim_v_x1, (95-height)), (dim_v_x1, 95))
        dwg.add(dwg.line((shape_left_x, 95), (dim_v_x1-3, 95), stroke=svgwrite.rgb(0, 0, 0), stroke_width=0.75, stroke_linecap="round"))
        dwg.add(dwg.line((shape_left_x, (95-height)), (dim_v_x1-3, (95-height)), stroke=svgwrite.rgb(0, 0, 0), stroke_width=0.75, stroke_linecap="round"))
        
        text = dwg.text(str(self._outer_height), insert=(dim_v_x1-3, (95-height/2)), fill=svgwrite.rgb(0, 0, 0), style="font-style:italic;font-family:Meiryo;text-anchor:middle")
        text.rotate(270, center=(dim_v_x1-3, (95-height/2)))
        dwg.add(text)

        #内部矩形の寸法線（横）
        dwg.draw_arrow((center_x-inner_width/2, 38), (center_x+inner_width/2, 38))
        dwg.add(dwg.line((center_x-inner_width/2, 35), (center_x-inner_width/2, 95-height/2), stroke=svgwrite.rgb(0, 0, 0), stroke_width=0.75, stroke_linecap="round"))
        dwg.add(dwg.line((center_x+inner_width/2, 35), (center_x+inner_width/2, 95-height/2), stroke=svgwrite.rgb(0, 0, 0), stroke_width=0.75, stroke_linecap="round"))
        dwg.add(dwg.text(f'{self._inner_width}', insert=(center_x, 33), fill=svgwrite.rgb(0, 0, 0), style="font-style:italic;font-family:Meiryo;text-anchor:middle"))
        
        #内部矩形の寸法線(縦)
        dwg.draw_arrow((dim_v_x2, (95-height/2-inner_height/2)), (dim_v_x2, (95-height/2+inner_height/2)))
        dwg.add(dwg.line((center_x, (95-height/2-inner_height/2)), (dim_v_x2-3, (95-height/2-inner_height/2)), stroke=svgwrite.rgb(0, 0, 0), stroke_width=0.75, stroke_linecap="round"))
        dwg.add(dwg.line((center_x, (95-height/2+inner_height/2)), (dim_v_x2-3, (95-height/2+inner_height/2)), stroke=svgwrite.rgb(0, 0, 0), stroke_width=0.75, stroke_linecap="round"))
        text = dwg.text(str(self._inner_height), insert=(dim_v_x2-3, (95-height/2)), fill=svgwrite.rgb(0, 0, 0), style="font-style:italic;font-family:Meiryo;text-anchor:middle")
        text.rotate(270, center=(dim_v_x2-3, (95-height/2)))
        dwg.add(text)

        self._figure = dwg
    

class TShape(CrossSection):
    def __init__(self, width, height, thickness):
        """
        This class is used to define the cross section of a T shape.
        """
        super().__init__()
        self._width = width
        self._height = height
        self._thickness = thickness

        self._name = "T型"

    def get_area(self):
        self._area = self._width * self._thickness + (self._height - self._thickness) * self._thickness    

    def get_centroid(self):
        #print("Calculating centroid for TShape")
        import sympy as sp
        self._explanation_centroid = []
        self._explanation_centroid.append("断面を上部と下部の2つの矩形に分割して考える。")
        self._explanation_centroid.append("上部の幅を$B$，全体の高さを$H$，厚さを$t$とすると，")
        self._explanation_centroid.append("上部の重心位置は$t/2$，断面積は$Bt$であり，下部の重心位置は$t+(H-t)/2= (H+t)/2$，断面積は$t(H-t)$である。")
        self._explanation_centroid.append("よって，断面一次モーメント$\sum_{i=1}^{n} y_{gi}  A_{i}$は，")
        self._explanation_centroid.append(r"$\sum_{i=1}^{n} y_{gi}  A_{i}$ = $ \frac{t}{2} \cdot Bt + \frac{H+t}{2} \cdot t(H-t)$")
        self._explanation_centroid.append(r"　=$\frac{Bt^2}{2} + \frac{t(H^2 - t^2)}{2}$")
        self._explanation_centroid.append("断面積$\sum_{i=1}^{n} A_i$を求めると，")
        self._explanation_centroid.append(r"$\sum_{i=1}^{n} A_i$= $Bt + t(H-t)$")
        self._explanation_centroid.append(r"　=$t(B + H - t)$")
        self._explanation_centroid.append("よって，重心の位置$y_g$は，")
        self._explanation_centroid.append(r"$y_g$ = $\frac{\sum_{i=1}^{n} y_{gi}  A_{i}}{\sum_{i=1}^{n} A_i}$ = $\frac{\frac{Bt^2}{2} + \frac{t(H^2 - t^2)}{2}}{t(B + H - t)}$=$\frac{Bt + H^2 - t^2}{2(B + H - t)}$")
        self._centroid = (
            sp.sympify("y_g"), #sp.sympify("(B*t + H**2 - t**2)/(2*(B + H - t))"), 
            (self._width * self._thickness ** 2 / 2 + self._thickness * (self._height ** 2 - self._thickness ** 2) / 2) / (self._thickness * (self._width + self._height - self._thickness))
        )

    def get_moment_of_inertia(self):
        #print("Calculating moment of inertia for TShape")
        self._explanation_moment_of_inertia = []
        self._explanation_moment_of_inertia.append("上部の，幅$B$，厚さ$t$の矩形の断面二次モーメントは，上部の長方形の図心を中心とすれば，")
        self._explanation_moment_of_inertia.append(r"　$I_{z1}$ = $\frac{Bt^3}{12}$")
        self._explanation_moment_of_inertia.append("下部の，厚さ$t$，高さ$H-t$の矩形の断面二次モーメントは，下部の長方形の図心を中心とすれば，")
        self._explanation_moment_of_inertia.append(r"　$I_{z2}$ = $\frac{t(H-t)^3}{12}$")
        self._explanation_moment_of_inertia.append("よって，断面全体の断面二次モーメント$I_z$は，平行軸の定理より，")
        self._explanation_moment_of_inertia.append(r"　$I_z$ = $I_{z1} + A_1 d_1^2 + I_{z2} + A_2 d_2^2$")
        self._explanation_moment_of_inertia.append("ここで，$A_1$，$A_2$はそれぞれ上部と下部の断面積，$d_1$，$d_2$はそれぞれ上部と下部の図心から断面全体の図心までの距離で，")
        self._explanation_moment_of_inertia.append(r"　$A_1$ = $Bt$，$d_1$ = $\frac{t}{2} - y_g$")
        self._explanation_moment_of_inertia.append(r"　$A_2$ = $t(H-t)$，$d_2$ = $t + \frac{H-t}{2} - y_g$")
        self._explanation_moment_of_inertia.append("これらを用いて式を整理すると，")
        self._explanation_moment_of_inertia.append(r"　$I_z$ = $\frac{Bt^3}{12} + Bt(\frac{t}{2} - y_g)^2 + \frac{t(H-t)^3}{12} + t(H-t)(t + \frac{H-t}{2} - y_g)^2$")

        B, H, t, yg = sp.symbols('B H t yg')
        Iy = (B*t**3/12 + B*t*(t/2 - yg)**2 + t*(H - t)**3/12 + t*(H - t)*(t + (H - t)/2 - yg)**2)
        Iy = Iy.subs(yg, (B*t + H**2 - t**2)/(2*(B + H - t)))
        Iy_simplified = Iy #sp.simplify(Iy)
        self._moment_of_inertia = (sp.symbols("I_z"), Iy_simplified.subs({B: self._width, H: self._height, t: self._thickness}).evalf())

    def generate_figure(self):
        
        initial_size = 65
        if self._width < self._height:
            height = initial_size
            width = self._width / self._height * initial_size
            thickness = self._thickness / self._height * initial_size
        else:
            width = initial_size
            height = self._height / self._width * initial_size
            thickness = self._thickness / self._width * initial_size

        padding = 5
        dim_v_x = 15 # 縦寸法線
        dim_t_x = 33 # 厚さ寸法線
        shape_left_x = 50
        center_x = shape_left_x + width / 2
        bottom = 95
        width_svg = shape_left_x + width + padding

        dwg = Figure(size=(width_svg, 100))

        # T 型断面の座標
        points = [(center_x-width/2, bottom-height), (center_x+width/2, bottom-height), 
                  (center_x+width/2, bottom-height+thickness), (center_x+thickness/2, bottom-height+thickness), 
                  (center_x+thickness/2, bottom), (center_x-thickness/2, bottom), 
                  (center_x-thickness/2, bottom-height+thickness), (center_x-width/2, bottom-height+thickness)]

        # polygon 要素を追加
        polygon = dwg.polygon(points=points, stroke="black", fill="none", stroke_width=1.5)
        dwg.add(polygon)


        #矩形の寸法線（横）
        dwg.draw_arrow((center_x-width/2, 20), (center_x+width/2, 20))
        dwg.add(dwg.line((center_x-width/2, 17), (center_x-width/2, bottom-height), stroke=svgwrite.rgb(0, 0, 0), stroke_width=0.75, stroke_linecap="round"))
        dwg.add(dwg.line((center_x+width/2, 17), (center_x+width/2, bottom-height), stroke=svgwrite.rgb(0, 0, 0), stroke_width=0.75, stroke_linecap="round"))
        dwg.add(dwg.text(f'{self._width}', insert=(center_x, 15), fill=svgwrite.rgb(0, 0, 0), style="font-family:Meiryo;text-anchor:middle", font_style="italic"))

        #矩形の寸法線(縦)
        dwg.draw_arrow((dim_v_x, (bottom-height)), (dim_v_x, bottom))
        dwg.add(dwg.line((center_x, bottom), (dim_v_x-3, bottom), stroke=svgwrite.rgb(0, 0, 0), stroke_width=0.75, stroke_linecap="round"))
        dwg.add(dwg.line((center_x, (bottom-height)), (dim_v_x-3, (bottom-height)), stroke=svgwrite.rgb(0, 0, 0), stroke_width=0.75, stroke_linecap="round"))
        
        text = dwg.text(str(self._height), insert=(dim_v_x-3, (bottom-height/2)), fill=svgwrite.rgb(0, 0, 0), style="font-style:italic;font-family:Meiryo;text-anchor:middle")
        text.rotate(270, center=(dim_v_x-3, (bottom-height/2)))
        dwg.add(text)

        #幅の寸法線
        dwg.draw_arrow((dim_t_x ,bottom-height), (dim_t_x, bottom-height+thickness))
        dwg.add(dwg.line((center_x-width/2, bottom-height+thickness), (dim_t_x-3, bottom-height+thickness), stroke=svgwrite.rgb(0, 0, 0), stroke_width=0.75, stroke_linecap="round"))
        dwg.add(dwg.line((center_x-width/2, bottom-height), (dim_t_x-3, bottom-height), stroke=svgwrite.rgb(0, 0, 0), stroke_width=0.75, stroke_linecap="round"))
        
        text = dwg.text(f'{self._thickness}', insert=(dim_t_x-3, bottom-height+thickness/2), fill=svgwrite.rgb(0, 0, 0), style="font-style:italic;font-family:Meiryo;text-anchor:middle")
        text.rotate(270, center=(dim_t_x-3, bottom-height+thickness/2))
        dwg.add(text)

        self._figure = dwg


class UShape(CrossSection):
    def __init__(self, width, height, thickness):
        """
        This class is used to define the cross section of a U shape.
        """
        super().__init__()
        self._width = width
        self._height = height
        self._thickness = thickness

        self._name = "U型"

    def get_area(self):
        self._area = (self._width * self._thickness + (self._height - self._thickness) * self._thickness * 2)
    
    def get_centroid(self):
        #print("Calculating centroid for UShape")
        self._explanation_centroid = []
        self._explanation_centroid.append("断面の全体の高さを$H$，幅を$B$，肉厚を$t$とする。")
        self._explanation_centroid.append("断面を高さ$H$，幅$B$の矩形から，高さ$H-t$，幅$B-2t$の矩形を引いた形状と考える。")
        self._explanation_centroid.append(r"断面一次モーメント$\sum_{i=1}^{n} y_{gi}  A_{i}$は，")
        self._explanation_centroid.append(r"$\sum_{i=1}^{n} y_{gi}  A_{i}$ = $ \frac{H}{2} \cdot BH - \left(t + \frac{H - t}{2}  \right) \cdot (B - 2t)(H - t)$")
        self._explanation_centroid.append(r"　=$\frac{BH^2}{2} - \frac{(H + t)(B - 2t)(H - t)}{2}$")
        self._explanation_centroid.append(r"　=$ \frac{BH^2}{2} - \frac{(B - 2t)(H^2 - t^2)}{2}$")
        self._explanation_centroid.append(r"　=$ \frac{B H^2}{2} - \frac{B H^2 - B t^2 - 2t H^2 + 2t^3}{2}$")
        self._explanation_centroid.append(r"　=$ \frac{B t^2 + 2t H^2 - 2t^3}{2}$")
        self._explanation_centroid.append(r"断面積$\sum_{i=1}^{n} A_i$を求めると，")
        self._explanation_centroid.append(r"$\sum_{i=1}^{n} A_i$= $BH - (B - 2t)(H - t)$")
        self._explanation_centroid.append(r"　=$Bt - 2tH - 2t^2$")
        self._explanation_centroid.append("よって，重心の位置$y_g$は，")
        self._explanation_centroid.append(r"$y_g$ = $\frac{B t + 2H^2 - 2t^2}{2(2H + B - 2t)}$")
        self._centroid = (sp.sympify("(B*t + 2*H**2 - 2*t**2)/(2*(2*H + B - 2*t))"), (self._width * self._thickness + 2 * self._height ** 2 - 2 * self._thickness ** 2) / (2 * (2 * self._height + self._width - 2 * self._thickness)))

    def generate_figure(self):
        dwg = Figure()
        initial_size = 65
        if self._width < self._height:
            height = initial_size
            width = self._width / self._height * initial_size
            thickness = self._thickness / self._height * initial_size
        else:
            width = initial_size
            height = self._height / self._width * initial_size
            thickness = self._thickness / self._width * initial_size


        # U 型断面の座標
        points = [(81-width/2, 95-height), (81+width/2, 95-height), 
                  (81+width/2, 95), (81+width/2-thickness, 95), 
                  (81+width/2-thickness, 95-height+thickness), (81-width/2+thickness, 95-height+thickness), 
                  (81-width/2+thickness, 95), (81-width/2, 95)]

        # polygon 要素を追加
        polygon = dwg.polygon(points=points, stroke="black", fill="none", stroke_width=1.5)
        dwg.add(polygon)

        #寸法線（横）
        dwg.draw_arrow((81-width/2, 20), (81+width/2, 20))
        dwg.add(dwg.line((81-width/2, 17), (81-width/2, 95-height), stroke=svgwrite.rgb(0, 0, 0), stroke_width=0.75, stroke_linecap="round"))
        dwg.add(dwg.line((81+width/2, 17), (81+width/2, 95-height), stroke=svgwrite.rgb(0, 0, 0), stroke_width=0.75, stroke_linecap="round"))
        offset = len(str(self._width))*8.0/2
        dwg.add(dwg.text(f'{self._width}', insert=(81 - offset, 15), fill=svgwrite.rgb(0, 0, 0), font_family="Meiryo", font_style="italic"))

        #寸法線(縦)
        dwg.draw_arrow((15, (95-height)), (15, 95))
        dwg.add(dwg.line((81-width/2, 95), (12, 95), stroke=svgwrite.rgb(0, 0, 0), stroke_width=0.75, stroke_linecap="round"))
        dwg.add(dwg.line((81-width/2, (95-height)), (12, (95-height)), stroke=svgwrite.rgb(0, 0, 0), stroke_width=0.75, stroke_linecap="round"))
        offset = len(str(self._height)) * 7/2
        text = dwg.text(str(self._height), insert=(15-offset, (95-height/2)-5), fill=svgwrite.rgb(0, 0, 0), style="font-style:italic;font-family:Meiryo")
        text.rotate(270, center=(15, (95-height/2)))
        dwg.add(text)

        #厚さの寸法線
        dwg.draw_arrow((33 ,95-height), (33, 95-height+thickness))
        dwg.add(dwg.line((81-width/2, 95-height+thickness), (30, 95-height+thickness), stroke=svgwrite.rgb(0, 0, 0), stroke_width=0.75, stroke_linecap="round"))
        dwg.add(dwg.line((81-width/2, 95-height), (30, 95-height), stroke=svgwrite.rgb(0, 0, 0), stroke_width=0.75, stroke_linecap="round"))
        offset = len(str(self._thickness))*8.0/2
        text = dwg.text(f'{self._thickness}', insert=(33 - offset, 95-height+thickness/2-5), fill=svgwrite.rgb(0, 0, 0), style="font-style:italic;font-family:Meiryo")
        text.rotate(270, center=(33, 95-height+thickness/2))
        dwg.add(text)

        self._figure = dwg

class HouseShape(CrossSection):
    def __init__(self, width, rect_height, triangle_height):
        """
        This class is used to define the cross section of a house shape.
        """
        super().__init__()
        self._width = width
        self._rect_height = rect_height
        self._triangle_height = triangle_height
        self._height = rect_height + triangle_height

        self._name = "家形断面"
        self._dimensions = [self._width, self._height]

    def get_centroid(self):
        #print("Calculating centroid for HouseShape")
        self._explanation_centroid = []
        self._explanation_centroid.append("断面を矩形部分と三角形部分に分割して考える。")
        self._explanation_centroid.append("矩形部分の幅を$B$，矩形部分の高さを$H_r$，三角形部分の高さを$H_t$とすると，")
        self._explanation_centroid.append("矩形部分の重心位置は$H_r/2$，断面積は$B H_r$であり，三角形部分の重心位置は$H_r + H_t/3$，断面積は$B H_t/2$である。")
        self._explanation_centroid.append("よって，断面一次モーメント$\sum_{i=1}^{n} y_{gi}  A_{i}$は，")
        self._explanation_centroid.append(r"$\sum_{i=1}^{n} y_{gi}  A_{i}$ = $ \frac{H_r}{2} \cdot B H_r + \left(H_r + \frac{H_t}{3}\right) \cdot \frac{B H_t}{2}$")
        self._explanation_centroid.append(r"　=$\frac{B H_r^2}{2} + \frac{B H_t (6H_r + H_t)}{6}$")
        self._explanation_centroid.append("断面積$\sum_{i=1}^{n} A_i$を求めると，")
        self._explanation_centroid.append(r"$\sum_{i=1}^{n} A_i$= $B H_r + \frac{B H_t}{2}$")
        self._explanation_centroid.append(r"　=$B \left(H_r + \frac{H_t}{2}\right)$")
        self._explanation_centroid.append("よって，重心の位置$y_g$は，")
        self._explanation_centroid.append(r"$y_g$ = $\frac{\sum_{i=1}^{n} y_{gi}  A_{i}}{\sum_{i=1}^{n} A_i}$ = $\frac{\frac{B H_r^2}{2} + \frac{B H_t (3H_r + 2H_t)}{6}}{B \left(H_r + \frac{H_t}{2}\right)}$=$\frac{3H_r^2 + H_t(3H_r + 2H_t)}{6(H_r + H_t/2)}$")
        self._centroid = (sp.sympify("(H_r^2 + H_t*(3*H_r + 2*H_t))/(3*(2*H_r + H_t))"), 
                          (self._rect_height ** 2 + self._triangle_height * (3 * self._rect_height + self._triangle_height)/3) / ((2*self._rect_height + self._triangle_height)))

    def generate_figure(self):
        dwg = Figure()
        initial_size = 65

        if self._width < self._height:
            height = initial_size
            width = self._width / self._height * initial_size
            rect_height = self._rect_height / self._height * initial_size
            triangle_height = self._triangle_height / self._height * initial_size
        else:
            width = initial_size
            height = self._height / self._width * initial_size
            rect_height = self._rect_height / self._width * initial_size
            triangle_height = self._triangle_height / self._width * initial_size

        # 家形断面の座標
        points = [(81 - width / 2, 95 - height), (81 + width / 2, 95 - height),
                  (81 + width / 2, 95 - triangle_height), (81, 95),
                  (81 - width / 2, 95 - triangle_height)]
        # polygon 要素を追加
        polygon = dwg.polygon(points=points, stroke="black", fill="none", stroke_width=1.5)
        dwg.add(polygon)

        #幅の寸法線（横）
        dwg.draw_arrow((81 - width / 2, 20), (81 + width / 2, 20))
        dwg.add(dwg.line((81 - width / 2, 17), (81 - width / 2, 95-height), stroke=svgwrite.rgb(0, 0, 0), stroke_width=0.75, stroke_linecap="round"))
        dwg.add(dwg.line((81 + width / 2, 17), (81 + width / 2, 95-height), stroke=svgwrite.rgb(0, 0, 0), stroke_width=0.75, stroke_linecap="round"))
        dwg.add(dwg.text(f'{self._width}', insert=(81, 15), fill=svgwrite.rgb(0, 0, 0), font_family="Meiryo", style="font-style:italic;font-family:Meiryo; text-anchor:middle; alignment-baseline:middle"))

        #高さの寸法線（上の四角形）
        dwg.draw_arrow((33, 95 - triangle_height), (33, 95))
        dwg.add(dwg.line((81-width/2, 95), (30, 95), stroke=svgwrite.rgb(0, 0, 0), stroke_width=0.75, stroke_linecap="round"))
        dwg.add(dwg.line((81-width/2, 95 - triangle_height), (30, 95 - triangle_height), stroke=svgwrite.rgb(0, 0, 0), stroke_width=0.75, stroke_linecap="round"))
        dwg.add(dwg.text(str(self._rect_height), insert=(25, (95 - rect_height / 2 - triangle_height)), fill=svgwrite.rgb(0, 0, 0), style="font-style:italic;font-family:Meiryo; text-anchor:middle; alignment-baseline:middle",transform=f"rotate(270, 25, {95 - rect_height / 2 - triangle_height})"))

        #高さの寸法線（三角形部分）
        dwg.draw_arrow((33, 95 - height), (33, 95 - triangle_height))
        dwg.add(dwg.line((81-width/2, 95 - triangle_height), (30, 95 - triangle_height), stroke=svgwrite.rgb(0, 0, 0), stroke_width=0.75, stroke_linecap="round"))
        dwg.add(dwg.line((81-width/2, 95 - height), (30, 95 - height), stroke=svgwrite.rgb(0, 0, 0), stroke_width=0.75, stroke_linecap="round"))
        dwg.add(dwg.text(str(self._triangle_height), insert=(25, (95 - triangle_height/ 2)), fill=svgwrite.rgb(0, 0, 0), style="font-style:italic;font-family:Meiryo; text-anchor:middle; alignment-baseline:middle",transform=f"rotate(270, 25, {95 - triangle_height / 2})"))
        self._figure = dwg

if __name__ == "__main__":
    circle = Circle(100)
    print(circle.area)
    print(circle.inertia)
    print(circle.figure)

    rectangle = Rectangle(100, 50)
    print(rectangle.area)
    print(rectangle.inertia)

    hollow_circle = HollowCircle(100, 80)
    print(hollow_circle.area)
    print(hollow_circle.inertia)

    hollow_rectangle = HollowRectangle(100, 50, 80, 40)
    print(hollow_rectangle.area)
    print(hollow_rectangle.inertia)