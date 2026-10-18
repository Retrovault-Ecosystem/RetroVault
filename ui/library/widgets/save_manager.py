"""Explicit save inspection/recovery; services own routing and file writes."""
import re
import zipfile

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QPushButton, QListWidget,
                             QFileDialog, QMessageBox)
from PyQt6.QtCore import Qt
from config.paths import data_home
from services.saves.context import save_context
from services.saves.policy import SavePolicy
from services.saves.recovery import SaveRecovery


class SaveManager(QDialog):
    def __init__(self, game, config_loader, session, parent=None):
        super().__init__(parent)
        self.game, self.config_loader, self.session = game, config_loader, session
        self.policy = SavePolicy()
        self.recovery = SaveRecovery(session, data_home() / 'retrovault/save-backups')
        self.setWindowTitle('Saves and recovery')
        self.resize(680, 420)
        layout = QVBoxLayout(self)
        self.description = QLabel()
        self.description.setTextFormat(Qt.TextFormat.PlainText)
        self.description.setWordWrap(True)
        layout.addWidget(self.description)
        self.files = QListWidget()
        layout.addWidget(self.files)
        self.enable = QPushButton('Use separate saves for this edition…')
        self.enable.clicked.connect(self.enable_isolation)
        layout.addWidget(self.enable)
        self.disable = QPushButton('Return to existing RetroArch save routing…')
        self.disable.clicked.connect(self.disable_isolation)
        layout.addWidget(self.disable)
        backup = QPushButton('Back up selected save')
        backup.clicked.connect(self.backup)
        layout.addWidget(backup)
        restore = QPushButton('Restore selected save from backup…')
        restore.clicked.connect(self.restore)
        layout.addWidget(restore)
        notice = QLabel('Quit normally before managing saves. Stop is not a promise that progress was saved.\n'
                        'In-game saves and emulator states are separate. Recovery requires the same edition, '
                        'backend, runtime and destination; it does not convert formats.')
        notice.setWordWrap(True)
        layout.addWidget(notice)
        self.refresh()

    def refresh(self):
        self.context = save_context(self.game, self.config_loader.load(), self.policy)
        context = self.context
        self.files.clear()
        self.targets = []
        self.enable.setVisible(context.backend == 'retroarch' and context.sram is None)
        self.disable.setVisible(context.backend == 'retroarch' and context.sram is not None)
        if context.sram is None:
            self.description.setText('Existing save routing remains controlled by RetroArch. '
                                     'No save was moved or renamed. Separate storage is optional; '
                                     'legacy destinations are not guessed or overwritten here.')
            return
        self.description.setText(f'In-game saves: {context.sram}\nEmulator states: {context.states}')
        for kind, root in (('sram', context.sram), ('state', context.states)):
            if root.is_dir() and not root.is_symlink():
                for path in sorted(root.iterdir()):
                    if not path.is_file() or path.is_symlink():
                        continue
                    # Do not list configuration/profile files as game saves.
                    if kind == 'sram' and path.suffix != '.srm':
                        continue
                    if kind == 'state' and not re.search(r'(?:\.state\d*|\.\d{3})$', path.name):
                        continue
                    self.targets.append((path, kind))
                    self.files.addItem(f'{"In-game save" if kind == "sram" else "Emulator state"}: {path.name}')

    def selected_target(self):
        row = self.files.currentRow()
        if row < 0:
            raise ValueError('Select one existing save file first.')
        return self.context.target(*self.targets[row])

    def run_action(self, action):
        try:
            action()
            self.refresh()
        except (OSError, ValueError, zipfile.BadZipFile) as exc:
            QMessageBox.warning(self, 'Save operation unavailable', str(exc))

    def enable_isolation(self):
        answer = QMessageBox.question(self, 'Start separate save storage?',
            'This edition will start with separate, empty RetroArch save storage. Existing saves stay '
            'where they are and will not be imported or overwritten. Continue?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No)
        if answer == QMessageBox.StandardButton.Yes:
            self.run_action(lambda: self.policy.enable(self.session, self.context.local_file_id,
                                                      self.context.core, str(self.context.rom)))

    def backup(self):
        def action():
            path = self.recovery.backup(self.selected_target())
            QMessageBox.information(self, 'Backup saved', str(path))
        self.run_action(action)

    def disable_isolation(self):
        answer = QMessageBox.question(self, 'Return to existing save routing?',
            'RetroArch will use its existing save routing again. Separate saves remain on disk; '
            'nothing is moved, deleted or merged. Continue?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No)
        if answer == QMessageBox.StandardButton.Yes:
            self.run_action(lambda: self.policy.disable(self.session, self.context.local_file_id,
                                                       self.context.core, str(self.context.rom)))

    def restore(self):
        def action():
            target = self.selected_target()
            filename, _ = QFileDialog.getOpenFileName(self, 'Select matching save backup',
                                                      str(self.recovery.backup_root), 'Save backups (*.rvsave)')
            if not filename:
                return
            answer = QMessageBox.question(self, 'Restore this save?',
                f'Replace {target.path.name} with the selected backup? A safety backup of its current '
                'contents will be created first.', QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No)
            if answer != QMessageBox.StandardButton.Yes:
                return
            result = self.recovery.restore(target, filename)
            message = 'Save restored. Safety backup: ' + result['safety_backup']
            if result['permission_warning']:
                message += '\nPermissions could not be restored: ' + result['permission_warning']
            QMessageBox.information(self, 'Save restored', message)
        self.run_action(action)
