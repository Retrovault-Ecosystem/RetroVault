"""Small optional SDL2 joystick inventory; no keyboard capture or device claiming."""
import atexit
import ctypes as C
from ctypes.util import find_library
import uuid


class DeviceInventory:
    def __init__(self):
        self.session=uuid.uuid4().hex
        self.lib=None

    def _load(self):
        if self.lib is not None:
            return self.lib
        path=find_library('SDL2-2.0') or find_library('SDL2')
        if not path:
            raise ValueError('SDL2 controller discovery is unavailable; existing emulator controls remain usable.')
        lib=C.CDLL(path)
        class GUID(C.Structure):
            _fields_=[('data',C.c_ubyte*16)]
        declarations={
            'SDL_InitSubSystem':([C.c_uint32],C.c_int),
            'SDL_QuitSubSystem':([C.c_uint32],None),
            'SDL_JoystickUpdate':([],None),
            'SDL_NumJoysticks':([],C.c_int),
            'SDL_JoystickNameForIndex':([C.c_int],C.c_char_p),
            'SDL_JoystickGetDeviceGUID':([C.c_int],GUID),
            'SDL_JoystickGetDeviceInstanceID':([C.c_int],C.c_int32),
            'SDL_JoystickOpen':([C.c_int],C.c_void_p),
            'SDL_JoystickClose':([C.c_void_p],None),
            'SDL_JoystickNumButtons':([C.c_void_p],C.c_int),
            'SDL_JoystickNumAxes':([C.c_void_p],C.c_int),
            'SDL_IsGameController':([C.c_int],C.c_int),
        }
        try:
            for name,(args,result) in declarations.items():
                function=getattr(lib,name);function.argtypes=args;function.restype=result
            if hasattr(lib,'SDL_JoystickGetSerial'):
                lib.SDL_JoystickGetSerial.argtypes=[C.c_void_p];lib.SDL_JoystickGetSerial.restype=C.c_char_p
            # Initialize GameController mappings as well as raw joystick input;
            # RetroArch's SDL2 namespace depends on SDL_IsGameController.
            if lib.SDL_InitSubSystem(0x2200)!=0:
                raise ValueError('SDL2 could not initialize controller discovery.')
        except AttributeError as exc:
            raise ValueError('Installed SDL2 lacks required controller functions.') from exc
        self.lib=lib
        atexit.register(lib.SDL_QuitSubSystem,0x2200)
        return lib

    def snapshot(self):
        try:
            lib=self._load()
        except OSError as exc:
            raise ValueError(f'Controller discovery unavailable: {exc}') from exc
        lib.SDL_JoystickUpdate()
        count=lib.SDL_NumJoysticks()
        if count<0:
            raise ValueError('Cannot enumerate controllers.')
        devices=[]
        for index in range(count):
            handle=lib.SDL_JoystickOpen(index)
            if not handle:
                continue
            try:
                serial=lib.SDL_JoystickGetSerial(handle) if hasattr(lib,'SDL_JoystickGetSerial') else None
                devices.append(dict(index=index,instance=lib.SDL_JoystickGetDeviceInstanceID(index),
                    guid=bytes(lib.SDL_JoystickGetDeviceGUID(index).data).hex(),
                    name=(lib.SDL_JoystickNameForIndex(index) or b'Unnamed controller').decode('utf-8','replace'),
                    serial=(serial or b'').decode('utf-8','replace'),session=self.session,
                    buttons=lib.SDL_JoystickNumButtons(handle),axes=lib.SDL_JoystickNumAxes(handle),
                    standardized=bool(lib.SDL_IsGameController(index))))
            finally:
                lib.SDL_JoystickClose(handle)
        return devices


inventory=DeviceInventory()
