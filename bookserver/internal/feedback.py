# ************************************************
# |docname| - Provide feedback for student answers
# ************************************************
#
# Imports
# =======
# These are listed in the order prescribed by `PEP 8
# <http://www.python.org/dev/peps/pep-0008/#imports>`_.
#
# Standard library
# ----------------
from functools import lru_cache
import json
import os
from pathlib import Path
import tempfile
from typing import Any, Dict

# Third-party imports
# -------------------
import js2py
from runestone.lp.lp_common_lib import (
    STUDENT_SOURCE_PATH,
    code_here_comment,
    read_sphinx_config,
)

# Local imports
# -------------
from ..models import runestone_component_dict
from .scheduled_builder import _scheduled_builder
from ..config import settings


# Code
# ====
# _`init_graders`: Install all the graders. While I'd prefer to include this functionality in `register_answer_table <register_answer_table>`, doing so would create a cycle of imports: the feedback functions below require an import of the models, while the models would require an import of these functions. So,
def init_graders():
    for table_name, grader in (
        ("fitb_answers", fitb_feedback),
        ("lp_answers", lp_feedback),
    ):
        runestone_component_dict[table_name].grader = grader


# Provide test code a way to send random numbers. See `RAND_FUNC <RAND_FUNC>`. To do so, read from the file. Return 0 as a "random" value if we can't read from the file (or even open it).
class TestFileValues:
    def __init__(self):
        self.values = []
        self.index = 0
        self.test_file_path = Path(settings._book_server_path / "../test/rand.txt")
        self.stat = None

    def get_value(self):
        # If the file changed, re-read values from it.
        try:
            stat = self.test_file_path.stat()
        except Exception:
            pass
        else:
            if stat != self.stat:
                self._read_test_file()

        # If we have values from a previous read of the file, return them.
        if self.index < len(self.values):
            self.index += 1
            return self.values[self.index - 1]

        # Re-use these values if possible.
        if len(self.values):
            self.index = 1
            return self.values[0]

        # Otherwise, return a "random" value of 0.
        return 0

    # Read the test file.
    def _read_test_file(self):
        try:
            with open(self.test_file_path) as f:
                lines = f.readlines()
            self.values = [float(v) for v in lines]
            self.index = 0
            self.stat = self.test_file_path.stat()
        except Exception:
            pass


# Make this global so its state remains between calls to ``get_js_context``.
test_file_values = TestFileValues()


# Load the JavaScript context needed for dynamic problems. Cache the results to make grading multiple problems faster.
@lru_cache(maxsize=16)
def get_js_context(book_path: Path):
    # By default, Babel assigns to ``exports`` before defining it. This is fine in the browser, but makes js2py choke. Pre-define it. Also, provide a way for tests to inject pre-defined "random" numbers.
    context = js2py.EvalJs(dict(exports={}, rs_test_rand=test_file_values.get_value))

    # These functions don't exist in ES5.1, but FITB code uses them. Here are simple polyfills. See `MDN's Object.entries polyfill <https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Object/entries#polyfill>`_, `MDN Object.assign polyfill <https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Object/assign#polyfill>`_. Note: ``Object.assign`` and ``console.log`` does exist in ES5.1, but js2py doesn't implement it.
    context.execute(
        """
        console.assert = function(test, arg) {
            if (test) {
                console.log(arg);
            }
        }

        // ES5 doesn't support binary numbers starting with ``0b``, so write a polyfill. Js2py doesn't allow me to override the built-in Number class, so use another name.
        Number_ = function(n) {
            if (typeof n === "string" && n.trim().slice(0, 2).toLowerCase() === "0b") {
                return parseInt(n.trim().slice(2), 2);
            }
            return Number(n);
        }

        // Must be writable: true, enumerable: false, configurable: true
        Object.defineProperty(Object, "assign", {
            value: function assign(target, varArgs) { // .length of function is 2
                'use strict';
                if (target === null || target === undefined) {
                    throw new TypeError('Cannot convert undefined or null to object');
                }

                var to = Object(target);

                for (var index = 1; index < arguments.length; index++) {
                    var nextSource = arguments[index];

                    if (nextSource !== null && nextSource !== undefined) {
                        for (var nextKey in nextSource) {
                            // Avoid bugs when hasOwnProperty is shadowed
                            if (Object.prototype.hasOwnProperty.call(nextSource, nextKey)) {
                                to[nextKey] = nextSource[nextKey];
                            }
                        }
                    }
                }
                return to;
            },
            writable: true,
            configurable: true
        });

        Object.entries = function( obj ) {
            var ownProps = Object.keys( obj ),
                i = ownProps.length,
                resArray = new Array(i); // preallocate the Array
            while (i--)
                resArray[i] = [ownProps[i], obj[ownProps[i]]];

            return resArray;
        };

        Object.values = function (obj) {
            return Object.keys(obj).map(function (e) {
                return obj[e];
            });
        };

        Math.imul = function(a, b) {
            return (a*b)&0xFFFFFFFF;
        }
    """
    )

    # Load in the server-side code.
    with open(book_path / "_static/server_side.js", encoding="utf-8") as f:
        context.execute(f.read())

    return context.serverSide


