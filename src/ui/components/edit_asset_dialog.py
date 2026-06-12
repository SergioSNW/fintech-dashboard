# src/ui/components/edit_asset_dialog.py

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QDoubleSpinBox,
    QPushButton,
    QWidget
)

class EditAssetDialog(QDialog):
    def __init__(self, parent=None, ticker: str = "", current_amount: float = 0.0):
        super().__init__(parent)
        self.setWindowTitle(f"Modify {ticker}")
        
        # Frameless window configuration
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        
        # FIX: Tells the window system to render the background fully transparent
        # This completely kills the white/gray rectangular ghost corners
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.setFixedSize(360, 220)
        
        master_layout = QVBoxLayout(self)
        master_layout.setContentsMargins(0, 0, 0, 0)
        master_layout.setSpacing(0)

        self.container = QWidget()
        self.container.setObjectName("DialogContainer")
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(20, 16, 20, 20)
        container_layout.setSpacing(14)
        
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)
        
        self.title_label = QLabel(f"Update Position: {ticker.upper()}")
        self.title_label.setObjectName("DialogTitle")
        
        self.close_btn = QPushButton("✕")
        self.close_btn.setObjectName("DialogCloseButton")
        self.close_btn.setCursor(Qt.PointingHandCursor)
        self.close_btn.setFixedSize(24, 24)
        self.close_btn.clicked.connect(self.reject)
        
        header_layout.addWidget(self.title_label, 1)
        header_layout.addWidget(self.close_btn, 0, Qt.AlignRight | Qt.AlignTop)
        
        self.info_label = QLabel("Enter the new absolute total holding amount:")
        self.info_label.setObjectName("DialogInfo")
        
        self.amount_input = QDoubleSpinBox()
        self.amount_input.setObjectName("DialogInput")
        self.amount_input.setDecimals(4)
        self.amount_input.setRange(0.0, 10000000.0)
        self.amount_input.setValue(current_amount)
        self.amount_input.setFocus()
        self.amount_input.selectAll()
        
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setObjectName("CancelButton")
        self.cancel_btn.setCursor(Qt.PointingHandCursor)
        self.cancel_btn.clicked.connect(self.reject)
        
        self.save_btn = QPushButton("Save Changes")
        self.save_btn.setObjectName("SaveButton")
        self.save_btn.setCursor(Qt.PointingHandCursor)
        self.save_btn.clicked.connect(self.accept)
        
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.save_btn)
        
        container_layout.addLayout(header_layout)
        container_layout.addWidget(self.info_label)
        container_layout.addWidget(self.amount_input)
        container_layout.addStretch()
        container_layout.addLayout(btn_layout)
        
        master_layout.addWidget(self.container)
        
        self.setStyleSheet("""
            #DialogContainer {
                background-color: #121217;
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 12px;
            }
            QLabel {
                font-family: 'Segoe UI', sans-serif;
                color: #cbd5e1;
            }
            #DialogTitle {
                font-size: 16px;
                font-weight: 700;
                color: #ffffff;
            }
            #DialogInfo {
                font-size: 13px;
                color: #a0a0a5;
            }
            QDoubleSpinBox#DialogInput {
                background-color: #1a1a22;
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 8px;
                padding: 8px 12px;
                color: #ffffff;
                font-size: 14px;
                font-weight: 600;
            }
            QDoubleSpinBox#DialogInput:focus {
                border-color: #00ff8c;
            }
            QPushButton {
                font-family: 'Segoe UI', sans-serif;
                font-size: 13px;
                font-weight: 700;
                border-radius: 10px;
                padding: 10px 16px;
            }
            QPushButton#SaveButton {
                background-color: #00ff8c;
                color: #0f0f12;
                border: none;
            }
            QPushButton#SaveButton:hover {
                background-color: #00e676;
            }
            QPushButton#CancelButton {
                background-color: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                color: #f8fafc;
            }
            QPushButton#CancelButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
            QPushButton#DialogCloseButton {
                background-color: transparent;
                border: none;
                color: #a0a0a5;
                font-size: 14px;
                font-weight: 400;
                padding: 0px;
            }
            QPushButton#DialogCloseButton:hover {
                color: #ef4444;
            }
        """)

    def get_amount(self) -> float:
        return self.amount_input.value()