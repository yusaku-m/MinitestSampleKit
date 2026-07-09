import sys
import numpy as np
import svgwrite

import matplotlib.pyplot as plt
import svgwrite.drawing
import sympy as sp

"""
作りかけ。領域の自動処理がむずい。
"""

#from .Figure import Figure

class Region():
    """
    This class is used to define the region of a section.
    equations: list of sympy equations.
    """
    def __init__(self, equations):
        self._equations = equations
        self._figure = None
    
    @property
    def figure(self):
        """
        This method is used to get the figure of the cross section.
        """

        if self._figure is None:
            self.generate_figure()

        return self._figure
   
    @property
    def equations(self):
        return self._equations

    def caluclate_cross_points(self):
        """
        与えられた数式のペア全ての交点を計算します。
        """
        x, y = sp.symbols('x y')
        equations = self._equations
        num_eq = len(equations)
        cross_points = []
        
        # 全てのペアについて交点を計算
        for i in range(num_eq):
            for j in range(i + 1, num_eq):
                eq1 = equations[i]
                eq2 = equations[j]
                
                # 連立方程式を解く (x, yについて)
                # sympy.solveはリスト、タプル、またはディクショナリで解を返します
                solutions = sp.solve((eq1, eq2), (x, y))
                
                if isinstance(solutions, dict):
                    # 解が1組の場合
                    solutions = [solutions]
                elif not solutions or isinstance(solutions[0], (sp.Equality, tuple)):
                    # 解がないか、または解が表現できない形式の場合（例：恒等式）はスキップ
                    pass
                
                for sol in solutions:
                    # 解が数値であることを確認し、リストに追加
                    if sol[x].is_real and sol[y].is_real:
                        cross_points.append((sol[x], sol[y]))
        
        # 重複する交点を削除 (数値比較の誤差を考慮しない簡易な方法)
        unique_points = []
        seen = set()
        for p in cross_points:
            # タプルを文字列に変換してセットに追加 (数値評価を使用)
            str_p = f"({sp.N(p[0]):.5f}, {sp.N(p[1]):.5f})"
            if str_p not in seen:
                seen.add(str_p)
                unique_points.append(p)
                
        return unique_points
   
    def get_integration_limits(self):
        """
        与えられた数式で囲まれた領域の積分範囲を求めます (dx dy 順)。
        出力形式: (sy, ey, sx, ex)
        """
        x, y = sp.symbols('x y')
        equations = self._equations
        
        # 1. 交点の計算
        cross_points = self.caluclate_cross_points()
        
        if not cross_points:
            return None # 領域が閉じられていない、または交点がない
        
        # 2. yの積分範囲 (sy, ey) を決定
        # 全ての交点のy座標の最小値と最大値
        y_coords = [p[1] for p in cross_points]
        sy = sp.Min(*y_coords)
        ey = sp.Max(*y_coords)
        
        # 3. xの積分範囲 (sx, ex) を決定 (yの関数)
        
        # 各方程式を y の関数として x について解く。
        # 例: sp.Eq(y, x) -> x = y
        # 例: sp.Eq(x, 0) -> x = 0
        x_solutions = []
        for eq in equations:
            # eq.lhs - eq.rhs = 0 の形を仮定し、x について解く
            sol = sp.solve(eq, x) 
            # sol は解のリスト
            x_solutions.extend(sol)
            
        # x の下限 sx(y) は全ての解の最小値、上限 ex(y) は全ての解の最大値
        # 領域が凸であることを仮定した場合、境界はこれらの解の関数で与えられる
        
        if not x_solutions:
             return None # xについて解ける方程式がない
             
        sx = sp.Min(*x_solutions)
        ex = sp.Max(*x_solutions)
        
        # 出力形式: (sy, ey, sx, ex)
        return (sy, ey, sx, ex)

    def generate_figure(self):
        # draw x and y axis
        pass

import sympy as sp

def region_from_boundaries(equations, x, y):
    # --- Step 1: 全ての交点を求める ---
    points = []
    n = len(equations)
    for i in range(n):
        for j in range(i+1, n):
            sol = sp.solve([equations[i], equations[j]], (x, y), dict=True)
            for s in sol:
                if s[x].is_real and s[y].is_real:
                    points.append((sp.simplify(s[x]), sp.simplify(s[y])))

    if not points:
        raise ValueError("交点が見つかりません。領域が閉じていない可能性があります。")

    # x 座標の最小・最大
    xs = [p[0] for p in points]
    xmin, xmax = min(xs), max(xs)

    # --- Step 2: y = f(x) 形式を抽出 ---
    y_funcs = []
    for eq in equations:
        try:
            sol = sp.solve(eq, y)
            for f in sol:
                y_funcs.append(f)
        except:
            pass

    if not y_funcs:
        raise ValueError("y = f(x) 形式に変換できる境界がありません。")

    # --- Step 3: 任意の x で上下境界を決める関数 ---
    def y_bounds(x_val):
        yvals = [f.subs(x, x_val) for f in y_funcs]
        yvals = [yv for yv in yvals if yv.is_real]
        if not yvals:
            raise ValueError("指定した x で y 値が得られません。")
        return min(yvals), max(yvals)

    # 結果として「x は xmin〜xmax、y は ymin(x)〜ymax(x)」を返す
    ymin = sp.Lambda(x, y_bounds(x)[0])
    ymax = sp.Lambda(x, y_bounds(x)[1])

    return xmin, xmax, ymin, ymax


if __name__ == "__main__":

    x, y = sp.symbols('x y')
    eq1 = sp.Eq(y, 0)
    eq2 = sp.Eq(x, 0)
    eq3 = sp.Eq(y, -x+1)

    equations = [eq1, eq2, eq3]
    region = Region(equations)
    print(region_from_boundaries(equations, x, y))

