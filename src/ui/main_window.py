from PySide6.QtCore import Qt, QDateTime, QThreadPool
from PySide6.QtWidgets import (
    QHeaderView,
    QLabel,
    QMainWindow,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
)
from src.domain.models import Portfolio
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Fintech Dashboard")
        self.setGeometry(100, 100, 1100, 700)
        self.setObjectName("MainWindow")

        self.central_widget = QWidget()
        self.central_widget.setObjectName("CentralWidget")
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(24, 24, 24, 24)
        self.layout.setSpacing(20)

        self.header_title = QLabel("Total Portfolio Value")
        self.header_title.setObjectName("HeaderTitle")

        self.total_value_label = QLabel("$0.00")
        self.total_value_label.setObjectName("TotalValue")

        self.last_update_label = QLabel("Last update: --")
        self.last_update_label.setObjectName("LastUpdate")

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setObjectName("RefreshButton")
        self.refresh_button.setCursor(Qt.PointingHandCursor)

        header_layout = QHBoxLayout()
        header_layout.addWidget(self.header_title, 0, Qt.AlignLeft)
        header_layout.addStretch(1)
        header_layout.addWidget(self.refresh_button, 0, Qt.AlignRight)

        summary_layout = QVBoxLayout()
        summary_layout.addWidget(self.total_value_label)
        summary_layout.addWidget(self.last_update_label)

        self.layout.addLayout(header_layout)
        self.layout.addLayout(summary_layout)

        self.table_widget = QTableWidget(0, 5)
        self.table_widget.setObjectName("AssetTable")
        self.table_widget.setHorizontalHeaderLabels(
            ["Asset Name", "Ticker", "Amount Held", "Live Price", "Total Value"]
        )
        self.table_widget.verticalHeader().setVisible(False)
        self.table_widget.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_widget.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_widget.setAlternatingRowColors(True)
        self.table_widget.setFocusPolicy(Qt.NoFocus)
        self.table_widget.setShowGrid(False)
        self.table_widget.horizontalHeader().setStretchLastSection(True)
        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.layout.addWidget(self.table_widget)
        self.setStyleSheet(self._build_stylesheet())

        self.thread_pool = QThreadPool.globalInstance()
        self.current_worker = None

    def _build_stylesheet(self) -> str:
        return """
        #MainWindow {
            background-color: #121214;
        }
        #CentralWidget {
            background-color: transparent;
        }
        QLabel {
            color: #e5e7eb;
            font-family: 'Segoe UI', sans-serif;
        }
        #HeaderTitle {
            font-size: 24px;
            font-weight: 700;
            color: #ffffff;
        }
        #TotalValue {
            font-size: 42px;
            font-weight: 800;
            color: #00e676;
            margin-top: 8px;
        }
        #LastUpdate {
            font-size: 13px;
            color: #a0a0a8;
            margin-top: 6px;
        }
        QPushButton#RefreshButton {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1d4ed8, stop:1 #0ea5e9);
            border: 1px solid #0f172a;
            border-radius: 10px;
            color: white;
            padding: 10px 18px;
            font-size: 13px;
            font-weight: 600;
            min-width: 120px;
        }
        QPushButton#RefreshButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2563eb, stop:1 #38bdf8);
        }
        QPushButton#RefreshButton:pressed {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1d4ed8, stop:1 #0ea5e9);
        }
        QTableWidget {
            background-color: #1e1e24;
            border: 1px solid #2a2a32;
            border-radius: 16px;
            color: #e5e7eb;
            gridline-color: #2a2a32;
            padding: 12px;
        }
        QHeaderView::section {
            background-color: #18181b;
            color: #94a3b8;
            border: none;
            padding: 12px 8px;
            font-size: 12px;
            font-weight: 600;
        }
        QTableWidget::item {
            border: none;
            padding: 12px 8px;
        }
        QTableWidget::item:selected {
            background-color: #27272a;
        }
        """

    def setPortfolio(self, portfolio: Portfolio):
        self.total_value_label.setText(f"${portfolio.total_value:,.2f}")
        timestamp = QDateTime.currentDateTime().toString("MMM d, yyyy hh:mm:ss ap")
        self.last_update_label.setText(f"Last update: {timestamp}")

        self.table_widget.setUpdatesEnabled(False)
        self.table_widget.setRowCount(len(portfolio.assets))
        for row, asset in enumerate(portfolio.assets):
            name = asset.name or asset.ticker
            ticker = asset.ticker
            amount_text = f"{asset.amount:,.4f}" if isinstance(asset.amount, float) else str(asset.amount)
            price_text = f"${asset.price:,.2f}" if getattr(asset, 'price', None) is not None else "--"
            total_text = f"${asset.total_value:,.2f}" if getattr(asset, 'total_value', None) is not None else "--"

            cells = [name, ticker, amount_text, price_text, total_text]
            for col, value in enumerate(cells):
                item = QTableWidgetItem(value)
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
                item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                self.table_widget.setItem(row, col, item)

        self.table_widget.setUpdatesEnabled(True)

    def setRefreshEnabled(self, enabled: bool):
        self.refresh_button.setEnabled(enabled)

    def setLastUpdateText(self, text: str):
        self.last_update_label.setText(text)


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication

    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()