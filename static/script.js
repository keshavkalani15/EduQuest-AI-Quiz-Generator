document.getElementById('mcq-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const keyword = document.getElementById('keyword').value;
    const difficultyLevel = document.getElementById('difficulty-level').value;
    const numMcqs = document.getElementById('num-mcqs').value;
    const resultsContainer = document.getElementById('mcq-results');
    const submitSection = document.getElementById('submit-section');
    const scoreResult = document.getElementById('score-result');

    // Reset all previous states
    resultsContainer.innerHTML = '<div class="text-center"><div class="spinner-border" role="status"><span class="visually-hidden">Loading...</span></div></div>';
    submitSection.style.display = 'none';
    scoreResult.innerHTML = '';

    // Enable submit button (in case it was disabled from previous submission)
    const submitButton = document.getElementById('submit-mcqs');
    if (submitButton) {
        submitButton.disabled = false;
    }

    try {
        const response = await fetch('/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                keyword: keyword,
                difficulty_level: difficultyLevel,
                num_mcqs: numMcqs
            })
        });

        const data = await response.json();

        if (data.error) {
            resultsContainer.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
            return;
        }

        if (typeof data.mcqs === 'string') {
            resultsContainer.innerHTML = `<div class="alert alert-danger">${data.mcqs}</div>`;
            return;
        }

        if (!Array.isArray(data.mcqs)) {
            resultsContainer.innerHTML = `<div class="alert alert-danger">Unexpected response format</div>`;
            return;
        }

        let mcqHTML = '<div class="card" id="mcq-quiz">';
        const correctAnswers = [];

        data.mcqs.forEach((mcq, index) => {
            if (!mcq.question || !mcq.options || !mcq.answer) {
                console.warn('Incomplete MCQ data:', mcq);
                return;
            }

            // Store correct answer
            correctAnswers.push(mcq.answer);

            mcqHTML += `
                <div class="card-body">
                    <h5 class="card-title">Question ${index + 1}</h5>
                    <p>${mcq.question}</p>
                    <div class="list-group">
                        ${mcq.options.map((option, optionIndex) => `
                            <label class="list-group-item">
                                <input class="form-check-input me-1" type="radio" name="question${index}" value="${String.fromCharCode(65 + optionIndex)}">
                                ${option}
                            </label>
                        `).join('')}
                    </div>
                    <div class="mt-2 text-muted small correct-answer" style="display:none;">
                        Correct Answer: ${mcq.answer}
                        ${mcq.explanation ? `<br>Explanation: ${mcq.explanation}` : ''}
                    </div>
                </div>
                ${index < data.mcqs.length - 1 ? '<hr>' : ''}
            `;
        });
        mcqHTML += '</div>';

        resultsContainer.innerHTML = mcqHTML;
        submitSection.style.display = 'block';

        // Reset any previous event listeners by cloning and replacing the submit button
        const oldSubmitButton = document.getElementById('submit-mcqs');
        const newSubmitButton = oldSubmitButton.cloneNode(true);
        oldSubmitButton.parentNode.replaceChild(newSubmitButton, oldSubmitButton);

        // Add new event listener for submit button
        newSubmitButton.addEventListener('click', () => {
            let score = 0;
            const totalQuestions = correctAnswers.length;

            // Disable all radio buttons after submission
            document.querySelectorAll('input[type="radio"]').forEach(radio => {
                radio.disabled = true;
            });

            // Disable submit button
            newSubmitButton.disabled = true;

            correctAnswers.forEach((correctAnswer, index) => {
                const selectedOption = document.querySelector(`input[name="question${index}"]:checked`);
                
                if (selectedOption && selectedOption.value === correctAnswer) {
                    score++;
                }

                // Highlight correct and incorrect answers
                const correctRadio = document.querySelector(`input[name="question${index}"][value="${correctAnswer}"]`);
                if (correctRadio) {
                    correctRadio.closest('label').classList.add('bg-success', 'text-white');
                }

                if (selectedOption && selectedOption.value !== correctAnswer) {
                    selectedOption.closest('label').classList.add('bg-danger', 'text-white');
                }
            });

            // Show score and correct answers
            scoreResult.innerHTML = `
                <div class="alert alert-info">
                    Your Score: ${score} out of ${totalQuestions} 
                    (${((score / totalQuestions) * 100).toFixed(2)}%)
                </div>
            `;

            // Reveal correct answers
            document.querySelectorAll('.correct-answer').forEach(el => {
                el.style.display = 'block';
            });
        });

    } catch (error) {
        console.error('Full error:', error);
        resultsContainer.innerHTML = `<div class="alert alert-danger">Error: ${error.message}</div>`;
    }
});