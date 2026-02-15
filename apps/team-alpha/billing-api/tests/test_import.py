import runpy
import os


def test_main_import(monkeypatch):
    # Ensure DB env vars exist so importing the module doesn't raise
    monkeypatch.setenv("DB_NAME", "testdb")
    monkeypatch.setenv("DB_USER", "testuser")
    monkeypatch.setenv("DB_PASSWORD", "testpass")

    # Run the module path to verify it loads without raising
    main_py = os.path.join(os.path.dirname(__file__), "..", "src", "main.py")
    runpy.run_path(main_py, run_name="__main__")
