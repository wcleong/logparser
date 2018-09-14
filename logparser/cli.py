"""Helper methods to set up the CLI"""

import argparse
import sys


def setup_cli(**kwargs):
    """
    Sets up the argparse parser

    Returns:
      argparse.ArgumentParser: parser
    """

    class DefaultHelpParser(argparse.ArgumentParser):
        """Prints help text on error"""

        def error(self, message):
            self.print_help(sys.stderr)
            sys.stderr.write('\n***ERROR*** \n%s\n' % message)
            sys.exit(2)

    parser = DefaultHelpParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter, **kwargs)

    return parser
