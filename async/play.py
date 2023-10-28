import asyncio

# I have an hour: Time boxed learnings.


async def await_me(*_):
    print('in await_me')
    # import pdb;pdb.set_trace()
    await asyncio.sleep(10_000)
    print('done with await_me')


async def return_me(*args):
    print('in return_me', *args)
    return 42


async def wrapper1():
    val = await await_me(print('in wrapper 1'))
    print('Returned from await me', val)


async def wrapper2():
    val = await return_me(print('in wrapper 2'))
    print('Returned from return me', val)


asyncio.run(wrapper1())

# So in wrapper1, we do get a delay between await_me and done with await_me. We
# also see that "in await_me" is printed without delay after "in wrapper1".
# Thus we can say that args are evaluated befroe being passed to the async def
# function.
#     in wrapper 1
#     in await_me
#     ... 1 second delay
#     done with await_me
#     Returned from await me None

# A question still stands: Does the whole line get paused when Python sees the
# await keyword? Core question: Where does Python actually pause and hand back
# control to the event loop?


# Throwing in a pdb block, we see that we jump into:
# asyncio/tasks.py at line 627:
#   Fun fact that on my machine the loop we created is a selector loop:
#        <_UnixSelectorEventLoop running=True closed=False debug=False>
#   We seem to create a future and tell the loop to "call it" (?) later (after the delay).
#   I could see this is how we hand back control. Tell the loop to do something later
#   and then return. Then the loop could some how determine the coroutine we
#   are in and simply stop working (maybe?).
#
#  But get this, there's a "return await future" below. What is that!?
#
#  In asyncio/base_events.py(745)call_at(), we add to our TODO queue (heap queue).
#  # And we return. But how do we pause?
#
#   Should we dis the "sleep" function to figure out what is happening with
#   that "return await future" call?
#
# Let's first up the ante with our sleep: 1 -> 10k. I don't want to be missing
# something because of small numbers.

# WOw! if we step at 'return await future' we run up the call stack.

# > /opt/homebrew/Cellar/python@3.11/3.11.5/Frameworks/Python.framework/Versions/3.11/lib/python3.11/asyncio/tasks.py(639)sleep()
# -> return await future
# (Pdb) s
# --Return--
# > /opt/homebrew/Cellar/python@3.11/3.11.5/Frameworks/Python.framework/Versions/3.11/lib/python3.11/asyncio/tasks.py(639)sleep()-><Future pending>
# -> return await future
# (Pdb) s
# --Return--
# > /Users/paul/Code/async/play.py(9)await_me()-><Future pending>
# -> await asyncio.sleep(10_000)
# (Pdb) s
# --Return--
# > /Users/paul/Code/async/play.py(19)wrapper1()-><Future pending>
# -> val = await await_me(print('in wrapper 1'))
# (Pdb) s
# > /opt/homebrew/Cellar/python@3.11/3.11.5/Frameworks/Python.framework/Versions/3.11/lib/python3.11/asyncio/events.py(95)_run()
# -> self = None  # Needed to break cycles when an exception occurs.

### WE eventually hit self._run_once() and pause

