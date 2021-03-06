from argparse import ArgumentParser
import logging
import os

from . import __version__
from ._errors import SujsonError
from ._sujson import Sujson
from ._logger import setup_custom_logger

logger = setup_custom_logger("sujson")

parser = ArgumentParser(description="%(prog)s v{}".format(__version__))
parser.add_argument(
    "-f", "--force", action="store_true", help="Force overwrite existing files"
)
parser.add_argument("-d", "--debug", action="store_true", help="Print debugging output")
parser.add_argument("-v", "--verbose", action="store_true", help="Print verbose output")
parser.add_argument(
    "-n",
    "--dry-run",
    action="store_true",
    help="Do not run, only print what would be done",
)
parser.add_argument(
    "--version",
    action="version",
    version="%(prog)s v{}".format(__version__),
    help="Print version and exit",
)
subparsers = parser.add_subparsers(dest="subcommand")


def argument(*name_or_flags, **kwargs):
    """
    Convenience function to properly format arguments to pass to the
    subcommand decorator.
    """
    return list(name_or_flags), kwargs


# https://gist.github.com/mivade/384c2c41c3a29c637cb6c603d4197f9f
def subcommand(_args=[], parent=subparsers):
    """
    Decorator to define a new subcommand in a sanity-preserving way.
    The function will be stored in the ``func`` variable when the parser
    parses arguments so that it can be called directly like so:
        args = parser.parse_args()
        args.func(args)

    Usage example::
        @subcommand([argument("-d", help="Enable debug mode", action="store_true")])
        def subcommand(args):
            print(args)

    Then on the command line::
        $ python parser.py subcommand -d
    """
    def decorator(func):
        _parser = parent.add_parser(func.__name__, description=func.__doc__)
        for arg in _args:
            _parser.add_argument(*arg[0], **arg[1])
        _parser.set_defaults(func=func)

    return decorator


@subcommand(
    [
        argument(
            "input", type=str, help="Input file, currently only .xslx or .csv supported"
        ),
        argument("config", type=str, help="Config file"),
        argument(
            "-o",
            "--output",
            type=str,
            help="Output file, currently only .json supported. If not given, will write to STDOUT.",
        ),
    ]
)
def ingest(_args):
    """
    Read a file with subjective data and store its contents in a *.sujson file
    """
    logger.debug("Ingesting with arguments: {}".format(_args))
    sujson = Sujson(force=_args.force, dry_run=_args.dry_run)

    suffix = os.path.splitext(_args.input)[1]
    # TODO @Qub3k Add import() function to the suJSON class and in this function decide whether to call import_xslx or
    #  import_csv
    if suffix in [".xls", ".xlsx"]:
        sujson.import_xslx(
            _args.input,
            _args.config,
            output_file=_args.output
            # TODO: add other possible arguments here (e.g. those from config)
        )
    elif suffix in [".csv"]:
        sujson.import_csv(
            _args.input,
            _args.config,
            output_file=_args.output
            # TODO: add other possible arguments here (e.g. record separator)
        )
    else:
        raise SujsonError("Unknown input file suffix {}".format(suffix))


@subcommand(
    [
        argument("input", type=str, help="Input suJSON file"),
        argument(
            "-o",
            "--output",
            type=str,
            help="Output file, currently .pickle and .csv supported. Defaults to \"output.pickle\".",
            default="output.pickle"
        ),
        argument(
            "-f", "--format",
            type=str,
            help="In which data format suJSON data is stored in the output file. "
                 "Supported formats include: raw suJSON (suJSON) "
                 "and Pandas DataFrame (Pandas). Defaults to \"suJSON\".",
            default="suJSON")
    ]
)
def export(_cli_args):
    """
    Reads subjective data from a suJSON file and stores the data in a file format of choice
    """
    logger.debug("Ingesting with arguments: {}".format(_cli_args))
    sujson = Sujson(force=_cli_args.force, dry_run=_cli_args.dry_run)

    is_export_successful = sujson.export(_cli_args.input, _cli_args.format, _cli_args.output)

    # Inform the user what is the status of the operation (did it go ok?)
    if is_export_successful:
        logger.info("Export finished with success")
    else:
        logger.error("Exporting failed")


if __name__ == "__main__":
    args = parser.parse_args()
    if args.debug:
        logger.setLevel(logging.DEBUG)
    elif args.verbose:
        logger.setLevel(logging.INFO)
    if args.subcommand is None:
        parser.print_help()
    else:
        args.func(args)
