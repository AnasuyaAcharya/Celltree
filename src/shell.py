import threading
import os
from multiprocessing import Pipe, Queue
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import FuzzyWordCompleter
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit import HTML



class Shell:

    def __init__(self, hello, cmdlist, notifiQ: Queue, pipes, initTarget=None):
        threading.Thread(target=lambda q: self.report(q), args=(notifiQ,)).start()
        sh = PromptSession()
        cmdcompleter = FuzzyWordCompleter(cmdlist, WORD=True)
        current = initTarget
        while True:
            try:
                with patch_stdout():
                    if current is None:
                        print('No target currently. Use switch to get started')
                    pstring = HTML(hello + '(<skyblue>' + str(current) + '</skyblue>)> ')
                    w = sh.prompt(pstring, completer=cmdcompleter)
                    if w=='quit':
                        break
                    if w.startswith('switch'):
                        c = w.split(' ', 1)
                        if len(c) != 2 or not c[1] in pipes.keys():
                            print('Invalid target', c[1:], '. Use list to see valid ones.')
                        else:
                            current = c[1]
                        continue
                        ##---------------
                    if w.startswith('list'):
                        print(list(pipes.keys()))
                        continue
                        ##---------------
                if current != None:
                    pipes[current].send(w)
            except Exception as ex:
                print('ERROR: ' + str(ex))
        os._exit(0)

    def report(self, notifiQ):
       while True:
           message = notifiQ.get()
           if message != None:
               print("\t" + message[0] + ":: " + str(message[1]))

