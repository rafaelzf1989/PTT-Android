from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.properties import StringProperty, ColorProperty
from kivy.core.window import Window
import socket
import threading

# --- Configuración ---
PORT = 5001

class PTTClientLayout(BoxLayout):
    status_text = StringProperty("Desconectado")
    indicator_color = ColorProperty([0.5, 0.5, 0.5, 1])  # Gris
    is_connected = False
    client_socket = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 20
        self.spacing = 15

        # --- Sección de Conexión ---
        conn_layout = GridLayout(cols=2, size_hint_y=None, height=50, spacing=10)
        conn_layout.add_widget(Label(text="IP del PC:", size_hint_x=0.3))
        self.ip_input = TextInput(text="192.168.1.100", multiline=False, input_filter='float')
        conn_layout.add_widget(self.ip_input)
        self.add_widget(conn_layout)

        self.connect_btn = Button(text="Conectar", size_hint_y=None, height=50, background_color=(0.2, 0.6, 0.8, 1))
        self.connect_btn.bind(on_press=self.toggle_connection)
        self.add_widget(self.connect_btn)

        self.status_label = Label(text=self.status_text, size_hint_y=None, height=30)
        self.add_widget(self.status_label)

        # --- Indicador Visual ---
        self.indicator_widget = Label(
            text="ESPERANDO",
            font_size='20sp',
            bold=True,
            color=(1, 1, 1, 1)
        )
        # Usamos un canvas para cambiar el color de fondo fácilmente
        with self.indicator_widget.canvas.before:
            from kivy.graphics import Color, Rectangle
            self.ind_color = Color(0.5, 0.5, 0.5, 1)
            self.ind_rect = Rectangle(pos=self.indicator_widget.pos, size=self.indicator_widget.size)
        self.indicator_widget.bind(pos=self.update_rect, size=self.update_rect)
        self.add_widget(self.indicator_widget)
        self.bind(indicator_color=self.update_indicator_color)

        # --- Botón PTT (Push-To-Talk) ---
        self.ptt_btn = Button(
            text="MANTENER PARA HABLAR",
            font_size='18sp',
            bold=True,
            background_color=(0.8, 0.2, 0.2, 1) if not self.is_connected else (0.2, 0.7, 0.2, 1),
            disabled=True
        )
        self.ptt_btn.bind(on_press=self.ptt_start)
        self.ptt_btn.bind(on_release=self.ptt_stop)
        self.add_widget(self.ptt_btn)

    def update_rect(self, instance, value):
        self.ind_rect.pos = instance.pos
        self.ind_rect.size = instance.size

    def update_indicator_color(self, instance, value):
        self.ind_color.rgba = value

    def toggle_connection(self, instance):
        if self.is_connected:
            self.disconnect()
        else:
            self.connect()

    def connect(self):
        ip = self.ip_input.text.strip()
        if not ip:
            self.status_text = "Por favor, ingresa una IP válida."
            return
        
        self.status_text = f"Conectando a {ip}:{PORT}..."
        self.connect_btn.disabled = True
        
        # La conexión se intenta en un hilo para no bloquear la UI
        threading.Thread(target=self._connect_thread, args=(ip,), daemon=True).start()

    def _connect_thread(self, ip):
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.settimeout(5)
            self.client_socket.connect((ip, PORT))
            self.client_socket.settimeout(None) # Vuelve al modo bloqueante para recibir
            self.is_connected = True
            Clock.schedule_once(lambda dt: self.on_connected_success(), 0)
            # Inicia el hilo de escucha de ACKs del servidor
            threading.Thread(target=self.listen_for_responses, daemon=True).start()
        except Exception as e:
            Clock.schedule_once(lambda dt: self.on_connected_error(str(e)), 0)

    def on_connected_success(self):
        self.status_text = "✅ Conectado al servidor"
        self.connect_btn.text = "Desconectar"
        self.connect_btn.background_color = (0.8, 0.2, 0.2, 1)
        self.connect_btn.disabled = False
        self.ptt_btn.disabled = False
        self.ptt_btn.background_color = (0.2, 0.7, 0.2, 1)

    def on_connected_error(self, error_msg):
        self.status_text = f"❌ Error de conexión: {error_msg}"
        self.connect_btn.disabled = False
        self.is_connected = False
        if self.client_socket:
            self.client_socket.close()

    def disconnect(self):
        self.is_connected = False
        if self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass
        self.client_socket = None
        self.status_text = "Desconectado"
        self.connect_btn.text = "Conectar"
        self.connect_btn.background_color = (0.2, 0.6, 0.8, 1)
        self.ptt_btn.disabled = True
        self.ptt_btn.background_color = (0.5, 0.5, 0.5, 1)
        self.indicator_color = [0.5, 0.5, 0.5, 1] # Gris

    def ptt_start(self, instance):
        if self.is_connected and self.client_socket:
            try:
                self.client_socket.sendall(b"PTT_START")
                self.indicator_color = [0.8, 0.2, 0.2, 1] # Rojo
                self.indicator_widget.text = "TRANSMITIENDO"
            except Exception as e:
                self.status_text = f"Error al enviar: {e}"
                self.disconnect()

    def ptt_stop(self, instance):
        if self.is_connected and self.client_socket:
            try:
                self.client_socket.sendall(b"PTT_STOP")
                self.indicator_color = [0.5, 0.5, 0.5, 1] # Gris
                self.indicator_widget.text = "ESPERANDO"
            except Exception as e:
                self.status_text = f"Error al enviar: {e}"
                self.disconnect()

    def listen_for_responses(self):
        while self.is_connected:
            try:
                data = self.client_socket.recv(1024)
                if not data:
                    break
                # Podríamos verificar si es "ACK", pero no es crítico para el flujo
            except:
                break
        # Si salimos del bucle, la conexión se perdió
        if self.is_connected:
            Clock.schedule_once(lambda dt: self.on_connection_lost(), 0)

    def on_connection_lost(self):
        self.status_text = "❌ Conexión perdida con el servidor"
        self.disconnect()


class PTTClientApp(App):
    def build(self):
        Window.clearcolor = (0.1, 0.1, 0.1, 1) # Fondo oscuro
        return PTTClientLayout()

if __name__ == '__main__':
    PTTClientApp().run()
