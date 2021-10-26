# *********************************************
# |docname| - Tests of the Runestone Components
# *********************************************
# These tests check both client-side and server-side aspects of the Runestone Components.
#
# Imports
# =======
# These are listed in the order prescribed by `PEP 8
# <http://www.python.org/dev/peps/pep-0008/#imports>`_.
#
# Standard library
# ----------------
import asyncio
import datetime
import json

# Third-party imports
# -------------------
import pytest
from runestone.activecode.test import test_activecode
from runestone.clickableArea.test import test_clickableArea
from runestone.dragndrop.test import test_dragndrop
from runestone.fitb.test import test_fitb
from runestone.mchoice.test import test_assess
from runestone.parsons.test import test_parsons
from runestone.poll.test import test_poll
from runestone.shared_conftest import element_has_css_class
from runestone.shortanswer.test import test_shortanswer
from runestone.spreadsheet.test import test_spreadsheet
from runestone.timed.test import test_timed
from runestone import runestone_version
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from sqlalchemy import null
from sqlalchemy.sql import select

# Local imports
# -------------
from bookserver.models import (
    ClickableareaAnswers,
    Code,
    MchoiceAnswers,
    FitbAnswers,
    DragndropAnswers,
    ParsonsAnswers,
    Useinfo,
    TimedExam,
    ShortanswerAnswers,
)


# Utilities
# =========
# Poll the database waiting for the client to perform an update via Ajax.
async def get_answer(session, stmt, minimum_len):
    async def poll():
        while True:
            # Get the results ordered by ID, so we can index this based on order of insertion.
            ret = (
                (await sess.execute(stmt.order_by(stmt.froms[0].c.id))).scalars().all()
            )
            if len(ret) >= minimum_len:
                return ret

    async with session() as sess:
        # Wait up to 10 seconds for the desired answer length.
        try:
            res = await asyncio.wait_for(poll(), 10)
            return res
        except Exception:
            return None


# Check the fields common to the tables of most Runestone components.
async def check_common_fields_raw(selenium_utils_user, session, stmt, index, div_id):
    row = (await get_answer(session, stmt, index + 1))[index]
    assert row.timestamp - datetime.datetime.utcnow() < datetime.timedelta(seconds=5)
    assert row.div_id == div_id
    assert row.sid == selenium_utils_user.user.username
    ## TODO FIXME uncomment this check!
    ##assert row.course_name == selenium_utils_user.user.course.course_name
    return row


# Return the answer, correct, and percent fields after checking common fields.
async def check_common_fields(selenium_utils_user, session, stmt, index, div_id):
    row = await check_common_fields_raw(
        selenium_utils_user, session, stmt, index, div_id
    )
    return row.answer, row.correct, row.percent


# Tricky fixures
# --------------
# The URL to fetch in order to do testing varies by the type of test:
#
# #.    When performing client-side testing in Runestone Components, the URL is usually "/index.html". A fixture defined in client testing code handles this; see the ``selenium_utils_1`` fixture in ``test_clickableArea.py`` in the Runestone Component, for example. The client-side tests then use this fixture.
# #.    When performing server-side testing, the URL is "/path/to/book/<url_here>.html"; see ``selenium_utils_user.get_book_url``. The fixture below provides one example of this. Then, inside a server-side test, the test invokes the client test directly, meaning that it passes its already-run fixture (which fetched the plain server-side testing page) to the client test, bypassing the client fixture.
#
# Both client-side and server-side tests must be structured carefully for this to work:
# - Client-side tests must invoke ``selenium_utils.wait_until_ready(div_id)``.
# - Client-side tests must **not** invoke ``selenium_utils.get`` in the body of the test, since this prevents server-side tests from fetching from the correct server-side location. Instead, invoke this in a fixture passed to the test, allow server-side tests to override this by passing a different fixture.
# - The ``div_id`` of client-side tests must match the div_id of server-side tests, meaning the two ``.rst`` files containing tests must use the same ``div_id``.
#
# A fixture for plain server-side testing.
@pytest.fixture
def selenium_utils_user_1(selenium_utils_user):
    selenium_utils_user.get_book_url("index.html")
    return selenium_utils_user


# Tests
# =====
#
# Active code
# -----------
# A fixture for active code server-side testing.
@pytest.fixture
def selenium_utils_user_ac(selenium_utils_user):
    selenium_utils_user.get_book_url("activecode.html")
    return selenium_utils_user


def test_runestone_version():
    assert runestone_version.startswith("6.")


@pytest.mark.asyncio
async def test_runlog(selenium_utils_user_ac, bookserver_session):
    div_id = "test_activecode_2"
    test_activecode.test_history(selenium_utils_user_ac)

    async def ac_check_runlog(div_id):
        row = await get_answer(
            bookserver_session, select(Code).where(Code.acid == div_id), 1
        )
        assert row

    await ac_check_runlog(div_id)


