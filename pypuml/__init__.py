__version__ = "0.1.0"

import sys
from pypuml.inspector import Project

if __name__ == "__main__":
    project = Project()
    project.load_from_file(sys.argv[1])
    project.generate()
