#Universidad Autónoma Metropolitana Unidad Azcapotzalco
#Nombre: Martin Chavez Jaramillo
#Matrícula: 2163036728
#Ingeniería en Computación
#Fecha: 23 Septiembre 2025
#Módulo control de la Interfaz
#DetectorGUI2.py
#======================================================================================#
#------------------------------ IMPORTACIÓN DE LIBRERIAS ------------------------------#
#======================================================================================#
import sys
from PySide6.QtWidgets import (QApplication, QWidget, QLabel, QVBoxLayout, QPushButton,
                              QHBoxLayout, QSlider, QCheckBox, QTextBrowser, QSplitter,
                              QGraphicsDropShadowEffect)
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QPixmap, QImage, QColor, QPainter, QRadialGradient, QPen
import cv2
import numpy as np
import time
#======================================================================================#
#--------------------------- IMPORTACIÓN DE MÓDULOS LOCALES ---------------------------#
#======================================================================================#
from DetectorTFLite2 import DetectorTFLite2
from ControlLEDs import ControlLEDs
from ControlOLED import ControlOLED
#======================================================================================#
#---------------------------- CLASE CONTENEDOR DEL LOGOTIPO ---------------------------#
#======================================================================================#
class LogoContainer(QLabel):
   def __init__(self, pixmap):
       super().__init__()
       self.pixmap_logo = pixmap
       self.setFixedSize(pixmap.size())
       self.setAlignment(Qt.AlignCenter)

       # Sombra del contenedor
       shadow = QGraphicsDropShadowEffect()
       shadow.setBlurRadius(20)
       shadow.setXOffset(0)
       shadow.setYOffset(0)
       shadow.setColor(QColor(0,0,0,180))
       self.setGraphicsEffect(shadow)

   def paintEvent(self, event):
       painter = QPainter(self)
       painter.setRenderHint(QPainter.Antialiasing)

       # Fondo con degradado radial
       grad = QRadialGradient(self.width()/2, self.height()/2, self.width()/2)
       grad.setColorAt(0, QColor(255,255,255,180))  # centro brillante
       grad.setColorAt(1, QColor(0,0,0,50))         # bordes oscuros
       painter.setBrush(grad)
       painter.setPen(Qt.NoPen)
       painter.drawRoundedRect(0, 0, self.width(), self.height(), 20, 20)

       # Dibujar el logo centrado
       logo_w = self.pixmap_logo.width()
       logo_h = self.pixmap_logo.height()
       painter.drawPixmap((self.width()-logo_w)//2, (self.height()-logo_h)//2,
                           self.pixmap_logo)
#======================================================================================#
#----------------------------- CLASE SEMÁFORO VIRTUAL GUI -----------------------------#
#======================================================================================#
class SemaforoWidget(QWidget):
   def __init__(self):
       super().__init__()
       self.rojo_on = False
       self.amarillo_on = False
       self.verde_on = False
       self.setFixedSize(60, 180)

       # Variables para parpadeo amarillo (visual)
       self.amarillo_visible = False
       self.ultimo_cambio_amarillo = time.time()
       self.parpadeo_intervalo = 0.5  # Igual que ControlLEDs.py

   def paintEvent(self, event):
       painter = QPainter(self)
       painter.setRenderHint(QPainter.Antialiasing)

       # Fondo negro
       painter.fillRect(0, 0, self.width(), self.height(), QColor(0, 0, 0))

       # Dibujar los LEDs
       radio = 20
       separacion = 10

       # Rojo
       color = QColor(255, 0, 0) if self.rojo_on else QColor(50, 0, 0)
       painter.setBrush(color)
       painter.drawEllipse(20, separacion, radio, radio)

       # Amarillo
       color = QColor(255, 255, 0) if self.amarillo_on else QColor(50, 50, 0)
       painter.setBrush(color)
       painter.drawEllipse(20, 2*separacion + radio, radio, radio)

       # Verde
       color = QColor(0, 255, 0) if self.verde_on else QColor(0, 50, 0)
       painter.setBrush(color)
       painter.drawEllipse(20, 3*separacion + 2*radio, radio, radio)

       # ----------------- Borde externo -----------------
       pen = QPen(QColor(255,255,255))
       #pen = QPainter(QColor(255,255,255))
       pen.setWidth(3)
       painter.setPen(pen)
       painter.setBrush(Qt.NoBrush)
       painter.drawRoundedRect(0, 0, self.width(), self.height(), 10, 10)

       painter.end()

   def update(self):
       super().update()
