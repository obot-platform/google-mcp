from unittest.mock import MagicMock, Mock, call

import pytest
from googleapiclient.errors import HttpError

from obot_gmail_mcp.apis.messages import list_messages, modify_message_labels


def test_modify_thread_labels_reports_added_and_removed_labels():
    service = MagicMock()
    service.users.return_value.messages.return_value.get.return_value.execute.return_value = {
        "threadId": "thread1"
    }
    service.users.return_value.threads.return_value.get.return_value.execute.return_value = {
        "id": "thread1",
        "messages": [{"id": "message1"}, {"id": "message2"}],
    }

    result = modify_message_labels(
        service,
        "message1",
        add_labels=["STARRED"],
        remove_labels=["UNREAD"],
        apply_action_to_thread=True,
    )

    assert "Added Labels: {'STARRED'}" in result
    assert "Removed Labels: {'UNREAD'}" in result


def test_list_messages_requests_only_the_requested_results():
    service = MagicMock()
    messages_api = service.users.return_value.messages.return_value
    messages_api.list.return_value.execute.return_value = {
        "messages": [{"id": str(i)} for i in range(100)]
    }

    messages = list_messages(service, "query", ["INBOX"], max_results=100)

    assert len(messages) == 100
    messages_api.list.assert_called_once_with(
        userId="me", q="query", labelIds=["INBOX"], maxResults=100
    )


def test_list_messages_with_zero_results_does_not_call_gmail():
    service = MagicMock()
    messages_api = service.users.return_value.messages.return_value

    messages = list_messages(service, "query", ["INBOX"], max_results=0)

    assert messages == []
    messages_api.list.assert_not_called()


def test_list_messages_uses_two_500_result_pages_for_1000_results():
    service = MagicMock()
    messages_api = service.users.return_value.messages.return_value
    messages_api.list.return_value.execute.side_effect = [
        {
            "messages": [{"id": str(i)} for i in range(500)],
            "nextPageToken": "next",
        },
        {"messages": [{"id": str(i)} for i in range(500, 1000)]},
    ]

    messages = list_messages(service, "query", ["INBOX"], max_results=1000)

    assert len(messages) == 1000
    assert messages_api.list.call_args_list == [
        call(userId="me", q="query", labelIds=["INBOX"], maxResults=500),
        call(
            userId="me",
            q="query",
            labelIds=["INBOX"],
            pageToken="next",
            maxResults=500,
        ),
    ]


def test_list_messages_requests_only_the_remaining_results_on_the_last_page():
    service = MagicMock()
    messages_api = service.users.return_value.messages.return_value
    messages_api.list.return_value.execute.side_effect = [
        {
            "messages": [{"id": str(i)} for i in range(500)],
            "nextPageToken": "next",
        },
        {"messages": [{"id": str(i)} for i in range(500, 550)]},
    ]

    messages = list_messages(service, "query", ["INBOX"], max_results=550)

    assert len(messages) == 550
    assert messages_api.list.call_args_list[1] == call(
        userId="me",
        q="query",
        labelIds=["INBOX"],
        pageToken="next",
        maxResults=50,
    )


def test_list_messages_truncates_an_oversized_response():
    service = MagicMock()
    messages_api = service.users.return_value.messages.return_value
    messages_api.list.return_value.execute.return_value = {
        "messages": [{"id": str(i)} for i in range(10)]
    }

    messages = list_messages(service, "query", ["INBOX"], max_results=3)

    assert messages == [{"id": "0"}, {"id": "1"}, {"id": "2"}]


def test_list_messages_stops_when_next_page_token_is_absent():
    service = MagicMock()
    messages_api = service.users.return_value.messages.return_value
    messages_api.list.return_value.execute.return_value = {"messages": [{"id": "1"}]}

    messages = list_messages(service, "query", ["INBOX"], max_results=500)

    assert messages == [{"id": "1"}]
    messages_api.list.assert_called_once()


def test_list_messages_without_a_limit_uses_500_result_pages():
    service = MagicMock()
    messages_api = service.users.return_value.messages.return_value
    messages_api.list.return_value.execute.side_effect = [
        {"messages": [{"id": "1"}], "nextPageToken": "next"},
        {"messages": [{"id": "2"}]},
    ]

    messages = list_messages(service, "query", ["INBOX"], max_results=None)

    assert messages == [{"id": "1"}, {"id": "2"}]
    assert [
        request.kwargs["maxResults"] for request in messages_api.list.call_args_list
    ] == [
        500,
        500,
    ]


def test_list_messages_preserves_http_errors():
    service = MagicMock()
    error = HttpError(Mock(status=403, reason="Forbidden"), b"Forbidden")
    service.users.return_value.messages.return_value.list.return_value.execute.side_effect = (
        error
    )

    with pytest.raises(HttpError) as exc_info:
        list_messages(service, "query", ["INBOX"], max_results=100)

    assert exc_info.value is error