# @pytest.mark.skip(reason="Need to port more server code first.")
@pytest.mark.asyncio
async def test_activecode_1(selenium_utils_user_ac, bookserver_session):
    session = bookserver_session

    async def ac_check_fields(index, div_id):
        row = (
            await get_answer(
                session, select(Code).where(Code.acid == div_id), index + 1
            )
        )[index]
        assert row.timestamp - datetime.datetime.utcnow() < datetime.timedelta(
            seconds=5
        )
        assert row.acid == div_id
        assert row.sid == selenium_utils_user_ac.user.username
        assert row.course_id == selenium_utils_user_ac.user.course.id
        return row

    test_activecode.test_history(selenium_utils_user_ac)
    row = await ac_check_fields(0, "test_activecode_2")
    assert row.code == "print('Goodbye')"
    assert row.comment is None
    assert row.language == "python"

    # Make sure that the appropriate row is in the useinfo table
    row = await get_answer(
        session,
        select(Useinfo).where(
            (Useinfo.div_id == "test_activecode_2")
            & (Useinfo.sid == selenium_utils_user_ac.user.username)
        ),
        1,
    )
    assert row
    # assert row.event == "activecode"
    # assert row.act == "run"


# ClickableArea
# -------------
@pytest.mark.asyncio
async def test_clickable_area_1(selenium_utils_user_1, bookserver_session):
    div_id = "test_clickablearea_1"

    async def ca_check_common_fields(index):
        return await check_common_fields(
            selenium_utils_user_1,
            bookserver_session,
            select(ClickableareaAnswers).where(ClickableareaAnswers.div_id == div_id),
            index,
            div_id,
        )

    test_clickableArea.test_ca1(selenium_utils_user_1)
    assert await ca_check_common_fields(0) == ("", False, None)

    test_clickableArea.test_ca2(selenium_utils_user_1)
    assert await ca_check_common_fields(1) == ("0;2", True, 1)

    # TODO: There are a lot more clickable area tests that could be easily ported!


# Drag-n-drop
# -----------
@pytest.mark.asyncio
async def test_dnd_1(selenium_utils_user_1, bookserver_session):
    div_id = "test_dnd_1"

    async def dnd_check_common_fields(index):
        return await check_common_fields(
            selenium_utils_user_1,
            bookserver_session,
            select(DragndropAnswers).where(DragndropAnswers.div_id == div_id),
            index,
            div_id,
        )

    test_dragndrop.test_dnd1(selenium_utils_user_1)
    assert await dnd_check_common_fields(0) == ("-1;-1;-1", False, None)

    # TODO: There are more dnd tests that could easily be ported!


# Fitb
# ----
# Test server-side logic in FITB questions.
@pytest.mark.asyncio
async def test_fitb_1(selenium_utils_user_1, bookserver_session):
    async def fitb_check_common_fields(index, div_id):
        answer, correct, percent = await check_common_fields(
            selenium_utils_user_1,
            bookserver_session,
            select(FitbAnswers).where(FitbAnswers.div_id == div_id),
            index,
            div_id,
        )
        return json.loads(answer), correct, percent

    test_fitb.test_fitb1(selenium_utils_user_1)
    assert await fitb_check_common_fields(0, "test_fitb_string") == (["", ""], False, 0)

    test_fitb.test_fitb2(selenium_utils_user_1)
    assert await fitb_check_common_fields(1, "test_fitb_string") == (
        ["red", ""],
        False,
        0.5,
    )

    test_fitb.test_fitb3(selenium_utils_user_1)
    assert await fitb_check_common_fields(2, "test_fitb_string") == (
        ["red", "away"],
        True,
        1,
    )

    test_fitb.test_fitb4(selenium_utils_user_1)
    assert await fitb_check_common_fields(3, "test_fitb_string") == (
        ["red", "away"],
        True,
        1,
    )

    test_fitb.test_fitboneblank_too_low(selenium_utils_user_1)
    assert await fitb_check_common_fields(0, "test_fitb_number") == ([" 6"], False, 0)

    test_fitb.test_fitboneblank_wildcard(selenium_utils_user_1)
    assert await fitb_check_common_fields(1, "test_fitb_number") == (
        ["I give up"],
        False,
        0,
    )

    test_fitb.test_fitbfillrange(selenium_utils_user_1)
    assert await fitb_check_common_fields(2, "test_fitb_number") == (
        [" 6.28 "],
        True,
        1,
    )

    test_fitb.test_fitbregex(selenium_utils_user_1)
    assert await fitb_check_common_fields(0, "test_fitb_regex_1") == (
        [" maire ", "LITTLE", "2"],
        True,
        1,
    )

    test_fitb.test_regexescapes1(selenium_utils_user_1)
    assert await fitb_check_common_fields(0, "test_fitb_regex_2") == (
        [r"C:\windows\system"],
        True,
        1,
    )

    test_fitb.test_regexescapes2(selenium_utils_user_1)
    assert await fitb_check_common_fields(0, "test_fitb_regex_3") == (["[]"], True, 1)


