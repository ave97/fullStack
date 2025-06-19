class Question:
    def __init__(
        self,
        questionNum: int,
        questionText: str,
        questionType: str,
        option1: str = None,
        option2: str = None,
        option3: str = None,
        option4: str = None,
        correctAnswer: str = None,
        matchingItems: list = None,
    ):
        self.questionNum = questionNum
        self.questionText = questionText
        self.questionType = questionType
        self.option1 = option1
        self.option2 = option2
        self.option3 = option3
        self.option4 = option4
        self.correctAnswer = correctAnswer
        self.matchingItems = matchingItems if matchingItems is not None else []

    # Getter methods
    def getQuestionNum(self):
        return self.questionNum

    def getQuestionText(self):
        return self.questionText

    def getQuestionType(self):
        return self.questionType

    def getOptions(self):
        return {
            "option1": self.option1,
            "option2": self.option2,
            "option3": self.option3,
            "option4": self.option4,
        }

    def getCorrectAnswer(self):
        return self.correctAnswer

    def getMatchingItems(self):
        return self.matchingItems


class Quiz:
    def __init__(self, quizTitle: str, quizLesson: int):
        self.quizTitle = quizTitle
        self.quizLesson = quizLesson

    def getTitle(self):
        return self.quizTitle

    def getLesson(self):
        return self.quizLesson
