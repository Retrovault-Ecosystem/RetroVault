"""Isolated in-memory Library rendering probe; emits JSON, never scans user ROMs."""
import argparse
import json
import os
import platform
import resource
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--count', type=int, default=100)
    parser.add_argument('--artwork', action='store_true')
    parser.add_argument('--query', default='Game 000')
    parser.add_argument('--cycles', type=int, default=0)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='rv-render-') as root:
        for key in ('XDG_CONFIG_HOME', 'XDG_DATA_HOME', 'XDG_CACHE_HOME'):
            os.environ[key] = str(Path(root) / key)
        os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
        from PyQt6.QtCore import QT_VERSION_STR, QTimer
        from PyQt6.QtWidgets import QApplication
        from services.library.models import Game
        from ui.library.gallery import GalleryView
        from ui.library.widgets.game_card import GameCard
        app = QApplication([])
        games = [Game(f'Game {i:06}', 'NES', 1980 + i % 20, '', '',
                      rom=f'/synthetic/{i}.nes', local_file_id=f'fixture-{i}')
                 for i in range(args.count)]
        if args.artwork:
            from PyQt6.QtGui import QImage, QColor
            cover = Path(root) / 'cover.png'
            image = QImage(800, 1000, QImage.Format.Format_RGB32)
            image.fill(QColor('blue')); image.save(str(cover))
            bad = Path(root) / 'invalid.png'; bad.write_text('invalid image')
            for i, game in enumerate(games):
                game.artwork = [str(cover), str(bad), str(Path(root)/'missing.png'), ''][i % 4]
        gaps = []; last = time.perf_counter()
        def tick():
            nonlocal last
            now = time.perf_counter(); gaps.append(now-last); last=now
        timer=QTimer();timer.timeout.connect(tick);timer.start(5)
        start=time.perf_counter()
        view=GalleryView(games);view.resize(1400,800);view.show();app.processEvents()
        constructed=time.perf_counter()-start
        start=time.perf_counter();view.toolbar.search.setText(args.query);app.processEvents()
        filtered=time.perf_counter()-start
        start=time.perf_counter();view.show_compact_view();app.processEvents()
        switched=time.perf_counter()-start
        start=time.perf_counter();view.show_gallery_view()
        view.grid.scroll.verticalScrollBar().setValue(view.grid.scroll.verticalScrollBar().maximum());app.processEvents()
        scrolled=time.perf_counter()-start
        repeated_rss = []
        for cycle in range(args.cycles):
            view.toolbar.search.setText('Game 000' if cycle % 2 else '')
            view.show_compact_view();app.processEvents()
            view.show_gallery_view();app.processEvents()
            from PyQt6.QtCore import QCoreApplication, QEvent
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
            if cycle % 5 == 4:
                repeated_rss.append(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        print(json.dumps(dict(count=args.count, query=args.query, cycles=args.cycles, repeated_peak_rss_kib=repeated_rss, python=platform.python_version(), qt=QT_VERSION_STR,
            system=platform.platform(), display=os.environ['QT_QPA_PLATFORM'], size=[1400,800],
            artwork=args.count * 3 // 4 if args.artwork else 0, archives=0, physical_files=0, families=args.count,
            construction=constructed, filtering=filtered, switching=switched, scrolling=scrolled, event_gap=max(gaps,default=0),
            cards=len(view.findChildren(GameCard)), rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)))
        view.close()


if __name__ == '__main__':
    main()
