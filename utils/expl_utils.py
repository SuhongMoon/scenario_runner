from tkinter import Tk, Text, TOP, BOTH, X, N, LEFT, RIGHT, BOTTOM, Message, W
from tkinter.ttk import Frame, Label, Entry, Button

class ExplDialog(Frame):

    def __init__(self, carla_world, widhth=700, height=600):
        super().__init__()
        self.current_action = ""
        self.current_justification = ""

        self.width = widhth
        self.height = height

        self.carla_world = carla_world

        self.initUI()

    def initUI(self):

        self.master.title("Describe your action and justify it")
        self.pack(fill=BOTH, expand=True)

        instruction = 'Instructions\nFill the two text boxes with the following\n\n' + \
        '(1) Describe WHAT you are doing, when you start the simulator and chnage your behavior\n' + \
        'Example a) I am moving forward\n' + \
        'Example b) I am passing another car while accelerating\n\n' + \
        '(2) WHY are you doing that or change the behavior\n' + \
        'Example a) as the lane is free\n' + \
        'Example b) since the car in front is going slowly and the left lane is empty\n\n' + \
        '- Do not mention objects that are not relevant to the action\n' + \
        '- Do not use proper nouns or nbames of the places\n' + \
        '- Do not use figures of speech\n\n' + \
        'You`ll note the examples always have a conjunction word such as \"as, because, since\" etc.\n' + \
        'This is to indicate the justification for the action'

        instruction_msg = Message(self, text = instruction, anchor=W, width = self.width, font=('Arial', 13))
        instruction_msg.pack(expand=True)

        action_frame = Frame(self)
        action_frame.pack(fill=X)

        action_lbl = Label(action_frame, text="Action", width=10, font=("Arial", 13) )
        action_lbl.pack(side=TOP, padx=5, pady=10, fill='both')

        self.action_entry = Entry(action_frame, textvariable=self.current_action)
        self.action_entry.pack(fill=X, padx=5, expand=True, ipady=3)

        justification_frame = Frame(self)
        justification_frame.pack(fill=X)

        justification_lbl = Label(justification_frame, text="Justification", width=14, font=("Arial", 13) )
        justification_lbl.pack(side=TOP, padx=5, pady=10, fill='both')

        self.justification_entry = Entry(justification_frame)
        self.justification_entry.pack(fill=X, padx=5, expand=True, ipady=3)

        submit_btn = Frame(self)
        submit_btn.pack(fill=X)

        btn = Button(submit_btn, text="Submit", command=self.onSubmit)
        btn.pack(padx=5, pady=10)

    def onSubmit(self):
        self.current_action = self.action_entry.get()
        self.current_justification = self.justification_entry.get()
        self.quit()

    def get_expl_desc(self):
        return self.current_justification, self.current_action
def main():
    # This part triggers the dialog
    root = Tk()
    width = 700
    height = 600
    window_size = f'{width}x{height}'
    root.geometry(window_size)
    app = ExplDialog(width, height)
    root.mainloop()

    user_input = (app.current_action, app.current_justification)

    try:
        root.destroy()
    except:
        pass

    return user_input

if __name__ == '__main__':
    follow_on_variable = main()
    print(follow_on_variable)