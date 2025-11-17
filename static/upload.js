function setupDragDrop(inputId, dropZoneId, previewId) {
    const fileInput = document.getElementById(inputId);
    const dropZone = document.getElementById(dropZoneId);
    const preview = document.getElementById(previewId);

    dropZone.addEventListener("click", () => fileInput.click());

    dropZone.addEventListener("dragover", (e) => {
        e.preventDefault();
        dropZone.classList.add("border-red-500");
    });

    dropZone.addEventListener("dragleave", () => {
        dropZone.classList.remove("border-red-500");
    });

    dropZone.addEventListener("drop", (e) => {
        e.preventDefault();
        dropZone.classList.remove("border-red-500");
        const files = e.dataTransfer.files;
        fileInput.files = files;
        preview.innerText = files.length > 1 ? `${files.length} files selected` : files[0].name;
    });

    fileInput.addEventListener("change", () => {
        preview.innerText = fileInput.files.length > 1
            ? `${fileInput.files.length} files selected`
            : fileInput.files[0].name;
    });
}
