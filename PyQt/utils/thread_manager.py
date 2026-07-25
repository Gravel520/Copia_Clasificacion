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
        threads_copy = list(self.threads)

        # Detener todos los hilos activos de forma segura.
        for thread in threads_copy:
            try:
                # Si el hilo ya está destruido, ignorarlo
                if thread is None:
                    continue

                # Si el VLCWorker, liberar mediaplayer
                if hasattr(thread, "mediaplayer"):
                    try:
                        thread.mediaplayer.stop()
                        thread.mediaplayer.set_media(None)
                    except:
                        pass

                # Si el hilo tiene un método stop_thread, llamarlo.
                if hasattr(thread, "stop_thread"):
                    try:
                        thread.stop_thread()
                    except:
                        pass

                # Si el hilo tiene flag detener, activarlo
                if hasattr(thread, "detener"):
                    thread.detener = True

                # Cerrar el hilo correctamente.
                if thread.isRunning():
                    thread.quit()
                    thread.wait()

            except RuntimeError:
                # El QThread ya ha sido destuido por Qt lo eliminamos del gestor
                pass

            except Exception as e:
                print("Error al cerrar hilo:", e)

            finally:
                # Eliminar el hilo del gestor.
                self.threads.remove(thread)    

    def clear(self):
        # Vaciar la lista de hilos (después de deternerlos).
        self.threads = []

# Creamos el gestor de hilos global.
thread_manager = ThreadManager()
