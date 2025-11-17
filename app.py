from flask import Flask, render_template, request, send_file
from pypdf import PdfWriter, PdfReader
from pdf2image import convert_from_path
import os
import zipfile
import uuid
import fitz  # PyMuPDF
import time
import shutil

def cleanup_uploads(max_age_minutes=30):
    now = time.time()
    max_age_seconds = max_age_minutes * 60

    for folder in os.listdir(UPLOAD_FOLDER):
        folder_path = os.path.join(UPLOAD_FOLDER, folder)

        if os.path.isdir(folder_path):
            folder_age = now - os.path.getmtime(folder_path)

            # Delete if older than max age
            if folder_age > max_age_seconds:
                shutil.rmtree(folder_path, ignore_errors=True)
                print(f"Deleted old folder: {folder_path}")

app = Flask(__name__)  # <-- IMPORTANT: define BEFORE routes

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

POPPLER_PATH = r"C:\poppler\poppler-25.11.0\Library\bin"   # your poppler path
#ads route
@app.route('/ads.txt')
def ads():
    return send_file("static/ads.txt")

#sitemap route
@app.route('/sitemap.xml')
def sitemap():
    return send_file("static/sitemap.xml")


# ---------------- HOME ----------------
@app.route("/")
def home():
    return render_template("home.html")


# --------------------- PDF MERGER ---------------------
@app.route("/pdf-merger", methods=["GET", "POST"])
def pdf_merger():
    cleanup_uploads()
    if request.method == "POST":
        files = request.files.getlist("pdfs")

        writer = PdfWriter()

        for f in files:
            save_path = os.path.join(UPLOAD_FOLDER, f.filename)
            f.save(save_path)

            reader = PdfReader(save_path)
            for page in reader.pages:
                writer.add_page(page)

        output_path = os.path.join(UPLOAD_FOLDER, "merged.pdf")
        with open(output_path, "wb") as output_file:
            writer.write(output_file)

        return send_file(output_path, as_attachment=True)

    return render_template("pdf_merger.html")


# --------------------- PDF COMPRESSOR ---------------------
@app.route("/pdf-compress", methods=["GET", "POST"])
def pdf_compress():
    cleanup_uploads()
    if request.method == "POST":
        compression_level = int(request.form["quality"])
        file = request.files["pdf"]

        input_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(input_path)

        output_path = os.path.join(UPLOAD_FOLDER, "compressed.pdf")

        doc = fitz.open(input_path)
        new_pdf = fitz.open()

        for page in doc:
            pix = page.get_pixmap(dpi=compression_level)
            img = new_pdf.new_page(width=pix.width, height=pix.height)
            img.insert_image(img.rect, pixmap=pix)

        new_pdf.save(output_path)
        new_pdf.close()
        doc.close()

        return send_file(output_path, as_attachment=True)

    return render_template("pdf_compress.html")


# --------------------- PDF SPLIT ---------------------
@app.route("/pdf-split", methods=["GET", "POST"])
def pdf_split():
    cleanup_uploads()
    if request.method == "POST":
        file = request.files["pdf"]
        start_page = int(request.form["start"]) - 1
        end_page = int(request.form["end"])

        input_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(input_path)

        output_path = os.path.join(UPLOAD_FOLDER, "splitted.pdf")

        reader = PdfReader(input_path)
        writer = PdfWriter()

        for i in range(start_page, end_page):
            writer.add_page(reader.pages[i])

        with open(output_path, "wb") as out:
            writer.write(out)

        return send_file(output_path, as_attachment=True)

    return render_template("pdf_split.html")


# --------------------- PDF → JPG ---------------------
@app.route("/pdf-to-jpg", methods=["GET", "POST"])
def pdf_to_jpg():
    cleanup_uploads()
    if request.method == "POST":
        file = request.files["pdf"]

        # Create a unique temp folder
        folder_id = str(uuid.uuid4())
        folder_path = os.path.join(UPLOAD_FOLDER, folder_id)
        os.makedirs(folder_path, exist_ok=True)

        pdf_path = os.path.join(folder_path, file.filename)
        file.save(pdf_path)

        # Convert the PDF into images
        images = convert_from_path(pdf_path, poppler_path=POPPLER_PATH, dpi=150)

        jpg_files = []

        for i, img in enumerate(images):
            img_name = f"page_{i+1}.jpg"
            img_path = os.path.join(folder_path, img_name)
            img.save(img_path, "JPEG")
            jpg_files.append(img_path)

        # Create a ZIP file of all JPGs
        zip_path = os.path.join(folder_path, "converted_images.zip")
        with zipfile.ZipFile(zip_path, "w") as zipf:
            for img_file in jpg_files:
                zipf.write(img_file, os.path.basename(img_file))

        return send_file(zip_path, as_attachment=True)

    return render_template("pdf_to_jpg.html")


# --------------------- JPG → PDF ---------------------
@app.route("/jpg-to-pdf", methods=["GET", "POST"])
def jpg_to_pdf():
    cleanup_uploads()
    if request.method == "POST":
        files = request.files.getlist("images")
        order = request.form["order"]

        # Convert "2,0,1" → [2, 0, 1]
        order_list = list(map(int, order.split(",")))
        ordered_files = [files[i] for i in order_list]

        output_path = os.path.join(UPLOAD_FOLDER, "converted.pdf")
        pdf = fitz.open()

        for f in ordered_files:
            img_path = os.path.join(UPLOAD_FOLDER, f.filename)
            f.save(img_path)

            img = fitz.open(img_path)
            rect = img[0].rect
            pdf_page = pdf.new_page(width=rect.width, height=rect.height)
            pdf_page.insert_image(rect, filename=img_path)
            img.close()

        pdf.save(output_path)
        pdf.close()

        return send_file(output_path, as_attachment=True)

    return render_template("jpg_to_pdf.html")


# --------------------- RUN ---------------------
if __name__ == "__main__":
    app.run()
