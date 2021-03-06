from collections import defaultdict
import re

from datetime import datetime as dt

from timeflow.helpers import (
    DATETIME_FORMAT,
    date_begins,
    date_ends,
    read_log_file_lines,
)


class Line():
    __slots__ = ['date', 'time', 'project', 'log', 'is_slack']

    def __init__(self, date, time, project, log, is_slack):
        self.date = date
        self.time = time
        self.project = project
        self.log = log
        self.is_slack = is_slack


def clean_line(time, project, log):
    "Cleans line data from unnecessary chars"
    # project and log can have new line char at the end, remove it
    if project and project[-1] == '\n':
        project = project[:-1]

    if log and log[-1] == '\n':
        log = log[:-1]

    return time, project, log


def parse_message(message):
    "Parses message as log can be empty"
    parsed_message = message.split(': ', 1)

    # if parsed message has only log stated, then the default project of Other is used
    if len(parsed_message) == 1:  # No colon found so either only a project has been put down or only a log
        split_message = parsed_message[0].split(None, 1)
        if len(split_message) == 1:
            project, log = parsed_message[0], ''
        elif parsed_message[0].lower().startswith('eq-'):
            project, log = split_message
        else:
            project, log = 'Other', parsed_message[0]
    else:
        project, log = parsed_message

    return project, log


def find_slack(project, log):
    if project.endswith("**") or log.endswith("**"):
        return True
    return False


def strip_log(string):
    "Strips string from slack marks and leading/trailing spaces"
    return string.strip().rstrip('**')


def parse_line(line):
    """Parses log line into logical units: time, project and message

    Log line looks like this:
    [date]_[time]_[project]:_[log message]
    """
    # get date time and the rest of a message
    split = line.strip().split(None, 2)
    if len(split) == 3:
        date, time, message = split
    else:
        message = ''
        date, time = split

    project, log = parse_message(message)
    time, project, log = clean_line(time, project, log)
    is_slack = find_slack(project, log)

    return Line(date, time, project, log, is_slack)


def parse_lines():
    """Returns a list of objects representing log file"""
    lines = read_log_file_lines()
    data = []
    for line in lines:
        data.append(parse_line(line))
    return data


def calc_time_diff(line, next_line):
    line_time = dt.strptime(
        "{} {}".format(line.date, line.time),
        DATETIME_FORMAT
    )
    next_line_time = dt.strptime(
        "{} {}".format(next_line.date, next_line.time),
        DATETIME_FORMAT
    )
    return (next_line_time - line_time).seconds


def calculate_stats(lines, date_from, date_to, today=False):
    work_time = []
    slack_time = []
    today_work_time = None

    line_begins = date_begins(lines, date_from)
    line_ends = date_ends(lines, date_to)

    date_not_found = (line_begins is None or line_ends < line_begins)
    if date_not_found:
        return work_time, slack_time, today_work_time

    data = parse_lines()

    for i, line in enumerate(data[line_begins:line_ends+1]):
        # if we got to the last line - stop
        if line_begins+i+1 > line_ends:
            break

        next_line = data[line_begins+i+1]

        line_date = line.date
        next_line_date = next_line.date

        # if it's day switch, skip this cycle
        if line_date != next_line_date:
            continue

        if next_line.is_slack:
            slack_time.append(calc_time_diff(line, next_line))
        else:
            work_time.append(calc_time_diff(line, next_line))

    if today:
        today_start_time = dt.strptime(
            "{} {}".format(data[line_begins].date, data[line_begins].time),
            DATETIME_FORMAT
        )
        today_work_time = (dt.now() - today_start_time).seconds

    return work_time, slack_time, today_work_time


def calculate_report(lines, date_from, date_to):
    """Creates and returns report dictionaries

    Report dicts have form like this:
    {<Project>: {<log_message>: <accumulative time>},
                {<log_message1>: <accumulative time1>}}
    """
    work_dict = defaultdict(lambda: defaultdict(dict))
    slack_dict = defaultdict(lambda: defaultdict(dict))

    line_begins = date_begins(lines, date_from)
    line_ends = date_ends(lines, date_to)

    date_not_found = (line_begins is None or line_ends < line_begins)
    if date_not_found:
        return work_dict, slack_dict

    data = parse_lines()

    for i, line in enumerate(data[line_begins:line_ends+1]):
        # if we got to the last line - stop
        if line_begins+i+1 > line_ends:
            break

        next_line = data[line_begins+i+1]

        line_date = line.date
        next_line_date = next_line.date
        # if it's day switch, skip this cycle
        if line_date != next_line_date:
            continue

        time_diff = calc_time_diff(line, next_line)

        project = strip_log(next_line.project)
        log = strip_log(next_line.log)
        if next_line.is_slack:
            # if log message is identical add time_diff
            # to total time of the log
            if slack_dict[project][log]:
                total_time = slack_dict[project][log]
                total_time += time_diff
                slack_dict[project][log] = total_time
            else:
                slack_dict[project][log] = time_diff
        else:
            if work_dict[project][log]:
                total_time = work_dict[project][log]
                total_time += time_diff
                work_dict[project][log] = total_time
            else:
                work_dict[project][log] = time_diff

    return work_dict, slack_dict
