from customtkinter import *
import json
from random import choice, sample


class KnowledgeBase:
    def __init__(self, base):
        with open(base, "r") as file:
            knowledge = json.load(file)
        self.questions = knowledge["Questions"]
        self.diagnostics = knowledge["Diagnostics"]
        self.goals = knowledge["Goals"]
        self.symptoms = knowledge["Symptoms"]
        self.facts = knowledge["Facts"]
        self.categories = knowledge["Categories"]


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
        self._diagnosis = "Inconclusive"
        self._screen = []
        set_default_color_theme("green")

        self._start_screen()

    def _start_screen(self):
        self._make_label("Introduction Text.")
        self._make_button("Start", self._next_question)

    def _make_label(self, text=None, wraplength=700, pady=10, padx=0):
        label = CTkLabel(self, text=text, wraplength=wraplength)
        label.pack(pady=pady, padx=padx)
        self._screen.append(label)

    def _make_button(self, text=None, command=None, pady=10, padx=0):
        button = CTkButton(self, text=text, command=command)
        button.pack(pady=pady, padx=padx)
        self._screen.append(button)

    def _make_check(self, text=None, command=None, var=None, on=None, off=None, pady=10, padx=0):
        check = CTkCheckBox(self, text=text, command=command, variable=var, onvalue=on, offvalue=off)
        check.pack(pady=pady, padx=padx)
        self._screen.append(check)

    def _next_question(self):
        if self._ready():
            self._result_screen()
            return
        self._choose_goal()
        symptom = self._choose_symptom()
        questions = [q for q in self._base.questions if check_conclusions(q, symptom)]
        if not questions:
            self._result_screen()
            return
        self._display(choice(questions))

    def _ready(self):
        for disorder in self._base.diagnostics:
            if self._diagnosable(disorder):
                self._true.append(disorder["conclusion"])   # this goal is now reached
                self._base.diagnostics.remove(disorder)           # cant diagnose it again
            if self._ruled_out(disorder):
                self._false.append(disorder["conclusion"])
                self._base.diagnostics.remove(disorder)

        if any((diagnosis := goal) in self._true for goal in self._base.goals):
            self._diagnosis = diagnosis
            return True
        return False

    def _ruled_out(self, disorder):
        falses = sum([sym in self._false for sym in disorder["requirements"]])
        threshold = len(disorder["requirements"]) - disorder["count"]
        return falses > threshold

    def _diagnosable(self, disorder):
        facts = sum([sym in self._true for sym in disorder["requirements"]])
        return facts >= disorder["count"] and (set(disorder["not"]) & set(self._false) == set(disorder["not"]))

    def _find_ata(self, symptom):
        return [question for question in self._base.questions if question["symptom"] == symptom][0]

    def _choose_goal(self):
        if not self._base.goals:
            self._result_screen()
            return
        self._current_goal = choice(self._base.goals)

    def _choose_symptom(self):
        categories = [categories for categories in self._base.categories if categories["conclusion"] == self._current_goal][0]
        return choice(categories["symptoms"])

    def _display(self, question):
        self._clear_screen()

        self._make_label(question["question"], 700)

        if question["category"] == "mcq":
            for option in question["options"]:
                self._make_button(option["answer"], lambda q=question, opt=option: self._answeredMC(q, opt), 5)
        if question["category"] == "ata":
            values = {}
            for option in sample(question["options"], len(question["options"])):
                value = BooleanVar()
                self._make_check(option["answer"], var=value, on=True, off=False)
                values[option["conclusion"]] = value
            self._make_button("Done", lambda q=question, v=values: self._answered(q, v))

    def _answeredMC(self, question, option):
        self._base.questions.remove(question)
        for question in self._base.questions:
            if check_conclusions(question, option["conclusion"]):
                self._base.questions.remove(question)
        self._display(self._find_ata(option["conclusion"]))

    def _answered(self, question, options):
        for fact, value in options.items():
            if value.get():
                self._true.append(self._base.facts.pop(self._base.facts.index(fact)))
            else:
                self._false.append(self._base.facts.pop(self._base.facts.index(fact)))
        self._base.questions.remove(question)
        self._next_question()

    def _result_screen(self):
        self._clear_screen()
        self._make_label(self._result_text0(), pady=50)
        self._make_label(self._result_text1(self._diagnosis), pady=5)
        self._make_label(self._result_text2())

    def _clear_screen(self):
        for label in self._screen:
            label.pack_forget()
        self._screen = []

    def _result_text0(self):
        return "Test Complete!"

    def _result_text1(self, diagnosis):
        return "U got: " + diagnosis

    def _result_text2(self):
        return "this is not real advice"


if __name__ == "__main__":
    sys = System("Differential Diagnoses of Autism Spectrum Disorder", "base.json")
    sys.mainloop()

# choose goal
# choose symptom based on goal
# choose MC question based on symptom
# display ATA question based on answer
# check if diagnosis is done
# choose new goal if no goal
# choose new symptom...