# Lp
# --
def test_lp_1(selenium_utils_user):
    su = selenium_utils_user
    href = "lp_demo.py.html"
    su.get_book_url(href)
    id_ = "test_lp_1"
    su.wait_until_ready(id_)

    snippets = su.driver.find_elements_by_class_name("code_snippet")
    assert len(snippets) == 1
    check_button = su.driver.find_element_by_id(id_)
    result_selector = f"#{id_} ~ .lp-result"
    result_area = su.driver.find_element_by_css_selector(result_selector)

    # Set snippets.
    code = "def one(): return 1"
    su.driver.execute_script(f'LPList["{id_}"].textAreas[0].setValue("{code}");')
    assert not result_area.text

    # Click the test button.
    check_button.click()
    su.wait.until(
        EC.text_to_be_present_in_element_value(
            (By.CSS_SELECTOR, result_selector), "Building..."
        )
    )

    # Wait until the build finishes.
    su.wait.until(
        EC.text_to_be_present_in_element(
            (By.CSS_SELECTOR, f"#{id_} ~ .lp-feedback"), "Correct. Grade: 100%"
        )
    )

    # Refresh the page. See if saved snippets are restored.
    su.get_book_url(href)
    su.wait_until_ready(id_)
    assert (
        su.driver.execute_script(f'return LPList["{id_}"].textAreas[0].getValue();')
        == code
    )


# Mchoice
# -------
@pytest.mark.asyncio
async def test_mchoice_1(selenium_utils_user_1, bookserver_session):
    div_id = "test_mchoice_1"

    async def mc_check_common_fields(index):
        return await check_common_fields(
            selenium_utils_user_1,
            bookserver_session,
            select(MchoiceAnswers).where(MchoiceAnswers.div_id == div_id),
            index,
            div_id,
        )

    test_assess.test_ma1(selenium_utils_user_1)
    assert await mc_check_common_fields(0) == ("", False, None)

    test_assess.test_ma2(selenium_utils_user_1)
    assert await mc_check_common_fields(1) == ("0,2", True, 1)

    # TODO: There are a lot more multiple choice tests that could be easily ported!


# Parsons's problems
# ------------------
@pytest.mark.asyncio
async def test_parsons_1(selenium_utils_user_1, bookserver_session):
    async def pp_check_common_fields(index, div_id):
        row = await check_common_fields_raw(
            selenium_utils_user_1,
            bookserver_session,
            select(ParsonsAnswers).where(ParsonsAnswers.div_id == div_id),
            index,
            div_id,
        )
        return row.answer, row.correct, row.percent, row.source

    test_parsons.test_general(selenium_utils_user_1)
    assert await pp_check_common_fields(0, "test_parsons_1") == (
        "-",
        False,
        None,
        "0_0-1_2_0-3_4_0-6_0-5_0",
    )
    assert await pp_check_common_fields(1, "test_parsons_1") == (
        "0_0-1_2_1-3_4_1-5_1",
        True,
        1.0,
        "6_0",
    )

    # TODO: There are several more Parsons's problems tests that could be easily ported.


# Poll
# ----
@pytest.mark.asyncio
async def test_poll_1(selenium_utils_user_1, bookserver_session):
    id = "test_poll_1"
    test_poll.test_poll(selenium_utils_user_1)
    assert (
        await get_answer(
            bookserver_session,
            select(Useinfo).where((Useinfo.div_id == id) & (Useinfo.event == "poll")),
            1,
        )
    )[0].act == "4"


# Short answer
# ------------
@pytest.mark.asyncio
async def test_short_answer_1(selenium_utils_user_1, bookserver_session):
    id = "test_short_answer_1"

    # The first test doesn't click the submit button.
    db = bookserver_session
    expr = select(ShortanswerAnswers).where(ShortanswerAnswers.div_id == id)
    test_shortanswer.test_sa1(selenium_utils_user_1)
    s = await get_answer(db, expr, 0)

    # The second test clicks submit with no text.
    test_shortanswer.test_sa2(selenium_utils_user_1)
    s = await get_answer(db, expr, 1)
    assert s[0].answer == ""

    # The third test types text then submits it.
    test_shortanswer.test_sa3(selenium_utils_user_1)
    s = await get_answer(db, expr, 2)
    assert s[1].answer == "My answer"

    # The fourth test is just a duplicate of the third test.
    test_shortanswer.test_sa4(selenium_utils_user_1)
    s = await get_answer(db, expr, 3)
    assert s[2].answer == "My answer"


