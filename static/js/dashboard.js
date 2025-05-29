document.addEventListener("DOMContentLoaded", function () {

    const links = document.querySelectorAll(".sidebar ul li a");
    const currentPath = window.location.pathname;

    links.forEach(link => {
        if (currentPath.includes(link.pathname) && link.pathname != "/") {
            link.classList.add("active");
        }
    });

    const viewButtons = document.querySelectorAll("#view-btn");

    viewButtons.forEach(button => {
        button.addEventListener("click", function () {
            const quizId = button.dataset.quizId;
            fetch("/quiz/" + button.dataset.quizId)
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        window.location.href = "/view_quiz/" + button.dataset.quizId;
                    } else {
                        console.log("Error: " + data.error);
                    }
            }).catch(error => console.error("Error: " + error));
        });
    });

    const animatedNumbers = document.querySelectorAll('.animated-number');

    animatedNumbers.forEach(el => {
        const target = parseFloat(el.dataset.target);
        const isPercentage = el.textContent.trim().includes('%');

        let count = 0;
        const increment = target / 60; // 60 frames ≈ 1 sec

        const updateCount = () => {
            count += increment;
            if (count >= target) {
                el.textContent = isPercentage ? `${target.toFixed(1)}%` : Math.round(target);
            } else {
                el.textContent = isPercentage ? `${count.toFixed(1)}%` : Math.round(count);
                requestAnimationFrame(updateCount);
            }
        };

        requestAnimationFrame(updateCount);
    });
});