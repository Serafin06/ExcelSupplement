from ExcelSup.Facade import ExcelEnrichmentFacade
from config import getEngine


def main():
    """Punkt wejścia aplikacji"""

    # Ścieżki do plików
    INPUT_FILE = "input.xlsx"
    OUTPUT_FILE = "output_enriched.xlsx"

    # Uruchom proces
    engine = getEngine()
    facade = ExcelEnrichmentFacade(engine)
    facade.process_file(INPUT_FILE, OUTPUT_FILE)


if __name__ == "__main__":
    main()
