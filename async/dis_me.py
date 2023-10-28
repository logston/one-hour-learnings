
async def return_me():
    return 42

async def await_me():
    await return_me()

# ➜  async git:(main) ✗ python3 -i dis_me.py
# >>> import dis
# >>> dis.dis(await_me)
#   5           0 RETURN_GENERATOR
#               2 POP_TOP
#               4 RESUME                   0

#   6           6 LOAD_GLOBAL              1 (NULL + return_me)
#              18 PRECALL                  0
#              22 CALL                     0
#              32 GET_AWAITABLE            0
#              34 LOAD_CONST               0 (None)
#         >>   36 SEND                     3 (to 44)
#              38 YIELD_VALUE
#              40 RESUME                   3
#              42 JUMP_BACKWARD_NO_INTERRUPT     4 (to 36)
#         >>   44 POP_TOP
#              46 LOAD_CONST               0 (None)
#              48 RETURN_VALUE
# >>> dis.dis(return_me)
#   2           0 RETURN_GENERATOR
#               2 POP_TOP
#               4 RESUME                   0

#   3           6 LOAD_CONST               1 (42)
#               8 RETURN_VALUE
# >>>
# >>> def basic():
# ...   return 42
# ...
# >>> dis.dis(basic)
#   1           0 RESUME                   0

#   2           2 LOAD_CONST               1 (42)
#               4 RETURN_VALUE

# Interestingly, we have a RETURN_GENERATOR and POP_TOP call at the start of
# each "async def function".
#
# GET_AWAITABLE https://github.com/python/cpython/blob/3.11/Python/ceval.c#L2542C25-L2542C25
# YIELD_VALUE https://github.com/python/cpython/blob/3.11/Python/ceval.c#L2638
# That looks like were we truly pause.
# _PyFrame_GetGenerator(frame)->gi_frame_state = FRAME_SUSPENDED;
# Hmmm: SEND - https://github.com/python/cpython/blob/3.11/Python/ceval.c#L2577
