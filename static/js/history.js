document.addEventListener("DOMContentLoaded", function () {
    const modal = document.getElementById("editQuizModal");
    const closeBtn = modal.querySelector(".close");
    const quickEditButtons = document.querySelectorAll(".quick-edit-btn");
    const editButtons = document.querySelectorAll(".edit-btn");
    const searchInput = document.getElementById("searchQuiz");
    searchInput.addEventListener("input", searchQuiz);

    document.querySelectorAll(".created-at").forEach(p => {
        const rawDate = p.dataset.createdAt;
        const date = new Date(rawDate);
        const formatted = date.toLocaleDateString("el-GR", {
            day: "2-digit",
            month: "2-digit",
            year: "numeric"
        });
        p.textContent = `Created at: ${formatted}`;
    });

    let latestQuizCard = null;

    // Άνοιγμα του modal όταν πατηθεί "Edit"
    quickEditButtons.forEach(button => {
        button.addEventListener("click", function () {
            const quizId = this.getAttribute("data-quiz-id");

            fetch(`/quiz/${quizId}`)
                .then(response => response.json())
                .then(data => {
                    document.getElementById("quizTitle").value = data.quiz_data.title;
                    document.getElementById("quizClass").value = data.quiz_data.class;

                    const lessonSelect = document.getElementById("quizLesson");
                    const lessonValue = data.quiz_data.lesson.trim().toLowerCase();

                    Array.from(lessonSelect.options).forEach(option => {
                        option.selected = option.value.trim().toLowerCase() === lessonValue;
                    });

                    modal.classList.add("show");
                });

            latestQuizCard = quizId;
        });
    });

    editButtons.forEach(button => {
        button.addEventListener("click", function () {
            const quizId = this.getAttribute("data-quiz-id");
            window.location.href = "/view_quiz/" + quizId;
        });
    });

    // Κλείσιμο του modal
    closeBtn.addEventListener("click", function () {
        modal.classList.remove("show");
    });

    // Κλείσιμο αν ο χρήστης πατήσει εκτός του modal
    window.addEventListener("click", function (event) {
        if (event.target === modal) {
            modal.classList.remove("show");
        }
    });

    const saveBtn = document.getElementById("modalSaveBtn");
    saveBtn.addEventListener("click", function (event) {
        event.preventDefault();
        const quizId = latestQuizCard;

        const title = document.getElementById("quizTitle").value;
        const lesson = document.getElementById("quizLesson").value;
        const quizClass = document.getElementById("quizClass").value;

        fetch("/quick_edit_quiz", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                quiz_id: quizId,
                title: title,
                lesson: lesson,
                class: quizClass
            })
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const saveModal = document.getElementById("saveModal");
                    saveModal.classList.add("show");
                    setTimeout(function () {
                        saveModal.classList.remove("show");
                        window.location.reload();
                    }, 1000);
                } else {
                    console.error("Failed to save changes:", data.error);
                }
            }).catch(error => console.error("Error: " + error));

        latestQuizCard = null;
    });

    const delBtns = document.querySelectorAll(".delete-btn");
    delBtns.forEach(button => {
        button.addEventListener("click", function () {
            var confirm = window.confirm("Are you sure you want to delete this quiz?");
            if (confirm) {
                var quiz = this.closest(".quiz-card").getAttribute("data-quiz-id");
                fetch("/delete_quizzes", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({ quiz_ids: [quiz] })
                })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            alert("Quiz is deleted successfully!");
                            button.closest(".quiz-card").remove();
                        } else {
                            alert("Error: " + data.error);
                        }
                    }).catch(error => console.error("Error: " + error));
            }
        });
    });

    const selectAll = document.getElementById("selectAll");
    const allCheckboxes = document.querySelectorAll(".quiz-card-checkbox");

    selectAll.addEventListener("change", function () {
        allCheckboxes.forEach(checkbox => {
            checkbox.checked = selectAll.checked;
        });
    });

    allCheckboxes.forEach(checkbox => {
        checkbox.addEventListener("change", function () {
            if (!this.checked) {
                selectAll.checked = false;
            }

            if ([...allCheckboxes].every(checkbox => checkbox.checked)) {
                selectAll.checked = true;
            }
        });
    });

    const deleteSelectedBtn = document.getElementById("deleteSelected");

    deleteSelectedBtn.addEventListener("click", function () {
        var confirm = window.confirm("Are you sure you want to delete selected quizzes?");
        if (confirm) {
            var selectedQuizzes = document.querySelectorAll(".quiz-card-checkbox:checked");
            if (selectedQuizzes.length === 0) {
                alert("No quizzes selected.");
                return;
            }

            var quizIds = Array.from(selectedQuizzes).map(quiz => quiz.closest(".quiz-card").getAttribute("data-quiz-id"));

            fetch("/delete_quizzes", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ quiz_ids: quizIds })
            })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert("Quizzes deleted successfully!");
                        selectedQuizzes.forEach(quiz => {
                            quiz.closest(".quiz-card").remove()
                        });
                        window.location.reload();
                    } else {
                        alert("Error: " + data.error);
                    }
                }).catch(error => console.error("Error: " + data.error));
        } else {
            return;
        }
    });

    const exportDropdownBtn = document.getElementById("exportDropdownBtn");
    const exportDropdown = document.querySelector(".dropdown-export");

    // Toggle dropdown menu
    exportDropdownBtn.addEventListener("click", function (e) {
        exportDropdown.classList.toggle("show");
    });

    // Handle export selection
    document.querySelectorAll(".dropdown-item").forEach(item => {
        item.addEventListener("click", function () {
            const type = this.getAttribute("data-export-type");
            exportQuizzes(type);
            exportDropdown.classList.remove("show");
        });
    });

    // Click outside to close
    window.addEventListener("click", function (e) {
        if (!exportDropdown.contains(e.target)) {
            exportDropdown.classList.remove("show");
        }
    });

    function exportQuizzes(type) {
        const selectedQuizzes = document.querySelectorAll(".quiz-card-checkbox:checked");
        if (selectedQuizzes.length === 0) {
            alert("No quizzes selected to export.");
            return;
        }

        const quizIds = Array.from(selectedQuizzes).map(q => q.closest(".quiz-card").dataset.quizId);

        fetch("/export_quizzes", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ quiz_ids: quizIds, export_type: type })
        })
            .then(res => res.blob())
            .then(blob => {
                const url = URL.createObjectURL(blob);
                const a = document.createElement("a");
                a.href = url;
                a.download = `export_${type}.zip`;
                a.click();
            })
            .catch(error => {
                console.error("Export failed:", error);
                alert("An error occurred during export.");
            });
    }


    const sortPage = document.getElementById("sortQuiz");
    const quizzesContainer = document.querySelector(".quiz-container");

    sortPage.addEventListener("change", function () {
        const selectedSort = sortPage.value;

        const quizCards = Array.from(quizzesContainer.querySelectorAll(".quiz-card"))
            .filter(card => !card.classList.contains("no-quizzes-message")); // αγνόησε το empty state

        if (selectedSort === "newest") {
            quizCards.sort((a, b) => {
                const dateA = new Date(a.dataset.createdAt);
                const dateB = new Date(b.dataset.createdAt);
                return dateB - dateA; // πιο πρόσφατο πρώτο
            });
        } else if (selectedSort === "oldest") {
            quizCards.sort((a, b) => {
                const dateA = new Date(a.dataset.createdAt);
                const dateB = new Date(b.dataset.createdAt);
                return dateA - dateB; // πιο παλιό πρώτο
            });
        } else if (selectedSort === "title") {
            quizCards.sort((a, b) => {
                const titleA = a.querySelector("h3").textContent.trim().toLowerCase();
                const titleB = b.querySelector("h3").textContent.trim().toLowerCase();
                return titleA.localeCompare(titleB);
            });
        }

        // Επανένωση των καρτών στο container με νέα σειρά
        quizCards.forEach(card => quizzesContainer.appendChild(card));
    });

    // Ενεργοποίηση default sorting στο πρώτο load
    sortPage.dispatchEvent(new Event("change"));
});

function searchQuiz() {
    const searchTerm = document.getElementById("searchQuiz").value.toLowerCase();
    const quizCards = document.querySelectorAll(".quiz-card");
    const noResultsMessage = document.getElementById("noResultsMessage");

    let visibleCount = 0;

    quizCards.forEach(function (card) {
        // Αγνόησε την "There are no quizzes yet!" κάρτα (αν υπάρχει)
        if (card.classList.contains("no-quizzes-message")) return;

        const title = card.querySelector("h3")?.textContent.toLowerCase() || "";

        if (title.includes(searchTerm)) {
            card.style.display = "";
            visibleCount++;
        } else {
            card.style.display = "none";
        }
    });

    // Εμφάνισε/κρύψε το μήνυμα αναζήτησης
    noResultsMessage.style.display = visibleCount === 0 ? "block" : "none";
}