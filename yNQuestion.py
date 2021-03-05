from tkinter import messagebox

answer = messagebox.askokcancel("Question","Do you want to open this file?")
print(answer)
answer = messagebox.askretrycancel("Question", "Do you want to try that again?")
print(answer)
answer = messagebox.askyesno("Question","Do you like Python?")
print(answer)
answer = messagebox.askyesnocancel("Question", "Continue playing?")
print(answer)

messagebox.showinfo("Information","Informative message")
messagebox.showerror("Error", "Error message")
messagebox.showwarning("Warning","Warning message")