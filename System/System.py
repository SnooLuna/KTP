# https://github.com/achudnova/projects-yt/blob/main/QuizApp/main.py
# Used as reference!

from customtkinter import *
import json
import random


class KnowledgeBase:
    def __init__(self, base):
        with open(base, "r") as file:
            knowledge = json.load(file)
        self.questions = knowledge["Questions"]
        self.rules = knowledge["Rules"]
        self.goals = knowledge["Goals"]
        self.facts = knowledge["Facts"]


def check_conclusions(question, requirement):
    return True in [option["conclusion"] == requirement for option in question["options"]]


class System(CTk):
    def __init__(self, title, base):
        super().__init__()

        self.title(title)
        self.geometry("800x450")
        self._base = KnowledgeBase(base)
        self._true = []
        self._false = []
        self._current_goal = None
        self._screen = []
        set_default_color_theme("green")

        self._start_screen()

    def _start_screen(self):
        self._make_label("Introduction Text.")
        self._make_button("Start", self._run)
        print(self._screen)

    def _make_label(self, text=None, wraplength=700, pady=10, padx=0):
        label = CTkLabel(self, text=text, wraplength=wraplength)
        label.pack(pady=pady, padx=padx)
        self._screen.append(label)

    def _make_button(self, text=None, command=None, pady=None, padx=None):
        button = CTkButton(self, text=text, command=command)
        button.pack(pady=pady, padx=padx)
        self._screen.append(button)

    def _run(self):
        self._choose_goal()
        if self._current_goal is None:
            self._result()
        question = self._find_question(self._choose_goal())
        self._display(question)

    def _choose_goal(self):
        self._current_goal = "OCD"
        return "OCD"  # random.choice(self._base.goals)

    def _find_question(self, goal):
        rule = random.choice([item for item in self._base.rules if item["conclusion"] == goal])
        requirement = random.choice(rule["requirements"])
        questions = [question for question in self._base.questions if check_conclusions(question, requirement)]
        if not questions:
            return self._find_question(requirement)
        return random.choice(questions)

    def _display(self, question):
        self._clear_screen()

        self._make_label(question["question"], 700)

        for option in question["options"]:
            self._make_button(option["answer"], lambda opt=option: self._answered(opt), 5)

    def _answered(self, option):
        self._true = self._base.facts.pop(self._base.facts.index(option["conclusion"]))

    def _result_screen(self, conclusion):
        pass

    def _clear_screen(self):
        for label in self._screen:
            label.pack_forget()


if __name__ == "__main__":
    sys = System("Differential Diagnoses of Autism Spectrum Disorder", "base.json")
    sys.mainloop()
