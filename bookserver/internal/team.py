# *********************************
# |docname| - team evaluation tools
# *********************************
# This module provides supports for collecting team evaluations and generating reports from those evaluations.
#
# Imports
# =======
# These are listed in the order prescribed by `PEP 8
# <http://www.python.org/dev/peps/pep-0008/#imports>`_.
#
# Standard library
# ----------------
from collections import defaultdict, OrderedDict
import csv
from pathlib import Path
import urllib.parse

# Third-party imports
# -------------------
from gluon import current
from gluon.html import XML, UL, A, DIV, TABLE, THEAD, TBODY, TR

# Local application imports
# -------------------------
from questions_report import questions_to_grades


# Functions
# =========
# Given a CSV file containing a list of teams and the desired course, create two data structures to store team information for the given course only and return these.
def _load_teams(course_name):
    # Type: Dict[user_id: str, team_name: str]
    # This only supports one team per user_id and course_name.
    team_member = dict()
    # Type: Dict[team_name: str, OrderedDict[user_id: str, name: str]]
    team = defaultdict(OrderedDict)
    with open(
        str(
            Path(
                current.request.folder,
                "books",
                current.get_course_row().base_course,
                course_name + ".csv",
            )
        ),
        "r",
        encoding="utf-8",
    ) as csv_file:
        is_first_row = True
        for row in csv.reader(csv_file):
            # Ignore blank rows
            if len(row) == 0:
                continue
            assert len(row) == 3, 'Incorrect number of rows in "{}".'.format(
                ",".join(row)
            )
            user_id, user_name, team_name = row
            # Ignore rows with no data
            if (
                not is_first_row
                and user_id == ""
                and user_name == ""
                and team_name == ""
            ):
                continue
            if is_first_row:
                is_first_row = False
                assert (
                    user_id == "user id"
                ), 'Expected the first column of the first row to be "user id" instead of  "{}".'.format(
                    user_id
                )
                assert (
                    user_name == "user name"
                ), 'Expected the second column of the first row to be "user name" instead of "{}".'.format(
                    user_name
                )
                assert (
                    team_name == "team name"
                ), 'Expected the third column of the first row to be "team name" instead of "{}".'.format(
                    team_name
                )
            else:
                # Add this user to the team.
                assert user_id not in team_member, "Duplicate user ID {}.".format(
                    user_id
                )
                team_member[user_id] = team_name
                assert (
                    user_id not in team[team_name]
                ), "Duplicate user ID {} in team {}.".format(user_id, team_name)
                team[team_name][user_id] = user_name

    return team, team_member


# This returns the team name for the given ``user_id`` and a list of team members/user IDs of the given ``user_id``.
def _get_team_members(user_id, team, team_member, is_list_of_names=True):
    # Identify the team of the given user.
    assert user_id in team_member, "User ID {} not in list of team members.".format(
        user_id
    )
    team_name = team_member[user_id]
    assert team_name in team, "Team {} of user ID {} not in list of teams.".format(
        team_name, user_id
    )
    this_team = team[team_name]

    # Extract only teammates of this user.
    teammate_member_list = [
        team_member_name if is_list_of_names else team_member_user_id
        for team_member_user_id, team_member_name in this_team.items()
        if team_member_user_id != user_id
    ]

    return team_name, teammate_member_list


# Convert any exceptions into an error message, so the view can complete.
def get_team_members(user_id, course_name):
    try:
        team, team_member_list = _load_teams(course_name)
        return _get_team_members(user_id, team, team_member_list)
    except Exception as e:
        return "Error: {}".format(e), ["Error"]


# Team reports
# ============
# Transform data from a team evaluation into a report.
#
# Globals
# -------
NO_DATA = "No data"


# EvalData
# --------
# A class to hold data about each evaluation. Attributes containing tuples are indexed by ``teammate_netids``. TODO: these are actually teammate e-mail addresses. Update this!
#
# - name: str
# - teammate_netids: (netid0, ...)
class EvalData:
    def __init__(self, name, teammate_netids):
        self.name = name
        self.teammate_netids = teammate_netids

    def __repr__(self):
        return "<team.EvalData instance, name={}, teammate_netids={}".format(
            repr(self.name), repr(self.teammate_netids)
        )


