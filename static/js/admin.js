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

// Fade out toast message after 3s
document.addEventListener("DOMContentLoaded", () => {
    const toast = document.querySelector(".toast");
    if (toast) {
        setTimeout(() => {
            toast.style.opacity = "0";
            setTimeout(() => toast.remove(), 1000);
        }, 3000);
    }

    const counters = document.querySelectorAll(".dashboard-item p");

    counters.forEach(counter => {
        const target = +counter.innerText;
        let count = 0;

        const update = () => {
            const speed = 20;
            const increment = Math.ceil(target / speed);
            count += increment;

            if (count >= target) {
                counter.innerText = target;
            } else {
                counter.innerText = count;
                requestAnimationFrame(update);
            }
        };

        counter.innerText = "0";
        update();
    });
});

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
