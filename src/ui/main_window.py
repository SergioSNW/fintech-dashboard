# src/ui/main_window.py

import asyncio
from PySide6.QtCore import Qt, QDateTime, QTimer, QPoint, QEvent
from PySide6.QtGui import QColor, QPainter, QPen, QPainterPath, QAction
from PySide6.QtCharts import QChart, QChartView, QPieSeries, QLineSeries, QDateTimeAxis, QValueAxis
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
    QStyledItemDelegate,
    QStyle,
    QComboBox,
    QMenu,
    QListView,
    QAbstractItemView,
    QFrame
)
from src.domain.models import Portfolio
from src.ui.components.add_asset_dialog import AddAssetDialog, DropdownItemDelegate


class SparklineDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)

    def paint(self, painter, option, index):
        prices = index.data(Qt.UserRole)
        change_24h = index.data(Qt.UserRole + 1)

        if not prices or len(prices) < 2:
            super().paint(painter, option, index)
            return

        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)

        is_light = getattr(self.parent(), "is_light_theme", False)

        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())
        else:
            if is_light:
                bg_color = QColor("#f1f5f9") if index.row() % 2 == 1 else QColor("#ffffff")
            else:
                bg_color = QColor("#1e1e26") if index.row() % 2 == 1 else QColor("#22222b")
            painter.fillRect(option.rect, bg_color)

        padding_x = 10
        padding_y = 6
        x = option.rect.x() + padding_x
        y = option.rect.y() + padding_y
        width = option.rect.width() - (padding_x * 2)
        height = option.rect.height() - (padding_y * 2)

        min_p = min(prices)
        max_p = max(prices)
        price_range = max_p - min_p if max_p != min_p else 1.0

        path = QPainterPath()
        for i, price in enumerate(prices):
            pt_x = x + (i / (len(prices) - 1)) * width
            pt_y = y + height - ((price - min_p) / price_range) * height
            if i == 0:
                path.moveTo(pt_x, pt_y)
            else:
                path.lineTo(pt_x, pt_y)

        if change_24h >= 0:
            line_color = QColor("#00c853") if is_light else QColor("#00ff8c")
        else:
            line_color = QColor("#ea580c") if is_light else QColor("#ef4444")

        pen = QPen(line_color, 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        painter.setPen(pen)
        painter.drawPath(path)
        painter.restore()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Fintech Dashboard")
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setGeometry(100, 100, 1420, 820)
        self.setObjectName("MainWindow")

        self.is_light_theme = False
        self.is_refreshing = False
        self.cooldown_remaining = 0
        self.portfolio_reference = None
        
        # Memory caching system to actively save CoinGecko standard API limits
        self.chart_cache = {}
        self.active_chart_ticker = None

        self.current_currency_symbol = "$"
        self.currency_rates = {"USD": 1.0, "EUR": 0.92, "GBP": 0.79}
        self.active_currency_key = "USD"

        # Explicit name mapping utility to translate raw tickers to premium names
        self.asset_name_map = {
            "BTC": "Bitcoin",
            "ETH": "Ethereum",
            "SOL": "Solana",
            "ADA": "Cardano",
            "DOT": "Polkadot",
            "XRP": "Ripple",
            "LINK": "Chainlink"
        }

        self.cooldown_timer = QTimer(self)
        self.cooldown_timer.setInterval(1000)
        self.cooldown_timer.timeout.connect(self._update_cooldown_tick)
        
        self.watchdog_timer = QTimer(self)
        self.watchdog_timer.setSingleShot(True)
        self.watchdog_timer.setInterval(6000)
        self.watchdog_timer.timeout.connect(self._handle_watchdog_timeout)

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

        self.theme_toggle_btn = QPushButton("🌙")
        self.theme_toggle_btn.setObjectName("ThemeToggleButton")
        self.theme_toggle_btn.setCursor(Qt.PointingHandCursor)
        self.theme_toggle_btn.setFixedSize(40, 40)
        self.theme_toggle_btn.clicked.connect(self.toggle_theme)

        self.currency_dropdown = QComboBox()
        self.currency_dropdown.setObjectName("CurrencyDropdown")
        self.currency_dropdown.addItems(["USD ($)", "EUR (€)", "GBP (£)"])
        self.currency_dropdown.setCursor(Qt.PointingHandCursor)
        self.currency_dropdown.setMaxVisibleItems(8)
        self.currency_dropdown.setEditable(False)
        self.currency_dropdown.setStyleSheet("QComboBox#CurrencyDropdown { padding-right: 28px; }")
        
        currency_view = QListView()
        currency_view.setObjectName("CurrencyDropdownPopup")
        currency_view.is_light_theme = self.is_light_theme
        currency_view.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        currency_view.setFrameShape(QFrame.NoFrame)
        currency_view.setFrameShadow(QFrame.Plain)
        currency_view.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        currency_view.setItemDelegate(DropdownItemDelegate(currency_view))
        currency_view.setStyleSheet("QListView#CurrencyDropdownPopup { background: transparent; border: none; }")
        self.currency_dropdown.setView(currency_view)
        
        self.currency_dropdown.currentTextChanged.connect(self._on_currency_changed)

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
        header_layout.setContentsMargins(20, 14, 20, 14)
        header_layout.setSpacing(12)
        header_layout.addWidget(self.header_title, 0, Qt.AlignVCenter)
        header_layout.addStretch(1)
        header_layout.addWidget(self.theme_toggle_btn, 0, Qt.AlignVCenter)
        header_layout.addWidget(self.currency_dropdown, 0, Qt.AlignVCenter)
        header_layout.addWidget(self.add_asset_button, 0, Qt.AlignVCenter)
        header_layout.addWidget(self.refresh_button, 0, Qt.AlignVCenter)
        header_layout.addWidget(self.minimize_button, 0, Qt.AlignVCenter)
        header_layout.addWidget(self.close_button, 0, Qt.AlignVCenter)

        self.top_header.installEventFilter(self)

        summary_layout = QVBoxLayout()
        summary_layout.setContentsMargins(0, 0, 0, 8)
        summary_layout.addWidget(self.total_value_label)
        summary_layout.addWidget(self.last_update_label)

        # 5 Columns layout: Asset, Amount Held, Live Price, Total Value, Actions
        self.asset_table = QTableWidget(0, 5)
        self.asset_table.setObjectName("AssetTable")
        self.asset_table.setHorizontalHeaderLabels(
            ["Asset", "Amount Held", "Live Price", "Total Value", "Actions"]
        )
        self.asset_table.verticalHeader().setVisible(False)
        self.asset_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.asset_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.asset_table.setAlternatingRowColors(True)
        self.asset_table.setFocusPolicy(Qt.NoFocus)
        self.asset_table.setShowGrid(False)
        self.asset_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.asset_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        
        # Consistent layout padding height supporting custom rows safely
        self.asset_table.verticalHeader().setDefaultSectionSize(48)
        self.asset_table.cellClicked.connect(self._on_asset_row_clicked)

        # Bottom Graphic Allocation and Trend Layout Switcher
        self.chart_container = QWidget()
        chart_container_layout = QHBoxLayout(self.chart_container)
        chart_container_layout.setContentsMargins(0, 0, 0, 0)
        chart_container_layout.setSpacing(14)

        # Left Column: Pie Composition Graph
        pie_wrapper = QWidget()
        pie_layout = QVBoxLayout(pie_wrapper)
        pie_layout.setContentsMargins(0, 0, 0, 0)
        self.chart_title = QLabel("Portfolio Allocation")
        self.chart_title.setObjectName("ChartTitle")
        self.allocation_chart = QChart()
        self.allocation_chart.setBackgroundVisible(False)
        self.allocation_chart.legend().setVisible(True)
        self.allocation_chart.legend().setAlignment(Qt.AlignBottom)
        self.chart_view = QChartView(self.allocation_chart)
        self.chart_view.setRenderHint(QPainter.Antialiasing)
        self.chart_view.setObjectName("AllocationChart")
        self.chart_view.setMinimumHeight(280)
        pie_layout.addWidget(self.chart_title)
        pie_layout.addWidget(self.chart_view)

        # Right Column: Historical Interactive Trend Graph Layer
        trend_wrapper = QWidget()
        trend_layout = QVBoxLayout(trend_wrapper)
        trend_layout.setContentsMargins(0, 0, 0, 0)
        self.trend_title = QLabel("Market Analytics (7-Day History)")
        self.trend_title.setObjectName("ChartTitle")
        self.historical_chart = QChart()
        self.historical_chart.setBackgroundVisible(False)
        self.historical_chart_view = QChartView(self.historical_chart)
        self.historical_chart_view.setRenderHint(QPainter.Antialiasing)
        self.historical_chart_view.setObjectName("AllocationChart")
        self.historical_chart_view.setMinimumHeight(280)
        trend_layout.addWidget(self.trend_title)
        trend_layout.addWidget(self.historical_chart_view)

        chart_container_layout.addWidget(pie_wrapper, 1)
        chart_container_layout.addWidget(trend_wrapper, 1)

        left_layout.addLayout(summary_layout)
        left_layout.addWidget(self.asset_table)
        left_layout.addWidget(self.chart_container)

        self.right_panel = QWidget()
        self.right_panel.setObjectName("RightPanel")
        right_layout = QVBoxLayout(self.right_panel)
        right_layout.setSpacing(15)
        right_layout.setContentsMargins(20, 20, 20, 20)

        self.market_title = QLabel("Global Market Tracker")
        self.market_title.setObjectName("MarketTitle")

        self.market_table = QTableWidget(0, 5)
        self.market_table.setObjectName("MarketTable")
        self.market_table.setHorizontalHeaderLabels(
            ["Asset", "Ticker", "Price", "24h Change", "Trend"]
        )
        self.market_table.verticalHeader().setVisible(False)
        self.market_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.market_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.market_table.setAlternatingRowColors(True)
        self.market_table.setFocusPolicy(Qt.NoFocus)
        self.market_table.setShowGrid(False)
        self.market_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.market_table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.market_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.market_table.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        self.market_table.cellClicked.connect(self._on_market_row_clicked)
        
        self.sparkline_delegate = SparklineDelegate(self)
        self.market_table.setItemDelegateForColumn(4, self.sparkline_delegate)

        right_layout.addWidget(self.market_title)
        right_layout.addWidget(self.market_table)

        body_layout = QHBoxLayout()
        body_layout.setSpacing(18)
        body_layout.addWidget(self.left_panel, 4)
        body_layout.addWidget(self.right_panel, 3)

        self.layout.addWidget(self.top_header)
        self.layout.addLayout(body_layout)
        
        self.setStyleSheet(self._build_stylesheet())

        self.manual_refresh_callback = None
        self.asset_added_callback = None
        self.asset_edited_callback = None
        self.asset_deleted_callback = None

        self.add_asset_button.clicked.connect(self.open_add_asset_dialog)
        self.refresh_button.clicked.connect(self.on_refresh_clicked)
        
        # Placeholder text on initialization
        self._set_historical_chart_message("Select any row asset to generate historical metrics")

    def eventFilter(self, watched, event):
        if watched == self.top_header and event.type() == QEvent.MouseButtonPress:
            if event.button() == Qt.LeftButton:
                window_handle = self.windowHandle()
                if window_handle:
                    window_handle.startSystemMove()
                    return True
        return super().eventFilter(watched, event)

    def toggle_theme(self):
        self.is_light_theme = not self.is_light_theme
        self.theme_toggle_btn.setText("☀️" if self.is_light_theme else "🌙")
        self.currency_dropdown.view().is_light_theme = self.is_light_theme
        self.setStyleSheet(self._build_stylesheet())
        if self.portfolio_reference:
            self.setPortfolio(self.portfolio_reference)
        if self.active_chart_ticker:
            self.update_historical_trend_chart(self.active_chart_ticker, self.chart_cache.get(self.active_chart_ticker, []))

    def _build_stylesheet(self) -> str:
        if self.is_light_theme:
            return """
            #MainWindow { background-color: #f1f5f9; }
            #CentralWidget { background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 12px; }
            QLabel { color: #334155; font-family: 'Segoe UI', sans-serif; }
            #HeaderTitle { font-size: 24px; font-weight: 700; color: #0f172a; }
            #ChartTitle { font-size: 16px; font-weight: 700; color: #0f172a; margin-top: 10px; margin-bottom: 4px; }
            #TotalValue { font-size: 48px; font-weight: 800; color: #2563eb; margin-top: 8px; }
            #LastUpdate { font-size: 13px; color: #64748b; margin-top: 6px; }
            
            QPushButton#RefreshButton, QPushButton#AddAssetButton {
                background-color: #f8fafc; border: 1px solid #cbd5e1;
                color: #334155; border-radius: 12px; padding: 12px 20px; font-size: 13px; font-weight: 700; min-width: 140px;
            }
            QPushButton#RefreshButton:hover, QPushButton#AddAssetButton:hover { background-color: #e2e8f0; }
            QPushButton#ThemeToggleButton { background-color: #f8fafc; border: 1px solid #cbd5e1; border-radius: 12px; font-size: 16px; padding: 0px; }
            QPushButton#ThemeToggleButton:hover { background-color: #e2e8f0; }
            QPushButton#RowActionButton { background-color: transparent; border: none; color: #64748b; font-size: 16px; font-weight: 800; padding: 2px; }
            QPushButton#RowActionButton:hover { color: #2563eb; }
            
            QComboBox#CurrencyDropdown {
                font-family: 'Segoe UI', sans-serif; background-color: #f8fafc; 
                border: 1px solid #cbd5e1; color: #334155; border-radius: 12px; 
                padding: 10px 14px; font-size: 13px; font-weight: 700; min-width: 110px;
            }
            QComboBox#CurrencyDropdown::drop-down { width: 28px; subcontrol-origin: padding; subcontrol-position: top right; border-left: 1px solid #cbd5e1; background: transparent; }
            QComboBox#CurrencyDropdown::down-arrow { image: none; width: 10px; height: 10px; border: none; }
            QComboBox#CurrencyDropdown QAbstractItemView, QComboBox#DialogDropdown QAbstractItemView { 
                font-family: 'Segoe UI', sans-serif; font-size: 13px; font-weight: 700;
                background-color: #ffffff; border: none; border-radius: 8px; color: #0f172a; outline: none; margin: 0; padding: 4px 0; max-height: 220px;
            }
            QListView#CurrencyDropdownPopup { background: transparent; border: none; }
            QComboBox#CurrencyDropdown QAbstractItemView::item:selected { background-color: #e2e8f0; color: #0f172a; }

            QPushButton#WindowControlButton, QPushButton#CloseButton { background-color: transparent; border: none; color: #64748b; font-size: 14px; }
            #LeftPanel, #RightPanel { background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 16px; }
            #TopHeader { background-color: #f1f5f9; border: 1px solid #e2e8f0; border-radius: 14px; }
            #MarketTitle { color: #0f172a; font-size: 18px; font-weight: 700; margin-bottom: 14px; }
            QChartView#AllocationChart { background-color: #f8fafc; border: 1px solid #cbd5e1; border-radius: 14px; }
            
            QTableWidget { background-color: #ffffff; alternate-background-color: #f1f5f9; border: 1px solid #e2e8f0; border-radius: 10px; color: #334155; gridline-color: transparent; }
            QTableWidget::item { padding: 10px; color: #334155; }
            QHeaderView::section { background-color: #e2e8f0 !important; color: #0f172a !important; border: none; border-bottom: 2px solid #2563eb; padding: 8px; font-size: 13px; font-weight: 700; }
            """
        else:
            return """
            #MainWindow { background-color: #0f0f12; }
            #CentralWidget { background-color: #121217; border: 1px solid rgba(255, 255, 255, 0.15); border-radius: 12px; }
            QLabel { color: #f8fafc; font-family: 'Segoe UI', sans-serif; }
            #HeaderTitle { font-size: 24px; font-weight: 700; color: #ffffff; }
            #ChartTitle { font-size: 16px; font-weight: 700; color: #ffffff; margin-top: 10px; margin-bottom: 4px; }
            #TotalValue { font-size: 48px; font-weight: 800; color: #00ff8c; margin-top: 8px; }
            #LastUpdate { font-size: 13px; color: #cbd5e1; margin-top: 6px; }
            
            QPushButton#RefreshButton, QPushButton#AddAssetButton {
                background-color: rgba(255, 255, 255, 0.08); border: 1px solid rgba(255, 255, 255, 0.12);
                color: #f8fafc; border-radius: 12px; padding: 12px 20px; font-size: 13px; font-weight: 700; min-width: 140px;
            }
            QPushButton#RefreshButton:hover, QPushButton#AddAssetButton:hover { background-color: rgba(255, 255, 255, 0.12); }
            QPushButton#ThemeToggleButton { background-color: rgba(255, 255, 255, 0.08); border: 1px solid rgba(255, 255, 255, 0.12); border-radius: 12px; font-size: 16px; padding: 0px; }
            QPushButton#ThemeToggleButton:hover { background-color: rgba(255, 255, 255, 0.12); }
            QPushButton#RowActionButton { background-color: transparent; border: none; color: #a0a0a5; font-size: 16px; font-weight: 800; padding: 2px; }
            QPushButton#RowActionButton:hover { color: #00ff8c; }
            
            QComboBox#CurrencyDropdown {
                font-family: 'Segoe UI', sans-serif; background-color: rgba(255, 255, 255, 0.08); 
                border: 1px solid rgba(255, 255, 255, 0.12); color: #f8fafc; border-radius: 12px; padding: 10px 14px; font-size: 13px; font-weight: 700; min-width: 110px;
            }
            QComboBox#CurrencyDropdown::drop-down { width: 28px; subcontrol-origin: padding; subcontrol-position: top right; border-left: 1px solid rgba(255, 255, 255, 0.12); background: transparent; }
            QComboBox#CurrencyDropdown::down-arrow { image: none; width: 10px; height: 10px; border: none; }
            QComboBox#CurrencyDropdown QAbstractItemView, QComboBox#DialogDropdown QAbstractItemView { 
                font-family: 'Segoe UI', sans-serif; font-size: 13px; font-weight: 700;
                background-color: #1a1a22; border: none; border-radius: 8px; color: #f8fafc; outline: none; margin: 0; padding: 4px 0; max-height: 220px;
            }
            QListView#CurrencyDropdownPopup { background: transparent; border: none; }
            QComboBox#CurrencyDropdown QAbstractItemView::item:selected { background-color: #2d2d38; color: #00ff8c; }

            QPushButton#WindowControlButton, QPushButton#CloseButton { background-color: transparent; border: none; color: #a0a0a5; font-size: 14px; }
            #LeftPanel, #RightPanel { background-color: #1a1a22; border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 16px; }
            #TopHeader { background-color: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 14px; }
            #MarketTitle { color: #ffffff; font-size: 18px; font-weight: 700; margin-bottom: 14px; }
            QChartView#AllocationChart { background-color: #1a1a22; border: 1px solid rgba(255, 255, 255, 0.12); border-radius: 14px; }
            
            QTableWidget { background-color: #22222b; alternate-background-color: #1e1e26; border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 10px; color: #e2e8f0; gridline-color: transparent; }
            QTableWidget::item { padding: 10px; color: #f1f5f9; }
            QHeaderView::section { background-color: #2d2d38 !important; color: #ffffff !important; border: none; border-bottom: 2px solid #00ff8c; padding: 8px; font-size: 13px; font-weight: 700; }
            """

    def _on_currency_changed(self, text: str):
        if "EUR" in text:
            self.current_currency_symbol = "€"
            self.active_currency_key = "EUR"
        elif "GBP" in text:
            self.current_currency_symbol = "£"
            self.active_currency_key = "GBP"
        else:
            self.current_currency_symbol = "$"
            self.active_currency_key = "USD"
            
        if self.portfolio_reference:
            self.setPortfolio(self.portfolio_reference)
        if self.active_chart_ticker:
            self.update_historical_trend_chart(self.active_chart_ticker, self.chart_cache.get(self.active_chart_ticker, []))

    def setLastUpdateText(self, text: str):
        self.last_update_label.setText(text)

    def handle_refresh_failure(self, error_message: str):
        current_text = self.last_update_label.text()
        if " | " in current_text:
            current_text = current_text.split(" | ")[0]
        self.last_update_label.setText(f"{current_text} | ⚠️ {error_message}")

    def setPortfolio(self, portfolio: Portfolio):
        self.portfolio_reference = portfolio
        rate = self.currency_rates[self.active_currency_key]
        
        converted_total = portfolio.total_value * rate
        self.total_value_label.setText(f"{self.current_currency_symbol}{converted_total:,.2f}")
        
        timestamp = QDateTime.currentDateTime().toString("MMM d, yyyy hh:mm:ss ap")
        if "Last update:" not in self.last_update_label.text() or "refreshing" in self.last_update_label.text():
            self.last_update_label.setText(f"Last update: {timestamp}")

        self.asset_table.setUpdatesEnabled(False)
        self.asset_table.setRowCount(len(portfolio.assets))
        
        for row, asset in enumerate(portfolio.assets):
            ticker = asset.ticker.strip().upper()
            
            # Resolve premium display name mapping safely
            resolved_name = asset.name or self.asset_name_map.get(ticker, ticker.capitalize())
            amount_text = f"{asset.amount:,.4f}" if isinstance(asset.amount, float) else str(asset.amount)
            
            raw_price = getattr(asset, 'price', None)
            raw_total = getattr(asset, 'total_value', None)
            
            price_text = f"{self.current_currency_symbol}{(raw_price * rate):,.2f}" if raw_price is not None else "--"
            total_text = f"{self.current_currency_symbol}{(raw_total * rate):,.2f}" if raw_total is not None else "--"

            # 1. FIXED: SIDE-BY-SIDE LAYOUT
            container = QWidget()
            cell_layout = QHBoxLayout(container)
            cell_layout.setContentsMargins(12, 0, 12, 0)
            cell_layout.setSpacing(8)
            cell_layout.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            
            name_label = QLabel(resolved_name)
            ticker_label = QLabel(f"({ticker})")
            
            if self.is_light_theme:
                name_label.setStyleSheet("font-weight: 700; font-size: 13px; color: #0f172a; background: transparent;")
                ticker_label.setStyleSheet("font-size: 12px; color: #64748b; font-weight: 600; background: transparent;")
            else:
                name_label.setStyleSheet("font-weight: 700; font-size: 13px; color: #ffffff; background: transparent;")
                ticker_label.setStyleSheet("font-size: 12px; color: #a0a0a5; font-weight: 600; background: transparent;")
                
            cell_layout.addWidget(name_label)
            cell_layout.addWidget(ticker_label)
            
            # Bind tracking ticker data dynamically to the container to bypass background painter bugs
            container.ticker_id = ticker
            self.asset_table.setCellWidget(row, 0, container)

            # CRITICAL: Keep underlying row item completely blank to avoid double text overlay leaks!
            blank_item = QTableWidgetItem()
            blank_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.asset_table.setItem(row, 0, blank_item)

            # 2. POPULATE CONVERTED DATA COLUMNS
            cells = [amount_text, price_text, total_text]
            for col_idx, value in enumerate(cells, start=1):
                item = QTableWidgetItem(value)
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
                item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                self.asset_table.setItem(row, col_idx, item)

            action_btn = QPushButton("•••")
            action_btn.setObjectName("RowActionButton")
            action_btn.setCursor(Qt.PointingHandCursor)
            action_btn.setFixedSize(40, 28)
            
            action_btn.clicked.connect(lambda checked=False, t=ticker, a=asset.amount: self._show_row_context_menu(t, a))
            self.asset_table.setCellWidget(row, 4, action_btn)

        self.asset_table.setUpdatesEnabled(True)
        self.update_allocation_chart(portfolio)

    def _show_row_context_menu(self, ticker: str, current_amount: float):
        menu = QMenu(self)
        if self.is_light_theme:
            menu.setStyleSheet("""
                QMenu { background-color: #ffffff; border: 1px solid #cbd5e1; color: #334155; padding: 4px; }
                QMenu::item { padding: 6px 20px; font-size: 13px; font-weight: 600; }
                QMenu::item:selected { background-color: #e2e8f0; color: #2563eb; }
            """)
        else:
            menu.setStyleSheet("""
                QMenu { background-color: #1a1a22; border: 1px solid rgba(255, 255, 255, 0.12); color: #f8fafc; padding: 4px; }
                QMenu::item { padding: 6px 20px; font-size: 13px; font-weight: 600; }
                QMenu::item:selected { background-color: #2d2d38; color: #00ff8c; }
            """)

        edit_action = QAction("✏️ Edit Holding Amount", self)
        delete_action = QAction("❌ Remove Asset Completely", self)
        
        menu.addAction(edit_action)
        menu.addSeparator()
        menu.addAction(delete_action)

        selected_action = menu.exec(QPoint(self.cursor().pos()))
        
        if selected_action == edit_action:
            from src.ui.components.edit_asset_dialog import EditAssetDialog
            dialog = EditAssetDialog(self, ticker=ticker, current_amount=current_amount)
            if dialog.exec() == QDialog.Accepted:
                new_val = dialog.get_amount()
                if self.asset_edited_callback:
                    self.asset_edited_callback(ticker, new_val)
                
        elif selected_action == delete_action:
            if self.asset_deleted_callback:
                self.asset_deleted_callback(ticker)

    def _handle_watchdog_timeout(self):
        self.watchdog_timer.stop()
        self.setLastUpdateText("Sync Issue: Network request timed out")
        self.is_refreshing = False
        self._check_and_enable_ui()

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

    def start_direct_refresh_pipeline(self):
        if self.manual_refresh_callback:
            self.is_refreshing = True
            self.setRefreshEnabled(False)
            self.refresh_button.setText("Refreshing...")
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
        
        palette = ["#3b82f6", "#10b981", "#f59e0b", "#8b5cf6", "#ec4899"] if self.is_light_theme else ["#00e676", "#3b82f6", "#f97316", "#8b5cf6", "#14b8a6"]
        rate = self.currency_rates[self.active_currency_key]

        aggregated_totals = {}
        for asset in portfolio.assets:
            val = getattr(asset, 'total_value', None)
            if val is not None and isinstance(val, (int, float)) and val > 0.0:
                ticker = asset.ticker.upper()
                aggregated_totals[ticker] = aggregated_totals.get(ticker, 0.0) + val

        for idx, (ticker, total_val) in enumerate(aggregated_totals.items()):
            converted_val = total_val * rate
            slice = series.append(ticker, converted_val)
            slice.setLabel(f"{ticker} {self.current_currency_symbol}{converted_val:,.2f}")
            slice.setLabelVisible(True)
            slice.setLabelColor(QColor("#334155") if self.is_light_theme else QColor("#ffffff"))
            slice.setBrush(QColor(palette[idx % len(palette)]))

        if series.count() == 0:
            series.append("No Data", 1.0).setBrush(QColor("#e2e8f0") if self.is_light_theme else QColor("#2a2a35"))

        self.allocation_chart.addSeries(series)
        self.allocation_chart.createDefaultAxes()
        self.allocation_chart.legend().setVisible(True)
        self.allocation_chart.legend().setLabelColor(QColor("#334155") if self.is_light_theme else QColor("#ffffff"))

    # ==========================================
    # GRAPH CONTROLLER & FIXED HIT PIPELINE
    # ==========================================
    def _on_asset_row_clicked(self, row, col):
        if col == 4:  
            return
        
        # FIXED: Pull metadata binding from column widget container safely
        cell_widget = self.asset_table.cellWidget(row, 0)
        if cell_widget and hasattr(cell_widget, 'ticker_id'):
            self.dispatch_historical_trend_request(cell_widget.ticker_id)

    def _on_market_row_clicked(self, row, col):
        ticker_item = self.market_table.item(row, 1)
        if ticker_item:
            self.dispatch_historical_trend_request(ticker_item.text())

    def dispatch_historical_trend_request(self, ticker: str):
        ticker = ticker.strip().upper()
        self.active_chart_ticker = ticker
        
        self.trend_title.setText(f"Market Analytics ({ticker} 7-Day History) — in {self.active_currency_key}")

        if ticker in self.chart_cache:
            self.update_historical_trend_chart(ticker, self.chart_cache[ticker])
            return

        self._set_historical_chart_message(f"Fetching historical metrics for {ticker}...")
        
        coin_id_map = {"BTC": "bitcoin", "ETH": "ethereum", "SOL": "solana", "ADA": "cardano", "DOT": "polkadot", "XRP": "ripple", "LINK": "chainlink"}
        coin_id = coin_id_map.get(ticker, ticker.lower())

        asyncio.create_task(self._async_fetch_historical_data(ticker, coin_id))

    async def _async_fetch_historical_data(self, ticker: str, coin_id: str):
        try:
            from src.infrastructure.api_client import APIClient
            client = APIClient()
            url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days=7"
            
            payload = await client.fetch_data(url)
            if payload and "prices" in payload:
                raw_prices = payload["prices"]
                self.chart_cache[ticker] = raw_prices
                
                if self.active_chart_ticker == ticker:
                    self.update_historical_trend_chart(ticker, raw_prices)
            else:
                self._set_historical_chart_message("Error: Received invalid data matrix structural formats")
        except Exception as e:
            if "429" in str(e):
                self._set_historical_chart_message("Rate Limit Reached. Please select again in a minute.")
            else:
                self._set_historical_chart_message("Historical trendline metrics currently unavailable")

    def update_historical_trend_chart(self, ticker: str, raw_api_prices: list):
        self.historical_chart.removeAllSeries()
        
        if not raw_api_prices or len(raw_api_prices) < 2:
            self._set_historical_chart_message("Insufficient historical records found.")
            return

        self.trend_title.setText(f"Market Analytics ({ticker} 7-Day History) — in {self.active_currency_key}")

        series = QLineSeries()
        rate = self.currency_rates[self.active_currency_key]
        
        min_time = float('inf')
        max_time = float('-inf')
        min_price = float('inf')
        max_price = float('-inf')
        
        for item in raw_api_prices:
            timestamp = item[0] 
            converted_price = item[1] * rate
            
            series.append(timestamp, converted_price)
            
            if timestamp < min_time: min_time = timestamp
            if timestamp > max_time: max_time = timestamp
            if converted_price < min_price: min_price = converted_price
            if converted_price > max_price: max_price = converted_price

        start_p = raw_api_prices[0][1]
        end_p = raw_api_prices[-1][1]
        
        if end_p >= start_p:
            line_color = QColor("#00c853") if self.is_light_theme else QColor("#00ff8c")
        else:
            line_color = QColor("#ea580c") if self.is_light_theme else QColor("#ef4444")

        pen = QPen(line_color, 3, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        series.setPen(pen)
        self.historical_chart.addSeries(series)

        for axis in self.historical_chart.axes():
            self.historical_chart.removeAxis(axis)

        axis_x = QDateTimeAxis()
        axis_x.setFormat("MM/dd")
        axis_x.setLabelsColor(QColor("#334155") if self.is_light_theme else QColor("#cbd5e1"))
        axis_x.setRange(QDateTime.fromMSecsSinceEpoch(int(min_time)), QDateTime.fromMSecsSinceEpoch(int(max_time)))
        axis_x.setTickCount(4)
        axis_x.setGridLineVisible(False)
        self.historical_chart.addAxis(axis_x, Qt.AlignBottom)
        series.attachAxis(axis_x)

        axis_y = QValueAxis()
        padding = (max_price - min_price) * 0.15 if max_price != min_price else 1.0
        axis_y.setRange(min_price - padding, max_price + padding)
        axis_y.setLabelsColor(QColor("#334155") if self.is_light_theme else QColor("#cbd5e1"))
        axis_y.setLabelFormat("%.2f")
        axis_y.setTickCount(5)
        axis_y.setGridLineColor(QColor("rgba(0,0,0,0.05)") if self.is_light_theme else QColor("rgba(255,255,255,0.05)"))
        
        font = axis_y.labelsFont()
        font.setFamily("Segoe UI")
        axis_y.setLabelsFont(font)
        
        self.historical_chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_y)

    def _set_historical_chart_message(self, message: str):
        self.historical_chart.removeAllSeries()
        for axis in self.historical_chart.axes():
            self.historical_chart.removeAxis(axis)
        
        axis_x = QValueAxis()
        axis_x.setRange(0, 10)
        axis_x.setVisible(False)
        axis_y = QValueAxis()
        axis_y.setRange(0, 10)
        axis_y.setVisible(False)
        
        self.historical_chart.addAxis(axis_x, Qt.AlignBottom)
        self.historical_chart.addAxis(axis_y, Qt.AlignLeft)
        
        self.historical_chart.setTitle(message)
        self.historical_chart.setTitleBrush(QColor("#64748b") if self.is_light_theme else QColor("#a0a0a5"))
    # ==========================================

    def setMarketData(self, market_assets):
        self.market_table.setUpdatesEnabled(False)
        self.market_table.setRowCount(len(market_assets))
        rate = self.currency_rates[self.active_currency_key]

        for row, asset in enumerate(market_assets):
            name_item = QTableWidgetItem(str(asset.name))
            ticker_item = QTableWidgetItem(str(asset.ticker))
            
            converted_price = asset.price * rate
            price_item = QTableWidgetItem(f"{self.current_currency_symbol}{converted_price:,.2f}")
            change_item = QTableWidgetItem(f"{asset.change_24h:+.2f}%")

            trend_item = QTableWidgetItem()
            
            prices_array = getattr(asset, 'sparkline_prices', [])
            converted_prices_array = [p * rate for p in prices_array]
            
            trend_item.setData(Qt.UserRole, converted_prices_array)
            trend_item.setData(Qt.UserRole + 1, asset.change_24h)

            for item in [name_item, ticker_item, price_item, change_item, trend_item]:
                item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                if item != trend_item:
                    item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)

            if asset.change_24h >= 0:
                change_item.setForeground(QColor("#00c853") if self.is_light_theme else QColor("#00ff8c"))
            else:
                change_item.setForeground(QColor("#ea580c") if self.is_light_theme else QColor("#ef4444"))

            self.market_table.setItem(row, 0, name_item)
            self.market_table.setItem(row, 1, ticker_item)
            self.market_table.setItem(row, 2, price_item)
            self.market_table.setItem(row, 3, change_item)
            self.market_table.setItem(row, 4, trend_item)

        self.market_table.setUpdatesEnabled(True)

    def setAssetAddedCallback(self, callback):
        self.asset_added_callback = callback

    def setAssetEditedCallback(self, callback):
        self.asset_edited_callback = callback

    def setAssetDeletedCallback(self, callback):
        self.asset_deleted_callback = callback

    def setManualRefreshCallback(self, callback):
        self.manual_refresh_callback = callback

    def open_add_asset_dialog(self):
        dialog = AddAssetDialog(self, is_light_theme=self.is_light_theme)
        if dialog.exec() == QDialog.Accepted:
            ticker, amount = dialog.get_data()
            print(f"[DEBUG] Dialog accepted. Ticker: '{ticker}', Amount: {amount}")
            print(f"[DEBUG] Has callback? {self.asset_added_callback is not None}")

            if ticker and amount > 0.0:
                if self.asset_added_callback:
                    self.asset_added_callback(ticker, amount)
                    print(f"[DEBUG] Callback fired successfully for {ticker}")
                    self.setPortfolio(self.portfolio_reference)
                else:
                    print("[WARNING] Asset data was valid, but self.asset_added_callback is None!")
            else:
                print(f"[WARNING] Insertion rejected because ticker was empty or amount ({amount}) <= 0.0")

    def setRefreshEnabled(self, enabled: bool):
        self.refresh_button.setEnabled(enabled)
        self.add_asset_button.setEnabled(enabled)