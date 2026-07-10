import sympy as sp
import math

from .Figure import Figure
from . import Action

class Beam():
    """
    梁のクラス。
    length: 梁の長さ（mm）
    supports: 支点のリスト。(支点の種類：文字列"fixed", "pin", "roller", 位置：0-1)のタプルで表される。
    actions: 荷重のリスト。荷重クラスのインスタンスを入力
    section: 断面クラスのインスタンスを入力

    パラメータ変数
    reacrtion_forces: 支点反力のリスト。(位置：0-1，"load" or "moment", 反力の大きさ)のタプルで表される。
    """
    def __init__(self, length, supports, actions, section = None, material = None, name="梁"):
        # 入力変数
        self._length = length
        self._supports = supports
        self._actions = actions
        self._section = section
        self._material = material

        # 生成変数
        self._figure = None
        self._stress = None
        self._deflection = None
        self._lengths = []

        #支点反力
        self._reaction_forces = None
        self._figure_reaction_forces = None
        self._explanation_reaction_forces = None

        #断面力
        self._shear_force = None #(区間のタプル，式)
        self._bending_moment = None #(区間のタプル，式)
        self._explanation_sectional_forces = None
        self._figures_sectional_forces = None
        self._maximum_bending_moment = None
        self._maximum_shear_force = None

        # 応力
        self._top_stress = None
        self._bottom_stress = None
        self._minimum_stress = None
        self._maximum_stress = None
        self._explanation_stress = None

        # たわみ
        self._bending_stiffness = None
        self._explanation_bending_stiffness = None
        self._slope = None
        self._deflection = None
        self._explanation_deflection = None
        self._maximum_slope = None
        self._maximum_deflection = None

        #線図
        self._shear_force_diagram = None
        self._bending_moment_diagram = None
        self._top_stress_diagram = None
        self._bottom_stress_diagram = None
        self._slope_diagram = None
        self._deflection_diagram = None


    @property
    def lengths(self):
        return self._lengths

    @property
    def length(self):
        if self._lengths is None:
            self._figure = self.generate_figure()
        return self._length
    
    @property
    def si_length(self):
        return self._length / 1000  # mm -> m

    @property
    def supports(self):
        return self._supports
    
    @property
    def actions(self):
        return self._actions
    
    @property
    def section(self):
        return self._section

    @property
    def material(self):
        return self._material

    @property
    def figure(self):
        if self._figure is None:
            self._figure = self.generate_figure()
        return self._figure

    """
    REACTION_DORCES
    """
    @property
    def reaction_forces(self):
        if self._reaction_forces is None:
            self.calculate_reaction_forces()
        return self._reaction_forces

    @property
    def explanation_reaction_forces(self):
        if self._explanation_reaction_forces is None:
            self.calculate_reaction_forces()
        return self._explanation_reaction_forces
    
    @property
    def figure_reaction_forces(self):
        if self._figure_reaction_forces is None:
            self.calculate_reaction_forces()
        return self._figure_reaction_forces
    
    @property
    def figures_sectional_forces(self):
        if self._figures_sectional_forces is None:
            self.calculate_sectional_forces()
        return self._figures_sectional_forces

    @property
    def figure_entire_free_body_diagram(self):
        """
        梁全体の自由物体図を生成する。
        """

        return self.generate_free_body_diagram(0, 1)
    
    """
    SECTIONAL FORCES
    """

    @property
    def shear_force(self):
        if self._shear_force is None:
            self.calculate_sectional_forces()
        return self._shear_force

    @property
    def bending_moment(self):
        if self._bending_moment is None:
            self.calculate_sectional_forces()
        return self._bending_moment
    
    @property
    def explanation_sectional_forces(self):
        if self._explanation_sectional_forces is None:
            self.calculate_sectional_forces()
        return self._explanation_sectional_forces

    @property
    def shear_force_diagram(self):
        if self._shear_force_diagram is None:
            self.generate_shear_force_diagram()
        return self._shear_force_diagram
    
    @property
    def bending_moment_diagram(self):
        if self._bending_moment_diagram is None:
            self.generate_bending_moment_diagram()
        return self._bending_moment_diagram

    @property
    def maximum_bending_moment(self):
        if self._maximum_bending_moment is None:
            self.calculate_maximum_sectional_forces()
        return self._maximum_bending_moment
    
    @property
    def maximum_shear_force(self):
        if self._maximum_shear_force is None:
            self.calculate_maximum_sectional_forces()
        return self._maximum_shear_force
    
    """
    bending stress
    """
    @property
    def top_stress(self):
        if self._top_stress is None:
            self.calculate_stress_distribution()
        return self._top_stress
    
    @property
    def bottom_stress(self):
        if self._bottom_stress is None:
            self.calculate_stress_distribution()
        return self._bottom_stress
    
    @property
    def maximum_stress(self):
        if self._maximum_stress is None:
            self.calculate_stress_distribution()
        return self._maximum_stress

    @property
    def minimum_stress(self):
        if self._minimum_stress is None:
            self.calculate_stress_distribution()
        return self._minimum_stress

    @property
    def explanation_stress(self):
        if self._explanation_stress is None:
            self.calculate_stress_distribution()
        return self._explanation_stress
    
    @property
    def top_stress_diagram(self):
        if self._top_stress_diagram is None:
            self.generate_top_stress_diagram()
        return self._top_stress_diagram

    @property
    def bottom_stress_diagram(self):
        if self._bottom_stress_diagram is None:
            self.generate_bottom_stress_diagram()
        return self._bottom_stress_diagram
    
    """
    DEFLECTION
    """
    @property
    def bending_stiffness(self):
        if self._bending_stiffness is None:
            self.calculate_bending_stiffness()
        return self._bending_stiffness
    
    @property
    def explanation_bending_stiffness(self):
        if self._explanation_bending_stiffness is None:
            self.calculate_bending_stiffness()
        return self._explanation_bending_stiffness
    
    @property
    def slope(self):
        if self._slope is None:
            self.calculate_deflection()
        return self._slope
    
    @property
    def deflection(self):
        if self._deflection is None:
            self.calculate_deflection()
        return self._deflection
    
    @property
    def explanation_deflection(self):
        if self._explanation_deflection is None:
            self.calculate_deflection()
        return self._explanation_deflection

    @property
    def maximum_slope(self):
        if self._maximum_slope is None:
            self.calculate_maximum_slope_and_deflection()
        return self._maximum_slope

    @property
    def maximum_deflection(self):
        if self._maximum_deflection is None:
            self.calculate_maximum_slope_and_deflection()
        return self._maximum_deflection
    
    @property
    def figure_slope(self):
        if self._slope_diagram is None:
            self.generate_slope_diagram()
        return self._slope_diagram
    
    @property
    def figure_deflection(self):
        if self._deflection_diagram is None:
            self.generate_deflection_diagram()
        return self._deflection_diagram

    def is_simply_supported(self):
        """
        単純支持梁かどうかを判定する。
        両端に回転支持と移動支持がある場合を単純支持梁とみなす。
        """
        if len(self.supports) != 2:
            return False
        
        has_pin = any(s[0] == "pin" for s in self.supports)
        has_roller = any(s[0] == "roller" for s in self.supports)
        positions = [s[1] for s in self.supports]
        
        return has_pin and has_roller and 0 in positions and 1 in positions

    def generate_figure(self, return_parameters=False):
        """
        梁の図を生成する。
        """

        maximum_force_length = 20  # 荷重の長さの最大値

        maximum_force_magnitude = max([abs(action.magnitude) for action in self.actions]) if self.actions else 1
        
        concentrated_loads = len([action for action in self.actions if isinstance(action, Action.ConcentratedLoad)])
        distributed_loads = len([action for action in self.actions if isinstance(action, Action.DistributedLoad)])

        action_dimension_number = 0

        for action in self.actions:
            if isinstance(action, Action.ConcentratedLoad) or isinstance(action, Action.ConcentratedMoment):
                if action.position != 0 and action.position != 1:
                    action_dimension_number += 1
            if isinstance(action, Action.DistributedLoad):
                if action._position_range[0] != 0:
                    action_dimension_number += 1
                if action._position_range[1] != 1:
                    action_dimension_number += 1

        total_support_dimension_number = sum(1 for support in self.supports if support[1] != 0 and support[1] != 1)

        support_initial_height_ratio = 4
        support_dimension_height_ratio = 3.6


        # 図の中心を取得
        height = 10  # 図の高さ（固定）
        support_initial_height = height * support_initial_height_ratio
        dwg = Figure(size=(162, 
                           60 + total_support_dimension_number * support_dimension_height_ratio * height + action_dimension_number * height * support_dimension_height_ratio + distributed_loads * height * 2
                           + support_initial_height
                           )) 
        #figureの外枠（デバッグ用）
        #dwg.add(dwg.rect(insert=(0, 0), size=(dwg.width, dwg.height), fill='none', stroke='green', stroke_width=1))

        center_x = dwg.width / 2
        center_y = dwg.height / 2 - (total_support_dimension_number*support_dimension_height_ratio*height/2) + (action_dimension_number*support_dimension_height_ratio*height/2) + (distributed_loads*height)
        length = dwg.width * 0.8  # 図の長さ（80%）

        # 梁本体を書く（長方形固定）
        dwg.draw_rectangle_from_center(insert_center=(center_x, center_y), size=(length, height), fill='white', stroke='black', stroke_width=1.5)

        self._lengths.append((0, 0, "左端"))
        symbol = sp.symbols("L")
        length_symbol = symbol
        self._lengths.append((symbol, 1, "右端"))

        # 支点を書く
        support_dimension_number = 0

        for support in self.supports:

            # 左端と右端以外の支点位置をlengthsに追加
            if support[1] != 0 and support[1] != 1:

                # 寸法引き出し線
                dwg.add(dwg.line((float(center_x - length / 2 + support[1] * length), float(center_y+height/2)), (float(center_x - length / 2 + support[1] * length), float(center_y + height * (support_initial_height_ratio*1.1 + support_dimension_height_ratio*support_dimension_number))),
                    stroke="black", stroke_width=0.75, stroke_linecap="round"))
                
                dwg.add(dwg.line((float(center_x - length / 2), float(center_y+height/2)), (float(center_x - length / 2), float(center_y + height * (support_initial_height_ratio*1.1 + 2*support_dimension_number))),
                    stroke="black", stroke_width=0.75, stroke_linecap="round"))

                dwg.draw_arrow((float(center_x - length / 2), float(center_y + height * (support_initial_height_ratio*1.05 + support_dimension_height_ratio*support_dimension_number))), (float(center_x - length / 2 + support[1] * length), float(center_y + height * (support_initial_height_ratio*1.05 + support_dimension_height_ratio*support_dimension_number))), arrow_type="both")

                symbol = sp.nsimplify(length_symbol * support[1], tolerance=1e-10)
                name = "回転支点" if support[0] == "pin" else "移動支点" if support[0] == "roller" else "固定支点"
                self._lengths.append((symbol, support[1], name))

                dwg.draw_equation(f'{symbol}', position=(float(center_x - length / 2 + support[1] * length / 2), float(center_y + height * (support_initial_height_ratio + support_dimension_height_ratio*support_dimension_number) - 8)))
                
                support_dimension_number += 1


        # 長さの寸法引き出し線
        dwg.add(dwg.line((float(center_x - length / 2), float(center_y)), (float(center_x - length / 2), float(center_y + height * (support_initial_height_ratio*1.1 + support_dimension_number*support_dimension_height_ratio))),
            stroke="black", stroke_width=0.75, stroke_linecap="round"))
        
        dwg.add(dwg.line((float(center_x + length / 2), float(center_y)), (float(center_x + length / 2), float(center_y + height * (support_initial_height_ratio*1.1 + support_dimension_number*support_dimension_height_ratio))),
            stroke="black", stroke_width=0.75, stroke_linecap="round"))

        dwg.draw_arrow((float(center_x - length / 2), float(center_y + height * (support_initial_height_ratio*1.05 + support_dimension_height_ratio*support_dimension_number))), (float(center_x + length / 2), float(center_y + height * (support_initial_height_ratio*1.05 + support_dimension_height_ratio*support_dimension_number))), arrow_type="both")

        dwg.draw_equation(f'L', position=(float(center_x), float(center_y + height * (support_initial_height_ratio + support_dimension_height_ratio*support_dimension_number) - 3)))

        for support in self.supports:

            if support[0] == "pin" :
                dwg.draw_pin_support((float(center_x - length / 2 + support[1] * length), float(center_y + height / 2)), size=float(height*0.3), circle=False)

            if support[0] == "roller":
                dwg.draw_roller_support((float(center_x - length / 2 + support[1] * length), float(center_y + height / 2)), size=float(height*0.3))

            elif support[0] == "fixed":
                if support[1] == 0:
                    angle = 90
                elif support[1] == 1:
                    angle = -90
                dwg.draw_fixed_support(
                    (float(center_x - length / 2 + support[1] * length), float(center_y)), 
                    width=float(height*5), height=float(height*1), rotate_angle=float(angle)
                )

        # 作用を書く
        adn = 1*distributed_loads
        cln = 1; cmn = 0; dln = 1
        
        for i, action in enumerate(self.actions):
            if isinstance(action, Action.ConcentratedLoad):
                force_length = float(maximum_force_length)
                position = float(center_x - length / 2 + action.position * length)
                dwg.draw_force(
                    start = (position, float(center_y - height / 2 - force_length-5)),
                    end = (position, float(center_y - height / 2 - 2)), 
                )
                #テキスト
                y_offset = -50 if distributed_loads > 0 else 0
                x_offset = -10 if distributed_loads > 0 else 0
                if concentrated_loads != 1:
                    dwg.draw_equation(f'P_{cln}', position=(float(position  + 10 + x_offset), float(center_y - height / 2 - force_length - 8 - y_offset)))
                else:
                    dwg.draw_equation(f'P', position=(float(position + 10 + x_offset), float(center_y - height / 2 - force_length - 8 - y_offset)))


            if isinstance(action, Action.ConcentratedMoment):
                position = float(center_x - length / 2 + action.position * length)
                dwg.draw_moment(
                    center = (position, float(center_y)),
                    radius = float(height),
                    color = "black"
                )
                #テキスト
                y_offset = -35 if distributed_loads > 0 else 0
                dwg.draw_equation(f'M_{cmn}', position=(float(position + 10), float(center_y - height - 2 - y_offset)))

            if isinstance(action, Action.DistributedLoad):
                start_position = float(center_x - length / 2)
                end_position = float(center_x + length / 2)
                force_length = float(maximum_force_length / 3 * 2)

                dwg.draw_distributed_load(
                    beam_leftend = (start_position, float(center_y - height / 2 - 2)),
                    beam_rightend = (end_position, float(center_y - height / 2 - 2)),
                    base_magnitude = force_length,
                    load_range = action._position_range,
                    function = action._function,
                    color="black"
                )
                #テキスト
                if action._function == "1":
                    dwg.draw_equation(f'w(x)==w_0', position=(float(start_position + (end_position - start_position)*(action._position_range[0]+action._position_range[1])/2), 
                                                              float(center_y - height / 2 - force_length -16)))
                else:
                    dwg.draw_equation(f'w(x)==w_0*{action._function}', position=(float(start_position + (end_position - start_position)*(action._position_range[0]+action._position_range[1])/2), float(center_y - height / 2 - force_length -16)))

            # 寸法

            if (action.position != 0 and action.position != 1) and (isinstance(action, Action.ConcentratedLoad) or isinstance(action, Action.ConcentratedMoment)):
        
                dwg.add(dwg.line((float(position), float(center_y-height/2)), (float(position), float(center_y - height * (3 + support_dimension_height_ratio*adn))),
                    stroke="black", stroke_width=0.75, stroke_linecap="round"))
                dwg.add(dwg.line((float(center_x - length / 2), float(center_y-height/2)), (float(center_x - length / 2), float(center_y - height * (3 + support_dimension_height_ratio*adn))),
                    stroke="black", stroke_width=0.75, stroke_linecap="round"))
                dwg.draw_arrow((float(center_x - length / 2), float(center_y - height * (2.5 + support_dimension_height_ratio*adn))), (float(position), float(center_y - height * (2.5 + support_dimension_height_ratio*adn))), arrow_type="both")
                
                symbol = sp.nsimplify(length_symbol * action.position, tolerance=1e-10)
                dwg.draw_equation(f'{str(symbol)}', position=(float((center_x - length / 2 + position) / 2), float(center_y - height * (3.6 + support_dimension_height_ratio*adn))))
                
                if isinstance(action, Action.ConcentratedLoad):
                    self._lengths.append((symbol, action.position, f"荷重$P_{cln}$の位置"))

                if isinstance(action, Action.ConcentratedMoment):
                    self._lengths.append((symbol, action.position, f"モーメント$M_{cmn}$の位置"))

                adn += 1
            
            if isinstance(action, Action.DistributedLoad) and (action._position_range[0] != 0):
                start_pos = float(center_x - length / 2 + action._position_range[0] * length)

                dwg.add(dwg.line((float(start_pos), float(center_y-height/2)), (float(start_pos), float(center_y - height * (3 + support_dimension_height_ratio*adn))),
                    stroke="black", stroke_width=0.75, stroke_linecap="round"))
                dwg.add(dwg.line((float(center_x - length / 2), float(center_y-height/2)), (float(center_x - length / 2), float(center_y - height * (3 + support_dimension_height_ratio*adn))),
                    stroke="black", stroke_width=0.75, stroke_linecap="round"))
                dwg.draw_arrow((float(center_x - length / 2), float(center_y - height * (2.5 + support_dimension_height_ratio*adn))), (float(start_pos), float(center_y - height * (2.5 + support_dimension_height_ratio*adn))), arrow_type="both")

                symbol = sp.nsimplify(length_symbol * action._position_range[0], tolerance=1e-10)
                dwg.draw_equation(f'{str(symbol)}', position=(float((center_x - length / 2 + start_pos) / 2), float(center_y - height * (3.6 + support_dimension_height_ratio*adn))))

                adn += 1
            
            if isinstance(action, Action.DistributedLoad) and (action._position_range[1] != 1):
                end_pos = float(center_x - length / 2 + action._position_range[1] * length)

                dwg.add(dwg.line((float(end_pos), float(center_y-height/2)), (float(end_pos), float(center_y - height * (3 + support_dimension_height_ratio*adn))),
                    stroke="black", stroke_width=0.75, stroke_linecap="round"))
                dwg.add(dwg.line((float(center_x - length / 2), float(center_y-height/2)), (float(center_x - length / 2), float(center_y - height * (3 + support_dimension_height_ratio*adn))),
                    stroke="black", stroke_width=0.75, stroke_linecap="round"))
                dwg.draw_arrow((float(center_x - length / 2), float(center_y - height * (2.5 + support_dimension_height_ratio*adn))), (float(end_pos), float(center_y - height * (2.5 + support_dimension_height_ratio*adn))), arrow_type="both")

                symbol = sp.nsimplify(length_symbol * action._position_range[1], tolerance=1e-10)
                dwg.draw_equation(f'{str(symbol)}', position=(float((center_x - length / 2 + end_pos) / 2), float(center_y - height * (3.6 + support_dimension_height_ratio*adn))))

                adn += 1

            if isinstance(action, Action.DistributedLoad):
                self._lengths.append((action.position_eq, action.position, "分布荷重を集中荷重に読み替えた作用位置"))

            # 他の荷重もここに追加可能
            if isinstance(action, Action.ConcentratedLoad):
                cln += 1
            if isinstance(action, Action.ConcentratedMoment):
                cmn += 1

        if return_parameters:
            return dwg, length, center_x, center_y, height
        
        else:
            return dwg

    def _add_equilibrium_explanation(self, force_equation, moment_equations_info):
        """釣り合い式の解説を追加する"""
        self._explanation_reaction_forces.append(f"上向きの力を正として力の釣り合いを考えると，")
        self._explanation_reaction_forces.append(f"　${sp.nsimplify(force_equation)}$=$0$")

        for i, (point_name, eq) in enumerate(moment_equations_info):
            if i == 0:
                self._explanation_reaction_forces.append(f"続いて，{point_name}を中心として，反時計回りを正とするモーメントの釣り合いを考えると，")
            else:
                self._explanation_reaction_forces.append(f"また，{point_name}を中心とした場合は，")
            self._explanation_reaction_forces.append(f"　${sp.nsimplify(eq)}$=$0$")

        self._explanation_reaction_forces.append(f"モーメントのつり合いの式は，上記の例を含め，いかなる点を中心としてもよい。")

    def _add_indeterminate_explanation(self, target_symbols):
        """不静定梁の解法の解説を追加する"""
        rn_mn = len(target_symbols)
        self._explanation_reaction_forces.append(f"支点反力の数({rn_mn})が釣り合い式の数(2)より多いため，本問題は不静定梁である。")
        self._explanation_reaction_forces.append("たわみの基礎式を用いた解法（積分法）により，境界条件から不足している方程式を導出する。")
        self._explanation_reaction_forces.append("1. 各区間の曲げモーメント $M(x)$ を，未知の反力を含んだ状態で求める。")
        self._explanation_reaction_forces.append("2. たわみの基礎式 $EI v''(x) = -M(x)$ を2回積分し，各区間のたわみ角 $v'$ とたわみ $v$ を求める。")
        self._explanation_reaction_forces.append("3. 支点位置での境界条件（支点位置でのたわみ $v=0$ など）および区間境界での連続条件を適用し，未知数に関する連立方程式を作成する。")
        self._explanation_reaction_forces.append("4. 作成した方程式と静力学的釣り合い式を連立させて，すべての支点反力を解く。")

    def _add_reaction_results_explanation(self, solutions, value_dict):
        """計算結果の解説を追加する"""
        new_reaction_forces = []

        self._explanation_reaction_forces.append("")

        for reaction in self._reaction_forces:
            if reaction[0] in solutions:
                value = solutions[reaction[0]].subs(value_dict)
                new_reaction_forces.append((reaction[0], value, reaction[2], solutions[reaction[0]]))
                unit = "Nm" if "M" in str(reaction[0]) else "N"
                #solution[reaction[0]] をPを含んだ変数に関して因数分解
                eq = sp.nsimplify(sp.factor(solutions[reaction[0]]))
                #print(f"eq: {eq}, value: {value}, unit: {unit}, reaction: {reaction}")
                self._explanation_reaction_forces[-1] += f"　${reaction[0]}$=${eq}$= {value:.0f} {unit}，"
            else:
                # 不静定などで解けなかった場合
                new_reaction_forces.append((reaction[0], 0, reaction[2], reaction[0]))
                self._explanation_reaction_forces[-1] += f"　${reaction[0]}$= 未知（不静定），"
        self._explanation_reaction_forces[-1] = self._explanation_reaction_forces[-1][:-1]
        
        self._reaction_forces = new_reaction_forces

    def calculate_indeterminate_reaction_forces_by_superprinciple(self, target_symbols, force_equation, moment_equation0):
        """
        重ね合わせの原理を用いて不静定梁の反力を計算する。
        """
        from .BeamLibrary import BEAM_REGISTRY
        import sympy as sp
        import numpy as np
        print("重ね合わせの原理を用いて不静定梁の反力計算にトライします。")

        L_sym = sp.symbols("L")
        D_sym = sp.symbols("D")
        
        # 支点構成の解析
        fixed_supports = [s for s in self.supports if s[0] == "fixed"]
        other_supports = [s for s in self.supports if s[0] in ["pin", "roller"]]
        
        case_type = []
        redundant_support = None
        redundant_index = -1
        
        # シンボル順序をシミュレート (calculate_reaction_forcesのロジックに厳密に合わせる)
        symbols_simulated = []
        for s in self.supports:
            if s[0] == "fixed":
                symbols_simulated.append(("M", s))
            if s[0] in ["pin", "roller", "fixed"]:
                symbols_simulated.append(("R", s))

        # 1. 2径間連続梁 (0, 0.5, 1 に支点)
        if len(fixed_supports) == 0 and len(other_supports) == 3:
            """
            連続梁の場合
            """
            # 支点位置を取得してソート
            support_info = []
            for i, s in enumerate(self.supports):
                # 荷重シンボルのインデックスを特定
                idx = [j for j, (stype, sref) in enumerate(symbols_simulated) if stype == "R" and sref == s][0]
                support_info.append((i, s, idx))
            
            sorted_supports = sorted(support_info, key=lambda x: float(x[1][1]))
            positions = [float(x[1][1]) for x in sorted_supports]
            
            # 数値的な誤差を考慮
            if all(np.isclose(positions, [0.0, 0.5, 1.0])):
                case_type.append("S_center")
                redundant_info = sorted_supports[1]
                redundant_support = redundant_info[1]
                redundant_index = redundant_info[2] # Load symbol index

        # 2. プロップトカチレバー (0固定, 1支持 または 1固定, 0支持)
        elif len(fixed_supports) == 1 and len(other_supports) == 1:
            
            """
            半固定梁の場合
            """
            
            fixed_support = fixed_supports[0]
            other_support = other_supports[0]
            
            if (np.isclose(float(fixed_support[1]), 0.0) and np.isclose(float(other_support[1]), 1.0)) or \
               (np.isclose(float(fixed_support[1]), 1.0) and np.isclose(float(other_support[1]), 0.0)):
                
                case_type.append("C_end")
                case_type.append("S_end")
                
                # 支点インデックスの特定
                m_idx = [j for j, (stype, sref) in enumerate(symbols_simulated) if stype == "M" and sref == fixed_support][0]
                redundant_index = [j for j, (stype, sref) in enumerate(symbols_simulated) if stype == "R" and sref == other_support][0]

        # 3. 両端固定梁 (0固定, 1固定)
        elif len(fixed_supports) == 2 and len(other_supports) == 0:
            """
            両端固定梁の場合
            """
            s_pos = sorted([float(s[1]) for s in fixed_supports])
            if np.isclose(s_pos[0], 0.0) and np.isclose(s_pos[1], 1.0):
                case_type.append("C_fixed_fixed")
                case_type.append("S_fixed_fixed")
                
                # C_fixed_fixed redundant info (User wants right side fixed, so redundant is at x=0)
                support_at_0 = [s for s in self.supports if np.isclose(float(s[1]), 0.0)][0]
                support_at_L = [s for s in self.supports if np.isclose(float(s[1]), 1.0)][0]
                m_redundant_idx = [j for j, (stype, sref) in enumerate(symbols_simulated) if stype == "M" and sref == support_at_0][0]
                r_redundant_idx = [j for j, (stype, sref) in enumerate(symbols_simulated) if stype == "R" and sref == support_at_0][0]

                # S_fixed_fixed redundant info
                m1_idx_s = [j for j, (stype, sref) in enumerate(symbols_simulated) if stype == "M" and sref == support_at_0][0]
                m2_idx_s = [j for j, (stype, sref) in enumerate(symbols_simulated) if stype == "M" and sref == support_at_L][0]
        
        if case_type == []:
            print("重ね合わせの原理を用いた解法の対象ケースに該当しませんでした。フォールバックします。")
            return None

        # 基本静定系の設定
        any_success = False
        final_solutions = None

        for i, case in enumerate(case_type):
            if case == "S_center":
                R_r_sym = target_symbols[redundant_index]
                base_name = "単純支持梁"
                redundant_name = f"中央の支点（$x=0.5L$）"
                delta_unit_formula = BEAM_REGISTRY["S_P_center"]
                delta_unit = -delta_unit_formula.delta_func(R_r_sym, L_sym, D_sym)
                comp_type = "delta"

            elif case == "C_end":
                R_r_sym = target_symbols[redundant_index]
                fixed_pos_val = [s[1] for s in self.supports if s[0] == "fixed"][0]
                fixed_pos = "左端" if np.isclose(float(fixed_pos_val), 0.0) else "右端"
                redundant_pos = "右端" if fixed_pos == "左端" else "左端"
                base_name = f"{fixed_pos}固定の片持ち梁"
                redundant_name = f"{redundant_pos}の支点"
                delta_unit_formula = BEAM_REGISTRY["C_P_end"]
                delta_unit = -delta_unit_formula.delta_func(R_r_sym, L_sym, D_sym)
                comp_type = "delta"

            elif case == "S_end":
                # 半固定梁を単純支持梁として読み替える（固定端のモーメントを不静定力とする）
                # fixed_supports[0] のモーメント反力を探す
                fixed_support = fixed_supports[0]
                fixed_pos_val = float(fixed_support[1])
                is_left = np.isclose(fixed_pos_val, 0.0)
                
                R_r_sym = target_symbols[m_idx]
                base_name = "単純支持梁"
                redundant_name = f"{'左端' if is_left else '右端'}の固定モーメント"
                
                # 単位モーメントによるたわみ角
                # S_M_a in registry: a is position. Here it's at end.
                if is_left:
                    # 左端の回転角 v'(0)
                    delta_unit_formula = BEAM_REGISTRY["S_M_left"]
                    delta_unit = -delta_unit_formula.thetaL_func(R_r_sym, L_sym, D_sym)
                else:
                    # 右端の回転角 v'(L)
                    delta_unit_formula = BEAM_REGISTRY["S_M_right"]
                    delta_unit = -delta_unit_formula.thetaR_func(R_r_sym, L_sym, D_sym)
                comp_type = "theta"
            
            elif case == "C_fixed_fixed":
                R1 = target_symbols[r_redundant_idx]
                M1 = target_symbols[m_redundant_idx]
                base_name = "片持ち梁"
                
                beam_num = len(self.actions) + 2 # 荷重 + R1 + M1

                if len(case_type) > 1:
                    self._explanation_reaction_forces.append(f"【重ね合わせ法{i+1}：{base_name}への読み替え】")

                self._explanation_reaction_forces.append(f"この梁を${R1}$および${M1}$を外力として受ける片持ち梁（$x=L$固定）として読み替え，たわみとたわみ角が共に$0$となる条件（適合条件）から解く。")

                possible = True
                total_delta_load = 0
                total_theta_load = 0
                self._explanation_reaction_forces.append("")
                for j, action in enumerate(self.actions):
                    delta_j = self._calculate_delta_from_action(action, "C_end", L_sym, D_sym, fixed_at=1.0)
                    theta_j = self._calculate_theta_from_action(action, "C_end", L_sym, D_sym, fixed_at=1.0)
                    if delta_j is None or theta_j is None:
                        possible = False; break
                    self._explanation_reaction_forces[-1] += f"梁{j+1}：$\\delta_{{{j+1}}}={sp.latex(sp.nsimplify(delta_j))}, \\theta_{{{j+1}}}={sp.latex(sp.nsimplify(theta_j))}$，"
                    total_delta_load += delta_j
                    total_theta_load += theta_j
                
                if not possible:
                    self._explanation_reaction_forces.pop()
                    self._explanation_reaction_forces.pop()
                    continue

                # 単位不静定力による影響
                # R1 (up) -> delta = -R1 L^3 / 3D, theta = R1 L^2 / 2D
                # M1 (CCW) -> delta = M1 L^2 / 2D, theta = -M1 L / D
                delta_R1 = -R1 * L_sym**3 / (3 * D_sym)
                theta_R1 = R1 * L_sym**2 / (2 * D_sym)
                delta_M1 = M1 * L_sym**2 / (2 * D_sym)
                theta_M1 = -M1 * L_sym / D_sym
                
                self._explanation_reaction_forces[-1] += f"梁{beam_num-1}：$\\delta_{{{beam_num-1}}}={sp.latex(sp.nsimplify(delta_R1))}, \\theta_{{{beam_num-1}}}={sp.latex(sp.nsimplify(theta_R1))}$，"
                self._explanation_reaction_forces[-1] += f"梁{beam_num}：$\\delta_{{{beam_num}}}={sp.latex(sp.nsimplify(delta_M1))}, \\theta_{{{beam_num}}}={sp.latex(sp.nsimplify(theta_M1))}$"
                
                eq1 = sp.Eq(total_delta_load + delta_R1 + delta_M1, 0)
                eq2 = sp.Eq(total_theta_load + theta_R1 + theta_M1, 0)
                
                self._explanation_reaction_forces.append(f"境界条件 $\\sum \\delta = 0, \\sum \\theta = 0$ より，")
                sols = sp.solve([eq1, eq2], [R1, M1])
                self._explanation_reaction_forces.append(f"　${R1} = {sp.latex(sp.nsimplify(sols[R1]))}, {M1} = {sp.latex(sp.nsimplify(sols[M1]))}$")
                
                solutions = sols
                # 他の反力 R2, M2
                other_symbols = [s for s in target_symbols if s not in [R1, M1]]
                remaining_eqs = [force_equation.subs(sols), moment_equation0.subs(sols)]
                other_sols = sp.solve(remaining_eqs, other_symbols)
                if isinstance(other_sols, list):
                    other_sols = other_sols[0] if other_sols else {}
                solutions.update(other_sols)
                any_success = True; final_solutions = solutions; print(f"{case}の計算に成功しました。")
                continue # C_fixed_fixed は 2x2 なのでここで終了

            elif case == "S_fixed_fixed":
                M1 = target_symbols[m1_idx_s]
                M2 = target_symbols[m2_idx_s]
                base_name = "単純支持梁"
                
                beam_num = len(self.actions) + 2 # 荷重 + M1 + M2

                if len(case_type) > 1:
                    self._explanation_reaction_forces.append(f"【重ね合わせ法{i+1}：{base_name}への読み替え】")


                self._explanation_reaction_forces.append(f"この梁を${M1}$および${M2}$を外力として受ける単純支持梁（$x=0, L$支持）として読み替え，両端のたわみ角が共に$0$となる条件（適合条件）から解く。")

                possible = True
                total_theta1_load = 0
                total_theta2_load = 0
                self._explanation_reaction_forces.append("")
                for j, action in enumerate(self.actions):
                    theta1_j = self._calculate_theta_from_action(action, "S_end_left", L_sym, D_sym)
                    theta2_j = self._calculate_theta_from_action(action, "S_end_right", L_sym, D_sym)
                    if theta1_j is None or theta2_j is None:
                        possible = False; break
                    self._explanation_reaction_forces[-1] += f"梁{j+1}：$\\theta_{{{j+1}L}}={sp.latex(sp.nsimplify(theta1_j))}, \\theta_{{{j+1}R}}={sp.latex(sp.nsimplify(theta2_j))}$，"
                    total_theta1_load += theta1_j
                    total_theta2_load += theta2_j
                
                if not possible:
                    self._explanation_reaction_forces.pop()
                    self._explanation_reaction_forces.pop()
                    continue

                # 単位不静定モーメントによる影響 (下向き正 v'(x))
                # CCW at x=0 (M1) -> theta1 = -M1 L / 3D, theta2 = M1 L / 6D
                # CCW at x=L (M2) -> theta1 = M2 L / 6D, theta2 = -M2 L / 3D
                theta1_M1 = -M1 * L_sym / (3 * D_sym)
                theta2_M1 = M1 * L_sym / (6 * D_sym)
                theta1_M2 = M2 * L_sym / (6 * D_sym)
                theta2_M2 = -M2 * L_sym / (3 * D_sym)
                
                self._explanation_reaction_forces[-1] += f"梁{beam_num-1}：$\\theta_{{{beam_num-1}L}}={sp.latex(sp.nsimplify(theta1_M1))}, \\theta_{{{beam_num-1}R}}={sp.latex(sp.nsimplify(theta2_M1))}$，"
                self._explanation_reaction_forces[-1] += f"梁{beam_num}：$\\theta_{{{beam_num}L}}={sp.latex(sp.nsimplify(theta1_M2))}, \\theta_{{{beam_num}R}}={sp.latex(sp.nsimplify(theta2_M2))}$"
                
                eq1 = sp.Eq(total_theta1_load + theta1_M1 + theta1_M2, 0)
                eq2 = sp.Eq(total_theta2_load + theta2_M1 + theta2_M2, 0)
                
                self._explanation_reaction_forces.append(f"境界条件 $\\sum \\theta_L = 0, \\sum \\theta_R = 0$ より，")
                sols = sp.solve([eq1, eq2], [M1, M2])
                self._explanation_reaction_forces.append(f"　${M1} = {sp.latex(sp.nsimplify(sols[M1]))}, {M2} = {sp.latex(sp.nsimplify(sols[M2]))}$")
                
                solutions = sols
                # 他の反力 R1, R2
                other_symbols = [s for s in target_symbols if s not in [M1, M2]]
                remaining_eqs = [force_equation.subs(sols), moment_equation0.subs(sols)]
                other_sols = sp.solve(remaining_eqs, other_symbols)
                if isinstance(other_sols, list):
                    other_sols = other_sols[0] if other_sols else {}
                solutions.update(other_sols)
                any_success = True; final_solutions = solutions; print(f"{case}の計算に成功しました。")
                continue

            beam_num = len(self.actions) + 1  # 荷重の数 + 基本系の荷重1つ
            
            explanation_title = ""
            if len(case_type) > 1:
                self._explanation_reaction_forces.append(f"【重ね合わせ法{i+1}：{base_name}への読み替え】")
            
            self._explanation_reaction_forces.append(explanation_title + f"この梁を${R_r_sym}$を外からの作用として受ける{base_name}として読み替え，図のように梁1から梁{beam_num}の重ね合わせとして考える。")
            
            possible = True
            total_load_comp = 0
            self._explanation_reaction_forces.append("")
            for i, action in enumerate(self.actions):
                if comp_type == "delta":
                    comp_i = self._calculate_delta_from_action(action, case, L_sym, D_sym)
                else:
                    comp_i = self._calculate_theta_from_action(action, case, L_sym, D_sym)

                if comp_i is None:
                    print(f"荷重{i+1}である{action}の{'たわみ' if comp_type == 'delta' else 'たわみ角'}の計算に失敗。")
                    possible = False
                    break
                
                comp_sym = "\\delta" if comp_type == "delta" else "\\theta"
                self._explanation_reaction_forces[-1] += f"梁{i+1}：${comp_sym}_{{{i+1}}} = {sp.latex(sp.nsimplify(comp_i))}$，"
                total_load_comp += comp_i


            if not possible:
                # このケースは失敗。説明から削除する（または失敗した旨を書く）
                self._explanation_reaction_forces.pop()
                self._explanation_reaction_forces.pop()
                continue
            
            comp_sym = "\\delta" if comp_type == "delta" else "\\theta"
            self._explanation_reaction_forces[-1] += f"梁{beam_num}：${comp_sym}_{{{beam_num}}} = {sp.latex(sp.nsimplify(delta_unit))}$"
            
            sum_eq = [f"{comp_sym}_{{{i}}}" for i in range(1, beam_num+1)]
            self._explanation_reaction_forces.append(f"境界条件 ${' + '.join(sum_eq)} = 0$ より，")
            compatibility_eq = sp.Eq(total_load_comp + delta_unit, 0)
            sol_R = sp.solve(compatibility_eq, R_r_sym)[0]
            self._explanation_reaction_forces.append(f"　${R_r_sym} = {sp.latex(sp.nsimplify(sol_R))}$")
            
            # 静的釣り合い式から他の反力を求める
            other_symbols = [s for s in target_symbols if s != R_r_sym]
            solutions = {R_r_sym: sol_R}
            
            remaining_eqs = [force_equation.subs(R_r_sym, sol_R), moment_equation0.subs(R_r_sym, sol_R)]
            other_sols = sp.solve(remaining_eqs, other_symbols)
            
            if isinstance(other_sols, list):
                if len(other_sols) > 0:
                    other_sols = other_sols[0]
                else:
                    other_sols = {}
                    
            solutions.update(other_sols)
            
            any_success = True
            if final_solutions is None:
                final_solutions = solutions

            print(f"{case}の計算に成功しました。")

        if any_success:
            return final_solutions
        
        print("すべての重ね合わせパターンで解法を断念しました。")
        return None

    def _calculate_delta_from_action(self, action, case_type, L, D, fixed_at=None):
        from .BeamLibrary import BEAM_REGISTRY
        import sympy as sp

        def to_sym(val):
            # SymPyのFloatやPythonのfloatを考慮してRationalに変換
            v = sp.sympify(val)
            if v.is_Number:
                return sp.nsimplify(v, tolerance=1e-10, rational=True)
            return v

        result = None
        if case_type == "S_center":
            if isinstance(action, Action.ConcentratedLoad):
                # 荷重のシンボルを決定
                total_p = len([a for a in self.actions if isinstance(a, Action.ConcentratedLoad)])
                if total_p > 1:
                    p_actions = [a for a in self.actions if isinstance(a, Action.ConcentratedLoad)]
                    idx = p_actions.index(action)
                    P = sp.symbols(f"P_{idx + 1}")
                else:
                    P = sp.symbols("P")

                pos = to_sym(action.position)
                if pos == sp.Rational(1, 2):
                    result = BEAM_REGISTRY["S_P_center"].delta_func(P, L, D)
                else:
                    a = pos * L
                    b = L - a
                    result = BEAM_REGISTRY["S_P_a"].delta_func(P, L, a, b, D)
            elif isinstance(action, Action.DistributedLoad):
                w0 = sp.symbols("w_0")
                pos_start = to_sym(action._position_range[0])
                pos_end = to_sym(action._position_range[1])

                if action.function == "1":
                    # 0からx*Lまでの等分布荷重(S_w_b)による中央たわみの差分から，
                    # 任意区間[pos_start*L, pos_end*L]の等分布荷重による中央たわみを求める
                    def f_center_delta(x_r):
                        a_r = x_r * L
                        return BEAM_REGISTRY["S_w_b"].delta_func(w0, L, a_r, L - a_r, D)

                    result = f_center_delta(pos_end) - f_center_delta(pos_start)
                elif pos_start == 0 and pos_end == 1:
                    if action.function == "x/L" or action.function == "1-x/L":
                        result = BEAM_REGISTRY["S_w_tri"].delta_func(w0, L, D)

            elif isinstance(action, Action.ConcentratedMoment):
                m_actions = [a for a in self.actions if isinstance(a, Action.ConcentratedMoment)]
                idx = m_actions.index(action)
                Mc = sp.symbols(f"M_{idx}")

                pos = to_sym(action.position)
                a = pos * L
                b = L - a
                result = BEAM_REGISTRY["S_M_a"].delta_func(Mc, L, a, b, D)

        elif case_type == "C_end":
            if fixed_at is not None:
                fixed_at_0 = (fixed_at == 0)
            else:
                fixed_pos_val = to_sym([s[1] for s in self.supports if s[0] == "fixed"][0])
                fixed_at_0 = (fixed_pos_val == 0)

            if isinstance(action, Action.ConcentratedLoad):
                total_p = len([a for a in self.actions if isinstance(a, Action.ConcentratedLoad)])
                if total_p > 1:
                    p_actions = [a for a in self.actions if isinstance(a, Action.ConcentratedLoad)]
                    idx = p_actions.index(action)
                    P = sp.symbols(f"P_{idx + 1}")
                else:
                    P = sp.symbols("P")

                pos = to_sym(action.position)
                rel_pos = pos if fixed_at_0 else (1 - pos) # 固定端からの距離比率
                if rel_pos == 1:
                    result = BEAM_REGISTRY["C_P_end"].delta_func(P, L, D)
                else:
                    # C_P_a in registry: a is distance from FREE end? 
                    # Let's check: P * L^3 / 6D * (1-a/L)^2 * (2+a/L). If a=0 (at free end), PL^3/3D.
                    # So a is distance from FIXED end? No, if a=0, (1)^2 * (2) = 2. PL^3/3D.
                    # If a=L (at free end), (0)^2 * (3) = 0.
                    # Wait, C_P_a in BeamLibrary is very strange. 
                    # 一般式を使用: delta = P * a^2 * (3*L - a) / (6 * D)  (aは固定端からの距離)
                    a = rel_pos * L
                    result = P * a**2 * (3 * L - a) / (6 * D)
            elif isinstance(action, Action.DistributedLoad):
                w0 = sp.symbols("w_0")
                pos_start = to_sym(action._position_range[0])
                pos_end = to_sym(action._position_range[1])
                
                if action.function == "1":
                    # 自由端でのたわみ: f(x) = w0 * x^3 * (4*L - x) / (24 * D)  (xは固定端からの距離)
                    def f_cant_delta(x_r):
                        return w0 * (x_r * L)**3 * (4 * L - x_r * L) / (24 * D)
                    
                    if fixed_at_0:
                        result = f_cant_delta(pos_end) - f_cant_delta(pos_start)
                    else:
                        result = f_cant_delta(1 - pos_start) - f_cant_delta(1 - pos_end)
                elif pos_start == 0 and pos_end == 1:
                    if (fixed_at_0 and action.function == "1-x/L") or (not fixed_at_0 and action.function == "x/L"):
                        result = BEAM_REGISTRY["C_w_tri"].delta_func(w0, L, D)
                    elif (fixed_at_0 and action.function == "x/L") or (not fixed_at_0 and action.function == "1-x/L"):
                        # 三角形分布荷重 (自由端が最大) : 11/120 * w0 * L^4 / D
                        result = 11 * w0 * L**4 / (120 * D)

            elif isinstance(action, Action.ConcentratedMoment):
                m_actions = [a for a in self.actions if isinstance(a, Action.ConcentratedMoment)]
                idx = m_actions.index(action)
                Mc = sp.symbols(f"M_{idx}")

                pos = to_sym(action.position)
                rel_pos = pos if fixed_at_0 else (1 - pos)
                a_fixed = rel_pos * L
                a_free = L - a_fixed
                
                # CCW(Mc>0) at free end of cantilever (fixed at other end)
                # If fixed at 0, Mc at L (CCW) -> upward deflection (negative)
                # If fixed at L, Mc at 0 (CCW) -> downward deflection (positive)
                res = BEAM_REGISTRY["C_M_a"].delta_func(Mc, L, a_free, D)
                result = -res if fixed_at_0 else res

        if result is not None:
            return sp.nsimplify(sp.simplify(result), tolerance=1e-10, rational=True)
        return None

    def _calculate_theta_from_action(self, action, case_type, L, D, fixed_at=None):
        from .BeamLibrary import BEAM_REGISTRY
        import sympy as sp
        import numpy as np

        def to_sym(val):
            v = sp.sympify(val)
            if v.is_Number:
                return sp.nsimplify(v, tolerance=1e-10, rational=True)
            return v

        result = None
        if case_type in ["S_end", "S_end_left", "S_end_right"]:
            # 半固定梁を単純支持梁として読み替えた場合
            # 固定端での回転角を計算する
            if case_type == "S_end_left":
                is_left_end = True
            elif case_type == "S_end_right":
                is_left_end = False
            else:
                fixed_supports = [s for s in self.supports if s[0] == "fixed"]
                if not fixed_supports:
                    return None
                fixed_support = fixed_supports[0]
                is_left_end = np.isclose(float(fixed_support[1]), 0.0)

            if isinstance(action, Action.ConcentratedLoad):
                total_p = len([a for a in self.actions if isinstance(a, Action.ConcentratedLoad)])
                if total_p > 1:
                    p_actions = [a for a in self.actions if isinstance(a, Action.ConcentratedLoad)]
                    idx = p_actions.index(action)
                    P = sp.symbols(f"P_{idx + 1}")
                else:
                    P = sp.symbols("P")
                
                pos = to_sym(action.position)
                # S_P_a in registry: a is distance from LEFT end.
                a = pos * L
                b = (1 - pos) * L
                if is_left_end:
                    # v'(0) は下向き正で正
                    result = BEAM_REGISTRY["S_P_a"].thetaL_func(P, L, a, b, D)
                else:
                    # v'(L) は下向き正で負だが registry は正を返すので反転
                    result = - BEAM_REGISTRY["S_P_a"].thetaR_func(P, L, a, b, D)

            elif isinstance(action, Action.DistributedLoad):
                w0 = sp.symbols("w_0")
                pos_start = to_sym(action._position_range[0])
                pos_end = to_sym(action._position_range[1])
                
                if action.function == "1":
                    if pos_start == 0 and pos_end == 1:
                        # 全体等分布荷重
                        if is_left_end:
                            result = BEAM_REGISTRY["S_w_all"].thetaL_func(w0, L, D) 
                        else:
                            result = - BEAM_REGISTRY["S_w_all"].thetaR_func(w0, L, D)
                    else:
                        # 部分等分布荷重 (0からaLまで)
                        if pos_start == 0:
                            a = pos_end * L
                            if is_left_end:
                                result = BEAM_REGISTRY["S_w_b"].thetaL_func(w0, L, a, (L-a), D)
                            else:
                                result = - BEAM_REGISTRY["S_w_b"].thetaR_func(w0, L, a, (L-a), D)
                        elif pos_end == 1:
                            # 右端からaLまで (対称性利用)
                            a = (1 - pos_start) * L
                            if is_left_end:
                                result = BEAM_REGISTRY["S_w_b"].thetaR_func(w0, L, a, (L-a), D)
                            else:
                                result = - BEAM_REGISTRY["S_w_b"].thetaL_func(w0, L, a, (L-a), D)

                elif pos_start == 0 and pos_end == 1:
                    if action.function == "x/L":
                        # 三角形分布荷重
                        if is_left_end:
                            result = BEAM_REGISTRY["S_w_tri"].thetaL_func(w0, L, D)
                        else:
                            result = - BEAM_REGISTRY["S_w_tri"].thetaR_func(w0, L, D)
                    elif action.function == "1-x/L":
                        if is_left_end:
                            result = BEAM_REGISTRY["S_w_tri"].thetaR_func(w0, L, D)
                        else:
                            result = - BEAM_REGISTRY["S_w_tri"].thetaL_func(w0, L, D)
            
            elif isinstance(action, Action.ConcentratedMoment):
                m_actions = [a for a in self.actions if isinstance(a, Action.ConcentratedMoment)]
                idx = m_actions.index(action)
                Mc = sp.symbols(f"M_{idx}")
                pos = to_sym(action.position)
                a = pos * L
                b = (1 - pos) * L
                if is_left_end:
                    # CCW(Mc>0) at left end hogs -> v'(0) negative.
                    # registry returns Mc*(L^2-3b^2)/6DL. 
                    # If Mc>0, a=0, b=L -> (L^2-3L^2)/6DL = -L/3D. Correct.
                    result = BEAM_REGISTRY["S_M_a"].thetaL_func(Mc, L, a, b, D)
                else:
                    # CCW(Mc>0) at right end rotates it UP -> v'(L) positive.
                    # registry returns Mc*(L^2-3a^2)/6DL.
                    # If Mc>0, a=L, b=0 -> (L^2-3L^2)/6DL = -L/3D. Correct for v'(L).
                    result = BEAM_REGISTRY["S_M_a"].thetaR_func(Mc, L, a, b, D)

        elif case_type == "C_end":
            if fixed_at is not None:
                fixed_at_0 = (fixed_at == 0)
            else:
                fixed_supports = [s for s in self.supports if s[0] == "fixed"]
                if not fixed_supports: return None
                # fixed-fixedの場合は最初(通常0)を固定端とする
                fixed_pos_val = to_sym(fixed_supports[0][1])
                fixed_at_0 = (fixed_pos_val == 0)

            if isinstance(action, Action.ConcentratedLoad):
                total_p = len([a for a in self.actions if isinstance(a, Action.ConcentratedLoad)])
                if total_p > 1:
                    p_actions = [a for a in self.actions if isinstance(a, Action.ConcentratedLoad)]
                    idx = p_actions.index(action)
                    P = sp.symbols(f"P_{idx + 1}")
                else:
                    P = sp.symbols("P")

                pos = to_sym(action.position)
                rel_pos = pos if fixed_at_0 else (1 - pos)
                a = rel_pos * L
                # theta = P * a^2 / (2 * D)
                # if fixed_at_L, rotation at x=0 is CCW (negative)
                result = P * a**2 / (2 * D)
                if not fixed_at_0:
                    result = -result
            elif isinstance(action, Action.DistributedLoad):
                w0 = sp.symbols("w_0")
                pos_start = to_sym(action._position_range[0])
                pos_end = to_sym(action._position_range[1])
                if action.function == "1":
                    # theta = w0 * a^3 / (6 * D) (aは固定端からの長さ)
                    def f_cant_theta(x_r):
                        return w0 * (x_r * L)**3 / (6 * D)
                    if fixed_at_0:
                        result = f_cant_theta(pos_end) - f_cant_theta(pos_start)
                    else:
                        result = -(f_cant_theta(1 - pos_start) - f_cant_theta(1 - pos_end))
                elif pos_start == 0 and pos_end == 1:
                    if (fixed_at_0 and action.function == "1-x/L") or (not fixed_at_0 and action.function == "x/L"):
                        # registry: lambda w0, L, D: w0 * L**3 / (24 * D)
                        res = BEAM_REGISTRY["C_w_tri"].thetaL_func(w0, L, D)
                        result = res if fixed_at_0 else -res
                    elif (fixed_at_0 and action.function == "x/L") or (not fixed_at_0 and action.function == "1-x/L"):
                        # 三角形分布荷重 (自由端が最大) : 1/8 * w0 * L^3 / D
                        res = w0 * L**3 / (8 * D)
                        result = res if fixed_at_0 else -res
            elif isinstance(action, Action.ConcentratedMoment):
                m_actions = [a for a in self.actions if isinstance(a, Action.ConcentratedMoment)]
                idx = m_actions.index(action)
                Mc = sp.symbols(f"M_{idx}")
                pos = to_sym(action.position)
                rel_pos = pos if fixed_at_0 else (1 - pos)
                a_fixed = rel_pos * L
                # CCW正(Mc>0) at a_fixed rotates it UP -> theta negative (if fixed at 0)
                # If fixed at L, Mc>0 rotates it CW at 0 -> theta positive
                a_free = L - a_fixed
                res = BEAM_REGISTRY["C_M_a"].thetaL_func(Mc, L, a_free, D)
                # CCW(Mc>0) always produces CCW rotation (negative slope)
                result = -res

        if result is not None:
            return sp.nsimplify(sp.simplify(result), tolerance=1e-10, rational=True)
        return None


    def calculate_indeterminate_reaction_forces(self, target_symbols, force_equation, moment_equation0):
        """
        不静定梁の反力を計算する。
        まず重ね合わせの原理を試みる。
        重ね合わせの原理が使用できない問題の場合は，たわみの基礎式を用いた算出法を呼び出す。
        """
        
        # 重ね合わせの原理を試みる
        solutions = self.calculate_indeterminate_reaction_forces_by_superprinciple(target_symbols, force_equation, moment_equation0)
        if solutions:
            return solutions
        
        print("重ね合わせの原理による解法が適用できないため，たわみの基礎式を用いた解法にフォールバックします。")
        # 失敗した場合は従来の積分法を使用
        return self.calculate_indeterminate_reaction_forces_by_differencial(target_symbols, force_equation, moment_equation0)

    def calculate_indeterminate_reaction_forces_by_differencial(self, target_symbols, force_equation, moment_equation0):
        """
        不静定梁の反力を計算する。
        たわみの境界条件（支点位置でのたわみが0）を利用して，不足している方程式を補う。
        """
        import sympy as sp
        x = sp.symbols("x")
        L = sp.symbols("L")
        
        # 解説の追加
        self._add_indeterminate_explanation(target_symbols)

        # 曲げ剛性の確保
        if self._bending_stiffness is None:
            self.calculate_bending_stiffness()
        # self.bending_stiffness[0] は式としての EI
        
        # 1. 暫定的に反力をシンボルとして sectional forces を計算
        original_reaction_forces = self._reaction_forces[:]
        # 反力の式(r[3])にシンボル自身をセット
        self._reaction_forces = [(r[0], r[1], r[2], r[0]) for r in self._reaction_forces]
        
        # 断面力の説明が重複しないように一時的に退避して計算
        original_explanation_sectional = self._explanation_sectional_forces
        self.calculate_sectional_forces()
        self._explanation_sectional_forces = original_explanation_sectional # 元に戻す
        
        # 2. たわみの基礎式をセットアップ
        segments = self.bending_moment 
        n_segments = len(segments)
        C = [sp.symbols(f"C_{i}") for i in range(1, n_segments+1)]
        D = [sp.symbols(f"C_{i}") for i in range(len(C)+1, len(C)+n_segments+1)]
        
        slope_eqs = []
        deflection_eqs = []
        for i in range(n_segments):
            (s_r, e_r), M_eq = segments[i]
            # EI v'' = -M(x)  -> v' = int(-M/EI) + C
            # ここでは EI を掛けた状態で計算し，最後に割る形にする
            slope_val = sp.integrate(-M_eq, x) + C[i]
            slope_eqs.append(slope_val)
            deflection_val = sp.integrate(slope_val, x) + D[i]
            deflection_eqs.append(deflection_val)
            
        equations = []
        # 支点条件 (たわみ=0, 固定端ならたわみ角=0)
        for s_type, pos_ratio in self.supports:
            pos_x = pos_ratio * L
            idx = -1
            for i in range(n_segments):
                (s_r, e_r), _ = segments[i]
                if s_r <= pos_ratio <= e_r:
                    idx = i
                    break
            if idx != -1:
                if s_type == "fixed":
                    equations.append(sp.Eq(slope_eqs[idx].subs(x, pos_x), 0))
                equations.append(sp.Eq(deflection_eqs[idx].subs(x, pos_x), 0))
                
        # 連続条件
        for i in range(n_segments - 1):
            boundary_x = segments[i][0][1] * L
            equations.append(sp.Eq(slope_eqs[i].subs(x, boundary_x), slope_eqs[i+1].subs(x, boundary_x)))
            equations.append(sp.Eq(deflection_eqs[i].subs(x, boundary_x), deflection_eqs[i+1].subs(x, boundary_x)))
            
        # 3. 釣り合いの式を追加
        equations.append(sp.Eq(force_equation, 0))
        equations.append(sp.Eq(moment_equation0, 0))
        
        # 4. 解く
        all_unknowns = list(target_symbols) + C + D
        solutions = sp.solve(equations, all_unknowns)
        
        # 解が辞書形式でない（リスト形式など）場合の変換
        if isinstance(solutions, list) and len(solutions) > 0:
            solutions = solutions[0]
            
        # 支点反力のリストを元の構造に戻す（calculate_reaction_forces の続きで利用）
        self._reaction_forces = original_reaction_forces
        
        return solutions

    def calculate_reaction_forces(self):
        """
        反力を計算する。
        現在の実装は静定梁および一部の不静定梁に対応。
        支点反力は，(記号, 大きさ, 位置, 数式)のタプルのリストで保存。
        """
        
        self._reaction_forces = []
        self._explanation_reaction_forces = []
        self._lengths = [] # 呼び出しごとに初期化
        target_symbols = []

        dwg, length, center_x, center_y, height = self.generate_figure(return_parameters=True)

        #支点反力の個数を数える
        rn = 0; mn = 0
        for support in self.supports:
            if support[0] == "fixed":
                rn += 1; mn += 1
            elif support[0] == "pin":
                rn += 1
            elif support[0] == "roller":
                rn += 1
                
        #支点反力の定義
        reaction_loads_number = 0; reaction_moments_number = 0
        for support in self.supports:
            if support[0] == "fixed":
                reaction_moments_number += 1
                if mn > 1:
                    symbol = sp.symbols(f"M_R{reaction_moments_number}")
                else:
                    symbol = sp.symbols(f"M_R")
                self._reaction_forces.append((symbol, 0, support[1],0)) #記号，大きさ，位置，ほかの形式での数式
                target_symbols.append(symbol)

                dwg.draw_moment(
                    center=(float(center_x - length / 2 + support[1] * length), float(center_y)),
                    radius=10.0,
                    color = "red"
                )

                dwg.add(dwg.text(f'{str(symbol)[0]}', insert=(float(center_x - length / 2 + support[1] * length + 12), float(center_y - 12)), text_anchor="middle", alignment_baseline="middle", font_size=12, fill="red"))

                if len(str(symbol)) > 1:
                    dwg.add(dwg.text(f'{str(symbol)[2:]}', insert=(float(center_x - length / 2 + support[1] * length + 12 + 8), float(center_y - 11)), text_anchor="middle", alignment_baseline="middle", font_size=7, fill="red"))

            if support[0] == "pin" or support[0] == "roller" or support[0] == "fixed":
                reaction_loads_number += 1
                symbol = sp.symbols(f"R_{reaction_loads_number}") if rn > 1 else sp.symbols(f"R")
                self._reaction_forces.append((symbol, 0, support[1],0)) #鉛直反力（記号，大きさ，位置）
                target_symbols.append(symbol)

                dwg.draw_force(
                    start = (float(center_x - length / 2 + support[1] * length), float(center_y + height*1.7 + 20)),
                    end = (float(center_x - length / 2 + support[1] * length), float(center_y + height*1.7)),
                    color = "red"
                )

                dwg.add(dwg.text(f'{str(symbol)[0]}', insert=(float(center_x - length / 2 + support[1] * length + 8), float(center_y + height*1.7 + 20)), text_anchor="middle", alignment_baseline="middle", font_size=12, fill="red"))

                if len(str(symbol)) > 1:
                    dwg.add(dwg.text(f'{str(symbol)[2:]}', insert=(float(center_x - length / 2 + support[1] * length + 8 + 6), float(center_y + height*1.7 + 20)), text_anchor="middle", alignment_baseline="middle", font_size=7, fill="red"))


        #荷重の定義
        loads = []
        reaction_loads_number = 0
        for reaction in self._reaction_forces:
            if  "M" not in str(reaction[0]):
                loads.append(reaction)

        total_concentrated_loads_number = len([action for action in self.actions if isinstance(action, Action.ConcentratedLoad)])

        concentrated_loads_number = 0
        for action in self.actions:
            if isinstance(action, Action.ConcentratedLoad):
                concentrated_loads_number += 1
                if total_concentrated_loads_number > 1:
                    symbol = sp.symbols(f"P_{concentrated_loads_number}")
                else:
                    symbol = sp.symbols(f"P")
                loads.append((symbol, action.si_magnitude, action.position))
            
            if isinstance(action, Action.DistributedLoad):
                # 分布荷重は集中荷重に変換して扱う
                symbol = action.magnitude_eq
                magnitude = action.si_magnitude
                position = action.position
                loads.append((symbol, magnitude, position))


        # モーメントの定義
        def define_moments(center=0):
            moments = []

            #centerの位置にあるlengthsのsimbolを取得
            center_length_symbol = None
            for length in self._lengths:
                if length[1] == center:
                    center_length_symbol = length[0]
                    break

            if center_length_symbol is None:
                center_length_symbol = center * sp.symbols("L")

            for reaction in self._reaction_forces:
                if "M" in str(reaction[0]):
                    moments.append(reaction)

                elif "R" in str(reaction[0]):

                    # reaction[2]に対応するlengthのsimbolを取得
                    reaction_length_symbol = None
                    for length in self._lengths:
                        if length[1] == reaction[2]:
                            reaction_length_symbol = length[0]
                            break
                    if reaction_length_symbol is None:
                        reaction_length_symbol = reaction[2]
                    moment_symbol = reaction[0] * (center_length_symbol - reaction_length_symbol)
                    moments.append((moment_symbol, reaction[2], 0))

            concentrated_loads_number = 0
            concentrated_moments_number = 0

            for action in self.actions:
                if isinstance(action, Action.ConcentratedLoad):
                    concentrated_loads_number += 1

                    if total_concentrated_loads_number > 1:
                        symbol = sp.symbols(f"P_{concentrated_loads_number}")
                    else:
                        symbol = sp.symbols(f"P")

                    action_length_symbol = None
                    for length in self._lengths:
                        if length[1] == action.position:
                            action_length_symbol = length[0]
                            break

                    if action_length_symbol is None:
                        action_length_symbol = action.position

                    #作用位置に対応するlengthのsimbolを取得
                    action_length_symbol = None
                    for length in self._lengths:
                        if length[1] == action.position:
                            action_length_symbol = length[0]
                            break

                    if action_length_symbol is None:
                        action_length_symbol = action.position

                    moment_symbol = symbol * (action_length_symbol - center_length_symbol)
                    moments.append((moment_symbol, action.position))
                
                if isinstance(action, Action.ConcentratedMoment):
                    symbol = sp.symbols(f"M_{concentrated_moments_number}")
                    concentrated_moments_number += 1
                    moments.append((symbol, action.si_magnitude, action.position))
                
                if isinstance(action, Action.DistributedLoad):

                    # 分布荷重は集中荷重に変換して扱う
                    symbol = action.magnitude_eq

                    moment_symbol = symbol * (action.position_eq - center_length_symbol)
                    #print(f"分布荷重の作用位置のlengthシンボル: {action.position_eq}, 中心：{center_length_symbol}, モーメントシンボル: {moment_symbol}")
                    

                    moments.append((moment_symbol, action.position))
            
            return moments

        # 釣り合い式の作成
        force_equation = sum([load[0] if "R" in str(load[0]) else -load[0] for load in loads])
        moment_equations_info = []
        for length in self._lengths:
            moment_equations_info.append((length[2], sum([moment[0] if "M" in str(moment[0]) else -moment[0] for moment in define_moments(center=length[1])])))
        
        # 1. 釣り合い式の解説を追加
        self._add_equilibrium_explanation(force_equation, moment_equations_info)

        # 反力の個数と方程式の個数を比較して解法を分岐
        if (rn + mn) > 2:
            print("不静定梁の可能性があるため，たわみの基礎式を用いた解法を試みます。")
            solutions = self.calculate_indeterminate_reaction_forces(target_symbols, force_equation, moment_equations_info[0][1])
            self._explanation_reaction_forces.append(f"つり合いの式と合わせて，連立方程式を解くと，支点反力は，")
        else:
            # 連立方程式を解く (静定梁)
            solutions = sp.solve([force_equation, moment_equations_info[0][1]], target_symbols)
            self._explanation_reaction_forces.append(f"力のつり合いの式と合わせて，連立方程式を解くと，支点反力は，")

        #print(f"solutions: {solutions}")

        # 値代入用辞書の作成
        value_dict = {}

        # 長さ
        for length in self._lengths:
            if "*" not in str(length[0]) and "/" not in str(length[0]):
                #print(f"length: {length}")
                value_dict[length[0]] = self.si_length * length[1]
        # 荷重
        for load in loads:
            if "*" not in str(load[0]):
                value_dict[load[0]] = load[1]
        # モーメント
        for moment in define_moments(center=self._lengths[0][1]):
            if "*" not in str(moment[0]):
                value_dict[moment[0]] = moment[1]
        
        # 分布荷重の大きさ(複数ある場合は未対応)
        for action in self.actions:
            if isinstance(action, Action.DistributedLoad):
                value_dict["w_0"] = action.si_base_magnitude
        
        #円周率
        value_dict["pi"] = sp.pi
        
        # 2. 結果の解説を追加
        self._add_reaction_results_explanation(solutions, value_dict)

        self._figure_reaction_forces = dwg


    def calculate_sectional_forces(self):
        """
        断面力分布を計算する。
        1.自由体図の区間を取得
        2.各区間ごとに
        2.1.自由体図を作成
        2.2.力の釣合いからせん断力を計算
        2.3.モーメントの釣合いから曲げモーメントを計算
        """

        self._explanation_sectional_forces = []
        self._figures_sectional_forces = []
        self._shear_force = []
        self._bending_moment = []

        #1.自由体図の区間境界を取得
        division_points = [0, 1]
        for action in self.actions:
            if isinstance(action, Action.ConcentratedLoad):
                # 集中荷重の場合
                division_points.append(action.position)
            elif isinstance(action, Action.DistributedLoad):
                # 分布荷重の場合
                division_points.append(action._position_range[0])
                division_points.append(action._position_range[1])
            elif isinstance(action, Action.ConcentratedMoment):
                # 集中モーメントの場合
                division_points.append(action.position)
        
        for support in self.supports:
            division_points.append(support[1])
        
        #ソート
        division_points = sorted(list(set(division_points)))
        #重複を削除
        division_points = [point for i, point in enumerate(division_points) if point not in division_points[:i]]
        #自由体作図用に，division_pointsの中間点のリストを作成
        mid_points = [(division_points[i] + division_points[i + 1]) / 2 for i in range(len(division_points) - 1)]
        #0を削除
        division_points = division_points[1:]

        # 2.各区間ごとに処理
        left_side = 0
        for division_point, mid_point in zip(division_points, mid_points):
            #print(f"区間境界: {division_point}")
            #2.1.自由体図を作成
            
            self._figures_sectional_forces.append(self.generate_free_body_diagram(0, mid_point, text=f"Left side FBD at ({left_side:.1f}L<x<{division_point:.1f}L)"))
            self._figures_sectional_forces.append(self.generate_free_body_diagram(mid_point, 1, text=f"Right side FBD at ({left_side:.1f}L<x<{division_point:.1f}L)"))

            L = sp.symbols("L")
            self._explanation_sectional_forces.append("")
            self._explanation_sectional_forces.append(f"==== ${sp.nsimplify(left_side*L)}$<$x$<${sp.nsimplify(division_point*L)}$の区間に仮想断面を取った場合 ====")


            for side, s, e in zip(["左側", "右側"], [0, mid_point], [mid_point, 1]):
                #2.2.力の釣合いからせん断力を計算
                #左側

                self._explanation_sectional_forces.append(
                    f"【{side}の自由体】")
        
                self._explanation_sectional_forces.append(f"力のつり合いから，")
                force_balance = self.generate_force_balance_equation(s, e)
                self._explanation_sectional_forces.append(f"　${sp.nsimplify(force_balance)}$=$0$")
                moment_balance = self.generate_moment_balance_equation(s, e, sp.symbols("x"))
                self._explanation_sectional_forces.append(f"また，モーメントのつりあいから，")
                self._explanation_sectional_forces.append(f"　${sp.nsimplify(moment_balance)}$=$0$")

                # 力の釣合い式とモーメントの釣合い式を解く
                V, M = sp.symbols("V M")
                solutions = sp.solve([force_balance, moment_balance], (V, M))
                self._explanation_sectional_forces.append(f"２式を解くと，せん断力$V$と曲げモーメント$M$は，")

                # 支点反力の式を代入
                dict_reaction_forces = {r[0]: r[3] for r in self._reaction_forces}
                actV = sp.nsimplify(sp.simplify(solutions[V].subs(dict_reaction_forces)))
                actM = sp.nsimplify(sp.simplify(solutions[M].subs(dict_reaction_forces)))
                self._explanation_sectional_forces.append(f"　$V$=${sp.nsimplify(sp.simplify(solutions[V]))}$=${actV}$")
                self._explanation_sectional_forces.append(f"　$M$=${sp.nsimplify(sp.simplify(solutions[M]))}$=${actM}$")

                if side == "左側":
                    self._shear_force.append(((left_side, division_point), actV))
                    self._bending_moment.append(((left_side, division_point), actM))

            left_side = division_point
        self._explanation_sectional_forces.append(f"※自由体図は，左右どちら側を使用してもよいが，ここでは両方を示している。")

    def calculate_maximum_sectional_forces(self):
        """
        断面力の最大値を計算する。

        """

        # 値代入用辞書の作成
        dict = {sp.symbols("L"): self.si_length}

        concentrated_moments_number = 0
        concentrated_loads_number = 0

        for action in self.actions:

            if isinstance(action, Action.DistributedLoad):
                dict["w_0"] = action.si_base_magnitude

            if isinstance(action, Action.ConcentratedLoad):
                total_concentrated_loads_number = len([a for a in self.actions if isinstance(a, Action.ConcentratedLoad)])
                if isinstance(action, Action.ConcentratedLoad):
                    concentrated_loads_number += 1
                    if total_concentrated_loads_number > 1:
                        symbol = sp.symbols(f"P_{concentrated_loads_number}")
                    else:
                        symbol = sp.symbols(f"P")
                    dict[symbol] = action.si_magnitude

            if isinstance(action, Action.ConcentratedMoment):
                if isinstance(action, Action.ConcentratedMoment):
                    symbol = sp.symbols(f"M_{concentrated_moments_number}")
                    concentrated_moments_number += 1
                    dict[symbol] = action.si_magnitude

        #------------------辞書ここまで------------------

        #せん断力の最大値
        maximum_shear_force = 0
        points = []
        for (s,e), eq in self.shear_force:
            #print(f"せん断力の式: {eq}, 区間: {s} - {e}")
            # eqがxを含む場合、最大値・最小値を計算
            points.append((sp.nsimplify(s*sp.symbols("L")), eq))
            points.append((sp.nsimplify(e*sp.symbols("L")), eq))

            if sp.symbols("x") in eq.free_symbols:

                diff_eq = sp.diff(eq, sp.symbols("x"))#.subs(dict)
                try:
                    diff_eq_exact = sp.nsimplify(diff_eq, tolerance=1e-10)
                    interval_exact = sp.Interval(sp.nsimplify(s, tolerance=1e-10), sp.nsimplify(e, tolerance=1e-10))
                    critical_point = sp.solveset(sp.Eq(diff_eq_exact, 0), sp.symbols("x"), domain=interval_exact)
                except Exception:
                    critical_point = sp.S.EmptySet

                #print(f"critical_point: {critical_point}, class: {type(critical_point)}")
                if isinstance(critical_point, sp.FiniteSet):
                    for cp in critical_point:
                        points.append((cp, eq))

                if isinstance(critical_point, sp.Interval):
                    points.append((critical_point.start, eq))

                if isinstance(critical_point, sp.Intersection):
                    #print(f"arg[0]: {critical_point.args[0]},arg[1]: {critical_point.args[1]}")
                    for cp in critical_point.args[1].args:
                        cp_val = cp.subs(dict) / self.si_length
                        #print(f"cp: {cp}, cp_val: {cp_val}")
                        try:
                            if s <= cp_val and cp_val <= e:
                                points.append((cp, eq))
                        except:
                            pass

        for point, eq in points:
            value = eq.subs(sp.symbols("x"), point).subs(dict).evalf()
            if abs(value) >= abs(maximum_shear_force):
                maximum_shear_force = value
                
                if isinstance(point, float):
                    maximum_shear_force_eq = eq.subs(sp.symbols("x"), point * sp.symbols("L"))
                    x_absmax = point / self.si_length  # 無次元化
                else:
                    maximum_shear_force_eq = eq.subs(sp.symbols("x"), point)
                    x_absmax = point.subs(dict) / self.si_length  # 無次元化

        #計算条件を付与して簡略化
        maximum_shear_force_eq = str(maximum_shear_force_eq)
        L = sp.symbols("L", real=True, positive=True)
        maximum_shear_force_eq = sp.sympify(maximum_shear_force_eq, locals={"L": L})
        maximum_shear_force_eq = sp.simplify(sp.nsimplify(sp.simplify(maximum_shear_force_eq)))
                
        #曲げモーメントの最大値
        maximum_bending_moment = 0
        points = []
        for (s,e), eq in self.bending_moment:
            #print(s,e, eq)

            #print(f"曲げモーメントの式: {eq}, 区間: {s}m - {e}m")
            #区間内での最大値・最小値を計算

            points.append((sp.nsimplify(s*sp.symbols("L")), eq))
            points.append((sp.nsimplify(e*sp.symbols("L")), eq))
            if sp.symbols("x") in eq.free_symbols:

                diff_eq = sp.diff(eq, sp.symbols("x"))#.subs(dict)
                try:
                    diff_eq_exact = sp.nsimplify(diff_eq, tolerance=1e-10)
                    interval_exact = sp.Interval(sp.nsimplify(s, tolerance=1e-10), sp.nsimplify(e, tolerance=1e-10))
                    critical_point = sp.solveset(sp.Eq(diff_eq_exact, 0), sp.symbols("x"), domain=interval_exact)
                except Exception:
                    critical_point = sp.S.EmptySet

                #print(f"critical_point: {critical_point}, class: {type(critical_point)}")
                if isinstance(critical_point, sp.FiniteSet):
                    for cp in critical_point:
                        points.append((cp, eq))

                if isinstance(critical_point, sp.Interval):
                    points.append((critical_point.start, eq))

                if isinstance(critical_point, sp.Intersection):
                    #print(f"arg[0]: {critical_point.args[0]},arg[1]: {critical_point.args[1]}")
                    for cp in critical_point.args[1].args:
                        cp_val = cp.subs(dict) / self.si_length
                        #print(f"cp: {cp}, cp_val: {cp_val}")
                        try:
                            if s <= cp_val and cp_val <= e:
                                points.append((cp, eq))
                        except:
                            pass
            
        #print(f"points for maximum bending moment: {points}")

        for point, eq in points:
            value = eq.subs(sp.symbols("x"), point).subs(dict).evalf()
            if abs(value) >= abs(maximum_bending_moment):
                maximum_bending_moment = value
                
                if isinstance(point, float):
                    maximum_bending_moment_eq = eq.subs(sp.symbols("x"), point * sp.symbols("L"))
                    x_absmax = point / self.si_length  # 無次元化
                else:
                    maximum_bending_moment_eq = eq.subs(sp.symbols("x"), point)
                    x_absmax = point.subs(dict) / self.si_length  # 無次元化

        #計算条件を付与して簡略化
        maximum_bending_moment_eq = str(maximum_bending_moment_eq)
        L = sp.symbols("L", real=True, positive=True)
        maximum_bending_moment_eq = sp.sympify(maximum_bending_moment_eq, locals={"L": L})
        maximum_bending_moment_eq = sp.simplify(sp.nsimplify(sp.simplify(maximum_bending_moment_eq)))

        #print(f"最大曲げモーメント発生位置x: {x_max}")
        #print(f"!!!!!!!!!!最大曲げモーメントの式: {maximum_bending_moment_eq}") 
        self._maximum_shear_force = (maximum_shear_force_eq, maximum_shear_force, x_absmax)
        self._maximum_bending_moment = (maximum_bending_moment_eq, maximum_bending_moment, x_absmax)

    def calculate_stress_distribution(self):
        """
        上表面と下表面の応力分布を計算する。
        """
        self._explanation_stress = []
        self._top_stress = []
        self._bottom_stress = []

        I_eq, I_value = self.section.moment_of_inertia
        yg_eq, yg_value = self.section.centroid
        
        #print(self.bending_moment)
        for (s,e), M_eq in self.bending_moment:
            # 上表面の応力分布
            top_sigma_eq = M_eq * (-yg_eq) / I_eq
            self._top_stress.append(((s,e), top_sigma_eq))
            self._explanation_stress.append(f"区間${sp.nsimplify(s*sp.symbols('L'))}$<$x$<${sp.nsimplify(e*sp.symbols('L'))}$における上表面の応力分布は，")
            self._explanation_stress.append(f"　$\\sigma_{{top}}$=$M(x)/ I_z$$\\cdot$($-y_g$)=${sp.nsimplify(top_sigma_eq)}$")

            # 下表面の応力分布
            bottom_sigma_eq = M_eq * (sp.Symbol("H") - yg_eq) / I_eq
            self._bottom_stress.append(((s,e), bottom_sigma_eq))
            self._explanation_stress.append(f"同区間において，下表面の応力分布は，")
            self._explanation_stress.append(f"　$\\sigma_{{bottom}}$=$M(x)/ I_z$$\\cdot$($H-y_g$)=${sp.nsimplify(bottom_sigma_eq)}$")
        
        dict = {
            sp.symbols("L"): sp.symbols("L", real=True, positive=True),
            sp.symbols("H"): sp.symbols("H", real=True, positive=True),
            sp.symbols("B"): sp.symbols("B", real=True, positive=True),
            sp.symbols("P"): sp.symbols("P", real=True, positive=True),
            sp.symbols("I_z"): sp.symbols("I_z", real=True, positive=True),
            sp.symbols("y_g"): sp.symbols("y_g", real=True, positive=True),
        }
        values_dict = {
            sp.symbols("L"): self.length,
            sp.symbols("H"): self.section.height,
            sp.symbols("B"): self.section.width,
            sp.symbols("I_z"): self.section.moment_of_inertia[1],
            sp.symbols("y_g"): self.section.centroid[1],
            sp.symbols("pi"): sp.pi,
        }

        if self.section.thickness is not None:
            dict[sp.symbols("t")] = sp.symbols("t", real=True, positive=True)
            values_dict[sp.symbols("t")] = self.section.thickness

        concentrated_moments_number=0; concentrated_loads_number = 0

        for action in self.actions:

            if isinstance(action, Action.DistributedLoad):
                values_dict["w_0"] = action.si_base_magnitude / 1e3
                new_symbol = sp.symbols("w_0", real=True, positive=True)
                dict["w_0"] = new_symbol

            if isinstance(action, Action.ConcentratedLoad):
                total_concentrated_loads_number = len([a for a in self.actions if isinstance(a, Action.ConcentratedLoad)])
                if isinstance(action, Action.ConcentratedLoad):
                    concentrated_loads_number += 1
                    if total_concentrated_loads_number > 1:
                        symbol = sp.symbols(f"P_{concentrated_loads_number}")
                        new_symbol = sp.symbols(f"P_{concentrated_loads_number}", real=True, positive=True)
                    else:
                        symbol = sp.symbols(f"P")
                        new_symbol = sp.symbols(f"P", real=True, positive=True)
                    values_dict[symbol] = action.si_magnitude
                    dict[symbol] = new_symbol

            if isinstance(action, Action.ConcentratedMoment):
                if isinstance(action, Action.ConcentratedMoment):
                    symbol = sp.symbols(f"M_{concentrated_moments_number}")
                    new_symbol = sp.symbols(f"M_{concentrated_moments_number}", real=True, positive=True)
                    concentrated_moments_number += 1
                    values_dict[symbol] = action.si_magnitude * 1e3
                    dict[symbol] = new_symbol

        maximum_stress = 0; maximum_stress_eq = None
        minimum_stress = 0; minimum_stress_eq = None
        for (s,e), eq in self.top_stress + self.bottom_stress:
            bufmax = sp.maximum(eq.subs(dict), sp.symbols("x"), sp.Interval(s*sp.symbols("L",real=True, positive=True),e*sp.symbols("L",real=True, positive=True)))
            bufmax_value = sp.maximum(eq.subs(values_dict), sp.symbols("x"), sp.Interval(s*self.length,e*self.length)).evalf()
            if bufmax_value >= maximum_stress:
                maximum_stress = bufmax_value
                maximum_stress_eq = bufmax
            
            bufmin = sp.minimum(eq.subs(dict), sp.symbols("x"), sp.Interval(s*sp.symbols("L",real=True, positive=True),e*sp.symbols("L",real=True, positive=True)))
            bufmin_value = sp.minimum(eq.subs(values_dict), sp.symbols("x"), sp.Interval(s*self.length,e*self.length)).evalf()

            # 996行目の後に追加
            bufmin_value = sp.minimum(eq.subs(values_dict), sp.symbols("x"), sp.Interval(s*self.length,e*self.length)).evalf()

            # もし計算結果が Float (数値) でない場合にエラー箇所を特定する
            if not bufmin_value.is_Number:
                print(f"Error: bufmin_value contains symbols: {bufmin_value.free_symbols}")
                # 応急処置として、未評価の変数を0などで置換するか、エラーを特定する

            if bufmin_value <= minimum_stress:
                minimum_stress = bufmin_value
                minimum_stress_eq = bufmin

        self._minimum_stress = (minimum_stress_eq, minimum_stress)
        self._maximum_stress = (maximum_stress_eq, maximum_stress)

        self._explanation_stress.append(f"これらをグラフ化すると，最大応力は，")
        self._explanation_stress.append(f"　$\\sigma_{{max}}$=${sp.nsimplify(maximum_stress_eq)}$={maximum_stress:.3f} MPa")
        self._explanation_stress.append(f"最小応力は，")
        self._explanation_stress.append(f"　$\\sigma_{{min}}$=${sp.nsimplify(minimum_stress_eq)}$={minimum_stress:.3f} MPa")
        
    def calculate_bending_stiffness(self):
        """
        曲げ剛性を計算する。
        """
        self._explanation_bending_stiffness = []
        I_eq, I_value = self.section.moment_of_inertia
        self._bending_stiffness = (I_eq * sp.symbols("E"), I_value* 1e-12 * self.material.young_modulus)
        self._explanation_bending_stiffness.append(f"曲げ剛性は，断面二次モーメント$I_z$と縦弾性係数$E$の積で表される。")
        self._explanation_bending_stiffness.append(f"　$D=EI_z=$${I_eq}$$\\cdot E$={I_value*1e-12:.3g} m⁴ × {self.material.young_modulus:.3g} N/m² = {self._bending_stiffness[1]:.3g} Nm²")

    def calculate_deflection(self):
        """
        梁のたわみ角とたわみ量を計算する。
        EI v'' = M(x) を2回積分し，境界条件と連続条件から積分定数を求める。
        """
        import sympy as sp
        x = sp.symbols("x")
        L = sp.symbols("L")
        EI = self.bending_stiffness[0] # 式としてのEI
        
        self._explanation_deflection = [
            "梁のたわみの基礎式 $D \\frac{d^2y(x)}{dx^2} = -M(x)$ を各区間で2回積分して求める。",
            f"ここで，曲げ剛性 $D = {sp.latex(EI)}$ である。"
        ]
        
        # 区間ごとのモーメント式を取得
        segments = self.bending_moment # [((s, e), M_eq), ...]
        n_segments = len(segments)
        
        # 積分定数の定義
        C = [sp.symbols(f"C_{i}") for i in range(1, n_segments+1)] # たわみ角用
        D = [sp.symbols(f"C_{i}") for i in range(len(C)+1, len(C)+n_segments+1)] # たわみ用
        
        slope_eqs = []
        deflection_eqs = []
        
        # 2回積分して一般解を作成
        for i in range(n_segments):
            (s_r, e_r), M_eq = segments[i]
            self._explanation_deflection.append(f"==== 区間 ${sp.latex(sp.nsimplify(s_r*L))}$<$x$<${sp.latex(sp.nsimplify(e_r*L))}$ ====")
            
            # 1回目積分 (EI * v' = int(M) + C)
            slope_val = sp.nsimplify(sp.simplify(sp.integrate(-M_eq, x) + C[i]))
            slope_eqs.append(slope_val)
            self._explanation_deflection.append(f"　$D i(x) = \\int ({sp.latex(sp.nsimplify(M_eq))}) dx = {sp.latex(slope_val)}$")
            
            # 2回目積分 (EI * v = int(EI * v') + D)
            deflection_val = sp.nsimplify(sp.simplify(sp.integrate(slope_val, x) + D[i]))
            deflection_eqs.append(deflection_val)
            self._explanation_deflection.append(f"　$D y(x) = \\int ({sp.latex(slope_val)}) dx = {sp.latex(deflection_val)}$")
            
        # 方程式リスト
        equations = []
        self._explanation_deflection.append(f"続いて，境界条件から条件式を作ると，")

        # 1. 境界条件 (支点)
        for s_type, pos_ratio in self.supports:
            pos_x = pos_ratio * L
            # どの区間に属するか判定
            idx = -1
            for i in range(n_segments):
                (s_r, e_r), _ = segments[i]
                if s_r <= pos_ratio <= e_r:
                    idx = i
                    break

            if idx != -1:
                pos_x_simp = sp.nsimplify(pos_x)
                # 固定支点なら たわみ角 v' = 0 (EI * v' = 0)
                if s_type == "fixed":
                    eq = sp.nsimplify(sp.Eq(slope_eqs[idx].subs(x, pos_x), 0))
                    equations.append(eq)
                    self._explanation_deflection.append(f"　・固定端 $x={sp.latex(pos_x_simp)}$ でのたわみ角 $i=0$ より：${sp.latex(eq)}$")

                # たわみ v = 0 (EI * v = 0)
                eq = sp.nsimplify(sp.Eq(deflection_eqs[idx].subs(x, pos_x), 0))
                equations.append(eq)
                self._explanation_deflection.append(f"　・支点 $x={sp.latex(pos_x_simp)}$ でのたわみ $y=0$ より：${sp.latex(eq)}$")

                    
        # 2. 連続条件 (区間の境界)
        for i in range(n_segments - 1):
            boundary_x = segments[i][0][1] * L # 現在の区間の終点
            # たわみ角の連続 (左の終端 = 右の始端)
            slope_cont_eq = sp.Eq(slope_eqs[i].subs(x, boundary_x), slope_eqs[i+1].subs(x, boundary_x))
            equations.append(slope_cont_eq)
            self._explanation_deflection.append(f"　・境界 $x={sp.latex(sp.nsimplify(boundary_x))}$ でのたわみ角の連続条件より：${sp.latex(sp.nsimplify(slope_cont_eq))}$")
            
            # たわみの連続
            deflect_cont_eq = sp.Eq(deflection_eqs[i].subs(x, boundary_x), deflection_eqs[i+1].subs(x, boundary_x))
            equations.append(deflect_cont_eq)
            self._explanation_deflection.append(f"　・同境界でのたわみ量の連続条件より：${sp.latex(sp.nsimplify(deflect_cont_eq))}$")
            
        # 連立方程式を解く
        constants = sp.solve(equations, C + D)
        self._explanation_deflection.append("これらの条件式を連立方程式として解き，積分定数を決定すると，")
        
        # 積分定数の表示を追加
        if constants:
            # 辞書形式であることを想定（線形連立方程式のため）
            c_list = []
            for sym in (C + D):
                val = constants.get(sym)
                if val is not None:
                    c_list.append(f"{sp.latex(sym)} = {sp.latex(sp.nsimplify(sp.simplify(val)))}")
            if c_list:
                self._explanation_deflection.append(f"　${', '.join(c_list)}$")
        
        # 結果の格納
        self._slope = []
        self._deflection = []
        D_sym = sp.symbols("D") # 曲げ剛性のシンボル
        for i in range(n_segments):
            (s_r, e_r), _ = segments[i]
            
            # Dをシンボルとした式
            slope_d = sp.nsimplify(sp.simplify((slope_eqs[i].subs(constants)) / D_sym))
            deflection_d = sp.nsimplify(sp.simplify((deflection_eqs[i].subs(constants)) / D_sym))

            self._slope.append(((s_r, e_r), slope_d))
            self._deflection.append(((s_r, e_r), deflection_d))
            
            self._explanation_deflection.append(f"区間 ${sp.latex(sp.nsimplify(s_r*L))}$<$x$<${sp.latex(sp.nsimplify(e_r*L))}$ のたわみ角曲線$i(x)$，たわみ曲線$y(x)$はそれぞれ，")
            self._explanation_deflection.append(f"　$i(x) = {sp.latex(slope_d)}$")
            self._explanation_deflection.append(f"　$y(x) = {sp.latex(deflection_d)}$")


    def calculate_maximum_slope_and_deflection(self):
        """
        たわみ角とたわみ量の最大値を計算する。
        """
        import sympy as sp
        x = sp.symbols("x")
        L_sym = sp.symbols("L")
        D_sym = sp.symbols("D")
        EI_sym = sp.symbols("EI")
        
        # 値代入用辞書の作成
        dict_vals = {
            L_sym: self.si_length,
            sp.symbols("E"): self.material.young_modulus if self.material else 200e9,
            sp.symbols("B"): self.section.width / 1000 if self.section else 0.1,
            sp.symbols("H"): self.section.height / 1000 if self.section else 0.1,
            sp.symbols("I_z"): self.section.moment_of_inertia[1] * 1e-12 if self.section else 1e-6,
            sp.symbols("y_g"): self.section.centroid[1] / 1000 if self.section else 0.05,
            sp.symbols("D"): self.bending_stiffness[1],
            sp.symbols("pi"): sp.pi,
        }
        if self.section and self.section.thickness:
            dict_vals[sp.symbols("t")] = self.section.thickness / 1000

        # 荷重などのシンボルと値の対応
        concentrated_moments_number = 0
        concentrated_loads_number = 0
        for action in self.actions:
            if isinstance(action, Action.DistributedLoad):
                dict_vals[sp.symbols("w_0")] = action.si_base_magnitude
            if isinstance(action, Action.ConcentratedLoad):
                total_p = len([a for a in self.actions if isinstance(a, Action.ConcentratedLoad)])
                symbol = sp.symbols("P" if total_p == 1 else f"P_{concentrated_loads_number+1}")
                dict_vals[symbol] = action.si_magnitude
                concentrated_loads_number += 1
            if isinstance(action, Action.ConcentratedMoment):
                symbol = sp.symbols(f"M_{concentrated_moments_number}")
                dict_vals[symbol] = action.si_magnitude
                concentrated_moments_number += 1

        # たわみ角の最大値探索
        max_slope_val = 0.0
        max_slope_raw_eq = None # 1/Dを含む式
        x_slope_max = 0
        
        for (s, e), eq in self.slope:
            points = [s * L_sym, e * L_sym]
            # 極値点
            if x in eq.free_symbols:
                diff_eq = sp.diff(eq, x)
                try:
                    critical_points = sp.solve(sp.Eq(diff_eq, 0), x)
                    for cp in critical_points:
                        cp_val = cp.subs(dict_vals).evalf()
                        if cp_val.is_real and s * self.si_length <= float(cp_val) <= e * self.si_length:
                            points.append(cp)
                except: pass
            
            for p in points:
                # 数値に変換して比較
                res = eq.subs(x, p).subs(dict_vals).evalf()
                val = float(abs(res))
                if val >= abs(float(max_slope_val)):
                    max_slope_val = float(res)
                    max_slope_raw_eq = eq.subs(x, p)
                    x_slope_max = float(p.subs(dict_vals).evalf()) / self.si_length

        # たわみ量の最大値探索
        max_defl_val = 0.0
        max_defl_raw_eq = None
        x_defl_max = 0
        
        for (s, e), eq in self.deflection:
            points = [s * L_sym, e * L_sym]
            # 極値点
            slope_eq = next(seq for (ss, ee), seq in self.slope if ss == s and ee == e)
            if x in slope_eq.free_symbols:
                try:
                    critical_points = sp.solve(sp.Eq(slope_eq, 0), x)
                    for cp in critical_points:
                        cp_val = cp.subs(dict_vals).evalf()
                        if cp_val.is_real and s * self.si_length <= float(cp_val) <= e * self.si_length:
                            points.append(cp)
                except: pass
                
            for p in points:
                res = eq.subs(x, p).subs(dict_vals).evalf()
                val = float(abs(res))
                if val >= abs(float(max_defl_val)):
                    max_defl_val = float(res)
                    max_defl_raw_eq = eq.subs(x, p)
                    x_defl_max = float(p.subs(dict_vals).evalf()) / self.si_length

        # 単位変換や簡略化
        L_real = sp.symbols("L", real=True, positive=True)
        E_sym = sp.symbols("E")
        
        # D-form: Dを記号として残す
        max_slope_d = sp.simplify(sp.nsimplify(max_slope_raw_eq.subs(L_sym, L_real)))
        max_defl_d = sp.simplify(sp.nsimplify(max_defl_raw_eq.subs(L_sym, L_real)))

        # Expanded-form: DをE*(Izの公式)に置き換えた記号式を表示
        I_z_eq = self.section.moment_of_inertia[0]
        max_slope_sub = sp.simplify(sp.nsimplify(max_slope_raw_eq.subs(sp.symbols("D"), E_sym * I_z_eq).subs(L_sym, L_real)))
        max_defl_sub = sp.simplify(sp.nsimplify(max_defl_raw_eq.subs(sp.symbols("D"), E_sym * I_z_eq).subs(L_sym, L_real)))

        # 解説の再構築
        fundamental_exp = []
        fundamental_exp.append("得られた，たわみ角曲線$i(x)$，たわみ曲線$y(x)$より，最大たわみ角$\\theta$と最大たわみ量$\\delta$を求める。")
        fundamental_exp.append(f"　$\\theta$ = $|i({sp.nsimplify(x_slope_max* L_sym)})|$ = $|{sp.latex(max_slope_d)}| = |{sp.latex(max_slope_sub)}|$ = {abs(max_slope_val):.3g} rad")
        fundamental_exp.append(f"　$\\delta$ = $|y({sp.nsimplify(x_defl_max* L_sym)})|$ = $|{sp.latex(max_defl_d)}| = |{sp.latex(max_defl_sub)}|$ = {abs(max_defl_val):.3g} m")

        # 面積モーメント法の解説作成
        area_moment_exp = []
        area_moment_exp.append("【面積モーメント法を用いた方法】")
        # 片持ち梁か単純支持梁かで方針を変える
        is_cantilever = any(s[0] == "fixed" for s in self.supports)
        
        
        # 2支点梁（単純支持・突き出し梁）の場合、支点間の中心のたわみを最大と近似する解説を追加
        approx_exp = []
        support_positions = sorted([s[1] for s in self.supports if s[0] in ["pin", "roller"]])
        if len(support_positions) == 2:
            # 支点間の中心を計算
            center_x_ratio = sum(support_positions) / 2
            
            # 支点間中央のたわみ
            center_defl_eq = None
            for (s, e), eq in self.deflection:
                if s <= center_x_ratio <= e:
                    center_defl_eq = eq.subs(x, center_x_ratio * L_sym)
                    break
            center_defl_val = float(abs(center_defl_eq.subs(dict_vals).evalf()))

            # 自由端のたわみ
            free_end_defl_val = 0
            free_end_defl_eq = None
            if len(self.supports) >= 2:
                left_free = True; right_free = True
                for p in support_positions:
                    #print(f"support position: {p}")
                    if p == 0:
                        left_free = False
                    if p == 1:
                        right_free = False
                
                if left_free:
                    left_free_eq = self.deflection[0][1].subs(x, 0)
                    left_free_val = float(abs(left_free_eq.subs(dict_vals).evalf()))
                    print(f"left_free_eq: {left_free_eq}, left_free_val: {left_free_val}")
                else:
                    left_free_eq = None
                    left_free_val = 0

                if right_free:
                    right_free_eq = self.deflection[-1][1].subs(x, 1*L_sym)
                    right_free_val = float(abs(right_free_eq.subs(dict_vals).evalf()))
                    print(f"right_free_eq: {right_free_eq}, right_free_val: {right_free_val}")
                else:
                    right_free_eq = None
                    right_free_val = 0


            if left_free_val >= right_free_val:
                free_end_defl_val = left_free_val
                free_end_defl_eq = left_free_eq
                free_end_x = 0
            else:
                free_end_defl_val = right_free_val
                free_end_defl_eq = right_free_eq
                free_end_x = 1
        
            #print(f"center_defl_val: {center_defl_val}, free_end_defl_val: {free_end_defl_val}")
            if free_end_defl_val > center_defl_val:
                max_defl_val = free_end_defl_val
                max_defl_eq = free_end_defl_eq
                x_defl_max = free_end_x
                is_free_end_max = True
            else:
                max_defl_val = center_defl_val
                max_defl_eq = center_defl_eq
                x_defl_max = center_x_ratio
                is_free_end_max = False

            # 近似用の式を簡略化
            # 数値評価用の辞書
            eval_dict = dict_vals.copy()
            # EI_sym を実際の剛性値 D で置換して数値評価できるようにする
            eval_dict[EI_sym] = self.bending_stiffness[1]
            
            # 数値計算された値
            max_defl_val = float(abs(max_defl_eq.subs(dict_vals).evalf()))
            
            approx_exp.append("【簡易計算（支点間中央または自由端のたわみによる近似）】")
            if self.is_simply_supported():
                approx_exp.append("変形方向が同じ作用のみの単純支持梁では，最大たわみは梁の中心付近となる。ここでは近似値として，梁の中心 ($x=L/2$) におけるたわみ量を最大たわみ量$\\delta$とする。")
            else:
                x_val_display = x_defl_max

                if is_free_end_max:
                    approx_exp.append(f"この梁では，支点間の中央のたわみよりも自由端 ($x={x_val_display:.3f}L$) におけるたわみ量の方が大きいため，これを最大たわみ量$\\delta$とする。")
                else:
                    approx_exp.append(f"突き出し梁の支点間のたわみは，支点間の中央付近または自由端で最大となる。今回は支点間の中央 ($x={x_val_display:.3f}L$) のたわみ量の方が自由端よりも大きいため，これを最大たわみ量$\\delta$とする。")
            
            approx_exp.append(f"　$\\delta$ =$|y({sp.nsimplify(x_defl_max* L_sym)})|$= ${max_defl_eq}$ = {max_defl_val:.4g} m")

        if is_cantilever:
            fixed_pos = next(s[1] for s in self.supports if s[0] == "fixed")
            target_pos = x_defl_max
            area_moment_exp.append(f"固定端 ($x={fixed_pos}L$) と最大たわみ発生点 ($x={target_pos:.3f}L$) の間の $M/EI$ 図の面積 $A$ と，その図心の最大たわみ発生点からの距離 $x_g$ を求める。")
            
            EI = self.bending_stiffness[0]
            # M/EI の積分 (面積)
            M_integrand = 0
            M_x_integrand = 0
            for (s, e), M_eq in self.bending_moment:
                # 区間の重なりを計算
                s_int = max(s, min(fixed_pos, target_pos))
                e_int = min(e, max(fixed_pos, target_pos))
                if s_int < e_int:
                    M_integrand += sp.integrate(M_eq / EI, (x, s_int * L_sym, e_int * L_sym))
                    M_x_integrand += sp.integrate((M_eq / EI) * (target_pos * L_sym - x), (x, s_int * L_sym, e_int * L_sym))
            
            A = sp.simplify(sp.nsimplify(M_integrand.subs(L_sym, L_real)))
            A_ei = sp.simplify(sp.nsimplify((A * self.bending_stiffness[0] / EI_sym).subs(L_sym, L_real)))
            A_val = abs(float(M_integrand.subs(dict_vals).evalf()))
            
            Mx_ei = sp.simplify(sp.nsimplify((M_x_integrand * self.bending_stiffness[0] / EI_sym).subs(L_sym, L_real)))
            Mx_val_eq = sp.simplify(sp.nsimplify(M_x_integrand.subs(L_sym, L_real)))
            M_x_val = abs(float(M_x_integrand.subs(dict_vals).evalf()))
            
            area_moment_exp.append(f"　面積 $A = |\\int_{{{fixed_pos}L}}^{{{target_pos:.3f}L}} \\frac{{M(x)}}{{EI}} dx| = |{sp.latex(A_ei)}| = |{sp.latex(A)}| = {A_val:.3g}$")
            area_moment_exp.append(f"　モーメント $A \\cdot x_g = |\\int_{{{fixed_pos}L}}^{{{target_pos:.3f}L}} \\frac{{M(x)}}{{EI}} ({target_pos:.3f}L - x) dx| = |{sp.latex(Mx_ei)}| = |{sp.latex(Mx_val_eq)}| = {M_x_val:.3g}$")
            area_moment_exp.append(f"よって，")
            area_moment_exp.append(f"　$\\theta = A = {A_val:.3g}$ rad")
            area_moment_exp.append(f"　$\\delta = A \\cdot x_g = {M_x_val:.3g}$ m")

        elif len(support_positions) == 2:
            area_moment_exp.append("2支点梁の場合，支点間の $M/EI$ 線図の面積とそのモーメントから，各点のたわみを求めることができる。")
            area_moment_exp.append(f"支点間の中央 ($x$=${sp.nsimplify(center_x_ratio)}L$) における値は以下の通り。")
            area_moment_exp.append(f"　$\\theta = {abs(max_slope_val):.3g}$ rad")
            area_moment_exp.append(f"　$\\delta = {abs(max_defl_val):.3g}$ m")

        self._explanation_deflection = self._explanation_deflection + fundamental_exp + approx_exp + area_moment_exp

        self._maximum_slope = (max_slope_d, abs(max_slope_val), x_slope_max)
        self._maximum_deflection = (max_defl_d, abs(max_defl_val), x_defl_max)


    def generate_free_body_diagram(self, start_x, end_x, text=""):
        """
        自由体図を作成する。
        start_x: 図の開始位置（xの位置0-1）
        end_x: 図の終了位置（xの位置0-1）
        """
        # 自由体図を作成するための処理をここに追加


        maximum_force_length = 20  # 荷重の長さの最大値
        concentrated_loads = len([action for action in self.actions if isinstance(action, Action.ConcentratedLoad)])
        distributed_loads = len([action for action in self.actions if isinstance(action, Action.DistributedLoad)])

        action_dimension_number = 1

        # 分布荷重のみ寸法引き出し線を記載   
        for action in self.actions:
            if isinstance(action, Action.DistributedLoad):
                if action._position_range[0] != 0 and (action._position_range[0] >= start_x or action._position_range[0] <= end_x):
                    action_dimension_number += 1
                if action._position_range[1] != 1 and (action._position_range[1] >= start_x or action._position_range[1] <= end_x):
                    action_dimension_number += 1

        support_initial_height_ratio = 4
        support_dimension_height_ratio = 3.6
        height = 10  # 梁の高さ（固定）


        #図のサイズを決定
        dwg = Figure(
            size = (
                162,
                60 + action_dimension_number * height * support_dimension_height_ratio + distributed_loads * height * 2
            + support_initial_height_ratio * height)
        )
        #figureの外枠（デバッグ用）
        #dwg.add(dwg.rect(insert=(0, 0), size=(dwg.width, dwg.height), fill='none', stroke='red', stroke_width=1))


        # 左上にtextを追加
        if text != "":
            dwg.add(dwg.text(text, insert=(0, 10), font_size=10, fill="black"))


        # 図の中心を取得
        length = dwg.width * 0.8   # 図の長さ（80%）

        sx= float(0.1 * dwg.width + length * start_x)  # 図の開始位置（左端）
        ex= float(sx + length * (end_x - start_x))  # 図の終了位置（右端）
        center_y = float(dwg.height / 2 + (action_dimension_number-1) * height * support_dimension_height_ratio + distributed_loads * height * 2)
        
        # 梁本体を書く（長方形固定）
        dwg.add(dwg.rect(insert=(sx, center_y - height / 2), size=(ex-sx, height), fill='white', stroke='black', stroke_width=1.5))
        
        #寸法線を記載する
        if start_x == 0 and end_x < 1:
            dwg.draw_equation(f'V', position=(float(ex+8), float(center_y + height / 2 + 20)), color="red")
            dwg.draw_force(start=(float(ex+3), float(center_y - height / 2 - 5)), end=(float(ex+3), float(center_y + height / 2 + 5)), color="red")
            dwg.draw_equation(f'M', position=(float(ex+10), float(center_y - height / 2 - 10)), color="red")
            dwg.draw_moment(center=(float(ex), float(center_y)), radius=float(height*1.5), color="red", angle_range=(40, 140))
            
            #寸法xを記載する
            #引き出し線
            dwg.add(dwg.line((float(sx), float(center_y + height / 2)), (float(sx), float(center_y + height / 2 + 50)),
                stroke="black", stroke_width=0.75, stroke_linecap="round"))
            dwg.add(dwg.line((float(ex), float(center_y + height / 2)), (float(ex), float(center_y + height / 2 + 50)),
                stroke="black", stroke_width=0.75, stroke_linecap="round"))
            dwg.draw_arrow((float(sx), float(center_y + height / 2 + 47)), (float(ex), float(center_y + height / 2 + 47)), arrow_type="both", color="black")
            dwg.draw_equation(f'x', position=(float((sx+ex)/2), float(center_y + height / 2 + 42)), color="black")

        elif start_x > 0 and end_x == 1:
            dwg.draw_equation(f'V', position=(float(sx-8), float(center_y + height / 2 + 20)), color="red")
            dwg.draw_force(start=(float(sx-3), float(center_y + height / 2+5)), end=(float(sx-3), float(center_y - height / 2 - 5)), color="red")
            dwg.draw_equation(f'M', position=(float(sx-10), float(center_y - height / 2 - 10)), color="red")
            dwg.draw_moment(center=(float(sx), float(center_y)),direction="CW", radius=float(height*1.5), color="red", angle_range=(40, 140))
            #寸法( L - x )を記載する
            dwg.add(dwg.line((float(sx), float(center_y + height / 2)), (float(sx), float(center_y + height / 2 + 50)),
                stroke="black", stroke_width=0.75, stroke_linecap="round"))
            dwg.add(dwg.line((float(ex), float(center_y + height / 2)), (float(ex), float(center_y + height / 2 + 50)),
                stroke="black", stroke_width=0.75, stroke_linecap="round"))
            dwg.draw_arrow((float(sx), float(center_y + height / 2 + 47)), (float(ex), float(center_y + height / 2 + 47)), arrow_type="both", color="black")
            dwg.draw_equation(f'L-x', position=(float((sx+ex)/2), float(center_y + height / 2 + 42)), color="black")


        #支点反力を書く
        for reaction in self.reaction_forces:
            #print(f"reaction position: {reaction[2]}, start_x: {start_x}, end_x: {end_x}")
            #print(reaction[2]>=start_x, reaction[2]<=end_x)
            if reaction[2] >= start_x and reaction[2] <= end_x:
                position = float(sx + (reaction[2] - start_x) * length)

                if "M" in str(reaction[0]):
                    dwg.draw_moment(
                        center = (position, float(center_y)),
                        radius = float(height),
                        color = "red"
                    )
                    dwg.draw_equation(f'{reaction[0]}', position=(float(position + 10), float(center_y - height - 7)), color="red")
                
                else:
                    dwg.draw_force(
                        start = (position, float(center_y + height * 0.5 + 23)),
                        end = (position, float(center_y + height * 0.5 + 3)),
                        color = "red"
                    )
                    dwg.draw_equation(f'{reaction[0]}', position=(float(position + 8), float(center_y + height*1.7 + 20)), color="red")

        # 作用を書く
        cln = 1; cmn = 0; dln = 1
        for i, action in enumerate(self.actions):
            if isinstance(action, Action.ConcentratedLoad):
                if action.position >= start_x and action.position <= end_x:
                    
                    force_length = float(maximum_force_length)
                    position = float(sx + (action.position - start_x) * length)

                    dwg.draw_force(
                        start = (position, float(center_y - height / 2 - force_length-5)),
                        end = (position, float(center_y - height / 2 - 2)), 
                    )

                    #テキスト
                    y_offset = -50 if distributed_loads > 0 else 0
                    x_offset = -10 if distributed_loads > 0 else 0
                    
                    if concentrated_loads != 1:
                        dwg.draw_equation(f'P_{cln}', position=(float(position  + 10 + x_offset), float(center_y - height / 2 - force_length - 8 - y_offset)))
                    else:
                        dwg.draw_equation(f'P', position=(float(position + 10 + x_offset), float(center_y - height / 2 - force_length - 8 - y_offset)))
                cln += 1

            if isinstance(action, Action.ConcentratedMoment):
                if action.position >= start_x and action.position <= end_x:
                    position = float(sx + (action.position - start_x) * length)
                    dwg.draw_moment(
                        center = (position, float(center_y)),
                        radius = float(height),
                        color = "black"
                    )
                    #テキスト
                    dwg.draw_equation(f'M_{cmn}', position=(float(position + 10), float(center_y - height - 2)))
                cmn += 1

            if isinstance(action, Action.DistributedLoad):
                    if start_x == 0:
                        magnitude_eq, position_eq = action.equivalent_concentrated_load_of_FBD("0", "x", end_x)
                        subs = {
                            sp.symbols("w_0"): action.si_base_magnitude, 
                            sp.symbols("x"): (end_x - start_x) * self.si_length, 
                            sp.symbols("L"): self.si_length
                        }
                    elif end_x == 1:
                        magnitude_eq, position_eq = action.equivalent_concentrated_load_of_FBD("x", "L", start_x)
                        subs = {
                            sp.symbols("w_0"): action.si_base_magnitude, 
                            sp.symbols("x"): start_x * self.si_length, 
                            sp.symbols("L"): self.si_length
                        }

                    magnitude_value = float(magnitude_eq.subs(subs))
                    #print(f"subs: {subs}, magnitude_eq: {magnitude_eq}, position_eq: {position_eq}, magnitude_value: {magnitude_value}")
                    if magnitude_value > 0:
                        position_value = float(position_eq.subs(subs)) / self.si_length

                        pos = float(sx + position_value * length)

                        dwg.draw_force(
                            start = (
                                pos, 
                                float(center_y - height / 2 - maximum_force_length * magnitude_value / abs(magnitude_value)),
                            ),
                            end = (pos, float(center_y - height / 2 - 2)),
                        )
                        #テキスト
                        dwg.draw_equation(f'{sp.nsimplify(magnitude_eq)}', position=(float(pos + 15), float(center_y - height / 2 - maximum_force_length * magnitude_value / abs(magnitude_value) - 8)), fontsize=7)

                        #分布荷重のみ寸法
                        if position_value != 0 and position_value != 1:

                            dwg.add(dwg.line((float(pos), float(center_y-height/2)), (float(pos), float(center_y - height * (2 + support_dimension_height_ratio*1))),
                                stroke="black", stroke_width=0.75, stroke_linecap="round"))
                            dwg.add(dwg.line((float(sx), float(center_y-height/2)), (float(sx), float(center_y - height * (2 + support_dimension_height_ratio*1))),
                                stroke="black", stroke_width=0.75, stroke_linecap="round"))
                            dwg.draw_arrow((float(sx), float(center_y - height * (1.5 + support_dimension_height_ratio*1))), (float(pos), float(center_y - height * (1.5 + support_dimension_height_ratio*1))), arrow_type="both")

                            dwg.draw_equation(f'{str(position_eq)}', position=(float((sx + pos) / 2), float(center_y - height * (2.6 + support_dimension_height_ratio*1))), fontsize=7)

        return dwg

    def generate_shear_force_diagram(self, number_of_points=20):

        """
        数式がかぶる問題
        作用の大きさを雑に１にしたせいで，最大値の計算が正しく行われない問題
        """

        dwg = Figure()  # ここを動的にしたい

        #figureの外枠
        #dwg.add(dwg.rect(insert=(0, 0), size=(dwg.width, dwg.height), fill='none', stroke='green', stroke_width=1))

        center_x = dwg.width / 2
        center_y = dwg.height / 2

        maximum_y = dwg.height / 2 * 0.6

        height = dwg.height * 0.8  # 図の高さ（固定）
        width = dwg.width * 0.8   # 図の長さ（80%）

        dict = {sp.symbols("L"): 1}
        cln = 1; cmn = 0

        #作用の大きさ一覧を取得
        magnitudes = []
        for action in self.actions:
            if isinstance(action, Action.DistributedLoad):
                magnitudes.append(action.si_base_magnitude * self.si_length)
            if isinstance(action, Action.ConcentratedLoad):
                magnitudes.append(action.si_magnitude)
            if isinstance(action, Action.ConcentratedMoment):
                magnitudes.append(action.si_magnitude / self.si_length)

        max_magnitude = max([mag for mag in magnitudes])
        min_magnitude = min([mag for mag in magnitudes])
        range_magnitude = max_magnitude - min_magnitude if max_magnitude != min_magnitude else 1

        #代入用辞書を作成
        for action in self.actions:
            if isinstance(action, Action.ConcentratedLoad):
                magnitude = action.si_magnitude / range_magnitude
                dict[sp.symbols(f"P_{cln}" if len([a for a in self.actions if isinstance(a, Action.ConcentratedLoad)]) > 1 else "P")] = magnitude
                cln += 1
            if isinstance(action, Action.DistributedLoad):
                magnitude = action.si_base_magnitude * self.si_length / range_magnitude
                dict[sp.symbols("w_0")] = magnitude
            if isinstance(action, Action.ConcentratedMoment):
                magnitude = action.si_magnitude / self.si_length / range_magnitude
                dict[sp.symbols(f"M_{cmn}")] = magnitude
                cmn += 1

        max_shear_force = max([
            abs(sp.maximum(eq.subs(dict), sp.symbols("x"), sp.Interval(s,e))) for (s,e), eq in self.shear_force] + [
            abs(sp.minimum(eq.subs(dict), sp.symbols("x"), sp.Interval(s,e))) for (s,e), eq in self.shear_force
        ])
        if max_shear_force == 0:
            max_shear_force = 1
        #print(f"max_shear_force: {max_shear_force}")

        #左上隅に"SFD"を追加
        dwg.add(dwg.text("SFD", insert=(0, 10), font_size=8, fill="black"))

        #中心に水平線を引く
        dwg.add(dwg.line((float(center_x - width / 2), float(center_y)), (float(center_x + width / 2), float(center_y)),
            stroke="black", stroke_width=0.75, stroke_linecap="round"))
        #左右に基準の縦線を引く
        dwg.add(dwg.line((float(center_x - width / 2), float(center_y - height / 2)), (float(center_x - width / 2), float(center_y + height / 2)),
            stroke="black", stroke_width=0.75, stroke_linecap="round"))
        dwg.add(dwg.line((float(center_x + width / 2), float(center_y - height / 2)), (float(center_x + width / 2), float(center_y + height / 2)),
            stroke="black", stroke_width=0.75, stroke_linecap="round"))

        #せん断力線図を描画する。
        prev_x = None; prev_y = None
        for (s,e), eq in self.shear_force:
            max_y = -1; min_y = 1; max_x = 0; min_x = 0
            for i in range(0, number_of_points + 1):
                x = (e - s) * (i / number_of_points) + s
                y = eq.subs(dict).subs({sp.symbols("x"): x})
                max_y = max(max_y, y)
                if y == max_y:
                    max_x = x
                min_y = min(min_y, y)
                if y == min_y:
                    min_x = x

                x_coord = float(center_x - width / 2 + x * width)
                y_coord = float(center_y - y * maximum_y / max_shear_force)

                if prev_x is not None and prev_y is not None and i == 0:
                    # 区間の始点に点線を引く
                    x_start = float(center_x - width / 2 + s * width)
                    dwg.add(dwg.line((float(x_start), float(center_y)), (float(x_start), float(prev_y)),
                        stroke="black", stroke_width=0.75, stroke_linecap="round", stroke_dasharray="3,3"))

                if prev_x is not None and prev_y is not None:
                    dwg.add(dwg.line((float(prev_x), float(prev_y)), (float(x_coord), float(y_coord)),
                        stroke="black", stroke_width=1.5, stroke_linecap="round"))
                    
                prev_x = x_coord
                prev_y = y_coord

        #曲げモーメント線図と同様に，特徴点を取得する
        feature_points = []; ses = []
        for (s,e), eq in self.shear_force:
            #始点と終点は無条件に追加
            ses.append(s); ses.append(e)
            sy = eq.subs(dict).subs({sp.symbols("x"): s})
            ey = eq.subs(dict).subs({sp.symbols("x"): e})
            feature_points.append((s, sy, eq.subs({sp.symbols("x"): s * sp.symbols("L")})))
            feature_points.append((e, ey, eq.subs({sp.symbols("x"): e * sp.symbols("L")})))

            #最大値・最小値の点を追加
            if sp.symbols("x") in eq.free_symbols:
                #最大値を求める
                expr_numerical = eq.subs(dict)
                # 数値誤差対策としてnsimplifyを適用
                expr_exact = sp.nsimplify(expr_numerical, tolerance=1e-10)
                interval_exact = sp.Interval(sp.nsimplify(s, tolerance=1e-10), sp.nsimplify(e, tolerance=1e-10))

                max_y = sp.maximum(expr_exact, sp.symbols("x"), interval_exact)
                min_y = sp.minimum(expr_exact, sp.symbols("x"), interval_exact)
                if max_y != min_y:  
                    try:
                        max_x = sp.solveset(sp.Eq(expr_exact, max_y), sp.symbols("x"), domain=sp.S.Reals)
                    except Exception:
                        max_x = []
                    
                    try:
                        min_x = sp.solveset(sp.Eq(expr_exact, min_y), sp.symbols("x"), domain=sp.S.Reals)
                    except Exception:
                        min_x = []
                    
                    for mx in max_x:
                        if mx >= s and mx <= e:
                            feature_points.append((mx, max_y, eq.subs({sp.symbols("x"): mx * sp.symbols("L")})))
                    for mx in min_x:
                        if mx >= s and mx <= e:
                            feature_points.append((mx, min_y, eq.subs({sp.symbols("x"): mx * sp.symbols("L")})))

        #完全に重複する点を削除
        unique_feature_points = []

        for point in feature_points:
            if not any([math.isclose(point[1], p[1], rel_tol=1e-5) for p in unique_feature_points]):
                unique_feature_points.append(point)

        #yによってソート
        unique_feature_points.sort(key=lambda x: x[1])

        #print(f"unique_feature_points (shear): {unique_feature_points}")
        #print(f"feature_points (shear): {feature_points}")

        #対応する高さと式を取得して，数式ラベルの配置と該当xまでの点線を引く
        
        for i, (fx, fy, feq) in enumerate(unique_feature_points):
            #print(f"fx: {fx}")
                                        
            x_coord = float(center_x - width / 2 + fx * width)
            y_coord = float(center_y - fy * maximum_y / max_shear_force)

            #数式ラベルの配置
            if i % 2 == 0:
                dwg.draw_equation(f'{sp.nsimplify(sp.simplify(feq.subs({sp.symbols("x"): fx*sp.symbols("L")})),tolerance=1e-5)}', position=(float(dwg.width), float(y_coord)), fontsize=7, fill ="white")
                #該当xまでの点線を引く
                dwg.add(dwg.line((float(center_x + width / 2), float(y_coord)), (float(x_coord), float(y_coord)),
                    stroke="black", stroke_width=0.75, stroke_linecap="round", stroke_dasharray="3,3"))
        
            else:
                dwg.draw_equation(f'{sp.nsimplify(sp.simplify(feq.subs({sp.symbols("x"): fx*sp.symbols("L")})),tolerance=1e-5)}', position=(0.0, float(y_coord)), fontsize=7, fill ="white")
                #該当xまでの点線を引く
                dwg.add(dwg.line((float(dwg.width*0.1), float(y_coord)), (float(x_coord), float(y_coord)),
                    stroke="black", stroke_width=0.75, stroke_linecap="round", stroke_dasharray="3,3"))

            # fxが寸法に絡まない場合，点線を縦に引き，xのラベルを追加
            if fx not in ses:
                dwg.add(dwg.line((float(x), float(center_y - height / 2)), (float(x), float(center_y + height / 2)),
                    stroke="black", stroke_width=0.75, stroke_linecap="round", stroke_dasharray="3,3"))
                dwg.draw_equation(f'x={sp.nsimplify(fx*sp.symbols("L"))}', position=(float(x), float(center_y + height / 2 + 5)), fontsize=7, fill ="black")
            
        self._shear_force_diagram = dwg

    def generate_bending_moment_diagram(self, number_of_points=20):

        """
        数式がかぶる問題
        →　左右に交互に出す？

        作用の大きさを雑に１にしたせいで，最大値の計算が正しく行われない問題
        →　しっかり値をもとめたうえで，最大値を計算するように修正したい
        """

        dwg = Figure()  # ここを動的にしたい

        #figureの外枠
        #dwg.add(dwg.rect(insert=(0, 0), size=(dwg.width, dwg.height), fill='none', stroke='green', stroke_width=1))

        center_x = dwg.width / 2
        center_y = dwg.height / 2

        maximum_y = dwg.height / 2 * 0.6

        #左上隅に"BMD"を追加
        dwg.add(dwg.text("BMD", insert=(0, 10), font_size=8, fill="black"))

        height = dwg.height * 0.8  # 図の高さ（固定）
        width = dwg.width * 0.8   # 図の長さ（80%）
        dict = {sp.symbols("L"): 1}

        #各作用によるモーメントの大きさを取得
        magnitudes = []
        for action in self.actions:
            if isinstance(action, Action.ConcentratedLoad):
                magnitudes.append(action.si_magnitude * self.si_length)
            if isinstance(action, Action.DistributedLoad):
                magnitudes.append(action.si_magnitude * self.si_length * self.si_length)
            if isinstance(action, Action.ConcentratedMoment):
                magnitudes.append(action.si_magnitude)

        maximum_magnitude = max([mag for mag in magnitudes])
        minimum_magnitude = min([mag for mag in magnitudes])
        range_magnitude = maximum_magnitude - minimum_magnitude if maximum_magnitude - minimum_magnitude != 0 else 1

        cln = 1; cmn = 0
        for action in self.actions:
            if isinstance(action, Action.ConcentratedLoad):
                magnitude = action.si_magnitude * self.si_length / range_magnitude
                dict[sp.symbols(f"P_{cln}" if len([a for a in self.actions if isinstance(a, Action.ConcentratedLoad)]) > 1 else "P")] = magnitude
                cln += 1
                
            if isinstance(action, Action.DistributedLoad):
                magnitude = action.si_magnitude / range_magnitude
                dict[sp.symbols("w_0")] = magnitude

            if isinstance(action, Action.ConcentratedMoment):
                magnitude = action.si_magnitude / range_magnitude
                dict[sp.symbols(f"M_{cmn}")] = magnitude
                cmn += 1

            #print(magnitude, action.si_magnitude, action)

        max_bending_moment = max([
            abs(sp.maximum(eq.subs(dict), sp.symbols("x"), sp.Interval(s,e))) for (s,e), eq in self.bending_moment] + [
            abs(sp.minimum(eq.subs(dict), sp.symbols("x"), sp.Interval(s,e))) for (s,e), eq in self.bending_moment
        ])
        
        if max_bending_moment == 0:
            max_bending_moment = 1

        #print(f"max_bending_moment: {max_bending_moment}")
        #print(f"raw_list: {[abs(sp.maximum(eq.subs(dict), sp.symbols('x'), sp.Interval(s,e))) for (s,e), eq in self.bending_moment]}")

        #中心に水平線を引く
        dwg.add(dwg.line((float(center_x - width / 2), float(center_y)), (float(center_x + width / 2), float(center_y)),
            stroke="black", stroke_width=0.75, stroke_linecap="round"))
        #左右に基準の縦線を引く
        dwg.add(dwg.line((float(center_x - width / 2), float(center_y - height / 2)), (float(center_x - width / 2), float(center_y + height / 2)),
            stroke="black", stroke_width=0.75, stroke_linecap="round"))
        dwg.add(dwg.line((float(center_x + width / 2), float(center_y - height / 2)), (float(center_x + width / 2), float(center_y + height / 2)),
            stroke="black", stroke_width=0.75, stroke_linecap="round"))
        
        #曲げモーメント線図を描画する。
        prev_x = None; prev_y = None
        ses = []
        for (s,e), eq in self.bending_moment:
            #print(f"曲げモーメント区間: {s} to {e}, eq: {eq}")
            ses.append(s); ses.append(e)
            max_y = -1; min_y = 1; max_x = 0; min_x = 0
            for i in range(0, number_of_points + 1):
                
                x = (e - s) * (i / number_of_points) + s
                y = eq.subs(dict).subs({sp.symbols("x"): x})

                x_coord = float(center_x - width / 2 + x * width)
                y_coord = float(center_y - y * maximum_y / max_bending_moment)

                if prev_x is not None and prev_y is not None and i == 0:
                    # 区間の始点に点線を引く
                    x_start = float(center_x - width / 2 + s * width)
                    dwg.add(dwg.line((float(x_start), float(center_y)), (float(x_start), float(prev_y)),
                        stroke="black", stroke_width=0.75, stroke_linecap="round", stroke_dasharray="3,3"))

                if prev_x is not None and prev_y is not None:
                    dwg.add(dwg.line((float(prev_x), float(prev_y)), (float(x_coord), float(y_coord)),
                        stroke="black", stroke_width=1.5, stroke_linecap="round"))
                    
                prev_x = x_coord
                prev_y = y_coord


        #特徴点の座標と数式を収集
        feature_points = []

        #最大値の点を取得
        eq, value, x = self.maximum_bending_moment
        feature_points.append((x, value/ abs(value) * max_bending_moment, eq))
        #print(feature_points)

        for (s,e), eq in self.bending_moment:

            #始点と終点は無条件に追加
            sy = eq.subs(dict).subs({sp.symbols("x"): s})
            ey = eq.subs(dict).subs({sp.symbols("x"): e})
            feature_points.append((s, sy, eq.subs({sp.symbols("x"): s * sp.symbols("L")})))
            feature_points.append((e, ey, eq.subs({sp.symbols("x"): e * sp.symbols("L")})))

            #最大値・最小値の点を追加
            if sp.symbols("x") in eq.free_symbols:
                #最大値を求める
                expr_numerical = eq.subs(dict)
                # 数値誤差対策としてnsimplifyを適用
                expr_exact = sp.nsimplify(expr_numerical, tolerance=1e-10)
                interval_exact = sp.Interval(sp.nsimplify(s, tolerance=1e-10), sp.nsimplify(e, tolerance=1e-10))

                max_y = sp.maximum(expr_exact, sp.symbols("x"), interval_exact)
                min_y = sp.minimum(expr_exact, sp.symbols("x"), interval_exact)
                if max_y != min_y:  
                    try:
                        max_x = sp.solveset(sp.Eq(expr_exact, max_y), sp.symbols("x"), domain=sp.S.Reals)
                    except Exception:
                        max_x = []
                    
                    try:
                        min_x = sp.solveset(sp.Eq(expr_exact, min_y), sp.symbols("x"), domain=sp.S.Reals)
                    except Exception:
                        min_x = []
                    
                    for mx in max_x:
                        if mx >= s and mx <= e:
                            feature_points.append((mx, max_y, eq.subs({sp.symbols("x"): mx * sp.symbols("L")})))
                    for mx in min_x:
                        if mx >= s and mx <= e:
                            feature_points.append((mx, min_y, eq.subs({sp.symbols("x"): mx * sp.symbols("L")})))

        #完全に重複する点を削除
        unique_feature_points = []

        for point in feature_points:
            if not any([math.isclose(point[1], p[1], rel_tol=1e-5) for p in unique_feature_points]):
                unique_feature_points.append(point)

        #yによってソート
        unique_feature_points.sort(key=lambda x: x[1])

        #print(f"unique_feature_points (bending): {unique_feature_points}")

        #対応する高さと式を取得して，数式ラベルの配置と該当xまでの点線を引く
        for i, (fx, fy, feq) in enumerate(unique_feature_points):
            #print(f"fx: {fx}")
                                        
            x = center_x - width / 2 + fx * width
            y = center_y - fy * maximum_y / max_bending_moment
            x = float(x); y = float(y)

            #数式ラベルの配置
            if i % 2 == 0:
                dwg.draw_equation(f'{sp.nsimplify(sp.simplify(feq.subs({sp.symbols("x"): fx*sp.symbols("L")})),tolerance=1e-5)}', position=(float(dwg.width), float(y)), fontsize=7, fill ="white")
                #該当xまでの点線を引く
                dwg.add(dwg.line((float(center_x + width / 2), float(y)), (float(x), float(y)),
                    stroke="black", stroke_width=0.75, stroke_linecap="round", stroke_dasharray="3,3"))
        
            else:
                dwg.draw_equation(f'{sp.nsimplify(sp.simplify(feq.subs({sp.symbols("x"): fx*sp.symbols("L")})),tolerance=1e-5)}', position=(0.0, float(y)), fontsize=7, fill ="white")
                #該当xまでの点線を引く
                dwg.add(dwg.line((float(dwg.width*0.1), float(y)), (float(x), float(y)),
                    stroke="black", stroke_width=0.75, stroke_linecap="round", stroke_dasharray="3,3"))

            # fxが寸法に絡まない場合，点線を縦に引き，xのラベルを追加
            if fx not in ses:
                dwg.add(dwg.line((float(x), float(y)), (float(x), float(center_y + height / 2)),
                    stroke="black", stroke_width=0.75, stroke_linecap="round", stroke_dasharray="3,3"))
                dwg.draw_equation(f'{sp.nsimplify(fx*sp.symbols("L"))}', position=(float(x), float(center_y + height / 2 + 5)), fontsize=7, fill ="white")
            
        self._bending_moment_diagram = dwg

    def generate_top_stress_diagram(self, number_of_points=20):
        dwg = Figure()  # ここを動的にしたい

        #figureの外枠
        #dwg.add(dwg.rect(insert=(0, 0), size=(dwg.width, dwg.height), fill='none', stroke='green', stroke_width=1))

        center_x = dwg.width / 2
        center_y = dwg.height / 2

        maximum_y = dwg.height / 2 * 0.6

        #左上隅に"TSD"を追加
        dwg.add(dwg.text("Top Stress", insert=(0, 10), font_size=8, fill="black"))

        height = dwg.height * 0.8  # 図の高さ（固定）
        width = dwg.width * 0.8   # 図の長さ（80%）

        dict = {
            sp.symbols("L"): 1,
            sp.symbols("B"): 1,
            sp.symbols("H"): 1,
            sp.symbols("t"): 1,
            sp.symbols("I_z"): 1,
            sp.symbols("y_g"): 0.5,
        }

        concentrated_loads_number = 0; concentrated_moments_number = 0
        for action in self.actions:

            if isinstance(action, Action.DistributedLoad):
                dict["w_0"] = action.si_base_magnitude / 1e3

            if isinstance(action, Action.ConcentratedLoad):
                total_concentrated_loads_number = len([a for a in self.actions if isinstance(a, Action.ConcentratedLoad)])
                if isinstance(action, Action.ConcentratedLoad):
                    concentrated_loads_number += 1
                    if total_concentrated_loads_number > 1:
                        symbol = sp.symbols(f"P_{concentrated_loads_number}")
                    else:
                        symbol = sp.symbols(f"P")
                    dict[symbol] = action.si_magnitude

            if isinstance(action, Action.ConcentratedMoment):
                if isinstance(action, Action.ConcentratedMoment):
                    symbol = sp.symbols(f"M_{concentrated_moments_number}")
                    concentrated_moments_number += 1
                    dict[symbol] = action.si_magnitude * 1e3



        # Beam.py 1613行目付近
        for (s, e), eq in self.top_stress:
            #subbed_eq = eq.subs(dict); print(f"DEBUG: range({s}, {e}), subbed_eq = {subbed_eq}")
            pass

        #print(f"top_stress: {self.top_stress}")
        max_top_stress = max([
            abs(sp.maximum(eq.subs(dict), sp.symbols("x"), sp.Interval(s,e))) for (s,e), eq in self.top_stress] + [
            abs(sp.minimum(eq.subs(dict), sp.symbols("x"), sp.Interval(s,e))) for (s,e), eq in self.top_stress
        ])
        if max_top_stress == 0:
            max_top_stress = 1

        #中心に水平線を引く
        dwg.add(dwg.line((float(center_x - width / 2), float(center_y)), (float(center_x + width / 2), float(center_y)),
            stroke="black", stroke_width=0.75, stroke_linecap="round"))
        #左右に基準の縦線を引く
        dwg.add(dwg.line((float(center_x - width / 2), float(center_y - height / 2)), (float(center_x - width / 2), float(center_y + height / 2)),
            stroke="black", stroke_width=0.75, stroke_linecap="round"))
        dwg.add(dwg.line((float(center_x + width / 2), float(center_y - height / 2)), (float(center_x + width / 2), float(center_y + height / 2)),
            stroke="black", stroke_width=0.75, stroke_linecap="round"))

        #上端応力線図を描画する。
        prev_x = None; prev_y = None
        for (s,e), eq in self.top_stress:
            for i in range(0, number_of_points + 1):
                x = (e - s) * (i / number_of_points) + s
                y = eq.subs(dict).subs({sp.symbols("x"): x})

                x_coord = float(center_x - width / 2 + x * width)
                y_coord = float(center_y - y * maximum_y / max_top_stress)

                if prev_x is not None and prev_y is not None and i == 0:
                    # 区間の始点に点線を引く
                    x_start = float(center_x - width / 2 + s * width)
                    dwg.add(dwg.line((float(x_start), float(center_y)), (float(x_start), float(prev_y)),
                        stroke="black", stroke_width=0.75, stroke_linecap="round", stroke_dasharray="3,3"))

                if prev_x is not None and prev_y is not None:
                    dwg.add(dwg.line((float(prev_x), float(prev_y)), (float(x_coord), float(y_coord)),
                        stroke="black", stroke_width=1.5, stroke_linecap="round"))
                    
                prev_x = x_coord
                prev_y = y_coord

        #特徴点の座標と数式を収集
        feature_points = []; ses = []
        for (s,e), eq in self.top_stress:
            #始点と終点は無条件に追加
            ses.append(s); ses.append(e)
            sy = eq.subs(dict).subs({sp.symbols("x"): s})
            ey = eq.subs(dict).subs({sp.symbols("x"): e})
            feature_points.append((s, sy, eq.subs({sp.symbols("x"): s * sp.symbols("L")})))
            feature_points.append((e, ey, eq.subs({sp.symbols("x"): e * sp.symbols("L")})))

            #最大値・最小値の点を追加
            if sp.symbols("x") in eq.free_symbols:
                #最大値を求める
                expr_numerical = eq.subs(dict)
                # 数値誤差対策としてnsimplifyを適用
                expr_exact = sp.nsimplify(expr_numerical, tolerance=1e-10)
                interval_exact = sp.Interval(sp.nsimplify(s, tolerance=1e-10), sp.nsimplify(e, tolerance=1e-10))

                max_y = sp.maximum(expr_exact, sp.symbols("x"), interval_exact)
                min_y = sp.minimum(expr_exact, sp.symbols("x"), interval_exact)
                if max_y != min_y:  
                    try:
                        max_x = sp.solveset(sp.Eq(expr_exact, max_y), sp.symbols("x"), domain=sp.S.Reals)
                    except Exception:
                        max_x = []
                    
                    try:
                        min_x = sp.solveset(sp.Eq(expr_exact, min_y), sp.symbols("x"), domain=sp.S.Reals)
                    except Exception:
                        min_x = []
                    
                    for mx in max_x:
                        if mx >= s and mx <= e:
                            feature_points.append((mx, max_y, eq.subs({sp.symbols("x"): mx * sp.symbols("L")})))
                    for mx in min_x:
                        if mx >= s and mx <= e:
                            feature_points.append((mx, min_y, eq.subs({sp.symbols("x"): mx * sp.symbols("L")})))
        #完全に重複する点を削除
        unique_feature_points = []
        for point in feature_points:
            if not any([math.isclose(point[1], p[1], rel_tol=1e-5) for p in unique_feature_points]):
                unique_feature_points.append(point)
        #yによってソート
        unique_feature_points.sort(key=lambda x: x[1])

        for i, (fx, fy, feq) in enumerate(unique_feature_points):
            #print(f"fx: {fx}")
                                        
            x = center_x - width / 2 + fx * width
            y = center_y - fy * maximum_y / max_top_stress
            x = float(x); y = float(y)

            #数式ラベルの配置
            if i % 2 == 0:
                dwg.draw_equation(f'{sp.nsimplify(sp.simplify(feq.subs({sp.symbols("x"): fx*sp.symbols("L")})),tolerance=1e-5)}', position=(float(dwg.width), float(y)), fontsize=7, fill ="white")
                #該当xまでの点線を引く
                dwg.add(dwg.line((float(center_x + width / 2), float(y)), (float(x), float(y)),
                    stroke="black", stroke_width=0.75, stroke_linecap="round", stroke_dasharray="3,3"))
        
            else:
                dwg.draw_equation(f'{sp.nsimplify(sp.simplify(feq.subs({sp.symbols("x"): fx*sp.symbols("L")})),tolerance=1e-5)}', position=(0.0, float(y)), fontsize=7, fill ="white")
                #該当xまでの点線を引く
                dwg.add(dwg.line((float(dwg.width*0.1), float(y)), (float(x), float(y)),
                    stroke="black", stroke_width=0.75, stroke_linecap="round", stroke_dasharray="3,3"))

            # fxが寸法に絡まない場合，点線を縦に引き，xのラベルを追加
            if fx not in ses:
                dwg.add(dwg.line((float(x), float(center_y - height / 2)), (float(x), float(center_y + height / 2)),
                    stroke="black", stroke_width=0.75, stroke_linecap="round", stroke_dasharray="3,3"))
                dwg.draw_equation(f'x={sp.nsimplify(fx*sp.symbols("L"))}', position=(float(x), float(center_y + height / 2 + 5)), fontsize=7, fill ="black")

        self._top_stress_diagram = dwg

    def generate_bottom_stress_diagram(self, number_of_points=20):
        dwg = Figure()  # ここを動的にしたい

        #figureの外枠
        #dwg.add(dwg.rect(insert=(0, 0), size=(dwg.width, dwg.height), fill='none', stroke='green', stroke_width=1))

        center_x = dwg.width / 2
        center_y = dwg.height / 2

        maximum_y = dwg.height / 2 * 0.6

        #左上隅に"BSD"を追加
        dwg.add(dwg.text("Bottom Stress", insert=(0, 10), font_size=8, fill="black"))

        height = dwg.height * 0.8  # 図の高さ（固定）
        width = dwg.width * 0.8   # 図の長さ（80%）

        dict = {
            sp.symbols("L"): 1,
            sp.symbols("B"): 1,
            sp.symbols("H"): 1,
            sp.symbols("t"): 1,
            sp.symbols("I_z"): 1,
            sp.symbols("y_g"): 0.5,
        }

        concentrated_loads_number = 0; concentrated_moments_number = 0
        for action in self.actions:

            if isinstance(action, Action.DistributedLoad):
                dict["w_0"] = action.si_base_magnitude / 1e3

            if isinstance(action, Action.ConcentratedLoad):
                total_concentrated_loads_number = len([a for a in self.actions if isinstance(a, Action.ConcentratedLoad)])
                if isinstance(action, Action.ConcentratedLoad):
                    concentrated_loads_number += 1
                    if total_concentrated_loads_number > 1:
                        symbol = sp.symbols(f"P_{concentrated_loads_number}")
                    else:
                        symbol = sp.symbols(f"P")
                    dict[symbol] = action.si_magnitude

            if isinstance(action, Action.ConcentratedMoment):
                if isinstance(action, Action.ConcentratedMoment):
                    symbol = sp.symbols(f"M_{concentrated_moments_number}")
                    concentrated_moments_number += 1
                    dict[symbol] = action.si_magnitude * 1e3


        max_bottom_stress = max([
            abs(sp.maximum(eq.subs(dict), sp.symbols("x"), sp.Interval(s,e))) for (s,e), eq in self.bottom_stress] + [
            abs(sp.minimum(eq.subs(dict), sp.symbols("x"), sp.Interval(s,e))) for (s,e), eq in self.bottom_stress
        ])
        if max_bottom_stress == 0:
            max_bottom_stress = 1

        #中心に水平線を引く
        dwg.add(dwg.line((float(center_x - width / 2), float(center_y)), (float(center_x + width / 2), float(center_y)),
            stroke="black", stroke_width=0.75, stroke_linecap="round"))
        #左右に基準の縦線を引く
        dwg.add(dwg.line((float(center_x - width / 2), float(center_y - height / 2)), (float(center_x - width / 2), float(center_y + height / 2)),
            stroke="black", stroke_width=0.75, stroke_linecap="round"))
        dwg.add(dwg.line((float(center_x + width / 2), float(center_y - height / 2)), (float(center_x + width / 2), float(center_y + height / 2)),
            stroke="black", stroke_width=0.75, stroke_linecap="round"))

        #下端応力線図を描画する。
        prev_x = None; prev_y = None
        for (s,e), eq in self.bottom_stress:
            for i in range(0, number_of_points + 1):
                x = (e - s) * (i / number_of_points) + s
                y = eq.subs(dict).subs({sp.symbols("x"): x})
                x_coord = float(center_x - width / 2 + x * width)
                y_coord = float(center_y - y * maximum_y / max_bottom_stress)

                if prev_x is not None and prev_y is not None and i == 0:
                    # 区間の始点に点線を引く
                    x_start = float(center_x - width / 2 + s * width)
                    dwg.add(dwg.line((float(x_start), float(center_y)), (float(x_start), float(prev_y)),
                        stroke="black", stroke_width=0.75, stroke_linecap="round", stroke_dasharray="3,3"))

                if prev_x is not None and prev_y is not None:
                    dwg.add(dwg.line((float(prev_x), float(prev_y)), (float(x_coord), float(y_coord)),
                        stroke="black", stroke_width=1.5, stroke_linecap="round"))
                
                prev_x = x_coord
                prev_y = y_coord

        #特徴点の座標と数式を収集
        feature_points = []; ses = []
        for (s,e), eq in self.bottom_stress:
            #始点と終点は無条件に追加
            ses.append(s); ses.append(e)
            sy = eq.subs(dict).subs({sp.symbols("x"): s})
            ey = eq.subs(dict).subs({sp.symbols("x"): e})
            feature_points.append((s, sy, eq.subs({sp.symbols("x"): s * sp.symbols("L")})))
            feature_points.append((e, ey, eq.subs({sp.symbols("x"): e * sp.symbols("L")})))

            #最大値・最小値の点を追加
            if sp.symbols("x") in eq.free_symbols:
                #最大値を求める
                expr_numerical = eq.subs(dict)
                # 数値誤差対策としてnsimplifyを適用
                expr_exact = sp.nsimplify(expr_numerical, tolerance=1e-10)
                interval_exact = sp.Interval(sp.nsimplify(s, tolerance=1e-10), sp.nsimplify(e, tolerance=1e-10))

                max_y = sp.maximum(expr_exact, sp.symbols("x"), interval_exact)
                min_y = sp.minimum(expr_exact, sp.symbols("x"), interval_exact)
                if max_y != min_y:  
                    try:
                        max_x = sp.solveset(sp.Eq(expr_exact, max_y), sp.symbols("x"), domain=sp.S.Reals)
                    except Exception:
                        max_x = []
                    
                    try:
                        min_x = sp.solveset(sp.Eq(expr_exact, min_y), sp.symbols("x"), domain=sp.S.Reals)
                    except Exception:
                        min_x = []
                    
                    for mx in max_x:
                        if mx >= s and mx <= e:
                            feature_points.append((mx, max_y, eq.subs({sp.symbols("x"): mx * sp.symbols("L")})))
                    for mx in min_x:
                        if mx >= s and mx <= e:
                            feature_points.append((mx, min_y, eq.subs({sp.symbols("x"): mx * sp.symbols("L")})))
        #完全に重複する点を削除
        unique_feature_points = []
        for point in feature_points:
            if not any([math.isclose(point[1], p[1], rel_tol=1e-5) for p in unique_feature_points]):
                unique_feature_points.append(point)
        #yによってソート
        unique_feature_points.sort(key=lambda x: x[1])

        for i, (fx, fy, feq) in enumerate(unique_feature_points):
            #print(f"fx: {fx}")
                                        
            x = center_x - width / 2 + fx * width
            y = center_y - fy * maximum_y / max_bottom_stress
            x = float(x); y = float(y)

            #数式ラベルの配置
            if i % 2 == 0:
                dwg.draw_equation(f'{sp.nsimplify(sp.simplify(feq.subs({sp.symbols("x"): fx*sp.symbols("L")})),tolerance=1e-5)}', position=(float(dwg.width), float(y)), fontsize=7, fill ="white")
                #該当xまでの点線を引く
                dwg.add(dwg.line((float(center_x + width / 2), float(y)), (float(x), float(y)),
                    stroke="black", stroke_width=0.75, stroke_linecap="round", stroke_dasharray="3,3"))
        
            else:
                dwg.draw_equation(f'{sp.nsimplify(sp.simplify(feq.subs({sp.symbols("x"): fx*sp.symbols("L")})),tolerance=1e-5)}', position=(0.0, float(y)), fontsize=7, fill ="white")
                #該当xまでの点線を引く
                dwg.add(dwg.line((float(dwg.width*0.1), float(y)), (float(x), float(y)),
                    stroke="black", stroke_width=0.75, stroke_linecap="round", stroke_dasharray="3,3"))

            # fxが寸法に絡まない場合，点線を縦に引き，xのラベルを追加
            if fx not in ses:
                dwg.add(dwg.line((float(x), float(center_y - height / 2)), (float(x), float(center_y + height / 2)),
                    stroke="black", stroke_width=0.75, stroke_linecap="round", stroke_dasharray="3,3"))
                dwg.draw_equation(f'x={sp.nsimplify(fx*sp.symbols("L"))}', position=(float(x), float(center_y + height / 2 + 5)), fontsize=7, fill ="black")
        
        self._bottom_stress_diagram = dwg

    def generate_slope_diagram(self, number_of_points=20):
        """
        たわみ角線図を生成する。
        """
        dwg = Figure()
        center_x = dwg.width / 2
        center_y = dwg.height / 2
        maximum_y = dwg.height / 2 * 0.6
        height = dwg.height * 0.8
        width = dwg.width * 0.8

        dwg.add(dwg.text("Slope Curve: i(x)", insert=(0, 10), font_size=8, fill="black"))

        # 代入用辞書の作成
        dict_vals = {
            sp.symbols("L"): 1,
            sp.symbols("E"): 1,
            sp.symbols("I_z"): 1,
            sp.symbols("B"): 1,
            sp.symbols("H"): 1,
            sp.symbols("y_g"): 1,
            sp.symbols("D"): 1,
            sp.symbols("pi"): math.pi,
        }

        cln = 1; cmn = 0
        magnitudes = []
        for action in self.actions:
            if isinstance(action, Action.ConcentratedLoad): magnitudes.append(abs(action.si_magnitude) * self.si_length)
            if isinstance(action, Action.DistributedLoad): magnitudes.append(abs(action.si_magnitude) * self.si_length**2)
            if isinstance(action, Action.ConcentratedMoment): magnitudes.append(abs(action.si_magnitude))

        range_mag = max(magnitudes) if magnitudes else 1
        if range_mag == 0: range_mag = 1

        for action in self.actions:
            if isinstance(action, Action.ConcentratedLoad):
                dict_vals[sp.symbols(f"P_{cln}" if len([a for a in self.actions if isinstance(a, Action.ConcentratedLoad)]) > 1 else "P")] = action.si_magnitude * self.si_length / range_mag
                cln += 1
            if isinstance(action, Action.DistributedLoad):
                dict_vals[sp.symbols("w_0")] = action.si_magnitude / range_mag
            if isinstance(action, Action.ConcentratedMoment):
                dict_vals[sp.symbols(f"M_{cmn}")] = action.si_magnitude / range_mag
                cmn += 1

        # 最大値の取得 (数値サンプリングによる堅牢な手法)
        vals = []
        for (s,e), eq in self.slope:
            sub_eq = eq
            for sym in eq.free_symbols:
                if sym.name == "x": continue
                for ds, dv in dict_vals.items():
                    if sym.name == ds.name:
                        sub_eq = sub_eq.subs(sym, dv)
            
            for i in range(number_of_points + 1):
                x_ratio = (e - s) * (i / number_of_points) + s
                try:
                    # xにx_ratioを代入（L=1を想定）
                    res = sub_eq.subs({sp.symbols("x"): x_ratio}).evalf()
                    v = float(res)
                    vals.append(abs(v))
                except:
                    pass
        max_val = max(vals) if vals else 1
        if max_val == 0: max_val = 1

        # 基準線の描画
        dwg.add(dwg.line((float(center_x - width / 2), float(center_y)), (float(center_x + width / 2), float(center_y)), stroke="black", stroke_width=0.75))
        dwg.add(dwg.line((float(center_x - width / 2), float(center_y - height / 2)), (float(center_x - width / 2), float(center_y + height / 2)), stroke="black", stroke_width=0.75))
        dwg.add(dwg.line((float(center_x + width / 2), float(center_y - height / 2)), (float(center_x + width / 2), float(center_y + height / 2)), stroke="black", stroke_width=0.75))

        # 曲線の描画
        prev_x = None; prev_y = None
        for (s,e), eq in self.slope:
            sub_eq = eq
            for sym in eq.free_symbols:
                if sym.name == "x": continue
                for ds, dv in dict_vals.items():
                    if sym.name == ds.name:
                        sub_eq = sub_eq.subs(sym, dv)

            for i in range(number_of_points + 1):
                x_ratio = (e - s) * (i / number_of_points) + s
                y_val = float(sub_eq.subs({sp.symbols("x"): x_ratio}).evalf())
                curr_x = float(center_x - width / 2 + x_ratio * width)
                curr_y = float(center_y - y_val * maximum_y / max_val)
                if prev_x is not None and i != 0:
                    dwg.add(dwg.line((float(prev_x), float(prev_y)), (float(curr_x), float(curr_y)), stroke="black", stroke_width=1.5))
                prev_x, prev_y = curr_x, curr_y

        # 特徴点の抽出とラベル
        feature_points = []
        eq_m, val_m, x_m = self.maximum_slope
        feature_points.append((x_m, (val_m / abs(val_m) * max_val) if val_m != 0 else 0, eq_m))
        for (s,e), eq in self.slope:
            sub_eq_eval = eq
            for sym in eq.free_symbols:
                if sym.name == "x": continue
                for ds, dv in dict_vals.items():
                    if sym.name == ds.name:
                        sub_eq_eval = sub_eq_eval.subs(sym, dv)
            
            feature_points.append((s, float(sub_eq_eval.subs({sp.symbols("x"): s}).evalf()), eq))
            feature_points.append((e, float(sub_eq_eval.subs({sp.symbols("x"): e}).evalf()), eq))

        unique_points = []
        for p in feature_points:
            if not any([math.isclose(float(p[1]), float(up[1]), rel_tol=1e-5) for up in unique_points]):
                unique_points.append(p)

        unique_points.sort(key=lambda x: x[1])

        for i, (fx, fy, feq) in enumerate(unique_points):
            # SymPy式の場合はsubsとevalfを行い、数値の場合は直接変換する
            try:
                if hasattr(fx, 'subs'):
                    fx_res = fx.subs(dict_vals).evalf()
                    fx_val = float(fx_res) if fx_res.is_Number else 0.0
                else:
                    fx_val = float(fx)
                
                if hasattr(fy, 'subs'):
                    fy_res = fy.subs(dict_vals).evalf()
                    fy_val = float(fy_res) if fy_res.is_Number else 0.0
                else:
                    fy_val = float(fy)
            except Exception:
                fx_val = 0.0
                fy_val = 0.0
            
            px = float(center_x - width / 2 + fx_val * width)
            py = float(center_y - fy_val * maximum_y / max_val)
            
            # xにfx*Lを代入してラベル用の定数式を作成
            label_eq = sp.simplify(sp.nsimplify(feq.subs({sp.symbols("x"): fx * sp.symbols("L")})))
            
            if i % 2 == 0:
                dwg.draw_equation(f'{sp.latex(label_eq)}', position=(float(dwg.width), float(py)), fontsize=7, fill="white")
                dwg.add(dwg.line((float(center_x + width / 2), float(py)), (float(px), float(py)),
                    stroke="black", stroke_width=0.75, stroke_linecap="round", stroke_dasharray="3,3"))
            else:
                dwg.draw_equation(f'{sp.latex(label_eq)}', position=(0.0, float(py)), fontsize=7, fill="white")
                dwg.add(dwg.line((float(dwg.width*0.1), float(py)), (float(px), float(py)),
                    stroke="black", stroke_width=0.75, stroke_linecap="round", stroke_dasharray="3,3"))

        self._slope_diagram = dwg

    def generate_deflection_diagram(self, number_of_points=20):
        """
        たわみ曲線（たわみ量線図）を生成する。
        """
        dwg = Figure()
        center_x = dwg.width / 2
        center_y = dwg.height / 2
        maximum_y = dwg.height / 2 * 0.6
        height = dwg.height * 0.8
        width = dwg.width * 0.8

        dwg.add(dwg.text("Deflection Curve: y(x)", insert=(0, 10), font_size=8, fill="black"))

        # 代入用辞書の作成
        dict_vals = {
            sp.symbols("L"): 1,
            sp.symbols("E"): 1,
            sp.symbols("I_z"): 1,
            sp.symbols("B"): 1,
            sp.symbols("H"): 1,
            sp.symbols("y_g"): 1,
            sp.symbols("D"): 1,
            sp.symbols("pi"): math.pi,
        }

        cln = 1; cmn = 0
        magnitudes = []
        for action in self.actions:
            if isinstance(action, Action.ConcentratedLoad): magnitudes.append(action.si_magnitude * self.si_length)
            if isinstance(action, Action.DistributedLoad): magnitudes.append(action.si_magnitude * self.si_length**2)
            if isinstance(action, Action.ConcentratedMoment): magnitudes.append(action.si_magnitude)

        range_mag = max(magnitudes) - min(magnitudes) if magnitudes and max(magnitudes) != min(magnitudes) else 1
        for action in self.actions:
            if isinstance(action, Action.ConcentratedLoad):
                dict_vals[sp.symbols(f"P_{cln}" if len([a for a in self.actions if isinstance(a, Action.ConcentratedLoad)]) > 1 else "P")] = action.si_magnitude * self.si_length / range_mag
                cln += 1
            if isinstance(action, Action.DistributedLoad):
                dict_vals[sp.symbols("w_0")] = action.si_magnitude / range_mag
            if isinstance(action, Action.ConcentratedMoment):
                dict_vals[sp.symbols(f"M_{cmn}")] = action.si_magnitude / range_mag
                cmn += 1

        # 最大値の取得 (数値サンプリングによる堅牢な手法)
        vals = []
        for (s,e), eq in self.deflection:
            sub_eq = eq
            for sym in eq.free_symbols:
                if sym.name == "x": continue
                for ds, dv in dict_vals.items():
                    if sym.name == ds.name:
                        sub_eq = sub_eq.subs(sym, dv)

            for i in range(number_of_points + 1):
                x_ratio = (e - s) * (i / number_of_points) + s
                try:
                    res = sub_eq.subs({sp.symbols("x"): x_ratio}).evalf()
                    v = float(res)
                    vals.append(abs(v))
                except:
                    pass
        max_val = max(vals) if vals else 1
        if max_val == 0: max_val = 1

        dwg.add(dwg.line((float(center_x - width / 2), float(center_y)), (float(center_x + width / 2), float(center_y)), stroke="black", stroke_width=0.75))
        dwg.add(dwg.line((float(center_x - width / 2), float(center_y - height / 2)), (float(center_x - width / 2), float(center_y + height / 2)), stroke="black", stroke_width=0.75))
        dwg.add(dwg.line((float(center_x + width / 2), float(center_y - height / 2)), (float(center_x + width / 2), float(center_y + height / 2)), stroke="black", stroke_width=0.75))

        # 曲線の描画
        prev_x = None; prev_y = None
        for (s,e), eq in self.deflection:
            sub_eq = eq
            for sym in eq.free_symbols:
                if sym.name == "x": continue
                for ds, dv in dict_vals.items():
                    if sym.name == ds.name:
                        sub_eq = sub_eq.subs(sym, dv)

            for i in range(number_of_points + 1):
                x_ratio = (e - s) * (i / number_of_points) + s
                y_val = -float(sub_eq.subs({sp.symbols("x"): x_ratio}).evalf())
                curr_x = float(center_x - width / 2 + x_ratio * width)
                curr_y = float(center_y - y_val * maximum_y / max_val)
                if prev_x is not None and i != 0:
                    dwg.add(dwg.line((float(prev_x), float(prev_y)), (float(curr_x), float(curr_y)), stroke="black", stroke_width=1.5))
                prev_x, prev_y = curr_x, curr_y

        # 特徴点の抽出とラベル
        feature_points = []
        eq_m, val_m, x_m = self.maximum_deflection
        feature_points.append((x_m, (-val_m / abs(val_m) * max_val) if val_m != 0 else 0, eq_m))
        for (s,e), eq in self.deflection:
            sub_eq_eval = eq
            for sym in eq.free_symbols:
                if sym.name == "x": continue
                for ds, dv in dict_vals.items():
                    if sym.name == ds.name:
                        sub_eq_eval = sub_eq_eval.subs(sym, dv)
            
            feature_points.append((s, -float(sub_eq_eval.subs({sp.symbols("x"): s}).evalf()), eq))
            feature_points.append((e, -float(sub_eq_eval.subs({sp.symbols("x"): e}).evalf()), eq))

        unique_points = []
        for p in feature_points:
            # y値だけでなくx値も考慮して重複排除
            if not any([math.isclose(float(p[1]), float(up[1]), rel_tol=1e-5) for up in unique_points]):
                unique_points.append(p)

        unique_points.sort(key=lambda x: x[1])

        for i, (fx, fy, feq) in enumerate(unique_points):
            # SymPy式の場合はsubsとevalfを行い、数値の場合は直接変換する
            try:
                if hasattr(fx, 'subs'):
                    fx_res = fx.subs(dict_vals).evalf()
                    fx_val = float(fx_res) if fx_res.is_Number else 0.0
                else:
                    fx_val = float(fx)
                
                if hasattr(fy, 'subs'):
                    fy_res = fy.subs(dict_vals).evalf()
                    fy_val = float(fy_res) if fy_res.is_Number else 0.0
                else:
                    fy_val = float(fy)
            except Exception:
                fx_val = 0.0
                fy_val = 0.0
            
            px = float(center_x - width / 2 + fx_val * width)
            py = float(center_y - fy_val * maximum_y / max_val)
            
            # xにfx*Lを代入してラベル用の定数式を作成
            label_eq = sp.simplify(sp.nsimplify(feq.subs({sp.symbols("x"): fx * sp.symbols("L")})))
            
            if i % 2 == 0:
                dwg.draw_equation(f'{sp.latex(label_eq)}', position=(float(dwg.width), float(py)), fontsize=7, fill="white")
                dwg.add(dwg.line((float(center_x + width / 2), float(py)), (float(px), float(py)),
                    stroke="black", stroke_width=0.75, stroke_linecap="round", stroke_dasharray="3,3"))
            else:
                dwg.draw_equation(f'{sp.latex(label_eq)}', position=(0.0, float(py)), fontsize=7, fill="white")
                dwg.add(dwg.line((float(dwg.width*0.1), float(py)), (float(px), float(py)),
                    stroke="black", stroke_width=0.75, stroke_linecap="round", stroke_dasharray="3,3"))

        self._deflection_diagram = dwg



    def generate_force_balance_equation(self, start, end):
        """
        start(0-1)からend(0-1)までの区間での自由体図における力の釣合いの式を作成する。
        """

        load = 0
        
        #支点反力
        for reaction in self._reaction_forces:
            if reaction[2] <= end and reaction[2] >= start and "M" not in str(reaction[0]):
                load += reaction[0]

        #作用
        total_concentrated_loads_number = len([action for action in self.actions if isinstance(action, Action.ConcentratedLoad)])
        cln = 1; dln = 1
        for action in self.actions:
            if isinstance(action, Action.ConcentratedLoad):
                if total_concentrated_loads_number > 1:
                    symbol = sp.symbols(f"P_{cln}")
                    cln += 1
                else:
                    symbol = sp.symbols(f"P")
                if action.position <= end and action.position >= start:
                    load -= symbol
            
            if isinstance(action, Action.DistributedLoad):
                if start == 0:
                    load -= action.equivalent_concentrated_load_of_FBD("0","x", end)[0]
                elif end == 1:
                    load -= action.equivalent_concentrated_load_of_FBD("x","L", start)[0]


        #断面力
        V = sp.symbols("V")
        if start == 0 and end < 1:
            load -= V
        elif start > 0 and end == 1:
            load += V

        return load

    def generate_moment_balance_equation(self, start, end, center):
        """
        start(0-1)からend(0-1)までの区間での自由体図におけるモーメントの釣合いの式を作成する。
        center: モーメントの中心位置(sp式)
        """
        #print(f"Generating moment balance equation from {start} to {end} around {center}")
        moment = 0
        #支点反力
        for reaction in self._reaction_forces:
            if reaction[2] <= end and reaction[2] >= start:
                if "M" in str(reaction[0]):
                    moment += reaction[0]
                else:
                    length_symbol = None
                    for length in self._lengths:
                        if length[1] == reaction[2]:
                            length_symbol = length[0]
                            break
                    if length_symbol is None:
                        length_symbol = reaction[2]
                    moment += reaction[0] * (length_symbol - center)
        
        #作用
        total_concentrated_loads_number = len([action for action in self.actions if isinstance(action, Action.ConcentratedLoad)])
        cln = 1; cmn = 0; dln = 1

        for action in self.actions:
            if isinstance(action, Action.ConcentratedLoad):
                if total_concentrated_loads_number > 1:
                    symbol = sp.symbols(f"P_{cln}")
                    cln += 1
                else:
                    symbol = sp.symbols(f"P")

                if action.position <= end and action.position >= start:
                    length_symbol = None
                    for length in self._lengths:
                        if length[1] == action.position:
                            length_symbol = length[0]
                            break
                    if length_symbol is None:
                        length_symbol = action.position
                    moment += symbol * (center - length_symbol)
            
            if isinstance(action, Action.ConcentratedMoment):
                if action.position <= end and action.position >= start:
                    symbol = sp.symbols(f"M_{cmn}")
                    moment += symbol
                cmn += 1
            
            if isinstance(action, Action.DistributedLoad):
                if start == 0:
                    eq_magnitude, eq_position = action.equivalent_concentrated_load_of_FBD("0","x", end)
                elif end == 1:
                    eq_magnitude, eq_position = action.equivalent_concentrated_load_of_FBD("x","L", start)
                    eq_position = eq_position + sp.symbols("x")

                moment += eq_magnitude * (center - eq_position)
        
        #断面力
        M = sp.symbols("M")
        if start == 0 and end < 1:
            moment += M
        elif start > 0 and end == 1:
            moment -= M

        return moment

