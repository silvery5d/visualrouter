import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QStatusBar
from src.graphics.canvas import VenueGraphicsScene, VenueGraphicsView


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VisualRouter - VR场馆路线规划")
        self.setMinimumSize(1200, 800)

        self.scene = VenueGraphicsScene()
        self.view = VenueGraphicsView(self.scene)
        self.setCentralWidget(self.view)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.view.mouse_moved.connect(self._update_mouse_pos)

    def _update_mouse_pos(self, x: float, y: float):
        self.status_bar.showMessage(f"X: {x:.2f}m  Y: {y:.2f}m")


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
