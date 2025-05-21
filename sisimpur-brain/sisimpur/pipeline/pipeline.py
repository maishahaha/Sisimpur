from .base import Step
from .detect import DetectStep
from .extract import ExtractStep
from .generate import GenerateQAStep
from .persist import PersistStep


class Pipeline:
    def __init__(self, steps: list[Step]):
        self.steps = steps

    def run(self, file_path: str, num_questions: int = None) -> dict:
        context = {"file_path": file_path, "num_questions": num_questions}
        for step in self.steps:
            context = step.run(context)
        return context


def default_pipeline():
    return Pipeline([DetectStep(), ExtractStep(), GenerateQAStep(), PersistStep()])
