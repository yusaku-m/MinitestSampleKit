from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.renderPDF import draw

from reportlab.lib.units import mm   

import os
import cv2
import numpy as np
import pandas as pd
import torch
import io
import json


from .Answer import AnswerV2 as Answer
from .NameBox import NameBox
from .Equation import Equation
from .Image import Image
from .Figure import FONT_PATH  # 日本語フォント登録は Figure 側で一元化（svglib+ReportLab 両対応）
from .Question import Question, BigQuestion

class Sheet():
    def __init__(self, title, questions, path: str = None,
                 marker_positions: list = [(10,284), (197, 284), (10, 10), (197, 10), (191, 10), (197, 16)],
                 marker_size: float = 3,
                 sheet_size: tuple = (210, 297),
                 monitor: bool = False,
                 student_number = None,
                 student_name = None,
                 metadata: dict = None) -> None:
        # 発行用変数
        self._title = title
        self._questions = questions

        #読み取り用変数
        self.sheet = None
        self.path = path
        self.marker_positions = marker_positions

        self.marker_size = marker_size
        self.sheet_size = sheet_size

        if sheet_size[0] > sheet_size[1]:
            self.direction = "horizontal"
        else:
            self.direction = "vertical"
    
        self.monitor = monitor
        self.answer_imgs = None
        self.answer_squares = None
        self.raw_answers = None
        self.format_answers = None
        self.student_number = student_number
        self.student_name = student_name
        self.score = 0
        self.metadata = metadata

    def __str__(self):
        """
        This method is used to return the title of the sheet.
        """
        return self._title

    @property
    def questions(self):
        """
        This method is used to get the questions.
        """
        return self._questions

    @property
    def corrects(self):
        """
        This method is used to get the answers of the questions.
        """
        return [q.answer for q in self._questions]
    
    
    def write_single_question(self, pdf_canvas, i, q, base_font_size, width, y, figure_y, initial_y, height, marker, answerbox):
        
        figure = q.generate_question_figures()
        width = 0
        
        if figure is None:
            # 断面や棒材の図がある場合は描画
            fig_exist = False
            ##print("make figure")
            if q.cross_section is not None:
                figure = q.cross_section.figure
                fig_exist = True

            elif q.rod is not None:
                ##print("make rod figure")
                figure = q.rod.figure
                fig_exist = True
            
            elif q.truss is not None:
                figure = q.truss.figure
                fig_exist = True
            
            elif q.beam is not None:
                figure = q.beam.figure
                fig_exist = True

            if fig_exist:
                width = figure.width
                height = figure.height

                buf_figure_y = y - height
                figure_y = buf_figure_y

                #図がページからはみ出す場合は改ページ
                if figure_y < 20*mm:
                    ##print(f"figure_y: {figure_y/mm:.1f} mm, です。改ページします。")
                    pdf_canvas.showPage()
                    if marker:
                        self.set_marker(pdf_canvas)
                    y = initial_y; figure_y = y - height
                
                figure.embed_to_pdf(pdf_canvas, 200*mm - width, figure_y)

        else:
            figure_y = y
            for fig in figure:
                width = fig.width
                height = fig.height

                buf_figure_y = figure_y - height
                figure_y = min(figure_y, buf_figure_y)

                #図がページからはみ出す場合は改ページ
                if figure_y < 20*mm:
                    pdf_canvas.showPage()
                    if marker:
                        self.set_marker(pdf_canvas)
                    y = initial_y; figure_y = y - height
                
                fig.embed_to_pdf(pdf_canvas, 200*mm - width, figure_y)


        pdf_canvas.setFillColorRGB(0, 0, 0); font_size = base_font_size; pdf_canvas.setFont('Meiryo', font_size)
        #問題番号の幅を取得
        font_size = base_font_size
        qnum_width = pdf_canvas.stringWidth(f"問{i+1}", 'Meiryo', font_size)

        #図の幅を除いた幅を取得
        text_width = 190*mm - width - 5*mm - qnum_width

        #問題文を求めた幅毎で改行
        if i > 0:
            y -= font_size * 1.618 * 0.5
        else:
            y -= font_size * 1.618
        if answerbox:
            text = f"{q}(s{q.id})"
        else:
            if q.answer_unit == "":
                text = f"{q}(s{q.id})"
            else:
                text = f"{q}[{q.answer_unit}](s{q.id})"

        #print(f"text_width: {text_width} , font_size: {font_size}")
        bufy = y
        y, first_line_y = self.embed_text(pdf_canvas, text, base_font_size, qnum_width + 10*mm + font_size * 0.5, text_width, y, initial_y, marker)

        if y > bufy:
            figure_y = y

        pdf_canvas.setFont('Meiryo', base_font_size)
        pdf_canvas.drawString(10*mm, first_line_y, f"問{i+1}")

        # 回答ボックスを描画
        if answerbox:
            answer = Answer(q.id, q.answer_unit)
            figure = answer.figure
            width = figure.width
            height = figure.height

            buf_figure_y = y - height - 3*mm
            figure_y = min(figure_y, buf_figure_y)

            #図がページからはみ出す場合は改ページ
            if figure_y < 20*mm:
                pdf_canvas.showPage()
                if marker:
                    self.set_marker(pdf_canvas)
                y = initial_y; figure_y = y - height - 3*mm
                
            figure.embed_to_pdf(pdf_canvas, qnum_width + 11.5*mm, y - height+3*mm)

        y = min(figure_y, y)

        return y, qnum_width

    def write_single_explanation(self, pdf_canvas, i, q, base_font_size, width, y, initial_y, height, figures = None):
        pdf_canvas.setFillColorRGB(0, 0, 0); font_size = base_font_size; pdf_canvas.setFont('Meiryo', font_size)

        qnum_width = pdf_canvas.stringWidth(f"問{i+1}", 'Meiryo', font_size)

        #図の幅を除いた幅を取得
        #print(f"width: {width}, qnum_width: {qnum_width}, 190*mm: {190*mm}")
        text_width = 190*mm - width - 5*mm - qnum_width; y -= font_size*1.618
        
        if y < 20*mm:
            pdf_canvas.showPage()
            y = initial_y; figure_y = y - height
            font_size = base_font_size ; pdf_canvas.setFont('Meiryo', font_size); y -= font_size*1.618

        if q.explanation is not None:
            #問題文を求めた幅毎で改行

            for paragraph in q.explanation:
                j = 0
                text = paragraph
                #print(f"text_width: {text_width} , font_size: {font_size}")

                if i != -1: # 初回の段落のみ：問題番号描画位置がページ跨ぎにならないよう事前確認
                    delta = self.get_row_height(pdf_canvas, text, base_font_size, text_width)
                    if delta:
                        adjustment = max((delta[0] - base_font_size * 1.618) / 2, 0)
                        if y - adjustment - delta[0] < 20 * mm:
                            pdf_canvas.showPage()
                            y = initial_y

                y, first_line_y = self.embed_text(pdf_canvas, text, base_font_size, qnum_width + 10*mm + font_size * 0.5, text_width, y, initial_y, marker=False)

                if i != -1: # 初回の段落のみ問題番号を描画
                    pdf_canvas.setFont('Meiryo', base_font_size)
                    pdf_canvas.drawString(10*mm, first_line_y, f"問{i+1}")
                    i = -1 # 二回目以降は描画しない


        return y

    def write_big_question(self, pdf_canvas, i, q, base_font_size, width, y, initial_y, height, marker, answerbox):
        """図の描画"""
        figure = q.generate_question_figures()
        width = 0; figure_y = y
        
        if figure is None:
            # 断面や棒材の図がある場合は描画
            fig_exist = False
            ##print("make figure")
            if q.cross_section is not None:
                figure = q.cross_section.figure
                fig_exist = True

            elif q.rod is not None:
                ##print("make rod figure")
                figure = q.rod.figure
                fig_exist = True
            
            elif q.truss is not None:
                figure = q.truss.figure
                fig_exist = True
            
            elif q.beam is not None:
                figure = q.beam.figure
                fig_exist = True

            if fig_exist:
                width = figure.width
                height = figure.height

                buf_figure_y = y - height
                figure_y = buf_figure_y

                #図がページからはみ出す場合は改ページ
                if figure_y < 20*mm:
                    ##print(f"figure_y: {figure_y/mm:.1f} mm, です。改ページします。")
                    pdf_canvas.showPage()
                    if marker:
                        self.set_marker(pdf_canvas)
                    y = initial_y; figure_y = y - height
                
                figure.embed_to_pdf(pdf_canvas, 200*mm - width, figure_y)
        
        else:
            figure_y = y
            for fig in figure:
                width = fig.width
                height = fig.height

                buf_figure_y = figure_y - height
                figure_y = min(figure_y, buf_figure_y)

                #図がページからはみ出す場合は改ページ
                if figure_y < 20*mm:
                    pdf_canvas.showPage()
                    if marker:
                        self.set_marker(pdf_canvas)
                    y = initial_y; figure_y = y - height
                
                fig.embed_to_pdf(pdf_canvas, 200*mm - width, figure_y)


        #問題番号の幅を取得
        font_size = base_font_size ; pdf_canvas.setFont('Meiryo', font_size)
        qnum_width = pdf_canvas.stringWidth(f"問{i+1}", 'Meiryo', font_size)

        #幅を取得
        text_width = 190*mm - 5*mm - qnum_width

        """全体概要の描画"""
        #問題文を求めた幅毎で改行
        ##print(q.question[0])
        text = f"{q.question[0]}(seed:{q.id})"

        if i > 0:
            y -= font_size * 1.618 * 0.5
        else:
            y -= font_size * 1.618
        bufy = y
        y, first_line_y = self.embed_text(pdf_canvas, text, base_font_size, qnum_width + 10*mm + font_size * 0.5, text_width - width, y, initial_y, marker)
        
        if y > bufy:
            figure_y = y

        pdf_canvas.setFont('Meiryo', base_font_size)
        pdf_canvas.drawString(10*mm, first_line_y, f"問{i+1}")

        """小問の描画"""
        for sq, sub_question in enumerate(q.question[1:]):
            #y -= font_size*0.218
            if answerbox:
                text = f"{sub_question}"
            else:
                text = f"{sub_question} [{q.answer_unit[sq]}]"
                
            miniqnum_width = pdf_canvas.stringWidth(f"({sq+1})", 'Meiryo', font_size)  + font_size * 0.5
            buf_text_width = text_width - miniqnum_width
            
            if y > figure_y:
                buf_text_width -= width

            bufy = y 
            y, first_line_y = self.embed_text(pdf_canvas, text, base_font_size, qnum_width + miniqnum_width + 10*mm + font_size * 0.5, buf_text_width, y, initial_y, marker)

            if y > bufy: #改ページされた場合
                figure_y = y

            pdf_canvas.setFont('Meiryo', base_font_size)
            pdf_canvas.drawString(qnum_width + 10*mm  + font_size * 0.5, first_line_y, f"({sq+1})")

            # 回答ボックスを描画
            if answerbox:
                answer = Answer(q.id, q.answer_unit[sq])
                figure = answer.figure
                height = figure.height

                ansbox_y = y - height - 1*mm

                #図がページからはみ出す場合は改ページ
                if ansbox_y < 20*mm:
                    pdf_canvas.showPage()
                    if marker:
                        self.set_marker(pdf_canvas)
                    y = initial_y; ansbox_y = y - height - 1*mm; figure_y = initial_y
                    
                figure.embed_to_pdf(pdf_canvas, qnum_width + miniqnum_width + 11.5*mm, y - height + 5*mm)
            else:
                ansbox_y = y

            #print(f"問{i+1}({sq+1}), y: {y/mm:.1f} mm, figure_y: {figure_y/mm:.1f} mm")
            y = min(ansbox_y, y)
        
        y = min(figure_y, y)

        return y, qnum_width

    def write_big_explanation(self, pdf_canvas, i, q, base_font_size, width, y, initial_y, height, figures = None):

        pdf_canvas.setFillColorRGB(0, 0, 0); font_size = base_font_size; pdf_canvas.setFont('Meiryo', font_size)
        qnum_width = pdf_canvas.stringWidth(f"問{i+1}", 'Meiryo', font_size)

        left_figures = len(figures) if figures is not None else 0

        #図の幅を除いた幅を取得
        text_width = 190*mm - width - 5*mm - qnum_width; y -= font_size*1.618

        if y < 20*mm:
            pdf_canvas.showPage()
            y = initial_y; figure_y = y - height
            font_size = base_font_size ; pdf_canvas.setFont('Meiryo', font_size); y -= font_size*1.618

        if q.explanation is not None:
            figure_y = y; fig_width = 0; fig_height = 0

            #問題文を求めた幅毎で改行
            for sq, mini_explanation in enumerate(q.explanation):

                miniqnum_width = pdf_canvas.stringWidth(f"({sq+1})", 'Meiryo', font_size)
                text_width = 190*mm - width - 5*mm - qnum_width - miniqnum_width

                for pk, paragraph in enumerate(mini_explanation):
                    # 図が残っていて，直前の図より下の位置に来たら図を描画
                    if figures is not None and left_figures > 0 and y <= figure_y:
                        figure = figures[ len(figures) - left_figures ]
                        fig_width = figure.width
                        fig_height = figure.height

                        buf_figure_y = y - fig_height - 3*mm
                        figure_y = min(y, buf_figure_y)

                        #図がページからはみ出す場合は改ページ
                        if figure_y < 20*mm:
                            pdf_canvas.showPage()
                            y = initial_y; figure_y = y - fig_height - 3*mm
                            font_size = base_font_size ; pdf_canvas.setFont('Meiryo', font_size); y -= font_size*1.618
                        
                        #print(f"left_figures: {left_figures}, figure_y: {figure_y/mm:.1f} mm, y: {y/mm:.1f} mm")
                        figure.embed_to_pdf(pdf_canvas, 200*mm - fig_width, figure_y + 3*mm)
                        left_figures -= 1
                        
                    # 図が残っておらず，直前の図より下の位置に来たら，図の分の幅を空ける
                    elif figures is not None and left_figures == 0 and y <= figure_y:
                        fig_width = 0

                    text = paragraph
                    if pk == 0:
                        delta = self.get_row_height(pdf_canvas, text, font_size, text_width - fig_width)
                        if delta:
                            adjustment = max((delta[0] - font_size * 1.618) / 2, 0)
                            if y - adjustment - delta[0] < 20 * mm:
                                pdf_canvas.showPage()
                                y = initial_y
                    y, first_line_y = self.embed_text(pdf_canvas, text, base_font_size, qnum_width + miniqnum_width + 10*mm + font_size * 0.5, text_width-fig_width, y, initial_y, marker=False)
                    
                    if pk == 0: # 小問の初回の段落のみ小問番号を描画
                        pdf_canvas.setFont('Meiryo', base_font_size)
                        pdf_canvas.drawString(10*mm+qnum_width, first_line_y, f"({sq+1})")
                        if i != -1: # 全体の初回の段落のみ問題番号を描画
                             pdf_canvas.drawString(10*mm, first_line_y, f"問{i+1}")
                             i = -1

        #大問完了時に改ページ
        pdf_canvas.showPage()
        y = initial_y; figure_y = y - fig_height - 3*mm
        font_size = base_font_size ; pdf_canvas.setFont('Meiryo', font_size); y -= font_size*1.618        
        return y

    def write_explanation(self, pdf_canvas, base_font_size, width, initial_y, height):
        y = initial_y
        #タイトル
        pdf_canvas.setFillColorRGB(0, 0, 0); font_size = base_font_size; pdf_canvas.setFont('Meiryo', font_size); y -= font_size*1.618
        pdf_canvas.drawString(10*mm, y, f"{self._title}　解説") #書き出し(横位置, 縦位置, 文字)
        #水平線を描画
        y -= 1.5*mm; pdf_canvas.setLineWidth(0.75); pdf_canvas.line(10*mm, y, 200*mm, y)
        
        for i, q in enumerate(self._questions):
            print(f"explanation question {i+1}/{len(self._questions)}")
            figures = None
            if q.explanation_figures is not None:
                figures = q.explanation_figures
            
            if issubclass(q.__class__, BigQuestion):
                y = self.write_big_explanation(pdf_canvas, i, q, base_font_size, width, y, initial_y, height, figures)

            elif issubclass(q.__class__, Question):
                y = self.write_single_explanation(pdf_canvas, i, q, base_font_size, width, y, initial_y, height, figures)

    def embed_text(self, pdf_canvas, paragraph, font_size, x_offset, text_width, y, initial_y, marker): #V2
        GAP = 0.5 * mm
        if text_width <= 0:
            raise ValueError(f"Error: text_width must be positive. Given text_width: {text_width}, font_size: {font_size}, text: '{paragraph}'")

        j = 0; eq_ratio = 1; alpha = 1.618
        text = paragraph
        initial_text_width = text_width
        current_text_width = text_width

        delta_y = self.get_row_height(pdf_canvas, text, font_size, text_width, alpha=alpha, eq_ratio=eq_ratio)

        split_texts = text.split('$')
        x = x_offset

        # 1行目が大きい場合のオフセット
        y -= max((delta_y[0] - font_size * 1.618)/2, 0)

        # ページからはみ出す場合は改ページ
        if y < 20*mm:
            pdf_canvas.showPage()
            y = initial_y
            if marker:
                self.set_marker(pdf_canvas)

        first_line_y = y

        for k, split_text in enumerate(split_texts):
            
            if k % 2 == 0:
                while len(split_text) > 0:
                    buftext = split_text
                    
                    while pdf_canvas.stringWidth(buftext, 'Meiryo', font_size) > current_text_width:
                        buftext = buftext[:-1]
                        if len(buftext) == 0: break
                    
                    if len(buftext) == 0:
                        y -= delta_y[j]; j += 1
                        x = x_offset
                        current_text_width = initial_text_width
                        if y < 20*mm:
                            pdf_canvas.showPage()
                            y = initial_y
                            if marker:
                                self.set_marker(pdf_canvas)
                        continue

                    # 追加スペースを計算
                    if len(buftext) > 1 and len(buftext) != len(split_text):
                        space = (current_text_width - pdf_canvas.stringWidth(buftext, 'Meiryo', font_size)) / (len(buftext) - 1)
                    else:
                        space = 0
                    
                    text_obj = pdf_canvas.beginText(x, y)
                    text_obj.setFont('Meiryo', font_size)
                    text_obj.setCharSpace(space)  # 文字間隔を設定
                    text_obj.textLine(buftext)  # テキストを追加
                    pdf_canvas.drawText(text_obj)

                    if len(buftext) != len(split_text):
                        y -= delta_y[j]; j += 1
                        x = x_offset
                        current_text_width = initial_text_width
                        if y < 20*mm:
                            pdf_canvas.showPage()
                            y = initial_y
                            if marker:
                                self.set_marker(pdf_canvas)
                    else:
                        w = pdf_canvas.stringWidth(buftext, 'Meiryo', font_size)
                        x += w + GAP
                        current_text_width -= (w + GAP)

                    split_text = split_text[len(buftext):]

            elif k % 2 == 1:
                eq = Equation (split_text, fontsize=10)
                eq_w = eq.width * eq_ratio
                
                if eq_w > current_text_width:
                    y -= delta_y[j]; j += 1
                    x = x_offset
                    current_text_width = initial_text_width
                    if y < 20*mm:
                        pdf_canvas.showPage()
                        y = initial_y
                        if marker:
                            self.set_marker(pdf_canvas)

                # 数式のベースラインを周囲テキストのベースライン y に合わせる
                # （インライン数式の標準的な揃え方）。
                eq.embed_to_pdf(pdf_canvas, x, y, valign="baseline")
                
                x += eq_w + GAP
                current_text_width -= (eq_w + GAP)

        y -= delta_y[j]; j += 1
        y -= font_size * alpha * 0.5

        return y, first_line_y

    def get_row_height(self, pdf_canvas, text, font_size, text_width, alpha= 1.618, eq_ratio = 1):
        GAP = 0.5 * mm
        split_texts = text.split('$')
        row_height = font_size
        alpha_val = font_size * (alpha-1)
        initial_text_width = text_width
        current_text_width = text_width

        heights = []

        # text_widthが負の場合、無限ループになるので、その場合はエラーを出す
        if text_width <= 0:
            raise ValueError(f"Error: text_width must be positive. Given text_width: {text_width}, font_size: {font_size}, text: '{text}'")

        for k, split_text in enumerate(split_texts):
            
            if k % 2 == 0:
                while len(split_text) > 0:
                    buftext = split_text
                    
                    while pdf_canvas.stringWidth(buftext, 'Meiryo', font_size) > current_text_width:
                        buftext = buftext[:-1]
                        if len(buftext) == 0: break
                        
                    if len(buftext) == 0:
                        heights.append(row_height + alpha_val); row_height = font_size
                        current_text_width = initial_text_width
                        continue

                    if len(buftext) != len(split_text):
                        heights.append(row_height + alpha_val); row_height = font_size
                        current_text_width = initial_text_width
                    else:
                        w = pdf_canvas.stringWidth(buftext, 'Meiryo', font_size)
                        current_text_width -= (w + GAP)

                    split_text = split_text[len(buftext):]

            elif k % 2 == 1:
                eq = Equation (split_text, fontsize=10)
                eq_w = eq.width * eq_ratio
                eq_h = eq.height * eq_ratio

                if eq_w > current_text_width:
                    heights.append(row_height + alpha_val); row_height = font_size
                    current_text_width = initial_text_width
                
                current_text_width -= (eq_w + GAP)
                row_height = max(eq_h, row_height)
        
        heights.append(row_height + alpha_val)

        formatted_heights = []
        for i,h in enumerate(heights):
            default = font_size + alpha_val
            delta_ba = heights[i-1] - default if i != 0 else 0
            delta_cu = heights[ i ] - default
            delta_af = heights[i+1] - default if i != len(heights)-1 else 0

            formatted_heights.append(default + delta_ba * 0.25 + delta_cu * 0.5 + delta_af * 0.25)

        return formatted_heights

    def set_marker(self, pdf_canvas):
        #ホモグラフィ変換用の黒マーカーを4隅に描画
        pdf_canvas.setFillColorRGB(0, 0, 0); pdf_canvas.setLineWidth(0.75)
        for pos in self.marker_positions:
            pdf_canvas.rect(pos[0]*mm, pos[1]*mm, self.marker_size*mm, self.marker_size*mm, fill=1) #書き出し(横位置, 縦位置, 幅, 高さ, 塗りつぶし)

    def _draw_qr(self, pdf_canvas, x, y, size=None):
        """メタデータをQRコードとして埋め込む"""
        if size is None:
            size = 15 * mm
        try:
            import qrcode as qrcode_lib
            from reportlab.lib.utils import ImageReader

            meta = self.metadata
            data_str = f"{meta['class']}:{meta['s']:02d}:{meta['w']:02d}:{meta['d']}:{meta['seed']}:{meta['p']:02d}"

            qr = qrcode_lib.QRCode(version=None, error_correction=qrcode_lib.constants.ERROR_CORRECT_L, box_size=8, border=2)
            qr.add_data(data_str)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")

            buf = io.BytesIO()
            img.save(buf, format='PNG')
            buf.seek(0)

            pdf_canvas.drawImage(ImageReader(buf), x, y, size, size)
            print(f"QR生成: {data_str}")
        except ImportError as e:
            print(f"QR生成スキップ（ライブラリ未インストール）: {e}")
        except Exception as e:
            print(f"QR生成エラー: {e}")

    def export_pdf(self, path, answerbox = True, namebox=True, explanation=True, marker=True, save = True, pdf_canvas=None, append_pdf=None, insert_at_page=-1, external_pdf_start_page=0):

        """
        This method is used to save the sheet as a pdf file.
        """

        initial_y = 289*mm

        if pdf_canvas is None:
            pdf_canvas = canvas.Canvas(f"{path}.pdf") 
            pdf_canvas.setAuthor("Sample Kit")
            pdf_canvas.setTitle(self._title)
            pdf_canvas.setSubject("")
            from reportlab.lib.pagesizes import A4, portrait #用紙の向き
            width, height = A4 
            pdf_canvas.setPageSize(portrait(A4))

        pdfmetrics.registerFont(TTFont('Meiryo', FONT_PATH))
        
        if marker:
            self.set_marker(pdf_canvas)

        y = initial_y

        #タイトルの右側に氏名欄を描画
        if namebox:
            name_box = NameBox(student_number=self.student_number, name=self.student_name)
            figure = name_box.figure
            figure_width = figure.width
            figure_height = figure.height
            y = initial_y - figure_height - 5*mm
            figure_x = 200*mm - figure_width
            figure.embed_to_pdf(pdf_canvas, figure_x, y)
            if self.metadata is not None:
                qr_size = 15 * mm
                self._draw_qr(pdf_canvas, figure_x - qr_size - 2*mm, y, qr_size)
            y += 7*mm
        else:
            if self.metadata is not None:
                self._draw_qr(pdf_canvas, 14*mm, 10*mm)

        base_font_size = 4*mm

        #タイトル
        pdf_canvas.setFillColorRGB(0, 0, 0); font_size = base_font_size; pdf_canvas.setFont('Meiryo', font_size); y -= font_size*1.618
        ##print(self._title)
        pdf_canvas.drawString(10*mm, y, self._title) #書き出し(横位置, 縦位置, 文字)

        #水平線を描画
        y -= 1.5*mm; pdf_canvas.setLineWidth(0.75); pdf_canvas.line(10*mm, y, 200*mm, y)

        initial_y = 284*mm

        for i, q in enumerate(self._questions):
            ##print(q.__class__.__name__)
            genq = q.generate_question()
            ##print("generate_question:", genq)
            figure_y = y; height = 0; width = 0

            if issubclass(q.__class__, BigQuestion):
                y, qnum_width = self.write_big_question(pdf_canvas, i, q, base_font_size, width, y, initial_y, height, marker, answerbox)

            elif issubclass(q.__class__, Question):
                y, qnum_width = self.write_single_question(pdf_canvas, i, q, base_font_size, width, y, figure_y, initial_y, height, marker, answerbox)
                ##print("BigQuestion")
                ##print(q.__class__.__bases__)

        ## 改ページ
        pdf_canvas.showPage()
        width = 0; height = 0
        if explanation:
               
            self.write_explanation(pdf_canvas, base_font_size, width, initial_y, height)

        
        if save:
            self.pdf_save_with_compression(pdf_canvas, path, append_pdf=append_pdf, insert_at_page=insert_at_page, external_pdf_start_page=external_pdf_start_page)
            #pdf_canvas.save()
        
        return pdf_canvas

    def export_explanation_pdf(self, path):
        """
        解説のみをPDFとして出力する。
        """
        initial_y = 284*mm
        base_font_size = 4*mm

        pdf_canvas = canvas.Canvas(f"{path}.pdf")
        pdf_canvas.setAuthor("Sample Kit")
        pdf_canvas.setTitle(f"{self._title} 解説")

        from reportlab.lib.pagesizes import A4, portrait
        pdf_canvas.setPageSize(portrait(A4))

        pdfmetrics.registerFont(TTFont('Meiryo', FONT_PATH))

        width = 0; height = 0
        self.write_explanation(pdf_canvas, base_font_size, width, initial_y, height)

        self.pdf_save_with_compression(pdf_canvas, path)

    def export_return_pdf(self, path, explanation=True, explanation_pdf=None):
        """
        This method is used to save the sheet as a pdf file.
        """

        initial_y = 284*mm
        base_font_size = 4*mm

        pdf_canvas = canvas.Canvas(f"{path}.pdf")
        pdf_canvas.setAuthor("Sample Kit")
        pdf_canvas.setTitle(self._title)
        pdf_canvas.setSubject("")

        pdfmetrics.registerFont(TTFont('Meiryo', FONT_PATH))

        from reportlab.lib.pagesizes import A4, portrait #用紙の向き
        width, height = A4
        pdf_canvas.setPageSize(portrait(A4))

        for i, s in enumerate(self.sheet):
            #self.sheet.img を配置
            import PIL
            img_rgb = cv2.cvtColor(s.img, cv2.COLOR_BGR2RGB)
            pil_image = PIL.Image.fromarray(img_rgb)
            img_buffer = io.BytesIO()
            pil_image.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            from reportlab.lib.utils import ImageReader
            image_reader = ImageReader(img_buffer)
            pdf_canvas.drawImage(image_reader, 0, 0, width=width, height=height, mask='auto')

            ## 改ページ
            pdf_canvas.showPage()

        if explanation and explanation_pdf is None:
            width = 0; height = 0
            #print("write explanation")
            #print(f"width: {width} mm, height: {height} mm")
            self.write_explanation(pdf_canvas, base_font_size, width, initial_y, height)

        #pdf_canvas.save()
        self.pdf_save_with_compression(pdf_canvas, path, append_pdf=explanation_pdf)
    def pdf_save_with_compression(self, pdf_canvas, path, append_pdf=None, insert_at_page=-1, external_pdf_start_page=0):
        """
        PDFファイルの圧縮
        """

        # 1. メモリ上のio.BytesIOにPDFデータを書き出す
        pdf_data_bytes = pdf_canvas.getpdfdata()

        # 1.5 結合が必要な場合は結合
        if append_pdf is not None:
            if os.path.exists(append_pdf):
                from pypdf import PdfWriter, PdfReader
                writer = PdfWriter()
                
                # 元のPDFを読み込む
                original_reader = PdfReader(io.BytesIO(pdf_data_bytes))
                num_original_pages = len(original_reader.pages)
                
                # 挿入位置の決定（負の場合は末尾）
                pos = insert_at_page
                if pos < 0 or pos > num_original_pages:
                    pos = num_original_pages
                
                # 挿入位置までのページを追加
                for i in range(pos):
                    writer.add_page(original_reader.pages[i])
                
                # 差し込みファイルを読み込んで追加
                append_reader = PdfReader(append_pdf)
                for i in range(external_pdf_start_page, len(append_reader.pages)):
                    writer.add_page(append_reader.pages[i])
                
                # 残りのページを追加
                for i in range(pos, num_original_pages):
                    writer.add_page(original_reader.pages[i])
                
                output_stream = io.BytesIO()
                writer.write(output_stream)
                pdf_data_bytes = output_stream.getvalue()
                writer.close()
            else:
                print(f"Warning: append_pdf file not found: {append_pdf}")
        
        # 2. Ghostscript (subprocess) を呼び出して圧縮する
        try:
            import subprocess
            
            # Ghostscriptのコマンド (gsのパスは環境に合わせて調整が必要)
            # Windowsの場合: 'gswin64c' など
            # Linux/macOSの場合: 'gs'
            gs_command = [
                'gswin64c.exe',  
                '-sDEVICE=pdfwrite',
                '-dCompatibilityLevel=1.4',
                
                # --- 【変更点】ここから本気の圧縮設定 ---
                
                # プリセットを /screen (72dpi相当) に変更
                # ※ これで画質が粗すぎる場合は /ebook に戻して下のResolution数値を調整してください
                '-dPDFSETTINGS=/screen', 
                
                # 画像の解像度を強制的に下げる (72〜96dpi推奨)
                '-dDownsampleColorImages=true',
                '-dColorImageResolution=150', 
                '-dDownsampleGrayImages=true',
                '-dGrayImageResolution=150',
                '-dDownsampleMonoImages=true',
                '-dMonoImageResolution=150',

                # テキストとラインアートの圧縮を有効化
                '-dCompressFonts=true',
                '-dSubsetFonts=true',
                '-dDetectDuplicateImages=true', # 重複画像を統合
                
                # --- ここまで ---

                '-dNumRenderingThreads=4',
                '-dDoThumbnails=false',
                '-dCompressEntireFile=true',
                '-dCompressEntireFile=true',
                '-dFloatResolution=2',
                '-dMaxSubsetPct=100',
                '-dSubsetFonts=true',
                '-dSimplifyClippingPaths=true',
                '-dNOPAUSE',
                '-dQUIET',
                '-dBATCH',
                '-sOutputFile=' + f"{path}.pdf", 
                '-' 
            ]


            # subprocessを実行し、メモリ上のPDFデータを標準入力として渡す
            process = subprocess.run(
                gs_command,
                input=pdf_data_bytes,
                check=True,
                capture_output=True,
                # shell=True # Windowsでパスが通っていない場合などに必要になるかも
            )
            
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            # Ghostscriptが失敗したか、インストールされていない場合
            print(f"Ghostscriptでの圧縮に失敗しました ({e})。")
            print("https://ghostscript.com/からインストールしてないかもです。")
            print(f'gswin64cコマンドが実行できるようにしてください。')
            print("フォールバックとして、未圧縮のPDFを保存します。")
            # 失敗した場合は、圧縮前のデータをそのまま保存する
            with open(f"{path}.pdf", "wb") as f:
                f.write(pdf_data_bytes)
        

    """
    この辺までpdf出力用
    この辺から画像読み込み・解析用
    """

    def read(self):
        """
        画像を読み込む
        """
        # パスがリストかどうかを確認
        if isinstance(self.path, list) is False:
            self.path = [self.path]
        self.sheet = []
        for p in self.path:
            if self.monitor is True:
               print("open", p)
            self.sheet.append(Image(p))
        
        if self.monitor is True:
            for i, s in enumerate(self.sheet):
                print(f"read image shape {i}:", s.img.shape)
                #s.show(f"raw{i}")

    def read_qr(self):
        """スキャン画像からQRコードを読み取り、メタデータdictを返す。見つからない場合はNoneを返す。

        cv2.wechat_qrcode_WeChatQRCode を使用する（cv2.QRCodeDetector より高速かつ高精度）。
        WeChatQRCode が使えない環境では cv2.QRCodeDetector にフォールバックする。
        """
        def _parse_text(text):
            if not text:
                return None
            try:
                parts = text.split(":")
                if len(parts) == 6:
                    return {
                        "class": parts[0],
                        "s": int(parts[1]),
                        "w": int(parts[2]),
                        "d": int(parts[3]),
                        "seed": int(parts[4]),
                        "p": int(parts[5])
                    }
            except (ValueError, IndexError):
                pass
            return None

        try:
            wechat = cv2.wechat_qrcode_WeChatQRCode()
        except Exception:
            wechat = None

        for s in self.sheet:
            if wechat is not None:
                try:
                    texts, _ = wechat.detectAndDecode(s.img)
                    for text in texts:
                        result = _parse_text(text)
                        if result:
                            return result
                    continue  # wechat が使えるなら fallback 不要
                except Exception:
                    pass
            # WeChatQRCode が使えない環境向けフォールバック
            _, decoded_info, _, _ = cv2.QRCodeDetector().detectAndDecodeMulti(s.img)
            for text in decoded_info:
                result = _parse_text(text)
                if result:
                    return result
        return None

    def get_reference_grids(self, size_min = 0.8, size_max = 1.2, black = 100):
        """
        基準の黒塗り位置を検出
        """
        results = []
        for i, s in enumerate(self.sheet):
            # 画像のサイズを設定
            height = s.img.shape[0]
            width = s.img.shape[1]

            # マーク１ブロックのサイズ
            req_height = self.marker_size / self.sheet_size[1] * height
            req_width = self.marker_size / self.sheet_size[0] * width

            image =  s.img[:,:,0]

            # 二値化
            _, binary = cv2.threshold(image, black, 255, cv2.THRESH_BINARY_INV)

            # 輪郭を検出
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # 検出された長方形のリスト
            rectangles = []

            # 長方形を検出して描画
            for contour in contours:
                # 輪郭の外接矩形を取得
                x, y, w, h = cv2.boundingRect(contour)

                if w > req_width*size_min and h > req_height*size_min and w < req_width*size_max and h < req_height*size_max:
                    rectangles.append((x, y, w, h))

            # 長方形同士の間隔の制限を設定
            min_distance = np.average(np.array(rectangles)[:,2:])*0.9  # 最小間隔

            # フィルタリングされた長方形のリスト
            filtered_rectangles = []

            # 長方形同士の間隔をフィルタリング
            for rect in rectangles:
                x, y, w, h = rect
                too_close = False
                for filtered_rect in filtered_rectangles:
                    fx, fy , _fw, _fh= filtered_rect
                    # 距離を計算
                    distance = np.sqrt((x - fx)**2 + (y - fy)**2)
                    if distance < min_distance:
                        too_close = True
                        break
                if not too_close:
                    filtered_rectangles.append(rect)

            # 長方形の中身が黒いもののみをフィルタリング
            rectangles = np.array(filtered_rectangles)
            filtered_rectangles = []

            for i, rect in enumerate(rectangles):
                x, y, w, h = rect
                #長方形部分をトリミング
                roi = binary[y:y + h, x:x + w]
                #輝度平均を計算
                mean_val = np.mean(roi)
                ##print("mean_val:", mean_val,i)

                
                if mean_val > 200:
                    filtered_rectangles.append(rect)

            result = np.float32(filtered_rectangles)
            ##print("result shape:", result.shape)
            result = result[:,:-2]
            results.append(result)

            if self.monitor is True:
                # デバッグ表示用に検出枠を複製画像へ描画する（s.img を直接描画すると，
                # aliment() が上下逆判定後に本メソッドを再度呼ぶ際，前回の描画が
                # 検出結果を壊すため，s.img 自体は書き換えない）
                debug_img = s.img.copy()
                for rect in filtered_rectangles:
                    x, y, w, h = rect
                    cv2.rectangle(debug_img, (x, y), (x + w, y + h), (0, 255, 0), 2)
                #print("get reference grid:", results[-1])
                #Image(img=debug_img).show(f"rect")
                #cv2.imshow(f"rect_binary", binary)
                if len(filtered_rectangles) != len(self.marker_positions):
                   print("reference gridnumber is not much:", len(filtered_rectangles))
            
        return results

    def marker_normalize(self):
       ##print("marker_normalize")
        if np.max(np.array(self.marker_positions)) > 1.0:
            #マーカー位置の正規化
            ##print("marker_positions:", self.marker_positions)
            markp = np.array(self.marker_positions, dtype=np.float32)
            ##print("markp:", markp)
            markp[:,1] = self.sheet_size[1] - markp[:,1]
            ##print("markp:", markp)
            maxx = np.max(markp[:,0]) + self.marker_size
            maxy = np.max(markp[:,1]) + self.marker_size
            minx = np.min(markp[:,0]); miny = np.min(markp[:,1])
            ##print("maxx, maxy, minx, miny:", maxx, maxy, minx, miny)
            markp[:,0] -= minx
            markp[:,1] -= miny 
            ##print("markp:", markp)
            markp[:,0] = markp[:,0] / (maxx - minx)
            markp[:,1] = markp[:,1] / (maxy - miny)
            ##print("markp:", markp)
            self.marker_positions = markp

            # マーク１ブロックのサイズ
            self.req_width = self.marker_size / (maxx - minx)
            self.req_height = self.marker_size / (maxy - miny)    
            ##print("req_width, req_height:", self.req_width, self.req_height)

    def make_reference(self):
        """
        基準の黒塗り位置を塗りつぶした画像を作成
        """
        images = []
        for i, s in enumerate(self.sheet):

            # 画像のサイズを設定
            height = s.img.shape[0]
            width = s.img.shape[1]

            self.marker_normalize()
            markp = np.array(self.marker_positions)
            req_height = self.req_height
            req_width = self.req_width

            # 白い画像を作成
            image = np.ones((int(height), 
                            int(width)),
                            dtype=np.uint8) * 255

            # 指定された位置に黒い正方形を描画
            for p in markp:
                top_left = ( int(p[0]*width), 
                                int(p[1]*height) )
                
                bottom_right = (int((p[0] + req_width)*width),
                                int((p[1] + req_height)*height))
                
                cv2.rectangle(image, top_left, bottom_right, (0, 0, 0), -1)

            images.append(Image(img=image))

        if self.monitor is True:
            print("make reference image shape:", images[-1].img.shape, "reqtangle h,w:", req_height, req_width)
            #images[-1].show(f"reference{i}")

        return images

    def rotation(self):
        """
        用紙の向き（水平or垂直）を補正する。
        """
        for i, s in enumerate(self.sheet):
            height = s.img.shape[0]
            width = s.img.shape[1]

            if (self.direction == "horizontal") and (width < height):
                s.img = cv2.rotate(s.img, cv2.ROTATE_90_CLOCKWISE)
                if self.monitor is True:
                   print(f"rotated to horizontal")

            if (self.direction == "vertical") and (height < width):
                s.img = cv2.rotate(s.img, cv2.ROTATE_90_CLOCKWISE)
                if self.monitor is True:
                   print(f"rotated to vertical")


            if self.monitor is True:
                print("rotation complete")
                #s.show(f"rotation{i}")        

    def rotation_aliment(self):
        """
        用紙の上下を基準パターンに合わせ補正する。
        安定動作せず。
        """
        # 方向判定（上下）
        best_match = 1e100
        
        references = self.make_reference()

        for i, s in enumerate(self.sheet):
            for j in range(2):
                reference =  references[i].img
                result_img = s.img[int(s.img.shape[0]*0.9):,:,0] - reference[int(s.img.shape[0]*0.9):,:]

                #cv2.imshow("result_img", result_img)
                #cv2.imshow("reference", reference)
                #cv2.imshow("sheet", s.img)
                #cv2.waitKey(0)
                
                min_val = np.abs(np.sum(result_img))
                ##print(i, max_val)
                if min_val < best_match:
                    best_match = min_val
                    best_rotation = j

                #回転してもう一度確認
                reference = cv2.rotate(reference, cv2.ROTATE_180)
                
                if self.monitor is True:
                   print(f"rotation: {j}, min_val: {min_val}")

            # 結果をもとに回転
            if self.monitor is True:
                print(f"best_rotation: {best_rotation}")

            if best_rotation == 1:
                #上手く判定できない場合があるので，180度回転はしない
                s.img = cv2.rotate(s.img, cv2.ROTATE_180)
                pass

            if self.monitor is True:
                print("rotation complete")
                #s.show(f"rotation2 {i}")

    def _is_upside_down(self, src_points, width, height):
        """
        検出されたマーカー座標と期待されるマーカー配置を比較して，
        用紙が上下逆かどうかを判定する。
        marker_normalize() の副作用（self.marker_positions の正規化）を利用するため，
        aliment() 内で呼び出すことで以降の buf 計算も正規化済み値で動く。
        """
        self.marker_normalize()
        expected = np.array(self.marker_positions, dtype=np.float32)  # (N,2) x_norm,y_norm

        src_n = src_points.copy().astype(np.float32)
        rng = src_n.max(axis=0) - src_n.min(axis=0)
        rng[rng == 0] = 1  # ゼロ除算防止
        src_n = (src_n - src_n.min(axis=0)) / rng

        def nn_error(pts):
            total = 0.0
            for p in pts:
                dists = np.sum((expected - p) ** 2, axis=1)
                total += dists.min()
            return total

        err_normal  = nn_error(src_n)
        err_flipped = nn_error(1.0 - src_n)  # 180度回転した場合
        return err_flipped < err_normal

    def aliment(self, black = 100):
        """
        基準の四角形を参照して，ひずみ補正を行う。
        """

        if self.monitor is True:
            print("aliment start")

        src_points_list = self.get_reference_grids()

        # 上下逆判定：マーカーの座標パターンで判定し，必要なら180度回転
        rotated = False
        for i, s in enumerate(self.sheet):
            if self._is_upside_down(src_points_list[i], s.img.shape[1], s.img.shape[0]):
                s.img = cv2.rotate(s.img, cv2.ROTATE_180)
                rotated = True
                if self.monitor is True:
                    print(f"sheet {i}: 上下逆を検出 → 180度回転")
        if rotated:
            src_points_list = self.get_reference_grids()

        for i, s in enumerate(self.sheet):
            image = s.img

            height = s.img.shape[0]
            width = s.img.shape[1]

            # 台形補正
            # 変換前の座標を指定（例: 四角形の頂点）
            src_points = src_points_list[i]

            # 取得した基準座標に合わせてトリミング
            req_height = self.marker_size / self.sheet_size[1] * height
            req_width = self.marker_size / self.sheet_size[0] * width

            s.img = s.img[int(np.min(src_points[:,1])) : ,
                                            int(np.min(src_points[:,0])) : , :]
            s.img = s.img[ : int(np.max(src_points[:,1]) - np.min(src_points[:,1])+req_height),
                                            : int(np.max(src_points[:,0]) - np.min(src_points[:,0])+req_width), :]

            #サイズを元に戻す
            s.img = cv2.resize(s.img,(width, height))

            if self.monitor is True:
               ##print(int(np.min(src_points[:,1])),int(np.max(src_points[:,1])))
               ##print(int(np.min(src_points[:,0])),int(np.max(src_points[:,0])))
                s.show("trim")

            # 再度座標を取得
            src_points[:,1] -= np.min(src_points[:,1])
            src_points[:,0] -= np.min(src_points[:,0])

            # 変換後の座標を指定（例: 台形の頂点）
            ##print("marker_positions:", self.marker_positions)
            buf = np.array(self.marker_positions)[:, [1, 0]]
            buf = buf * [width, height]
            ##print(buf)

            # 拡大
            src_points[:,0] = src_points[:,0] / np.average(src_points[:,0])  * np.average(buf[:,0])
            src_points[:,1] = src_points[:,1] / np.average(src_points[:,1])  * np.average(buf[:,1])

            dst_points = []

            # 最も近い点の組み合わせをリストアップしたい（現状は余白幅に未対応）
            for point in np.array(src_points):
                index = np.argmin((point[0] - buf[:,0])**2 + (point[1] - buf[:,1])**2)
                dst_points.append(buf[index])

            dst_points = np.array(dst_points)

            if self.monitor is True:
               print("dst_points:",dst_points)

            # 透視変換行列を計算
            ##print("s",src_points, "d", dst_points)
            H, status = cv2.findHomography(src_points, dst_points)
            ##print("H:", H)
            # 画像を透視変換
            s.img = cv2.warpPerspective(s.img, H, (width, height), borderValue=(255, 255, 255))

            if self.monitor is True:
               ##print("aliment complete")
                #s.show(f"aliment{i}")
                #ret, img_thresh = cv2.threshold(s.img[:,:,0], black, 255, cv2.THRESH_BINARY)
                #image = Image(img=img_thresh)
                #image.show(f"aliment except b{i}")
                pass

    def get_answerimg(self, namebox: bool = False):
        self.answer_squares = []; self.answer_imgs = []; squares = []
        #print(self.sheet)

        for i, s in enumerate(self.sheet):

            img = cv2.cvtColor(s.img, cv2.COLOR_BGR2GRAY)

            squares += self.detect_squares(img, i, min_size_ratiotowidth=0.03, max_size_ratiotowidth=0.10, allow_different_size_ratio=0.1)
            #print(f"detect squares in sheet {i}: {len(squares)}")

        ##print(len(squares))
        #yに対してソート
        squares = sorted(squares, key=lambda x: x[2])
        #snumに対してソート
        squares = sorted(squares, key=lambda x: x[0])
        
        buf = [squares[0:2]]
        squares = squares[2:]

        #6つずつに分割
        length_of_miniquestions = sum([len(q.answer) if issubclass(q.__class__, BigQuestion) else 1 for q in self._questions])
        #print("length_of_miniquestions:", length_of_miniquestions, "len(squares):", len(squares))

        squares = buf + [squares[i:i+6] for i in range(0, len(squares), 6)]

        #xに対してソート
        squares = [sorted(square, key=lambda x: x[1]) for square in squares]

        ##print("squares:", squares)
        # 整頓した正方形のリストを保存
        self.answer_squares += squares

        # 白黒反転

        for i, s  in enumerate(self.sheet):
            nega = 255 - s.img

            for k, sq in enumerate(squares):

                a = 7; ss = []
                for j, (snum, x, y, w, h) in enumerate(sq):
                    
                    if i == snum:
                        ss.append(cv2.resize(nega[y:y+h, x:x+h][a:-a,a:-a].copy(), (64, 63)))
                        
                        #cv2.putText(s.img, f"{i+1}-{j+1}", (x-20, y-20), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 4, cv2.LINE_AA)                    
                        if j == 0:
                            cv2.rectangle(s.img, (x, y), (x+w, y+h), (0, 0, 255), 4)
                        else:
                            cv2.rectangle(s.img, (x, y), (x+w, y+h), (0, 0, 255), 2)
                        

                #該当箇所をトリム
                if len(ss) > 0:
                    self.answer_imgs.append(ss)

        if self.monitor is True:
            s.show(f"squares{i}")
    

    def prediction(self, data, model_instances, device):
        """
        予測を行う
        """
        predictions = []
        #print("model_instances:", len(model_instances))
        for model_instance in model_instances:
            model_instance.to(device)
            model_instance.eval()
            with torch.no_grad():
                output = model_instance(data)
                predictions.append(output.argmax(1).item())

        predictions = torch.tensor(predictions)
        #ユニークな値を取得
        unique = predictions.unique()
        #print(unique)

        #各値の出現回数をカウント
        counts = torch.bincount(predictions, minlength=11)

        return int(counts.argmax().item()), counts


    def get_answers_and_predict(self, plusminus_model_instances, number_model_instances, device, result_dir="./files/result/"):
        """
        初回採点時の予測を行う関数
        """
        if self.answer_imgs is None:
            self.get_answerimg()

        answers = []
        pred = []

        # 出席番号の取得'
        for j, img in enumerate(self.answer_imgs[0]):
            ##print("img shape:", img.shape)
            norm_img = self.image_preprocess(img).to(device)

            if self.monitor:
                cv2.imshow("norm_img", norm_img[0][0].cpu().numpy())
                cv2.waitKey(1)

            pred.append(self.prediction(norm_img, number_model_instances, device))
            mode = "number"

            instance = Image(img=img)
            #fの長さを取得
            try:
                flen = len(open(f"{result_dir}/predictions.csv", "r", encoding="utf-8-sig").readlines())
                if flen == 0:
                    raise ValueError("flen is 0")
            except:
                flen = 1
                #reslt_dirが存在しない場合は作成
                if not os.path.exists(result_dir):
                    os.makedirs(result_dir)
                with open(f"{result_dir}/predictions.csv", "a", encoding="utf-8-sig") as f:
                    f.write(f"ID,Source_path,Sheet_number,Question_Number,Answer_Number,Image_Index,x,y,w,h,Predict_Mode,Votes_for_0,Votes_for_1,Votes_for_2,Votes_for_3,Votes_for_4,Votes_for_5,Votes_for_6,Votes_for_7,Votes_for_8,Votes_for_9,Votes_for_10,Predicted,Corrected\n")

            instance.save(f"{result_dir}/image/raw/{flen}")

            snum, x, y, w, h = self.answer_squares[0][j]

            #fに追記
            with open(f"{result_dir}/predictions.csv", "a", encoding="utf-8-sig") as f:
                f.write(f"{flen},{os.path.basename(self.path[snum])},{snum},0,0,{j},{x},{y},{w},{h},{mode},{', '.join([str(int(p.item())) for p in pred[-1][1]])},{pred[-1][0]},{pred[-1][0]}\n")
        

        # 各質問の回答の取得 
        i = 1
        for q_index, q in enumerate(self.questions):

            if issubclass(q.__class__, BigQuestion) is False:
                answer  = [q.answer]
                q.score = 0
            else:
                answer = q.answer
                q.score = [0] * len(answer)

            for anum, a in enumerate(answer):

                #print(q.answer, "anum:", anum)
                answer_img = self.answer_imgs[i]
                pred = []

                split_position = 4

                texts = ""               
                for j, img in enumerate(answer_img):
                    ##print("img shape:", img.shape)
                    norm_img = self.image_preprocess(img).to(device)

                    if self.monitor:
                        cv2.imshow("norm_img", norm_img[0][0].cpu().numpy())
                        cv2.waitKey(1)


                    with torch.no_grad():
                        if j % split_position == 0:
                            pred.append(self.prediction(norm_img, plusminus_model_instances, device))
                            mode = "plusminus"


                        if j % split_position >= 1:
                            ##print(number_model_instance(norm_img))
                            pred.append(self.prediction(norm_img, number_model_instances, device))
                            mode = "number"

                    instance = Image(img=img)
                    flen = len(open(f"{result_dir}/predictions.csv", "r", encoding="utf-8-sig").readlines())
                    instance.save(f"{result_dir}/image/raw/{flen}")
                    
                    snum, x, y, w, h = self.answer_squares[i][j]
                    
                    flen = len(open(f"{result_dir}/predictions.csv", "r", encoding="utf-8-sig").readlines())
                    with open(f"{result_dir}/predictions.csv", "a", encoding="utf-8-sig") as f:
                        f.write(f"{flen},{os.path.basename(self.path[snum])},{snum},{q_index+1},{anum+1},{j},{x},{y},{w},{h},{mode},{', '.join([str(int(p.item())) for p in pred[-1][1]])},{pred[-1][0]},{pred[-1][0]}\n")

                answers.append(pred)
                i += 1
                
        self.raw_answers = answers


        if self.monitor is True:
            for i, s in enumerate(self.sheet):
                s.show(f"answers {i}")

    def get_format_answers(self, plusminus_model_instances, number_model_instances, device, result_dir="./files/result/"):
        """
        予測結果をもとに，解答の形式を整えて，得点を計算する関数
        """
        # format_answersとanswersを作成
        # csvから
        df = []
        for path in self.path:
            #print("terget path:", path)
            try:
                buf = pd.read_csv(f"{result_dir}/predictions.csv", encoding="utf-8-sig")
                #print(buf)
                # ファイル名のみを取り出して比較（端末間のルートパスの違いを無視）
                buf = buf[buf["Source_path"].apply(lambda x: os.path.basename(str(x)).lower()) == os.path.basename(path).lower()]
                count = len(buf)
                #print(f"read {count} predictions from {result_dir}/predictions.csv for path {path}")
                df.append(buf)
            except:
                count = 0

            if count == 0:
                self.get_answers_and_predict(plusminus_model_instances, number_model_instances, device, result_dir=result_dir)
                buf = pd.read_csv(f"{result_dir}/predictions.csv", encoding="utf-8-sig")
                #print(buf)
                # ここでもファイル名で比較
                buf = buf[buf["Source_path"].apply(lambda x: os.path.basename(str(x)).lower()) == os.path.basename(path).lower()]
                count = len(buf)
                #print(f"read {count} predictions from {result_dir}/predictions.csv for path {path}")
                df.append(buf)

        df = pd.concat(df)

        format_answers = []
        
        texts = ""
        pred = []
        # 出席番号の取得'
        for d in range(2):

            #textに予測結果を追加
            ddf = df[(df["Question_Number"] == 0) & (df["Answer_Number"] == 0) & (df["Image_Index"] == d) & (df["Predict_Mode"] == "number")]
            text = str(ddf["Corrected"].values[0])

            if text == "10":
                text = "0"

            snum, x, y, w, h = int(ddf["Sheet_number"].values[0]), int(ddf["x"].values[0]), int(ddf["y"].values[0]), int(ddf["w"].values[0]), int(ddf["h"].values[0])

            cv2.putText(self.sheet[snum].img, text, (x+w-10, y+h+30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 4, cv2.LINE_AA)

            texts += text

        if "blank" not in texts:
            self.student_number = int(texts)
        else:
            self.student_number = 99
        

        ##print(len(self.answer_imgs[1:]))

        for qnum, q in enumerate(self.questions):

            if issubclass(q.__class__, BigQuestion) is False:
                answer  = [q.answer]
                q.score = 0
            else:
                answer = q.answer
                q.score = [0] * len(answer)

            for anum, a in enumerate(answer):
                if type(a) == list:
                    a = a[0]

                split_position = 4

                texts = ""               
                for j in range(6):

                    with torch.no_grad():
                        if j % split_position == 0:
                            preddf = df[(df["Question_Number"] == qnum+1) & (df["Answer_Number"] == anum+1) & (df["Image_Index"] == j) & (df["Predict_Mode"] == "plusminus")]
                            pred.append(preddf["Corrected"].values[0])
                            
                            if pred[-1] == 0:
                                text = "+"
                            elif pred[-1] == 1:
                                text = "-"
                            else:
                                text = "+"

                        if j % split_position >= 1:
                            ##print(number_model_instance(norm_img))
                            preddf = df[(df["Question_Number"] == qnum+1) & (df["Answer_Number"] == anum+1) & (df["Image_Index"] == j) & (df["Predict_Mode"] == "number")]
                            pred.append(preddf["Corrected"].values[0])

                            if pred[-1] == 10:  # 空欄の場合
                                if (split_position==2 and j == 3) or (split_position==4 and j == 5):
                                    text = "1"
                                elif split_position==4 and (j == 2 or j == 3):
                                    text = "0"
                                else:
                                    text = "blank"
                            else:
                                text = f"{pred[-1]}"
                        


                    if split_position == 4 and j==2:
                        texts += "."
                        
                    if j == split_position:
                        texts += "E"

                    texts += text
                    
                    snum, x, y, w, h = int(preddf["Sheet_number"].values[0]), int(preddf["x"].values[0]), int(preddf["y"].values[0]), int(preddf["w"].values[0]), int(preddf["h"].values[0])
                    
                    cv2.putText(self.sheet[snum].img, text, (x+w-10, y+h+30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 4, cv2.LINE_AA)

                
                if "blank" not in texts:
                    format_answers.append(float(texts))
                    cv2.putText(self.sheet[snum].img, f"Your answer:{texts}", (x+w+100, y+h-30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 4, cv2.LINE_AA)

                    #質問のスコアを計算
                    if issubclass(q.__class__, BigQuestion):
                        q.scoring(format_answers[-1], 100 / (len(self.answer_imgs)-1), anum)
                        cv2.putText(self.sheet[snum].img, f"Your score:{q.score[anum]:.2f}", (x+w+100, y+h+70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 4, cv2.LINE_AA)
                    elif issubclass(q.__class__, Question):
                        q.scoring(format_answers[-1], 100 / (len(self.answer_imgs)-1))
                        cv2.putText(self.sheet[snum].img, f"Your score:{q.score:.1f}", (x+w+100, y+h+70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 4, cv2.LINE_AA)
                    
                    #print(f"correct answer: {a}, your answer: {format_answers[-1]}, score: {q.score[anum] if issubclass(q.__class__, BigQuestion) else q.score}")
                    cv2.putText(self.sheet[snum].img, f"Correct answer:{a:.1E}", (x+w+100, y+h+20), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 4, cv2.LINE_AA)

                else:
                    if issubclass(q.__class__, BigQuestion):
                        q.score[anum] = 0
                    elif issubclass(q.__class__, Question):
                        q.score = 0

            
        self.format_answers = format_answers
        self.scoring()
        cv2.putText(self.sheet[0].img, f"{self.score}", (700, 100), cv2.FONT_HERSHEY_SIMPLEX, 3, (0, 0, 255), 5, cv2.LINE_AA)

        if self.monitor is True:
        ##print("answers:", answers)
            for i, s in enumerate(self.sheet):
                s.show(f"answers {i}")


    def scoring(self): 
        """
        得点を計算する。
        """
        
        score = 0
        ##print("self.student_num:",self.student_number)

        for quesion in self.questions:
            if issubclass(quesion.__class__, BigQuestion):
                ##print("quesion.score:", quesion.score)
                score += sum(quesion.score)

            elif issubclass(quesion.__class__, Question):
                ##print("quesion.score:", quesion.score)
                score += quesion.score

        ##print("score:", score)
        self.score = int(score)

    def detect_squares(self, img, sheetnum, min_size_ratiotowidth, max_size_ratiotowidth, allow_different_size_ratio):

        bold = 1
        while True:

            width = img.shape[1]; height = img.shape[0]

            min_size = int(width * min_size_ratiotowidth)
            max_size = int(width * max_size_ratiotowidth)

            # 2値化
            _, img_bin = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU)
            #cv2.imshow("img_bin_raw", img_bin)
            #cv2.waitKey(1)

            # モルフォロジー変換で縦線を強調
            kernel = np.ones((50,bold), np.uint8)
            for i in range(1):
                img_v = cv2.erode(img_bin, kernel, iterations=1)
                img_v = cv2.dilate(img_v, kernel, iterations=1)

            # モルフォロジー変換で横線を強調
            kernel = np.ones((bold,50), np.uint8)
            for i in range(1):
                img_h = cv2.erode(img_bin, kernel, iterations=1)
                img_h = cv2.dilate(img_h, kernel, iterations=1)

            #強調結果を合成
            img_bin = cv2.bitwise_or(img_v, img_h)

            if self.monitor:
                buf = cv2.resize(img_bin, (int(width*0.5), int(height*0.5)))
                cv2.imshow("img_bin", buf)
                cv2.waitKey(1)

            # 輪郭を検出
            contours, _ = cv2.findContours(img_bin, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # 大きさがmin_size以上の正方形を抽出
            squares = []

            ##print("contours:", len(contours))

            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)

                #print("x,y,w,h:", x, y, w, h)
                #print("min_size, max_size:", min_size, max_size)
                #print("w-h/w, allow_different_size_ratio:", abs(w-h)/w, allow_different_size_ratio)

                if w > min_size and h > min_size and w < max_size and h < max_size and abs(w-h)/w < allow_different_size_ratio and ((x < width*0.7 and y < height*0.9) or y < height*0.1) :
                    squares.append((sheetnum, x, y, w, h))
                    ##print("squares:", len(squares))

            #cv2.imshow("img_bin", img_bin)
            #cv2.waitKey(0)

            if sheetnum == 0 and (len(squares) -2) % 6 == 0:
                break
            elif sheetnum != 0 and len(squares) % 6 == 0:
                break

            bold += 1

            if bold > 10:
                raise ValueError(f"Error: Infinite loop detected in get_square, sheetnum:{sheetnum}")



        return squares

    def normalize_images(self, images, threshold=0.2):
        """
        画像の値を、各画像の最大値が1、最小値が0になるように正規化します。
        ただし、最大値と最小値の差がthreshold以下の場合、その画像は正規化されません。（空欄を想定）

        Args:
        images: torch.Tensor型の画像データ（torch.Size([N, C, H, W])）。
        threshold: 画像の最大値と最小値の差がこの値以下の場合、その画像は正規化されません。

        Returns:
        torch.Tensor型の正規化された画像データ。
        """

        # 3次元目と4次元目をフラットに
        buf = images.view(images.shape[0], 1 ,-1)
        ##print(images.shape)

        # 各画像の最大値と最小値を計算
        image_max = buf.max(dim=2)[0][:,0]
        image_min = buf.min(dim=2)[0][:,0]

        # 各画像の値から最小値を引いて、最大値と最小値の差で割る
        image_max = image_max.view(-1,1,1,1)
        image_min = image_min.view(-1,1,1,1)


        normalized_images = (images - image_min) / (image_max - image_min)

        return normalized_images

    def save(self, dir: str = "./files/result/image", filename: str = None):
        for i, s in enumerate(self.sheet):
            if filename is None:
                #filename = os.path.splitext(os.path.basename(self.path))[0]
                filename = f"{self.student_number}".zfill(2) + "_" + f"{i}".zfill(2)
            s.save(f"{dir}/{filename}", overwrite=False)

        #os.makedirs(f"./files/result/csv", exist_ok= True)
        #self.result.to_csv(f"./files/result/csv/{filename}.csv")


    def image_preprocess(self, img):
        """
        画像の前処理を行う。
        空欄検知ロジック + 大津の二値化。
        """
        # 青チャンネルを使用
        blue_img = img[:, :, 0]


        # --- 大津の二値化 ---
        _, thresh_img = cv2.threshold(blue_img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # --- 重心（モーメント）によるセンタリング ---
        M = cv2.moments(thresh_img)
        if M["m00"] != 0:
            # 現在の重心座標 (cX, cY)
            cX = int(M["m10"] / M["m00"])
            cY = int(M["m01"] / M["m00"])
            H, W = thresh_img.shape
            
            # 画像の中心座標との差分
            shift_x = int(W / 2) - cX
            shift_y = int(H / 2) - cY
            
            # アフィン変換で行列移動（背景は0で埋める）
            M_shift = np.float32([[1, 0, shift_x], [0, 1, shift_y]])
            thresh_centered = cv2.warpAffine(
                thresh_img, M_shift, (W, H), 
                borderMode=cv2.BORDER_CONSTANT, borderValue=0
            )
        else:
            thresh_centered = thresh_img

        # Tensorに変換して [0, 1] に正規化（形状を [1, 1, H, W] に）
        # ※ここでも batch 処理側と合わせるため、float32 にキャストして 255.0 で割ります
        norm_img = torch.tensor(thresh_centered, dtype=torch.float32).unsqueeze(0).unsqueeze(0)
        norm_img /= 255.0

        return norm_img
