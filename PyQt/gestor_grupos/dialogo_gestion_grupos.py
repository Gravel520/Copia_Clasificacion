'''

'''

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QInputDialog,
    QComboBox, QListWidget, QPushButton, QLabel, QMessageBox
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon
from config_paths import get_assets

class DialogoGestionGrupos(QDialog):
    def __init__(self, gestor_grupos, todas_carpetas, parent = None):
        super().__init__(parent)
        self.gestor = gestor_grupos
        self.todas_carpetas = todas_carpetas

        self.setWindowTitle("Configurar Carpetas de Grupos")
        self.resize(650, 450)
        self.init_ui()

    def init_ui(self):
        # Layout Principal Vertical
        layout_principal = QVBoxLayout(self)

        # --- SECCIÓN SUPERIOR: Combo de Selección de Grupo ---
        layout_combo = QHBoxLayout()
        layout_combo.addWidget(QLabel("Seleccionar Grupo:"))
        self.combo_grupos = QComboBox()
        self.actualizar_combo_grupos()
        self.combo_grupos.currentTextChanged.connect(self.cargar_carpetas_del_grupo)
        layout_combo.addWidget(self.combo_grupos, 1)
        layout_principal.addLayout(layout_combo)

        # --- SECCIÓN CENTRAL: Listas Cruzadas ---
        layout_listas_central = QHBoxLayout()

        # Lista Izquierda: Carpetas Disponibles globales en la App
        layout_izq = QVBoxLayout()
        layout_izq.addWidget(QLabel("Carpetas Disponibles:"))
        self.lista_disponibles = QListWidget()
        layout_izq.addWidget(self.lista_disponibles)
        layout_listas_central.addLayout(layout_izq)

        # Columna Central: Botones de traspaso de elementos [>]  y [<]
        layout_botones_traspaso = QVBoxLayout()
        layout_botones_traspaso.setAlignment(Qt.AlignCenter)

        self.btn_añadir = QPushButton()
        self.btn_añadir.setIcon(QIcon(f'{get_assets()}siguiente.png'))
        self.btn_añadir.setToolTip("Añadir al grupo")
        self.btn_añadir.setIconSize(QSize(15, 32))
        self.btn_añadir.clicked.connect(self.pasar_a_la_derecha)

        self.btn_eliminar = QPushButton()
        self.btn_eliminar.setIcon(QIcon(f'{get_assets()}anterior.png'))
        self.btn_eliminar.setToolTip("Eliminar del grupo")
        self.btn_eliminar.setIconSize(QSize(15, 32))
        self.btn_eliminar.clicked.connect(self.pasar_a_la_izquierda)

        layout_botones_traspaso.addWidget(self.btn_añadir)
        layout_botones_traspaso.addSpacing(10)
        layout_botones_traspaso.addWidget(self.btn_eliminar)
        layout_listas_central.addLayout(layout_botones_traspaso)

        # Lista Derecha: Carpetas asignadas al grupo seleccionado
        layout_der = QVBoxLayout()
        layout_der.addWidget(QLabel("Carpetas en este Grupo:"))
        self.lista_grupo = QListWidget()
        layout_der.addWidget(self.lista_grupo)
        layout_listas_central.addLayout(layout_der)

        layout_principal.addLayout(layout_listas_central)

        # --- SECCIÓN INFERIOR: Aceptar / Cancelar ---
        layout_inferior = QHBoxLayout()

        self.btn_eliminar = QPushButton("Eliminar Grupo")
        self.btn_crear = QPushButton("Crear Grupo")
        self.btn_eliminar.clicked.connect(self.eliminar_grupo)
        self.btn_crear.clicked.connect(self.crear_grupo)

        self.btn_aceptar = QPushButton("Aceptar")
        self.btn_aceptar.clicked.connect(self.guardar_cambios)

        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.clicked.connect(self.reject)

        layout_inferior.addWidget(self.btn_eliminar)
        layout_inferior.addWidget(self.btn_crear)
        layout_inferior.addStretch()

        layout_inferior.addWidget(self.btn_aceptar)
        layout_inferior.addWidget(self.btn_cancelar)
        layout_principal.addLayout(layout_inferior)

        # Cargar los datos iniciales según el grupo activo en el combo
        self.cargar_carpetas_del_grupo()

    def actualizar_combo_grupos(self):
        self.combo_grupos.clear()
        for g in self.gestor.obtener_grupos():
            self.combo_grupos.addItem(g["nombre"])

    def cargar_carpetas_del_grupo(self):
        grupo_seleccionado = self.combo_grupos.currentText()
        if not grupo_seleccionado:
            return
        
        grupo = self.gestor.obtener_grupo(grupo_seleccionado)
        carpetas_asignadas = grupo.get("carpetas", []) if grupo else []

        # Limpiar pantallas anteriores
        self.lista_grupo.clear()
        self.lista_disponibles.clear()

        # Poblar lista de asignadas (Derecha)
        for carpeta in carpetas_asignadas:
            self.lista_grupo.addItem(carpeta)

        # Poblar lista de disponibles (Izquierda): Solo las que NO pertenezcan al 
        #   grupo actual
        for carpeta in self.todas_carpetas:
            if carpeta not in carpetas_asignadas:
                self.lista_disponibles.addItem(carpeta)

    def pasar_a_la_derecha(self):
        ''' Pasa el elemento seleccionado de Disponibles a Asignadas '''
        item_seleccionado = self.lista_disponibles.currentItem()
        if item_seleccionado:
            texto = item_seleccionado.text()
            # Eliminar de la izquierda, añadir a la derecha
            self.lista_disponibles.takeItem(self.lista_disponibles.row(item_seleccionado))
            self.lista_grupo.addItem(texto)
            self.lista_grupo.setCurrentRow(self.lista_grupo.count() - 1)

    def pasar_a_la_izquierda(self):
        ''' Elimina el elemento del grupo devolviéndolo a disponibles '''
        item_seleccionado = self.lista_grupo.currentItem()
        if item_seleccionado:
            texto = item_seleccionado.text()
            # Eliminar de la derecha, añadir a la izquierda
            self.lista_grupo.takeItem(self.lista_grupo.row(item_seleccionado))
            self.lista_disponibles.addItem(texto)
            self.lista_disponibles.setCurrentRow(self.lista_disponibles.count() - 1)

    def guardar_cambios(self):
        grupo_seleccionado = self.combo_grupos.currentText()
        if not grupo_seleccionado:
            self.reject()
            return
        
        # Extraer todos los elementos vigentes de la lista derecha
        nuevas_carpetas = []
        for i in range(self.lista_grupo.count()):
            nuevas_carpetas.append(self.lista_grupo.item(i).text())

        # Actualizar en el Gestor de Grupos (guarda en JSON automaticamente)
        self.gestor.modificar_grupo(grupo_seleccionado, nuevas_carpetas=nuevas_carpetas)

        QMessageBox.information(self, "Éxito", f"Grupo '{grupo_seleccionado}' actualizado correctamente.")
        self.accept()

    def eliminar_grupo(self):
        grupo_seleccionado = self.combo_grupos.currentText()
        if not grupo_seleccionado:
            return
        
        # Pedimos confirmación al usuario para eliminar grupo
        respuesta = QMessageBox.question(
            self,
            "Confirmar eliminación",
            f"¿Eliminar el grupo: {grupo_seleccionado}",
            QMessageBox.Yes | QMessageBox.No
        )

        if respuesta == QMessageBox.Yes:
            self.gestor.eliminar_grupo(grupo_seleccionado)
            self.actualizar_combo_grupos()
            self.cargar_carpetas_del_grupo()

    def crear_grupo(self):
        nombre_grupo, aceptado = QInputDialog.getText(
            self,
            "Nuevo Grupo",
            "Escribe el nombre del nuevo grupo de viajes:"
        )

        if not aceptado or not nombre_grupo.strip():
            return
        
        nombre_grupo = nombre_grupo.strip()

        # Validamos que no exista un nombre igual
        if self.gestor.obtener_grupo(nombre_grupo) is not None:
            QMessageBox.warning(self, "Error", f"El grupo '{nombre_grupo}' ya existe.")
            return
        
        self.gestor.crear_grupo(nombre=nombre_grupo, carpetas=[])

        self.actualizar_combo_grupos()
        index = self.combo_grupos.findText(nombre_grupo)
        if index != -1:
            self.combo_grupos.setCurrentIndex(index)