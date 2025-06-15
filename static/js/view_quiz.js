function handleQuestionTypeChange(selectElement) {
    const questionDiv = selectElement.closest(".question");
    const type = selectElement.value;

    const options = questionDiv.querySelector(".options-container");
    const trueFalse = questionDiv.querySelector(".true-false-container");
    const matching = questionDiv.querySelector(".matching-container");

    options.style.display = "none";
    trueFalse.style.display = "none";
    matching.style.display = "none";

    if (type === "multiple_choice") options.style.display = "block";
    else if (type === "true_false") trueFalse.style.display = "flex";
    else if (type === "matching") matching.style.display = "block";
}

function renumberMatchingPairs(matchingContainer, questionIndex) {
    const pairs = matchingContainer.querySelectorAll(".matching-pair");
    let counter = 1;

    pairs.forEach(pair => {
        const inputs = pair.querySelectorAll("input");
        if (inputs.length === 2) {
            inputs[0].name = `matching_${questionIndex}_${counter++}`;
            inputs[1].name = `matching_${questionIndex}_${counter++}`;
        }
    });
}

function renumberQuestions() {
    document.querySelectorAll(".question").forEach((q, i) => {
        const newIndex = i + 1;
        q.querySelector("h3").textContent = `Question ${newIndex}`;

        const typeSelect = q.querySelector("select[name^='questionType_']");
        if (typeSelect) typeSelect.name = `questionType_${newIndex}`;

        const textInput = q.querySelector("input[name^='question_']");
        if (textInput) textInput.name = `question_${newIndex}`;

        const idInput = q.querySelector("input[name^='question_id_']");
        if (idInput) idInput.name = `question_id_${newIndex}`;

        for (let j = 1; j <= 4; j++) {
            const opt = q.querySelector(`input[name^='option_'][name$='_${j}']`);
            if (opt) opt.name = `option_${newIndex}_${j}`;
        }

        const correctInput = q.querySelector(`input[name^='correct_']`);
        if (correctInput) correctInput.name = `correct_${newIndex}`;

        const tfSelect = q.querySelector("select[name^='trueFalseAnswer_']");
        if (tfSelect) tfSelect.name = `trueFalseAnswer_${newIndex}`;

        const matchingContainer = q.querySelector(".matching-container");
        if (matchingContainer) renumberMatchingPairs(matchingContainer, newIndex);
    });
}

