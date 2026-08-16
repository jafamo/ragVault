from app.repositories.chat_repo import ChatSessionRepository


def test_create_and_get_session():
    chat_repo = ChatSessionRepository()

    session = chat_repo.create_session()

    assert chat_repo.get_session(session.id).id == session.id


def test_get_unknown_session_returns_none():
    assert ChatSessionRepository().get_session("no-existe") is None


def test_list_sessions_includes_created_session():
    chat_repo = ChatSessionRepository()
    session = chat_repo.create_session()

    sessions = chat_repo.list_sessions()

    assert any(s.id == session.id for s in sessions)


def test_delete_session_removes_it_and_cascades_messages():
    chat_repo = ChatSessionRepository()
    session = chat_repo.create_session()
    chat_repo.add_message(session.id, role="user", content="hola")

    deleted = chat_repo.delete_session(session.id)

    assert deleted is True
    assert chat_repo.get_session(session.id) is None
    assert chat_repo.list_messages(session.id) == []


def test_delete_unknown_session_returns_false():
    assert ChatSessionRepository().delete_session("no-existe") is False


def test_add_message_and_list_messages_in_order():
    chat_repo = ChatSessionRepository()
    session = chat_repo.create_session()

    chat_repo.add_message(session.id, role="user", content="pregunta")
    chat_repo.add_message(
        session.id, role="assistant", content="respuesta", model_used="llama3.1:8b", sources="{}"
    )

    messages = chat_repo.list_messages(session.id)

    assert [m.role for m in messages] == ["user", "assistant"]
    assert messages[1].model_used == "llama3.1:8b"
    assert messages[1].sources == "{}"


def test_add_message_to_unknown_session_returns_none():
    assert ChatSessionRepository().add_message("no-existe", role="user", content="x") is None


def test_add_message_updates_session_updated_at():
    chat_repo = ChatSessionRepository()
    session = chat_repo.create_session()
    original_updated_at = session.updated_at

    chat_repo.add_message(session.id, role="user", content="hola")

    assert chat_repo.get_session(session.id).updated_at >= original_updated_at


def test_set_title_if_empty_sets_title():
    chat_repo = ChatSessionRepository()
    session = chat_repo.create_session()

    chat_repo.set_title_if_empty(session.id, "Título generado")

    assert chat_repo.get_session(session.id).title == "Título generado"


def test_set_title_if_empty_does_not_overwrite_existing_title():
    chat_repo = ChatSessionRepository()
    session = chat_repo.create_session()
    chat_repo.set_title_if_empty(session.id, "Primer título")

    chat_repo.set_title_if_empty(session.id, "Segundo título")

    assert chat_repo.get_session(session.id).title == "Primer título"
