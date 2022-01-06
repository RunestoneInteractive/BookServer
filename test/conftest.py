# ***************************************
# |docname| - pytest fixtures for testing
# ***************************************
#
# ``conftest.py`` is the standard file for defining **fixtures**
# for `pytest <https://docs.pytest.org/en/stable/fixture.html>`_.
# One job of a fixture is to arrange and set up the environment
# for the actual test.
# It may seem a bit mysterious to newcomers that you define
# fixtures in here and use them in your various ``xxx_test.py`` files
# especially because you do not need to import the fixtures they just
# magically show up.  Bizarrely fixtures are called into action on
# behalf of a test by adding them as a parameter to that test.
#
#
# Imports
# =======
# These are listed in the order prescribed by `PEP 8
# <http://www.python.org/dev/peps/pep-0008/#imports>`_.
#
# Standard library
# ----------------
import datetime
import io
import logging
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from threading import Lock, Thread
from typing import Optional
from shutil import rmtree, copytree
from urllib.error import URLError
from urllib.request import urlopen

# Third-party imports
# -------------------
import console_ctrl
import coverage
from fastapi.testclient import TestClient
from _pytest.monkeypatch import MonkeyPatch
import pytest
from pyvirtualdisplay import Display

# Since ``selenium_driver`` is a parameter to a function (which is a fixture), flake8 sees it as unused. However, pytest understands this as a request for the ``selenium_driver`` fixture and needs it.
from runestone.shared_conftest import _SeleniumUtils, selenium_driver  # noqa: F401
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from sqlalchemy.sql import text

# Local imports
# -------------
# Put the book server in test mode, since the following imports will look at this setting.
os.environ["BOOK_SERVER_CONFIG"] = "test"

# Start code coverage here. The imports below load code that must be covered. This seems cleaner than other solutions (create a separate pytest plugin just for coverage, put coverage code in a ``conftest.py`` that's imported before this one.)
cov = coverage.Coverage()
cov.start()

# These all need a ``noqa: E402`` comment, since they come after the statements above.
from bookserver.config import DatabaseType, settings  # noqa; E402
from bookserver.db import async_session, engine  # noqa; E402
from bookserver.crud import (  # noqa; E402
    create_user,
    create_course,
    fetch_base_course,
    fetch_course,
)
from bookserver.main import app  # noqa; E402
from bookserver.models import AuthUserValidator, CoursesValidator  # noqa; E402
from .ci_utils import is_linux, is_darwin, is_win, pushd  # noqa; E402

# Globals
# =======
bookserver_port = 8080
bookserver_address = f"http://localhost:{bookserver_port}"
# Set up logging.
logger = logging.getLogger(__name__)


# Pytest setup
# ============
# Add `command-line options <http://doc.pytest.org/en/latest/example/parametrize.html#generating-parameters-combinations-depending-on-command-line>`_.
def pytest_addoption(parser):
    # Per the `API reference <http://doc.pytest.org/en/latest/reference.html#_pytest.hookspec.pytest_addoption>`_,
    # options are argparse style.
    parser.addoption(
        "--skipdbinit",
        action="store_true",
        help="Skip initialization of the test database.",
    )

    # This runs the server in a separate window with a usable console. A developer can add ``import pdb; pdb.set_trace()`` at any point in the bookserver to invoke the debugger and understand what's happening. The same technique also works well in the tests -- stop at a certain point in the test and (if running a Selenium-based test) look at the JavaScript console, or examine local variables in Python, etc.
    parser.addoption(
        "--server_debug",
        action="store_true",
        help="Enable server debug mode.",
    )


