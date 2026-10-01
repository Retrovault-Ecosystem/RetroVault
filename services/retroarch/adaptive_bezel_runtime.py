"""Render a package-owned movable inner frame around the actual viewport.

Only artwork is resampled. The game image never enters this renderer. Packages
opt in with an explicit frame rectangle and a clean housing texture rectangle;
other packages keep their original overlay. Outer controls/branding stay fixed.
"""
import atexit
import json
import re
import shutil
import tempfile
from pathlib import Path

from PyQt6.QtCore import QRect
from PyQt6.QtGui import QColor, QImage, QPainter

from .overlay_runtime import _default_runtime_directory


class AdaptiveBezelRuntime:
    def __init__(self, directory=None):
        self.directory = Path(directory or _default_runtime_directory())
        self._created = []
        atexit.register(self.cleanup)

    @staticmethod
    def _rect(value, canvas):
        if (not isinstance(value, list) or len(value) != 4
                or any(type(v) is not int for v in value)):
            raise ValueError("Adaptive bezel rectangles require four integers.")
        rect = QRect(*value)
        if rect.isEmpty() or not canvas.contains(rect):
            raise ValueError("Adaptive bezel rectangle exceeds its canvas.")
        return rect

    def create(self, *, package, glass, geometry):
        data = json.loads(Path(package.production_manifest).read_text())
        spec = data.get("adaptive_frame")
        if spec is None:
            return package.overlay
        if not isinstance(spec, dict):
            raise ValueError("Invalid adaptive bezel specification.")
        canvas = QRect(0, 0, glass.canvas_width, glass.canvas_height)
        frame = self._rect(spec.get("frame"), canvas)
        texture = self._rect(spec.get("housing_texture"), canvas)
        aperture = QRect(glass.x, glass.y, glass.width, glass.height)
        target = QRect(geometry.x, geometry.y, geometry.width, geometry.height)
        if not frame.contains(aperture) or not aperture.contains(target):
            raise ValueError("Adaptive bezel requires a contained viewport.")
        if texture.intersects(frame):
            raise ValueError("Housing texture must be outside the movable frame.")
        overlay = Path(package.overlay)
        text = overlay.read_text()
        match = re.search(r'^overlay0_overlay\s*=\s*"([^"\n]+)"\s*$', text, re.M)
        if not match:
            raise ValueError("Adaptive bezel requires one declared artwork image.")
        source = QImage(str(overlay.parent / match.group(1)))
        if source.isNull() or source.rect() != canvas:
            raise ValueError("Adaptive bezel artwork does not match its canvas.")
        result = source.convertToFormat(QImage.Format.Format_ARGB32)
        painter = QPainter(result)
        try:
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
            # Replace the old frame with the package's own housing material.
            for y in range(frame.y(), frame.y() + frame.height(), texture.height()):
                for x in range(frame.x(), frame.x() + frame.width(), texture.width()):
                    width = min(texture.width(), frame.x() + frame.width() - x)
                    height = min(texture.height(), frame.y() + frame.height() - y)
                    painter.drawImage(QRect(x, y, width, height), source,
                                      QRect(texture.x(), texture.y(), width, height))
            sx = [frame.x(), aperture.x(), aperture.x() + aperture.width(), frame.x() + frame.width()]
            sy = [frame.y(), aperture.y(), aperture.y() + aperture.height(), frame.y() + frame.height()]
            dx = [target.x() - (aperture.x() - frame.x()), target.x(), target.x() + target.width(), target.x() + target.width() + sx[3] - sx[2]]
            dy = [target.y() - (aperture.y() - frame.y()), target.y(), target.y() + target.height(), target.y() + target.height() + sy[3] - sy[2]]
            # Keep corner/rim thickness. Resample only the straight rim lengths.
            for row in range(3):
                for col in range(3):
                    if row == col == 1:
                        continue
                    src = QRect(sx[col], sy[row], sx[col+1]-sx[col], sy[row+1]-sy[row])
                    dst = QRect(dx[col], dy[row], dx[col+1]-dx[col], dy[row+1]-dy[row])
                    if not src.isEmpty():
                        painter.drawImage(dst, source, src)
            painter.fillRect(target, QColor(0, 0, 0, 0))
        finally:
            painter.end()
        self.directory.mkdir(parents=True, exist_ok=True)
        root = Path(tempfile.mkdtemp(prefix="bezel-", dir=self.directory))
        self._created.append(root)
        image = root / "artwork.png"
        if not result.save(str(image)):
            raise OSError("Could not save adaptive bezel artwork.")
        descriptor = root / "overlay.cfg"
        descriptor.write_text('overlays = "1"\noverlay0_overlay = "artwork.png"\noverlay0_full_screen = true\noverlay0_descs = 0\n')
        return str(descriptor)

    def cleanup(self):
        remaining = []
        for root in self._created:
            try:
                shutil.rmtree(root)
            except FileNotFoundError:
                pass
            except OSError:
                remaining.append(root)
        self._created = remaining
