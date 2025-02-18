from classifier import Classifier

class WritingToolClassifier(Classifier):
    def __init__(self) -> None:
        super().__init__(['writing', 'scrivener'])
        self.topic = "writing software/tools"
