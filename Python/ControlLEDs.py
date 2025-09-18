#ControlLEDs.py
#======================================================================================#
#--------------------------------------------------------------------------------------#
#============================== IMPORTACIÓN DE LIBRERIAS ==============================#
import time
from gpiozero import LED
#======================================================================================#
#--------------------------------------------------------------------------------------#
#============================== CLASE QUE CONTROLA LEDS ===============================#
class ControlLEDs:
                       #========== ASIGNACIÓN DE PINES ==========#
   def __init__(self, pin_rojo=17, pin_amarillo=27, pin_verde=22):
       #========== INICIALIZAR LEDS ===========#
       self.led_rojo = LED(pin_rojo)
       self.led_amarillo = LED(pin_amarillo)
       self.led_verde = LED(pin_verde)
       # === VARIABLES DE PARPADEO AMARILLO ===#
       self.ultimo_cambio_amarillo = 0
       self.estado_led_amarillo = False
       self.parpadeo_amarillo_activo = False
       self.contador_parpadeo = 0
       self.parpadeos_max = 6
#======================================================================================#
#--------------------------------------------------------------------------------------#
#=========================== ENCENDIDO Y APAGADO DE LEDS ==============================#
   def encender_rojo(self):
       self.led_rojo.on()
   def apagar_rojo(self):
       self.led_rojo.off()
   def encender_verde(self):
       self.led_verde.on()
   def apagar_verde(self):
       self.led_verde.off()
   def encender_amarillo(self):
       self.led_amarillo.on()
   def apagar_amarillo(self):
       self.led_amarillo.off()
#======================================================================================#
#--------------------------------------------------------------------------------------#
#=========================== LÓGICA DE SEMÁFORO PRINCIPAL =============================#
   # ENCENDER EL LED ROJO,
   # SÓLO *SI NO* ESTÁ ACTIVO
   # EL PARPADEO DE LED AMARILLO
   def semaforo_rojo(self):
       self.led_rojo.on()
       self.led_verde.off()
       if not self.parpadeo_amarillo_activo:
           self.led_amarillo.off()

   # ENCENDER EL LED VERDE,
   # SÓLO *SI NO* ESTÁ ACTIVO
   # EL PARPADEO DE LED AMARILLO
   def semaforo_verde(self):
       self.led_verde.on()
       self.led_rojo.off()
       if not self.parpadeo_amarillo_activo:
           self.led_amarillo.off()
#======================================================================================#
#--------------------------------------------------------------------------------------#
#========================= LÓGICA DE PARPADEO LED AMARILLO ============================#
   def iniciar_parpadeo_amarillo(self, n_parpadeos=3):
       self.parpadeo_amarillo_activo = True
       self.contador_parpadeo = 0
       self.parpadeos_max = n_parpadeos * 2

   def detener_parpadeo_amarillo(self):
       self.parpadeo_amarillo_activo = False
       self.apagar_amarillo()

   def actualizar_parpadeo_amarillo(self):
       """Llamar cada frame desde el loop principal"""
       if not self.parpadeo_amarillo_activo:
           return

       ahora = time.time()
       if ahora - self.ultimo_cambio_amarillo >= 0.5:  # cambiar cada 500 ms
           self.estado_led_amarillo = not self.estado_led_amarillo
           if self.estado_led_amarillo:
               self.encender_amarillo()
           else:
               self.apagar_amarillo()

           self.contador_parpadeo += 1
           self.ultimo_cambio_amarillo = ahora

           if self.contador_parpadeo >= self.parpadeos_max:
               self.parpadeo_amarillo_activo = False
               self.apagar_amarillo()
#======================================================================================#
#--------------------------------------------------------------------------------------#
#============================== APAGAR TODOS LOS LEDS =================================#
   def apagar_todos(self):
       self.led_rojo.off()
       self.led_amarillo.off()
       self.led_verde.off()
#======================================================================================#
#--------------------------------------------------------------------------------------#
#======================================================================================#
