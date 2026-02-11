"""Unit tests for the contact collection AgentTask."""

import sys

import pytest

sys.path.insert(0, "src")


@pytest.mark.unit
class TestContactInfoResult:
    """Tests for ContactInfoResult dataclass."""

    def test_contact_info_result_stores_all_fields(self):
        """ContactInfoResult should store all fields."""
        from tasks.collect_contact import ContactInfoResult

        result = ContactInfoResult(
            first_name="John",
            last_name="Smith",
            phone_number="4075551234",
        )
        assert result.first_name == "John"
        assert result.last_name == "Smith"
        assert result.phone_number == "4075551234"

    def test_contact_info_result_equality(self):
        """Two results with same data should be equal (dataclass)."""
        from tasks.collect_contact import ContactInfoResult

        r1 = ContactInfoResult("John", "Smith", "4075551234")
        r2 = ContactInfoResult("John", "Smith", "4075551234")
        assert r1 == r2

    def test_contact_info_result_different_values(self):
        """Results with different data should not be equal."""
        from tasks.collect_contact import ContactInfoResult

        r1 = ContactInfoResult("John", "Smith", "4075551234")
        r2 = ContactInfoResult("Jane", "Doe", "5551234567")
        assert r1 != r2


@pytest.mark.unit
class TestCollectContactInfoTask:
    """Tests for CollectContactInfoTask."""

    def test_task_is_importable(self):
        """Task class should be importable."""
        from tasks.collect_contact import CollectContactInfoTask

        assert CollectContactInfoTask is not None

    def test_task_has_correct_instructions(self):
        """Task instructions should mention one question at a time."""
        from tasks.collect_contact import CollectContactInfoTask

        task = CollectContactInfoTask()
        assert "ONE question" in task.instructions

    def test_task_initializes_with_none_chat_ctx(self):
        """Task should accept None chat_ctx parameter."""
        from tasks.collect_contact import CollectContactInfoTask

        task = CollectContactInfoTask(chat_ctx=None)
        assert task is not None

    def test_task_has_record_contact_info_tool(self):
        """Task should have record_contact_info as a tool."""
        from tasks.collect_contact import CollectContactInfoTask

        task = CollectContactInfoTask()
        # Tools are extracted from methods decorated with @function_tool
        # Check that the task has tools
        assert hasattr(task, "tools")
        tool_ids = [tool.id for tool in task.tools]
        assert "record_contact_info" in tool_ids

    def test_module_exports(self):
        """Module should export expected classes."""
        from tasks.collect_contact import CollectContactInfoTask, ContactInfoResult

        assert CollectContactInfoTask is not None
        assert ContactInfoResult is not None