# TeamData
# --------
# A class to collect data about each team. Tuples are indexed by team_netids.
class TeamData:
    def __init__(self, grades, eval_data_dict, team_netids):
        self.grades = grades
        self.eval_data_dict = eval_data_dict
        self.team_netids = team_netids
        self.collected_response = set()

    def __repr__(self):
        return "<team.TeamData instance, team_netids={}>".format(repr(self.team_netids))

    # Given a key and one or move div_ids, store data in ``eval_data_dict`` using that key.
    def collect_responses(self, key, *args, **kwargs):
        average = kwargs.get("average", False)

        # If we've already done the work, simply return the key from last time.
        if args not in self.collected_response:
            self.collected_response.add(args)

            # Walk through all grades with these div_ids and put them in eval_data.
            for user_id, div_id_dict in self.grades.items():
                # Ignore info about each user.
                if user_id is None:
                    continue
                responses = []
                for arg in args:
                    # Get this user's response (index 2) for the provided div_id.
                    response = div_id_dict.get(arg, [None] * 3)[2]
                    # Fill-in-the-blank questions return a list; others don't. Convert non-lists into a single-element list, then add all list elements. This supports multi-blank fitb questions.
                    responses.extend(
                        response if isinstance(response, list) else [response]
                    )
                # Transform the user_id into an e-mail, which is how eval_data_dict is addressed.
                email = self.grades[user_id][None].email
                # Process only students in the team list.
                if email in self.eval_data_dict:
                    # Discard responses for undefined team members.
                    responses = responses[
                        : len(self.eval_data_dict[email].teammate_netids)
                    ]
                    # Normalize data to be averaged.
                    if average:
                        responses = _normalize_grades(responses)
                    setattr(self.eval_data_dict[email], key, responses)

        return key

    # Produce a list of the eval_data.key for all team members.
    def list_(self, *args):
        key = self.collect_responses(*args)
        names = [
            getattr(self.eval_data_dict[x], key, NO_DATA) for x in self.team_netids
        ]
        return UL(*[name for name in names])

    # Produce a table of eval_data.name, eval_data.key for all team members.
    def table(self, *args):
        key = self.collect_responses(*args)
        html_table = HtmlTableMaker()
        for x in self.team_netids:
            html_table.add_data(
                self.eval_data_dict[x].name,
                *getattr(self.eval_data_dict[x], key, [NO_DATA])
            )
        return html_table.to_html()

    # Produce a table of eval_data.key for each member about each team member.
    def grid(self, *args, **kwargs):
        average = kwargs.get("average", False)
        key = self.collect_responses(*args, **kwargs)
        html_table = HtmlTableMaker()
        # Print a title of names of each team member
        html_table.add_header(
            XML("Evaluator→<br />↓Evaluatee↓"),
            *(
                [self.eval_data_dict[x].name for x in self.team_netids]
                + (["Average", "Delta"] if average else [])
            )
        )

        # Produce each row of the table.
        for x in self.team_netids:
            # Look up the values that team member x reported about team member y.
            vals = [self.teammate(y, x, key) for y in self.team_netids]
            if average:
                good_vals = [val for val in vals if _isfloat(val)]
                if not good_vals:
                    # If no other team members provided an evaluation, and this is the average evaluation for the one person on the team who provided data, provide a placeholder.
                    vals.append(NO_DATA)
                else:
                    vals.append(sum(good_vals) / (len(good_vals)))
                # Save the average for this user.
                setattr(self.eval_data_dict[x], key + "_average", vals[-1])
                # Save this normalized delta. This is :math:`\frac{actual - expected}{expected} \cdot 100 = \left( \frac{actual}{expected} - 1 \right) \cdot 100`, where ``actual = vals[-1]``, :math:`expected = \frac{1}{\# teammates - 1} \cdot 100`, and ``#teammates = len(self.teammates)``.
                delta = (
                    NO_DATA
                    if vals[-1] == NO_DATA
                    else (
                        vals[-1] / (1.0 / (len(self.team_netids) - 1.0) * 100.0) - 1.0
                    )
                    * 100.0
                )
                setattr(self.eval_data_dict[x], key + "_delta", delta)
                vals.append(delta)
                # Format nicely.
                vals = ["{:.1f}%".format(val) if _isfloat(val) else val for val in vals]
            html_table.add_data(self.eval_data_dict[x].name, *vals)
        return html_table.to_html()

    # Look up the value in key that netid reported about teammate_netid.
    def teammate(self, netid, teammate_netid, key):
        # There are no self-evaluations.
        if netid == teammate_netid:
            return ""
        # If students don't submit an evaluation, return NO_DATA.
        eval_data = self.eval_data_dict[netid]
        try:
            index = eval_data.teammate_netids.index(teammate_netid)
            return getattr(eval_data, key)[index]
        except (ValueError, IndexError, AttributeError):
            return NO_DATA


