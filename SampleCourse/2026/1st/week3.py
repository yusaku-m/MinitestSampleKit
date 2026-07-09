"""サンプル週3: 片持ち張り出し梁（オーバーハング）+ 集中荷重

ランダマイズされる要素:
- 梁の長さ L
- 支点2（roller）の位置そのもの（0.6L〜0.8Lの範囲でランダム）
  → 「拘束条件（支点位置）自体がランダムに変わる」例。支点位置が変わると
    张り出し部分の長さが変わり、曲げモーメント分布の形も学生ごとに変わる。
- 集中荷重の大きさ（張り出し部分＝支点2より右側に作用させる）
- 断面形状・寸法、材料

週2の「単純支持（両端が梁端）」に対し、支点2を梁端より内側に置くことで
オーバーハング（片側が持ち出しになる）構造を作れる。パラメータの範囲指定だけで
支持条件のバリエーションを増やせることを示す例。
"""
import sys
sys.path.append("../../..")
import packages.quiz.CrossSection as CrossSection
import packages.quiz.Material as Material
import packages.quiz.Action as Action
import packages.quiz.Parameter as Parameter
from packages.quiz.Beam import Beam
from packages.quiz.Question import BigQuestion

import sympy as sp


class Question1(BigQuestion):
    def __init__(self, id):
        """
        張り出し梁のたわみを求める問題
        (1)支点1の垂直反力
        (2)支点2の垂直反力
        (3)絶対値が最大となる曲げモーメント
        (4)断面の図心の位置
        (5)断面2次モーメント
        (6)曲げ剛性
        (7)最大のたわみ角
        (8)最大のたわみ量
        """
        super().__init__(id)

        self._parameter_classes = [
            (Parameter.Length, (1e3, 10e3, 1e3)),
        ]

        self._beam_class = Beam
        # 支点2（roller）の位置自体を 0.6L〜0.8L の範囲でランダム化 → 張り出し量が毎回変わる
        self._supports = [("pin", (0.0, 0.0, 0.01)), ("roller", (0.6, 0.8, 0.2))]
        self._actions = [
            # 張り出し部分（支点2より右側 = 0.85L〜1.0L）に集中荷重を作用させる
            (Action.ConcentratedLoad, (1, 10, 1), (0.85, 1.0, 0.05)),
        ]

        self._cross_section_classes = [
            [CrossSection.Rectangle, (12, 1e2, 12), (1e2, 3e2, 1e2)],
            [CrossSection.Circle, (1e2, 3e2, 1e2)],
        ]

        self._material_classes = [
            Material.Steel,
            Material.Aluminum,
        ]

        self._answer_unit = ["N", "N", "Nm", "mm", "mm⁴", "Nm²", "rad", "mm"]

    def generate_question(self):
        action_text = ""
        for action in self.beam.actions:
            if isinstance(action, Action.ConcentratedLoad):
                action_text += (
                    f"，荷重$P$={abs(action.magnitude):.0f} kN の集中荷重が"
                    f"$x$=${sp.nsimplify(action.position*sp.symbols('L'))}$の位置（張り出し部分）に作用し"
                )

        support_text = ""
        for support in self.beam.supports:
            if len(support_text) > 0:
                support_text += "，"
            if support[0] == "pin":
                support_text += f"$x$=${sp.nsimplify(support[1]*sp.symbols('L'))}$の位置で回転支持（支点1）"
            elif support[0] == "roller":
                support_text += f"$x$=${sp.nsimplify(support[1]*sp.symbols('L'))}$の位置で移動支持（支点2）"

        q = [
            f"長さ$L$={self.beam.si_length} mの梁において，左端を原点として右側へ向かう$x$軸を定義する。"
            f"この梁が{support_text}されており（支点2より右側が張り出し部分となる），{action_text}ている。"
            f"梁の断面が右図の形状で，材料の縦弾性係数が$E$={self.beam.material.young_modulus * 1e-9:.0f} GPa"
            f"のとき，以下のそれぞれを求めよ。",
            "支点1に生じる垂直反力$R_1$",
            "支点2に生じる垂直反力$R_2$",
            "絶対値が最大となる曲げモーメント$M_{max}$",
            r"断面の上端から図心までの距離$y_g=\frac{\int_A y dA}{\int_A dA}$",
            r"中立軸まわりの断面二次モーメント$I_z=\int_A y^2 dA$",
            "曲げ剛性$D=EI$",
            "最大のたわみ角の絶対値$\\theta$",
            "最大のたわみ量の絶対値$\\delta$",
        ]
        return q

    def generate_question_figures(self):
        return [self.beam.section.figure]

    def generate_answer(self):
        reaction_forces = self.beam.reaction_forces
        R_1 = reaction_forces[0][1]
        R_2 = reaction_forces[1][1]
        M_max = self.beam.maximum_bending_moment[1]
        centroid = self.beam.section.centroid[1]
        Iz = self.beam.section.moment_of_inertia[1]
        D = self.beam.bending_stiffness[1]
        maximum_slope = abs(self.beam.maximum_slope[1])
        maximum_deflection = abs(self.beam.maximum_deflection[1]) * 1e3

        return [R_1, R_2, M_max, centroid, Iz, D, maximum_slope, maximum_deflection]

    def generate_explanation(self):
        answers = [self.answer_format(f"{a:.2E}") for a in self.answer]
        mmax = self.beam.maximum_bending_moment[0]

        explanation = [
            self.beam.explanation_reaction_forces
            + [f"　　= {self.raw_answer[0]:.2f} {self.answer_unit[0]} = {answers[0]} {self.answer_unit[0]}"],
            ["(1)と同様にモーメントのつり合い、あるいは垂直方向の力のつり合いより，",
             f"　$R_2$= {self.raw_answer[1]:.2f} {self.answer_unit[1]} = {answers[1]} {self.answer_unit[1]}"],
            self.beam.explanation_sectional_forces
            + [
                "$M$を$x$の関数として，グラフを書き（BMD参照），最大の絶対値をもつ値を求めると，"
                "（張り出し部分では符号が反転することに注意）",
                f"　$M_{{max}}$=${mmax}$={self.raw_answer[2]:.0f}={answers[2]} {self.answer_unit[2]}",
            ],
            self.beam.section.explanation_centroid
            + [f"　　= {self.raw_answer[3]:.2f} {self.answer_unit[3]} = {answers[3]} {self.answer_unit[3]}"],
            self.beam.section.explanation_moment_of_inertia
            + ["従って，", f"　$I_Z$= {self.raw_answer[4]:.2f} {self.answer_unit[4]} = {answers[4]} {self.answer_unit[4]}"],
            self.beam.explanation_bending_stiffness
            + ["従って，", f"　$D$= {self.raw_answer[5]:.2f} {self.answer_unit[5]} = {answers[5]} {self.answer_unit[5]}"],
            self.beam.explanation_deflection
            + [
                "従って，",
                f"　$\\theta$= {self.raw_answer[6]:.2f} {self.answer_unit[6]} = {answers[6]} {self.answer_unit[6]}",
            ],
            [
                "(7)より，",
                f"　$\\delta$= {self.raw_answer[7]:.2f} {self.answer_unit[7]} = {answers[7]} {self.answer_unit[7]}",
            ],
        ]
        return explanation

    def generate_explanation_figures(self):
        return (
            [self.beam.figure_reaction_forces, self.beam.bending_moment_diagram,
             self.beam.figure_slope, self.beam.figure_deflection]
            + self.beam.figures_sectional_forces
        )


def Exercises(seed=0):
    return [Question1(i) for i in range(3)]


def MiniTest(seed=0):
    return [Question1(seed)]
