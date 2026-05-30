# src/ui/main_window.py

from PySide6.QtCore import Qt, QDateTime, QTimer, QPoint, QEvent
from PySide6.QtGui import QColor, QPainter, QPen, QPainterPath, QAction
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
    QStyledItemDelegate,
    QStyle,
    QComboBox,
    QMenu,
    QListView,
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
        
        self.current_currency_symbol = "$"
        self.currency_rates = {"USD": 1.0, "EUR": 0.92, "GBP": 0.79}
        self.active_currency_key = "USD"

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
        self.currency_dropdown.setMaxVisibleItems(5)
        
        # Hard platform overrides to prevent native frame leaks
        currency_view = QListView()
        currency_view.is_light_theme = self.is_light_theme
        currency_view.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        currency_view.setAttribute(Qt.WA_TranslucentBackground)
        currency_view.setFrameShape(QFrame.NoFrame)
        currency_view.setItemDelegate(DropdownItemDelegate(currency_view))
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

        self.asset_table = QTableWidget(0, 6)
        self.asset_table.setObjectName("AssetTable")
        self.asset_table.setHorizontalHeaderLabels(
            ["Asset Name", "Ticker", "Amount Held", "Live Price", "Total Value", "Actions"]
        )
        self.asset_table.verticalHeader().setVisible(False)
        self.asset_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.asset_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.asset_table.setAlternatingRowColors(True)
        self.asset_table.setFocusPolicy(Qt.NoFocus)
        self.asset_table.setShowGrid(False)
        
        self.asset_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.asset_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)

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
            
            QPushButton#ThemeToggleButton {
                background-color: #f8fafc; border: 1px solid #cbd5e1; border-radius: 12px; font-size: 16px; padding: 0px;
            }
            QPushButton#ThemeToggleButton:hover { background-color: #e2e8f0; }
            
            QPushButton#RowActionButton {
                background-color: transparent; border: none; color: #64748b; font-size: 16px; font-weight: 800; padding: 2px;
            }
            QPushButton#RowActionButton:hover { color: #2563eb; }
            
            QComboBox#CurrencyDropdown {
                font-family: 'Segoe UI', sans-serif; background-color: #f8fafc; 
                border: 1px solid #cbd5e1; color: #334155; border-radius: 12px; 
                padding: 10px 14px; font-size: 13px; font-weight: 700; min-width: 110px;
            }
            QComboBox#CurrencyDropdown::drop-down { border: none; background: transparent; }
            
            QComboBox#CurrencyDropdown QAbstractItemView, QComboBox#DialogDropdown QAbstractItemView { 
                font-family: 'Segoe UI', sans-serif; font-size: 13px; font-weight: 700;
                background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 8px;
                color: #0f172a; outline: none;
            }

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
            
            QPushButton#ThemeToggleButton {
                background-color: rgba(255, 255, 255, 0.08); border: 1px solid rgba(255, 255, 255, 0.12); border-radius: 12px; font-size: 16px; padding: 0px;
            }
            QPushButton#ThemeToggleButton:hover { background-color: rgba(255, 255, 255, 0.12); }
            
            QPushButton#RowActionButton {
                background-color: transparent; border: none; color: #a0a0a5; font-size: 16px; font-weight: 800; padding: 2px;
            }
            QPushButton#RowActionButton:hover { color: #00ff8c; }
            
            QComboBox#CurrencyDropdown {
                font-family: 'Segoe UI', sans-serif; background-color: rgba(255, 255, 255, 0.08); 
                border: 1px solid rgba(255, 255, 255, 0.12); color: #f8fafc; border-radius: 12px; 
                padding: 10px 14px; font-size: 13px; font-weight: 700; min-width: 110px;
            }
            QComboBox#CurrencyDropdown::drop-down { border: none; background: transparent; }
            
            QComboBox#CurrencyDropdown QAbstractItemView, QComboBox#DialogDropdown QAbstractItemView { 
                font-family: 'Segoe UI', sans-serif; font-size: 13px; font-weight: 700;
                background-color: #1a1a22; border: 1px solid rgba(255, 255, 255, 0.15); border-radius: 8px;
                color: #f8fafc; outline: none;
            }

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
            name = asset.name or asset.ticker
            ticker = asset.ticker
            amount_text = f"{asset.amount:,.4f}" if isinstance(asset.amount, float) else str(asset.amount)
            
            raw_price = getattr(asset, 'price', None)
            raw_total = getattr(asset, 'total_value', None)
            
            price_text = f"{self.current_currency_symbol}{(raw_price * rate):,.2f}" if raw_price is not None else "--"
            total_text = f"{self.current_currency_symbol}{(raw_total * rate):,.2f}" if raw_total is not None else "--"

            cells = [name, ticker, amount_text, price_text, total_text]
            for col, value in enumerate(cells):
                item = QTableWidgetItem(value)
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
                item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                self.asset_table.setItem(row, col, item)

            action_btn = QPushButton("•••")
            action_btn.setObjectName("RowActionButton")
            action_btn.setCursor(Qt.PointingHandCursor)
            action_btn.setFixedSize(40, 28)
            
            action_btn.clicked.connect(lambda checked=False, t=ticker, a=asset.amount: self._show_row_context_menu(t, a))
            self.asset_table.setCellWidget(row, 5, action_btn)

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
            if ticker and amount > 0.0 and self.asset_added_callback:
                self.asset_added_callback(ticker, amount)

    def setRefreshEnabled(self, enabled: bool):
        self.refresh_button.setEnabled(enabled)
        self.add_asset_button.setEnabled(enabled)