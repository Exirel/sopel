"""Plugin objects' definition.

.. versionadded:: 8.1

The core of a plugin consists of several objects, either plugin callables or
plugin jobs. These objects are represented by instances of
:class:`PluginCallable` and :class:`PluginJob` respectively.

.. seealso::

    The :mod:`sopel.plugin`'s decorator create these objects directly.

.. important::

    This is all relatively new. Its usage and documentation is for Sopel core
    development and advanced developers. It is subject to rapid changes
    between versions without much (or any) warning.

    Do **not** build your plugin based on what is here, you do **not** need to.

"""
# Copyright 2025, Florian Strzelecki <florian.strzelecki@gmail.com>
#
# Licensed under the Eiffel Forum License 2.
from __future__ import annotations

import abc
import inspect
import re
from typing import (
    Any,
    Callable,
    Literal,
    override,
    Type,
    TYPE_CHECKING,
    TypeVar,
)

from typing_extensions import override

from sopel.config.core_section import COMMAND_DEFAULT_HELP_PREFIX
from sopel.lifecycle import deprecated


if TYPE_CHECKING:
    from sopel.bot import Sopel, SopelWrapper
    from sopel.config import Config
    from sopel.trigger import Trigger


TypedPluginObject = TypeVar('TypedPluginObject', bound='AbstractPluginObject')
"""A :class:`~typing.TypeVar` bound to :class:`AbstractPluginObject`.

When used in the :meth:`AbstractPluginObject.from_plugin_object` class method,
it means the return value must be an instance of the class used to call that
method and not a different subclass of ``AbstractRule``.

.. versionadded:: 8.1
"""


class AbstractPluginObject(abc.ABC):
    """Abstract definition of a plugin object.

    A plugin object encapsulates the logic and attributes required for a plugin
    to register and execute this object.

    .. versionadded:: 8.1
    """
    _sopel_callable = True

    plugin_name: str | None
    label: str | None
    threaded: bool
    doc: str | None

    @property
    @deprecated(
        reason='`rule_label` is replaced by the `label` attribute.',
        version='8.1',
        removed_in='9.0',
    )
    def rule_label(self):
        return self.label

    @property
    @deprecated(
        reason='`thread` is replaced by the `threaded` attribute.',
        version='8.1',
        removed_in='9.0',
    )
    def thread(self):
        # compatiblity property
        # TODO: remove in Sopel 9
        return self.threaded

    @classmethod
    def from_plugin_object(
        cls: Type[TypedPluginObject],
        obj: AbstractPluginObject,
    ) -> TypedPluginObject:
        """Convert a plugin ``obj`` to this type of plugin object.

        :param obj: the plugin object to convert from
        :return: an instance of the new plugin object from ``obj``

        This class method will create a new instance of plugin object based on
        ``obj``'s generic attributes (like its label) and the same callable,
        assuming ``obj`` is a different type of plugin object.

        .. seealso::

            The :py:deco:`~sopel.plugin.label` decorator returns a
            :class:`PluginGeneric` that needs to be converted into a plugin
            callable or a plugin job by this class method.

        """
        handler = cls(obj.get_handler())
        handler.plugin_name = obj.plugin_name
        handler.label = obj.label
        handler.threaded = obj.threaded
        handler.doc = obj.doc

        return handler

    @abc.abstractmethod
    def __init__(self, handler: Callable) -> None:
        ...

    @abc.abstractmethod
    def get_handler(self) -> Callable:
        """Return this plugin object's handler.

        :return: the plugin object's handler
        """


