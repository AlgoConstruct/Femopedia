"""A mechanical guard against the bug class behind finding I1: a name listed
in @sensitive_variables(...) that the function never actually binds as a
local.

Django's SafeExceptionReporterFilter scrubs a traceback frame's locals by
looking up each name in the *bound* locals dict against the names the
decorator declared. A declared name the function never assigns to is not
wrong in a way Python complains about -- the decorator just accepts any
strings -- so nothing catches it short of reading every decorated view by
hand. auth_views.recover shipped exactly that bug: `replacement` held a
plaintext recovery code and the lines after it could raise, but
`replacement` was never named in the decorator (the reviewer's finding I1).

What this test proves, precisely: for every @sensitive_variables(...) call
below that names specific variables, each named variable is bound somewhere
in the function -- as a parameter, an assignment target, a for-loop target,
a with-as target, an except-as name, or a walrus target. It is a *static*
check (source is parsed with `ast`, nothing is executed), so it covers every
decorated view uniformly rather than requiring one hand-written
exception-triggering test per view (three of nine had one before this fix;
see I2).

What this test does NOT prove: it does not prove the decorator's list is
*complete*. A genuinely sensitive local that was never added to
@sensitive_variables at all -- the actual shape of the pre-fix I1 bug, where
`replacement` was bound but undeclared -- passes this test silently, because
there is nothing to check it against. Recognising that a given local *is* a
plaintext credential is a judgement call this test cannot make; it only
holds the decorator to its own word once someone has made that call.

A bare `@sensitive_variables()` (no arguments) marks *every* local sensitive
-- Django's own semantics -- so there are no specific names to check there;
those views are skipped rather than asserted on.
"""

import ast
import inspect

import pytest

from apps.accounts import account_views, auth_views, authentication, session_views, views

# Every callable in apps.accounts carrying @sensitive_variables, as of the
# accounts-core fix wave (9 total). Add new ones here as they are decorated.
DECORATED_VIEWS = [
    (views, "create_device"),
    (authentication.DeviceTokenAuthentication, "authenticate"),
    (auth_views, "signup"),
    (auth_views, "recover"),
    (auth_views, "password_reset"),
    (auth_views, "password_reset_confirm"),
    (account_views, "password_change"),
    (account_views, "device_revoke"),
    (session_views, "login"),
    (session_views, "logout"),
]


def _function_node(owner, name: str) -> ast.FunctionDef:
    source = inspect.getsource(owner)
    # dedent isn't needed: inspect.getsource on a module returns unindented
    # top-level source, and on a class returns the class block starting at
    # column 0 of its own `class` line.
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError(f"no function named {name!r} found in {owner!r}")


def _declared_sensitive_names(node: ast.FunctionDef) -> set[str] | None:
    """Names passed to @sensitive_variables(...) on this function, or None
    if it was decorated bare (@sensitive_variables()) -- Django then treats
    *all* locals as sensitive, so there is nothing to check by name."""
    for decorator in node.decorator_list:
        if not isinstance(decorator, ast.Call):
            continue
        func = decorator.func
        func_name = func.id if isinstance(func, ast.Name) else getattr(func, "attr", None)
        if func_name != "sensitive_variables":
            continue
        if not decorator.args:
            return None
        return {arg.value for arg in decorator.args if isinstance(arg, ast.Constant)}
    return set()


def _bound_names(node: ast.FunctionDef) -> set[str]:
    """Every name this function binds as a local: parameters, assignment
    targets (plain, augmented, annotated, walrus), for-loop targets,
    with-as targets, and except-as names."""
    names: set[str] = set()
    args = node.args
    for arglist in (args.posonlyargs, args.args, args.kwonlyargs):
        names.update(a.arg for a in arglist)
    if args.vararg:
        names.add(args.vararg.arg)
    if args.kwarg:
        names.add(args.kwarg.arg)

    class Visitor(ast.NodeVisitor):
        def visit_Name(self, inner):
            if isinstance(inner.ctx, (ast.Store,)):
                names.add(inner.id)
            self.generic_visit(inner)

        def visit_ExceptHandler(self, inner):
            if inner.name:
                names.add(inner.name)
            self.generic_visit(inner)

    Visitor().generic_visit(node)
    return names


@pytest.mark.parametrize(
    "owner,name",
    DECORATED_VIEWS,
    ids=[f"{getattr(o, '__name__', getattr(o, '__qualname__', o))}.{n}" for o, n in DECORATED_VIEWS],
)
def test_every_declared_sensitive_variable_is_actually_bound(owner, name):
    node = _function_node(owner, name)
    declared = _declared_sensitive_names(node)
    if declared is None:
        pytest.skip(f"{name} uses bare @sensitive_variables() -- all locals covered")

    bound = _bound_names(node)
    missing = declared - bound
    assert not missing, (
        f"{name}: @sensitive_variables names {missing} that the function "
        f"never binds as a local -- Django's traceback scrubber has "
        f"nothing to scrub for these names, so they do nothing"
    )
