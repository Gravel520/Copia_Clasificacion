'''
Script en Python.
Es un gestor global de hilos, para cerrar todos los hilos
    que puedan estar abiertos antes de cerrar la aplicación.

La idea es simple:
    · Cada vez que se crea un worker + QThread se registra en un
    gestor.
    · Cuando la app se va a cerrar el gestor recorre todos los hilos
    activos.
    · Los detiene correctamente (quit() + wait()).
    · Se evita el error fatal de "PyQt5.QtCore.QThread: Destroyed 
    while thread is running".

Para usar el gestor globalmente:
    1. Tenemos que importar este módulo desde cualquier script.
    from utils.thread_manager import thread_manager <- Esto será el
    gestor global de hilos.
    2. Registrar los hilos que se creen con el gestor.
    thread_manager.add(thread)
'''

from PyQt5.QtCore import QThread

class ThreadManager:
    def __init__(self):
        self.threads = []

    def add(self, thread: QThread):
        # Registrar un hilo para poder gestionarlo después.
        self.threads.append(thread)

    def stop_all(self):
        # Detener todos los hilos activos de forma segura.
        for thread in self.threads:

            # Si el hilo tiene un método stop_thread, llamarlo.
            if hasattr(thread, "stop_thread"):
                thread.stop_thread()

            # Si el hilo tiene flag detener, activarlo
            if hasattr(thread, "detener"):
                thread.detener = True

            # Cerrar el hilo correctamente.
            if thread.isRunning():
                thread.quit()
                thread.wait()

    def clear(self):
        # Vaciar la lista de hilos (después de deternerlos).
        self.threads = []

# Creamos el gestor de hilos global.
thread_manager = ThreadManager()
