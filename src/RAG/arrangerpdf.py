from PyPDF2 import PdfReader, PdfWriter

input_pdf_path = r"code\RAG\tcps2-2022-fr.pdf"
output_pdf_path = r"code\RAG\tcps2-2022-fr-pageutile.pdf"
pages_to_remove = [0,1,2,3,4,5,6,7, 8] # Removes the 3rd and 6th pages (indices 2 and 5)

reader = PdfReader(input_pdf_path)
writer = PdfWriter()

for i in range(len(reader.pages)):
    if i not in pages_to_remove:
        writer.add_page(reader.pages[i])

with open(output_pdf_path, "wb") as output_pdf_file:
    writer.write(output_pdf_file)

print(f"Pages with indices {pages_to_remove} removed from {input_pdf_path} and saved to {output_pdf_path}")