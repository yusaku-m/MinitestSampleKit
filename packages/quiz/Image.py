#画像処理用クラス
import os
import cv2
import pyautogui

class Image():
    def __init__(self, path = "", img = ""):
        """
        pathで指定された画像ファイルを開く。ファイル名には全角文字を含めない
        またはimgに与えられた画像を格納する。
        """

        if path != "":
            currentpath = os.getcwd()

            #フルパスの場合のみディレクトリ移動(opencvは全角非対応)
            if os.path.isabs(path):
                os.chdir(os.path.dirname(path))
                img = cv2.imread(f"./{os.path.basename(path)}")
                os.chdir(currentpath)
            else:
                img = cv2.imread(path)

        #print(img.shape)

        self.img = img


    def show(self, windowname = "show", waittime = 1, size_limit = 0.8, enlargement = False):
        """
        画像を表示
        waittime:   0でキーを待機，1以上で指定ms待機
        resize_ratio: 拡大
        size_limit: ディスプレイ解像度を基準とした表示幅または高さの上限
        enlargement: size_limitまで拡大するか否か
        """
        img_width = self.img.shape[1]; img_height = self.img.shape[0]
        monitor_width, monitor_height = pyautogui.size()

        height_ratio = img_height / monitor_height
        width_ratio  = img_width  / monitor_width

        if (height_ratio > size_limit) or (width_ratio > size_limit) or (enlargement is True):
            # サイズ上限を超えた場合　または　拡大オプションがオンでサイズ変更
            if height_ratio > width_ratio:
                height = int(monitor_height * size_limit)
                width =  int(height / img_height * img_width )
            else:
                width =  int(monitor_width * size_limit)
                height = int(width / img_width * img_height)
        else:
            # そうでなければ現尺
            width =  img_width
            height = img_height

        img = cv2.resize(self.img, (width, height) )
        cv2.imshow(windowname, img)
        cv2.waitKey(waittime)
    
    def save(self, path, overwrite = False, monitor = False):
        """
        指定パスへjpgとして保存
        overwrite: trueなら上書き
        """
        basefolder = os.getcwd()
        tergetfolder = os.path.dirname(path)
        filename     = os.path.basename(path)
        if not os.path.exists(tergetfolder):
            if monitor is True:
                print('Folder is not exist...')
            os.makedirs(tergetfolder)
        os.chdir(tergetfolder)
        bufpath = filename
        i = 0

        if overwrite is False:
            while os.path.exists(f"{bufpath}.jpg"):
                if monitor is True:
                    print('File exist already. Make a new file')
                i += 1
                bufpath = f"{filename}_{str(i).zfill(2)}"

        cv2.imwrite(f"{bufpath}.jpg", self.img)
        if monitor is True:
            print("File is saved")
        os.chdir(basefolder)

