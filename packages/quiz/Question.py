from typing import List

import numpy as np
from decimal import Decimal, ROUND_HALF_UP
import math

from . import Action

class Question():
    def __init__(self, id):
        """
        一問一答形式
        self._id: int
        self._cross_section_classes: クラスのlist，１要素目はクラス，２要素目以降は寸法の最小値と最大値のlist
        self.cross_section_dementions: 寸法の最小値と最大値のlist
        self._material_classes: クラスのlist
        self._figure_classes: クラスのlist
        self._parameter_classes: クラスのlist，１要素目はクラス，２要素目以降は値の最小値と最大値のlist
        self._question: str
        self._action: Action
        self._cross_section: CrossSection
        self._material: Material
        """
        # 外部入力変数
        self._id = id
        self._action_classes = None
        self._parameter_classes = None
        self._cross_section_classes = None
        self.cross_section_demension_ranges = None
        self._material_classes = None 
        self._figure_classes = None
        self._parameter_classes = None
        self._answer_unit = None
        self._beam_class = None


        #組み合わせ棒など，棒を使用する問題
        self._rod_class = None
        self._truss_class = None

        # 内部生成変数
        self._question = ""
        self._action = None
        self._cross_section = None
        self._material = None
        self._parameters = None
        self._answer = None
        self._raw_answer = None
        self._explanation = None
        self._explanation_figures = None

        # 組み合わせ棒など，棒を使用する問題
        self._rod = None
        self._truss = None

        # 組み合わせ梁など，梁を使用する問題
        self._beam = None
        self.score = 0
        

        
    @property
    def id(self):
        return self._id
    
    @property
    def question(self):
        if self._question == "":
            self._question = self.generate_question()
        return self._question

    @property
    def answer(self):
        if self._raw_answer is None:
            self._raw_answer = self.generate_answer()
            #print(f"raw_answer: {self._raw_answer}")
        if self._answer is None:
            self._answer = self.round_half_up_dynamic(self._raw_answer)
            
        return self._answer
    
    @property
    def raw_answer(self):
        if self._raw_answer is None:
            self._raw_answer = self.generate_answer()
        #print(f"raw_answer: {self._raw_answer}")
        return self._raw_answer
    
    @property
    def explanation(self):
        if self._explanation is None:
            self._explanation = self.generate_explanation()
        return self._explanation

    @property
    def explanation_figures(self):
        if self._explanation_figures is None:
            self._explanation_figures = self.generate_explanation_figures()
        return self._explanation_figures

    @property
    def answer_unit(self):
        return self._answer_unit

    @property
    def action(self):
        if (self._action_classes is not None) and (self._action is None):
            action_class_info = self._action_classes[self._id % len(self._action_classes)]
            action_class = action_class_info[0]
            range = action_class_info[1]

            value_unit = range[2] if len(range) >= 3 else 1
            np.random.seed(self._id)
            self._action = action_class(np.random.randint(range[0], range[1]) // value_unit * value_unit)
        return self._action

    @property
    def cross_section(self):

        if (self._cross_section_classes is not None) and (self._cross_section is None):
            #print(f"{self._id}, {self._cross_section_classes}, {len(self._cross_section_classes)}, {self._id % len(self._cross_section_classes)}")
            cross_section_info = self._cross_section_classes[self._id % len(self._cross_section_classes)]
            cross_section_class = cross_section_info[0]
            np.random.seed(self._id)
            demensions = []
            for demension in cross_section_info[1:]:
                if len(demension) > 2:
                    unit = demension[2]
                    demensions.append(np.random.randint(demension[0], demension[1]) // unit * unit)
                else:
                    demensions.append(np.random.randint(demension[0], demension[1]))

            self._cross_section = cross_section_class(*demensions)
        return self._cross_section

    @property
    def material(self):
        if (self._material_classes is not None) and (self._material is None):
            material_class = self._material_classes[self._id % len(self._material_classes)]
            self._material = material_class()
        return self._material
    
    @property
    def parameters(self):
        if (self._parameter_classes is not None) and (self._parameters is None):
            self._parameters = []
            np.random.seed(self._id)
            for parameter_class_info in self._parameter_classes:
                parameter_class = parameter_class_info[0]
                range = parameter_class_info[1]
                
                value_unit = range[2] if len(range) >= 3 else 1
                self._parameters.append(parameter_class(np.random.randint(range[0], range[1])// value_unit * value_unit))

        return self._parameters
    
    @property
    def rod(self):

        if (self._rod_class is not None) and (self._rod is None):
            args = (self._id,) + self._rod_class[1:]
            self._rod = self._rod_class[0](*args)
        return self._rod
    
    @property
    def truss(self):
        if (self._truss_class is not None) and (self._truss is None):
            args = (self._id,) + self._truss_class[1:]
            self._truss = self._truss_class[0](*args)
        return self._truss
    
    @property
    def beam(self):
        np.random.seed(self._id)
        if (self._beam_class is not None) and (self._beam is None):
            for p in self._parameter_classes:
                if "Length" in p[0].__name__:
                    unit = p[1][2] if len(p[1]) >= 3 else 1
                    length = np.random.randint(p[1][0], p[1][1]) // unit * unit
                    break
            
            """支点"""
            supports = []
            for s in self._supports:
                unit = s[1][2] if len(s[1]) >= 3 else 1
                position = np.random.randint((s[1][0]*1.01)//unit, ((s[1][1]*1.01)+unit)//unit) * unit
                #小数点以下2桁で丸める
                position = round(position, 2)
                import sympy as sp
                position = sp.nsimplify(position, tolerance=1e-10)
                supports.append((s[0], position))
            
            actions = []

            """荷重"""
            for a in self._actions:
                unit = a[2][2] if (a[2] is not None) and (len(a[2]) >= 3) else 1

                """
                位置の決定
                """
                position = None
                
                if a[2] is not None and a[0].__name__ != "DistributedLoad":

                    count = 0
                    while True:
                        count += 1
                        if count > 1000:
                            #print(a[0], a[1], a[2])
                            #インスタンスのクラス名を取得
                            raise Exception(f"{a[0].__name__}の位置の決定に失敗しました")
                        
                        position = np.random.randint((a[2][0]*1.01)//unit, ((a[2][1]*1.01)+unit)//unit) * unit
                        #print(f"position: {position}")

                        # 集中荷重は支点と重ならないようにする
                        if "ConcentratedLoad" in a[0].__name__:
                            overlap = False
                            for support in supports:
                                if position == support[1]:
                                    overlap = True
                                    break
                            if not overlap:
                                break

                        # 固定支点を含むかを確認
                        fix_exists = False
                        for support in supports:
                            if support[0] == "fixed":
                                fix_exists = True
                                break

                        if "ConcentratedMoment" in a[0].__name__ and fix_exists:
                            # 固定支点がある場合，集中モーメントは固定支点に作用させない
                            overlap = False
                            for support in supports:
                                if position == support[1] and support[0] == "fixed":
                                    overlap = True
                                    #print("overlap with fixed support")
                                    break
                            if not overlap:
                                break

                        elif "ConcentratedMoment" in a[0].__name__:
                            # 固定支点がない場合，集中モーメントはどこでもよい
                            break
                elif a[2] is not None and a[0].__name__ == "DistributedLoad":
                    # 分布荷重の場合は位置範囲をそのまま使う
                    position = a[2]


                #print(a)

                if len(a) >= 4:
                    """
                    向きの決定（集中荷重のみ）
                    現状は未実装
                    """
                    if a[3] is not None and "ConcentratedLoad" in a[0].__name__:
                        angle = None
                    
                    """
                    関数の決定（分布荷重のみ）
                    """
                    function = "1"
                    if a[3] is not None and "DistributedLoad" in a[0].__name__:
                        function = a[3]


                """
                大きさの決定
                """

                magnitude_unit = a[1][2] if len(a[1]) >= 3 else 1
                magnitude = np.random.randint(a[1][0], a[1][1]) // magnitude_unit * magnitude_unit

                

                #集中荷重の場合は向きをランダムに決定
                if "ConcentratedLoad" in a[0].__name__:
                    
                    if len(a) < 4:
                        actions.append(a[0](magnitude, position))

                    else:
                        if a[3] is not None:
                            unit = a[3][2] if len(a[3]) >= 3 else 1
                            angle = np.random.randint((a[3][0]*1.01)//unit, ((a[3][1]*1.01)+unit)//unit) * unit
                        else:
                            angle = 0

                        actions.append(a[0](magnitude, position, angle))


                elif "ConcentratedMoment" in a[0].__name__:
                    actions.append(a[0](magnitude, position))
                
                elif "DistributedLoad" in a[0].__name__:
                    actions.append(a[0](magnitude, position, length, function))


            #print(self.material)
            args = (length,)  + (supports,) + (actions,) + (self.cross_section,) + (self.material,)
            #print(args)
            #print(self._beam_class)
            self._beam = self._beam_class(*args)


        return self._beam

    def __str__(self):
        if self._question == "":
            self._question = self.generate_question()
        return self._question
    
    def __repr__(self):
        return self.__str__()

    def generate_question(self):
        print("not defined generate_question for this question")
    
    def generate_question_figures(self):
        #print("not defined generate_question_figures for this question")
        return None
    
    def generate_answer(self):
        print("not defined generate_answer for this question")
    
    def generate_explanation(self):
        print("not defined generate_explanation for this question")
    
    def generate_explanation_figures(self):
        print("not defined generate_explanation_figures for this question")
        return None

    def scoring(self, answer, allocation):
        self.scoringV3(answer, allocation)

    def scoringV1(self, answer, allocation):
        score = 0
        corrects = self.answer

        if corrects == answer:
            score += allocation
        else:
            #corrects と　answerの符号が合致する場合は配点の1/3を加点
            if (corrects > 0 and answer > 0) or (corrects < 0 and answer < 0):
                score += allocation / 3
            corrects_text  = f"{corrects:.0E}"
            answer_text = f"{answer:.0E}"
            #最初の数字が合致する場合は配点の1/3を加点
            if corrects_text.split("E")[0][-1] == answer_text.split("E")[0][-1]:
                score += allocation / 3
            #指数が±1の時は配点の1/3を加点
            if abs(int(corrects_text.split("E")[1]) - int(answer_text.split("E")[1])) <= 1:
                score += allocation / 3

        self.score = score
    
    def scoringV2(self, answer, allocation):
        """
        Docstring for scoringV2
        回答が少数第2位までの場合の採点方法
        """
        score = 0
        corrects = self.answer


        answer = self.round_half_up_dynamic(answer)
        #完全一致の場合
        if corrects == answer:
            score += allocation
        #正答が0の場合
        elif corrects == 0:
            pass
        #倍半分の範囲内であれば配点の0.8倍を加点
        elif answer / corrects <= 3.0 and answer / corrects >= 0.33 and answer / corrects >= 0:
            score += allocation * 0.8
        # 化数のみが一致する場合は配点の0.8を加点
        elif f"{corrects:.1E}"[:4] == f"{answer:.1E}"[:4]:
            score += allocation * 0.8
        # 化数の符号のみ異なる場合は配点の0.8を加点
        elif f"{abs(corrects):.1E}" == f"{abs(answer):.1E}":
            score += allocation * 0.8
        # 絶対値の化数のみが一致する場合は配点の0.8を加点
        elif f"{abs(corrects):.1E}"[:4] == f"{abs(answer):.1E}"[:4]:
            score += allocation * 0.6
        # 値が倍半分の範囲内，かつ化数の符号が異なる場合は配点の0.6を加点
        elif abs(answer / corrects) <= 3.0 and abs(answer / corrects) >= 0.33:
            score += allocation * 0.6
    

        self.score = score

    def scoringV3(self, answer, allocation):
        """
        Docstring for scoringV3
        回答が少数第2位までの場合の採点方法
        正答がリストの場合に対応
        """
        score = 0
        corrects = self.answer
        answer = self.round_half_up_dynamic(answer)

        if type(corrects) != list:
            corrects = [corrects]

        for correct in corrects:
            buf_score = 0
            #完全一致の場合
            if correct == answer:
                buf_score += allocation
            #正答が0の場合
            elif correct == 0:
                pass
            #倍半分の範囲内であれば配点の0.8倍を加点
            elif answer / correct <= 3.0 and answer / correct >= 0.33 and answer / correct >= 0:
                buf_score += allocation * 0.8
            # 化数のみが一致する場合は配点の0.8を加点
            elif f"{correct:.1E}"[:4] == f"{answer:.1E}"[:4]:
                buf_score += allocation * 0.8
            # 化数の符号のみ異なる場合は配点の0.8を加点
            elif f"{abs(correct):.1E}" == f"{abs(answer):.1E}":
                buf_score += allocation * 0.8
            # 絶対値の化数のみが一致する場合は配点の0.8を加点
            elif f"{abs(correct):.1E}"[:4] == f"{abs(answer):.1E}"[:4]:
                buf_score += allocation * 0.6
            # 値が倍半分の範囲内，かつ化数の符号が異なる場合は配点の0.6を加点
            elif abs(answer / correct) <= 3.0 and abs(answer / correct) >= 0.33:
                buf_score += allocation * 0.6
            
            if buf_score > score:
                score = buf_score
        

        self.score = score


    def round_half_up_dynamic(self, float_value):
        """
        四捨五入
        """
        f = float_value
        #print(f"round_half_up_dynamic: {f}")
        try:        
            d = int(math.floor(math.log10(abs(f))))
            rounding_place = Decimal('1e{}'.format(d-1))
            return Decimal(str(f)).quantize(rounding_place, rounding=ROUND_HALF_UP)
        except ValueError:
            return Decimal('0')
        except OverflowError:
            return Decimal('0')

    def answer_format(self, sci_str):
        # 正答表示を自然に
        # 上付き文字の対応表
        superscript_map = {
            "-": "⁻",
            "0": "⁰",
            "1": "¹",
            "2": "²",
            "3": "³",
            "4": "⁴",
            "5": "⁵",
            "6": "⁶",
            "7": "⁷",
            "8": "⁸",
            "9": "⁹"
        }

        # 浮動小数点文字列を指数表記に変換（例：-7E-03 → -7.0e-03）
        #print(sci_str)
        number = float(sci_str)
        mantissa, exp = f"{number:.10e}".split("e")  # 精度は必要に応じて調整可

        # 基数（mantissa）の余分な小数点や0を取り除く
        mantissa = mantissa.rstrip('0').rstrip('.') if '.' in mantissa else mantissa

        # 指数（exponent）を上付き文字に変換
        exp_sign = "-" if int(exp) < 0 else ""
        exp_digits = str(abs(int(exp)))
        superscript_exp = ''.join(superscript_map[d] for d in exp_sign + exp_digits)
        
        #print(f"Formatted answer: {mantissa}×10{superscript_exp}")
        
        return f"{mantissa}×10{superscript_exp}"
    
class BigQuestion(Question):
    def __init__(self, id):
        """
        複数質問の集合
        """
        super().__init__(id)
        
    @property
    def answer(self):
        if self._raw_answer is None:
            self._raw_answer = self.generate_answer()
        if self._answer is None:
            self._answer = []
            for a in self._raw_answer:
                # a がリスト（１つの質問に対して複数の正答がある）場合に対応
                if type(a) == list:
                    self._answer.append([self.round_half_up_dynamic(sub_a) for sub_a in a])
                else:
                    self._answer.append(self.round_half_up_dynamic(a))
        return self._answer

    def scoring(self, answer, allocation, q_index=None):
        self.scoringV3(answer, allocation, q_index)
    
    def scoringV1(self, answer, allocation, q_index=None):


        if q_index is None:
            """
            全ての回答に対してスコアを計算
            """
            self.score = []

            corrects = self.answer

            allocation = allocation / len(corrects)  # 配点を各回答に均等に割り当て
            #print(f"corrects: {corrects}, answer: {answer}")
            for i in range(len(corrects)):
                score = 0
                if corrects[i] == answer[i]:
                    score += allocation
                else:
                    #corrects と　answerの符号が合致する場合は配点の1/3を加点
                    if (corrects[i] > 0 and answer[i] > 0) or (corrects[i] < 0 and answer[i] < 0):
                        score += allocation / 3
                    corrects_text  = f"{corrects[i]:.0E}"
                    answer_text = f"{answer[i]:.0E}"
                    #最初の数字が合致する場合は配点の1/3を加点
                    if corrects_text.split("E")[0][-1] == answer_text.split("E")[0][-1]:
                        score += allocation / 3
                    #指数が±1の時は配点の1/3を加点
                    if abs(int(corrects_text.split("E")[1]) - int(answer_text.split("E")[1])) <= 1:
                        score += allocation / 3

                self.score.append(score)
        else:
            """
            特定の質問に対してスコアを計算
            """
            if self.score == 0:
                self.score = [0] * len(self.answer)

            self.score[q_index] = 0
            corrects = self.answer[q_index]
            score = 0
            
            if corrects == answer:
                score += allocation
            else:
                #corrects と　answerの符号が合致する場合は配点の1/3を加点
                if (corrects > 0 and answer > 0) or (corrects < 0 and answer < 0):
                    score += allocation / 3
                corrects_text  = f"{corrects:.0E}"
                answer_text = f"{answer:.0E}"
                #最初の数字が合致する場合は配点の1/3を加点
                if corrects_text.split("E")[0][-1] == answer_text.split("E")[0][-1]:
                    score += allocation / 3
                #指数が±1の時は配点の1/3を加点
                if abs(int(corrects_text.split("E")[1]) - int(answer_text.split("E")[1])) <= 1:
                    score += allocation / 3

            self.score[q_index] = score

    def scoringV2(self, answer, allocation, q_index=None):
        """
        Docstring for scoringV2
        回答が少数第2位までの場合の採点方法
        """
        if q_index is None:
            """
            全ての回答に対してスコアを計算
            """
            self.score = []

            corrects = self.answer

            allocation = allocation / len(corrects)  # 配点を各回答に均等に割り当て
            #print(f"corrects: {corrects}, answer: {answer}")
            for i in range(len(corrects)):
                ans = self.round_half_up_dynamic(answer[i])
                score = 0
                #完全一致の場合
                if corrects[i] == ans:
                    score += allocation
                #倍半分の範囲内であれば配点の0.8倍を加点
                elif ans / corrects[i] <= 3.0 and ans / corrects[i] >= 0.33 and ans / corrects[i] >= 0:
                    score += allocation * 0.8
                # 化数のみが一致する場合は配点の0.8を加点
                elif f"{corrects[i]:.1E}"[:4] == f"{ans:.1E}"[:4]:
                    score += allocation * 0.8
                # 化数の符号のみ異なる場合は配点の0.8を加点
                elif f"{corrects[i]:.1E}"[1:] == f"{ans:.1E}"[1:]:
                    score += allocation * 0.8
                # 化数（符号除く）のみが一致する場合は配点の0.6を加点
                elif f"{abs(corrects[i]):.1E}"[:4] == f"{abs(ans):.1E}"[:4]:
                    score += allocation * 0.6
                # 値が倍半分の範囲内，かつ化数の符号が異なる場合は配点の0.6を加点
                elif abs(ans / corrects[i]) <= 3.0 and abs(ans / corrects[i]) >= 0.33:
                    score += allocation * 0.6

                self.score.append(score)
        else:
            """
            特定の質問に対してスコアを計算
            """
            if self.score == 0:
                self.score = [0] * len(self.answer)

            print(f"{len(self.score)}, {len(self.answer)}, q_index: {q_index}")
            print(f"before scoring: {self.score}")

            self.score[q_index] = 0
            corrects = self.answer[q_index]
            score = 0
            answer = self.round_half_up_dynamic(answer)

            print(f"corrects: {corrects}, answer: {answer}, correctsstr: {f'{corrects:.1E}'}, answerstr: {f'{answer:.1E}'}")
            

            #完全一致の場合
            if corrects == answer:
                score += allocation
            #倍半分の範囲内であれば配点の0.8倍を加点
            elif corrects == 0:
                pass
            elif answer / corrects <= 3.0 and answer / corrects >= 0.33 and answer / corrects >= 0:
                print("倍半分の範囲内")
                score += allocation * 0.8  
            # 化数のみが一致する場合は配点の0.8を加点
            elif f"{corrects:.1E}"[:4] == f"{answer:.1E}"[:4]:
                print("化数のみが一致する場合")
                score += allocation * 0.8
            # 化数の符号のみ異なる場合は配点の0.8を加点
            elif f"{corrects:.1E}"[1:] == f"{answer:.1E}"[1:]:
                print("化数の符号のみ異なる場合")
                score += allocation * 0.8
            # 化数（符号除く）のみが一致する場合は配点の0.6を加点
            elif f"{abs(corrects):.1E}"[:4] == f"{abs(answer):.1E}"[:4]:
                print("絶対値の化数のみが一致する場合")
                score += allocation * 0.6
            # 値が倍半分の範囲内，かつ化数の符号が異なる場合は配点の0.6を加点
            elif abs(answer / corrects) <= 3.0 and abs(answer / corrects) >= 0.33:
                print("値が倍半分の範囲内，かつ化数の符号が異なる場合")
                score += allocation * 0.6 

            self.score[q_index] = score

    def scoringV3(self, answer, allocation, q_index=None):
        """
        Docstring for scoringV2
        回答が少数第2位までの場合の採点方法
        questionクラスのscoringV3と同様に，正答が複数ある場合は最も高いスコアを採用する方式に変更
        """
        if q_index is None:
            """
            全ての回答に対してスコアを計算
            """
            self.score = []

            corrects = self.answer

            allocation = allocation / len(corrects)  # 配点を各回答に均等に割り当て
            #print(f"corrects: {corrects}, answer: {answer}")
            for i, correct in enumerate(corrects):

                ans = self.round_half_up_dynamic(answer[i])

                if type(correct) != list:
                    correct = [correct]

                score = 0
                for c in correct:
                    buf_score = 0

                    #完全一致の場合
                    if c == ans:
                        buf_score += allocation
                    #正答が0の場合
                    elif c == 0:
                        pass
                    #倍半分の範囲内であれば配点の0.8倍を加点
                    elif ans / c <= 3.0 and ans / c >= 0.33 and ans / c >= 0:
                        buf_score += allocation * 0.8
                    # 化数のみが一致する場合は配点の0.8を加点
                    elif f"{c:.1E}"[:4] == f"{ans:.1E}"[:4]:
                        buf_score += allocation * 0.8
                    # 化数の符号のみ異なる場合は配点の0.8を加点
                    elif f"{c:.1E}"[1:] == f"{ans:.1E}"[1:]:
                        buf_score += allocation * 0.8
                    # 化数（符号除く）のみが一致する場合は配点の0.6を加点
                    elif f"{abs(c):.1E}"[:4] == f"{abs(ans):.1E}"[:4]:
                        buf_score += allocation * 0.6
                    # 値が倍半分の範囲内，かつ化数の符号が異なる場合は配点の0.6を加点
                    elif abs(ans / c) <= 3.0 and abs(ans / c) >= 0.33:
                        buf_score += allocation * 0.6
                    
                    if buf_score > score:
                        score = buf_score

                self.score.append(score)
        else:
            """
            特定の質問に対してスコアを計算
            """
            if self.score == 0:
                self.score = [0] * len(self.answer)

            # print(f"{len(self.score)}, {len(self.answer)}, q_index: {q_index}")
            # print(f"before scoring: {self.score}")

            self.score[q_index] = 0
            corrects = self.answer[q_index]
            score = 0
            answer = self.round_half_up_dynamic(answer)

            # print(f"corrects: {corrects}, answer: {answer}, correctsstr: {f'{corrects:.1E}'}, answerstr: {f'{answer:.1E}'}")
            
            if type(corrects) != list:
                corrects = [corrects]

            for correct in corrects:
                buf_score = 0
                #完全一致の場合
                if correct == answer:
                    buf_score += allocation
                #正答が0の場合
                elif correct == 0:
                    pass
                #倍半分の範囲内であれば配点の0.8倍を加点
                elif answer / correct <= 3.0 and answer / correct >= 0.33 and answer / correct >= 0:
                    # print("倍半分の範囲内")
                    buf_score += allocation * 0.8  
                # 化数のみが一致する場合は配点の0.8を加点
                elif f"{correct:.1E}"[:4] == f"{answer:.1E}"[:4]:
                    # print("化数のみが一致する場合")
                    buf_score += allocation * 0.8
                # 化数の符号のみ異なる場合は配点の0.8を加点
                elif f"{correct:.1E}"[1:] == f"{answer:.1E}"[1:]:
                    # print("化数の符号のみ異なる場合")
                    buf_score += allocation * 0.8
                # 化数（符号除く）のみが一致する場合は配点の0.6を加点
                elif f"{abs(correct):.1E}"[:4] == f"{abs(answer):.1E}"[:4]:
                    # print("絶対値の化数のみが一致する場合")
                    buf_score += allocation * 0.6
                # 値が倍半分の範囲内，かつ化数の符号が異なる場合は配点の0.6を加点
                elif abs(answer / correct) <= 3.0 and abs(answer / correct) >= 0.33:
                    # print("値が倍半分の範囲内，かつ化数の符号が異なる場合")
                    buf_score += allocation * 0.6 
                
                if buf_score > score:
                    score = buf_score

            self.score[q_index] = score

