'''
Script en Python.
'''

import os
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QTextEdit, QPushButton,
    QHBoxLayout, QCheckBox, QComboBox, QProgressBar
)
from PyQt5.QtGui import QMovie
from PyQt5.QtCore import QThread, pyqtSignal, Qt

from .worker import WorkerAutodiagnostico
from config_paths import get_spinner

class DialogoAutodiagnostico(QDialog):
    def __init__(self, ruta_json, raiz_backup, parent = None):
        super().__init__(parent)
        self.setWindowTitle("Autodiagnóstico del sistema")
        self.resize(600, 600)

        self.ruta_json = ruta_json
        self.raiz_backup = raiz_backup

        layout = QVBoxLayout(self)

        # -------------------------
        # Selección de diagnósticos
        # -------------------------
        self.chkCompleto = QCheckBox("Diagnóstico completo")
        self.chkJsonCarpetas = QCheckBox("JSON ↔ Carpetas")
        self.chkJsonCache = QCheckBox("JSON ↔ Cache de ubicaciones")
        self.chkIntegridad = QCheckBox("Integridad de archivos")
        self.chkDirectorios = QCheckBox("Directorios vacíos")
        self.chkCorrupcion = QCheckBox("Archivos corruptos")

        layout.addWidget(self.chkCompleto)
        layout.addWidget(self.chkJsonCarpetas)
        layout.addWidget(self.chkJsonCache)
        layout.addWidget(self.chkIntegridad)
        layout.addWidget(self.chkDirectorios)
        layout.addWidget(self.chkCorrupcion)

        # -------------------------
        # Programación automática
        # -------------------------
        layout.addWidget(QLabel("Programar autodiagnóstico cada:"))

        hprog = QHBoxLayout()
        self.cmbCantidad = QComboBox()
        self.cmbCantidad.addItems([str(i) for i in range(1, 11)])

        self.cmbUnidad = QComboBox()
        self.cmbUnidad.addItems(["días", "meses", "años"])

        hprog.addWidget(self.cmbCantidad)
        hprog.addWidget(self.cmbUnidad)
        layout.addLayout(hprog)

        # -------------------------
        # Spinner
        # -------------------------
        self.lblSpinner = QLabel()
        self.movie = QMovie(get_spinner())
        self.lblSpinner.setMovie(self.movie)
        self.lblSpinner.setAlignment(Qt.AlignCenter)
        self.lblSpinner.hide()
        layout.addWidget(self.lblSpinner)

        # -------------------------
        # Barra de progreso
        # -------------------------
        self.progress = QProgressBar()
        self.progress.setValue(0)
        layout.addWidget(self.progress)

        # -------------------------
        # Zona de reporte
        # -------------------------
        self.txtReporte = QTextEdit()
        self.txtReporte.setReadOnly(True)
        layout.addWidget(self.txtReporte)

        # -------------------------
        # Botones
        # -------------------------
        hbtn = QHBoxLayout()
        self.btnEmpezar = QPushButton("Empezar")
        self.btnCancelar = QPushButton("Cancelar")
        self.btnGuardar = QPushButton("Guardar reporte")
        self.btnGuardar.setEnabled(False)

        hbtn.addWidget(self.btnEmpezar)
        hbtn.addWidget(self.btnCancelar)
        hbtn.addWidget(self.btnGuardar)
        layout.addLayout(hbtn)

        # -------------------------
        # Conexiones
        # -------------------------
        self.btnEmpezar.clicked.connect(self.iniciar)
        self.btnCancelar.clicked.connect(self.cancelar)
        self.btnGuardar.clicked.connect(self.guardar_reporte)

        self.thread_ = None
        self.worker = None

    # ---------------------------------------------------------
    # Iniciar autodiagnóstico
    # ---------------------------------------------------------
    def iniciar(self):
        self.txtReporte.clear()
        seleccionados = self.obtener_chequeos_seleccionados()
        if not seleccionados:
            self.txtReporte.setText("☣ Debes seleccionar al menos un diagnóstico.")
            return
        
        self.progress.setMaximum(len(seleccionados) if "completo" not in seleccionados else 5)
        self.progress.setValue(0)

        self.lblSpinner.show()
        self.movie.start()

        # Crear hilo + worker
        self.thread_ = QThread()
        self.worker = WorkerAutodiagnostico(
            self.ruta_json,
            self.raiz_backup,
            seleccionados
        )
        self.worker.moveToThread(self.thread_)

        # Conexiones
        self.thread_.started.connect(self.worker.run)
        self.worker.progreso.connect(self.actualizar_estado)
        self.worker.avance.connect(self.actualizar_progreso)
        self.worker.terminado.connect(self.finalizar)

        # Cuando termine, cerramos el hilo
        self.worker.terminado.connect(self.thread_.quit)
        self.worker.terminado.connect(self.worker.deleteLater)
        self.thread_.finished.connect(self.thread_.deleteLater)

        # Iniciar
        self.thread_.start()

    # ---------------------------------------------------------
    # Obtener lista de chequeos seleccionados
    # ---------------------------------------------------------
    def obtener_chequeos_seleccionados(self):
        if self.chkCompleto.isChecked():
            return ["completo"]
        
        lista = []
        if self.chkJsonCarpetas.isChecked():
            lista.append("json_carpetas")
        if self.chkJsonCache.isChecked():
            lista.append("json_cache")
        if self.chkIntegridad.isChecked():
            lista.append("integridad")
        if self.chkDirectorios.isChecked():
            lista.append("directorios")
        if self.chkCorrupcion.isChecked():
            lista.append("corrupcion")

        return lista
    
    # ---------------------------------------------------------
    # Actualizar estado
    # ---------------------------------------------------------
    def actualizar_estado(self, mensaje):
        self.txtReporte.append(mensaje)

    # ---------------------------------------------------------
    # Actualizar barra de progreso
    # ---------------------------------------------------------
    def actualizar_progreso(self):
        self.progress.setValue(self.progress.value() + 1)

    # ---------------------------------------------------------
    # Finalizar
    # ---------------------------------------------------------
    def finalizar(self, reporte):
        print(reporte)
        self.movie.stop()
        self.lblSpinner.hide()

        self.txtReporte.append("\n=== RESULTADO FINAL ===\n")

        for bloque in reporte:
            self.txtReporte.append(f"🔍 {bloque['nombre']}\n")
            self.txtReporte.append(f"Problemas detectados: {bloque['problemas']}\n")
            self.txtReporte.append("")

        self.btnGuardar.setEnabled(True)

    # ---------------------------------------------------------
    # Cancelar
    # ---------------------------------------------------------
    def cancelar(self):
        if self.thread_ and self.thread_.isRunning():
            self.thread_.terminate()
        self.close()

    # ---------------------------------------------------------
    # Guardar reporte
    # ---------------------------------------------------------
    def guardar_reporte(self):
        with open("reporte_autodiagnostico.txt", "w", encoding="utf-8") as f:
            f.write(self.txtReporte.toPlainText())
        self.txtReporte.append("\n💾 Reporte guardado en 'reporte_autodiagnostico.txt'")
