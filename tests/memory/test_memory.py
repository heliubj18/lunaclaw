import pytest

from lunaclaw.memory.store import FileMemoryStore, Memory


@pytest.fixture
def store(tmp_path):
    return FileMemoryStore(data_dir=tmp_path)


@pytest.mark.asyncio
async def test_write_and_read(store):
    memory_id = await store.write(Memory(content="test fact", category="general", tags=["test"]))
    assert memory_id is not None
    memory = await store.read(memory_id)
    assert memory.content == "test fact"
    assert memory.category == "general"


@pytest.mark.asyncio
async def test_search(store):
    await store.write(Memory(content="python is great", category="general"))
    await store.write(Memory(content="rust is fast", category="general"))
    results = await store.search("python")
    assert len(results) >= 1
    assert any("python" in m.content for m in results)


@pytest.mark.asyncio
async def test_list_by_category(store):
    await store.write(Memory(content="fact 1", category="project"))
    await store.write(Memory(content="fact 2", category="user"))
    await store.write(Memory(content="fact 3", category="project"))

    project_memories = await store.list(category="project")
    assert len(project_memories) == 2

    all_memories = await store.list(category=None)
    assert len(all_memories) == 3


@pytest.mark.asyncio
async def test_delete(store):
    memory_id = await store.write(Memory(content="to delete", category="general"))
    await store.delete(memory_id)
    memory = await store.read(memory_id)
    assert memory is None
