# src/ui/components/add_asset_dialog.py

from PySide6.QtCore import Qt, QEvent
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QDoubleSpinBox,
    QPushButton,
    QWidget,
    QComboBox,
    QListView,
    QStyledItemDelegate,
    QStyle,
    QFrame
)

class DropdownItemDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)

    def paint(self, painter, option, index):
        painter.save()
        is_light = getattr(self.parent(), "is_light_theme", False)
        
        if option.state & QStyle.State_Selected:
            bg_color = QColor("#e2e8f0") if is_light else QColor("#2d2d38")
            text_color = QColor("#0f172a") if is_light else QColor("#00ff8c")
        else:
            bg_color = QColor("#ffffff") if is_light else QColor("#1a1a22")
            text_color = QColor("#334155") if is_light else QColor("#f8fafc")

        painter.fillRect(option.rect, bg_color)
        painter.setPen(text_color)
        
        text = index.data(Qt.DisplayRole)
        text_rect = option.rect.adjusted(12, 0, 0, 0)
        painter.drawText(text_rect, Qt.AlignVCenter | Qt.AlignLeft, text)
        painter.restore()


class AddAssetDialog(QDialog):
    def __init__(self, parent=None, is_light_theme=False):
        super().__init__(parent)
        self.is_light_theme = is_light_theme
        self.setWindowTitle("Add Asset")
        
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(380, 260)

        master_layout = QVBoxLayout(self)
        master_layout.setContentsMargins(0, 0, 0, 0)
        master_layout.setSpacing(0)

        self.container = QWidget()
        self.container.setObjectName("DialogContainer")
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(24, 18, 24, 24)
        container_layout.setSpacing(14)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)

        self.title_label = QLabel("Add New Asset")
        self.title_label.setObjectName("DialogTitle")

        self.close_btn = QPushButton("✕")
        self.close_btn.setObjectName("DialogCloseButton")
        self.close_btn.setCursor(Qt.PointingHandCursor)
        self.close_btn.setFixedSize(24, 24)
        self.close_btn.clicked.connect(self.reject)

        header_layout.addWidget(self.title_label, 1)
        header_layout.addWidget(self.close_btn, 0, Qt.AlignRight | Qt.AlignTop)

        form_layout = QVBoxLayout()
        form_layout.setSpacing(12)

        self.ticker_label = QLabel("Select Crypto Asset:")
        self.ticker_label.setObjectName("FieldLabel")
        
        self.ticker_dropdown = QComboBox()
        self.ticker_dropdown.setObjectName("DialogDropdown")
        self.ticker_dropdown.setCursor(Qt.PointingHandCursor)
        self.ticker_dropdown.addItems(["BTC", "ETH", "SOL", "ADA", "DOT", "XRP", "LINK"])
        self.ticker_dropdown.setMaxVisibleItems(10)
        
        # Hard platform overrides to prevent native frame leaks
        dropdown_view = QListView()
        dropdown_view.is_light_theme = self.is_light_theme  
        dropdown_view.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        dropdown_view.setAttribute(Qt.WA_TranslucentBackground)
        dropdown_view.setFrameShape(QFrame.NoFrame)
        dropdown_view.setItemDelegate(DropdownItemDelegate(dropdown_view))
        self.ticker_dropdown.setView(dropdown_view)

        self.amount_label = QLabel("Amount Held:")
        self.amount_label.setObjectName("FieldLabel")

        self.amount_input = QDoubleSpinBox()
        self.amount_input.setObjectName("DialogInput")
        self.amount_input.setDecimals(4)
        self.amount_input.setRange(0.0, 10000000.0)

        form_layout.addWidget(self.ticker_label)
        form_layout.addWidget(self.ticker_dropdown)
        form_layout.addWidget(self.amount_label)
        form_layout.addWidget(self.amount_input)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setObjectName("CancelButton")
        self.cancel_btn.setCursor(Qt.PointingHandCursor)
        self.cancel_btn.clicked.connect(self.reject)

        self.add_btn = QPushButton("Add to Portfolio")
        self.add_btn.setObjectName("AddButton")
        self.add_btn.setCursor(Qt.PointingHandCursor)
        self.add_btn.clicked.connect(self.accept)

        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.add_btn)

        container_layout.addLayout(header_layout)
        container_layout.addLayout(form_layout)
        container_layout.addStretch()
        container_layout.addLayout(btn_layout)

        master_layout.addWidget(self.container)
        self.setStyleSheet(self._build_stylesheet())

    def _build_stylesheet(self) -> str:
        if self.is_light_theme:
            return """
                #DialogContainer { background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; }
                QLabel { font-family: 'Segoe UI', sans-serif; color: #334155; }
                #DialogTitle { font-size: 16px; font-weight: 700; color: #0f172a; }
                #FieldLabel { font-size: 12px; font-weight: 600; color: #64748b; margin-bottom: -2px; }
                
                QDoubleSpinBox#DialogInput, QComboBox#DialogDropdown {
                    font-family: 'Segoe UI', sans-serif; background-color: #f8fafc;
                    border: 1px solid #cbd5e1; border-radius: 8px; padding: 8px 12px; color: #0f172a; font-size: 13px; font-weight: 600;
                }
                QComboBox#DialogDropdown::drop-down { border: none; background: transparent; }
                
                QComboBox#DialogDropdown QAbstractItemView { 
                    font-family: 'Segoe UI', sans-serif; font-size: 13px; font-weight: 600;
                    background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 8px;
                    color: #0f172a; outline: none;
                }
                
                QDoubleSpinBox#DialogInput::up-button, QDoubleSpinBox#DialogInput::down-button {
                    background: transparent; border: none; width: 20px;
                }
                QDoubleSpinBox#DialogInput::up-button { subcontrol-origin: border; subcontrol-position: top right; margin-right: 4px; margin-top: 2px; }
                QDoubleSpinBox#DialogInput::down-button { subcontrol-origin: border; subcontrol-position: bottom right; margin-right: 4px; margin-bottom: 2px; }
                
                QDoubleSpinBox#DialogInput:focus, QComboBox#DialogDropdown:focus { border-color: #3b82f6; }
                QPushButton { font-family: 'Segoe UI', sans-serif; font-size: 13px; font-weight: 700; border-radius: 10px; padding: 10px 16px; }
                QPushButton#AddButton { background-color: #3b82f6; color: #ffffff; border: none; }
                QPushButton#AddButton:hover { background-color: #2563eb; }
                QPushButton#CancelButton { background-color: #f1f5f9; border: 1px solid #cbd5e1; color: #334155; }
                QPushButton#CancelButton:hover { background-color: #e2e8f0; }
                QPushButton#DialogCloseButton { background-color: transparent; border: none; color: #64748b; font-size: 14px; padding: 0px; }
                QPushButton#DialogCloseButton:hover { color: #ef4444; }
            """
        else:
            return """
                #DialogContainer { background-color: #121217; border: 1px solid rgba(255, 255, 255, 0.15); border-radius: 12px; }
                QLabel { font-family: 'Segoe UI', sans-serif; color: #cbd5e1; }
                #DialogTitle { font-size: 16px; font-weight: 700; color: #ffffff; }
                #FieldLabel { font-size: 12px; font-weight: 600; color: #a0a0a5; margin-bottom: -2px; }
                
                QDoubleSpinBox#DialogInput, QComboBox#DialogDropdown {
                    font-family: 'Segoe UI', sans-serif; background-color: #1a1a22;
                    border: 1px solid rgba(255, 255, 255, 0.12); border-radius: 8px; padding: 8px 12px; color: #ffffff; font-size: 13px; font-weight: 600;
                }
                QComboBox#DialogDropdown::drop-down { border: none; background: transparent; }
                
                QComboBox#DialogDropdown QAbstractItemView { 
                    font-family: 'Segoe UI', sans-serif; font-size: 13px; font-weight: 600;
                    background-color: #1a1a22; border: 1px solid rgba(255, 255, 255, 0.15); border-radius: 8px;
                    color: #f8fafc; outline: none;
                }
                
                QDoubleSpinBox#DialogInput::up-button, QDoubleSpinBox#DialogInput::down-button {
                    background: transparent; border: none; width: 20px;
                }
                QDoubleSpinBox#DialogInput::up-button { subcontrol-origin: border; subcontrol-position: top right; margin-right: 4px; margin-top: 2px; }
                QDoubleSpinBox#DialogInput::down-button { subcontrol-origin: border; subcontrol-position: bottom right; margin-right: 4px; margin-bottom: 2px; }
                
                QDoubleSpinBox#DialogInput:focus, QComboBox#DialogDropdown:focus { border-color: #00ff8c; }
                QPushButton { font-family: 'Segoe UI', sans-serif; font-size: 13px; font-weight: 700; border-radius: 10px; padding: 10px 16px; }
                QPushButton#AddButton { background-color: #00ff8c; color: #0f0f12; border: none; }
                QPushButton#AddButton:hover { background-color: #00e676; }
                QPushButton#CancelButton { background-color: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); color: #f8fafc; }
                QPushButton#CancelButton:hover { background-color: rgba(255, 255, 255, 0.1); }
                QPushButton#DialogCloseButton { background-color: transparent; border: none; color: #a0a0a5; font-size: 14px; padding: 0px; }
                QPushButton#DialogCloseButton:hover { color: #ef4444; }
            """

    def event(self, event):
        if event.type() == QEvent.WindowDeactivate:
            if self.ticker_dropdown.view() and self.ticker_dropdown.view().isVisible():
                return super().event(event)
            self.reject()
            return True
        return super().event(event)

    def get_data(self):
        return self.ticker_dropdown.currentText(), self.amount_input.value()