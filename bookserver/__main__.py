# *****************************************************
# |docname| - Provide a simple method to run the server
# *****************************************************
# From the terminal / command line, execute either ``bookserver`` or ``python -m bookserver``, which runs the book server.

import uvicorn


def run():
    # See https://www.uvicorn.org/deployment/#running-programmatically.
    uvicorn.run("bookserver.main:app", port=8080)


if __name__ == "__main__":
    run()
