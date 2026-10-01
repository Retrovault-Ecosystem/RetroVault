"""One process-session owner across registered emulator adapters."""
from threading import RLock

from .snes9x import Snes9xLauncher


class EmulatorSession:
    def __init__(self, retroarch, snes9x=None):
        self.retroarch = retroarch
        self.snes9x = snes9x if snes9x is not None else Snes9xLauncher()
        self._owner = None
        self._lock = RLock()

    @property
    def command(self):
        return self.retroarch.command

    @property
    def active_process(self):
        return self._owner.active_process if self._owner is not None else None

    def process_running(self):
        return any(adapter.process_running() for adapter in (self.retroarch, self.snes9x))

    def _launch(self, adapter, request):
        with self._lock:
            if self.process_running():
                return {'success': False, 'error': 'Another game session is running.'}
            self.clear_exited_process()
            # Keep ownership even when launch raises or reports a cleanup failure.
            self._owner = adapter
            return adapter.launch(request)

    def launch(self, profile):
        return self._launch(self.retroarch, profile)

    def launch_standalone(self, request):
        return self._launch(self.snes9x, request)

    def clear_exited_process(self):
        with self._lock:
            for adapter in (self.retroarch, self.snes9x):
                adapter.clear_exited_process()
            if not self.process_running():
                self._owner = None

    def stop(self):
        with self._lock:
            return self._owner.stop() if self._owner is not None else False

    def shutdown(self):
        errors = []
        with self._lock:
            for adapter in (self.retroarch, self.snes9x):
                try:
                    adapter.shutdown()
                except (OSError, RuntimeError) as exc:
                    errors.append(str(exc))
        if errors:
            raise RuntimeError('; '.join(errors))
