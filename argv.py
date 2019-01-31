#!/usr/bin/python3 -B

"""
A collection of simple command-line parsing functions.
"""

from __future__ import print_function as __print  # hide from help(argv)

import os                         # standard library
import sys                        # standard library
import re                         # standard library  # pylint: disable=unused-import
import glob                       # standard library
import unittest                   # standard library

# pylint: disable=invalid-name

######################################################################################
#
#  P U B L I C   A P I
#
######################################################################################

def filenames(patterns, extensions=None, sort=False, allowAllCaps=False):
    """
    Examples:
      filenames, basenames = argv.filenames(sys.argv[1:])
      filenames, basenames = argv.filenames(sys.argv[1:], [".ppm", ".png"], sort=True)
      filenames, basenames = argv.filenames(sys.argv[1:], [".jpg"], allowAllCaps=True)
    """
    fullnames = [glob.glob(filepattern) for filepattern in patterns]                # expand wildcards
    fullnames = [item for sublist in fullnames for item in sublist]                 # flatten nested lists
    fullnames = [f for f in set(fullnames) if os.path.exists(f)]                    # check file existence
    if extensions is not None:
        extensions += [e.upper() for e in extensions] if allowAllCaps else []       # jpg => [jpg, JPG]
        fullnames = [f for f in fullnames if os.path.splitext(f)[1] in extensions]  # filter by extension
    fullnames = sorted(fullnames) if sort else fullnames                            # sort if requested
    basenames = [os.path.splitext(f)[0] for f in fullnames]                         # strip extensions
    return fullnames, basenames

def exists(argname):
    """
    Example:
      showHelp = argv.exists("--help")
    """
    if argname in sys.argv:
        argidx = sys.argv.index(argname)
        del sys.argv[argidx]
        return True
    return False

def intval(argname, default=None, accepted=None, condition=None):
    """
    Example:
      numtiles = argv.intval("--split", 1, [1, 2, 3, 4])
    """
    argstr = _string(argname)
    useDefault = argstr is None
    if not useDefault:
        errmsg = "Invalid value for '%s': '%s' does not represent an integer."%(argname, argstr)
        _enforce(_isInt(argstr), errmsg)
        argval = int(argstr, 0)  # hex values must have the "0x" prefix for this to work
        if not _isValid(argname, argval, accepted, condition):
            sys.exit(-1)
    return default if useDefault else argval

def floatval(argname, default=None, accepted=None, condition=None):
    """
    Example:
      factor = argv.floatval("--factor", 1.0, condition='1.0 <= v <= 3.0')
    """
    argstr = _string(argname)
    useDefault = argstr is None
    if not useDefault:
        errmsg = "Invalid value for '%s': '%s' does not represent a number."%(argname, argstr)
        _enforce(_isFloat(argstr), errmsg)
        if not _isValid(argname, float(argstr), accepted, condition):
            sys.exit(-1)
    return default if useDefault else float(argstr)

def stringval(argname, default=None, accepted=None, condition=None):
    """
    Example:
      bayer = argv.stringval("--bayer", default="AUTO", accepted=["AUTO", "GBRG", "RGGB"])
    """
    argstr = _string(argname)
    useDefault = argstr is None
    if not useDefault:
        if not _isValid(argname, argstr, accepted, condition):
            sys.exit(-1)
    return default if useDefault else argstr

def intpair(argname, default=None):
    """
    Example:
      width, height = argv.intpair("--size", default=(1920, 1080))
    """
    if argname in sys.argv:
        argidx = sys.argv.index(argname)
        val1 = int(sys.argv[argidx + 1])
        val2 = int(sys.argv[argidx + 2])
        del sys.argv[argidx:argidx + 3]
        return (val1, val2)
    return default

def floatpair(argname, default=None):
    """
    Example:
      factor1, factor2 = argv.floatpair("--factors", default=(1.0, 1.0))
    """
    if argname in sys.argv:
        argidx = sys.argv.index(argname)
        val1 = float(sys.argv[argidx + 1])
        val2 = float(sys.argv[argidx + 2])
        del sys.argv[argidx:argidx + 3]
        return (val1, val2)
    return default

def floatstring(argname, default=None, accepted=None):
    """
    Examples:
      blacklevel = argv.floatstring("--whitelevel", "AUTO", accepted=["AUTO"])
      whitelevel = argv.floatstring("--blacklevel", 1023.0, accepted=["AUTO"])
    """
    argstr = _string(argname)
    if argstr is not None:
        try:
            result = float(argstr)
            return result
        except ValueError:
            if _isValid(argname, argstr, accepted):
                return argstr
            else:
                sys.exit(-1)
    else:
        return default

def exitIfAnyUnparsedOptions():
    """
    Example:
      factor = argv.floatval("--factor", default=1.0)
      showHelp = argv.exists("--help")
      argv.exitIfAnyUnparsedOptions()
    """
    isOptionArg = ["--" in arg for arg in sys.argv]
    if any(isOptionArg):
        argname = sys.argv[isOptionArg.index(True)]
        print("Unrecognized command-line option: %s"%(argname))
        sys.exit(-1)

