from Tkinter import *

class MenuBar: #'player' is the name of the Tk window
    def __init__(self, parent):
        self.menubar = Menu(parent)
        self.Create()

    def Create(self):
        player.config(menu = self.menubar)

    def add_menu(self, menuname, commands):
        menu = Menu(self.menubar, tearoff = 0)

        for command in commands:
            menu.add_command(label = command[0], command = command[1])
            if command[2]:
                menu.add_separator()

        self.menubar.add_cascade(label=menuname, menu=menu)

def onExit():
    import sys
    sys.exit()

def onOpen():
    print 'Open'

    player = Tk()

    menubar = MenuBar(player)

    fileMenu = menubar.add_menu("File", commands = [("Open", onOpen, True), ("Exit", onExit, False)])

    player.mainloop()