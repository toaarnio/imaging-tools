#!/usr/bin/env -S python3 -B

"""
A collection of simple command-line parsing & config file handling functions.

Copyright (c) 2018 Tomi Aarnio. MIT License.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import os                         # standard library
import sys                        # standard library
import re                         # standard library # pylint: disable=unused-import # noqa
import glob                       # standard library
import unittest                   # standard library
import toml                       # pip install toml
import mergedeep                  # pip install mergedeep
import dotwiz                     # pip install dotwiz

# pylint: disable=invalid-name


######################################################################################
#
#  C O N F I G   F I L E   H A N D L I N G
#
######################################################################################


class Config(dotwiz.DotWiz):
    """
    Dictionary-like storage for config options, with support for TOML config files
    and convenient merging.

    Example:
      defaults = Config()
      defaults.foo = "bar"
      defaults.items = ["foo", "bar"]
      args = Config()
      args.items = argv.stringval("--items", repeats=True)
      config = defaults.merge(args)  # 'args' takes precedence
    """
    @classmethod
    def load(cls, filename):
        """
        Create a new Config instance and populate it from the given TOML file.
        """
        if os.path.isfile(filename):
            with open(filename, "r") as f:
                loaded = toml.load(f)
                instance = cls(**loaded)
                return instance
        else:
            print(f"Config file '{filename}' does not exist. Terminating.")
            sys.exit(-1)

    def merge(self, other):
        """
        Merge this config with the given config. In case of conflicting keys, the other
        config takes priority.

        Arguments:
          - other: dictionary to merge with self

        Returns:
          - copy of self with the contents of 'other' merged in
        """
        merged = mergedeep.merge({}, self, other, strategy=mergedeep.Strategy.REPLACE)
        merged = self.__class__(**merged)
        return merged

    def cleanup(self):
        """
        Iterate over dictionary items and drop those that are empty or None.

        Returns:
          - cleaned-up copy of self
        """
        cleaned = {}
        for key, value in self.items():
            if value == [] or value == set() or value is None:
                continue
            cleaned[key] = value
        cleaned = self.__class__(**cleaned)
        return cleaned


######################################################################################
#
#  C O M M A N D - L I N E   P A R S I N G
#
######################################################################################


def filenames(patterns, extensions=None, sort=False, allowAllCaps=False, numRequired=0):
    """
    Examples:
      filenames, basenames = argv.filenames(sys.argv[1:], numRequired=2)
      filenames, basenames = argv.filenames(sys.argv[1:], [".ppm", ".png"], sort=True)
      filenames, basenames = argv.filenames(sys.argv[1:], [".jpg"], allowAllCaps=True)
    """
    fullnames = [glob.glob(filepattern, recursive=True) for filepattern in patterns]  # expand wildcards
    fullnames = [item for sublist in fullnames for item in sublist]                 # flatten nested lists
    fullnames = [f for f in fullnames if os.path.isfile(f)]                         # check file existence
    if extensions is not None:
        extensions += [e.upper() for e in extensions] if allowAllCaps else []       # jpg => [jpg, JPG]
        fullnames = [f for f in fullnames if os.path.splitext(f)[1] in extensions]  # filter by extension
    fullnames = sorted(fullnames) if sort else fullnames                            # sort if requested
    basenames = [os.path.splitext(f)[0] for f in fullnames]                         # strip extensions
    errmsg = f"Found {len(fullnames)} matching files, {numRequired} required."      # check file count
    _enforce(len(fullnames) >= numRequired, errmsg)
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


def intval(argname, default=None, accepted=None, condition=None, repeats=False):
    """
    Example:
      numtiles = argv.intval("--split", 1, [1, 2, 3, 4])
    """
    if not repeats:  # pylint: disable=no-else-return
        argstr = _string(argname)
        useDefault = argstr is None
        if not useDefault:
            errmsg = f"Invalid value for '{argname}': '{argstr}' does not represent an integer."
            _enforce(_isInt(argstr), errmsg)
            argval = int(argstr, 0)  # hex values must have the "0x" prefix for this to work
            if not _isValid(argname, argval, accepted, condition):
                sys.exit(-1)
        return default if useDefault else argval
    else:
        argSet = set()
        argstr = _string(argname)
        while argstr is not None:
            errmsg = f"Invalid value for '{argname}': '{argstr}' does not represent an integer."
            _enforce(_isInt(argstr), errmsg)
            argval = int(argstr, 0)  # hex values must have the "0x" prefix for this to work
            if not _isValid(argname, argval, accepted, condition):
                sys.exit(-1)
            argSet |= {argval}
            argstr = _string(argname)
        if not argSet and default is not None:
            argSet = {default}
        return argSet


def floatval(argname, default=None, accepted=None, condition=None, repeats=False):
    """
    Example:
      factor = argv.floatval("--factor", 1.0, condition='1.0 <= v <= 3.0')
    """
    if not repeats:
        argstr = _string(argname)
        useDefault = argstr is None
        if not useDefault:
            errmsg = f"Invalid value for '{argname}': '{argstr}' does not represent a number."
            _enforce(_isFloat(argstr), errmsg)
            if not _isValid(argname, float(argstr), accepted, condition):
                sys.exit(-1)
        return default if useDefault else float(argstr)
    else:
        argSet = set()
        argstr = _string(argname)
        while argstr is not None:
            errmsg = f"Invalid value for '{argname}': '{argstr}' does not represent a number."
            _enforce(_isFloat(argstr), errmsg)
            argval = float(argstr)
            if not _isValid(argname, argval, accepted, condition):
                sys.exit(-1)
            argSet |= {argval}
            argstr = _string(argname)
        if not argSet and default is not None:
            argSet = {default}
        return argSet


def stringval(argname, default=None, accepted=None, condition=None, repeats=False):
    """
    Examples:
      bayer = argv.stringval("--bayer", default="AUTO", accepted=["AUTO", "GBRG", "RGGB"])
      sources = argv.stringval("--source", default="all", accepted=["foo", "bar", "baz", "all"], repeats=True)
    """
    if not repeats:  # pylint: disable=no-else-return
        argstr = _string(argname)
        useDefault = argstr is None
        if not useDefault:
            if not _isValid(argname, argstr, accepted, condition):
                sys.exit(-1)
        return default if useDefault else argstr
    else:
        argSet = set()
        argstr = _string(argname)
        while argstr is not None:
            if not _isValid(argname, argstr, accepted, condition):
                sys.exit(-1)
            argSet |= {argstr}
            argstr = _string(argname)
        if not argSet and default is not None:
            argSet = {default}
        return argSet


def intpair(argname, default=None, repeats=False):
    """
    Examples:
      width, height = argv.intpair("--size", default=(1920, 1080))
      limits = argv.intpair("--limits", default=(0, 1), repeats=True)
    """
    if not repeats:
        pair = _intpair(argname)
        pair = default if pair is None else pair
        return pair
    else:
        pairSet = set()
        pair = _intpair(argname)
        while pair is not None:
            pairSet |= set([pair])
            pair = _intpair(argname)
        if not pairSet and default is not None:
            pairSet = {default}
        return pairSet


def floatpair(argname, default=None):
    """
    Example:
      factor1, factor2 = argv.floatpair("--factors", default=(1.0, 1.0))
    """
    if argname in sys.argv:
        argidx = sys.argv.index(argname)
        if len(sys.argv) >= argidx + 3:
            val1 = sys.argv[argidx + 1]
            val2 = sys.argv[argidx + 2]
            del sys.argv[argidx:argidx + 3]
            _enforce(_isFloat(val1), f"Invalid value for '{argname}': '{val1}' does not represent a decimal number")
            _enforce(_isFloat(val2), f"Invalid value for '{argname}': '{val2}' does not represent a decimal number.")
            val1 = float(val1)
            val2 = float(val2)
            return [val1, val2]
        print(f"Missing value(s) for '{argname}': Expected a pair of decimal numbers.")
        sys.exit(-1)
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
    isOptionArg = [arg.startswith("-") for arg in sys.argv]
    if any(isOptionArg):
        argname = sys.argv[isOptionArg.index(True)]
        print(f"Unrecognized command-line option: {argname}")
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
        if len(sys.argv) >= argidx + 2:
            argstr = sys.argv[argidx + 1]
            del sys.argv[argidx:argidx + 2]
            return argstr
        else:
            return ""
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
            print(f"Invalid value for '{argname}': '{arg}' is not in the set {validArgs}.")
            return False
    if condition is not None:
        validator = eval(f"lambda v: {condition}")  # pylint: disable=eval-used
        if validator(arg) is not True:
            print(f"Invalid value for '{argname}': '{arg}' does not satisfy '{condition}'.")
            return False
    return True


def _intpair(argname):
    if argname in sys.argv:
        argidx = sys.argv.index(argname)
        if len(sys.argv) >= argidx + 3:
            val1 = sys.argv[argidx + 1]
            val2 = sys.argv[argidx + 2]
            del sys.argv[argidx:argidx + 3]
            _enforce(_isInt(val1), f"Invalid value for '{argname}': '{val1}' does not represent an integer.")
            _enforce(_isInt(val2), f"Invalid value for '{argname}': '{val2}' does not represent an integer.")
            val1 = int(val1)
            val2 = int(val2)
            return (val1, val2)
        print(f"Missing value(s) for '{argname}': Expected a pair of integers.")
        sys.exit(-1)
    return None


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
        self.assertEqual(intval("--nonexisting", repeats=True), set())
        self.assertEqual(intval("--nonexisting", default=3, repeats=True), {3})
        exitIfAnyUnparsedOptions()

    def test_floatval(self):
        print("Testing argv.floatval()...")
        sys.argv = ["--foo", "2", "--bar", "0.3"]
        self.assertEqual(floatval("--foo"), 2.0)
        self.assertEqual(floatval("--bar", condition='v >= 0.2'), 0.3)
        self.assertEqual(exists("--foo"), False)
        self.assertEqual(floatval("--nonexisting", repeats=True), set())
        self.assertEqual(floatval("--nonexisting", default=3.141, repeats=True), {3.141})
        exitIfAnyUnparsedOptions()

    def test_stringval(self):
        print("Testing argv.stringval()...")
        sys.argv = ["--foo", "2", "--bar", "baz", "--baz", "foo"]
        self.assertEqual(stringval("--foo"), "2")
        self.assertEqual(stringval("--bar", condition="len(v) > 2"), "baz")
        self.assertEqual(stringval("--baz", accepted=["foo"]), "foo")
        exitIfAnyUnparsedOptions()

    def test_stringval_repeat(self):
        print("Testing argv.stringval(repeats=True)...")
        sys.argv = ["--repeated", "foo", "--repeated", "bar", "--repeated", "baz"]
        self.assertEqual(stringval("--repeated", repeats=True), set(("foo", "bar", "baz")))
        self.assertEqual(stringval("--nonexisting", repeats=True), set())
        self.assertEqual(stringval("--nonexisting", default="foo", repeats=True), {"foo"})
        exitIfAnyUnparsedOptions()

    def test_intpair(self):
        print("Testing argv.intpair()...")
        sys.argv = ["--foo", "-1", "1"]
        self.assertEqual(intpair("--foo"), (-1, 1))
        self.assertEqual(intpair("--foo", default=(0, 2)), (0, 2))
        sys.argv = ["--repeated", "-1", "1", "--repeated", "10", "20"]
        self.assertEqual(intpair("--repeated", repeats=True), set([(-1, 1), (10, 20)]))
        self.assertEqual(intpair("--repeated", default=(2, 1), repeats=True), set([(2, 1)]))
        self.assertEqual(intpair("--nonexisting", repeats=True), set())
        self.assertEqual(intpair("--nonexisting", default=(2, 3), repeats=True), {(2, 3)})

    def test_floatpair(self):
        print("Testing argv.floatpair()...")
        sys.argv = ["--foo", "-1.2", "2.1"]
        self.assertEqual(floatpair("--foo"), [-1.2, 2.1])
        self.assertEqual(intpair("--foo", default=[0.1, -1.5]), [0.1, -1.5])

    def test_missing_values(self):
        print("Testing missing argument values...")
        sys.argv = ["--foo", "3"]
        self.assertRaises(SystemExit, lambda: intpair("--foo"))
        sys.argv = ["--foo", "3.0"]
        self.assertRaises(SystemExit, lambda: floatpair("--foo"))
        sys.argv = ["--foo", "3.1", "3.2"]
        self.assertRaises(SystemExit, lambda: intpair("--foo"))
        sys.argv = ["--foo", "2", "2.1"]
        self.assertRaises(SystemExit, lambda: intpair("--foo"))
        sys.argv = ["--foo"]
        self.assertRaises(SystemExit, lambda: stringval("--foo", accepted=["bar"]))

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

    def test_config(self):
        print("Testing argv.Config...")
        config = Config()
        config.foo = "bar"
        config.bar = ["baz", "bae"]
        config.empty = []
        config2 = Config(bar=["foo"])
        merged = config.merge(config2)
        self.assertEqual(merged.foo, "bar")
        self.assertEqual(merged.bar, ["foo"])
        self.assertEqual(config.bar, ["baz", "bae"])
        self.assertEqual(config2.bar, ["foo"])
        self.assertTrue("empty" not in config.cleanup())


def __main():
    print("--" * 35)
    suite = unittest.TestLoader().loadTestsFromTestCase(_Tests)
    unittest.TextTestRunner(verbosity=0).run(suite)


if __name__ == "__main__":
    __main()