# .. _code_coverage:
#
# Code coverage
# -------------
# Getting code coverage to work in tricky. This is because code coverage must be collected while running pytest and while running the webserver. Since these run in parallel, trying to create a single coverage data file doesn't work. Therefore, we must set coverage's `parallel flag to True <parallel=True>`, so that each data file will be uniquely named. After pytest finishes, combine these two data files to produce a coverage result. While pytest-cov would be ideal, it `overrides <https://pytest-cov.readthedocs.io/en/latest/config.html>`_ the ``parallel`` flag (sigh).
#
# A simpler solution: invoke ``coverage run -m pytest``, then ``coverage combine``, then ``coverage report``. I opted for this complexity, to make it easy to just invoke pytest and get coverage with no further steps.
#
# Output a coverage report when testing is done. See the `docs <https://docs.pytest.org/en/latest/reference.html#_pytest.hookspec>`__.pytest_terminal_summary.
def pytest_terminal_summary(terminalreporter):
    cov.stop()
    cov.save()
    # Combine this (pytest) coverage with the webserver coverage. Use a new object, since the ``cov`` object is tied to the data file produced by the pytest run. Otherwise, the report is correct, but the resulting ``.coverage`` data file is empty.
    cov_all = coverage.Coverage()
    cov_all.combine()

    # Report on this combined data.
    f = io.StringIO()
    cov_all.report(file=f)
    terminalreporter.write(f.getvalue())


