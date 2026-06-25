import os, pytest, logging
logging.basicConfig(level=logging.INFO)
LIVE = bool(os.environ.get("ANTHROPIC_API_KEY"))
def pytest_configure(config):
    config.addinivalue_line("markers","live: requires ANTHROPIC_API_KEY")
    config.addinivalue_line("markers","smoke: smoke tests")
    config.addinivalue_line("markers","regression: regression tests")