#======================================================================================#
#--------------------------- CLASE INTERFAZ PRINCIPAL (MAIN) --------------------------#
#======================================================================================#
class DetectorGUI(QWidget):
   def __init__(self):
       super().__init__()
       self.setWindowTitle("Wheelchair Detector GUI")
       self.leds = ControlLEDs()
       self.oled = ControlOLED()
       self.detector = DetectorTFLite2(leds=self.leds, oled=self.oled)
#======================================================================================#
#---------------------------- LABEL QUE CONTENDRÁ EL VIDEO ----------------------------#
#======================================================================================#
       self.video_label = QLabel()
       self.video_label.setFixedSize(640, 480)
       self.video_label.setStyleSheet("""
       border: 5px solid white;
       """)
#======================================================================================#
#--------------------------- CAJA DE HISTORIAL DE DETECCIÓN ---------------------------#
#======================================================================================#
       self.texto_deteccion = QTextBrowser()
       self.texto_deteccion.setReadOnly(True)
       self.texto_deteccion.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
       self.texto_deteccion.setFixedWidth(300)
       self.historial_detecciones = []
#======================================================================================#
#----------------------------- LLAMADA A LA CLASE SEMÁFORO ----------------------------#
#======================================================================================#
       self.semaforo = SemaforoWidget()
#======================================================================================#
#---------------------------- BOTÓN PARA SALIR DEL SISTEMA ----------------------------#
#======================================================================================#
       self.exit_button = QPushButton("Salir")
       self.exit_button.clicked.connect(self.close_app)
#======================================================================================#
#---------------------------- SE PLASMA EL LOGO A VISUALIZAR --------------------------#
#======================================================================================#
       # --- Logo ---
       pixmap_logo = QPixmap("uam_logo.png")
       pixmap_logo = pixmap_logo.scaled(550, 550, Qt.KeepAspectRatio,
       Qt.SmoothTransformation)
       self.logo_container = LogoContainer(pixmap_logo)
       # BORDE BLANCO OPCIONAL
       self.logo_container.setStyleSheet("""
       border: 3px solid white;
       border-radius: 15px;
       """)
#======================================================================================#
#--------------------------- SLIDER PARA UMBRAL DE CONFIANZA --------------------------#
#======================================================================================#
       self.umbral_slider = QSlider(Qt.Horizontal)
       self.umbral_slider.setRange(10, 100)  # equivale 0.10–1.00
       self.umbral_slider.setValue(int(self.detector.confidence_threshold * 100))
       self.umbral_slider.valueChanged.connect(self.actualizar_umbral)
       self.umbral_valor = QLabel(f"{self.detector.confidence_threshold:.2f}")
#======================================================================================#
#--------------------- POSICIONAMIENTO DE LOS WIDGETS DEL SISTEMA ---------------------#
#======================================================================================#
       # Lado izquierdo: video + semáforo + salir + umbral
       lado_izquierdo = QVBoxLayout()
       lado_izquierdo.addWidget(self.video_label)
# =====================================================================================#
       # Layout horizontal para sémaforo a la izquierda y resto centrado
       h_layout_superior = QHBoxLayout()
# =====================================================================================#
       # Semáfoto a la izquierda
       h_layout_superior.addWidget(self.semaforo, alignment=Qt.AlignTop | Qt.AlignLeft)
# =====================================================================================#
       # Layout vertical centrado para logo + salir
       v_layout_central = QVBoxLayout()
       v_layout_central.setAlignment(Qt.AlignCenter)
       v_layout_central.addWidget(self.logo_container)
       v_layout_central.addWidget(self.exit_button)
       h_layout_superior.addLayout(v_layout_central)
# =====================================================================================#
       # Layou horizontal centrado para umbral
       umbral_layout = QHBoxLayout()
       umbral_layout.setAlignment(Qt.AlignCenter) # Alinear centralmente
       umbral_label = QLabel("Umbral de confianza:")
       umbral_layout.addWidget(umbral_label)
       umbral_layout.addWidget(self.umbral_slider)
       umbral_layout.addWidget(self.umbral_valor)
       lado_izquierdo.addLayout(umbral_layout)
# =====================================================================================#
       # Envolver lado izquierdo en QWidget para el splitter
       widget_izquierdo = QWidget()
       widget_izquierdo.setLayout(lado_izquierdo)
       splitter = QSplitter(Qt.Horizontal)
       splitter.addWidget(widget_izquierdo)
       splitter.addWidget(self.texto_deteccion)
       splitter.setStretchFactor(0, 3)
       splitter.setStretchFactor(1, 1)
