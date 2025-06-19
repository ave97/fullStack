document.addEventListener("DOMContentLoaded", () => {
    const table = document.getElementById("quizTable");
    if (!table) return;

    const headers = table.querySelectorAll("th");
    headers.forEach((header, columnIndex) => {
        let ascending = true;

        header.addEventListener("click", () => {
            const tbody = table.querySelector("tbody");
            const rows = Array.from(tbody.querySelectorAll("tr"));

            rows.sort((a, b) => {
                const cellA = a.children[columnIndex].innerText.trim();
                const cellB = b.children[columnIndex].innerText.trim();

                const valA = isNaN(cellA) ? cellA.toLowerCase() : parseFloat(cellA);
                const valB = isNaN(cellB) ? cellB.toLowerCase() : parseFloat(cellB);

                if (valA < valB) return ascending ? -1 : 1;
                if (valA > valB) return ascending ? 1 : -1;
                return 0;
            });

            ascending = !ascending;
            rows.forEach(row => tbody.appendChild(row));

            // Καθαρίζουμε όλα τα indicators
            document.querySelectorAll(".sort-indicator").forEach(ind => ind.textContent = "⇅");

            // Ορίζουμε ενεργό indicator
            const indicator = header.querySelector(".sort-indicator");
            if (indicator) indicator.textContent = ascending ? "↑" : "↓";
        });
    });
});