# > /opt/homebrew/Cellar/python@3.11/3.11.5/Frameworks/Python.framework/Versions/3.11/lib/python3.11/asyncio/base_events.py(1906)_run_once()
# -> for i in range(ntodo):
# (Pdb) l
# 1901            # Note: We run all currently scheduled callbacks, but not any
# 1902            # callbacks scheduled by callbacks run this time around --
# 1903            # they will be run the next time (after another I/O poll).
# 1904            # Use an idiom that is thread-safe without using locks.
# 1905            ntodo = len(self._ready)
# 1906 ->         for i in range(ntodo):
# 1907                handle = self._ready.popleft()
# 1908                if handle._cancelled:
# 1909                    continue
# 1910                if self._debug:
# 1911                    try:
# (Pdb) p ntodo
# 1
# (Pdb) n
# > /opt/homebrew/Cellar/python@3.11/3.11.5/Frameworks/Python.framework/Versions/3.11/lib/python3.11/asyncio/base_events.py(1923)_run_once()
# -> handle = None  # Needed to break cycles when an exception occurs.
# (Pdb) l
# 1918                                           _format_handle(handle), dt)
# 1919                    finally:
# 1920                        self._current_handle = None
# 1921                else:
# 1922                    handle._run()
# 1923 ->         handle = None  # Needed to break cycles when an exception occurs.
# 1924
# 1925        def _set_coroutine_origin_tracking(self, enabled):
# 1926            if bool(enabled) == bool(self._coroutine_origin_tracking_enabled):
# 1927                return
# 1928
# (Pdb) n
# --Return--
# > /opt/homebrew/Cellar/python@3.11/3.11.5/Frameworks/Python.framework/Versions/3.11/lib/python3.11/asyncio/base_events.py(1923)_run_once()->None
# -> handle = None  # Needed to break cycles when an exception occurs.
# (Pdb) n
# > /opt/homebrew/Cellar/python@3.11/3.11.5/Frameworks/Python.framework/Versions/3.11/lib/python3.11/asyncio/base_events.py(608)run_forever()
# -> if self._stopping:
# (Pdb) l
# 603                                        finalizer=self._asyncgen_finalizer_hook)
# 604
# 605                 events._set_running_loop(self)
# 606                 while True:
# 607                     self._run_once()
# 608  ->                 if self._stopping:
# 609                         break
# 610             finally:
# 611                 self._stopping = False
# 612                 self._thread_id = None
# 613                 events._set_running_loop(None)
# (Pdb) n
# > /opt/homebrew/Cellar/python@3.11/3.11.5/Frameworks/Python.framework/Versions/3.11/lib/python3.11/asyncio/base_events.py(606)run_forever()
# -> while True:
# (Pdb) n
# > /opt/homebrew/Cellar/python@3.11/3.11.5/Frameworks/Python.framework/Versions/3.11/lib/python3.11/asyncio/base_events.py(607)run_forever()
# -> self._run_once()
# (Pdb) l
# 602                 sys.set_asyncgen_hooks(firstiter=self._asyncgen_firstiter_hook,
# 603                                        finalizer=self._asyncgen_finalizer_hook)
# 604
# 605                 events._set_running_loop(self)
# 606                 while True:
# 607  ->                 self._run_once()
# 608                     if self._stopping:
# 609                         break
# 610             finally:
# 611                 self._stopping = False
# 612                 self._thread_id = None
# (Pdb) n


# We get into _run_once and somethings are interesting...
# we have a MAXIMUM_SELECT_TIMEOUT of 86400 or one day.

# And here we have something that pauses the thread:  event_list = self._selector.select(timeout)


# Paused: Here's where we've gone as far as PDB will take us...

# > /opt/homebrew/Cellar/python@3.11/3.11.5/Frameworks/Python.framework/Versions/3.11/lib/python3.11/selectors.py(561)select()
# -> kev_list = self._selector.control(None, max_ev, timeout)
# (Pdb) l
# 556                 # behavior with the other selector classes, we prevent that here
# 557                 # (using max). See https://bugs.python.org/issue29255
# 558                 max_ev = max(len(self._fd_to_key), 1)
# 559                 ready = []
# 560                 try:
# 561  ->                 kev_list = self._selector.control(None, max_ev, timeout)
# 562                 except InterruptedError:
# 563                     return ready
# 564                 for kev in kev_list:
# 565                     fd = kev.ident
# 566                     flag = kev.filter
# (Pdb) s

# ...
# (Pdb) p self._selector
# <select.kqueue object at 0x100c24bf0>

# https://man.freebsd.org/cgi/man.cgi?query=kqueue&sektion=2
# https://docs.python.org/3/library/select.html#kqueue-objects
# https://docs.python.org/3/library/select.html#select.kqueue.control



# 'return await future' -> 'return (await future)' -> 'val = (await future) \n return val'
# This reinforces the fact that Python does something special when it hits an
# await, it passes control back to the outer context. In this case, the wrapper async def function.
# Keeps passing until it hits loop code.

# Is this what computer science is? The testing of hypothesis to re-disocver
# our own code? Seems like we are not instructing ourselves well enough if 1/2
# our time is spent rediscovering what others have *written* ( not even
# discovered but written). We are not even dicovering mysteries of the
# universe. We are solving problems we created. Seems lack luster.

# Seems like the future or awaitable (sleep in this case) was responsible for
# creating a future on the event loop and then awaiting the future. Futures are
# special I guess in that await does not need to wait for them. await knows that
# they are on the event loop and will be dealt with when they are ready so it
# just passes control back to the outer context (?).
