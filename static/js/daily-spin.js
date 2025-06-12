function getRandomRewardMessage(bonus) {
    const messages = [
        "🎉 Yay! You won: ",
        "✨ Awesome! You earned: ",
        "🏆 Great job! Reward: ",
        "🎊 Hooray! You got: "
    ];
    const random = Math.floor(Math.random() * messages.length);
    return messages[random] + bonus + "!";
}

document.addEventListener("DOMContentLoaded", () => {
    const modal = document.getElementById("bonusModal");
    const openBtn = document.getElementById("openBonusModal");
    const closeBtn = document.querySelector(".modal .close");
    const flipCards = document.querySelectorAll(".flip-card");
    const resultMessage = document.getElementById("resultMessage");

    let rewards = [];
    let yourBonus = "";
    let correctIndex = -1;
    let hasSpun = false;

    // Έλεγχος αν έχει ήδη κάνει spin
    fetch("/has_spun_today")
        .then(res => res.json())
        .then(data => {
            if (data.spun) {
                openBtn.disabled = true;
                openBtn.textContent = "✔️ Bonus claimed";
                openBtn.classList.add("disabled-btn");
            }
        });

    // Κουμπί για να ανοίξει το modal (δεν στέλνει ακόμα τίποτα)
    openBtn.addEventListener("click", () => {
        if (hasSpun) return;

        // Reset κάρτες
        flipCards.forEach(card => {
            card.classList.remove("flipped", "highlighted-card");
            card.querySelector(".flip-back").textContent = "";
            card.style.pointerEvents = "auto";
        });

        resultMessage.textContent = "";
        modal.style.display = "block";
    });

    // Κλείσιμο modal
    closeBtn.addEventListener("click", () => {
        modal.style.display = "none";
    });

    // Κλικ σε κάρτα — Στέλνει τη θέση στο Flask
    flipCards.forEach((card, index) => {
        card.addEventListener("click", () => {
            if (card.classList.contains("flipped") || hasSpun) return;

            fetch("/daily_spin", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ chosen_index: index })
            })
                .then(res => res.json())
                .then(data => {
                    if (!data.success) {
                        resultMessage.textContent = "⚠️ Κάτι πήγε λάθος.";
                        return;
                    }

                    rewards = data.rewards;
                    yourBonus = data.your_bonus;
                    correctIndex = data.correct_index;
                    hasSpun = true;

                    // Γυρνά μόνο την κάρτα που πάτησε ο μαθητής
                    card.setAttribute("data-reward", rewards[index]);
                    card.querySelector(".flip-back").textContent = rewards[index];
                    card.classList.add("flipped");
                    card.style.pointerEvents = "none";

                    if (index === correctIndex) {
                        card.classList.add("highlighted-card");
                    }

                    flipCards.forEach(c => c.style.pointerEvents = "none");

                    // ⏳ Μετά από 1.5s γύρνα τις υπόλοιπες
                    setTimeout(() => {
                        flipCards.forEach((c, i) => {
                            if (i !== index && !c.classList.contains("flipped")) {
                                c.setAttribute("data-reward", rewards[i]);
                                c.querySelector(".flip-back").textContent = rewards[i];
                                c.classList.add("flipped");

                                if (i === correctIndex) {
                                    c.classList.add("highlighted-card");
                                }
                            }
                        });
                    }, 1500);

                    // Μήνυμα
                    if (index === correctIndex) {
                        resultMessage.textContent = getRandomRewardMessage(yourBonus);
                    }

                    setTimeout(() => {
                        modal.style.display = "none";
                        location.reload();
                    }, 4000);
                });
        });
    });
});