# Provide feedback for a fill-in-the-blank problem. This should produce
# identical results to the code in ``evaluateAnswers`` in ``fitb.js``.
async def fitb_feedback(
    # The validator for the ``fitb_answers`` table containing data before it's stored in the db. This function updates the grade stored in the validator.
    fitb_validator: Any,
    # The feedback to use when grading this question, taken from the ``feedback`` field of the ``fitb_answers`` table.
    feedback: Dict[Any, Any],
    # The base course this question appears in.
    base_course: str,
) -> Dict[str, Any]:
    # Load and run the JS grader.
    dyn_vars = feedback["dyn_vars"]
    blankNames = feedback["blankNames"]
    js_context = get_js_context(
        Path(settings.book_path) / base_course / "published" / base_course
    )
    # Use a render to get the dynamic vars for a dynamic problem.
    dyn_vars_eval = None
    problemHtml = ""
    if dyn_vars:
        problemHtml, dyn_vars_eval = js_context.fitb.renderDynamicContent(
            fitb_validator.seed, dyn_vars, feedback["problemHtml"]
        )

    # Get the answer.
    answer_json = fitb_validator.answer
    # If there's no answer, skip grading.
    if answer_json is None:
        return dict(seed=fitb_validator.seed, problemHtml=problemHtml)
    try:
        # The new format is JSON.
        answer = json.loads(answer_json)
        # Some answers may parse as JSON, but still be in the old format. The
        # new format should always return an array.
        assert isinstance(answer, list)
    except Exception:
        # The old format is comma-separated.
        answer = answer_json.split(",")

    # Grade using the JavaScript grader.
    displayFeed, correct, isCorrectArray, percent = js_context.fitb.evaluateAnswersCore(
        blankNames, answer, feedback["feedbackArray"], dyn_vars_eval, True
    )
    # For dynamic problems, render the feedback.
    if dyn_vars:
        for index in range(len(displayFeed)):
            displayFeed[index] = js_context.fitb.renderDynamicFeedback(
                blankNames, answer, index, displayFeed[index], dyn_vars_eval
            )

    # Store updates to the database.
    fitb_validator.correct = correct
    fitb_validator.percent = percent

    # Return grading results to the client for a non-exam scenario.
    if settings.is_exam:
        return dict(
            displayFeed=["Response recorded."] * len(answer),
            correct=True,
            isCorrectArray=[True] * len(answer),
            problemHtml=problemHtml,
        )
    else:
        return dict(
            displayFeed=displayFeed,
            correct=correct,
            isCorrectArray=isCorrectArray,
            problemHtml=problemHtml,
        )


