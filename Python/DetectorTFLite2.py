#DetectorTFLite2.py
#======================================================================================#
#------------------------------ IMPORTACIÓN DE LIBRERIAS ------------------------------#
#======================================================================================#
import cv2
import numpy as np
import tflite_runtime.interpreter as tflite
import time
import matplotlib.pyplot as plt
#======================================================================================#
#--------------------------- IMPORTACIÓN DE MÓDULOS LOCALES ---------------------------#
#======================================================================================#
from ControlLEDs import ControlLEDs
from ControlOLED import ControlOLED
#======================================================================================#
#------------------------------ CLASE DETECTOR TFLITE V2 ------------------------------#
#======================================================================================#
class DetectorTFLite2:
   def __init__(self, leds: ControlLEDs, oled: ControlOLED,
                model_path="model_tflite/best_float32.tflite"): #MODELO YOLO EN TFLITE
#======================================================================================#
#------------------------------ CONFIGURACIONES GENERALES -----------------------------#
#======================================================================================#
       """ CONTROL MANUAL DE HISTOGRAMA, ECUALIZCIÓN Y FPS """
       self.ENABLE_HISTOGRAM = False
       self.ENABLE_EQUALIZATION = False
       self.ENABLE_FPS = True

       """ CONTROL DE LEDS AL HABER DETECCIÓN O NO """
       self.RED_DURATION = 15 # TIEMPO EN SEGUNDO PARA LED ROJO
       self.YELLO_PARPADEO = 3 # NÚMERO TOTAL DE PARPADEOS PARA LED AMARILLO

       """ CONTROL MANUAL DEL UMBRAL DE CONFIANZA PARA DETECCIÓN """
       self.confidence_threshold = 0.9  # SE PUEDE CONTROLAR TAMBIÉN DESDE LA INTERFAZ

       """ OBJETOS DE CONTROL """
       self.leds = leds
       self.oled = oled
       self.model_path = model_path

       """ ÚLTIMA DETECCIÓN REGISTRADA (LABEL, CONFIANZA) """
       self.ultima_deteccion = None

       """ REFRESCAR HISTOGRAMA """
       plt.ion()
#======================================================================================#
#------------------------------ CARGAR MODELO YOLO-TFLITE -----------------------------#
#======================================================================================#
       self.interpreter = tflite.Interpreter(model_path=self.model_path)
       self.interpreter.allocate_tensors()

       self.input_details = self.interpreter.get_input_details()
       self.output_details = self.interpreter.get_output_details()

       self.input_index = self.input_details[0]['index']
       self.output_index = self.output_details[0]['index']

       #input_shape = self.input_details[0]['shape']
       #self.model_height = input_shape[1]
       #self.model_width = input_shape[2]
       self.input_shape = self.input_details[0]['shape']
       self.model_height = self.input_shape[1]
       self.model_width = self.input_shape[2]
#======================================================================================#
#------------------------------ CONFIGUACIÓN DE LA CÁMARA -----------------------------#
#======================================================================================#
       self.cap = cv2.VideoCapture(0)
       if not self.cap.isOpened():
           raise RuntimeError("No se pudo abrir la cámara USB. Verificar conexión")
#======================================================================================#
#-------------------------------- VARIABLES DE ESTADO ---------------------------------#
#======================================================================================#
       self.prev_time = 0
       self.red_active = False
       self.red_start_time = 0
       self.status = "Inicializando"
       self.color = (255, 255, 255)
       self.fps = 0
       self.remaining = 0
#======================================================================================#
#------------------------------ FUNCIÓN DE ECUALIZACIÓN -------------------------------#
#======================================================================================#
   def ecualizar(self, frame):
       yuv = cv2.cvtColor(frame, cv2.COLOR_BGR2YUV)
       yuv[:,:,0] = cv2.equalizeHist(yuv[:,:,0])
       return cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR)
#======================================================================================#
#------------------------------- FUNCIÓN DEL HISTOGRAMA -------------------------------#
#======================================================================================#
   def _mostrar_histograma_inline(self, frame_bgr):

       """Versión simple: crea/refresca una figura única con plt.pause()."""
       gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
       hist = cv2.calcHist([gray], [0], None, [256], [0, 256])

       plt.figure("Histograma de Intensidad", figsize=(8, 5))
       plt.clf()
       plt.title("Histograma (escala de grises)")
       plt.xlabel("Intensidad (0 - 255)")
       plt.ylabel("Número de píxeles")
       plt.plot(hist, color='black')
       plt.xlim([0, 256])
       plt.grid(True, linestyle="--", alpha=0.5)
       plt.pause(0.001)  # refresco no bloqueante
