import sys
class _Getch:
    """Gets a single character from standard input.  Does not echo to the
screen."""
    def __init__(self):
        try:
            self.impl = _GetchWindows()
        except ImportError:
            self.impl = _GetchUnix()
 
    def __call__(self): return self.impl()
 
 
class _GetchUnix:
    def __init__(self):
        import tty, sys
 
    def __call__(self):
        import sys, tty, termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno(), termios.TCSANOW)
            ch = sys.stdin.read(1)
            sys.stdout.write(ch)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch
 
 
class _GetchWindows:
    def __init__(self):
        import msvcrt
 
    def __call__(self):
        import msvcrt
        return msvcrt.getch()
 
 
getch = _Getch()
## end of http://code.activestate.com/recipes/134892/ }}}
 
# command = ""
# while True:
#     ch = getch()
#     if ch == "\r":
#         print("\nExecute command: " + command)
#         command = ""
#         sys.stdout.write("\033[80D")
#     else:
#         command += ch
#         if command == "quit":
#             sys.stdout.write("\033[80D")
#             print "\nBye."
#             break

import time 
if __name__=="__main__":
    i = 0
    while True:
        print( i, getch() )
        time.sleep( 1 )
        i = i+1