class PluginGeneric(AbstractPluginObject):
    @classmethod
    def ensure_callable(
        cls: Type[PluginGeneric],
        obj: Callable | AbstractPluginObject,
    ) -> AbstractPluginObject:
        """Ensure that ``obj`` is a proper plugin object.

        :param obj: a function or a plugin object
        :return: a properly defined plugin object

        If ``obj`` is already an instance of ``AbstractPluginObject``, it is
        returned as-is. Otherwise, a new ``PluginGeneric`` is created from it.

        .. note::

            Since a generic plugin object doesn't hold much value, it never
            converts a specific plugin object into a generic one as to prevent
            meta-data loss.

        """
        if isinstance(obj, AbstractPluginObject):
            return obj

        handler = cls(obj)

        # shared meta data
        handler.label = getattr(obj, 'rule_label', handler.label)
        handler.threaded = getattr(obj, 'thread', handler.threaded)

        return handler

    def __init__(self, handler: Callable) -> None:
        self._handler = handler

        # shared meta data
        self.plugin_name = None
        self.label = self._handler.__name__
        self.threaded = True
        self.doc = inspect.getdoc(self._handler)

    @override
    def get_handler(self) -> Callable:
        return self._handler


class PluginCallable(AbstractPluginObject):
    """Plugin callable, i.e. execute a plugin function when triggered.

    :param handler: a function to be called when the plugin callable is invoked
    """
    @property
    @deprecated(
        reason='`echo` is replaced by the `allow_echo` attribute.',
        version='8.1',
        removed_in='9.0',
    )
    def echo(self):
        return self.allow_echo

    @property
    @deprecated(
        reason='`event` is replaced by the `events` attribute.',
        version='8.1',
        removed_in='9.0',
    )
    def event(self):
        return self.events

    @property
    @deprecated(
        reason='`example` is replaced by the `examples` attribute.',
        version='8.1',
        removed_in='9.0',
    )
    def example(self):
        return self.examples

    @property
    @deprecated(
        reason='`rule` is replaced by the `rules` attribute.',
        version='8.1',
        removed_in='9.0',
    )
    def rule(self):
        return self.rules

    @classmethod
    def ensure_callable(
        cls: Type[PluginCallable],
        obj: Callable | AbstractPluginObject,
    ) -> PluginCallable:
        """Ensure that ``obj`` is a plugin callable.

        :param obj: a function or a plugin object
        :return: a properly defined plugin callable

        If ``obj`` is already an instance of ``AbstractPluginObject``, it
        converts it into a plugin callable. Otherwise, a new plugin callable is
        created, using the ``obj`` as its handler.
        """
        if isinstance(obj, cls):
            return obj

        if isinstance(obj, AbstractPluginObject):
            handler = cls.from_plugin_object(obj)
            obj = obj.get_handler()
        else:
            handler = cls(obj)

        # shared meta data
        handler.label = getattr(obj, 'rule_label', handler.label)
        handler.threaded = getattr(obj, 'thread', handler.threaded)

        # meta
        handler.allow_bots = getattr(obj, 'allow_bots', handler.allow_bots)
        handler.allow_echo = getattr(obj, 'echo', handler.allow_echo)
        handler.priority = getattr(obj, 'priority', handler.priority)
        handler.output_prefix = getattr(
            obj, 'output_prefix', handler.output_prefix)
        handler._docs = getattr(obj, '_docs', handler._docs)

        # rules
        handler.events = getattr(obj, 'event', handler.events)
        handler.ctcp = getattr(obj, 'ctcp', handler.ctcp)
        handler.rules = getattr(obj, 'rule', handler.rules)
        handler.rule_lazy_loaders = getattr(
            obj, 'rule_lazy_loaders', handler.rule_lazy_loaders)
        handler.find_rules = getattr(obj, 'find_rules', handler.find_rules)
        handler.search_rules = getattr(
            obj, 'search_rules', handler.search_rules)

        # urls
        handler.url_regex = getattr(obj, 'url_regex', handler.url_regex)
        handler.url_lazy_loaders = getattr(
            obj, 'url_lazy_loaders', handler.url_lazy_loaders)

        # named rules
        handler.commands = getattr(
            obj, 'commands', handler.commands)
        handler.nickname_commands = getattr(
            obj, 'nickname_commands', handler.nickname_commands)
        handler.action_commands = getattr(
            obj, 'action_commands', handler.action_commands)

        # rate limiting
        handler.user_rate = getattr(obj, 'user_rate', None)
        handler.channel_rate = getattr(obj, 'channel_rate', None)
        handler.global_rate = getattr(obj, 'global_rate', None)
        handler.user_rate_message = getattr(obj, 'user_rate_message', None)
        handler.channel_rate_message = getattr(
            obj, 'channel_rate_message', None)
        handler.global_rate_message = getattr(obj, 'global_rate_message', None)
        handler.default_rate_message = getattr(
            obj, 'default_rate_message', None)
        handler.unblockable = getattr(obj, 'unblockable', handler.unblockable)

        return handler

    @property
    def is_limitable(self) -> bool:
        """Check if the callable is subject to rate limiting.

        :return: ``True`` if it is subject to rate limiting

        Limitable callables aren't necessarily triggerable directly, but they
        all must pass through Sopel's rate-limiting machinery during
        dispatching.
        """
        allowed = any([
            self.rules,
            self.rule_lazy_loaders,
            self.find_rules,
            self.find_rules_lazy_loaders,
            self.search_rules,
            self.search_rules_lazy_loaders,
            self.event,
            self.ctcp,
            self.commands,
            self.nickname_commands,
            self.action_commands,
            self.url_regex,
            self.url_lazy_loaders,
        ])

        return allowed

    @property
    def is_triggerable(self) -> bool:
        """Check if the callable can handle the bot's triggers.

        :return: ``True`` if it can handle the bot's triggers

        A triggerable is a callable that will be used by the bot to handle a
        particular trigger (i.e. an IRC message): it can be a regex rule, an
        event, a CTCP command, a command, a nickname command, or an action
        command. However, it must not be a job or a URL callback.

        .. seealso::

            Many of the decorators defined in :mod:`sopel.plugin` make the
            decorated function a triggerable object.

        """
        forbidden = any([
            self.url_regex,
            self.url_lazy_loaders,
        ])

        allowed = any([
            self.rules,
            self.rule_lazy_loaders,
            self.find_rules,
            self.find_rules_lazy_loaders,
            self.search_rules,
            self.search_rules_lazy_loaders,
            self.event,
            self.ctcp,
            self.commands,
            self.nickname_commands,
            self.action_commands,
        ])

        return allowed and not forbidden

    @property
    def is_url_callback(self) -> bool:
        """Check if the callable can handle a URL callback.

        :return: ``True`` if it can handle a URL callback

        A URL callback handler is a callable that will be used by the bot to
        handle a particular URL in an IRC message.

        .. seealso::

            Both :func:`sopel.plugin.url` :func:`sopel.plugin.url_lazy` make
            the decorated function a URL callback handler.

        """
        allowed = any([
            self.url_regex,
            self.url_lazy_loaders,
        ])

        return allowed

    def __init__(
        self,
        handler: Callable[[SopelWrapper, Trigger], Any],
    ) -> None:
        self._handler = handler

        # shared meta data
        self.plugin_name: str | None = None
        self.label: str = self._handler.__name__
        self.threaded: bool = True
        self.doc = inspect.getdoc(self._handler)

        # documentation
        self.examples: list[dict] = []
        self._docs: dict = {}

        # rules
        self.events: list = []
        self.ctcp: list = []
        self.commands: list = []
        self.nickname_commands: list = []
        self.action_commands: list = []
        self.rules: list = []
        self.rule_lazy_loaders: list = []
        self.find_rules: list = []
        self.find_rules_lazy_loaders: list = []
        self.search_rules: list = []
        self.search_rules_lazy_loaders: list = []
        self.url_regex: list = []
        self.url_lazy_loaders: list = []

        # allow special conditions
        self.allow_bots: bool = False
        self.allow_echo: bool = False

        # how to run it
        self.priority: Literal['low', 'medium', 'high'] = 'medium'
        self.unblockable: bool = False

        # rate limiting
        self.user_rate: int | None = None
        self.channel_rate: int | None = None
        self.global_rate: int | None = None
        self.default_rate_message: str | None = None
        self.user_rate_message: str | None = None
        self.channel_rate_message: str | None = None
        self.global_rate_message: str | None = None

        # output management
        self.output_prefix: str = ''

    def __call__(
        self,
        bot: SopelWrapper,
        trigger: Trigger,
    ) -> Any:
        return self._handler(bot, trigger)

    @override
    def get_handler(self) -> Callable:
        return self._handler

    def setup(self, settings: Config) -> None:
        """Setup of the plugin callable.

        :param settings: the bot's configuration

        This method will be called by the bot before registering the callable.
        It ensures the value of various meta-data.
        """
        nick = settings.core.nick
        help_prefix = settings.core.help_prefix
        docs = []
        examples = []

        if self.is_limitable:
            self.user_rate = self.user_rate or 0
            self.channel_rate = self.channel_rate or 0
            self.global_rate = self.global_rate or 0

        if not self.is_triggerable and not self.is_url_callback:
            return

        if not self.events:
            self.events = ['PRIVMSG']
        else:
            self.events = [event.upper() for event in self.events]

        if self.ctcp:
            # Can be implementation-dependent
            _regex_type = type(re.compile(''))
            self.ctcp = [
                (ctcp_pattern
                    if isinstance(ctcp_pattern, _regex_type)
                    else re.compile(ctcp_pattern, re.IGNORECASE))
                for ctcp_pattern in self.ctcp
            ]

        if not any([
            self.commands,
            self.action_commands,
            self.nickname_commands,
        ]):
            # no need to handle documentation for non-command
            return

        docstring = inspect.getdoc(self._handler)
        if docstring:
            docs = docstring.splitlines()

        if self.examples:
            # If no examples are flagged as user-facing,
            # just show the first one like Sopel<7.0 did
            examples = [
                rec["example"]
                for rec in self.examples
                if rec["is_help"]
            ] or [self.examples[0]["example"]]

            for i, example in enumerate(examples):
                example = example.replace('$nickname', nick)
                if example[0] != help_prefix and not example.startswith(nick):
                    example = example.replace(
                        COMMAND_DEFAULT_HELP_PREFIX, help_prefix, 1)
                examples[i] = example

        if docs or examples:
            for command in self.commands + self.nickname_commands:
                self._docs[command] = (docs, examples)


