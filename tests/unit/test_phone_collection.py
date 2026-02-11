"""Unit tests for DTMF phone collection utility."""

import sys

import pytest

sys.path.insert(0, "src")


@pytest.mark.unit
class TestPhoneCollectionUtility:
    """Unit tests for phone collection utility functions."""

    def test_is_sip_caller_returns_false_without_context(self):
        """Without job context, should return False."""
        from tasks.phone_collection import is_sip_caller

        assert is_sip_caller() is False

    @pytest.mark.asyncio
    async def test_collect_phone_returns_none_on_import_error(self):
        """When GetDtmfTask import fails, should return None gracefully."""
        from tasks.phone_collection import collect_phone_number_dtmf

        # Without a real chat_ctx, this should fail gracefully
        result = await collect_phone_number_dtmf(None)
        assert result is None

    def test_phone_collection_module_importable(self):
        """Module should be importable without errors."""
        from tasks import phone_collection

        assert hasattr(phone_collection, "collect_phone_number_dtmf")
        assert hasattr(phone_collection, "is_sip_caller")

    def test_tasks_package_importable(self):
        """Tasks package should be importable."""
        import tasks

        assert tasks is not None