# lp feedback
# ===========
async def lp_feedback(lp_validator: Any, feedback: Dict[Any, Any], base_course: str):
    # Begin by reformatting the answer for storage in the database. Do this now, so the code will be stored correctly even if the function returns early due to an error.
    try:
        code_snippets = json.loads(lp_validator.answer)
    except Exception:
        lp_validator.answer = json.dumps({})
        return {"errors": [f"Unable to load answers from '{lp_validator.answer}'."]}
    lp_validator.answer = json.dumps(dict(code_snippets=code_snippets))

    sphinx_base_path = os.path.join(settings.book_path, base_course)
    source_path = feedback["source_path"]
    # Read the Sphinx config file to find paths relative to this directory.
    sphinx_config = read_sphinx_config(sphinx_base_path)
    if not sphinx_config:
        return {
            "errors": [
                "Unable to load Sphinx configuration file from {}".format(
                    sphinx_base_path
                )
            ]
        }
    sphinx_source_path = sphinx_config["SPHINX_SOURCE_PATH"]
    sphinx_out_path = sphinx_config["SPHINX_OUT_PATH"]

    # Next, read the student source in for the program the student is working on.
    try:
        # Find the path to the student source file.
        abs_source_path = os.path.normpath(
            os.path.join(
                sphinx_base_path, sphinx_out_path, STUDENT_SOURCE_PATH, source_path
            )
        )
        with open(abs_source_path, encoding="utf-8") as f:
            source_str = f.read()
    except Exception as e:
        return {
            "errors": ["Cannot open source file {}: {}.".format(abs_source_path, e)]
        }

    # Create a snippet-replaced version of the source, by looking for "put code
    # here" comments and replacing them with the provided code. To do so,
    # first split out the "put code here" comments.
    split_source = source_str.split(code_here_comment(source_path))
    # Sanity check! Source with n "put code here" comments splits into n+1
    # items, into which the n student code snippets should be interleaved.
    if len(split_source) - 1 != len(code_snippets):
        return {"errors": ["Wrong number of snippets."]}
    # Interleave these with the student snippets.
    interleaved_source = [""] * (2 * len(split_source) - 1)
    interleaved_source[::2] = split_source
    try:
        interleaved_source[1::2] = _platform_edit(
            feedback["builder"], code_snippets, source_path
        )
    except Exception as e:
        return {"errors": ["An exception occurred: {}".format(e)]}
    # Join them into a single string. Make sure newlines separate everything.
    source_str = "\n".join(interleaved_source)

    # Create a temporary directory, then write the source there.
    with tempfile.TemporaryDirectory() as temp_path:
        temp_source_path = os.path.join(temp_path, os.path.basename(source_path))
        with open(temp_source_path, "w", encoding="utf-8") as f:
            f.write(source_str)

        try:
            res = _scheduled_builder.delay(
                feedback["builder"],
                temp_source_path,
                sphinx_base_path,
                sphinx_source_path,
                sphinx_out_path,
                source_path,
            )
            output, correct = res.get(timeout=60)
        except Exception as e:
            return {"errors": ["Error in build task: {}".format(e)]}
        else:
            # Strip whitespace and return only the last 4K or data or so.
            # There's no need for more -- it's probably just a crashed or
            # confused program spewing output, so don't waste bandwidth or
            # storage space on it.
            resultString = output.strip()[-4096:]
            # Update the data to be stored in the database.
            lp_validator.answer = json.dumps(
                dict(code_snippets=code_snippets, resultString=resultString)
            )
            lp_validator.correct = correct
            # Return just new data (not the code snippets) to the client.
            return {
                # The answer.
                "answer": {"resultString": resultString},
                "correct": correct,
            }


# This function should take a list of code snippets and modify them to prepare
# for the platform-specific compile. For example, add a line number directive
# to the beginning of each.
def _platform_edit(
    # The builder which will be used to build these snippets.
    builder,
    # A list of code snippets submitted by the user.
    code_snippets,
    # The name of the source file into which these snippets will be inserted.
    source_path,
):

    # Prepend a line number directive to each snippet. I can't get this to work
    # in the assembler. I tried:
    #
    # - From Section 4.11 (Misc directives):
    #
    #   -   ``.appline 1``
    #   -   ``.ln 1`` (produces the message ``Error: unknown pseudo-op: `.ln'``.
    #       But if I use the assembly option ``-a``, the listing file show that
    #       this directive inserts line 1 of the source .s file into the listing
    #       file. ???
    #   -   ``.loc 1 1`` (trying ``.loc 1, 1`` produces ``Error: rest of line
    #       ignored; first ignored character is `,'``)
    #
    # - From Section 4.12 (directives for debug information):
    #
    #   -   ``.line 1``. I also tried this inside a ``.def/.endef`` pair, which
    #       just produced error messages.
    #
    # Perhaps saving each snippet to a file, then including them via
    # ``.include`` would help. Ugh.
    #
    # Select what to prepend based on the language.
    ext = os.path.splitext(source_path)[1]
    if ext == ".c":
        # See https://gcc.gnu.org/onlinedocs/cpp/Line-Control.html.
        fmt = '#line 1 "box {}"\n'
    elif ext == ".s":
        fmt = ""
    elif ext == ".py":
        # Python doesn't (easily) support `setting line numbers <https://lists.gt.net/python/python/164854>`_.
        fmt = ""
    else:
        # This is an unsupported language. It would be nice to report this as an error instead of raising an exception.
        raise RuntimeError("Unsupported extension {}".format(ext))
    return [
        fmt.format(index + 1) + code_snippets[index]
        for index in range(len(code_snippets))
    ]
