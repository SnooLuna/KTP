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
        self.text = knowledge["Text"]


def check_conclusions(question, requirement):
    return True in [option["conclusion"] == requirement for option in question["options"]]


class System(CTk):
    def __init__(self, title, base):
        super().__init__()

        self.title(title)
        self.geometry("750x600")
        self._base = KnowledgeBase(base)
        self._true = []
        self._false = []
        self._current_goal = None
        self._diagnosis = "Inconclusive"
        self._screen = []
        self._frame = CTkFrame(self)
        self._frame.pack(pady=20, padx=20, fill="x")
        set_default_color_theme("dark-blue")

        self._start_screen()

    def _start_screen(self):
        self._make_label("Welcome to this self-assessment quiz!", pady=20, fontsize=25)
        self._make_label(self._base.text["introduction"], pady=20)
        self._make_button("Start", self._next_question)

    def _make_label(self, text=None, wraplength=700, pady=10, padx=0, fontsize=18):
        label = CTkLabel(self._frame, text=text, wraplength=wraplength, font=("Arial", fontsize))
        label.pack(pady=pady, padx=padx)
        self._screen.append(label)

    def _make_button(self, text=None, command=None, pady=10, padx=0):
        button = CTkButton(self._frame, text=text, command=command, font=("Arial", 16))
        button.pack(pady=pady, padx=padx, ipadx=15, ipady=5)
        self._screen.append(button)

    def _make_check(self, text=None, command=None, var=None, on=None, off=None, pady=10, padx=40):
        check = CTkCheckBox(self._frame, text=text, command=command, variable=var, onvalue=on, offvalue=off,
                            border_width=2, font=("Arial", 14))
        check.pack(pady=pady, padx=padx, anchor="w")
        self._screen.append(check)

    def _next_question(self):
        if self._ready():
            self._result_screen()
            return
        if not self._choose_goal():
            return
        symptom = self._choose_symptom()
        questions = [q for q in self._base.questions if check_conclusions(q, symptom)]
        if not questions:
            if self._base.symptoms:
                questions = [q for q in self._base.questions if q["category"] == "ata" and q["symptom"] == symptom]
            else:
                self._result_screen()
                return
        self._display(choice(questions))

    def _ready(self):
        ds = []
        for disorder in self._base.diagnostics:
            if self._diagnosable(disorder):
                self._true.append(disorder["conclusion"])   # this goal is now reached
                ds.append(disorder)
            elif self._ruled_out(disorder):
                self._false.append(disorder["conclusion"])
                if disorder["conclusion"] in self._base.goals:
                    self._base.goals.remove(disorder["conclusion"])
                ds.append(disorder)

        for d in ds:
            self._base.diagnostics.remove(d)

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
        # print(disorder["conclusion"], facts, disorder["count"], self._false, '\n', self._true)
        return facts >= disorder["count"] and (set(disorder["not"]) & set(self._false) == set(disorder["not"]))

    def _find_ata(self, symptom):
        return [question for question in self._base.questions
                if question["category"] == "ata" and question["symptom"] == symptom][0]

    def _choose_goal(self):
        if not self._base.goals:
            self._result_screen()
            return False
        self._current_goal = choice(self._base.goals)
        return True

    def _choose_symptom(self):
        categories = [categories for categories in self._base.categories if categories["conclusion"] == self._current_goal][0]
        return choice(categories["symptoms"])

    def _display(self, question):
        self._clear_screen()

        if question["category"] == "mcq":
            self._make_label(question["question"], 700, pady=50)
            for option in question["options"]:
                self._make_button(option["answer"], lambda opt=option: self._answeredMC(opt), pady=20)
        if question["category"] == "ata":
            self._make_label(question["question"], 700)
            values = {}
            for option in sample(question["options"], len(question["options"])):
                value = BooleanVar()
                self._make_check(option["answer"], var=value, on=True, off=False)
                values[option["conclusion"]] = value
            self._make_button("Done", lambda q=question, v=values: self._answered(q, v))

    def _answeredMC(self, option):
        qs = []
        for question in self._base.questions:
            if check_conclusions(question, option["conclusion"]):
                qs.append(question)
        for q in qs:
            self._base.questions.remove(q)
        self._display(self._find_ata(option["conclusion"]))

    def _answered(self, question, options):
        for fact, value in options.items():
            if fact == "Inconclusive":
                continue
            if value.get():
                self._true.append(self._base.facts.pop(self._base.facts.index(fact)))
            else:
                self._false.append(self._base.facts.pop(self._base.facts.index(fact)))
        self._base.questions.remove(question)
        self._base.symptoms.remove(question["symptom"])
        self._next_question()

    def _result_screen(self):
        self._clear_screen()
        self._make_label("Test complete!", pady=50, fontsize=24)
        self._make_label("Your result is:\n" + self._diagnosis, pady=5, fontsize=24)
        self._make_label(self._base.text["disclaimer"], pady=30)

    def _clear_screen(self):
        for label in self._screen:
            label.pack_forget()
        self._screen = []


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
