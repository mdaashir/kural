"""Shared pytest fixtures for Kural's test suite.

All fixtures here are mic-free, GPU-free, model-free, and network-free.
Tests that require real hardware must be marked with @pytest.mark.gpu or
@pytest.mark.mic and are excluded from CI.
"""
