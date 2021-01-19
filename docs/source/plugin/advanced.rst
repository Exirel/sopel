.. _plugin-advanced:

======================
Advanced Tips & Tricks
======================

Now that you have the basic knowledges about plugins, you may have more
questions, or there is a specific need you want to fulfill but can't quite
grasp how to implement it. After all, this documentation alone can't cover
every possible case!

In this chapter, we'll try to share the many tips and tricks both core
developers and plugin authors have found over time.

If something is not in here, feel free to ask about it on our IRC channel, or
maybe open an issue with the solution you come up with for your own plugin.


Tracking events before/after the bot did
========================================

When a user joins a channel, or quits the server, Sopel will automatically
update the information about said user and channel. For example, when they
joins a channel, that information is recorded in
:attr:`bot.channels <sopel.bot.Sopel.channels>`, by adding a new 
:class:`User <sopel.tools.target.User>` object to the correct
:attr:`channel.users <sopel.tools.target.Channel.users>` dict.

That's all good until you want to do something before or after the change has
been recorded by Sopel: you need to be careful how you declare your rules.

Before Event
------------

To handle an event before Sopel records any change, you should use these
decorators together::

    @plugin.event('event-name')  # replace by your event
    @plugin.priority('high')     # ensure execution before Sopel
    @plugin.thread(False)        # ensure sequential execution
    @plugin.unblockable          # optional
    def before_event_name(bot, trigger):
        # the bot is not updated yet

The high priority and running the callable sequentially ensure together that
anything you do in your callable will be done **before** Sopel updates its
state: users won't be added or removed yet on JOIN/QUIT.

After Event
-----------

To handle an event after Sopel recorded any change, you should use these
decorators together::

    @plugin.event('event-name')  # replace by your event
    @plugin.priority('low')      # ensure execution after Sopel
    @plugin.thread(False)        # optional
    @plugin.unblockable          # optional
    def after_event_name(bot, trigger):
        # the bot has been updated already

The low priority is enough to ensure that anything you do in your callable will
be done **after** Sopel updated its state: users won't exist anymore after
a QUIT/PART event, and they will be available after a JOIN event.

Note that you don't specifically needs to use ``@plugin.thread(False)``, but
it is still recommended to prevent any race condition.
