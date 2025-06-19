document.addEventListener('DOMContentLoaded', function () {
    let score = 0;
    let correctAnswer = 0;
    let angle = 0;
    let startTime = null;
    let pendingPoints = 0;
    let currentWinningSlice = null;
    let idleRotationInterval = null;
    let matches = [];
    let userAnswers = [];
    let totalSpins = 0;
    let questionLocked = false;
    let questionActive = false;

    const scoreDisplay = document.getElementById('score');
    const timerDisplay = document.getElementById('timer');
    const spinButton = document.getElementById('spinWheelBtn');
    const tickSound = new Audio('/static/sounds/wheel-tick.mp3');
    const correctSound = new Audio('/static/sounds/correct.mp3');
    const wrongSound = new Audio('/static/sounds/wrong.mp3');
    const questionBox = document.getElementById('questionBox');
    const quizData = JSON.parse(document.getElementById('game-container').getAttribute('data-quiz'));
    const questions = quizData.questions;
    let currentQuestionIndex = 0;

    tickSound.loop = true;
    tickSound.volume = 1;
    correctSound.volume = 1;
    wrongSound.volume = 1;

    function startIdleRotation() {
        let idleAngle = 0;
        idleRotationInterval = setInterval(() => {
            idleAngle += 0.1;
            wheelSetup.wheelGroup.style.transform = `rotate(${idleAngle}deg)`;
        }, 20);
    }

    const timerInterval = setInterval(updateTimerDisplay, 1000);

    function updateTimerDisplay() {
        if (startTime) {
            const now = Date.now();
            const elapsed = Math.floor((now - startTime) / 1000);
            const minutes = Math.floor(elapsed / 60);
            const seconds = elapsed % 60;
            timerDisplay.textContent = `Time: ${minutes}:${seconds.toString().padStart(2, '0')}`;
        }
    }

    spinButton.addEventListener('click', function () {
        if (spinButton.disabled || questionActive) return;  // Αν υπάρχει ενεργή ερώτηση, μην κάνει spin
        spinButton.disabled = true;

        if (currentWinningSlice) {
            currentWinningSlice.classList.remove('slice-blink', 'slice-pop');
        }
        if (!startTime) startTime = Date.now();

        if (idleRotationInterval) {
            clearInterval(idleRotationInterval);
            idleRotationInterval = null;
        }

        const spins = Math.floor(Math.random() * 3) + 3;
        const extraDegrees = Math.floor(Math.random() * 360);
        angle += spins * 360 + extraDegrees;

        tickSound.play();
        wheelSetup.wheelGroup.style.transform = `rotate(${angle}deg)`;

        totalSpins++;

        setTimeout(() => {
            tickSound.pause();
            tickSound.currentTime = 0;

            const normalized = angle % 360;
            const sector = Math.floor((360 - normalized) / wheelSetup.sliceAngle);
            const pickedLabel = wheelSetup.labels[sector % wheelSetup.numberOfSlices];

            if (currentWinningSlice) currentWinningSlice.classList.remove('slice-blink', 'slice-pop');
            wheelSetup.slices.forEach(slice => slice.classList.remove('slice-blink', 'slice-pop'));

            const winningSlice = wheelSetup.slices[sector % wheelSetup.numberOfSlices];
            currentWinningSlice = winningSlice;
            winningSlice.classList.add('slice-blink', 'slice-pop');

            scoreDisplay.classList.remove('bling', 'win', 'lose', 'bomb');

            if (pickedLabel === 'Bomb') {
                wrongSound.play();
                score = 0;
                scoreDisplay.classList.add('bomb');
                scoreDisplay.textContent = `Score: ${score}`;
                questionActive = false;
                spinButton.disabled = false;
                setTimeout(() => scoreDisplay.classList.remove('bomb'), 1500);
                return;
            } else if (pickedLabel.startsWith('-')) {
                wrongSound.play();
                score = Math.max(0, score - Math.abs(parseInt(pickedLabel)));
                scoreDisplay.classList.add('bling', 'lose');
                scoreDisplay.textContent = `Score: ${score}`;
                questionActive = false;
                spinButton.disabled = false;
                setTimeout(() => scoreDisplay.classList.remove('bling', 'lose'), 1500);
                return;
            }

            pendingPoints = parseInt(pickedLabel);
            showNextQuestion();
            spinButton.disabled = false;
        }, 4000);
    });

    function showNextQuestion() {
        questionActive = true;

        questionBox.innerHTML = '';
        if (currentQuestionIndex >= questions.length) return endGame();

        const question = questions[currentQuestionIndex];

        const title = document.createElement('div');
        title.textContent = question.question_text;
        title.style.marginBottom = '20px';
        title.style.fontSize = '22px';
        questionBox.appendChild(title);

        const audio = document.getElementById("ttsAudio");
        const filename = `quiz_${quizData.id}_question_${question.id}`;
        audio.src = `/static/sounds/questions/${filename}.mp3`;
        audio.play();

        const wrapper = document.createElement('div');
        wrapper.classList.add('options-wrapper');
        questionBox.appendChild(wrapper);

        if (question.question_type === 'multiple_choice') {
            question.options.forEach((option, index) => {
                if (option) {
                    const btn = document.createElement('button');
                    btn.textContent = option;
                    btn.classList.add('answer-button');
                    btn.onclick = () => checkAnswer(index + 1, question.correct_answer, question, option);
                    wrapper.appendChild(btn);
                }
            });
        } else if (question.question_type === 'true_false') {
            ['True', 'False'].forEach(option => {
                const btn = document.createElement('button');
                btn.textContent = option;
                btn.classList.add('answer-button');
                btn.onclick = () => checkAnswer(option.toLowerCase(), String(question.correct_answer).toLowerCase(), question, option);
                wrapper.appendChild(btn);
            });
        } else if (question.question_type === 'matching') {
            matches = [];
            const pairs = question.matching_pairs;
            const leftItems = [...new Set(pairs.map(p => p.item_1))];
            const rightItems = [...new Set(pairs.map(p => p.item_2))];

            shuffleArray(leftItems);
            shuffleArray(rightItems);

            const container = document.createElement("div");
            container.classList.add("matching-container");

            const leftCol = document.createElement("div");
            leftCol.classList.add("matching-column", "left-column");
            const rightCol = document.createElement("div");
            rightCol.classList.add("matching-column", "right-column");

            leftItems.forEach(item => {
                const el = document.createElement("div");
                el.classList.add("match-item");
                el.textContent = item;
                el.setAttribute("data-side", "left");
                el.setAttribute("data-value", item);
                leftCol.appendChild(el);
            });

            rightItems.forEach(item => {
                const el = document.createElement("div");
                el.classList.add("match-item");
                el.textContent = item;
                el.setAttribute("data-side", "right");
                el.setAttribute("data-value", item);
                rightCol.appendChild(el);
            });

            container.appendChild(leftCol);
            container.appendChild(rightCol);

            const svgLines = document.createElementNS("http://www.w3.org/2000/svg", "svg");
            svgLines.classList.add("matching-lines");
            svgLines.setAttribute("width", "100%");
            svgLines.setAttribute("height", "100%");
            svgLines.style.position = "absolute";
            svgLines.style.top = "0";
            svgLines.style.left = "0";
            svgLines.style.pointerEvents = "none";
            container.appendChild(svgLines);

            questionBox.appendChild(container);
            setupMatchingLogic();

            const submitBtn = document.createElement('button');
            submitBtn.textContent = "Submit Answer";
            submitBtn.classList.add("answer-button");
            submitBtn.onclick = () => checkMatchingAnswer(matches, question.matching_pairs, question);
            questionBox.appendChild(submitBtn);
        }

        setTimeout(() => {
            questionBox.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 100);
    }

    function setupMatchingLogic() {
        let firstSelected = null;
        matches = [];

        document.querySelectorAll(".match-item").forEach(item => {
            item.addEventListener("click", () => {
                if (item.classList.contains("selected")) {
                    item.classList.remove("selected");
                    firstSelected = null;
                    return;
                }

                item.classList.add("selected");

                if (!firstSelected) {
                    firstSelected = item;
                } else if (firstSelected.getAttribute("data-side") !== item.getAttribute("data-side")) {
                    const left = firstSelected.getAttribute("data-side") === "left" ? firstSelected : item;
                    const right = firstSelected.getAttribute("data-side") === "right" ? firstSelected : item;

                    matches.push({ left: left.getAttribute("data-value"), right: right.getAttribute("data-value") });

                    left.classList.add("matched");
                    right.classList.add("matched");
                    left.classList.remove("selected");
                    right.classList.remove("selected");

                    const svg = document.querySelector(".matching-lines");
                    const leftRect = left.getBoundingClientRect();
                    const rightRect = right.getBoundingClientRect();
                    const containerRect = svg.parentElement.getBoundingClientRect();

                    const x1 = leftRect.right - containerRect.left;
                    const y1 = leftRect.top + leftRect.height / 2 - containerRect.top;
                    const x2 = rightRect.left - containerRect.left;
                    const y2 = rightRect.top + rightRect.height / 2 - containerRect.top;

                    const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
                    line.setAttribute("x1", x1);
                    line.setAttribute("y1", y1);
                    line.setAttribute("x2", x2);
                    line.setAttribute("y2", y2);
                    line.setAttribute("stroke", "#ffd166");
                    line.setAttribute("stroke-width", "3");
                    line.setAttribute("stroke-linecap", "round");

                    svg.appendChild(line);
                    firstSelected = null;
                } else {
                    firstSelected.classList.remove("selected");
                    item.classList.remove("selected");
                    firstSelected = null;
                }
            });
        });
    }

    function checkAnswer(selected, correct, question, userResponse) {
        if (questionLocked) return;
        questionLocked = true;
        const isCorrect = selected === correct;
        if (isCorrect) {
            correctSound.play();
            score += pendingPoints;
            correctAnswer++;
            scoreDisplay.classList.add("bling", "win");
        } else {
            wrongSound.play();
            scoreDisplay.classList.add("bling", "lose");
        }

        scoreDisplay.textContent = `Score: ${score}`;
        userAnswers.push({ question, correct: isCorrect, userResponse });

        // if (currentWinningSlice) {
        //     currentWinningSlice.classList.remove('slice-blink', 'slice-pop');
        // }

        setTimeout(() => {
            scoreDisplay.classList.remove("bling", "win", "lose");
            currentQuestionIndex++;
            questionBox.innerHTML = '<div>Spin the wheel</div>';
            questionLocked = false;
            questionActive = false;

            document.getElementById('wheel-container').scrollIntoView({
                behavior: 'smooth',
                block: 'center'
            });

            if (currentQuestionIndex >= questions.length) endGame();
        }, 1500);
    }

    function checkMatchingAnswer(givenMatches, correctMatches, question) {
        const svg = document.querySelector(".matching-lines");
        const lines = svg.querySelectorAll("line");
        let correctCount = 0;

        givenMatches.forEach((match, index) => {
            const isCorrect = correctMatches.some(
                correct => correct.item_1 === match.left && correct.item_2 === match.right
            );
            if (lines[index]) lines[index].setAttribute("stroke", isCorrect ? "#4caf50" : "#e53935");
            if (isCorrect) correctCount++;
        });

        const isAllCorrect = correctCount === correctMatches.length;
        if (isAllCorrect) {
            correctSound.play();
            score += pendingPoints;
            scoreDisplay.classList.add("bling", "win");
        } else {
            wrongSound.play();
            scoreDisplay.classList.add("bling", "lose");
        }

        scoreDisplay.textContent = `Score: ${score}`;
        userAnswers.push({ question, correct: isAllCorrect, userResponse: givenMatches });

        if (currentWinningSlice) {
            currentWinningSlice.classList.remove('slice-blink', 'slice-pop');
        }

        setTimeout(() => {
            scoreDisplay.classList.remove("bling", "win", "lose");
            currentQuestionIndex++;
            questionBox.innerHTML = '<div>Spin the wheel</div>';
            questionLocked = false;
            questionActive = false;

            document.getElementById('wheel-container').scrollIntoView({
                behavior: 'smooth',
                block: 'center'
            });

            if (currentQuestionIndex >= questions.length) endGame();
        }, 1500);
    }

    function endGame() {
        spinButton.disabled = true;
        clearInterval(timerInterval);
        const endTime = Date.now();
        const totalTime = Math.floor((endTime - startTime) / 1000);

        const payload = {
            quiz_id: quizData.id,
            score,
            totalTime,
            correct: userAnswers.filter(a => a.correct).length,
            total: userAnswers.length,
            answers: userAnswers,
            total_spins: totalSpins
        };

        fetch("/quiz_summary_data", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        }).then(() => {
            window.location.href = `/quiz_summary/${quizData.id}`;
        });
    }

    function shuffleArray(array) {
        for (let i = array.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [array[i], array[j]] = [array[j], array[i]];
        }
    }

    startIdleRotation();
});
