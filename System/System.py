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


def question_has_matching_symptom(question, requirement):
    """Returns true if any of the conclusions of this question match the requirement"""
    return True in [option["conclusion"] == requirement for option in question["options"]]


def category_has_matching_symptom(question, requirement):
    """Returns true if any of the conclusions of this question match the requirement"""
    return True in [symptom == requirement for symptom in question["symptoms"]]


class System(CTk):
    def __init__(self, title, base):
        super().__init__()

        self._base = KnowledgeBase(base)
        self._true = []
        self._false = []
        self._current_goal = None
        self._diagnosis = "Inconclusive"

        self.title(title)
        self.geometry("750x600")
        self._screen = []
        self._frame = CTkFrame(self)
        self._frame.pack(pady=20, padx=20, fill="x")
        set_default_color_theme("dark-blue")

        self._start_screen()

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

    def _clear_screen(self):
        for widget in self._screen:      # Clear all widgets on the screen
            widget.destroy()
        self._screen = []                # Return it to be an empty list

    def _start_screen(self):
        self._make_label("Welcome to this self-assessment quiz!", pady=20, fontsize=25)
        self._make_label(self._base.text["introduction"], pady=20)
        self._make_button("Start", self._next_question)

    def _next_question(self):
        if self._ready():
            self._result_screen()               # Show diagnosis if found
            return
        if not self._choose_goal():             # Find new goal to focus on
            self._result_screen()               # Show (inconclusive) diagnosis if no more goals
            return
        symptom = self._choose_symptom()        # Find a symptom for this goal
                                                # Find all questions that focus on this symptom
        questions = [q for q in self._base.questions if question_has_matching_symptom(q, symptom)]
        if not questions:                       # No multiple choice questions were found
            if self._base.symptoms:             # There are still symptoms to ask about, ask last ATA
                questions = [q for q in self._base.questions if q["category"] == "ata" and q["symptom"] == symptom]
            else:
                self._result_screen()           # There are no symptoms to ask, show (inconclusive) diagnosis
                return
        self._display(choice(questions))        # Display the question to the user

    def _ready(self):
        ds = []
        for disorder in self._base.diagnostics:             # Go through each potential diagnosis or sub-goal
            if self._diagnosable(disorder):                 # Check if this can be concluded
                self._true.append(disorder["conclusion"])   # This goal is now reached, so add it to true facts
                ds.append(disorder)                         # Save this to be removed from potential diagnoses
            elif self._ruled_out(disorder):                 # This diagnosis is impossible to conclude
                self._false.append(disorder["conclusion"])  # Add it to false facts
                if disorder["conclusion"] in self._base.goals:          # Is this a full diagnosis (no sub-goal)
                    self._base.goals.remove(disorder["conclusion"])     # remove it as a potential goal
                ds.append(disorder)                         # Save this to be removed from potential diagnoses

        for d in ds:
            self._base.diagnostics.remove(d)                # remove concluded diagnoses and sub-goals

        if any((diagnosis := goal) in self._true for goal in self._base.goals):
            self._diagnosis = diagnosis                     # We've found a full diagnosis to conclude, ready
            return True
        return False                                        # We need to ask more questions, not ready

    def _diagnosable(self, disorder):
        # Find the amount of true facts related to this disorder
        facts = sum([sym in self._true for sym in disorder["requirements"]])
        # Return true if there are enough true facts to conclude disorder, and if any overlapping diagnoses
        # have been concluded to be false
        return facts >= disorder["count"] and all(diff in self._false for diff in disorder["not"])

    def _ruled_out(self, disorder):
        # Find the amount of false facts related to this disorder
        falses = sum([sym in self._false for sym in disorder["requirements"]])
        # Find how many false facts would rule out this disorder
        threshold = len(disorder["requirements"]) - disorder["count"]
        return falses > threshold   # Return true if this disorder is impossible to diagnose

    def _choose_goal(self):
        if not self._base.goals:                        # no goals are left, return false
            return False
        self._current_goal = choice(self._base.goals)   # make a random choice from the available goals
        return True

    def _choose_symptom(self):
        # Return a symptom category based on random choice from the list that matches our goal
        category = next(category for category in self._base.categories if category["conclusion"] == self._current_goal)
        return choice(category["symptoms"])

    def _display(self, question):
        self._clear_screen()            # clear anything previously on screen

        if question["category"] == "mcq":   # makes question label and answer buttons for MC questions
            self._make_label(question["question"], 700, pady=50)
            for option in question["options"]:
                self._make_button(option["answer"], lambda opt=option: self._answeredMC(opt), pady=20)

        if question["category"] == "ata":   # makes question label and answer checkboxes for ATA questions
            self._make_label(question["question"], 700)
            values = {}   # dictionary to store truth values into
            for option in sample(question["options"], len(question["options"])):
                value = BooleanVar()
                self._make_check(option["answer"], var=value, on=True, off=False)
                values[option["conclusion"]] = value
            # Final button for processing the checked truth values
            self._make_button("Done", lambda q=question, v=values: self._answeredATA(q, v))

    def _answeredMC(self, option):
        # Remove any way for the program to ask about this category again
        qs = []
        for question in self._base.questions:   # Go through questions to find the ones with the same conclusion
            if question_has_matching_symptom(question, option["conclusion"]):
                qs.append(question)
        for q in qs:
            self._base.questions.remove(q)      # Remove these questions from the list of possible questions to ask

        ds = []
        for disorder in self._base.categories:  # Go through disorders to find ones reasoning about the same category
            if category_has_matching_symptom(disorder, option["conclusion"]):
                ds.append(disorder)
        for d in ds:
            d["symptoms"].remove(option["conclusion"])      # Remove the option to ask about this category
            if not d["symptoms"]:
                self._base.categories.remove(d)             # Make sure there are no empty lists left over

        self._base.symptoms.remove(option["conclusion"])    # Remove the symptom category itself

        self._display(self._find_ata(option["conclusion"]))     # Display the ATA question related to this category

    def _find_ata(self, symptom):
        # Return the ATA question for which the "symptom" matches the goal category
        return next(question for question in self._base.questions
                    if question["category"] == "ata" and question["symptom"] == symptom)

    def _answeredATA(self, question, options):
        for fact, truth in options.items():
            if fact == "Inconclusive":  # Decoy questions don't need to be processed
                continue
            if truth.get():             # Move checked facts to list of true
                self._true.append(self._base.facts.pop(self._base.facts.index(fact)))
            else:                       # Move unchecked facts to list of false
                self._false.append(self._base.facts.pop(self._base.facts.index(fact)))
        self._base.questions.remove(question)               # Remove this ATA question
        self._next_question()                               # Continue asking questions

    def _result_screen(self):
        self._clear_screen()
        self._make_label("Test complete!", pady=50, fontsize=24)
        self._make_label("Your result is:\n" + self._diagnosis, pady=5, fontsize=24)
        self._make_label(self._base.text["disclaimer"], pady=30)


if __name__ == "__main__":
    sys = System("Differential Diagnoses of Autism Spectrum Disorder", "base.json")
    sys.mainloop()
