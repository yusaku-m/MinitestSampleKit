from .Figure import Figure

class NameBox():
    def __init__(self, height = 32, student_number = None, name = None):
        # 入力変数
        self._height = height
        self._student_number = student_number
        self._name = name

        # 生成変数
        self._figure = None

    @property
    def figure(self):
        if self._figure is None:
            self.generate_figure()
        return self._figure

    
    def generate_figure(self):
        self._figure = Figure(size=(self._height*5.25, self._height))
        square_size = self._height*0.7

        #出席番号欄
        self._figure.add(self._figure.text(f"十の位", insert=(self._height*0.1 +square_size * 0.5, self._height*0.1), font_size=square_size*0.3, font_family='Meiryo', text_anchor='middle', alignment_baseline='hanging'))
        self._figure.add(self._figure.rect(insert=(self._height*0.1, square_size * 0.3), size=(square_size, square_size), fill='none', stroke='black', stroke_width=1.5))
        self._figure.add(self._figure.text(f"一の位", insert=(self._height*0.1 + square_size*1.7, self._height*0.1), font_size=square_size*0.3, font_family='Meiryo', text_anchor='middle', alignment_baseline='hanging'))
        self._figure.add(self._figure.rect(insert=(self._height*0.1+square_size*1.2, square_size*0.3), size=(square_size, square_size), fill='none', stroke='black', stroke_width=1.5))

        if self._student_number is not None:
            try:
                s_num = str(int(self._student_number)).zfill(2)
                tens = s_num[-2]
                ones = s_num[-1]
                font_size = square_size*0.8
                self._figure.add(self._figure.text(tens, insert=(self._height*0.1 + square_size*0.5 , square_size * 0.3 + font_size), font_size=font_size, font_family='Meiryo', text_anchor='middle', alignment_baseline='hanging'))
                self._figure.add(self._figure.text(ones, insert=(self._height*0.1 + square_size*1.7 , square_size * 0.3 + font_size), font_size=font_size, font_family='Meiryo', text_anchor='middle', alignment_baseline='hanging'))
            except:
                pass

        #氏名欄
        self._figure.add(self._figure.text(f"氏名", insert=(self._height*0.1 + square_size*2.5, self._height*0.1), font_size=square_size*0.3, font_family='Meiryo', text_anchor='start', alignment_baseline='hanging'))
        self._figure.add(self._figure.rect(insert=(square_size*2.5, square_size*0.3), size=(square_size*5, square_size), fill='none', stroke='black', stroke_width=1.5))

        if self._name is not None:
             font_size = square_size*0.8
             self._figure.add(self._figure.text(self._name, insert=(square_size*2.6, square_size * 0.3 + font_size), font_size=font_size, font_family='Meiryo', text_anchor='start', alignment_baseline='hanging'))