class PluginJob(AbstractPluginObject):
    @property
    @deprecated(
        reason='`interval` is replaced by the `intervals` attribute.',
        version='8.1',
        removed_in='9.0',
    )
    def interval(self):
        return self.intervals

    @classmethod
    def ensure_callable(
        cls: Type[PluginJob],
        obj: Callable | AbstractPluginObject,
    ) -> PluginJob:
        """Ensure that ``obj`` is a plugin job.

        :param obj: a function or a plugin object
        :return: a properly defined plugin job

        If ``obj`` is already an instance of ``AbstractPluginObject``, it
        converts it into a plugin job. Otherwise, a new plugin job is created,
        using the ``obj`` as its handler.
        """
        if isinstance(obj, cls):
            return obj

        if isinstance(obj, AbstractPluginObject):
            handler = cls.from_plugin_object(obj)
            obj = obj.get_handler()
        else:
            handler = cls(obj)

        # jobs
        handler.intervals = getattr(obj, 'interval', handler.intervals)
        handler.threaded = getattr(obj, 'thread', handler.threaded)

        return handler

    def __init__(self, handler: Callable[[Sopel], Any]):
        self._handler = handler

        # shared meta data
        self.plugin_name: str | None = None
        self.label: str = self._handler.__name__
        self.threaded: bool = True
        self.doc = inspect.getdoc(self._handler)

        # job
        self.intervals: list = []

    def __call__(self, bot: Sopel) -> Any:
        return self._handler(bot)

    @override
    def get_handler(self) -> Callable:
        return self._handler

    def setup(self, settings: Config) -> None:
        """Optional setup.

        :param settings: the bot's configuration

        This method will be called by the bot before registering the job.

        .. note::

            This methods is a no-op. It exists for subclasses that may requires
            to perform operation before registration.

        """
