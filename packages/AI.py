import torch
import torch.nn as nn
import torch.nn.functional as F
from collections import OrderedDict

class PlusMinusNeuralNetwork(nn.Module):
    def __init__(self):
        super().__init__()
        dropout_rate = 0.2
        self.layer1 = nn.Sequential(
            # 畳み込み層
            # 1チャンネルを32チャンネルにする、3x3のフィルターを使う、1つずつずらす
            nn.Conv2d(1, 32, 3, 1),
            # 活性化関数
            nn.ReLU(),
            nn.Conv2d(32, 32, 1, 1),
            nn.ReLU(),
            # プーリング層、2x2の領域から最大のものを1つ取り出す
            nn.MaxPool2d(2, 2),
            # Dropout
            nn.Dropout(dropout_rate),
        )
        self.layer2 = nn.Sequential(
            # 畳み込み層
            # 32チャンネルを64チャンネルにする、3x3のフィルターを使う、1つずつずらす
            nn.Conv2d(32, 64, 3, 1),
            # 活性化関数
            nn.ReLU(),
            nn.Conv2d(64, 64, 1, 1),
            nn.ReLU(),
            nn.MaxPool2d(2, 2),
            # Dropout
            nn.Dropout(dropout_rate),
        )
        self.layer3 = nn.Sequential(
            # 畳み込み層
            nn.Conv2d(64, 128, 3, 1),
            # 活性化関数
            nn.ReLU(),
            nn.Conv2d(128, 128, 1, 1),
            nn.ReLU(),
            nn.MaxPool2d(2, 2),
            # Dropout
            nn.Dropout(dropout_rate),
        )
        self.layer4 = nn.Sequential(
            # 畳み込み層
            nn.Conv2d(128, 256, 3, 1),
            # 活性化関数
            nn.ReLU(),
            nn.Conv2d(256, 256, 1, 1),
            nn.ReLU(),
            nn.MaxPool2d(2, 2),
            # Dropout
            nn.Dropout(dropout_rate),
        )
        self.layer_last = nn.Sequential(
            # (チャンネル数 )となるように縦横を平均化
            nn.AdaptiveAvgPool2d(1),
            nn.Flatten(),
            # 線形層
            nn.Linear(256, 3),
            nn.LogSoftmax(dim=1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.layer1(x)
        #print(x.shape)
        x = self.layer2(x)
        #print(x.shape)
        x = self.layer3(x)
        #print(x.shape)
        x = self.layer4(x)
        #print(x.shape)
        x = self.layer_last(x)
        #print(x.shape)
        return x
    
class NumberNeuralNetwork(nn.Module):
    def __init__(self):
        super().__init__()
        dropout_rate = 0.2
        self.layer1 = nn.Sequential(
            # 畳み込み層
            # 1チャンネルを32チャンネルにする、3x3のフィルターを使う、1つずつずらす
            nn.Conv2d(1, 32, 3, 1),
            # 活性化関数
            nn.ReLU(),
            nn.Conv2d(32, 32, 1, 1),
            nn.ReLU(),
            # プーリング層、2x2の領域から最大のものを1つ取り出す
            nn.MaxPool2d(2, 2),
            # Dropout
            nn.Dropout(dropout_rate),
        )
        self.layer2 = nn.Sequential(
            # 畳み込み層
            # 32チャンネルを64チャンネルにする、3x3のフィルターを使う、1つずつずらす
            nn.Conv2d(32, 64, 3, 1),
            # 活性化関数
            nn.ReLU(),
            nn.Conv2d(64, 64, 1, 1),
            nn.ReLU(),
            nn.MaxPool2d(2, 2),
            # Dropout
            nn.Dropout(dropout_rate),
        )
        self.layer3 = nn.Sequential(
            # 畳み込み層
            nn.Conv2d(64, 128, 3, 1),
            # 活性化関数
            nn.ReLU(),
            nn.Conv2d(128, 128, 1, 1),
            nn.ReLU(),
            nn.MaxPool2d(2, 2),
            # Dropout
            nn.Dropout(dropout_rate),
        )
        self.layer4 = nn.Sequential(
            # 畳み込み層
            nn.Conv2d(128, 256, 3, 1),
            # 活性化関数
            nn.ReLU(),
            nn.Conv2d(256, 256, 1, 1),
            nn.ReLU(),
            nn.MaxPool2d(2, 2),
            # Dropout
            nn.Dropout(dropout_rate),
        )
        self.layer_last = nn.Sequential(
            # (チャンネル数 )となるように縦横を平均化
            nn.AdaptiveAvgPool2d(1),
            nn.Flatten(),
            # 線形層
            nn.Linear(256, 11),
            nn.LogSoftmax(dim=1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.layer1(x)
        #print(x.shape)
        x = self.layer2(x)
        #print(x.shape)
        x = self.layer3(x)
        #print(x.shape)
        x = self.layer4(x)
        #print(x.shape)
        x = self.layer_last(x)
        #print(x.shape)
        return x

# Denseブロック内の単一の畳み込み層
class _DenseLayer(nn.Sequential):
    def __init__(self, num_input_features, growth_rate, bn_size, drop_rate):
        super(_DenseLayer, self).__init__()
        self.add_module('norm1', nn.BatchNorm2d(num_input_features))
        self.add_module('relu1', nn.ReLU(inplace=True))
        self.add_module('conv1', nn.Conv2d(num_input_features, bn_size * growth_rate,
                                           kernel_size=1, stride=1, bias=False))
        self.add_module('norm2', nn.BatchNorm2d(bn_size * growth_rate))
        self.add_module('relu2', nn.ReLU(inplace=True))
        self.add_module('conv2', nn.Conv2d(bn_size * growth_rate, growth_rate,
                                           kernel_size=3, stride=1, padding=1, bias=False))
        self.drop_rate = drop_rate

    def forward(self, x):
        new_features = super(_DenseLayer, self).forward(x)
        if self.drop_rate > 0:
            new_features = F.dropout(new_features, p=self.drop_rate, training=self.training)
        return torch.cat([x, new_features], 1)

# 複数のDense層で構成されるDenseブロック
class _DenseBlock(nn.Sequential):
    def __init__(self, num_layers, num_input_features, bn_size, growth_rate, drop_rate):
        super(_DenseBlock, self).__init__()
        for i in range(num_layers):
            layer = _DenseLayer(num_input_features + i * growth_rate, growth_rate, bn_size, drop_rate)
            self.add_module(f'denselayer{i + 1}', layer)

# 異なるDenseブロック間の遷移層
class _Transition(nn.Sequential):
    def __init__(self, num_input_features, num_output_features):
        super(_Transition, self).__init__()
        self.add_module('norm', nn.BatchNorm2d(num_input_features))
        self.add_module('relu', nn.ReLU(inplace=True))
        self.add_module('conv', nn.Conv2d(num_input_features, num_output_features,
                                          kernel_size=1, stride=1, bias=False))
        self.add_module('pool', nn.AvgPool2d(kernel_size=2, stride=2))

class NumberNeuralNetworkV1(nn.Module):
    def __init__(self, growth_rate=32, block_config=(6, 12, 24, 16),
                 num_init_features=64, bn_size=4, drop_rate=0, num_classes=11):
        super(NumberNeuralNetwork, self).__init__()

        # 最初期の畳み込み層
        # 入力チャネルを1 (グレースケール) に設定
        # 画像サイズが小さい (63x64) ため、カーネルサイズとストライドを調整
        self.features = nn.Sequential(OrderedDict([
            ('conv0', nn.Conv2d(1, num_init_features, kernel_size=3, stride=1,
                                padding=1, bias=False)), # 63x64 を保持
            ('norm0', nn.BatchNorm2d(num_init_features)),
            ('relu0', nn.ReLU(inplace=True)),
            ('pool0', nn.MaxPool2d(kernel_size=2, stride=2)) # ここで 31x32 程度になる
        ]))

        # 各Denseブロックと遷移層
        num_features = num_init_features
        for i, num_layers in enumerate(block_config):
            block = _DenseBlock(num_layers=num_layers, num_input_features=num_features,
                                bn_size=bn_size, growth_rate=growth_rate,
                                drop_rate=drop_rate)
            self.features.add_module(f'denseblock{i + 1}', block)
            num_features += num_layers * growth_rate
            if i != len(block_config) - 1:
                trans = _Transition(num_input_features=num_features,
                                    num_output_features=num_features // 2)
                self.features.add_module(f'transition{i + 1}', trans)
                num_features = num_features // 2

        # 最終のBatchNormとReLU
        self.features.add_module('norm5', nn.BatchNorm2d(num_features))
        self.features.add_module('relu5', nn.ReLU(inplace=True))

        # 分類器
        # グローバル平均プーリング後の特徴マップサイズを計算する必要があります
        # 例: 31x32 -> 15x16 -> 7x8 -> 3x4 (MaxPool/AvgPoolの回数とstrideによる)
        # 最終的な特徴マップの空間的次元を把握し、それに合わせてプーリングを調整します
        # 最終のAvgPool2dで特徴マップを 1x1 にします。
        self.classifier = nn.Linear(num_features, num_classes)

        # パラメータの初期化
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight)
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.Linear):
                nn.init.constant_(m.bias, 0)

    def forward(self, x):
        features = self.features(x)
        # グローバル平均プーリング
        out = F.adaptive_avg_pool2d(features, (1, 1))
        out = torch.flatten(out, 1) # out.view(out.size(0), -1) と同義
        out = self.classifier(out)
        return out
