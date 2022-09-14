import itertools
from typing import TYPE_CHECKING

from pyspa.core.guards import CheckPayloadMismatch

if TYPE_CHECKING:
    from starlite.types import Guard


def resolve_id_guards(id_guard: str | tuple[str, str] | list[str | tuple[str, str]]) -> list["Guard"]:
    """Resolves guards by ID.

    Parameters
    ----------
    id_guard a guard id or collection of guard ids

    Returns
    -------
    resolved guards.
    """
    if isinstance(id_guard, str):
        return [CheckPayloadMismatch("id", id_guard).__call__]

    if isinstance(id_guard, tuple):
        return [CheckPayloadMismatch(*id_guard)]

    return list(itertools.chain.from_iterable(resolve_id_guards(t) for t in id_guard))
