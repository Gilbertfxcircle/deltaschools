"""Backend test suite.

Tests of the pure domain "laws" import only stdlib + app.core/app.domain, so they
run with no third-party dependencies (``python -m unittest discover``). Tests
that exercise FastAPI/SQLAlchemy require ``pip install -r requirements.txt``.
"""