def grades_table(team_data_dict, *args):
    html_table = HtmlTableMaker()
    eval_data_attr_list = ["name"]
    for arg in args:
        eval_data_attr_list += [arg + "_average", arg + "_delta"]
    html_table.add_header("e-mail", "team", *eval_data_attr_list)
    # Sort this by team, then by last name, first name. Easy -- this is the order that team_data_dict is already in!
    for team_name, team_data in team_data_dict.items():
        eval_data_dict = team_data.eval_data_dict
        for email in team_data.team_netids:
            vals = [
                getattr(eval_data_dict[email], eval_data_attr, NO_DATA)
                for eval_data_attr in eval_data_attr_list
            ]
            html_table.add_data(
                email,
                team_name,
                *["{:.1f}%".format(val) if _isfloat(val) else val for val in vals]
            )
    return html_table.to_html()


# A class to generate simple HTML tables.
class HtmlTableMaker(object):
    def __init__(self):
        self.head = []
        self.body = []

    def add_header(self, *args):
        self.head.append(args)

    def add_data(self, *args):
        self.body.append(args)

    def to_html(self):
        args = []
        if self.head:
            args.append(THEAD(*[TR(*rows) for rows in self.head]))
        args.append(TBODY(*[TR(*rows) for rows in self.body]))
        return TABLE(*args, _class="table", _style="white-space: pre-wrap;")


# team_report
# -----------
# Build the data structures needed to produce a team report.
def team_report(
    # The subchapter name containing the evaluation. Simply remove ``.rst`` from the filename -- ``team_evaluation_1.rst`` has a subchapter_name of ``team_evaluation_1``.
    subchapter_name,
    # The course name.
    course_name,
    # The string "true" if the current user is an instructor; otherwise, the string "false".
    is_instructor_str,
    # True to write out a table of contents.
    write_toc=True,
):

    if is_instructor_str != "true":
        return {}, {}, None, "You must be an instructor to access this page."

    team, team_member = _load_teams(course_name)
    # TODO
    grades = questions_to_grades(
        course_name,
        (db.questions.chapter == current.request.args[-2])
        # TODO: Use something like request.args[-1][:-5] (this takes the ``.html`` extension off the subchapter name), but renamed for the eval document, not this document. Or include the report at the bottom of the eval?)
        & (db.questions.subchapter == subchapter_name)
        & (db.questions.base_course == current.get_course_row().base_course),
    )

    # Type: Dict[net_id: str, eval_data: EvalData].
    eval_data_dict = {
        user_id: EvalData(
            team[team_name][user_id],
            _get_team_members(user_id, team, team_member, False)[1],
        )
        for user_id, team_name in team_member.items()
    }
    # Type: OrderedDict[team_name: str, team_data: TeamData].
    # The dict is sorted by team name.
    team_data_dict = OrderedDict()
    for team_name in sorted(team.keys()):
        # Create the struct [[netid, first_name, last_name], ...]
        ##                     [0]      [1]         [2]
        team_struct = [
            [userid] + name.split(None, 1) for userid, name in team[team_name].items()
        ]
        team_data_dict[team_name] = TeamData(
            grades,
            eval_data_dict,
            # Sort it by last name then first name.
            [
                x[0]
                for x in sorted(
                    team_struct,
                    key=lambda x: (x[2], x[1]) if len(x) >= 3 else (x[1], ""),
                )
            ],
        )

    # Write a TOC
    toc_str = UL(
        *[
            A(team_name, _href="#" + urllib.parse.quote(team_name))
            for team_name, team_data in team_data_dict.items()
        ]
    ) if write_toc else ""

    return eval_data_dict, team_data_dict, grades, toc_str


# Utilities
# =========
def _isfloat(val):
    return isinstance(val, float)


def _maybe_to_float(_str):
    try:
        return float(_str)
    except Exception:
        return _str


# Normalize student grades.
def _normalize_grades(grades_str):
    # Convert the grades to floats where possible.
    grades = [_maybe_to_float(grade_str) for grade_str in grades_str]
    # Sum the floats.
    grades_sum = sum([grade for grade in grades if _isfloat(grade)])
    # Return a normalized value for floats, or the string
    return [
        grade / grades_sum * 100
        if _isfloat(grade) and grades_sum != 0
        else '{} from "{}"'.format(NO_DATA, grade)
        for grade in grades
    ]


# Make a list of sequentially numbered strings. For example, ``str_array('foo', 3)`` produces ``['foo0', 'foo1', 'foo2']``.
def str_array(
    # The string prefix for the array.
    prefix_str,
    # These parameters are passed to `range <https://docs.python.org/3/library/stdtypes.html#range>`_, and each resulting value appended to the ``prefix_str``.
    *range_args
):
    return [prefix_str + str(index) for index in range(*range_args)]


# Insert an anchor which the table of contents refers to.
def toc_anchor(team_name):
    return DIV("", _id=urllib.parse.quote(team_name))
