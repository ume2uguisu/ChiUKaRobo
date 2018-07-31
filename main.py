
#必要なライブラリを読みます
import uos
import ure
import utime
import ujson
from machine import SPI, Pin
import sdcard
import ssd1331

#ここに書いた値はプログラム中で変えないよ。
SD_MOUNT_PATH = '/sd'
CONFIG_FILE = 'image_settings.json'
DEFAULT_SLEEP = 1
SD_ERROR = '/sd_error.bmp'
JSON_ERROR = '/json_error.bmp'
IMAGE_ERROR = '/image_error.bmp'

#画像データをOLEDに送るメソッド
def send_image(image_name):
  #画像データを入れるバッファを用意
  buffer = bytearray()

  #ファイルを開く
  with open(image_name, 'rb') as f:
    #ビットマップ画像のヘッダから、データ位置、横幅、高さ、色情報ビット数を取得
    f.seek(10, 0)
    offset = int.from_bytes(f.read(4), 'little')
    f.seek(4, 1)
    width = int.from_bytes(f.read(4), 'little')
    height = int.from_bytes(f.read(4), 'little')
    f.seek(2, 1)
    bit_count = int.from_bytes(f.read(2), 'little')
    
    #色情報ビット数から、読み込みバイト数を決定
    if(bit_count == 24):
      color_data_bytes = 3
    elif(bit_count == 32):
      color_data_bytes = 4
    else:
      #24ビット、32ビット以外のビットマップは非対応なので例外送信
      raise

    #画像データを読んで、ディスプレイに送る色情報へ変換
    for y in range(0, height):
      for x in range(0, width):
        display_position = ((height -1 - y) * width) + x
        read_position = display_position * color_data_bytes
        f.seek(read_position + offset, 0)
        rgb = f.read(color_data_bytes)
        color = ssd1331.color565(rgb[2], rgb[1], rgb[0])

        buffer.extend(color.to_bytes(2, 'big'))

  #ディスプレイへ画像を送信
  display.blit_buffer(buffer, 0, 0, width, height)

#定義ファイルに指定された画像を表示するメソッド
def read_from_config_file():
  try:
    with open(CONFIG_FILE, 'r') as conf_f:
      conf = ujson.load(conf_f)
  except:
    send_image(JSON_ERROR)
    raise

  while(True):
    for image in conf:
      try:
        send_image(image['file_name'])
    
      except:
        send_image(IMAGE_ERROR)

      utime.sleep(float(image['display_sec']))

#SDカードに存在する画像を表示するメソッド（定義ファイルが無い時に使われます）
def read_from_file_list():
  while(True):
    target_list=uos.listdir()
    
    for target in target_list:
      if (ure.match('.*bmp$', target)):
        try:
          send_image(target)
    
        except:
          send_image(IMAGE_ERROR)
          raise

        utime.sleep(DEFAULT_SLEEP)


###プログラムはここから動くよ

#SDカードやディスプレイが接続されるシリアルバスの初期化
spi = SPI(1, baudrate=26000000, polarity=1, phase=1, sck=Pin(18), mosi=Pin(17), miso=Pin(19))

#ディスプレイの初期化
display = ssd1331.SSD1331(spi, dc=Pin(12), cs=Pin(15), rst=Pin(16))

#SDカードを準備
try:
  sd = sdcard.SDCard(spi, Pin(5))
  uos.mount(sd, SD_MOUNT_PATH)
  uos.chdir(SD_MOUNT_PATH)
except:
  #SDカードの準備に失敗したら、エラー画面出すよ
  send_image(SD_ERROR)
  raise

#画像定義ファイルステータスが
try:
  uos.stat(CONFIG_FILE)
  #所得できたら定義ファイルから画像を表示するメソッドを実行
  read_from_config_file()
except:
  #取得できなかったらSDカードに存在する画像を表示するメソッドを実行
  read_from_file_list()


