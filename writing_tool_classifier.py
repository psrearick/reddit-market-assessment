from classifier import Classifier

class WritingToolClassifier(Classifier):
    def __init__(self) -> None:
        super().__init__(['writing'])
        # super().__init__(['writing', 'writers', 'selfpublish', 'screenwriting'])
        self.topic = "software for fiction writing (using, finding, switching, complaints, support, feature requests, promotion, etc.)"
