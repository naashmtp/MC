import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from minecraft_manager import tail_log


def create_temp_log(lines):
    fp = tempfile.NamedTemporaryFile(delete=False)
    for line in lines:
        fp.write((line + "\n").encode())
    fp.close()
    return fp.name


def test_tail_log_default():
    lines = [f"line {i}" for i in range(1, 41)]
    path = create_temp_log(lines)
    try:
        result = tail_log(path)
        assert result.splitlines() == lines[-20:]
    finally:
        os.unlink(path)


def test_tail_log_custom_values():
    lines = [f"entry {i}" for i in range(30)]
    path = create_temp_log(lines)
    try:
        assert tail_log(path, 10).splitlines() == lines[-10:]
        assert tail_log(path, 1).splitlines() == lines[-1:]
        assert tail_log(path, 0) == ""
    finally:
        os.unlink(path)


def test_tail_log_more_than_file():
    lines = ["a", "b", "c"]
    path = create_temp_log(lines)
    try:
        assert tail_log(path, 10).splitlines() == lines
    finally:
        os.unlink(path)
