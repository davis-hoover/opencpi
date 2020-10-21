import sys


def ask(*args):  # TODO: Verify whether the ${*} from the Bash file is the same as *args
    """Confirm with the user about performing an action"""
    if JENKINS_HOME:  # TODO: figure out where this directory should be found
        print(f"OCPI:WARNING: Running under Jenkins: auto-answered 'yes' to '{args}?'")
        ans = True
    if not force:
        while not (ans is True or ans is False):
            ans = input(f"Are you sure you want to {args}? (y or n)")
            if ans is "n" or ans is "N":
                ans = False
            elif ans is "y" or ans is "Y":
                ans = True
        if ans is False:
            sys.exit(1)