document.addEventListener("DOMContentLoaded", () => {
    const quizForm = document.getElementById("quizForm");
    const updateBtn = document.getElementById("updateBtn");
    const addQuestionBtn = document.getElementById("addQuestion");
    const questionsContainer = document.querySelector(".questionsContainer");

    let questionCount = document.querySelectorAll(".question").length;

    addQuestionBtn.addEventListener("click", () => {
        questionCount++;
        const html = `
        <div class="question">
            <div class="question-type">
                <h3>Question ${questionCount}</h3>
                <label>Question Type: </label>
                <select name="questionType_${questionCount}" required>
                    <option value="multiple_choice">Multiple Choice</option>
                    <option value="true_false">True/False</option>
                    <option value="matching">Matching</option>
                </select>
            </div>

            <div class="question-content">
                <label>Question Text: </label>
                <input type="text" name="question_${questionCount}" required>
            </div>

            <div class="options-container" style="display: block;">
                <label>Options:</label>
                <input type="text" name="option_${questionCount}_1" required>
                <input type="text" name="option_${questionCount}_2" required>
                <input type="text" name="option_${questionCount}_3" required>
                <input type="text" name="option_${questionCount}_4" required>
                <label>Correct Answer:</label>
                <select name="correct_${questionCount}" required>
                    <option value="1">Answer 1</option>
                    <option value="2">Answer 2</option>
                    <option value="3">Answer 3</option>
                    <option value="4">Answer 4</option>
                </select>
            </div>

            <div class="true-false-container" style="display: none;">
                <label>Answer:</label>
                <select name="trueFalseAnswer_${questionCount}" required>
                    <option value="true">True</option>
                    <option value="false">False</option>
                </select>
            </div>

            <div class="matching-container" style="display: none;">
                <label>Match items:</label>
                <div class="matching-pairs">
                    <div class="matching-pair">
                        <input type="text" name="matching_${questionCount}_1" required>
                        <input type="text" name="matching_${questionCount}_2" required>
                        <button type="button" class="removePairBtn">❌</button>
                    </div>
                </div>
                <button type="button" class="addPairBtn">➕ Add Pair</button>
            </div>

            <button type="button" class="removeQuestion">Remove Question</button>
        </div>`;

        questionsContainer.insertAdjacentHTML("beforeend", html);
        const newQ = questionsContainer.lastElementChild;

        newQ.querySelector("select").addEventListener("change", function () {
            handleQuestionTypeChange(this);
        });

        newQ.querySelector(".addPairBtn").addEventListener("click", function () {
            const question = this.closest(".question");
            const qIndex = question.querySelector("select[name^='questionType_']").name.split("_")[1];
            const pairsContainer = question.querySelector(".matching-pairs");
            const totalInputs = pairsContainer.querySelectorAll("input").length;

            const pair = document.createElement("div");
            pair.className = "matching-pair";
            pair.innerHTML = `
                <input type="text" name="matching_${qIndex}_${totalInputs + 1}" required>
                <input type="text" name="matching_${qIndex}_${totalInputs + 2}" required>
                <button type="button" class="removePairBtn">❌</button>`;
            pairsContainer.appendChild(pair);
            renumberMatchingPairs(pairsContainer, qIndex);
        });

        renumberQuestions();
    });

    questionsContainer.addEventListener("click", function (e) {
        if (e.target.classList.contains("removeQuestion")) {
            e.preventDefault();
            e.target.closest(".question").remove();
            renumberQuestions();
        }

        if (e.target.classList.contains("removePairBtn")) {
            const pair = e.target.closest(".matching-pair");
            const question = e.target.closest(".question");
            const matchingContainer = question.querySelector(".matching-container");
            const qIndex = question.querySelector("select[name^='questionType_']").name.split("_")[1];
            pair.remove();
            renumberMatchingPairs(matchingContainer, qIndex);
        }
    });

    // Setup for existing questions
    document.querySelectorAll(".question select[name^='questionType_']").forEach(select => {
        handleQuestionTypeChange(select);
        select.addEventListener("change", () => handleQuestionTypeChange(select));
    });

    document.querySelectorAll(".addPairBtn").forEach(btn => {
        btn.addEventListener("click", function () {
            const question = this.closest(".question");
            const qIndex = question.querySelector("select[name^='questionType_']").name.split("_")[1];
            const pairsContainer = question.querySelector(".matching-pairs");
            const totalInputs = pairsContainer.querySelectorAll("input").length;

            const pair = document.createElement("div");
            pair.className = "matching-pair";
            pair.innerHTML = `
                <input type="text" name="matching_${qIndex}_${totalInputs + 1}" required>
                <input type="text" name="matching_${qIndex}_${totalInputs + 2}" required>
                <button type="button" class="removePairBtn">❌</button>`;
            pairsContainer.appendChild(pair);
            renumberMatchingPairs(pairsContainer, qIndex);
        });
    });

    // Submit
    updateBtn.addEventListener("click", function (e) {
        e.preventDefault();

        const quizId = window.location.pathname.split("/").pop();
        const quizData = {
            id: quizId,
            quizTitle: document.getElementById("quizTitle").value,
            quizLesson: document.getElementById("quizLesson").value,
            quizClass: document.getElementById("quizClass").value,
            questions: {}
        };

        document.querySelectorAll(".question").forEach((question, i) => {
            const index = i + 1;
            const q = {};
            const select = question.querySelector("select[name^='questionType_']");
            const type = select.value;
            q.question_type = type;

            const qText = question.querySelector(`input[name="question_${index}"]`);
            if (qText) q.question_text = qText.value;

            const qId = question.querySelector(`input[name="question_id_${index}"]`);
            if (qId) q.id = qId.value;

            if (type === "multiple_choice") {
                for (let j = 1; j <= 4; j++) {
                    const opt = question.querySelector(`input[name="option_${index}_${j}"]`);
                    if (opt) q[`option_${j}`] = opt.value;
                }
                const correct = question.querySelector(`select[name="correct_${index}"]`);
                if (correct) q.correct_answer = correct.value;
            } else if (type === "true_false") {
                const tf = question.querySelector(`select[name="trueFalseAnswer_${index}"]`);
                if (tf) q.correct_answer = tf.value;
            } else if (type === "matching") {
                q.matching = [];
                question.querySelectorAll(".matching-pair input").forEach(input => {
                    q.matching.push(input.value);
                });
            }

            console.log("Correct answer for question", index, ":", q.correct_answer);


            const key = q.id ? q.id : `new_${index}`;
            quizData.questions[key] = q;

            console.log("QUIZ DATA TO SEND:", quizData);

        });

        fetch(`/update_quiz/${quizId}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(quizData)
        })
            .then(res => res.json())
            .then(data => {
                if (data.success) window.location.href = "/history";
                else alert("Update failed.");
            })
            .catch(err => {
                console.error("Update error:", err);
                alert("Something went wrong.");
            });
    });
});