# =====================================================================================#
       # Añadir layout superior al lado izquierdo
       lado_izquierdo.addLayout(h_layout_superior)
# =====================================================================================#
       # Layout horizontal principal
       main_layout = QHBoxLayout()
       main_layout.addWidget(splitter)
# =====================================================================================#
       self.setLayout(main_layout)
# =====================================================================================#
       # Timer para actualizar frames
       self.timer = QTimer()
       self.timer.timeout.connect(self.update_frame)
       self.timer.start(30)
# =====================================================================================#
   # Convertir frame OpenCV a QPixmap
   def convert_cv_qt(self, cv_img):
       rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
       h, w, ch = rgb_image.shape
       bytes_per_line = ch * w
       qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
       return QPixmap.fromImage(qt_image)
# =====================================================================================#
   # Actualizar cada frame
   def update_frame(self):
       frame = self.detector.procesar_frame()
       if frame is not None:
           pixmap = self.convert_cv_qt(frame)
           self.video_label.setPixmap(pixmap)
# =====================================================================================#
       # Actualizar semáforo GUI
       self.semaforo.rojo_on = self.detector.red_active
       self.semaforo.amarillo_on = self.detector.leds.estado_led_amarillo
       self.semaforo.verde_on = not self.detector.red_active
       self.semaforo.update()
# =====================================================================================#
       # ------------------ Mostrar última detección en caja de texto -----------------
       if hasattr(self.detector, "ultima_deteccion") and(self.detector.ultima_deteccion
                                                                       is not None):
           label, conf = self.detector.ultima_deteccion
           mensaje = f"{label} detectada con una precisión de: {conf:.2f}"
       else:
           mensaje = "Nada detectado"
# =====================================================================================#       
       # INSERTAR EL MENSAJE AL INICIO DEL HISTORIAL
       if len(self.historial_detecciones) == 0 or (mensaje !=
                                                       self.historial_detecciones[0]):
           self.historial_detecciones.insert(0, mensaje)
# =====================================================================================#
       # MANTENER MÁXIMO 100 REGISTROS
       if len(self.historial_detecciones) > 100:
           self.historial_detecciones.pop() # ELIMINAR EL MAS ANTIGUO
# =====================================================================================#
       # ACTUALIZAR QTextBrowser sin resetear scroll
       #GUARDAR POSICION ACTUAL DEL SCROLL
       scroll_bar = self.texto_deteccion.verticalScrollBar()
       valor_scroll = scroll_bar.value()
# =====================================================================================#
       # LIMPIAR Y AGREGAR TODAS LAS LINEAS (LA PRIMERA SELA LA MAS RECIENTE)
       self.texto_deteccion.clear()
       for linea in self.historial_detecciones:
           self.texto_deteccion.append(linea)
# =====================================================================================#
       # RESTAURAR SCROLL SOLO SI ESTABA EN EL MEDIO/BAJO
       scroll_bar.setValue(valor_scroll)
# =====================================================================================#
   # ---- Nuevos métodos GUI ----
   def actualizar_umbral(self, value):
       nuevo_umbral = value / 100.0
       self.umbral_valor.setText(f"{nuevo_umbral:.2f}")
       self.detector.confidence_threshold = nuevo_umbral
       print(f"[GUI] Nuevo umbral de confianza: {nuevo_umbral:.2f}")
#======================================================================================#
#--------------------------- SALIR DE LA APP DEL SISTEMA GUI --------------------------#
#======================================================================================#
   # Salir de la app
   def close_app(self):
       self.timer.stop()
       self.detector.detener()
       self.close()
#======================================================================================#
#--------------------------- EJECUTAR SISTEMA (GUI PRINCIPAL) -------------------------#
#======================================================================================#
if __name__ == "__main__":
   app = QApplication(sys.argv)
#======================================================================================#
#------------------------- CARGAR ESTILOS GLOBALES QSS EN GUI -------------------------#
#======================================================================================#
   try:
       with open("estilos.qss", "r") as f:
           app.setStyleSheet(f.read())
   except:
       print("No se encontró el archivo estilos.qss, se usará estilo por defecto")
   gui = DetectorGUI()
   gui.show()
   sys.exit(app.exec())
#======================================================================================#
#--------------------------------------------------------------------------------------#
#======================================================================================#
