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

import numpy as np
import sympy as sp


class Question1(BigQuestion):
    def __init__(self, id, random_choice_num=None):
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

        random_choice_num を指定すると、上記8問からランダムにその数だけ選んで出題する
        （小テストの設問数を絞るための仕組み。使い方は week12.py のQuestion3を参照）。
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

        all_answer_units = ["N", "N", "Nm", "mm", "mm⁴", "Nm²", "rad", "mm"]

        if random_choice_num is not None:
            np.random.seed(self._id)
            indices = np.random.choice(len(all_answer_units), random_choice_num, replace=False)
            self.selected_indices = sorted(indices.tolist())
        else:
            self.selected_indices = list(range(len(all_answer_units)))

        self._all_answer_units = all_answer_units
        self._answer_unit = [all_answer_units[i] for i in self.selected_indices]

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

        main_text = (
            f"長さ$L$={self.beam.si_length} mの梁において，左端を原点として右側へ向かう$x$軸を定義する。"
            f"この梁が{support_text}されており（支点2より右側が張り出し部分となる），{action_text}ている。"
            f"梁の断面が右図の形状で，材料の縦弾性係数が$E$={self.beam.material.young_modulus * 1e-9:.0f} GPa"
            f"のとき，以下のそれぞれを求めよ。"
        )
        all_questions = [
            "支点1に生じる垂直反力$R_1$",
            "支点2に生じる垂直反力$R_2$",
            "絶対値が最大となる曲げモーメント$M_{max}$",
            r"断面の上端から図心までの距離$y_g=\frac{\int_A y dA}{\int_A dA}$",
            r"中立軸まわりの断面二次モーメント$I_z=\int_A y^2 dA$",
            "曲げ剛性$D=EI$",
            "最大のたわみ角の絶対値$\\theta$",
            "最大のたわみ量の絶対値$\\delta$",
        ]
        return [main_text] + [all_questions[i] for i in self.selected_indices]

    def generate_question_figures(self):
        return [self.beam.section.figure]

    def _calculate_values(self):
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

    def generate_answer(self):
        all_answers = self._calculate_values()
        return [all_answers[i] for i in self.selected_indices]

    def generate_explanation(self):
        all_values = self._calculate_values()
        all_formatted = [self.answer_format(f"{a:.2E}") for a in all_values]
        units = self._all_answer_units
        mmax = self.beam.maximum_bending_moment[0]

        all_explanations = [
            self.beam.explanation_reaction_forces
            + [f"　　= {all_values[0]:.2f} {units[0]} = {all_formatted[0]} {units[0]}"],
            ["支点反力のつり合い（モーメントのつり合い、あるいは垂直方向の力のつり合い）より，",
             f"　$R_2$= {all_values[1]:.2f} {units[1]} = {all_formatted[1]} {units[1]}"],
            self.beam.explanation_sectional_forces
            + [
                "$M$を$x$の関数として，グラフを書き（BMD参照），最大の絶対値をもつ値を求めると，"
                "（張り出し部分では符号が反転することに注意）",
                f"　$M_{{max}}$=${mmax}$={all_values[2]:.0f}={all_formatted[2]} {units[2]}",
            ],
            self.beam.section.explanation_centroid
            + [f"　　= {all_values[3]:.2f} {units[3]} = {all_formatted[3]} {units[3]}"],
            self.beam.section.explanation_moment_of_inertia
            + ["従って，", f"　$I_Z$= {all_values[4]:.2f} {units[4]} = {all_formatted[4]} {units[4]}"],
            self.beam.explanation_bending_stiffness
            + ["従って，", f"　$D$= {all_values[5]:.2f} {units[5]} = {all_formatted[5]} {units[5]}"],
            self.beam.explanation_deflection
            + [
                "従って，",
                f"　$\\theta$= {all_values[6]:.2f} {units[6]} = {all_formatted[6]} {units[6]}",
            ],
            [
                "たわみ角の式より，",
                f"　$\\delta$= {all_values[7]:.2f} {units[7]} = {all_formatted[7]} {units[7]}",
            ],
        ]
        return [all_explanations[i] for i in self.selected_indices]

    def generate_explanation_figures(self):
        return (
            [self.beam.figure_reaction_forces, self.beam.bending_moment_diagram,
             self.beam.figure_slope, self.beam.figure_deflection]
            + self.beam.figures_sectional_forces
        )


def Exercises(seed=0):
    return [Question1(i) for i in range(3)]


def MiniTest(seed=0):
    return [Question1(seed, random_choice_num=5)]
