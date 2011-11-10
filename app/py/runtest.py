#!/usr/bin/python
#
# This script is based on http://code.google.com/appengine/docs/python/tools/localunittesting.html
#
import optparse
import sys
import unittest
import os.path

USAGE = """%prog SDK_PATH
Run unit tests for App Engine apps.

SDK_PATH    Path to the SDK installation"""


def main(sdk_path):
    sys.path.insert(0, sdk_path)
    import dev_appserver
    dev_appserver.fix_sys_path()
    suite = unittest.loader.TestLoader().discover(os.path.dirname(__file__), pattern="*_test.py")
    unittest.TextTestRunner(verbosity=2).run(suite)


if __name__ == '__main__':
    parser = optparse.OptionParser(USAGE)
    options, args = parser.parse_args()
    if len(args) != 1:
        print 'Error: Exactly 1 arguments required.'
        parser.print_help()
        sys.exit(1)
    SDK_PATH = args[0]
    main(SDK_PATH)