# Selectquestion
# --------------
# A fixture for selectquestion server-side testing.
@pytest.fixture
def selenium_utils_user_2(selenium_utils_user):
    selenium_utils_user.get_book_url("selectquestion.html")
    return selenium_utils_user


@pytest.mark.asyncio
async def test_selectquestion_1(selenium_utils_user_2, bookserver_session):
    await test_poll_1(selenium_utils_user_2, bookserver_session)


@pytest.mark.skip(reason="Spreadsheet has not been verified with selectquestion")
def test_selectquestion_2(selenium_utils_user_2):
    test_spreadsheet_1(selenium_utils_user_2)


@pytest.mark.asyncio
async def test_selectquestion_3(selenium_utils_user_2, bookserver_session):
    await test_clickable_area_1(selenium_utils_user_2, bookserver_session)


@pytest.mark.asyncio
async def test_selectquestion_4(selenium_utils_user_2, bookserver_session):
    await test_fitb_1(selenium_utils_user_2, bookserver_session)


@pytest.mark.asyncio
async def test_selectquestion_5(selenium_utils_user_2, bookserver_session):
    await test_mchoice_1(selenium_utils_user_2, bookserver_session)


@pytest.mark.asyncio
async def test_selectquestion_6(selenium_utils_user_2, bookserver_session):
    await test_parsons_1(selenium_utils_user_2, bookserver_session)


@pytest.mark.asyncio
async def test_selectquestion_7(selenium_utils_user_2, bookserver_session):
    await test_dnd_1(selenium_utils_user_2, bookserver_session)


@pytest.mark.asyncio
async def test_selectquestion_8(selenium_utils_user_2, bookserver_session):
    await test_activecode_1(selenium_utils_user_2, bookserver_session)


@pytest.mark.asyncio
async def test_selectquestion_10(selenium_utils_user_2, bookserver_session):
    await test_short_answer_1(selenium_utils_user_2, bookserver_session)


@pytest.mark.skip(reason="Need to port more server code first.")
@pytest.mark.asyncio
async def test_selectquestion_11(selenium_utils_user_2, bookserver_session):
    _test_timed_1(selenium_utils_user_2, bookserver_session, "test_timed_2")


# Spreadsheet
# -----------
def test_spreadsheet_1(selenium_utils_user_1):
    test_spreadsheet.test_ss_autograde(selenium_utils_user_1)


# Timed questions
# ---------------
@pytest.fixture
def selenium_utils_user_timed(selenium_utils_user):
    selenium_utils_user.get_book_url("multiquestion.html")
    return selenium_utils_user


# Provide the ability to invoke tests with a specific div_id, since the selectquestion test is a different problem with a different div_id than the plain test.
async def _test_timed_1(selenium_utils_user_timed, bookserver_session, timed_divid):
    async def tt_check_common_fields(index, div_id):
        row = await check_common_fields_raw(
            selenium_utils_user_timed,
            bookserver_session,
            select(TimedExam).where(TimedExam.div_id == div_id),
            index,
            div_id,
        )
        # The tests should finish the timed exam in a few seconds.
        assert row.time_taken < 10
        return row.correct, row.incorrect, row.skipped, row.reset

    test_timed._test_1(selenium_utils_user_timed, timed_divid)
    assert await tt_check_common_fields(0, timed_divid) == (0, 0, 0, None)
    assert await tt_check_common_fields(1, timed_divid) == (6, 0, 1, None)


@pytest.mark.asyncio
async def test_timed_1(selenium_utils_user_timed, bookserver_session):
    await _test_timed_1(selenium_utils_user_timed, bookserver_session, "test_timed_1")


# progress tests
# --------------
@pytest.mark.asyncio
async def test_toc_decorators(selenium_utils_user, bookserver_session):
    su = selenium_utils_user
    href = "test_chapter_1/subchapter_a.html"
    su.get_book_url(href)
    # find #completionButton and click on it
    cbid = "completionButton"
    cb = su.driver.find_element_by_id(cbid)
    assert cb is not None
    cb.click()
    # Then go back to index and search for toctree-l2 and active or completed
    # cll = cb.get_attribute
    su.wait.until(element_has_css_class((By.ID, cbid), "buttonConfirmCompletion"))

    su.get_book_url("index.html")
    jtc = su.driver.find_element_by_id("jump-to-chapter")
    assert jtc is not null

    complete = su.driver.find_element_by_class_name("completed")
    assert complete is not null
