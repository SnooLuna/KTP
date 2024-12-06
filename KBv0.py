# https://github.com/achudnova/projects-yt/blob/main/QuizApp/main.py
# Used as reference!

import tkinter as tk
from tkinter import messagebox, ttk
from ttkbootstrap import Style
import json

with open("questions.json", "r") as file:
    questions_data = json.load(file)

with open("advice.json", "r") as file:
    diagnosis_advice = json.load(file)

diagnoses = ["SOUND", "AUTISM", "ADHD"]


class PersonalityTestApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Autism Diagnosis")
        self.root.geometry("800x450")
        
        self.category_scores = [0, 0, 0]
        self.current_question_index = 0

        self.info_label = tk.Label(root, text="Introduction Text.")
        self.info_label.pack(pady=10)

        self.start_button = tk.Button(root, text="Start", command=self.start_test)
        self.start_button.pack(pady=10)


    def start_test(self):
        self.info_label.pack_forget()
        self.start_button.pack_forget()
        self.show_question()


    def show_question(self):
        if self.current_question_index < len(questions_data["questions"]):
            question_data = questions_data["questions"][self.current_question_index]
            self.display_question(question_data)
        else:
            messagebox.showinfo("Out of questions!", "This is bad!")


    def display_question(self, question_data):
        self.question_label = tk.Label(
            self.root,
            text = question_data["question"],
            wraplength=700,
            justify="center",
    )
        self.question_label.pack(pady=10)
        
        self.option_buttons = []
        for option in question_data["options"]:
            button = tk.Button(
                self.root, 
                text = option["answer"],
                wraplength = 700,
                justify = "left",
                command = lambda opt=option: self.answer_question(opt))
            button.pack(pady = 5)
            self.option_buttons.append(button)

    def answer_question(self, option):
        category, increment = option["value"]
        self.category_scores[category] += increment

        for i, score in enumerate(self.category_scores):
            if score >= questions_data["thresholds"][i]: # add to array in questions.json to add more options
                self.end_test(i)
                return

        self.clear_question()
        self.current_question_index += 1
        self.show_question()

    def clear_question(self):
        self.question_label.pack_forget()
        for button in self.option_buttons:
            button.pack_forget()

    def end_test(self, exceeded_category):
        diagnosis_label = diagnoses[exceeded_category]
        advice = diagnosis_advice.get(diagnosis_label, {}).get("advice", "Not implemented yet.")
        
        result_text = f"Your diagnosis is: {diagnosis_label}\n\n {advice}"

        
        self.clear_question()
        
        self.result_label = tk.Label(self.root, text=result_text)
        self.result_label.pack(pady=20)


if __name__ == "__main__":
    root = tk.Tk()
    app = PersonalityTestApp(root)
    style = Style()
    root.mainloop()