#======================================================================================#
#------------------------- FUNCIÓN DE PROCESAMIENTO DE FRAMES -------------------------#
#======================================================================================#
   """ PROCESAR UN FRAME """
   def procesar_frame(self):
       ret, frame = self.cap.read()
       if not ret:
           return None

       """ ECUALIZACIÓN """
       frame_eq = self.ecualizar(frame) if self.ENABLE_EQUALIZATION else frame.copy()

       """ HISTOGRAMA (inline, sin clases externas) """
       if self.ENABLE_HISTOGRAM:
           self._mostrar_histograma_inline(frame_eq)

       """ PREPROCESAMIENTO Y DETECCIÓN """
       resized = cv2.resize(frame_eq, (self.model_width, self.model_height))
       normalized = resized / 255.0
       input_tensor = np.expand_dims(normalized.astype(np.float32), axis=0)

       self.interpreter.set_tensor(self.input_index, input_tensor)
       self.interpreter.invoke()
       output = self.interpreter.get_tensor(self.output_index)
       output = np.squeeze(output).T

       threshold = self.confidence_threshold
       detecciones_validas = output[output[:, 4] > threshold]

       current_time = time.time()
       self.leds.actualizar_parpadeo_amarillo()
#======================================================================================#
#---------------------------- LÓGICA DE DETECCIÓN EN VIVO -----------------------------#
#======================================================================================#
       if not self.red_active and len(detecciones_validas) > 0:
           self.leds.iniciar_parpadeo_amarillo(3)
           self.status = "Persona detectada"
           self.color = (0, 255, 0)
           self.red_active = True
           self.red_start_time = current_time
           self.oled.mostrar_icono("icono_wheel1.png", self.RED_DURATION)

       elif self.red_active:
           elapsed = current_time - self.red_start_time
           self.remaining = int(self.RED_DURATION - elapsed)
           if elapsed >= self.RED_DURATION:
               self.leds.iniciar_parpadeo_amarillo(3)
               self.status = "No hay deteccion"
               self.color = (0, 0, 255)
               self.oled.mostrar_texto("AVANCE", x=5, y=20, size=30)
               self.red_active = False
           else:
               self.status = "Persona detectada"
               self.color = (0, 255, 0)
               self.leds.semaforo_rojo()
               self.remaining = max(0, int(self.RED_DURATION - elapsed))
               self.oled.mostrar_icono("icono_wheel1.png", self.remaining)
       else:
           self.status = "No hay deteccion"
           self.color = (0, 0, 255)
           self.leds.semaforo_verde()
           self.oled.mostrar_texto("AVANCE", x=5, y=20, size=30)

       if self.red_active and not self.leds.parpadeo_amarillo_activo:
           self.leds.semaforo_rojo()
       elif not self.red_active and not self.leds.parpadeo_amarillo_activo:
           self.leds.semaforo_verde()
#======================================================================================#
#------------------------------ BOUNDING BOXES POR FRAME ------------------------------#
#======================================================================================#
       boxes = []
       scores = []
       for det in detecciones_validas:
           x, y, w, h, score = det
           x1 = int((x - w / 2) * frame.shape[1])
           y1 = int((y - h / 2) * frame.shape[0])
           x2 = int((x + w / 2) * frame.shape[1])
           y2 = int((y + h / 2) * frame.shape[0])

           x1 = max(0, x1); y1 = max(0, y1)
           x2 = min(frame.shape[1], x2); y2 = min(frame.shape[0], y2)

           boxes.append([x1, y1, x2 - x1, y2 - y1])
           scores.append(float(score))

       self.ultima_deteccion = None

       indices = cv2.dnn.NMSBoxes(boxes, scores, score_threshold=threshold,
                                   nms_threshold=0.4)
       if len(indices) > 0:

           # Tomamos la detección con mayor confianza
           best_idx = max(indices.flatten(), key=lambda i: scores[i])
           best_score = scores[best_idx]

           #Guardar la última detección para la GUI
           self.ultima_deteccion = ("Persona", best_score)

           for i in indices.flatten():
               x, y, w, h = boxes[i]
               score = scores[i]
               cv2.rectangle(frame_eq, (x, y), (x + w, y + h), self.color, 2)
               label = f"{score:.2f}"
               cv2.putText(frame_eq, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX,
                           0.5, self.color, 2)
#======================================================================================#
#----------------------------- MUESTRA DE FPS EN PANTALLA -----------------------------#
#======================================================================================#
       if self.ENABLE_FPS:
           curr_time = time.time()
           self.fps = 1 / (curr_time - self.prev_time) if self.prev_time > 0 else 0
           self.prev_time = curr_time

       # Caja de estado
       cv2.rectangle(frame_eq, (10, 10), (250, 50), (0, 0, 0), -1)
       cv2.putText(frame_eq, self.status, (10, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                   self.color, 2)

       if self.ENABLE_FPS:
           cv2.rectangle(frame_eq, (10, 55), (130, 90), (0, 0, 0), -1)
           cv2.putText(frame_eq, f"FPS: {self.fps:.2f}", (10, 80),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

       return frame_eq
#======================================================================================#
#----------------------------- DETENER Y LIMPIAR SISTEMA ------------------------------#
#======================================================================================#
   def detener(self):
       self.cap.release()
       cv2.destroyAllWindows()
       # No cerramos figuras explícitamente: plt.ion() + cierre de app es suficiente
       self.leds.apagar_todos()
       self.oled.limpiar()
       self.oled.apagar()
       print("Recursos liberados y hardware apagado")
#======================================================================================#
#--------------------------------------------------------------------------------------#
#======================================================================================#
