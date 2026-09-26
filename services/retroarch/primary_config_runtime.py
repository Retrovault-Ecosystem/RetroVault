import os
import re
import tempfile
from pathlib import Path


class PrimaryConfigRuntime:
    """
    Materialize a transient RetroArch primary configuration.

    Some RetroArch settings, notably the video driver, must be selected
    before video initialization and therefore cannot reliably be changed
    by a later --appendconfig layer.

    RetroVault never edits the user's persistent RetroArch configuration.
    Instead it copies the selected primary configuration and changes only
    explicitly-owned early-initialization settings in the transient copy.
    """

    _VIDEO_DRIVER = re.compile(
        r'(?m)^[ \\t]*video_driver[ \\t]*='
        r'[ \\t]*"[^"]*"[ \\t]*$'
    )

    # RetroVault production presentation owns these authorities explicitly.
    # They must be disabled in the transient primary configuration so
    # RetroArch cannot load a core/content automatic override or automatic
    # shader after RetroVault has selected its canonical presentation
    # package.  The persistent user configuration is never modified.
    _PRESENTATION_AUTOMATION_KEYS = (
        "auto_overrides_enable",
        "auto_shaders_enable",
        "input_overlay_enable_autopreferred",
    )

    @staticmethod
    def _replace_single_boolean_directive(
        text,
        key,
        value,
    ):
        pattern = re.compile(
            rf'(?m)^[ \\t]*{re.escape(key)}[ \\t]*='
            rf'[ \\t]*"(?:true|false)"[ \\t]*$',
            re.IGNORECASE,
        )

        matches = list(pattern.finditer(text))

        if len(matches) > 1:
            raise ValueError(
                "Expected at most one "
                f"{key} directive in RetroArch primary "
                f"configuration; found {len(matches)}."
            )

        directive = f'{key} = "{value}"'

        if len(matches) == 1:
            return pattern.sub(
                directive,
                text,
                count=1,
            )

        # RetroArch configurations are allowed to omit settings that use
        # built-in defaults. RetroVault still needs an explicit transient
        # production value, so materialize the missing directive without
        # changing the persistent source configuration.
        if text and not text.endswith("\n"):
            text += "\n"

        return text + directive + "\n"

    def __init__(
        self,
        directory=None,
    ):
        self.directory = Path(
            directory
            or (
                Path.home()
                / ".cache"
                / "retrovault"
                / "primary-runtime"
            )
        )

    @staticmethod
    def qualified_video_driver():
        """
        Return a host/session-level early video-driver override.

        The current production qualification establishes GLCore for the
        Wayland path. This is deliberately environment-scoped rather than
        platform-, title-, ROM-, raster-, or geometry-scoped.
        """
        if os.environ.get(
            "WAYLAND_DISPLAY",
            "",
        ).strip():
            return "glcore"

        return ""

    @staticmethod
    def default_config_candidates():
        xdg_config_home = os.environ.get(
            "XDG_CONFIG_HOME",
            "",
        ).strip()

        candidates = []

        # Flatpak RetroArch stores its real persistent config here when
        # launched through the host wrapper used by this installation.
        candidates.append(
            Path.home()
            / ".var"
            / "app"
            / "org.libretro.RetroArch"
            / "config"
            / "retroarch"
            / "retroarch.cfg"
        )

        if xdg_config_home:
            candidates.append(
                Path(xdg_config_home).expanduser()
                / "retroarch"
                / "retroarch.cfg"
            )

        candidates.extend(
            (
                Path.home()
                / ".config"
                / "retroarch"
                / "retroarch.cfg",
                Path.home()
                / ".retroarch.cfg",
            )
        )

        return tuple(candidates)

    def discover_source(
        self,
        source=None,
    ):
        if source:
            candidate = Path(
                source
            ).expanduser()

            if not candidate.is_file():
                raise ValueError(
                    "RetroArch primary configuration "
                    f"does not exist: {candidate}"
                )

            return candidate

        for candidate in (
            self.default_config_candidates()
        ):
            if candidate.is_file():
                return candidate

        return None

    def create(
        self,
        source=None,
        *,
        video_driver=None,
        overlay=None,
    ):
        driver = (
            self.qualified_video_driver()
            if video_driver is None
            else str(video_driver).strip()
        )

        if not driver:
            return None

        source_path = self.discover_source(
            source
        )

        if source_path is None:
            raise ValueError(
                "RetroArch primary configuration "
                "could not be located for transient "
                "video-driver qualification."
            )

        text = source_path.read_text(
            encoding="utf-8",
            errors="strict",
        )

        matches = list(
            self._VIDEO_DRIVER.finditer(
                text
            )
        )

        if len(matches) != 1:
            raise ValueError(
                "Expected exactly one video_driver "
                "directive in RetroArch primary "
                f"configuration; found {len(matches)}."
            )

        replacement = (
            f'video_driver = "{driver}"'
        )

        text = self._VIDEO_DRIVER.sub(
            replacement,
            text,
            count=1,
        )

        # Establish RetroVault's presentation authority in the transient
        # primary configuration before RetroArch initializes the core and
        # content. Explicit RetroVault overlay/shader/runtime layers are
        # applied later by the launcher.
        for key in self._PRESENTATION_AUTOMATION_KEYS:
            text = self._replace_single_boolean_directive(
                text,
                key,
                "false",
            )

        if overlay:
            overlay_path = (
                Path(overlay)
                .expanduser()
                .resolve(strict=False)
            )

            if not overlay_path.is_file():
                raise ValueError(
                    "RetroArch primary overlay configuration "
                    f"does not exist: {overlay_path}"
                )

            escaped_overlay = (
                str(overlay_path)
                .replace("\\", "\\\\")
                .replace('"', '\\"')
            )

            primary_overlay_values = {
                "input_overlay": escaped_overlay,
                "input_overlay_enable": "true",
                "input_overlay_opacity": "1.000000",
                "input_overlay_scale": "1.000000",
            }

            for key, value in primary_overlay_values.items():
                pattern = re.compile(
                    rf'(?m)^[ \t]*{re.escape(key)}[ \t]*='
                    rf'[ \t]*"[^"]*"[ \t]*$'
                )

                matches = list(pattern.finditer(text))

                if len(matches) > 1:
                    raise ValueError(
                        "Expected at most one "
                        f"{key} directive in RetroArch primary "
                        f"configuration; found {len(matches)}."
                    )

                directive = f'{key} = "{value}"'

                if matches:
                    text = pattern.sub(
                        lambda _match, d=directive: d,
                        text,
                        count=1,
                    )
                else:
                    if text and not text.endswith("\n"):
                        text += "\n"

                    text += directive + "\n"

        self.directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        handle = tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            prefix="primary-",
            suffix=".cfg",
            dir=self.directory,
            delete=False,
        )

        try:
            handle.write(
                text
            )
            handle.flush()
        finally:
            handle.close()

        return handle.name

    def cleanup(
        self,
        path,
    ):
        if not path:
            return

        candidate = Path(
            path
        )

        try:
            candidate.unlink()
        except FileNotFoundError:
            pass
