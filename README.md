# BLEKeyboardLink

nRF52840デバイスを経由して他のデバイスにパソコンのキーボード入力およびマウス入力を送信するプログラムです。

## 推奨デバイス

* [nRF52840 MDBT50Q 開発用USBドングル（ブートローダ書き込み済）](https://www.switch-science.com/products/6761)

## Arduino

[Arduino IDE](https://www.arduino.cc/en/software)をインストールして、ボードマネージャから`Adafruit nRF52 by Adafruit`を追加してください。

`ble_keyboard_link.ino`を開いて、`Raytac nRF52840 Dongle`を指定してビルド＆書き込みしてください。

## Python

次のライブラリをインストールしてください。

```sh
pip install pynput keyboard pyserial
```

nRF52840デバイスが接続されているシリアルポートを指定して起動してください。

```sh
python ble_keyboard_link.py COM20
```

ディスプレイの設定で拡大縮小を設定している場合、引数`display_scale`で指定してください。

```sh
python ble_keyboard_link.py COM20 --display_scale 1.5
```
