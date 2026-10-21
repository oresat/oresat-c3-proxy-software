import sys
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QLabel,
    QPushButton,
)

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt6 Custom List Items Example")
        self.resize(400, 300)

        layout = QVBoxLayout(self)
        
        # Create the main list widget
        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)

        # Data representing each row and its unique identifier/action
        tasks = [
            ("Download Database", "db_download"),
            ("Clear Cache Files", "clear_cache"),
            ("Generate Report", "gen_report"),
        ]

        for text, action_id in tasks:
            # Create a container widget for the list item row
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(5, 2, 5, 2)

            # Label for the row
            label = QLabel(text)
            
            # Button with a unique action connected using a lambda closure
            button = QPushButton("Run")
            button.clicked.connect(lambda checked, aid=action_id, t=text: self.handle_action(aid, t))

            row_layout.addWidget(label)
            row_layout.addStretch()
            row_layout.addWidget(button)

            # Create a QListWidgetItem and assign the custom row widget
            list_item = QListWidgetItem(self.list_widget)
            list_item.setSizeHint(row_widget.sizeHint())
            self.list_widget.setItemWidget(list_item, row_widget)

    def handle_action(self, action_id, task_name):
        # Each button executes a distinct block of logic based on its action_id
        if action_id == "db_download":
            print(f"Executing protocol for: {task_name} (Downloading...)")
        elif action_id == "clear_cache":
            print(f"Executing protocol for: {task_name} (Purging...)")
        elif action_id == "gen_report":
            print(f"Executing protocol for: {task_name} (Compiling...)")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
