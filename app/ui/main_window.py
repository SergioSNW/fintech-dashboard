import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
from app.ui.styles import load_dark_mode_stylesheet

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Fintech Dashboard")
        self.setGeometry(100, 100, 800, 600)

        layout = QVBoxLayout()
        self.label = QLabel("Fetching data...", self)
        layout.addWidget(self.label)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.load_data()

    def load_data(self):
        from app.backend.tasks import fetch_data
        loop = asyncio.get_event_loop()
        data = loop.run_until_complete(fetch_data())
        if data:
            self.label.setText(f"Data: {data}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    dark_mode_stylesheet = load_dark_mode_stylesheet()
    app.setStyleSheet(dark_mode_stylesheet)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())