function togglePassword(inputId, icon) {
    const input = document.getElementById(inputId);
    const isPassword = input.type === "password";
    input.type = isPassword ? "text" : "password";
    icon.classList.toggle("fa-eye");
    icon.classList.toggle("fa-eye-slash");
}


document.addEventListener("DOMContentLoaded", function () {
    const modal = document.getElementById("loginModal");
    const flipContainer = document.querySelector(".flip-container");

    const showRegister = document.getElementById("showRegister");
    const showLogin = document.getElementById("showLogin");

    const loginError = document.getElementById("loginError");
    const registerError = document.getElementById("registerError");

    const errorMessage = modal ? modal.getAttribute("data-error") : null;
    const isRegister = modal.getAttribute("data-register");

    const modalContent = modal.querySelector(".modal-content");

    // Αρχική ρύθμιση του modal content για login ή register
    if (isRegister === "true" || isRegister === "True") {
        // Προσθέτουμε την κλάση register-form όταν είναι στην εγγραφή
        modalContent.classList.add("register-form");
        modalContent.classList.remove("login-form");
    } else {
        // Προσθέτουμε την κλάση login-form όταν είναι στη σύνδεση
        modalContent.classList.add("login-form");
        modalContent.classList.remove("register-form");
    }

    // Αν υπάρχει error εμφανίζουμε το μήνυμα στο σωστό form
    if (errorMessage && errorMessage.trim() !== "") {
        modal.classList.add("show");

        if (isRegister === "true" || isRegister === "True") {
            flipContainer.classList.add("active");
            if (registerError) {
                registerError.textContent = "";
                registerError.style.display = "none";

                registerError.textContent = errorMessage;
                registerError.style.display = "block";
                modalContent.classList.add("error-active");
            }
        } else {
            if (loginError) {
                loginError.textContent = "";
                loginError.style.display = "none";

                loginError.textContent = errorMessage;
                loginError.style.display = "block";
                modalContent.classList.add("error-active");
            }
        }
    }

    // Εναλλαγή σε Εγγραφή (με περιστροφή)
    if (showRegister) {
        showRegister.addEventListener("click", function (event) {
            event.preventDefault();
            flipContainer.classList.add("active");
            modalContent.classList.add("register-form");
            modalContent.classList.remove("login-form");

            // Αφαιρούμε την κλάση error-active όταν αλλάζουμε φόρμα
            modalContent.classList.remove("error-active");

            // Κλείνουμε το μήνυμα λάθους
            if (registerError) {
                registerError.style.display = "none";
            }
        });
    }

    // Εναλλαγή σε Σύνδεση (με περιστροφή πίσω)
    if (showLogin) {
        showLogin.addEventListener("click", function (event) {
            event.preventDefault();
            flipContainer.classList.remove("active");
            modalContent.classList.add("login-form");
            modalContent.classList.remove("register-form");

            // Αφαιρούμε την κλάση error-active όταν αλλάζουμε φόρμα
            modalContent.classList.remove("error-active");

            // Κλείνουμε το μήνυμα λάθους
            if (loginError) {
                loginError.style.display = "none";
            }
        });
    }

    const roleSelect = document.getElementById("register-role");
    const classField = document.getElementById("classField");

    function toggleClassField() {
        if (roleSelect.value === "student") {
            classField.style.display = "block";
            document.getElementById("class").required = true;
        } else {
            classField.style.display = "none";
            document.getElementById("class").required = false;
        }
    }

    // Τρέχει με την αρχική τιμή
    toggleClassField();

    // Επανυπολογισμός όταν αλλάζει επιλογή
    roleSelect.addEventListener("change", toggleClassField);
});
