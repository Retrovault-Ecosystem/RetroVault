"""Reversible controller drafts; backend services own discovery and persistence."""
from copy import deepcopy

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QComboBox, QFormLayout, QGroupBox, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QTabWidget, QVBoxLayout)

from config.controller_preferences import BUTTONS, DEFAULT_KEYS, from_config, defaults
from services.input.devices import inventory
from services.input.mappings import resolved_profile


class PlayerEditor(QGroupBox):
    def __init__(self, number):
        super().__init__(f'Player {number}')
        self.number = number
        self.device = QComboBox()
        self.fields = {}
        form = QFormLayout(self)
        form.addRow('Input', self.device)
        for button in BUTTONS:
            field = QLineEdit()
            field.setAccessibleName(f'Player {number} {button}')
            self.fields[button] = field
            form.addRow(button.upper(), field)
        self.device.currentIndexChanged.connect(self._changed)
        self.load(None, [])

    def _changed(self):
        selection = self.device.currentData()
        for index, (button, field) in enumerate(self.fields.items()):
            field.setEnabled(selection is not None)
            field.setText(DEFAULT_KEYS[button] if selection == 'keyboard' else f'b{index}')

    def value(self):
        selected = self.device.currentData()
        if selected is None:
            return None
        return dict(kind='keyboard' if selected == 'keyboard' else 'gamepad',
                    device={} if selected == 'keyboard' else deepcopy(selected),
                    bindings={button: field.text().strip() for button, field in self.fields.items()})

    def load(self, player, devices):
        self.device.blockSignals(True)
        self.device.clear()
        if self.number == 1:
            self.device.addItem('Keyboard', 'keyboard')
        else:
            self.device.addItem('Not assigned', None)
        for device in devices:
            identity = {key: device[key] for key in ('guid', 'serial', 'name', 'session', 'instance')}
            self.device.addItem(f'{device["name"]} — device {device["index"] + 1}', identity)
        selected = 'keyboard' if player and player['kind'] == 'keyboard' else (
            player['device'] if player else ('keyboard' if self.number == 1 else None))
        index = self.device.findData(selected)
        if index < 0:
            self.device.addItem(f'{selected["name"]} — saved assignment; refresh/preview to check', selected)
            index = self.device.count() - 1
        self.device.setCurrentIndex(index)
        self.device.blockSignals(False)
        self._changed()
        if player:
            for button, value in player['bindings'].items():
                self.fields[button].setText(value)


class BackendEditor(QGroupBox):
    def __init__(self, backend):
        super().__init__()
        self.backend = backend
        layout = QVBoxLayout(self)
        self.mode = QComboBox()
        self.mode.addItem('Use existing emulator controls (default)', 'existing')
        self.mode.addItem('Use RetroVault controller profile', 'managed')
        layout.addWidget(self.mode)
        row = QHBoxLayout()
        self.players = [PlayerEditor(1), PlayerEditor(2)]
        for player in self.players:
            row.addWidget(player)
        layout.addLayout(row)
        self.mode.currentIndexChanged.connect(self._enable)
        self._enable()

    def _enable(self):
        for player in self.players:
            player.setEnabled(self.mode.currentData() == 'managed')

    def load(self, profile, devices):
        self.mode.setCurrentIndex(self.mode.findData(profile['mode']))
        for index, player in enumerate(self.players):
            player.load(profile['players'][index] if index < len(profile['players']) else None, devices)
        self._enable()

    def value(self):
        mode = self.mode.currentData()
        return dict(mode=mode, players=[value for player in self.players
                                       if (value := player.value()) is not None] if mode == 'managed' else [])


class ControllerSettings(QGroupBox):
    def __init__(self, service, parent=None, *, device_inventory=None):
        super().__init__('Controller profiles', parent)
        self.service = service
        self.inventory = device_inventory or inventory
        self.devices = []
        self.saved = from_config(service.config_loader.load())
        layout = QVBoxLayout(self)
        note = QLabel('Profiles apply on the next launch. Existing emulator controls remain the default. '
                      'Keyboard: arrows, return, tab, space, or a–z. Gamepads: b0 means button 0; '
                      'a0:+ / a0:- means an axis direction. Button numbers differ by backend. '
                      'Hardware qualification is pending; USB, Bluetooth or Wi-Fi alone does not prove compatibility. '
                      'Preview checks the draft; it does not rebind a running game.')
        note.setWordWrap(True)
        layout.addWidget(note)
        tabs = QTabWidget()
        self.editors = {backend: BackendEditor(backend) for backend in ('retroarch', 'snes9x')}
        for backend, label in (('retroarch', 'RetroArch'), ('snes9x', 'Native Snes9x')):
            tabs.addTab(self.editors[backend], label)
        layout.addWidget(tabs)
        actions = QHBoxLayout()
        for title, callback in (('Refresh devices', self.refresh), ('Preview', self.preview),
                                ('Apply', self.apply), ('Cancel', self.cancel),
                                ('Reset to existing controls', self.reset)):
            button = QPushButton(title)
            button.clicked.connect(callback)
            actions.addWidget(button)
        layout.addLayout(actions)
        self.status = QLabel()
        self.status.setTextFormat(Qt.TextFormat.PlainText)
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        self._load(self.saved)

    def _load(self, values):
        for backend, editor in self.editors.items():
            editor.load(values[backend], self.devices)

    def value(self):
        return {backend: editor.value() for backend, editor in self.editors.items()}

    def refresh(self):
        draft = self.value()
        try:
            self.devices = self.inventory.snapshot()
        except (OSError, ValueError) as exc:
            self.status.setText(str(exc))
            return
        self._load(draft)
        self.status.setText(f'{len(self.devices)} gamepad(s) detected. Assignments retained. '
                            'Use Preview to check saved assignments. Reconnected devices without '
                            'serial identification must be selected again.')

    def preview(self):
        try:
            values = self.value()
            needs_devices = any(p['kind'] == 'gamepad' for profile in values.values()
                                if profile['mode'] == 'managed' for p in profile['players'])
            devices = self.inventory.snapshot() if needs_devices else []
            for backend in self.editors:
                resolved_profile({'controllers': values}, backend, devices)
        except (OSError, ValueError) as exc:
            self.status.setText(f'Preview: {exc}')
            return
        self.status.setText('Draft mappings and current assignments pass validation. Nothing was saved. '
                            'Gameplay, reconnect and two-player operation still require qualification.')

    def apply(self):
        try:
            result = self.service.save_controller_preferences(self.value())
        except (OSError, ValueError) as exc:
            self.status.setText(f'Could not save controller preferences: {exc}')
            return
        self.saved = from_config(result.config)
        self._load(self.saved)
        message = 'Controller preferences saved for the next launch. Running sessions are unchanged.'
        if result.refresh_error:
            message += f' Saved successfully, but rereading settings failed: {result.refresh_error}'
        self.status.setText(message)

    def cancel(self):
        self._load(self.saved)
        self.status.setText('Unsaved controller edits discarded.')

    def reset(self):
        self._load(defaults())
        self.status.setText('Draft reset to existing emulator controls. Apply to save, or Cancel to undo.')
