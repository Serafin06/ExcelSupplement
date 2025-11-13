from pathlib import Path

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QDateEdit, QTextEdit, QFileDialog,
    QGroupBox, QMessageBox
)
from PyQt6.QtCore import QDate, QThread, pyqtSignal

from ExcelSup.Facade import ExcelEnrichmentFacade
from config import getEngine


class ProcessingThread(QThread):
    """Worker thread do przetwarzania w tle"""
    finished = pyqtSignal(bool, str)

    def __init__(self, input_file, output_file, date_start, date_end):
        super().__init__()
        self.input_file = input_file
        self.output_file = output_file
        self.date_start = date_start
        self.date_end = date_end

    def run(self):
        try:
            engine = getEngine()
            facade = ExcelEnrichmentFacade(engine, self.date_start, self.date_end)
            facade.process_file(self.input_file, self.output_file)
            self.finished.emit(True, "Przetwarzanie zakończone pomyślnie!")
        except Exception as e:
            self.finished.emit(False, f"Błąd: {str(e)}")


class MainWindow(QMainWindow):
    """Główne okno aplikacji"""

    def __init__(self):
        super().__init__()
        self.input_file = ""
        self.output_file = ""
        self.processing_thread = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Excel Supplement - Uzupełnianie danych o materiałach")
        self.setGeometry(100, 100, 800, 700)

        # Centralny widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # === SEKCJA 1: Wymagania pliku Excel ===
        requirements_group = QGroupBox("📋 Wymagania pliku Excel")
        requirements_layout = QVBoxLayout()

        self.requirements_text = QTextEdit()
        self.requirements_text.setReadOnly(True)
        self.requirements_text.setMaximumHeight(150)
        requirements_text_content = """
Plik Excel musi zawierać:
- Kolumnę "Purchase item number" (C) - z numerami artykułów/indeksów
- Nagłówki kolumn muszą znajdować się w pierwszym wierszu (1)

Program automatycznie utworzy nowy plik Excel i doda kolumny z danymi materiałów:
  - SZEROKOSC_1, GRUBOSC_11, GRUBOSC_21, GRUBOSC_31, RECEPTURA_1, TECH (technologiczna ilość wytworzenia), JM2
  - Material_type_1/2/3 z procentowym składem i kontaktem z produktem
  - SALES_DATES - daty sprzedaży z zakresu lub informacja o wcześniejszej sprzedaży
        """
        self.requirements_text.setPlainText(requirements_text_content.strip())

        requirements_layout.addWidget(self.requirements_text)
        requirements_group.setLayout(requirements_layout)
        main_layout.addWidget(requirements_group)

        # === SEKCJA 2: Wybór plików ===
        files_group = QGroupBox("📁 Pliki")
        files_layout = QVBoxLayout()

        # Input file
        input_layout = QHBoxLayout()
        input_label = QLabel("Plik wejściowy:")
        input_label.setFixedWidth(120)
        self.input_file_edit = QLineEdit()
        self.input_file_edit.setReadOnly(True)
        self.input_file_edit.setPlaceholderText("Wybierz plik Excel do przetworzenia...")
        input_browse_btn = QPushButton("Przeglądaj...")
        input_browse_btn.clicked.connect(self.browse_input_file)

        input_layout.addWidget(input_label)
        input_layout.addWidget(self.input_file_edit)
        input_layout.addWidget(input_browse_btn)

        # Output file
        output_layout = QHBoxLayout()
        output_label = QLabel("Plik wyjściowy:")
        output_label.setFixedWidth(120)
        self.output_file_edit = QLineEdit()
        self.output_file_edit.setReadOnly(True)
        self.output_file_edit.setPlaceholderText("Wybierz gdzie zapisać wynik...")
        output_browse_btn = QPushButton("Przeglądaj...")
        output_browse_btn.clicked.connect(self.browse_output_file)

        output_layout.addWidget(output_label)
        output_layout.addWidget(self.output_file_edit)
        output_layout.addWidget(output_browse_btn)

        files_layout.addLayout(input_layout)
        files_layout.addLayout(output_layout)
        files_group.setLayout(files_layout)
        main_layout.addWidget(files_group)

        # === SEKCJA 3: Zakres dat ===
        dates_group = QGroupBox("📅 Zakres dat sprzedaży")
        dates_layout = QHBoxLayout()

        start_label = QLabel("Data początkowa:")
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(QDate(2024, 10, 1))  # Q4 2024
        self.start_date_edit.setDisplayFormat("yyyy-MM-dd")

        end_label = QLabel("Data końcowa:")
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(QDate(2025, 9, 30))  # Q3 2025
        self.end_date_edit.setDisplayFormat("yyyy-MM-dd")


        dates_layout.addWidget(start_label)
        dates_layout.addWidget(self.start_date_edit)
        dates_layout.addWidget(end_label)
        dates_layout.addWidget(self.end_date_edit)
        dates_layout.addStretch()

        dates_group.setLayout(dates_layout)
        main_layout.addWidget(dates_group)

        # === SEKCJA 4: Przyciski akcji ===
        action_layout = QHBoxLayout()

        self.process_btn = QPushButton("▶️ Przetwórz plik")
        self.process_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.process_btn.clicked.connect(self.process_file)

        cancel_btn = QPushButton("❌ Zamknij")
        cancel_btn.clicked.connect(self.close)

        action_layout.addStretch()
        action_layout.addWidget(self.process_btn)
        action_layout.addWidget(cancel_btn)

        main_layout.addLayout(action_layout)

        # === SEKCJA 5: Status ===
        self.status_label = QLabel("Gotowy do pracy")
        self.status_label.setStyleSheet("padding: 10px; background-color: #e8f5e9; border-radius: 5px;")
        main_layout.addWidget(self.status_label)

        main_layout.addStretch()

    def browse_input_file(self):
        """Wybór pliku wejściowego"""
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Wybierz plik Excel",
            "",
            "Pliki Excel (*.xlsx *.xls)"
        )
        if file_name:
            self.input_file = file_name
            self.input_file_edit.setText(file_name)

            # Automatycznie zaproponuj nazwę wyjściową
            if not self.output_file:
                path = Path(file_name)
                suggested_output = str(path.parent / f"{path.stem}_enriched{path.suffix}")
                self.output_file = suggested_output
                self.output_file_edit.setText(suggested_output)

    def browse_output_file(self):
        """Wybór pliku wyjściowego"""
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Zapisz jako",
            self.output_file or "",
            "Pliki Excel (*.xlsx)"
        )
        if file_name:
            self.output_file = file_name
            self.output_file_edit.setText(file_name)

    def validate_inputs(self) -> bool:
        """Walidacja danych wejściowych"""
        if not self.input_file:
            QMessageBox.warning(self, "Brak pliku", "Wybierz plik wejściowy!")
            return False

        if not self.output_file:
            QMessageBox.warning(self, "Brak pliku", "Wybierz plik wyjściowy!")
            return False

        if not Path(self.input_file).exists():
            QMessageBox.warning(self, "Błąd", "Plik wejściowy nie istnieje!")
            return False

        return True

    def process_file(self):
        """Uruchom przetwarzanie pliku"""
        if not self.validate_inputs():
            return

        # Pobierz daty
        date_start = self.start_date_edit.date().toString("yyyy-MM-dd")
        date_end = self.end_date_edit.date().toString("yyyy-MM-dd")

        # Wyłącz przycisk
        self.process_btn.setEnabled(False)
        self.status_label.setText("⏳ Przetwarzanie w toku...")
        self.status_label.setStyleSheet("padding: 10px; background-color: #fff3cd; border-radius: 5px;")

        # Uruchom w osobnym wątku
        self.processing_thread = ProcessingThread(
            self.input_file,
            self.output_file,
            date_start,
            date_end
        )
        self.processing_thread.finished.connect(self.on_processing_finished)
        self.processing_thread.start()

    def on_processing_finished(self, success: bool, message: str):
        """Callback po zakończeniu przetwarzania"""
        self.process_btn.setEnabled(True)

        if success:
            self.status_label.setText(f"✅ {message}")
            self.status_label.setStyleSheet("padding: 10px; background-color: #d4edda; border-radius: 5px;")
            QMessageBox.information(self, "Sukces", f"{message}\n\nPlik zapisany: {self.output_file}")
        else:
            self.status_label.setText(f"❌ {message}")
            self.status_label.setStyleSheet("padding: 10px; background-color: #f8d7da; border-radius: 5px;")
            QMessageBox.critical(self, "Błąd", message)


