'''

'''

import sys, os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QMessageBox, QFileDialog,
    QDialog, QLabel
    )
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtCore import QUrl
from PyQt5.QtWidgets import QTableWidgetItem
from PyQt5 import uic
from PyQt5.QtGui import QPixmap
from componentes.controles import ScrollableMessageBox, SpinnerOverlay
from componentes.dialogo_cantidad import DialogoSeleccionCantidad
from config import *
from worker.mapa_worker import MapaWorker
from worker.copia_worker import CopiaWorker
from bridge.bridge import Bridge
from copia_clasificador_fotos import obtener_archivos

ARCHIVOS_SEL = {}  # clave: ruta_archivo, valor: hash_archivo

class MapaWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.ui = uic.loadUi(RUTA_UI)
        self.ui.showMaximized()

        # Visor web
        self.view = QWebEngineView()
        self.view.load(QUrl.fromLocalFile(os.path.abspath(f"{RUTA_MAPA_HTML}")))

        # Canal web
        self.channel = QWebChannel()
        self.bridge = Bridge(
            self.ui.tableWidget,
            self.ui.labelFechaListado,
            self.ui.labelMapaActualizado,
            self.ui.button_generar_mapa,
            self.ui.button_sel_multiple,
            self.view,
            self.ui.labelVisor,
            RUTA_JSON_UNICO,
            self.set_mapa_habilitado
        )
        self.channel.registerObject("bridge", self.bridge)
        self.view.page().setWebChannel(self.channel)

        # Estado del mapa (actualizado o NO)
        self.mapa_actualizado = True
        self.set_mapa_habilitado(True) # También se actualiza 'Pendientes' al abrir
        self.ui.button_generar_mapa.setVisible(False)        

        # Señales
        self.bridge.actualizarFoto.connect(self.mostrar_foto)
        self.bridge.pendientes_actualizados.connect(self.actualizar_menu_pendientes)

        # Insertar visor web en el layout
        layout = QVBoxLayout(self.ui.QWidget_foto)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.addWidget(self.view)

        self.signs_controls()

    def show(self):
        self.ui.show()

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
    # MOSTRAR FOTO
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

        pixmap = QPixmap(ruta_archivo)
        if not pixmap.isNull():
            self.ui.labelVisor.setPixmap(pixmap)
            self.ui.labelVisor.setScaledContents(True)

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
    # COPIA DESDE PC O MÓVIL
    # ============================================================
    def select_directory(self):
        carpeta_origen = QFileDialog.getExistingDirectory(self, "Seleccionar directorio de origen")
        if not carpeta_origen:
            return
        self.iniciar_copia(carpeta_origen)

    def select_movil(self):
        self.iniciar_copia(None)

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
        self.view.load(QUrl.fromLocalFile(os.path.abspath(f"{RUTA_MAPA_HTML}")))
        QMessageBox.information(self, "Mapa actualizado", "El mapa ha sido generado correctamente.")

        self.set_mapa_habilitado(True)

    # ============================================================
    # CLASIFICAR ARCHIVOS
    # ============================================================
    def clasificar_archivos(self):
        # El usuario elige una carpeta y se lanza la clasificación.
        carpeta = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta para clasificar")
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

    # ============================================================
    # CLASIFICAR PENDIENTES
    # ============================================================
    def clasificar_pendientes(self):
        # 1️⃣ Actualizar contador de pendientes
        self.bridge.cargar_pendientes()

        # 2️⃣ Ruta de la carpeta de pendientes (Sin_GPS)
        ruta_pendientes = os.path.join(RUTA_PRINCIPAL, "(Sin_GPS)(Sin_GPS)(0000-00)")

        if not os.path.isdir(ruta_pendientes):
            QMessageBox.warning(self, "Pendientes", f"No existe la carpeta de pendientes:\n{ruta_pendientes}")
            return
        
        # 3️⃣ Decirle al Bridge que esa es la carpeta actual
        self.bridge.recibirRuta(ruta_pendientes)

    # ============================================================
    # MENÚ PENDIENTES
    # ============================================================
    def actualizar_menu_pendientes(self, total):
        self.ui.actionPendientes.setText(f'Pendientes ({total})')
        self.ui.actionPendientes.setEnabled(total > 0)

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
        self.ui.button_sel_multiple.clicked.connect(self.columna_seleccion)

        self.ui.actionDesde_Movil.triggered.connect(self.select_movil)

        self.ui.actionClasificar.triggered.connect(self.clasificar_archivos)

        self.ui.actionPendientes.triggered.connect(self.clasificar_pendientes)
        self.ui.actionSalir_3.triggered.connect(self.close)

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


def main():
    app = QApplication(sys.argv)
    ventana = MapaWindow()
    ventana.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
