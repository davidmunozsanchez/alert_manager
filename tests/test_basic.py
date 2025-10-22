from src.main import hello
def test_simple():
    """Basic test to verify GitHub Actions setup"""
    assert hello() == "Hello from Alert Manager"