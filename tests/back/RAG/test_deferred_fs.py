"""Filesystem removals must follow the transaction, not the call order.

Deleting a file cannot be rolled back, so a removal issued while a transaction
is open leaves surviving rows pointing at nothing when that transaction fails.
These tests pin the guarantee down at the primitive, so no call site has to be
audited for it one at a time.
"""

import os

import pytest
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from DashAI.back.services.RAG.deferred_fs import remove_after_commit, remove_now

Base = declarative_base()


class Row(Base):
    """A stand-in for whatever row a file belongs to."""

    __tablename__ = "deferred_fs_row"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)


@pytest.fixture
def db():
    """An isolated in-memory session."""
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()
    engine.dispose()


@pytest.fixture
def a_file(tmp_path):
    """A file on disk, and its path."""
    path = tmp_path / "artifact.bin"
    path.write_bytes(b"contents")
    return str(path)


@pytest.fixture
def a_directory(tmp_path):
    """A populated directory, and its path."""
    folder = tmp_path / "matrices"
    folder.mkdir()
    (folder / "matrix.npy").write_bytes(b"0123")
    return str(folder)


def test_a_queued_path_survives_until_the_commit(db, a_file):
    """Nothing is removed while the transaction is still open."""
    db.add(Row(id=1, name="keep"))
    remove_after_commit(db, a_file)

    assert os.path.exists(a_file), "removed before the transaction committed"

    db.commit()
    assert not os.path.exists(a_file)


def test_a_rollback_keeps_the_file(db, a_file):
    """The rows that justified the removal survive, so the file must too."""
    db.add(Row(id=1, name="doomed"))
    remove_after_commit(db, a_file)

    db.rollback()

    assert os.path.exists(a_file), (
        "the transaction failed, so the row still points at this file"
    )

    # And the queue is not carried into the next transaction.
    db.add(Row(id=2, name="unrelated"))
    db.commit()
    assert os.path.exists(a_file)


def test_successive_commits_each_take_only_their_own(db, tmp_path):
    """One session that commits repeatedly -- a job doing several operations.

    The listener is registered once, on the Session class, so it never
    unregisters; what keeps successive commits honest is that the queue lives in
    ``Session.info`` and is drained on each one.
    """
    paths = []
    for index in range(3):
        path = tmp_path / f"step{index}.bin"
        path.write_bytes(b"x")
        paths.append(str(path))

    for index, path in enumerate(paths):
        db.add(Row(id=index + 1, name=f"step{index}"))
        remove_after_commit(db, path)
        db.commit()

        assert not os.path.exists(path), "this commit's own path was not removed"
        for later in paths[index + 1 :]:
            assert os.path.exists(later), "a later commit's path was removed early"


def test_a_commit_with_an_empty_queue_is_a_no_op(db, a_file):
    """A second commit must not re-run the removals the first one did."""
    db.add(Row(id=1, name="first"))
    remove_after_commit(db, a_file)
    db.commit()
    assert not os.path.exists(a_file)

    # Re-create it: if the queue were not drained, this commit would remove it.
    with open(a_file, "wb") as handle:
        handle.write(b"recreated")
    db.add(Row(id=2, name="second"))
    db.commit()
    assert os.path.exists(a_file)


def test_a_savepoint_rollback_keeps_the_outer_queue(db, a_file):
    """Rolling back a savepoint must not cancel the whole transaction's queue.

    Both ``after_rollback`` and ``after_soft_rollback`` fire for a savepoint, so
    treating either as "the transaction failed" drops paths the enclosing
    transaction is still going to commit.
    """
    db.add(Row(id=1, name="outer"))
    remove_after_commit(db, a_file)

    savepoint = db.begin_nested()
    db.add(Row(id=2, name="inner"))
    savepoint.rollback()

    assert os.path.exists(a_file), "removed while the outer transaction lived"

    db.commit()
    assert not os.path.exists(a_file), (
        "the savepoint rollback swallowed the outer transaction's queue"
    )


def test_a_committed_savepoint_still_defers_to_the_outer_commit(db, a_file):
    """A path queued inside a savepoint waits for the real commit."""
    savepoint = db.begin_nested()
    db.add(Row(id=1, name="inner"))
    remove_after_commit(db, a_file)
    savepoint.commit()

    assert os.path.exists(a_file), "a savepoint commit is not the transaction"

    db.commit()
    assert not os.path.exists(a_file)


def test_directories_and_files_are_both_handled(db, a_file, a_directory):
    """Artifact folders and document blobs travel the same queue."""
    remove_after_commit(db, a_directory)
    remove_after_commit(db, a_file)
    db.commit()

    assert not os.path.exists(a_directory)
    assert not os.path.exists(a_file)


def test_queueing_nothing_is_harmless(db):
    """A nullable column can be queued without the caller guarding it."""
    remove_after_commit(db, None)
    remove_after_commit(db, "")
    db.commit()  # must not raise


def test_a_missing_path_does_not_break_the_commit(db, tmp_path):
    """A path already gone is not an error: cleanup runs more than once."""
    remove_after_commit(db, str(tmp_path / "never-existed"))
    db.add(Row(id=1, name="fine"))
    db.commit()

    assert db.query(Row).count() == 1


def test_each_session_carries_its_own_queue(a_file, tmp_path):
    """One session committing must not remove another's pending paths."""
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    first, second = factory(), factory()

    other = tmp_path / "second.bin"
    other.write_bytes(b"x")

    remove_after_commit(first, a_file)
    remove_after_commit(second, str(other))

    first.commit()
    assert not os.path.exists(a_file)
    assert os.path.exists(other), "the other session's queue was flushed too"

    second.commit()
    assert not os.path.exists(other)

    first.close()
    second.close()
    engine.dispose()


def test_remove_now_reports_rather_than_raises(tmp_path):
    """The immediate helper is best-effort, so cleanup never fails a request."""
    remove_now(str(tmp_path / "absent"))
    remove_now(None)
