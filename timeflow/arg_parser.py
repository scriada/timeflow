import argparse
from datetime import datetime as dt
from datetime import timedelta
import os
import subprocess

from timeflow import __version__
from timeflow.helpers import (
    DATE_FORMAT, LOG_FILE,
    get_last_month,
    get_last_week,
    get_month_range,
    get_week_range,
    read_log_file_lines,
    print_stats,
    print_report,
    write_to_log_file,
    print_today_work_time)

from timeflow.log_parser import (
    calculate_report,
    calculate_stats,
)


def log(args):
    write_to_log_file(' '.join(args.message))


def edit(args):
    if args.editor:
        subprocess.call([args.editor, LOG_FILE])
    else:
        editor = os.environ.get('EDITOR')
        if editor in ('vi', 'vim'):  # open the file with the cursor on the last line of the file
            subprocess.call([editor, '+', LOG_FILE])
        elif editor:
            subprocess.call([editor, LOG_FILE])
        else:
            subprocess.call([
                "echo",
                "Set your default editor in EDITOR environment variable or \n"
                "call edit command with -e option and pass your editor, e.g.:\n"
                "timeflow edit -e vim",
            ])


def stats(args):
    today = False
    if args.yesterday:
        yesterday_obj = dt.now() - timedelta(days=1)
        date_from = date_to = yesterday_obj.strftime(DATE_FORMAT)
    elif args.day:
        date_from = date_to = args.day
    elif args.week:
        date_from, date_to = get_week_range(args.week)
    elif args.last_week:
        date_from,  date_to = get_last_week()
    elif args.month:
        date_from,  date_to = get_month_range(args.month)
    elif args.last_month:
        date_from,  date_to = get_last_month()
    elif args._from and not args.to:
        date_from = args._from
        date_to = dt.now().strftime(DATE_FORMAT)
    elif args._from and args.to:
        date_from = args._from
        date_to = args.to
    else:
        # default action is to show today's  stats
        date_from = date_to = dt.now().strftime(DATE_FORMAT)
        today = True

    lines = read_log_file_lines()
    work_time, slack_time, today_work_time = calculate_stats(lines, date_from, date_to, today=today)
    if args.report:
        work_report, slack_report = calculate_report(lines, date_from, date_to)

        print_report(work_report, slack_report, work_time, slack_time, colorize=args.color)
        print_today_work_time(today_work_time)
    else:
        print_stats(work_time, slack_time, today_work_time)
        print_today_work_time(today_work_time)


def set_log_parser(subparser):
    log_parser = subparser.add_parser("log", help="Create timelog message")
    log_parser.add_argument("message", nargs='*', default="", help="message that will be logged")
    # call log() function, when processing log command
    log_parser.set_defaults(func=log)


def set_edit_parser(subparser):
    edit_parser = subparser.add_parser("edit", help="Edit timelog file")
    edit_parser.add_argument("-e", "--editor", help="Explicitly set editor")
    # call edit() function, when processing edit command
    edit_parser.set_defaults(func=edit)


def set_stats_parser(subparser):
    stats_parser = subparser.add_parser("stats", help="Show how much time was spent working or slacking")

    stats_parser.add_argument("--today", action="store_true", help="Show today's work times (default)")
    stats_parser.add_argument("-y", "--yesterday", action="store_true", help="Show yesterday's work times")
    stats_parser.add_argument("-d", "--day", metavar="YYYY-MM-DD", help="Show specific day's work times")

    stats_parser.add_argument("--week", help="Show specific week's work times")
    stats_parser.add_argument("--last-week", action="store_true", help="Show last week's work times")

    stats_parser.add_argument("--month", help="Show specific month's work times")
    stats_parser.add_argument("--last-month", action="store_true", help="Show last month's work times")

    stats_parser.add_argument("-f", "--from", metavar="YYYY-MM-DD", help="Show work times from specific date", dest="_from")
    stats_parser.add_argument("-t", "--to", metavar="YYYY-MM-DD", help="Show work times from to specific date")

    stats_parser.add_argument("-r", "--report", action="store_true", help="Show stats in report form")
    stats_parser.add_argument("-c", "--color", action="store_true", help="Colorize stats report")

    # call stats() function, when processing stats command
    stats_parser.set_defaults(func=stats)


def parse_args(args):
    parser = argparse.ArgumentParser()

    parser.add_argument("-v", "--version",
                        help="Show timeflow's version",
                        action="version",
                        version="timeflow {}".format(__version__))

    subparser = parser.add_subparsers(help="sub-command help")
    set_log_parser(subparser)
    set_edit_parser(subparser)
    set_stats_parser(subparser)

    return parser.parse_args(args)
