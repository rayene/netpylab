import os
import wx.py

class PyShell(wx.py.shell.Shell):
    def __init__(self, parent, id=-1, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=wx.CLIP_CHILDREN,
                 introText='', locals=None, *args, **kwds):
        wx.py.shell.Shell.__init__(self, parent, id=-1, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=wx.CLIP_CHILDREN,
                 introText='', InterpClass = Interpreter, locals=None, *args, **kwds)
        self.parent = parent
        self.interp.window = self
        self.mode = 'manual_input'
        
        self.syntax_errors = 0
        self.runtime_errors = 0
        self.remaining_lines = []
        self._pause = False
        self.redirectStderr() 
        self.redirectStdout() 
        
    
    def runfile(self, filename):
        f = open(filename)
        self.remaining_lines = f.readlines()
        f.close

    def play(self):
        self.prompt()
        self._pause = False
        while len(self.remaining_lines):
            command = self.remaining_lines.pop(0)
            self.run(command, prompt=False, verbose=True)
            if self.syntax_errors >0 or self.runtime_errors >0 or self._pause:
                return
            
    def pause(self):
        self._pause = True
         

    def push(self, command):
        """Send command to the interpreter for execution."""
        self.write(os.linesep)
        self.more = self.interp.push(command)
        if not self.more:
            self.addHistory(command.rstrip())
        self.prompt()
    
    def syntaxerror(self, msg):
        self.syntax_errors +=1
        # d= wx.MessageDialog(self, msg, 'Syntax Error:', wx.OK | wx.ICON_ERROR)
        # d.ShowModal()
        # d.Destroy()
        wx.Bell()
    
    def runtimeerror(self, msg):
        self.runtime_errors +=1
        # d= wx.MessageDialog(self, msg, 'Error:', wx.OK | wx.ICON_ERROR)
        # d.ShowModal()
        # d.Destroy()
        wx.Bell()
    
    def reset(self):
        self.runtime_errors = self.syntaxerror = 0

class Interpreter(wx.py.interpreter.Interpreter):
    def showsyntaxerror(self, filename = None):
        self.errormsg = ''
        wx.py.interpreter.Interpreter.showsyntaxerror(self, filename)
        self.window.syntaxerror(self.errormsg)
        
    def showtraceback(self):
        self.errormsg = ''
        wx.py.interpreter.Interpreter.showtraceback(self)
        self.window.runtimeerror(self.errormsg)

    def write(self, data):
        wx.py.interpreter.Interpreter.write(self, data)
        self.errormsg+= data
