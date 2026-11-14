"""First screen on the right-hand side: language picker + continue."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QLabel,
    QMenu,
    QMessageBox,
    QPushButton,
    QStackedLayout,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from vacuula_installer.i18n import Translator
from vacuula_installer.widgets.background_flair import BackgroundFlairWidget
from vacuula_installer.widgets.language_selector import FlagButton


class WelcomeScreen(QWidget):
    """Emits :attr:`continueRequested` when the user is ready to move on."""

    continueRequested = Signal()
    sshKeyChanged = Signal(str)  # dev: path to an OpenSSH public key, "" when removed

    def __init__(self, translator: Translator, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._translator = translator

        layers = QStackedLayout(self)
        layers.setStackingMode(QStackedLayout.StackingMode.StackAll)

        self._flair = BackgroundFlairWidget(self)
        
        layers.addWidget(self._flair)


        foreground = QWidget(self)
        foreground.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        fg_layout = QVBoxLayout(foreground)
        #fg_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        fg_layout.setSpacing(16)
        fg_layout.setContentsMargins(50, 40, 50, 26)
        fg_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self._flag_button = FlagButton(self._translator, foreground)
        self._tagline_label = QLabel(foreground)
        self._tagline_label.setObjectName("taglineLabel")
        self._tagline_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._continue_button = QPushButton(foreground)
        self._continue_button.setObjectName("continueButton")
        self._continue_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._continue_button.clicked.connect(self.continueRequested)
        self._helpinfo = QLabel(foreground)
        self._helpinfo.setObjectName("serversearchDetailLabel")
        self._helpinfo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._helpinfo.setWordWrap(True)
        self._helpinfo.setOpenExternalLinks(True)

        fg_layout.addStretch(1)
        fg_layout.addWidget(self._flag_button, alignment=Qt.AlignmentFlag.AlignHCenter)
        fg_layout.addWidget(self._tagline_label)
        fg_layout.addSpacing(10)
        fg_layout.addWidget(
            self._continue_button, alignment=Qt.AlignmentFlag.AlignHCenter
        )
        fg_layout.addSpacing(24)
        fg_layout.addWidget(self._helpinfo)
        fg_layout.addStretch(1)
        fg_layout.addWidget(self._build_dev_button(foreground), alignment=Qt.AlignmentFlag.AlignRight)
        

        layers.addWidget(foreground)

        self._translator.languageChanged.connect(self._retranslate)
        self._retranslate()

    def _retranslate(self) -> None:
        self._tagline_label.setText(self._translator.tr("welcome.tagline"))
        self._continue_button.setText(self._translator.tr("welcome.continue"))
        self._helpinfo.setText(self._translator.tr("welcome.find_help"))


    # -- dev options (English only, not translated) ---------------------------------

    def _build_dev_button(self, parent: QWidget) -> QToolButton:
        self._ssh_key_path = ""
        self._dev_button = QToolButton(parent)
        self._dev_button.setObjectName("devButton")
        self._dev_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._dev_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)

        menu = QMenu(self._dev_button)
        menu.setObjectName("devMenu")
        self._choose_key_action = menu.addAction("Choose SSH key for Gen4…")
        self._choose_key_action.triggered.connect(self._choose_ssh_key)
        self._remove_key_action = menu.addAction("Remove SSH key")
        self._remove_key_action.triggered.connect(lambda: self.set_ssh_key(""))
        self._dev_button.setMenu(menu)
        self.set_ssh_key("", notify=False)
        return self._dev_button

    def _choose_ssh_key(self) -> None:
        start_dir = Path.home() / ".ssh"
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Choose your SSH public key",
            str(start_dir if start_dir.is_dir() else Path.home()),
            "Public keys (*.pub);;All files (*)",
        )
        if not path:
            return
        try:
            key = Path(path).read_text(encoding="utf-8").strip()
        except (OSError, UnicodeDecodeError):
            key = ""
        if not key.startswith(("ssh-", "ecdsa-")):
            QMessageBox.warning(
                self,
                "Not a public key",
                "That file is not an OpenSSH public key. Pick the .pub file, never the private key.",
            )
            return
        self.set_ssh_key(path)

    def set_ssh_key(self, path: str, notify: bool = True) -> None:
        self._ssh_key_path = path
        if path:
            self._dev_button.setText(f"Dev · SSH: {Path(path).name}")
            self._dev_button.setToolTip(f"Gen4 robots get Dropbear SSH with the key in {path}")
        else:
            self._dev_button.setText("Dev")
            self._dev_button.setToolTip("Developer options")
        self._remove_key_action.setEnabled(bool(path))
        if notify:
            self.sshKeyChanged.emit(path)
