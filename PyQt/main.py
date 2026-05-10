'''

'''

import sys, os
import config_manager
os.environ['VLC_VERBOSE'] = '-1'
import vlc
os.environ["PATH"] = os.path.dirname(__file__) + os.pathsep + os.environ["PATH"]

import mpv
from config_manager import settings
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QMessageBox, QFileDialog,
    QDialog, QWidget, QTableWidgetItem, QAbstractItemView
    )
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtCore import QUrl, QSize, Qt
from PyQt5 import uic
from PyQt5.QtGui import QPixmap, QTransform
from PIL import Image
from io import BytesIO
from componentes.controles import ScrollableMessageBox, SpinnerOverlay
from componentes.dialogo_cantidad import DialogoSeleccionCantidad
from componentes.video_player_vlc import VideoPlayer
from config_paths import (
    get_ruta_mapa_html, get_ruta_ui, ruta_json_unico, 
    get_ruta_principal, get_ruta_miniaturas, extensiones_validas,
    get_ruta_logo, ruta_movil
    )
from worker.mapa_worker import MapaWorker
from worker.copia_worker import CopiaWorker
from bridge.bridge import Bridge
from copia_clasificador_fotos import obtener_archivos, cargar_json_unico, calcular_hash_md5
from componentes.dialogo_configuracion import ConfigDialog
from pagina_estadistica.pagina_estadistica import PaginaEstadisticas

ARCHIVOS_SEL = {}  # clave: ruta_archivo, valor: hash_archivo
NUM_COLS = 7

class MapaWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.ui = uic.loadUi(get_ruta_ui())
        self.ui.showMaximized()

        # Referenciar al VideoPlayer abierto
        self.vp = None

        self.ruta_clasificacion = None
        self.miniaturas = True

        # VLC Player
        self.vlc_instance = vlc.Instance()
        self.vlc_player = self.vlc_instance.media_player_new()

        # Crear un contenedor para el widget de MPV
        self.mpv_container = QWidget(self.ui.labelVisor)
        self.mpv_container.setGeometry(self.ui.labelVisor.rect())
        self.mpv_container.hide()

        # Crear instancia MPV embebida en el labelVisor
        self.mpv_player = mpv.MPV(
            wid=str(int(self.mpv_container.winId())),
            vo='gpu', # salida de video moderna
            hwdec='auto', # aceleración por hardware
            log_handler=None, # sin logs molestos
            ytdl=False
        )

        # Visor web
        self.view = QWebEngineView()
        # Mostramos el mapa o el logo.
        ruta_mapa = get_ruta_mapa_html()
        ruta_logo = get_ruta_logo()

        mostrar = ruta_mapa if os.path.exists(ruta_mapa) else ruta_logo

        self.view.load(QUrl.fromLocalFile(os.path.abspath(mostrar)))

        # Canal web
        self.channel = QWebChannel()
        self.bridge = Bridge(
            self.ui.tableWidget,
            self.ui.tableClasificacion,
            self.ui.labelFechaListado,
            self.ui.labelArchivosSeleccionadosClasificacion,
            self.ui.labelMapaActualizado,
            self.ui.button_generar_mapa,
            self.ui.button_sel_multiple,
            self.view,
            self.ui.labelVisor,
            ruta_json_unico(),
            self.set_mapa_habilitado,
            self.contar_pendientes,
        )
        self.bridge.enviarListaArchivos.connect(self.recibir_archivos_para_clasificacion)
        self.channel.registerObject("bridge", self.bridge)
        self.view.page().setWebChannel(self.channel)

        # Inicializar el config.ini.
        self.iniciar_config_ini()

        # Estado del mapa (actualizado o NO)
        self.mapa_actualizado = None
        mapa_ok = settings.value("Estado/mapa_generado") == "True"
        self.set_mapa_habilitado(mapa_ok) # También se actualiza 'Pendientes' al abrir

        # Señales
        self.bridge.actualizarFoto.connect(self.mostrar_foto)
        self.bridge.pendientes_actualizados.connect(self.actualizar_menu_pendientes)

        # Insertar visor web en el layout
        layout = QVBoxLayout(self.ui.QWidget_foto)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.addWidget(self.view)

        # Inicializar tabla de clasificación.
        self.tableClasificacion = self.ui.tableClasificacion
        
        self.tableClasificacion.setIconSize(QSize(150, 150))
        self.tableClasificacion.setShowGrid(False)
        self.tableClasificacion.setSelectionMode(QAbstractItemView.NoSelection)
        self.tableClasificacion.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tableClasificacion.setFocusPolicy(Qt.NoFocus)
        self.tableClasificacion.setAlternatingRowColors(False)
        self.tableClasificacion.verticalHeader().setVisible(False)
        self.tableClasificacion.horizontalHeader().setVisible(False)
        self.tableClasificacion.setStyleSheet("""
            QTableWidget {
                background: white;
                border: none;
            }
            QTableWidget::item {
                border: none;
                padding: 5px;
            }
            QTableWidget::item:hover {
                background: #f0f0f0;
                border-radius: 8px;
            }
        """)

        self.contar_pendientes()

        # ----------------------------------------
        # CONECTAR WIDGET A LA VISTA CLASIFICACION
        # ----------------------------------------       
        self.btnMiniaturas = self.ui.button_miniaturas_clasificacion
        self.btnLista = self.ui.button_lista_clasificacion

        self.btnMoverClasificacion = self.ui.button_mover_clasificacion
        self.btnCopiarClasificacion = self.ui.button_copiar_clasificacion
        self.btnCompartirClasificacion = self.ui.button_compartir_clasificacion
        self.btnBorrarClasificacion = self.ui.button_eliminar_clasificacion
        self.btnSeleccionarClasificacion = self.ui.button_seleccionar_todos_clasificacion
        self.labelCarpetaOrigen = self.ui.labelFechaListadoClasificacion
        self.labelArSelClasificacion = self.ui.labelArchivosSeleccionadosClasificacion

        self.tableClasificacion.setColumnCount(NUM_COLS)

        for c in range(NUM_COLS):
            self.tableClasificacion.setColumnWidth(c, 180)

        # Acceder al stacked.
        self.stacked = self.ui.stackedWidget
        self.pagina_estadistica = PaginaEstadisticas()
        layout = QVBoxLayout(self.ui.pageEstadistica)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.pagina_estadistica)

        indice = int(config_manager.settings.value("General/pantalla"))
        self.cambiar_vista(indice)

        self.signs_controls()

    def show(self):
        self.ui.show()

    def cambiar_vista(self, indice):
        if self.ruta_clasificacion == None and indice == 1: indice = 0
        self.chk_value = False

        self.stacked.setCurrentIndex(indice)
        self.bridge.set_vista(indice)
        
        config_manager.settings.setValue("General/pantalla", str(indice))
        config_manager.settings.sync()

        if indice == 0:
            mapa_ok = settings.value("Estado/mapa_generado") == "True"
            self.set_mapa_habilitado(mapa_ok)

        elif indice == 1:
            self.ui.actionDesde_Movil.setEnabled(False)
            self.ui.actionClasificar.setEnabled(False)
            self.labelCarpetaOrigen.setText(self.ui.labelFechaListado.text())
            self.bridge.cargar_galeria(self.ruta_clasificacion, self.miniaturas, 100)

        elif indice == 2:
            self.ui.actionDesde_Movil.setEnabled(False)
            self.ui.actionClasificar.setEnabled(False)

    def recibir_archivos_para_clasificacion(self, ruta):
        if not ruta:
            return
        self.ruta_clasificacion = ruta

    def setMiniatura(self, valor, tamano=100):
        self.miniaturas = valor
        self.bridge.cargar_galeria(self.ruta_clasificacion, self.miniaturas, tamano)

    def seleccion_multiple_clasificacion(self):
        nueva_visibilidad = False
        table = self.tableClasificacion
        columna = self.tableClasificacion.columnCount()
        num_filas = self.tableClasificacion.rowCount()
        self.chk_value = not self.chk_value
        state = self.chk_value

        for columna in range(columna):
            self.checked_unchecked_all_checkbox(
                nueva_visibilidad, table, columna, num_filas, state
            )

    # ============================================================
    # HABILITAR APLICACIÓN
    # ============================================================ 
    def set_mapa_habilitado(self, habilitado):
        # Deshabilitar el visor del mapa.
        self.view.setEnabled(habilitado)

        # Deshabilitar acciones del menú.
        self.ui.actionDesde_Movil.setEnabled(habilitado)
        self.ui.actionClasificar.setEnabled(habilitado)
        # Actualizamos el habilitado de 'Pendientes' por separado.
        self.bridge.cargar_pendientes()
        self.ui.actionPendientes.setEnabled(habilitado)

        self.ui.menuFiltro.setEnabled(habilitado)
        self.ui.menuMarcas.setEnabled(habilitado)

        if habilitado:
            self.ui.labelMapaActualizado.setText("Mapa actualizado")
            self.ui.labelMapaActualizado.setStyleSheet("color: green; font-weight: bold;")        
            self.ui.button_generar_mapa.setVisible(False)
            self.mapa_actualizado = True
        else:
            self.ui.labelMapaActualizado.setText("Mapa desactualizado")
            self.ui.labelMapaActualizado.setStyleSheet("color: red; font-weight: bold;")        
            self.ui.button_generar_mapa.setVisible(True)
            self.mapa_actualizado = False

    # ============================================================
    # GENERAR MAPA MANUALMENTE
    # ============================================================ 
    def generar_mapa_manual(self):
        self.mapa_actualizado = True

        self.ui.labelMapaActualizado.setText("Generando mapa...")
        self.ui.labelMapaActualizado.setStyleSheet("color: orange; font-weight: bold;")

        self.ui.button_generar_mapa.setVisible(False)

        self.spinner = SpinnerOverlay(self.view, "Generando mapa...")
        self.spinner.show()

        self.worker_mapa = MapaWorker()
        self.worker_mapa.pendientes_actualizados.connect(self.bridge._reenviar_pendientes)
        self.worker_mapa.terminado.connect(self.mapa_finalizado)
        self.worker_mapa.start()

    # ============================================================
    # MOSTRAR FOTO O VIDEO
    # ============================================================
    def mostrar_foto(self, item=None):
        if isinstance(item, QTableWidgetItem):
            row = item.row()
            ruta_archivo = self.ui.tableWidget.item(row, 2).text()
        else:
            if isinstance(item, str):
                ruta_archivo = item
            else:
                row = self.ui.tableWidget.currentRow()
                if row < 0:
                    return
                ruta_archivo = self.ui.tableWidget.item(row, 2).text()

        if not ruta_archivo:
            return
        
        extension = ruta_archivo.lower().split(".")[-1]

        # Imagen
        if extension in ["jpg", "jpeg", "png", "bmp", "gif"]:
            self.vlc_player.stop()
            self.mostrar_imagen(ruta_archivo)
            return
        
        # Video
        if extension in ["mp4", "avi", "mkv", "mov", "mts"]:
            self.mostrar_video(ruta_archivo)
            return
        
        print("Tipo de archivo no soportado: ", ruta_archivo)

    def mostrar_imagen(self, ruta_archivo):
        # Pausar MPV si estaba reproduciendo
        try:
            self.mpv_player.pause = True
        except:
            pass

        self.mpv_container.hide()

        img = Image.open(ruta_archivo)
        exif = img.getexif()

        orientacion = exif.get(274, 1)

        pixmap = QPixmap(ruta_archivo)
        transform = QTransform()
        if orientacion == 3:
            transform.rotate(180)
        elif orientacion == 6:
            transform.rotate(90)
        elif orientacion == 8:
            transform.rotate(270)

        pixmap = pixmap.transformed(transform)
        
        if not pixmap.isNull():
            self.ui.labelVisor.setPixmap(pixmap)
            self.ui.labelVisor.setScaledContents(True)

    def mostrar_video(self, ruta_archivo):
        # Limpiar imagen previa.
        self.ui.labelVisor.clear()
        self.mpv_container.show()

        @self.mpv_player.property_observer('time-pos')
        def time_observer(_name, value):
            if value is not None and value >=5:
                self.mpv_player.pause = True

        # Reproducir con MPV
        self.mpv_player.pause = False
        self.mpv_player.play(ruta_archivo)

    def ver_video(self, row, column):
        if self.bridge.vista_actual == 0: # Tabla Principal
            ruta_archivo = self.ui.tableWidget.item(row, 2).text()
            datos = self.ui.labelFechaListado.text()

        elif self.bridge.vista_actual == 1: # Tabla Clasificación
            widget = self.tableClasificacion.cellWidget(row, column)
            if widget is None:
                return
            ruta_archivo = widget.ruta
            datos = self.labelCarpetaOrigen.text()
        
        # Pausar MPV
        try:
            self.mpv_player.pause = True
        except:
            pass

        # Si hay un reproductos abierto lo cerramos
        if self.vp is not None:
            self.vp.close()
            self.vp = None

        # Creamos uno nuevo.
        self.vp = VideoPlayer(ruta_archivo, datos)
        self.vp.show()

    def resizeEvent(self, a0):
        ancho = self.tableClasificacion.width()
        col_width = 180
        num_cols = max(1, ancho // col_width)

        self.tableClasificacion.setColumnCount(num_cols)
        for c in range(num_cols):
            self.tableClasificacion.setColumnWidth(c, col_width)

        super().resizeEvent(a0)
        self.mpv_container.setGeometry(self.ui.labelVisor.rect())

    # ============================================================
    # COLUMNA SELECCIÓN
    # ============================================================
    def columna_seleccion(self):
        ARCHIVOS_SEL.clear()
        table = self.ui.tableWidget
        columna = 0
        columna_oculta = table.isColumnHidden(columna)
        num_filas = table.rowCount()

        if not columna_oculta:
            nueva_visibilidad = True
            ancho_columna_1 = 205
        elif num_filas > 8:
            nueva_visibilidad = False
            ancho_columna_1 = 135
        else:
            nueva_visibilidad = False
            ancho_columna_1 = 155

        table.setColumnHidden(columna, nueva_visibilidad)
        table.setColumnWidth(1, ancho_columna_1)

        self.checked_unchecked_all_checkbox(
            nueva_visibilidad, table, columna, num_filas, False
        )

    def checked_unchecked_all_checkbox(self, nueva_visibilidad, table, columna, num_filas, state):
        if not nueva_visibilidad:
            for fila in range(num_filas):
                celda = table.cellWidget(fila, columna)
                if celda is not None:
                    layout = celda.layout()
                    if layout is not None and layout.count() > 0:
                        checkbox = layout.itemAt(0).widget()
                        if checkbox is not None:
                            checkbox.setChecked(state)

    # ============================================================
    # COPIA DESDE MÓVIL
    # ============================================================
    def select_movil(self):
        #carpeta = ruta_movil()
        archivos = obtener_archivos()

        total = len(archivos)
        
        if total == 0:
            QMessageBox.warning(self, "Sin archivos", "No se encontraron archivos para clasificar.")
            return

        # 2️⃣ Mostrar diálogo de selección
        dlg = DialogoSeleccionCantidad(total, self)
        if dlg.exec_() != QDialog.Accepted:
            return
        
        seleccion = dlg.obtener_resultado()

        # 3️⃣ Pasar parámetros al Bridge
        self.bridge.iniciar_clasificacion(
            None,
            seleccion["modo"],
            seleccion["inicio"],
            seleccion["fin"]
            )
        
        config_manager.settings.setValue("Estado/ultimo_intervalo", f"{seleccion['inicio']}-{seleccion['fin']}")
        config_manager.settings.sync()

    def iniciar_copia(self, carpeta_origen=None):
        self.spinner = SpinnerOverlay(self, "Clasificando archivos...")
        self.spinner.show()

        self.worker_copia = CopiaWorker(carpeta_origen)
        self.worker_copia.terminado.connect(self.copia_finalizada)
        self.worker_copia.start()

    def copia_finalizada(self, mensaje):
        self.spinner.movie.stop()
        self.spinner.close()

        if mensaje == '':
            return

        ancho, alto = self.analizar_mensaje(mensaje)
        num_copiados = alto
        ancho = min(500, 7 * ancho)
        alto = min(600, 18 * alto)

        if mensaje:
            dlg = ScrollableMessageBox(f"Copia de Archivos: {num_copiados} archivos copiados", mensaje)
        else:
            dlg = ScrollableMessageBox("Copia de Archivos", "No se pudo realizar la copia.")
        dlg.resize(ancho, alto)
        dlg.exec_()

        if num_copiados > 0:
            self.spinner = SpinnerOverlay(self, "Generando el mapa...")
            self.spinner.show()

            self.worker_mapa = MapaWorker()
            self.worker_mapa.pendientes_actualizados.connect(self.bridge._reenviar_pendientes)
            self.worker_mapa.terminado.connect(self.mapa_finalizado)
            self.worker_mapa.start()

    def mapa_finalizado(self):
        self.spinner.movie.stop()
        self.spinner.close()
        self.view.load(QUrl.fromLocalFile(os.path.abspath(f"{get_ruta_mapa_html()}")))
        QMessageBox.information(self, "Mapa actualizado", "El mapa ha sido generado correctamente.")

        config_manager.settings.setValue("Estado/mapa_generado", "True")
        config_manager.settings.sync()        

        self.set_mapa_habilitado(True)

        self.contar_pendientes()

    # ============================================================
    # CLASIFICAR ARCHIVOS
    # ============================================================
    def clasificar_archivos(self):
        # El usuario elige una carpeta y se lanza la clasificación.
        ultima_carpeta = settings.value("General/ultima_origen")
        carpeta = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta para clasificar", ultima_carpeta)
        if not carpeta:
            return
        
        # 1️⃣ Obtener lista de archivos
        archivos = obtener_archivos(carpeta)
        total = len(archivos)

        if total == 0:
            QMessageBox.warning(self, "Sin archivos", "No se encontraron archivos para clasificar.")
            return
        
        # 2️⃣ Mostrar diálogo de selección
        dlg = DialogoSeleccionCantidad(total, self)
        if dlg.exec_() != QDialog.Accepted:
            return
        
        seleccion = dlg.obtener_resultado()

        # 3️⃣ Pasar parámetros al Bridge
        self.bridge.iniciar_clasificacion(
            carpeta,
            seleccion["modo"],
            seleccion["inicio"],
            seleccion["fin"]
            )
        
        config_manager.settings.setValue("Estado/ultimo_intervalo", f"{seleccion['inicio']}-{seleccion['fin']}")
        config_manager.settings.sync()

    # ============================================================
    # CLASIFICAR PENDIENTES
    # ============================================================
    def clasificar_pendientes(self):
        # 1️⃣ Actualizar contador de pendientes
        self.bridge.cargar_pendientes()

        # 2️⃣ Ruta de la carpeta de pendientes (Sin_GPS)
        ruta_pendientes = os.path.join(get_ruta_principal(), "(Sin_GPS)(Sin_GPS)(0000-00)")

        if not os.path.isdir(ruta_pendientes):
            QMessageBox.warning(self, "Pendientes", f"No existe la carpeta de pendientes:\n{ruta_pendientes}")
            return
        
        # 3️⃣ Decirle al Bridge que esa es la carpeta actual
        self.bridge.recibirRuta(ruta_pendientes)

    def contar_pendientes(self):
        data = cargar_json_unico(ruta_json_unico())
        total_pendientes = data["stats"]["total_pendientes"]
        self.actualizar_menu_pendientes(total_pendientes)

    def contar_clasificados(self):
        data = cargar_json_unico(ruta_json_unico())
        return data["stats"]["total_clasificados"]

    # ============================================================
    # MENÚ PENDIENTES
    # ============================================================
    def actualizar_menu_pendientes(self, total):
        self.ui.actionPendientes.setText(f'Pendientes ({total})')
        self.ui.actionPendientes.setEnabled(total > 0)

    # ============================================================
    # CONFIGURACIÓN
    # ============================================================
    def settings_form(self):
        dlg_settings = ConfigDialog()
        
        if dlg_settings.exec_():
            cfg = config_manager.load_config()

            # Convertir mapa_generado a booleano
            mapa_ok = cfg["mapa_generado"] == "True"

            # Actualizar la interfaz
            self.set_mapa_habilitado(mapa_ok)

    def iniciar_config_ini(self):
        if os.path.exists("config.ini"):
            return
        
        drivers = ConfigDialog.get_windows_drivers(self)
        unidad = drivers[0]
        
        data = {
            "origen": unidad,
            "destino": unidad,
            "unidad": unidad,
            "pantalla": "0",
            "ultimo_intervalo": "0-0",
            "mapa_generado": "True",
            "ultima_origen": unidad,
            "ultima_destino": unidad,
            "correo": "",
            "password": "",
        }

        config_manager.save_config(data)

    # ============================================================
    # UTILIDADES
    # ============================================================
    @staticmethod
    def analizar_mensaje(message):
        lineas = message.splitlines()
        num_lineas = len(lineas)
        longitud_maxima = max((len(linea) for linea in lineas), default=0)
        return longitud_maxima, num_lineas

    def closeEvent(self, e):
        reply = QMessageBox.question(
            self, "Confirmar salida",
            "¿Estás seguro de salir de la app?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            QApplication.quit()
        else:
            e.ignore()

    # ============================================================
    # CONEXIONES DE SEÑALES
    # ============================================================
    def signs_controls(self):
        self.ui.tableWidget.itemClicked.connect(self.mostrar_foto)
        self.ui.tableWidget.currentItemChanged.connect(self.mostrar_foto)
        self.ui.tableWidget.cellDoubleClicked.connect(self.ver_video)

        self.ui.button_sel_multiple.clicked.connect(self.columna_seleccion)

        self.ui.actionDesde_Movil.triggered.connect(self.select_movil)

        self.ui.actionClasificar.triggered.connect(self.clasificar_archivos)

        self.ui.actionPendientes.triggered.connect(self.clasificar_pendientes)

        self.ui.actionConfiguracion.triggered.connect(self.settings_form)

        self.ui.actionSalir_3.triggered.connect(self.close)

        self.ui.actionPrincipal.triggered.connect(lambda: self.cambiar_vista(0))
        self.ui.actionClasificacion.triggered.connect(lambda: self.cambiar_vista(1))
        self.ui.actionEstadistica.triggered.connect(lambda: self.cambiar_vista(2))

        self.ui.button_generar_mapa.clicked.connect(self.generar_mapa_manual)

        self.ui.button_sel_multiple.marcarTodos.connect(
            lambda: self.checked_unchecked_all_checkbox(
                False, self.ui.tableWidget, 0, self.ui.tableWidget.rowCount(), True
            )
        )
        self.ui.button_sel_multiple.desmarcarTodos.connect(
            lambda: self.checked_unchecked_all_checkbox(
                False, self.ui.tableWidget, 0, self.ui.tableWidget.rowCount(), False
            )
        )

        # ------------------------------
        # SEÑALES DE VISTA CLASIFICACION
        # ------------------------------
        self.btnMiniaturas.clicked.connect(lambda: self.setMiniatura(True))
        self.btnLista.clicked.connect(lambda: self.setMiniatura(False, 180))

        self.tableClasificacion.cellDoubleClicked.connect(self.ver_video)

        self.btnCopiarClasificacion.clicked.connect(lambda: self.bridge.accion("copiar", None, None))
        self.btnMoverClasificacion.clicked.connect(lambda: self.bridge.accion("mover", None, None))
        self.btnBorrarClasificacion.clicked.connect(lambda: self.bridge.accion("borrar", None, None))
        self.btnCompartirClasificacion.clicked.connect(lambda: self.bridge.accion("compartir", None, None))
        
        self.btnSeleccionarClasificacion.clicked.connect(self.seleccion_multiple_clasificacion)

        self.btnMiniaturas.min_grande.connect(lambda: self.setMiniatura(True, 180))


def main():
    app = QApplication(sys.argv)
    ventana = MapaWindow()
    ventana.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