# Server prep and run
# ===================
# This fixture starts and shuts down the web2py server.
#
# Execute this `fixture <https://docs.pytest.org/en/latest/fixture.html>`_ once per `session <https://docs.pytest.org/en/latest/fixture.html#scope-sharing-a-fixture-instance-across-tests-in-a-class-module-or-session>`_.
@pytest.fixture(scope="session")
def run_bookserver(pytestconfig, init_db):
    # Start the bookserver and the scheduler.
    prefix_args = []
    # Pass pytest's log level to Celery; if not specified, it defaults to INFO. Note that the command-line option uses dashes instead of underscores, while the config file uses underscripts (see the `docs <https://docs.pytest.org/en/6.2.x/logging.html#live-logs>`__).
    log_level = pytestconfig.getoption("log_cli_level") or "INFO"
    if pytestconfig.getoption("server_debug"):
        # Don't redirect stdio, so the developer can see and interact with it.
        kwargs = {}
        # TODO: these come from `SO <https://stackoverflow.com/a/19308462/16038919>`__ but are not tested.
        if is_linux:
            # This is a guess, and will depend on your distro. Fix as necessary. Another common choice: ``["xterm", "-e"]``.
            prefix_args = ["gnome-terminal", "-x"]
        elif is_darwin:
            prefix_args = ["open", "-W", "-a", "Terminal.app"]
    else:
        kwargs = dict(stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if is_win:
        # This is required on Windows to be able to stop the web server cleanly.
        kwargs.update(dict(creationflags=subprocess.CREATE_NEW_CONSOLE))
    book_server_process = subprocess.Popen(
        prefix_args
        + [
            sys.executable,
            "-m",
            "coverage",
            "run",
            "-m",
            # Run from uvicorn, so coverage still works. Running from `../bookserver/__main__.py` wouldn't include coverage.
            "uvicorn",
            f"--port={bookserver_port}",
            f"--log-level={log_level.lower()}",
            "bookserver.main:app",
        ],
        # Produce text (not binary) output for nice output in ``echo()`` below.
        universal_newlines=True,
        **kwargs,
    )

    # Run Celery. Per `Celery issue #3422 <https://github.com/celery/celery/issues/3422>`_, there are problems with coverage and Celery. This seems to work.
    celery_process = subprocess.Popen(
        prefix_args
        + [
            sys.executable,
            "-m",
            "coverage",
            "run",
            "-m",
            "celery",
            "--app=bookserver.internal.scheduled_builder",
            "worker",
            "--pool=threads",
            "--concurrency=4",
            # See the `Celery worker CLI docs <https://docs.celeryproject.org/en/stable/reference/cli.html#celery-worker>`_.
            f"--loglevel={log_level}",
        ],
        # Produce text (not binary) output for nice output in ``echo()`` below.
        universal_newlines=True,
        **kwargs,
    )

    # Start a thread to read bookserver output and echo it.
    print_lock = Lock()

    def echo(popen_obj, description_str):
        stdout, stderr = popen_obj.communicate()
        # Use a lock to keep output together.
        with print_lock:
            log_subprocess(stdout, stderr, description_str)

    echo_threads = [
        Thread(target=echo, args=(book_server_process, "book server")),
        Thread(target=echo, args=(celery_process, "celery process")),
    ]
    for echo_thread in echo_threads:
        echo_thread.start()

    def terminate_process(process):
        if is_win:
            # Send a ctrl-c to the web server, so that it can shut down cleanly and record the coverage data. On Windows, using ``process.terminate()`` produces no coverage data.
            console_ctrl.send_ctrl_c(process.pid)
            try:
                process.wait(5)
            except subprocess.TimeoutExpired:
                # If that didn't work, just kill it.
                logger.warning("Unable to cleanly end process. Terminating.")
                process.terminate()
        else:
            # On Unix, this shuts the webserver down cleanly.
            process.terminate()

    # Terminate the server and celery, printing any output produced.
    def shut_down():
        terminate_process(book_server_process)
        terminate_process(celery_process)
        for echo_thread in echo_threads:
            echo_thread.join()

    logger.info(f"Waiting for the webserver to come up... at {bookserver_address}")
    for tries in range(10):
        try:
            urlopen(bookserver_address, timeout=1)
            break
        except URLError as e:
            logger.info(f"Try {tries}: {e}")
        time.sleep(1)
    else:
        shut_down()
        assert False, f"Server {bookserver_address} not up."
    logger.info("done.")

    # After this comes the `teardown code <https://docs.pytest.org/en/latest/fixture.html#fixture-finalization-executing-teardown-code>`_.
    yield

    shut_down()


def log_subprocess(stdout: Optional[str], stderr: Optional[str], description_str: str):
    log_output(description_str + ".stdout", stdout or "")
    # A lot of output from stderr isn't actually an error. Treat it more like another stdout.
    log_output(description_str + ".stderr", stderr or "")


def log_output(log_name: str, log_text: str):
    local_logger = logging.getLogger(log_name)
    for line in log_text.splitlines():
        line = line.lower()
        if "critical" in line:
            local_logger.critical(line)
        elif "error" in line or "traceback" in line:
            local_logger.error(line)
        elif "warning" in line:
            local_logger.warning(line)
        elif "debug" in line:
            local_logger.debug(line)
        else:
            local_logger.info(line)


# Database
# ========
@pytest.fixture(scope="session")
def init_db(pytestconfig):
    assert os.environ["TEST_DBURL"]
    dburl = os.environ["TEST_DBURL"]

    if pytestconfig.getoption("skipdbinit"):
        logger.info("Skipping DB initialization.")
        return

    # Start with a clean database.
    if settings.database_type == DatabaseType.SQLite:
        match = re.match(r"^sqlite:///(.*)$", dburl)
        path = match.group(1)
        if Path(path).exists():
            os.unlink(path)

    elif settings.database_type == DatabaseType.PostgreSQL:
        # Extract the components of the DBURL. The expected format is ``postgresql://user:password@netloc/dbname``, a simplified form of the `connection URI <https://www.postgresql.org/docs/9.6/static/libpq-connect.html#LIBPQ-CONNSTRING>`_.
        (empty1, pguser, pgpassword, pgnetloc, dbname, empty2) = re.split(
            r"^postgresql://(.*):(.*)@(.*)\/(.*)$", dburl
        )
        # Per the `docs <https://docs.python.org/3/library/re.html#re.split>`_, the first and last split are empty because the pattern matches at the beginning and the end of the string.
        assert not empty1 and not empty2
        # The `postgres command-line utilities <https://www.postgresql.org/docs/current/libpq-envars.html>`_ require these.
        os.environ["PGPASSWORD"] = pgpassword
        os.environ["PGUSER"] = pguser
        os.environ["PGHOST"] = pgnetloc

        try:
            subprocess.run(f"dropdb --if-exists {dbname}", check=True, shell=True)
            subprocess.run(f"createdb --echo {dbname}", check=True, shell=True)
        except Exception as e:
            assert False, f"Failed to drop the database: {e}. Do you have permission?"

    else:
        assert False, "Unknown database type."

    # Copy the test book to the books directory.
    test_book_path = f"{settings.book_path}/test_course_1"
    rmtree(test_book_path, ignore_errors=True)
    # Sometimes this fails for no good reason on Windows. Retry.
    for retry in range(100):
        try:
            copytree(
                f"{settings.runestone_path}/tests/test_course_1",
                test_book_path,
            )
            break
        except OSError:
            if retry == 99:
                raise

    # Start the app to initialize the database.
    with TestClient(app):
        pass

    # Build the test book to add in db fields needed.
    with pushd(test_book_path), MonkeyPatch().context() as m:
        m.setenv("WEB2PY_CONFIG", "test")

        def run_subprocess(args: str, description: str):
            logger.info(f"Running {description}: {args}")
            cp = subprocess.run(
                args, capture_output=True, check=True, shell=True, text=True
            )
            log_subprocess(cp.stdout, cp.stderr, description)

        run_subprocess(
            "{} -m runestone build --all".format(sys.executable), "runestone.build"
        )
        run_subprocess(
            "{} -m runestone deploy".format(sys.executable), "runestone.deploy"
        )


#
# .. _bookserver_session:
#
# bookserver_session
# ------------------
# This fixture provides access to a clean instance of the Runestone database. by returning a bookserver ``async_session``.
@pytest.fixture
async def bookserver_session(init_db):
    # Get a list of (almost) all tables in the database. Note that these queries exclude specific tables, which the ``runestone build`` populates and which  should not be modified otherwise. One method to identify these tables which should not be truncated is to run ``pg_dump --data-only $TEST_DBURL > out.sql`` on a clean database, then inspect the output to see which tables have data. It also excludes all the scheduler tables, since truncating these tables makes the process take a lot longer.
    keep_tables = """
        (
            'questions',
            'source_code',
            'chapters',
            'sub_chapters',
            'scheduler_run',
            'scheduler_task',
            'scheduler_task_deps',
            'scheduler_worker'
        )
        """
    if settings.database_type == DatabaseType.PostgreSQL:
        tables_query = f"""
            SELECT input_table_name AS truncate_query FROM (
                SELECT table_name AS input_table_name
                FROM information_schema.tables
                WHERE
                    table_schema NOT IN (
                        'pg_catalog', 'information_schema'
                    )
                    AND table_name NOT IN {keep_tables}
                    AND table_schema NOT LIKE 'pg_toast%'
            ) AS information
            ORDER BY input_table_name;
            """
    elif settings.database_type == DatabaseType.SQLite:
        # Taken from `SQList docs <https://www.sqlite.org/faq.html#q7>`_.
        tables_query = f"""
            SELECT name FROM sqlite_schema
            WHERE type='table' AND name NOT IN {keep_tables}
            ORDER BY name;
            """
    else:
        assert False, "Unknown database type."

    # We can't use a session here, since that only expects/generates SQL from ORM operations; using a session causes a rollback at the end of the session, since (I think) no ORM operations occurred.
    async with engine.begin() as conn:
        tables_to_delete = (await conn.execute(text(tables_query))).scalars().all()
        if settings.database_type == DatabaseType.PostgreSQL:
            tables = '"' + '", "'.join(tables_to_delete) + '"'
            await conn.execute(text(f"TRUNCATE {tables} CASCADE;"))
        else:
            for table in tables_to_delete:
                await conn.execute(text(f'DELETE FROM "{table}";'))

    # The database is clean. Proceed with the test.
    yield async_session

    # Otherwise, testing with Postgres produces weird failures.
    await engine.dispose()


# Provide a ``TestClient(app)`` with the database properly configured.
@pytest.fixture
def test_client_app(bookserver_session):
    return TestClient(app)


# User management
# ===============
@pytest.fixture
def create_test_course(bookserver_session):
    async def _create_test_course(**kwargs):
        # If the base course doesn't exist and isn't this course, make that first.
        base_course_name = kwargs["base_course"]
        if base_course_name != kwargs["course_name"] and not await fetch_base_course(
            base_course_name
        ):
            base_course = CoursesValidator(**kwargs)
            base_course.course_name = base_course_name
            await create_course(base_course)

        course = CoursesValidator(**kwargs)
        await create_course(course)
        # Fetch the newly-created course to get its ID.
        return await fetch_course(course.course_name)

    return _create_test_course


@pytest.fixture
async def test_course_1(create_test_course):
    return await create_test_course(
        course_name="test_child_course_1",
        term_start_date=datetime.datetime(2000, 1, 1),
        institution="Test U",
        login_required=True,
        base_course="test_course_1",
        allow_pairs=True,
        student_price=None,
        downloads_enabled=True,
        courselevel="",
        new_server=False,
    )


# A class to hold a user plus the class the user is in.
class TestAuthUserValidator(AuthUserValidator):
    course: CoursesValidator


@pytest.fixture
def create_test_user(bookserver_session):
    async def _create_test_user(**kwargs):
        # TODO: Add this user to the provided course.
        course = kwargs.pop("course")
        kwargs["course_id"] = course.id
        kwargs["course_name"] = course.course_name
        user = AuthUserValidator(**kwargs)
        assert await create_user(user)
        return TestAuthUserValidator(course=course, **kwargs)

    return _create_test_user


# Provide a way to get a prebuilt test user.
@pytest.fixture
async def test_user_1(create_test_user, test_course_1):
    return await create_test_user(
        username="test_user_1",
        first_name="test",
        last_name="user 1",
        email="test@user1.com",
        password="password_1",
        created_on=datetime.datetime(2000, 1, 1),
        modified_on=datetime.datetime(2000, 1, 1),
        registration_key="",
        reset_password_key="",
        registration_id="",
        course=test_course_1,
        active=True,
        donated=True,
        accept_tcp=True,
    )


# Selenium
# ========
# Provide access to Runestone through a web browser using Selenium. There's a lot of shared code between these tests and the Runestone Component tests using Selenium; see :doc:`runestone/shared_conftest.py` for details.
#
# Create an instance of Selenium once per testing session.
@pytest.fixture(scope="session")
def selenium_driver_session(run_bookserver):
    is_linux = sys.platform.startswith("linux")
    # Start a virtual display for Linux if there's no display available.
    if is_linux and "DISPLAY" not in os.environ:
        display = Display(visible=0, size=(1280, 1024))
        display.start()
    else:
        display = None

    # Start up the Selenium driver.
    options = Options()
    options.add_argument("--window-size=1200,800")
    # When run as root, Chrome complains ``Running as root without --no-sandbox is not supported. See https://crbug.com/638180.`` Here's a `crude check for being root <https://stackoverflow.com/a/52621917>`_.
    if is_linux and os.geteuid() == 0:
        options.add_argument("--no-sandbox")
    # _`selenium_logging`: Ask Chrome to save the logs from the JavaScript console. Copied from `SO <https://stackoverflow.com/a/63625977/16038919>`__.
    caps = webdriver.DesiredCapabilities.CHROME.copy()
    caps["goog:loggingPrefs"] = {"browser": "ALL"}
    driver = webdriver.Chrome(options=options, desired_capabilities=caps)

    yield driver

    # Shut everything down.
    driver.close()
    driver.quit()
    if display:
        display.stop()


# Provide additional server methods for Selenium.
class _SeleniumServerUtils(_SeleniumUtils):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None

    def login(
        self,
        # A ``_TestUser`` instance.
        test_user,
    ):

        self.get("auth/login")
        self.driver.find_element_by_id("loginuser").send_keys(test_user.username)
        self.driver.find_element_by_id("loginpw").send_keys(test_user.password)
        self.driver.find_element_by_id("login_button").click()
        self.user = test_user

    def logout(self):
        self.get("auth/logout")
        self.wait.until(
            EC.text_to_be_present_in_element((By.CSS_SELECTOR, "h1"), "Login")
        )
        self.user = None

    def get_book_url(self, url):
        return self.get(f"books/published/test_child_course_1/{url}")


# Present ``_SeleniumServerUtils`` as a fixture.
@pytest.fixture
def selenium_utils(selenium_driver):  # noqa: F811
    return _SeleniumServerUtils(selenium_driver, bookserver_address)


# A fixture to login to the test_user_1 account using Selenium before testing, then logout when the tests complete.
@pytest.fixture
def selenium_utils_user(selenium_utils, test_user_1):
    selenium_utils.login(test_user_1)
    yield selenium_utils
    selenium_utils.logout()
