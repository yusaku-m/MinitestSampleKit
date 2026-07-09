class BeamFormula:
    def __init__(self, name, thetaL_latex, thetaR_latex, delta_latex, thetaL_func, thetaR_func, delta_func):
        """
        梁の公式を管理するクラス
        name: 梁のモデル名
        thetaL_latex: 左端たわみ角のLaTeX形式
        thetaR_latex: 右端たわみ角のLaTeX形式
        delta_latex: たわみ量のLaTeX形式
        thetaL_func: 左端たわみ角を計算する関数 (P, L, a, D 等を引数にとる)
        thetaR_func: 右端たわみ角を計算する関数 (P, L, a, D 等を引数にとる)
        delta_func: たわみ量を計算する関数 (P, L, a, D 等を引数にとる)
        """
        self.name = name
        self.thetaL_latex = thetaL_latex
        self.thetaR_latex = thetaR_latex
        self.delta_latex = delta_latex
        self.thetaL_func = thetaL_func
        self.thetaR_func = thetaR_func
        self.delta_func = delta_func

    @property
    def theta_latex(self):
        return self.thetaL_latex

    @property
    def theta_func(self):
        return self.thetaL_func

# 14種類の梁モデルのレジストリ
BEAM_REGISTRY = {
    # --- 片持ち梁 (Cantilever: C) ---
    "C_P_end": BeamFormula(
        "片持ち梁・自由端集中荷重",
        r"\theta = \frac{PL^2}{2D}",
        r"\theta = \frac{PL^2}{2D}",
        r"\delta = \frac{PL^3}{3D}",
        lambda P, L, D: P * L**2 / (2 * D),
        lambda P, L, D: P * L**2 / (2 * D),
        lambda P, L, D: P * L**3 / (3 * D)
    ),
    "C_P_a": BeamFormula(
        "片持ち梁・任意位置集中荷重",
        r"\theta = \frac{P(L-a)^2}{2D}",
        r"\theta = \frac{P(L-a)^2}{2D}",
        r"\delta = \frac{PL^3}{6D}\left(1-\frac{a}{L}\right)^2\left(2+\frac{a}{L}\right)",
        lambda P, L, a, D: P * (L - a)**2 / (2 * D),
        lambda P, L, a, D: P * (L - a)**2 / (2 * D),
        lambda P, L, a, D: (P * L**3 / (6 * D)) * (1 - a/L)**2 * (2 + a/L)
    ),
    "C_w_all": BeamFormula(
        "片持ち梁・全体に等分布荷重",
        r"\theta = \frac{w_0 L^3}{6D}",
        r"\theta = \frac{w_0 L^3}{6D}",
        r"\delta = \frac{w_0 L^4}{8D}",
        lambda w0, L, D: w0 * L**3 / (6 * D),
        lambda w0, L, D: w0 * L**3 / (6 * D),
        lambda w0, L, D: w0 * L**4 / (8 * D)
    ),
    "C_w_b": BeamFormula(
        "片持ち梁・自由端から$a$離れた位置までに等分布荷重",
        r"\theta = \frac{w_0 L^3}{6D}\left(1-\frac{b^3}{L^3}\right)",
        r"\theta = \frac{w_0 L^3}{6D}\left(1-\frac{b^3}{L^3}\right)",
        r"\delta = \frac{w_0 L^4}{24D}\left(3-4\frac{b^3}{L^3}+\frac{b^4}{L^4}\right)",
        lambda w0, L, b, D: (w0 * L**3 / (6 * D)) * (1 - b**3 / L**3),
        lambda w0, L, b, D: (w0 * L**3 / (6 * D)) * (1 - b**3 / L**3),
        lambda w0, L, b, D: (w0 * L**4 / (24 * D)) * (3 - 4 * b**3 / L**3 + b**4 / L**4)
    ),
    "C_w_tri": BeamFormula(
        "片持ち梁・全体に三角形分布荷重",
        r"\theta = \frac{w_0 L^3}{24D}",
        r"\theta = \frac{w_0 L^3}{24D}",
        r"\delta = \frac{w_0 L^4}{30D}",
        lambda w0, L, D: w0 * L**3 / (24 * D),
        lambda w0, L, D: w0 * L**3 / (24 * D),
        lambda w0, L, D: w0 * L**4 / (30 * D)
    ),
    "C_M_end": BeamFormula(
        "片持ち梁・自由端集中モーメント",
        r"\theta = \frac{M_c L}{D}",
        r"\theta = \frac{M_c L}{D}",
        r"\delta = \frac{M_c L^2}{2D}",
        lambda Mc, L, D: Mc * L / D,
        lambda Mc, L, D: Mc * L / D,
        lambda Mc, L, D: Mc * L**2 / (2 * D)
    ),
    "C_M_a": BeamFormula(
        "片持ち梁・任意位置集中モーメント",
        r"\theta = \frac{M_c(L-a)}{D}",
        r"\theta = \frac{M_c(L-a)}{D}",
        r"\delta = \frac{M_c(L^2-a^2)}{2D}",
        lambda Mc, L, a, D: Mc * (L - a) / D,
        lambda Mc, L, a, D: Mc * (L - a) / D,
        lambda Mc, L, a, D: Mc * (L**2 - a**2) / (2 * D)
    ),

    # --- 単純支持梁 (Simply Supported: S) ---
    "S_P_center": BeamFormula(
        "単純支持梁・中央集中荷重",
        r"\theta = \frac{PL^2}{16D}",
        r"\theta = \frac{PL^2}{16D}",
        r"\delta = \frac{PL^3}{48D}",
        lambda P, L, D: P * L**2 / (16 * D),
        lambda P, L, D: P * L**2 / (16 * D),
        lambda P, L, D: P * L**3 / (48 * D)
    ),
    "S_P_a": BeamFormula(
        "単純支持梁・任意位置集中荷重",
        r"\theta_L = \frac{Pb}{6DL}(L^2-b^2)",
        r"\theta_R = \frac{Pa}{6DL}(L^2-a^2)",
        r"\delta = \frac{Pa^2b^2}{3DL}",
        lambda P, L, a, b, D: P * b * (L**2 - b**2) / (6 * D * L),
        lambda P, L, a, b, D: P * a * (L**2 - a**2) / (6 * D * L),
        lambda P, L, a, b, D: P * a**2 * b**2 / (3 * D * L)
    ),
    "S_w_all": BeamFormula(
        "単純支持梁・全体に等分布荷重",
        r"\theta = \frac{w_0 L^3}{24D}",
        r"\theta = \frac{w_0 L^3}{24D}",
        r"\delta = \frac{5w_0 L^4}{384D}",
        lambda w0, L, D: w0 * L**3 / (24 * D),
        lambda w0, L, D: w0 * L**3 / (24 * D),
        lambda w0, L, D: 5 * w0 * L**4 / (384 * D)
    ),
    "S_w_b": BeamFormula(
        "単純支持梁・左端から$a$離れた位置までに等分布荷重",
        r"\theta_L = \frac{w_0 a^2(2L-a)^2}{24LD}",
        r"\theta_R = \frac{w_0 a^2(2L^2-a^2)}{24LD}",
        r"\delta_{max}",
        lambda w0, L, a, b, D: w0 * a**2 * (2 * L - a)**2 / (24 * L * D),
        lambda w0, L, a, b, D: w0 * a**2 * (2 * L**2 - a**2) / (24 * L * D),
        lambda w0, L, a, b, D: 0 # 複雑なため省略
    ),
    "S_w_tri": BeamFormula(
        "単純支持梁・全体に三角形分布荷重",
        r"\theta_L = \frac{7w_0 L^3}{360D}",
        r"\theta_R = \frac{8w_0 L^3}{360D} = \frac{w_0 L^3}{45D}",
        r"\delta = \frac{w_0 L^4}{120D}",
        lambda w0, L, D: 7 * w0 * L**3 / (360 * D),
        lambda w0, L, D: 8 * w0 * L**3 / (360 * D),
        lambda w0, L, D: w0 * L**4 / (120 * D)
    ),
    "S_M_ends": BeamFormula(
        "単純支持梁・両端集中モーメント",
        r"\theta_L = \frac{(2M_A+M_B)L}{6D}",
        r"\theta_R = \frac{(M_A+2M_B)L}{6D}",
        r"\delta_{max}",
        lambda MA, MB, L, D: (2 * MA + MB) * L / (6 * D),
        lambda MA, MB, L, D: (MA + 2 * MB) * L / (6 * D),
        lambda MA, MB, L, D: 0 # 複雑なため省略
    ),
    "S_M_a": BeamFormula(
        "単純支持梁・任意位置集中モーメント",
        r"\theta_L = \frac{M_c}{6DL}(L^2-3b^2)",
        r"\theta_R = \frac{M_c}{6DL}(L^2-3a^2)",
        r"\delta_{max}",
        lambda Mc, L, a, b, D: Mc * (L**2 - 3 * b**2) / (6 * D * L),
        lambda Mc, L, a, b, D: Mc * (L**2 - 3 * a**2) / (6 * D * L),
        lambda Mc, L, a, b, D: 0 # 複雑なため省略
    ),
    "S_M_left": BeamFormula(
        "単純支持梁・左端集中モーメント",
        r"\theta_L = \frac{M_L L}{3D}",
        r"\theta_R = \frac{M_L L}{6D}",
        r"\delta_{max}",
        lambda ML, L, D: ML * L / (3 * D),
        lambda ML, L, D: ML * L / (6 * D),
        lambda ML, L, D: 0
    ),
    "S_M_right": BeamFormula(
        "単純支持梁・右端集中モーメント",
        r"\theta_L = \frac{M_R L}{6D}",
        r"\theta_R = \frac{M_R L}{3D}",
        r"\delta_{max}",
        lambda MR, L, D: MR * L / (6 * D),
        lambda MR, L, D: MR * L / (3 * D),
        lambda MR, L, D: 0
    ),
}
