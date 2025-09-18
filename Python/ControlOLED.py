#ControlOLED.py
#======================================================================================#
#------------------------------ IMPORTACIÓN DE LIBRERIAS ------------------------------#
#======================================================================================#
import time
import board
import busio
from PIL import Image, ImageOps, ImageDraw, ImageFont
import adafruit_ssd1306
#======================================================================================#
#------------------------------ CLASE QUE CONTROLA OLED -------------------------------#
#======================================================================================#
class ControlOLED:
                   # DIMESIÓN DEL DISPLAY
   def __init__(self, width=128, height=64):
       i2c = busio.I2C(board.SCL, board.SDA)
       """ INICIALIZACIÓN DE DISPLAY OLED """
       self.oled = adafruit_ssd1306.SSD1306_I2C(width, height, i2c)
       self.oled.fill(0)
       self.oled.show()
       # I2C ES EL PROTÓCOLO DE COMUNICACIÓN PARA EL OLED CON RBPI 5
#======================================================================================#
#------------------------------ PREPARA ÍCONO EN OLED ---------------------------------#
#======================================================================================#
   """ =============== FONDO BLANCO Y NEGRO =============== """
   def preparar_icono(self, path, size=(48,48)):
       img = Image.open(path).convert("RGBA")
       fondo = Image.new("RGBA", img.size, (255,255,255,255))
       fondo.paste(img, (0,0), img)
       img_gray = fondo.convert("L")
       umbral = 128
       img_bw = img_gray.point(lambda x: 255 if x < umbral else 0, mode="1")
       img_final = img_bw.resize(size)
       return img_final

   """ =============== MOSTRAR ÍCONO CON SEGUNDOS =============== """
   def mostrar_icono(self, path_icono, segundos):
       icono = self.preparar_icono(path_icono, size=(48,48))
       imagen_oled = Image.new("1", (self.oled.width, self.oled.height))
       imagen_oled.paste(icono, (20,10))  # centrado aprox
       draw = ImageDraw.Draw(imagen_oled)
       try:
           font = ImageFont.truetype("DejaVuSans-Bold.ttf", 26)
       except:
           font = ImageFont.load_default()
       draw.text((70,15), f"{segundos}s", font=font, fill=255)
       self.oled.image(imagen_oled)
       self.oled.show()

   """ ================== MOSTRAR TEXTO EN OLED ================== """
   def mostrar_texto(self, texto, x=0, y=0, size=16):
       imagen = Image.new("1", (self.oled.width, self.oled.height))
       draw = ImageDraw.Draw(imagen)
       try:
           font = ImageFont.truetype("DejaVuSans.ttf", size)
       except:
           font = ImageFont.load_default()
       draw.text((x,y), texto, font=font, fill=255)
       self.oled.image(imagen)
       self.oled.show()
#======================================================================================#
#------------------------------ LIMPIAR Y APAGAR OLED ---------------------------------#
#======================================================================================#
   def limpiar(self):
       self.oled.fill(0)
       self.oled.show()

   def apagar(self):
       try:
           self.oled.poweroff()
       except AttributeError:
           try:
               self.oled.write_cmd(0xAE)
           except AttributeError:
               print("Método de apagado no disponible")
#======================================================================================#
#--------------------------------------------------------------------------------------#
#======================================================================================#
