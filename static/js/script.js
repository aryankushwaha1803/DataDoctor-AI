
document.addEventListener("DOMContentLoaded", function () {
    const uploadInput = document.querySelector('input[type="file"]');

    if (uploadInput) {
        uploadInput.addEventListener("change", function () {
            if (this.files.length > 0) {
                console.log("Selected file:", this.files[0].name);
            }
        });
    }
});
