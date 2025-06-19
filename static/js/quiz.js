document.addEventListener("DOMContentLoaded", function () {
    const questionsContainer = document.getElementById("questionsContainer");
    const addQuestionButton = document.getElementById("addQuestion");
    let questionCount = 1;

    // Initialize the first question on page load
    initializeQuestion(questionCount);

    addQuestionButton.addEventListener("click", function () {
        questionCount++;

        // Create new question
        const newQuestion = document.createElement("div");
        newQuestion.classList.add("question");

        // Add content to the new question
        newQuestion.innerHTML = `
            <div class="question-type">
                <h3>Question ${questionCount}</h3>
                <label>Question Type: </label>
                <select id="questionType_${questionCount}" name="questionType_${questionCount}" required>
                    <option value="default">Select Question Type</option>
                    <option value="multiple_choice">Multiple Choice</option>
                    <option value="true_false">True/False</option>
                    <option value="matching">Matching</option>
                </select>
            </div>
            
            <div class="selectQuestionType" id="selectQT_${questionCount}">
                <h4>Please select question type to proceed</h4>
            </div>

            <!-- Question Field -->
            <div class="question-content" id="questionContent_${questionCount}">
                <label>Question: </label>
                <input type="text" name="question_${questionCount}" required>
            </div>
            <!-- Options -->
            <div id="optionContainer_${questionCount}" class="options-container">
                <label>Options: </label>
                <input type="text" name="option_${questionCount}_1" placeholder="Answer 1" required>
                <input type="text" name="option_${questionCount}_2" placeholder="Answer 2" required>
                <input type="text" name="option_${questionCount}_3" placeholder="Answer 3" required>
                <input type="text" name="option_${questionCount}_4" placeholder="Answer 4" required>
            </div>
            
            <!-- True/False -->
            <div id="trueFalseContainer_${questionCount}" class="true-false-container" style="display: none;">
                <label>Answer: </label>
                <select name="trueFalseAnswer_${questionCount}" required>
                    <option value="true">True</option>
                    <option value="false">False</option>
                </select>
            </div>

            <!-- Matching -->
            <div id="matchingContainer_${questionCount}" class="matching-container" style="display: none;">
                <label>Match items: </label>
                <div class="matching-pair">
                    <input type="text" name="matching_${questionCount}_1" placeholder="Item 1" required>
                    <input type="text" name="matching_${questionCount}_2" placeholder="Item 2" required>
                    <button type="button" class="removeMatchingBtn" id="removeMatchingBtn_${questionCount}">Remove Matching</button>
                </div>
                <button type="button" id="addMatchingBtn_${questionCount}" class="addMatchingBtn">Add Matching</button>
            </div>
            
            <!-- Correct Answer (only for multiple choice questions) -->
            <div id="correctAnswerContainer_${questionCount}" class="correct-answer-container" style="display: none;">
                <label>Correct Answer:</label>
                <select name="correct_${questionCount}" required>
                    <option value="1">Answer 1</option>
                    <option value="2">Answer 2</option>
                    <option value="3">Answer 3</option>
                    <option value="4">Answer 4</option>
                 </select>
            </div>
            
            <!-- Remove Question Button -->
            <button type="button" class="removeQuestion">Remove Question</button>
        `;

        // Append new question to the container
        questionsContainer.appendChild(newQuestion);
        newQuestion.scrollIntoView({ behavior: 'smooth', block: 'start' });

        // Event listener to handle remove button
        const removeButton = newQuestion.querySelector(".removeQuestion");
        removeButton.addEventListener("click", function () {
            newQuestion.remove();
            questionCount--;
            updateQuestionNumbers();
        });

        // Event listener to handle question type changes
        const questionTypeSelect = newQuestion.querySelector(`#questionType_${questionCount}`);
        questionTypeSelect.addEventListener("change", function () {
            handleQuestionTypeChange(questionCount);
        });

        // Call handleQuestionTypeChange to initialize the question properly
        handleQuestionTypeChange(questionCount);
    });

    // Initialize Question 1
    function initializeQuestion(questionId) {
        const questionTypeSelect = document.getElementById(`questionType_${questionId}`);
        questionTypeSelect.addEventListener("change", function () {
            handleQuestionTypeChange(questionId);
        });
        // Initialize it immediately on page load
        handleQuestionTypeChange(questionId);
    }

    // Handle question type changes dynamically
    function handleQuestionTypeChange(questionId) {
        const questionTypeSelect = document.getElementById(`questionType_${questionId}`);
        const optionContainer = document.getElementById(`optionContainer_${questionId}`);
        const trueFalseContainer = document.getElementById(`trueFalseContainer_${questionId}`);
        const matchingContainer = document.getElementById(`matchingContainer_${questionId}`);
        const matchingInputs = matchingContainer.querySelectorAll('input');
        const correctAnswerContainer = document.getElementById(`correctAnswerContainer_${questionId}`);
        const selectQT = document.getElementById(`selectQT_${questionId}`);
        const question = document.getElementById(`questionContent_${questionId}`)

        switch (questionTypeSelect.value) {
            case "multiple_choice":
                question.style.display = "flex";
                optionContainer.style.display = "block";
                trueFalseContainer.style.display = "none";
                matchingContainer.style.display = "none";
                trueFalseContainer.querySelectorAll("select").forEach(sel => sel.removeAttribute("required"));
                matchingInputs.forEach(input => input.removeAttribute("required"));
                correctAnswerContainer.style.display = "block";
                selectQT.style.display = "none";
                break;
            case "true_false":
                question.style.display = "flex";
                optionContainer.style.display = "none";
                trueFalseContainer.style.display = "flex";
                matchingContainer.style.display = "none";
                optionContainer.querySelectorAll("input").forEach(input => input.removeAttribute("required"));
                trueFalseContainer.querySelectorAll("select").forEach(sel => sel.setAttribute("required", "true"));
                matchingInputs.forEach(input => input.removeAttribute("required"));
                correctAnswerContainer.style.display = "none";
                selectQT.style.display = "none";
                break;
            case "matching":
                question.style.display = "flex";
                optionContainer.style.display = "none";
                trueFalseContainer.style.display = "none";
                matchingContainer.style.display = "block";
                optionContainer.querySelectorAll("input").forEach(input => input.removeAttribute("required"));
                trueFalseContainer.querySelectorAll("input").forEach(input => input.removeAttribute("required"));
                matchingInputs.forEach(input => input.setAttribute("required", "true"));
                correctAnswerContainer.style.display = "none";
                selectQT.style.display = "none";
                break;
            default:
                question.style.display = "none";
                optionContainer.style.display = "none";
                trueFalseContainer.style.display = "none";
                matchingContainer.style.display = "none";
                correctAnswerContainer.style.display = "none";
                selectQT.style.display = "block";
                break;
        }
    }

    // Update question numbers when a question is removed
    function updateQuestionNumbers() {
        const allQuestions = document.querySelectorAll(".question");
        allQuestions.forEach((question, index) => {
            const questionTitle = question.querySelector("h3");
            questionTitle.textContent = 'Question ' + (index + 1);
            const inputs = question.querySelectorAll("input, select");
            inputs.forEach(input => {
                input.name = input.name.replace(/\d+/, index + 1);
            });
        });
    }


    questionsContainer.addEventListener('click', function (e) {
        // Handle "Add Matching" button click
        if (e.target && e.target.classList.contains('addMatchingBtn')) {
            const questionId = e.target.id.split('_')[1];
            const matchingContainer = document.getElementById(`matchingContainer_${questionId}`);

            const matchingInputs = matchingContainer.querySelectorAll('input');
            const nextIndex = matchingInputs.length + 1;

            const newPair = document.createElement('div');
            newPair.classList.add('matching-pair');

            const newInput1 = document.createElement('input');
            newInput1.type = 'text';
            newInput1.name = `matching_${questionId}_${nextIndex}`;
            newInput1.placeholder = `Item ${nextIndex}`;
            newInput1.required = true;

            const newInput2 = document.createElement('input');
            newInput2.type = 'text';
            newInput2.name = `matching_${questionId}_${nextIndex + 1}`;
            newInput2.placeholder = `Item ${nextIndex + 1}`;
            newInput2.required = true;

            const newButton = document.createElement('button');
            newButton.type = "button";
            newButton.className = "removeMatchingBtn";
            newButton.textContent = "Remove Matching";

            newPair.appendChild(newInput1);
            newPair.appendChild(newInput2);
            newPair.appendChild(newButton);

            matchingContainer.insertBefore(newPair, matchingContainer.querySelector('.addMatchingBtn'));

            newButton.addEventListener('click', function () {
                newPair.remove();
                updatePlaceholders(questionId);
            });
        }
    });
});

