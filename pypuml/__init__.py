__version__ = "0.1.0"

import sys
from inspector import Project

if __name__ == "__main__":
    s = Project.load_from_files([sys.argv[1]])
    s.walk()
