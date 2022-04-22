"""Tests for the ``sopel.plugins.callables`` module."""
from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from sopel.plugins.callables import PluginCallable


if TYPE_CHECKING:
    from sopel.bot import SopelWrapper
    from sopel.trigger import Trigger


TMP_CONFIG = """
[core]
owner = testnick
nick = TestBot
alias_nicks =
    AliasBot
    SupBot
enable = coretasks
"""


@pytest.fixture
def tmpconfig(configfactory):
    return configfactory('test.cfg', TMP_CONFIG)


@pytest.fixture
def mockbot(tmpconfig, botfactory):
    return botfactory(tmpconfig)


def test_call(mockbot, triggerfactory):
    wrapped = triggerfactory.wrapper(
        mockbot, ':Foo!foo@example.com PRIVMSG #channel :test message')
    expected = 'test value: test message'

    def handler(bot: SopelWrapper, trigger: Trigger):
        return 'test value: %s' % str(trigger)

    plugin_callable = PluginCallable(handler)
    assert plugin_callable(wrapped, wrapped._trigger) == expected
