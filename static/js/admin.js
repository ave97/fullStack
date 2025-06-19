function openEditModal(id, username, email, role) {
    document.getElementById("edit-user-id").value = id;
    document.getElementById("edit-username").value = username;
    document.getElementById("edit-email").value = email;
    document.getElementById("edit-role").value = role;
    document.getElementById("editModal").style.display = "block";
}

function closeEditModal() {
    document.getElementById("editModal").style.display = "none";
}

document.addEventListener("DOMContentLoaded", () => {
    const form = document.querySelector(".lesson-form");
    const input = form.querySelector("input[name='lesson_name']");
    const lessonTable = document.querySelector(".lesson-table tbody");

    // Add new lesson
    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const lessonName = input.value.trim();
        if (!lessonName) return;

        const response = await fetch("/admin/add_lesson", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ lesson_name: lessonName })
        });

        if (!response.ok) return showToast("⚠️ Lesson already exists");
        const lesson = await response.json();

        const row = document.createElement("tr");
        row.dataset.id = lesson.id;
        row.innerHTML = `
            <td>—</td>
            <td class="lesson-name">${lesson.name}</td>
            <td>
                <button class="edit-btn"><i class="fa-solid fa-pen"></i></button>
                <button class="delete-btn"><i class="fa-solid fa-xmark"></i></button>
            </td>
        `;
        lessonTable.appendChild(row);
        input.value = "";
        showToast("✅ Lesson added");
    });

    lessonTable.addEventListener("click", async (e) => {
        const row = e.target.closest("tr");
        if (!row) return;
        const id = row.dataset.id;

        // DELETE
        if (e.target.closest(".delete-btn")) {
            if (!confirm("Delete this lesson?")) return;
            const res = await fetch(`/admin/delete_lesson/${id}`, { method: "POST" });
            if (res.ok) {
                row.remove();
                showToast("🗑️ Lesson deleted");
            }
            return;
        }

        // EDIT
        if (e.target.closest(".edit-btn")) {
            const cell = row.querySelector(".lesson-name");
            const currentName = cell.textContent.trim();

            // Μην ανοίγεις πολλαπλό input
            if (cell.querySelector("input")) return;

            cell.innerHTML = `
            <input type="text" value="${currentName}" class="edit-input" />
            <button class="save-btn"><i class="fa-solid fa-check"></i></button>
            <button class="cancel-btn"><i class="fa-solid fa-xmark"></i></button>
        `;

            const input = cell.querySelector(".edit-input");
            const saveBtn = cell.querySelector(".save-btn");
            const cancelBtn = cell.querySelector(".cancel-btn");

            input.focus();

            cancelBtn.addEventListener("click", () => {
                cell.textContent = currentName;
            });

            saveBtn.addEventListener("click", async () => {
                const newName = input.value.trim();
                if (!newName || newName === currentName) {
                    cell.textContent = currentName;
                    return;
                }

                const res = await fetch("/admin/update_lesson", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ id, name: newName })
                });

                if (res.ok) {
                    cell.textContent = newName;
                    showToast("✏️ Lesson updated");
                } else {
                    cell.textContent = currentName;
                    showToast("⚠️ Name already in use");
                }
            });
        }
    });
});

// Optional: Toast message for feedback
function showToast(message) {
    let toast = document.getElementById("toast");
    if (!toast) {
        toast = document.createElement("div");
        toast.id = "toast";
        toast.style.position = "fixed";
        toast.style.bottom = "20px";
        toast.style.right = "20px";
        toast.style.background = "#2ecc71";
        toast.style.color = "#fff";
        toast.style.padding = "10px 20px";
        toast.style.borderRadius = "6px";
        toast.style.zIndex = "9999";
        document.body.appendChild(toast);
    }
    toast.textContent = message;
    toast.style.display = "block";
    setTimeout(() => (toast.style.display = "none"), 2500);
}


function filterUsers() {
    const input = document.getElementById("searchInput");
    const filter = input.value.toLowerCase();
    const rows = document.querySelectorAll(".user-table tbody tr:not(#noResultsRow)");
    let visibleCount = 0;

    rows.forEach(row => {
        const text = row.innerText.toLowerCase();
        const match = text.includes(filter);
        row.style.display = match ? "" : "none";
        if (match) visibleCount++;
    });

    // Εμφάνιση ή απόκρυψη του μηνύματος "Δεν βρέθηκαν"
    document.getElementById("noResultsRow").style.display = visibleCount === 0 ? "" : "none";
}
