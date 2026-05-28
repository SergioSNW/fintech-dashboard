# src/ui/main_window.py

from PySide6.QtCore import Qt, QDateTime, QThreadPool, QTimer
from PySide6.QtGui import QColor, QPainter, QFont
from PySide6.QtCharts import QChart, QChartView, QPieSeries
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
    QDialog,
)
from src.domain.models import Portfolio
from src.ui.components.add_asset_dialog import AddAssetDialog


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Fintech Dashboard")
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setGeometry(100, 100, 1200, 800)
        self.setObjectName("MainWindow")

        self.is_refreshing = False
        self.cooldown_remaining = 0
        
        self.cooldown_timer = QTimer(self)
        self.cooldown_timer.setInterval(1000)
        self.cooldown_timer.timeout.connect(self._update_cooldown_tick)

        self.central_widget = QWidget()
        self.central_widget.setObjectName("CentralWidget")
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(24, 24, 24, 24)
        self.layout.setSpacing(20)

        self.left_panel = QWidget()
        self.left_panel.setObjectName("LeftPanel")
        left_layout = QVBoxLayout(self.left_panel)
        left_layout.setSpacing(15)
        left_layout.setContentsMargins(20, 20, 20, 20)

        self.header_title = QLabel("Fintech Dashboard")
        self.header_title.setObjectName("HeaderTitle")

        self.total_value_label = QLabel("$0.00")
        self.total_value_label.setObjectName("TotalValue")

        self.last_update_label = QLabel("Last update: --")
        self.last_update_label.setObjectName("LastUpdate")

        self.add_asset_button = QPushButton("+ Add Asset")
        self.add_asset_button.setObjectName("AddAssetButton")
        self.add_asset_button.setCursor(Qt.PointingHandCursor)

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setObjectName("RefreshButton")
        self.refresh_button.setCursor(Qt.PointingHandCursor)

        self.minimize_button = QPushButton("—")
        self.minimize_button.setObjectName("WindowControlButton")
        self.minimize_button.setCursor(Qt.PointingHandCursor)
        self.minimize_button.setFixedSize(30, 30)
        self.minimize_button.clicked.connect(self.showMinimized)

        self.close_button = QPushButton("✕")
        self.close_button.setObjectName("CloseButton")
        self.close_button.setCursor(Qt.PointingHandCursor)
        self.close_button.setFixedSize(30, 30)
        self.close_button.clicked.connect(self.close)

        self.top_header = QWidget()
        self.top_header.setObjectName("TopHeader")
        header_layout = QHBoxLayout(self.top_header)
        header_layout.setContentsMargins(20, 20, 20, 20)
        header_layout.setSpacing(12)
        header_layout.addWidget(self.header_title, 0, Qt.AlignLeft)
        header_layout.addStretch(1)
        header_layout.addWidget(self.add_asset_button)
        header_layout.addWidget(self.refresh_button)
        header_layout.addWidget(self.minimize_button)
        header_layout.addWidget(self.close_button)

        summary_layout = QVBoxLayout()
        summary_layout.setContentsMargins(0, 0, 0, 8)
        summary_layout.addWidget(self.total_value_label)
        summary_layout.addWidget(self.last_update_label)

        self.asset_table = QTableWidget(0, 5)
        self.asset_table.setObjectName("AssetTable")
        self.asset_table.setHorizontalHeaderLabels(
            ["Asset Name", "Ticker", "Amount Held", "Live Price", "Total Value"]
        )
        self.asset_table.verticalHeader().setVisible(False)
        self.asset_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.asset_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.asset_table.setAlternatingRowColors(True)
        self.asset_table.setFocusPolicy(Qt.NoFocus)
        self.asset_table.setShowGrid(False)
        self.asset_table.horizontalHeader().setStretchLastSection(True)
        self.asset_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.chart_title = QLabel("Portfolio Allocation")
        self.chart_title.setObjectName("ChartTitle")

        self.allocation_chart = QChart()
        self.allocation_chart.setBackgroundVisible(False)
        self.allocation_chart.legend().setVisible(True)
        self.allocation_chart.legend().setAlignment(Qt.AlignBottom)
        self.allocation_chart.legend().setLabelColor(QColor("#ffffff"))

        self.chart_view = QChartView(self.allocation_chart)
        self.chart_view.setRenderHint(QPainter.Antialiasing)
        self.chart_view.setObjectName("AllocationChart")
        self.chart_view.setMinimumHeight(280)

        left_layout.addLayout(summary_layout)
        left_layout.addWidget(self.asset_table)
        left_layout.addWidget(self.chart_title)
        left_layout.addWidget(self.chart_view)

        self.right_panel = QWidget()
        self.right_panel.setObjectName("RightPanel")
        right_layout = QVBoxLayout(self.right_panel)
        right_layout.setSpacing(15)
        right_layout.setContentsMargins(20, 20, 20, 20)

        self.market_title = QLabel("Global Market Tracker")
        self.market_title.setObjectName("MarketTitle")

        self.market_table = QTableWidget(0, 4)
        self.market_table.setObjectName("MarketTable")
        self.market_table.setHorizontalHeaderLabels(
            ["Asset", "Ticker", "Price", "24h Change"]
        )
        self.market_table.verticalHeader().setVisible(False)
        self.market_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.market_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.market_table.setAlternatingRowColors(True)
        self.market_table.setFocusPolicy(Qt.NoFocus)
        self.market_table.setShowGrid(False)
        self.market_table.horizontalHeader().setStretchLastSection(True)
        self.market_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        right_layout.addWidget(self.market_title)
        right_layout.addWidget(self.market_table)

        body_layout = QHBoxLayout()
        body_layout.setSpacing(18)
        body_layout.addWidget(self.left_panel, 3)
        body_layout.addWidget(self.right_panel, 2)

        self.layout.addWidget(self.top_header)
        self.layout.addLayout(body_layout)
        
        # Apply Cleaned, High-Contrast Stylesheet
        self.setStyleSheet(self._build_stylesheet())

        self.thread_pool = QThreadPool.globalInstance()
        self.manual_refresh_callback = None
        self.asset_added_callback = None

        self.add_asset_button.clicked.connect(self.open_add_asset_dialog)
        self.refresh_button.clicked.connect(self.on_refresh_clicked)

    def _build_stylesheet(self) -> str:
        return """
        #MainWindow {
            background-color: #0f0f12;
        }
        #CentralWidget {
            background-color: #121217;
            border: 1px solid rgba(255, 255, 255, 0.15);
            border-radius: 12px;
        }
        QLabel {
            color: #f8fafc;
            font-family: 'Segoe UI', sans-serif;
        }
        #HeaderTitle {
            font-size: 24px;
            font-weight: 700;
            color: #ffffff;
        }
        #ChartTitle {
            font-size: 16px; 
            font-weight: 700; 
            color: #ffffff; 
            margin-top: 10px;
            margin-bottom: 4px;
        }
        #TotalValue {
            font-size: 48px;
            font-weight: 800;
            color: #00ff8c;
            margin-top: 8px;
        }
        #LastUpdate {
            font-size: 13px;
            color: #cbd5e1;
            margin-top: 6px;
        }
        QPushButton#RefreshButton,
        QPushButton#AddAssetButton {
            background-color: rgba(255, 255, 255, 0.08);
            border: 1px solid rgba(255, 255, 255, 0.12);
            color: #f8fafc;
            border-radius: 12px;
            padding: 12px 20px;
            font-size: 13px;
            font-weight: 700;
            min-width: 150px;
        }
        QPushButton#RefreshButton:hover,
        QPushButton#AddAssetButton:hover {
            background-color: rgba(255, 255, 255, 0.12);
        }
        QPushButton#RefreshButton:disabled,
        QPushButton#AddAssetButton:disabled {
            background-color: rgba(255, 255, 255, 0.02);
            color: #64748b;
            border-color: rgba(255, 255, 255, 0.04);
        }
        QPushButton#WindowControlButton, QPushButton#CloseButton {
            background-color: transparent;
            border: none;
            color: #a0a0a5;
            font-size: 14px;
        }
        #LeftPanel, #RightPanel {
            background-color: #1a1a22;
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 16px;
        }
        #TopHeader {
            background-color: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 14px;
        }
        #MarketTitle {
            color: #ffffff;
            font-size: 18px;
            font-weight: 700;
            margin-bottom: 14px;
        }
        QChartView#AllocationChart {
            background-color: #1a1a22;
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 14px;
        }
        QTableWidget {
            background-color: #22222b;
            alternate-background-color: #1e1e26;
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 10px;
            color: #e2e8f0;
            gridline-color: transparent;
        }
        QTableWidget::item {
            padding: 10px;
            color: #f1f5f9;
        }
        QHeaderView::section {
            background-color: #2d2d38 !important;
            color: #ffffff !important;
            border: none;
            border-bottom: 2px solid #00ff8c;
            padding: 8px;
            font-size: 13px;
            font-weight: 700;
        }
        """

    def setLastUpdateText(self, text: str):
        self.last_update_label.setText(text)

    def setPortfolio(self, portfolio: Portfolio):
        self.total_value_label.setText(f"${portfolio.total_value:,.2f}")
        timestamp = QDateTime.currentDateTime().toString("MMM d, yyyy hh:mm:ss ap")
        self.last_update_label.setText(f"Last update: {timestamp}")

        self.asset_table.setUpdatesEnabled(False)
        self.asset_table.setRowCount(len(portfolio.assets))
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
                self.asset_table.setItem(row, col, item)

        self.asset_table.setUpdatesEnabled(True)
        self.update_allocation_chart(portfolio)

    def handle_portfolio_update(self, updated_portfolio: Portfolio):
        self.setPortfolio(updated_portfolio)
        self.is_refreshing = False
        self._check_and_enable_ui()

    def handle_market_data_update(self, market_assets):
        self.setMarketData(market_assets)

    def on_refresh_clicked(self):
        if self.is_refreshing or self.cooldown_remaining > 0:
            return
            
        if self.manual_refresh_callback:
            self.is_refreshing = True
            self.cooldown_remaining = 3
            self.setRefreshEnabled(False)
            self.refresh_button.setText(f"Refreshing ({self.cooldown_remaining}s)...")
            
            self.cooldown_timer.start()
            self.manual_refresh_callback()

    def _update_cooldown_tick(self):
        if self.cooldown_remaining > 0:
            self.cooldown_remaining -= 1
            
        if self.cooldown_remaining > 0:
            self.refresh_button.setText(f"Refreshing ({self.cooldown_remaining}s)...")
        else:
            self.cooldown_timer.stop()
            self._check_and_enable_ui()

    def _check_and_enable_ui(self):
        if not self.is_refreshing and self.cooldown_remaining == 0:
            self.refresh_button.setText("Refresh")
            self.setRefreshEnabled(True)

    def update_allocation_chart(self, portfolio: Portfolio):
        self.allocation_chart.removeAllSeries()
        series = QPieSeries()
        palette = ["#00e676", "#3b82f6", "#f97316", "#8b5cf6", "#14b8a6"]

        for idx, asset in enumerate(portfolio.assets):
            if asset.total_value > 0.0:
                slice = series.append(asset.ticker, asset.total_value)
                slice.setLabel(f"{asset.ticker} {asset.total_value:,.2f}")
                slice.setLabelVisible(True)
                slice.setLabelColor(QColor("#ffffff"))
                slice.setBrush(QColor(palette[idx % len(palette)]))

        if series.count() == 0:
            series.append("No Data", 1.0).setBrush(QColor("#2a2a35"))

        self.allocation_chart.addSeries(series)
        self.allocation_chart.createDefaultAxes()
        self.allocation_chart.legend().setVisible(True)
        self.allocation_chart.legend().setLabelColor(QColor("#ffffff"))

    def setMarketData(self, market_assets):
        self.market_table.setUpdatesEnabled(False)
        self.market_table.setRowCount(len(market_assets))

        for row, asset in enumerate(market_assets):
            name_item = QTableWidgetItem(asset.name)
            ticker_item = QTableWidgetItem(asset.ticker)
            price_item = QTableWidgetItem(f"${asset.price:,.2f}")
            change_item = QTableWidgetItem(f"{asset.change_24h:+.2f}%")

            for item in [name_item, ticker_item, price_item, change_item]:
                item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)

            if asset.change_24h >= 0:
                change_item.setForeground(QColor("#00e676"))
            else:
                change_item.setForeground(QColor("#ef4444"))

            self.market_table.setItem(row, 0, name_item)
            self.market_table.setItem(row, 1, ticker_item)
            self.market_table.setItem(row, 2, price_item)
            self.market_table.setItem(row, 3, change_item)

        self.market_table.setUpdatesEnabled(True)

    def setAssetAddedCallback(self, callback):
        self.asset_added_callback = callback

    def setManualRefreshCallback(self, callback):
        self.manual_refresh_callback = callback

    def open_add_asset_dialog(self):
        dialog = AddAssetDialog(self)
        if dialog.exec() == QDialog.Accepted:
            ticker, amount = dialog.get_data()
            if ticker and amount > 0.0 and self.asset_added_callback:
                self.asset_added_callback(ticker, amount)

    def setRefreshEnabled(self, enabled: bool):
        self.refresh_button.setEnabled(enabled)
        self.add_asset_button.setEnabled(enabled)