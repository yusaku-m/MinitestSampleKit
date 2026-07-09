from .Figure import Figure

class Answer():
    def __init__(self, number, unit,height = 48):
        # 入力変数
        self._number = number
        self._height = height
        self._unit = unit

        # 生成変数
        self._figure = None

    @property
    def figure(self):
        if self._figure is None:
            self.generate_figure()
        return self._figure

    
    def generate_figure(self):
        self._figure = Figure(size=(self._height*5, self._height))
        square_size = self._height*0.8

        #基数及び符号欄
        self._figure.add(self._figure.rect(insert=(self._height*0.1, self._height*0.2), size=(square_size, square_size), fill='none', stroke='black', stroke_width=1.5))
        self._figure.add(self._figure.rect(insert=(self._height*0.1 + square_size*1.2, self._height*0.2), size=(square_size, square_size), fill='none', stroke='black', stroke_width=1.5))
        self._figure.add(self._figure.text(f"×10", insert=(self._height*1.9, self._height*0.6), font_size=square_size*0.45, font_family='Meiryo', text_anchor='start', alignment_baseline='middle'))

        # 符号欄であることを文字で示す
        self._figure.add(self._figure.text("+/-", insert=(self._height*0.1 + square_size*0.5, self._height*0.05), font_size=square_size*0.25, font_family='Meiryo', text_anchor='middle', alignment_baseline='baseline'))

        # 基数の文字を配置
        self._figure.add(self._figure.text(f"化数", insert=(self._height*0.1 + square_size*1.7, self._height*0.05), font_size=square_size*0.25, font_family='Meiryo', text_anchor='middle', alignment_baseline='baseline'))

        #指数および符号欄
        self._figure.add(self._figure.rect(insert=(square_size*3.5, self._height*0.1), size=(square_size/2, square_size/2), fill='none', stroke='black', stroke_width=1.5))
        self._figure.add(self._figure.rect(insert=(square_size*4.1, self._height*0.1), size=(square_size/2, square_size/2), fill='none', stroke='black', stroke_width=1.5))
        self._figure.add(self._figure.text(f"{self._unit}", insert=(self._height*3.75, self._height*0.6), font_size=square_size*0.35, font_family='Meiryo', text_anchor='start', alignment_baseline='middle'))

        # 符号欄であることを文字で示す
        self._figure.add(self._figure.text("+/-", insert=(square_size*3.5 + square_size/4, 0), font_size=square_size*0.25, font_family='Meiryo', text_anchor='middle', alignment_baseline='baseline'))
        # 指数の文字を配置
        self._figure.add(self._figure.text(f"指数", insert=(square_size*4.35, 0), font_size=square_size*0.25, font_family='Meiryo', text_anchor='middle', alignment_baseline='baseline'))

class AnswerV2(Answer):
    """
    化数の桁数を指定できるバージョン
    """

    def __init__(self, number, unit, digits=3, height = 48):
        self._digits = digits
        super().__init__(number, unit, height)
    
    def generate_figure(self):
        self._figure = Figure(size=(self._height*(2 + self._digits*1.2 + 2), self._height))
        square_size = self._height*0.8

        #基数及び符号欄
        self._figure.add(self._figure.rect(insert=(self._height*0.1, self._height*0.2), size=(square_size, square_size), fill='none', stroke='black', stroke_width=1.5))

        self._figure.add(self._figure.rect(insert=(self._height*0.1 + square_size*1.2, self._height*0.2), size=(square_size, square_size), fill='none', stroke='black', stroke_width=1.5))
        #一の位
        self._figure.add(self._figure.text(f"1の位", insert=(self._height*0.1 + square_size*1.7, self._height*0.1), font_size=square_size*0.2, font_family='Meiryo', text_anchor='middle', alignment_baseline='middle'))

        #小数点を配置
        if self._digits > 1:
            self._figure.add(self._figure.text(".", insert=(self._height*0.1 + square_size*1.2 + square_size*1.15, self._height*1.0), font_size=square_size*0.45, font_family='Meiryo', text_anchor='middle', alignment_baseline='middle'))
            
        # 桁数分の枠を配置
        for i in range(self._digits-1):
            self._figure.add(self._figure.rect(insert=(self._height*0.1 + square_size*2.5 + square_size*1.2*i, self._height*0.2), size=(square_size, square_size), fill='none', stroke='black', stroke_width=1.5))
            #小数点第i+1位
            self._figure.add(self._figure.text(f"小数第{i+1}位", insert=(self._height*0.1 + square_size*2.5 + square_size*1.2*i + square_size*0.5, self._height*0.1), font_size=square_size*0.2, font_family='Meiryo', text_anchor='middle', alignment_baseline='middle'))

        self._figure.add(self._figure.text(f"×10", insert=(self._height*0.1 + square_size* (1.2*(self._digits+1)), self._height*0.7), font_size=square_size*0.45, font_family='Meiryo', text_anchor='start', alignment_baseline='middle'))



        # 符号欄であることを文字で示す
        self._figure.add(self._figure.text("+/-", insert=(self._height*0.1 + square_size*0.5, self._height*0.1), font_size=square_size*0.20, font_family='Meiryo', text_anchor='middle', alignment_baseline='baseline'))

        # 化数の文字を配置
        #self._figure.add(self._figure.text(f"化数", insert=(self._height*0.1 + square_size*1.7 + square_size*1.2*(self._digits-1)/2, 0), font_size=square_size*0.25, font_family='Meiryo', text_anchor='middle', alignment_baseline='baseline'))
        
        #指数および符号欄
        self._figure.add(self._figure.rect(insert=(self._height*0.1 + square_size*3.2 + square_size*(1.2*(self._digits-1)+0.3), self._height*0.1), size=(square_size/2, square_size/2), fill='none', stroke='black', stroke_width=1.5))
        self._figure.add(self._figure.rect(insert=(self._height*0.1 + square_size*3.8+ square_size*(1.2*(self._digits-1)+0.3), self._height*0.1), size=(square_size/2, square_size/2), fill='none', stroke='black', stroke_width=1.5))
        #単位
        if "$" not in self._unit :
            self._figure.add(self._figure.text(f"{self._unit}", insert=(self._height*4 + square_size*1.2*(self._digits-1), self._height*0.7), font_size=square_size*0.35, font_family='Meiryo', text_anchor='start', alignment_baseline='middle'))
        else:
            eq = f"{self._unit}".split("$")[1]
            self._figure.draw_equation(eq, position=(self._height*4 + square_size*1.2*(self._digits-1), self._height*0.7), fontsize=square_size*0.35, halign="left")


        # 符号欄であることを文字で示す
        self._figure.add(self._figure.text("+/-", insert=(self._height*0.1 + square_size*3.45 + square_size*(1.2*(self._digits-1)+0.3), 0), font_size=square_size*0.20, font_family='Meiryo', text_anchor='middle', alignment_baseline='baseline'))
        
        # 指数の文字を配置
        self._figure.add(self._figure.text(f"指数", insert=(self._height*0.1 + square_size*4.05 + square_size*(1.2*(self._digits-1)+0.3), 0), font_size=square_size*0.20, font_family='Meiryo', text_anchor='middle', alignment_baseline='baseline'))