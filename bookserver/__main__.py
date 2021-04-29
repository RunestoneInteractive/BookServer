# *****************************************************
# |docname| - Provide a simple method to run the server
# *****************************************************
# From the terminal / command line, execute ``python -m bookserver``, which causes this script to run.

if __name__ == "__main__":
    import uvicorn

    # See https://www.uvicorn.org/deployment/#running-programmatically.
    uvicorn.run("bookserver.main:app", port=8080)
