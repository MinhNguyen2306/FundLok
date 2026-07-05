# DEPRECATED (HANDOFF-02 Fix C): merged into app.uploads.router (files_router).
# This module is no longer imported anywhere -- see app/main.py, which now
# imports `files_router` from app.uploads.router instead of from here.
#
# Left as an empty stub rather than deleted because this sandbox environment
# cannot delete/unlink files on the mounted repo; Edward, please delete this
# whole app/files/ directory (router.py, service.py, schemas.py, __init__.py)
# from your terminal once this PR is reviewed.
