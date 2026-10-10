"""One owned Qt discovery worker, one pending request, one publication owner."""
from PyQt6.QtCore import QObject, QThread, QTimer, pyqtSignal
from services.library.discovery import DiscoveryControl, DiscoveryCancelled


class _DiscoveryWorker(QThread):
    progress = pyqtSignal(object)

    def __init__(self, controller, request, generation, parent):
        super().__init__(parent)
        self.controller, self.request, self.generation = controller, request, generation
        self.control = DiscoveryControl(self.progress.emit)
        self.result = None
        self.error = None

    def run(self):
        try:
            self.result = self.controller.prepare_discovery(self.request, self.control)
        except Exception as exc:
            # Deliver worker errors to the UI; never let an exception strand its owner.
            self.error = exc


class DiscoveryJobs(QObject):
    status = pyqtSignal(str)
    busy_changed = pyqtSignal(bool)
    published = pyqtSignal(object)
    failed = pyqtSignal(str)
    idle = pyqtSignal()

    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.controller = controller
        self._worker = None
        self._generation = 0
        self._pending = None
        self._closing = False
        self.committing = False

    @property
    def busy(self):
        return self._worker is not None or self.committing

    def request(self, kind='refresh', directory=None):
        if self._closing or self.committing:
            return
        self._generation += 1
        if self._worker is not None:
            self._pending = (kind, directory)
            self._worker.control.cancel()
            self.status.emit('Cancelling older discovery; latest request is pending…')
            return
        self._start(kind, directory)

    def _start(self, kind, directory):
        try:
            request = self.controller.discovery_request(kind, directory)
        except (OSError, ValueError, RuntimeError) as exc:
            self.failed.emit(str(exc))
            self.busy_changed.emit(False)
            self.idle.emit()
            return
        worker = _DiscoveryWorker(self.controller, request, self._generation, self)
        self._worker = worker
        worker.progress.connect(self._progress)
        worker.finished.connect(self._finished)
        self.busy_changed.emit(True)
        self.status.emit('Discovering Library… Browse the last completed Library while this runs.')
        worker.start()

    def _progress(self, progress):
        worker = self.sender()
        if worker is self._worker and worker.generation == self._generation and not self._closing:
            units = {'Scanning': 'files examined', 'Directories': 'directories visited',
                     'Hashing': 'chunks read', 'Artwork': 'games checked',
                     'Inspecting archive': 'archives inspected'}
            unit = units.get(progress.phase)
            self.status.emit(f'{progress.phase}: {progress.count} {unit} (total not yet known)'
                             if unit else f'{progress.phase}…')

    def cancel(self):
        if self.committing:
            return
        self._generation += 1
        self._pending = None
        if self._worker is not None:
            self._worker.control.cancel()
            self.status.emit('Cancelling discovery… No update will be published.')

    def _finished(self):
        worker = self._worker
        if worker is None:
            return
        self._worker = None
        if self._closing or worker.generation != self._generation or isinstance(worker.error, DiscoveryCancelled):
            self.status.emit('Discovery cancelled; Library unchanged.')
        elif worker.error is not None:
            self.failed.emit(f'Discovery failed; Library unchanged: {worker.error}')
        else:
            self.committing = True
            self.busy_changed.emit(True)
            self.status.emit('Finishing Library update — cannot cancel.')
            # Yield to Qt before the non-cancellable publication phase, so its
            # status and disabled Cancel control can be presented honestly.
            result = worker.result
            worker.deleteLater()
            QTimer.singleShot(0, lambda: self._publish(result))
            return
        worker.deleteLater()
        self._complete()

    def _publish(self, prepared):
        try:
            result = self.controller.publish_discovery(prepared)
        except (OSError, ValueError, RuntimeError) as exc:
            self.failed.emit(str(exc))
        else:
            # The snapshot has committed even if a dependent view cannot repaint.
            self.published.emit(result)
        finally:
            self.committing = False
            self._complete()

    def _complete(self):
        pending, self._pending = self._pending, None
        if pending is not None and not self._closing:
            self._start(*pending)
        else:
            self.busy_changed.emit(False)
            self.idle.emit()

    def shutdown(self):
        self._closing = True
        self.cancel()
        return not self.busy
