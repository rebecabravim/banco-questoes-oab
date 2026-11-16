import argparse
from pathlib import Path
import fitz  # PyMuPDF


def extract_pdf_text(pdf_path: Path) -> str:
    text_pages = []

    with fitz.open(pdf_path) as pdf:
        page_number = 3
        page = pdf[page_number - 1]

        text = page.get_text("text")

        if text.strip():
            text_pages.append(f"\n\n===== Página {page_number} =====\n\n")
            text_pages.append(text)

    return "".join(text_pages)


def save_text(text: str, pdf_path: Path) -> Path:
    output_dir = Path("provas-extraidas")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / f"{pdf_path.stem}_pyMuPDF_2.txt"
    output_file.write_text(text, encoding="utf-8")

    return output_file


def main():
    parser = argparse.ArgumentParser(
        description="Extrai somente a página 3 de um PDF da OAB."
    )

    parser.add_argument(
        "pdf_path",
        help="Caminho do arquivo PDF."
    )

    args = parser.parse_args()

    pdf_path = Path(args.pdf_path)

    if not pdf_path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {pdf_path}")

    if pdf_path.suffix.lower() != ".pdf":
        raise ValueError("O arquivo informado precisa ser um PDF.")

    extracted_text = extract_pdf_text(pdf_path)
    output_file = save_text(extracted_text, pdf_path)

    print("Texto extraído com sucesso.")
    print(f"Arquivo salvo em: {output_file}")


if __name__ == "__main__":
    main()