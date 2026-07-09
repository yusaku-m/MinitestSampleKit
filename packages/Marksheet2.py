from .Image import Image
from scipy.optimize import linear_sum_assignment

import os
import cv2
import numpy as np
import pandas as pd

import torch
from torch import nn


class Marksheet():
    """

    等間隔のマークシート。青色のみ使用可能。

    path:スキャンした画像のパス

    row:用紙全体の行数

    column:用紙全体の列数
    
    marker_position:黒で塗りつぶしたマーカーのリスト。(r,c)のタプルの形で行列を指定，方向等の調整に使用

    direction:horizontalで横向き，verticalで縦向き

    binary_threshold:２値化時の閾値マーク部分が真っ黒になるように調整

    mark_threshold:マークとの合致率の閾値

    monitor:Trueで動作ログ表示

    """
    def __init__(self, path, row, column,
                 marker_positions, 
                 direction = "horizontal", 
                 binary_threshold = 240,
                 mark_threshold = 0.5,
                 monitor = False):
        self.sheet = None
        self.path = path
        self.row = row
        self.column = column
        self.marker_positions = marker_positions
        self.direction = direction
        self.binary_threshold = binary_threshold
        self.mark_threshold = mark_threshold
        self.monitor = monitor
        self.grids =[]
        self.result = []

        if self.monitor is True:
            print("init")

    def read(self):
        """
        画像を読み込む
        """

        if self.monitor is True:
            print("open", self.path)
        self.sheet = Image(self.path)
        
        if self.monitor is True:
            print("read image shape:", self.sheet.img.shape)
            self.sheet.show("raw")
    
    def threshold_check(self):

        ret, bufimage = cv2.threshold(self.sheet.img[:,:,0], self.binary_threshold, 255, cv2.THRESH_BINARY)
        image = Image(img=bufimage)
        image.show("check")

    def get_reference_grids(self, size_min = 0.8, size_max = 1.2, black = 100):
        """
        基準の黒塗り位置を検出
        """

        # 画像のサイズを設定
        height = self.sheet.img.shape[0]
        width = self.sheet.img.shape[1]

        # マーク１ブロックのサイズ
        req_height = height / self.row
        req_width = width / self.column

        image =  self.sheet.img[:,:,0]

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
        # print("rectangles:", len(rectangles))
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
                # 長方形内部が黒で塗りつぶされているか確認
                req_only = self.sheet.img[y:y+h, x:x+w, 0]
                req_binary = cv2.threshold(req_only, black, 255, cv2.THRESH_BINARY)[1]
                #print("req_binary mean:", np.mean(req_binary))
                #cv2.imshow("req_binary", req_binary)
                #cv2.waitKey(0)
                if np.mean(req_binary) < 0.5 * 255:  # 黒塗りの閾値
                    filtered_rectangles.append(rect)

        result = np.float32(filtered_rectangles)

        result = result[:,:-2]
        # フィルタリングされた長方形を描画
        for rect in filtered_rectangles:
            x, y, w, h = rect
            cv2.rectangle(self.sheet.img, (x, y), (x + w, y + h), (0, 255, 0), 2)

        if self.monitor is True:
            print("get reference grid:", result)
            self.sheet.show("rect")
            if len(filtered_rectangles) != len(self.marker_positions):
                print("reference gridnumber is not much:", len(filtered_rectangles))
            


        return result

    def make_reference(self):
        """
        基準の黒塗り位置を塗りつぶした画像を作成
        """
        # 画像のサイズを設定
        height = self.sheet.img.shape[0]
        width = self.sheet.img.shape[1]

        # マーク１ブロックのサイズ
        req_height = height / self.row
        req_width = width / self.column
        
        # 白い画像を作成
        image = np.ones((int(height), 
                         int(width)),
                         dtype=np.uint8) * 255

        # 指定された位置に黒い正方形を描画
        for row, col in self.marker_positions:
            top_left = (int((col-2) * req_width), 
                        int((row-2) * req_height))
            
            bottom_right = (int((col-1) * req_width), 
                            int((row-1) * req_height))
            
            cv2.rectangle(image, top_left, bottom_right, (0, 0, 0), -1)

        image = Image(img=image)

        if self.monitor is True:
            print("make reference image shape:", image.img.shape, "reqtangle h,w:", req_height, req_width)
            image.show("reference")

        return image
    
    def rotation(self):
        """
        用紙の向き（水平or垂直）を補正する。
        """
        height = self.sheet.img.shape[0]
        width = self.sheet.img.shape[1]

        if (self.direction == "horizontal") and (width < height):
            self.sheet.img = cv2.rotate(self.sheet.img, cv2.ROTATE_90_CLOCKWISE)
            if self.monitor is True:
                print(f"rotated to horizontal")

        if (self.direction == "vertical") and (height < width):
            self.sheet.img = cv2.rotate(self.sheet.img, cv2.ROTATE_90_CLOCKWISE)
            if self.monitor is True:
                print(f"rotated to vertical")


        if self.monitor is True:
            print("rotation complete")
            self.sheet.show("rotation")

    def rotation_aliment(self):
        """
        用紙の上下を基準パターンに合わせ補正する。
        """
        # 方向判定（上下）
        best_match = 1e100
        
        reference = self.make_reference().img

        for j in range(2):
            result_img = self.sheet.img[:,:,0] - reference
            min_val = np.abs(np.sum(result_img))
            #print(i, max_val)
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
            self.sheet.img = cv2.rotate(self.sheet.img, cv2.ROTATE_180)

        if self.monitor is True:
            print("rotation complete")
            self.sheet.show("rotation2")

    def aliment(self, black = 100):
        """
        基準の四角形を参照して，ひずみ補正を行う。        
        """

        if self.monitor is True:
            print("aliment start")

        image = self.sheet.img

        height = self.sheet.img.shape[0]
        width = self.sheet.img.shape[1]

        # 台形補正
        # 変換前の座標を指定（例: 四角形の頂点）
        src_points = self.get_reference_grids()

        # 取得した基準座標に合わせてトリミング
        self.row -= 2; self.column -= 2
        self.sheet.img = self.sheet.img[int(np.min(src_points[:,1])) : , 
                                        int(np.min(src_points[:,0])) : , :]
        self.sheet.img = self.sheet.img[ : int((np.max(src_points[:,1]) - np.min(src_points[:,1])) / self.row * (self.row + 1)), 
                                         : int((np.max(src_points[:,0]) - np.min(src_points[:,0]))  /self.column * (self.column + 1)), :]

        #サイズを元に戻す
        self.sheet.img = cv2.resize(self.sheet.img,(width, height))

        if self.monitor is True:
            print(int(np.min(src_points[:,1])),int(np.max(src_points[:,1])))
            print(int(np.min(src_points[:,0])),int(np.max(src_points[:,0])))
            self.sheet.show("trim")

        # 上下向きの補正
        self.rotation_aliment()

        # 再度座標を取得
        src_points = self.get_reference_grids()



        # マーク１ブロックのサイズ
        req_height = height / self.row
        req_width = width / self.column

        # 変換後の座標を指定（例: 台形の頂点）
        buf = np.array(self.marker_positions)[:, [1, 0]]
        buf = (buf - 2) * [req_width, req_height]
        
        dst_points = []

        # 最も近い点の組み合わせをリストアップ
        for point in np.array(src_points):
            index = np.argmin((point[0] - buf[:,0])**2 + (point[1] - buf[:,1])**2)
            dst_points.append(buf[index])

        dst_points = np.array(dst_points)

        if self.monitor is True:
            print("dst_points:",dst_points)

        # 透視変換行列を計算
        H, status = cv2.findHomography(src_points, dst_points)

        # 画像を透視変換
        self.sheet.img = cv2.warpPerspective(self.sheet.img, H, (width, height), borderValue=(255, 255, 255))

 
        if self.monitor is True:
            print("aliment complete")
            self.sheet.show("aliment")
            ret, img_thresh = cv2.threshold(self.sheet.img[:,:,0], black, 255, cv2.THRESH_BINARY)
            image = Image(img=img_thresh)
            image.show("aliment except b")


    def draw_grid(self):
        """
        分割したマークのマス目を描画する
        """

        # 画像のサイズを設定
        height = self.sheet.img.shape[0]
        width = self.sheet.img.shape[1]

        # マーク１ブロックのサイズ
        req_height = height / self.row
        req_width = width / self.column

        # 白い画像を作成
        image = self.sheet.img

        # グリッドの間隔
        grid_size = 40

        # 垂直線を描画
        for x in np.linspace(0, width, self.column + 1):
            cv2.line(image, (int(x), 0), (int(x), height), (0, 0, 255), 1)

        # 水平線を描画
        for y in np.linspace(0, height, self.row + 1):
            cv2.line(image, (0, int(y)), (width, int(y)), (0, 0, 255), 1)

        image = Image(img=image)

        if self.monitor is True:
            print("make reference image shape:", image.img.shape, "reqtangle h,w:", req_height, req_width)
            image.show("grid")

        return image
    
    def mark_check(self):
        """
        マークを読み取って結果を配列で返す
        """
        ret, bufimage = cv2.threshold(self.sheet.img[:,:,0], self.binary_threshold, 255, cv2.THRESH_BINARY)
        bufimage = 255 - bufimage

        result = []
        for line in self.grids:
            row = []
            for grid in line:
                grid.make_mark()
                row.append(grid.mark_check())
            result.append(row)

        if self.monitor is True:
            print("mark check")
            self.sheet.show("mark check")
            cv2.imshow("bufimage", bufimage)
            cv2.waitKey(1)


        self.result = pd.DataFrame(np.array(result))

    def make_grids(self):
        """
        マークの１マスに関するクラスを作成
        """
        # 画像のサイズを設定
        height = self.sheet.img.shape[0]
        width = self.sheet.img.shape[1]

        # マーク１ブロックのサイズ
        req_height = height / self.row
        req_width = width / self.column

        self.grids =[]
        for r in range(self.row):
            line =[]
            for c in range(self.column):
                img = self.sheet.img[int(r * req_height) : int((r+1) * req_height), 
                                     int(c * req_width) : int((c+1) * req_width), :]
                
                line.append(Markgrid(img, self.binary_threshold, self.mark_threshold, monitor=self.monitor))
            self.grids.append(line)

    def handwrite_check(self, net_instance, device, terget_grids = [], labels = None):
        """
        手書きマスの数字を読み取る
        """
        if self.monitor is True:
            print("handwrite check start")

        for row, line in enumerate(self.handwrite_grids):
            for col, grid in enumerate(line):
                if (row, col) in terget_grids:
                    print(f"handwrite check: {row}, {col}")
                    self.result[col][row] = grid.number_check(net_instance, device, labels=labels)

        if self.monitor is True:
            print("handwrite check complete")
            self.sheet.show("handwrite check")

    def make_handwrite_grids(self, remove_thickness = 0.2):
        """
        手書きマスのクラスを作成
        """
        rt = remove_thickness
        # 画像のサイズを設定
        height = self.sheet.img.shape[0]
        width = self.sheet.img.shape[1]

        # マーク１ブロックのサイズ
        req_height = height / self.row
        req_width = width / self.column
        
        rh = int(req_height * rt)
        rw = int(req_width * rt)

        self.handwrite_grids =[]
        for r in range(self.row - 1):
            line =[]
            for c in range(self.column - 1):
                img = self.sheet.img[int(r * req_height) + rh : int((r+2) * req_height - rh), 
                                     int(c * req_width) + rw : int((c+2) * req_width - rw), :]
                print(f"make handwrite grid: {r}, {c}, shape: {img.shape}")
                
                line.append(HandWriteGrid(img, monitor=self.monitor))
            self.handwrite_grids.append(line)
    
    def save(self):
        filename = os.path.splitext(os.path.basename(self.path))[0]
        self.sheet.save(f"./files/result/image/{filename}", overwrite=True)

        os.makedirs(f"./files/result/csv", exist_ok= True)
        self.result.to_csv(f"./files/result/csv/{filename}.csv")

