// Tabs
function showTab(id) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    document.getElementById(id).classList.add('active');

    // Αν το event προκλήθηκε από click (για browser συμβατότητα)
    if (event && event.target) {
        event.target.classList.add('active');
    }
}

// Modal Edit
function openEditModal() {
    document.getElementById("editModal").style.display = "flex";
}

function closeEditModal() {
    document.getElementById("editModal").style.display = "none";
}

// Avatar upload preview
function previewImage(event) {
    const photoProfile = document.getElementById("photo-profile");
    const file = event.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function (e) {
            photoProfile.src = e.target.result;
        };
        reader.readAsDataURL(file);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    // Trigger hidden file input when button clicked
    const uploadBtn = document.querySelector('.upload-photo-btn');
    const uploadInput = document.getElementById('upload');
    if (uploadBtn && uploadInput) {
        uploadBtn.addEventListener('click', () => {
            uploadInput.click();
        });
    }

    // Optional: close modal on ESC
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') closeEditModal();
    });

    // Optional: close modal if clicking outside content
    const modal = document.getElementById("editModal");
    if (modal) {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) closeEditModal();
        });
    }
});
