from weasyprint import HTML
import os


def convert_html_to_pdf(html_file, pdf_file):
    """
    Convert HTML file to PDF using WeasyPrint

    Args:
        html_file (str): Path to the HTML file
        pdf_file (str): Path where the PDF will be saved
    """
    # Get the absolute path of the HTML file
    base_dir = os.path.dirname(os.path.abspath(__file__))
    html_path = os.path.join(base_dir, html_file)
    pdf_path = os.path.join(base_dir, pdf_file)

    # Create PDF from HTML
    HTML(filename=html_path).write_pdf(pdf_path)

    print(f"PDF created successfully at {pdf_path}")


if __name__ == "__main__":
    # Convert the CV template to PDF
    convert_html_to_pdf("templates/cv.html", "cv.pdf")
