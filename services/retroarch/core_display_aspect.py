import ctypes
import math
from pathlib import Path

from .display_aspect import CoreDisplayAspect


class _RetroGameGeometry(ctypes.Structure):
    _fields_ = (
        ("base_width", ctypes.c_uint),
        ("base_height", ctypes.c_uint),
        ("max_width", ctypes.c_uint),
        ("max_height", ctypes.c_uint),
        ("aspect_ratio", ctypes.c_float),
    )


class _RetroSystemTiming(ctypes.Structure):
    _fields_ = (
        ("fps", ctypes.c_double),
        ("sample_rate", ctypes.c_double),
    )


class _RetroSystemAVInfo(ctypes.Structure):
    _fields_ = (
        ("geometry", _RetroGameGeometry),
        ("timing", _RetroSystemTiming),
    )


class LibretroDisplayAspectProbe:
    """
    Acquire libretro's prelaunch display-aspect authority.

    The libretro API explicitly permits retro_get_system_av_info() to be
    called before retro_init().  RetroVault therefore uses this boundary
    only as a prelaunch metadata query.  It intentionally does not call:

      - retro_set_environment();
      - retro_init();
      - retro_load_game();
      - retro_unload_game();
      - retro_deinit().

    No content is loaded and no emulation lifecycle is entered.

    geometry.aspect_ratio is the primary display-shape authority.  When
    the core explicitly reports a non-positive aspect ratio, libretro's
    base geometry supplies the fallback ratio.

    This boundary intentionally does not derive display shape from:

      - ROM filename or path;
      - game/title identity;
      - archive member identity;
      - platform-specific raster tables;
      - source raster dimensions when a positive display aspect exists;
      - bezel/artwork dimensions.

    Runtime RETRO_ENVIRONMENT_SET_GEOMETRY remains a distinct authority.
    A core may legitimately supersede this initial aspect after content
    startup; that later observation must never be replaced with a
    title-, ROM-, or raster-specific heuristic.
    """

    def __init__(self, loader=None):
        self._loader = (
            loader
            if loader is not None
            else ctypes.CDLL
        )

    @staticmethod
    def _core_path(core):
        if not isinstance(core, str):
            raise ValueError(
                "Core path must be a string."
            )

        if not core.strip():
            raise ValueError(
                "Core path cannot be empty."
            )

        path = Path(
            core
        ).expanduser()

        if not path.is_file():
            raise ValueError(
                f"Libretro core does not exist: {path}"
            )

        return path

    @staticmethod
    def _aspect_from_geometry(geometry):
        aspect = float(
            geometry.aspect_ratio
        )

        if not math.isfinite(aspect):
            raise ValueError(
                "Libretro core returned a non-finite display aspect."
            )

        if aspect > 0:
            return CoreDisplayAspect(
                width=aspect,
                height=1.0,
            )

        width = int(
            geometry.base_width
        )
        height = int(
            geometry.base_height
        )

        if width <= 0 or height <= 0:
            raise ValueError(
                "Libretro core returned invalid AV geometry."
            )

        return CoreDisplayAspect(
            width=width,
            height=height,
        )

    def acquire(self, core):
        path = self._core_path(
            core
        )

        try:
            library = self._loader(
                str(path)
            )
        except OSError as error:
            raise ValueError(
                f"Unable to load libretro core: {path}"
            ) from error

        try:
            get_av_info = (
                library.retro_get_system_av_info
            )
        except AttributeError as error:
            raise ValueError(
                "Libretro core does not export "
                "retro_get_system_av_info."
            ) from error

        get_av_info.argtypes = [
            ctypes.POINTER(
                _RetroSystemAVInfo
            )
        ]
        get_av_info.restype = None

        av_info = _RetroSystemAVInfo()

        get_av_info(
            ctypes.byref(
                av_info
            )
        )

        return self._aspect_from_geometry(
            av_info.geometry
        )