######################################################################################
#
#  I N T E R N A L   F U N C T I O N S
#
######################################################################################

def _enforce(expression, errorMessageIfFalse):
    """ If 'expression' is False, prints out the given error message and exits. """
    if not expression:
        print(errorMessageIfFalse)
        sys.exit(-1)

def _string(argname, default=None):
    """ Parses arguments of the form '--argname string', returns the string. """
    if argname in sys.argv:
        argidx = sys.argv.index(argname)
        argstr = sys.argv[argidx + 1]
        del sys.argv[argidx:argidx + 2]
        return argstr
    return default

def _isInt(argstr):
    """ Returns True if and only if the given string represents an integer. """
    try:
        int(argstr, 0)  # hex values must have the "0x" prefix for this to work
        return True
    except (ValueError, TypeError):
        return False

def _isFloat(argstr):
    """ Returns True if and only if the given string represents a float. """
    try:
        float(argstr)
        return True
    except ValueError:
        return False

def _isValid(argname, arg, validArgs=None, condition=None):
    """ Checks that 'arg' is in validArgs and satisfies the given condition. """
    if validArgs is not None:
        if arg not in validArgs:
            print("Invalid value for '%s': '%s' is not in the set %s."%(argname, arg, validArgs))
            return False
    if condition is not None:
        validator = eval("lambda v: %s"%(condition))  # pylint: disable=eval-used
        if validator(arg) is not True:
            print("Invalid value for '%s': '%s' does not satisfy '%s'."%(argname, arg, condition))
            return False
    return True

######################################################################################
#
#  U N I T   T E S T S
#
######################################################################################

class _Tests(unittest.TestCase):

    # pylint: disable=missing-docstring

    def test_exists(self):
        print("Testing argv.exists()...")
        sys.argv = ["argv.py", "--foo"]
        self.assertEqual(exists("--foo"), True)
        self.assertEqual(exists("--foo"), False)
        exitIfAnyUnparsedOptions()

    def test_intval(self):
        print("Testing argv.intval()...")
        sys.argv = ["--foo", "2", "--bar", "4", "--baz", "0xfe"]
        self.assertEqual(intval("--foo"), 2)
        self.assertEqual(intval("--baz"), 254)
        self.assertEqual(intval("--bar", accepted=[3, 4, 5]), 4)
        self.assertEqual(exists("--foo"), False)
        exitIfAnyUnparsedOptions()

    def test_floatval(self):
        print("Testing argv.floatval()...")
        sys.argv = ["--foo", "2", "--bar", "0.3"]
        self.assertEqual(floatval("--foo"), 2.0)
        self.assertEqual(floatval("--bar", condition='v >= 0.2'), 0.3)
        self.assertEqual(exists("--foo"), False)
        exitIfAnyUnparsedOptions()

    def test_stringval(self):
        print("Testing argv.stringval()...")
        sys.argv = ["--foo", "2", "--bar", "baz", "--baz", "foo"]
        self.assertEqual(stringval("--foo"), "2")
        self.assertEqual(stringval("--bar", condition="len(v) > 2"), "baz")
        self.assertEqual(stringval("--baz", accepted=["foo"]), "foo")
        exitIfAnyUnparsedOptions()

    def test_invalid_types(self):
        print("Testing invalid numeric types...")
        sys.argv = ["--foo", "2.0", "--bar", "-5.0", "--foo", "0xfg", "--baz", "-.1e", "--bae"]
        self.assertRaises(SystemExit, lambda: intval("--foo"))
        self.assertRaises(SystemExit, lambda: intval("--bar"))
        self.assertRaises(SystemExit, lambda: intval("--foo"))
        self.assertRaises(SystemExit, lambda: floatval("--baz"))
        self.assertRaises(SystemExit, exitIfAnyUnparsedOptions)

    def test_conditions(self):
        print("Testing invalid numeric values...")
        sys.argv = ["--foo", "2.0", "--bar", "-5.0", "--str1", "baz", "--str2", "foo"]
        self.assertRaises(SystemExit, lambda: floatval("--foo", condition="v > 2.0"))
        self.assertRaises(SystemExit, lambda: floatval("--bar", accepted=[-4.99, -5.01, -5.02]))
        self.assertRaises(SystemExit, lambda: stringval("--str1", accepted=["foo", "bar"]))
        self.assertRaises(SystemExit, lambda: stringval("--str2", condition="len(v) > 4"))
        exitIfAnyUnparsedOptions()

def __main():
    print("--" * 35)
    suite = unittest.TestLoader().loadTestsFromTestCase(_Tests)
    unittest.TextTestRunner(verbosity=0).run(suite)

if __name__ == "__main__":
    __main()
