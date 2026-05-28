from PySide6.QtCore import Qt
from PySide6.QtGui import QDoubleValidator
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QVBoxLayout,
)


class AddAssetDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Asset")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setModal(True)
        self.setFixedSize(380, 220)

        self.ticker_input = QComboBox()
        self.ticker_input.addItems([
            "BTC", "ETH", "SOL", "ADA", "DOT",
            "XRP", "LINK", "DOGE", "AVAX", "MATIC",
        ])
        self.ticker_input.setEditable(False)
        self.ticker_input.setInsertPolicy(QComboBox.NoInsert)
        self.ticker_input.setMaxVisibleItems(10)
        
        # FIX: Force the dropdown popup view to auto-collapse and submit selection instantly on index shift
        self.ticker_input.currentIndexChanged.connect(self.ticker_input.hidePopup)

        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("e.g. 1.5")
        self.amount_input.setValidator(QDoubleValidator(0.0, 1e9, 8, self))

        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        form_layout.addRow("Asset Ticker", self.ticker_input)
        form_layout.addRow("Amount", self.amount_input)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self.save_button = self.button_box.button(QDialogButtonBox.Save)
        self.cancel_button = self.button_box.button(QDialogButtonBox.Cancel)
        self.save_button.setObjectName("SaveButton")
        self.cancel_button.setObjectName("CancelButton")
        
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(18)
        layout.addLayout(form_layout)
        layout.addWidget(self.button_box)
        self.setLayout(layout)

        self.setStyleSheet(self._build_stylesheet())

    def _build_stylesheet(self) -> str:
        return """
        QDialog {
            background-color: #1a1a22;
            border: 1px solid rgba(255, 255, 255, 0.15);
            border-radius: 14px;
        }
        QLabel {
            color: #ffffff;
            font-size: 13px;
            font-family: 'Segoe UI', sans-serif;
        }
        QComboBox, QLineEdit {
            background-color: #2a2a32;
            color: #ffffff;
            border: 1px solid rgba(255, 255, 255, 0.25);
            border-radius: 6px;
            padding: 8px 12px;
            min-height: 38px;
            font-size: 13px;
        }
        QLineEdit:focus, QComboBox:focus {
            border: 1px solid #00ff8c;
        }
        QComboBox::drop-down {
            border: none;
            background: transparent;
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 26px;
        }
        QComboBox QAbstractItemView {
            background-color: #1e1e24;
            color: #ffffff;
            border: 1px solid rgba(255, 255, 255, 0.25);
            border-radius: 6px;
            selection-background-color: rgba(0, 255, 140, 0.25);
            selection-color: #ffffff;
            padding: 6px;
        }
        QDialogButtonBox QPushButton {
            border-radius: 10px;
            padding: 10px 18px;
            min-width: 90px;
            font-weight: 600;
            font-size: 13px;
        }
        QPushButton#SaveButton {
            background-color: rgba(0, 255, 140, 0.18);
            color: #00ff8c;
            border: 1px solid rgba(0, 255, 140, 0.4);
        }
        QPushButton#SaveButton:hover {
            background-color: rgba(0, 255, 140, 0.26);
        }
        QPushButton#CancelButton {
            background-color: #2a2a32;
            color: #e5e7eb;
            border: 1px solid rgba(255, 255, 255, 0.12);
        }
        QPushButton#CancelButton:hover {
            background-color: #343a42;
        }
        """

    def get_data(self):
        ticker = self.ticker_input.currentText().strip().upper()
        try:
            amount = float(self.amount_input.text().strip())
        except ValueError:
            amount = 0.0
        return ticker, amount