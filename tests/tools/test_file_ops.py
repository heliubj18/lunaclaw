import pytest
from pathlib import Path
from lunaclaw.tools.file_ops import FileReadTool, FileWriteTool, FileEditTool, GlobTool, GrepTool
from lunaclaw.audit.tracer import TraceContext


@pytest.fixture
def trace():
    return TraceContext()


@pytest.fixture
def sample_dir(tmp_path):
    (tmp_path / "hello.txt").write_text("hello world\nfoo bar\nbaz")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "test.py").write_text("def test():\n    pass\n")
    return tmp_path


# FileRead
@pytest.mark.asyncio
async def test_file_read(sample_dir, trace):
    tool = FileReadTool()
    result = await tool.execute({"path": str(sample_dir / "hello.txt")}, trace)
    assert result.success is True
    assert "hello world" in result.output


@pytest.mark.asyncio
async def test_file_read_not_found(trace):
    tool = FileReadTool()
    result = await tool.execute({"path": "/nonexistent/file.txt"}, trace)
    assert result.success is False


# FileWrite
@pytest.mark.asyncio
async def test_file_write(tmp_path, trace):
    tool = FileWriteTool()
    path = str(tmp_path / "new.txt")
    result = await tool.execute({"path": path, "content": "new content"}, trace)
    assert result.success is True
    assert Path(path).read_text() == "new content"


# FileEdit
@pytest.mark.asyncio
async def test_file_edit(sample_dir, trace):
    tool = FileEditTool()
    path = str(sample_dir / "hello.txt")
    result = await tool.execute(
        {
            "path": path,
            "old_string": "hello world",
            "new_string": "goodbye world",
        },
        trace,
    )
    assert result.success is True
    assert "goodbye world" in Path(path).read_text()


@pytest.mark.asyncio
async def test_file_edit_not_found_string(sample_dir, trace):
    tool = FileEditTool()
    result = await tool.execute(
        {
            "path": str(sample_dir / "hello.txt"),
            "old_string": "nonexistent",
            "new_string": "replacement",
        },
        trace,
    )
    assert result.success is False


# Glob
@pytest.mark.asyncio
async def test_glob(sample_dir, trace):
    tool = GlobTool()
    result = await tool.execute({"pattern": "**/*.py", "path": str(sample_dir)}, trace)
    assert result.success is True
    assert "test.py" in result.output


# Grep
@pytest.mark.asyncio
async def test_grep(sample_dir, trace):
    tool = GrepTool()
    result = await tool.execute({"pattern": "foo", "path": str(sample_dir)}, trace)
    assert result.success is True
    assert "foo bar" in result.output