class Markgrid():
    """
    マークの１マスに関するクラス。
    
    img:対象マスの画像
    """

    def __init__(self, img, binary_threshold, mark_threshold, vratio = 0.8, hratio = 0.5, monitor = False):

        self.img = img
        self.binary_threshold = binary_threshold
        self.mark_threshold = mark_threshold
        self.vratio = vratio
        self.hratio = hratio
        self.monitor = monitor

    def make_mark(self):
        """
        マークの楕円形状を作成

        vratio:枠内でのマークの比率，実際より小さめに設定する
        """
        # 画像のサイズを設定
        height = int(self.img.shape[0])
        width = int(self.img.shape[1])

        # 楕円半径
        vradius = int(height * self.vratio / 2)
        hradius = int(width * self.hratio / 2)

        # 黒い画像を作成
        image = np.zeros((height, width), dtype=np.uint8)

        # 楕円の中心座標
        center_coordinates = (width//2, height//2)

        # 楕円のサイズ (長軸と短軸の半径)
        axes_length = (hradius, vradius)  # 半径なので20×30ピクセルの楕円

        # 楕円の色 (黒)
        color = (255, 255, 255)

        # 楕円を描画
        cv2.ellipse(image, center_coordinates, axes_length, 0, 0, 360, color, -1)
        
        return image

    def mark_check(self):
        """
        マークとの合致率が閾値以上かを判定する。
        """
        ret, bufimage = cv2.threshold(self.img[:,:,0], self.binary_threshold, 255, cv2.THRESH_BINARY)
        bufimage = 255 - bufimage

        reference = self.make_mark()
        mean = np.mean(bufimage[reference == 255] / 255)
        
        if mean > self.mark_threshold:
            # 画像のサイズを設定
            height = int(self.img.shape[0])
            width = int(self.img.shape[1])

            # 円半径
            radius = int(height * 0.1)

            # 楕円の中心座標
            center_coordinates = (width//2, height//2)

            # 楕円のサイズ (長軸と短軸の半径)
            axes_length = (radius, radius)

            # 楕円の色 (黒)
            color = (0, 0, 255)

            # 楕円を描画
            cv2.ellipse(self.img, center_coordinates, axes_length, 0, 0, 360, color, -1)

            return True
        
        else:
            return False

class HandWriteGrid():
    """
    手書きマスのクラス。
    2×2の4マスが１つのマスを表す。
    """
    def __init__(self, img,  monitor = False):

        self.img = img
        self.monitor = monitor
        self.predicted_number = None

    def number_check(self, net_instance, device, labels = None):

        img = self.img.copy()
        nega = 255 - img
        img = cv2.resize(nega, (64, 63))
        model_instance = net_instance

        #青のチャンネルのみをgray_imgとして再定義
        gray_img = img[:, :, 0]
        norm_img = self.normalize_images(torch.tensor(gray_img).unsqueeze(0).unsqueeze(0).float())
        norm_img = torch.tensor(gray_img, dtype=torch.float32) / 255.0
        norm_img = norm_img.unsqueeze(0).unsqueeze(0)

        threshold_n = norm_img.mean((1,2,3), keepdim=False) * 1.5
        threshold_n = 0.13

        norm_img[norm_img < threshold_n] = 0
        norm_img[norm_img >= threshold_n] = 1
        norm_img = norm_img.to(device)

        with torch.no_grad():
            model_instance.eval()
            print(model_instance(norm_img))
            pred = model_instance(norm_img).argmax(1).item()
            self.predicted_number = pred
        
        if labels is not None:
            pred = labels[pred]

        cv2.putText(self.img, str(pred), (0, 17), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        instance = Image(img=gray_img)
        instance.save(f"./files/result/image/{pred}/{pred}")
        
        if self.monitor is True:
            print("norm_img shape:", norm_img.shape)
            cv2.imshow("gray_img", gray_img)
            cv2.imshow("norm_img", norm_img[0][0].cpu().numpy())
            cv2.waitKey(1)

            print(f"predicted number: {pred}")

        return pred

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
        print(images.shape)
        # 各画像の最大値と最小値を計算
        image_max = buf.max(dim=2)[0][:,0]
        image_min = buf.min(dim=2)[0][:,0]
        # 各画像の値から最小値を引いて、最大値と最小値の差で割る
        image_max = image_max.view(-1,1,1,1)
        image_min = image_min.view(-1,1,1,1)


        normalized_images = (images - image_min) / (image_max - image_min)

        return normalized_images

    def image_preprocess(self, img):
        """
        画像の前処理を行う。
        サイズを指定してリサイズし、グレースケールに変換する。
        """
        # 動的２値化
        """
        gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        norm_img = self.normalize_images(torch.tensor(gray_img).unsqueeze(0).unsqueeze(0).float())
        threshold_n = norm_img.mean((1,2,3), keepdim=False) * 1.5
        """

        #固定値での正規化
        #青チャンネルだけを使用
        norm_img = torch.tensor(img[:,:,0], dtype=torch.float32).unsqueeze(0).unsqueeze(0)
        norm_img /= 255
        threshold_n = 0.13

        norm_img[norm_img < threshold_n] = 0
        norm_img[norm_img >= threshold_n] = 1

        return norm_img.to(self.device)