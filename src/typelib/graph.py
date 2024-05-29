from __future__ import annotations

import collections
import dataclasses
import graphlib
import inspect
import typing

from typelib import classes, compat, constants, inspection, refs

__all__ = ("static_order", "itertypes", "get_type_graph")


@compat.cache
def static_order(t: type | str | refs.ForwardRef) -> typing.Iterable[TypeNode]:
    """Get an ordered iterable of types which resolve into the root type provided.

    Args:
        t: The type to extract an ordered stack from.
    """
    if isinstance(t, (str, refs.ForwardRef)):
        ref = refs.forwardref(t) if isinstance(t, str) else t
        t = refs.evaluate(ref)
        # We want to leverage the cache if possible, hence the recursive call.
        #   Shouldn't actually recurse more than once.
        return static_order(t)

    return [*itertypes(t)]


def itertypes(t: type | str | refs.ForwardRef) -> typing.Iterable[TypeNode]:
    """Iterate over the type-graph represented by `t` from edges to root.

    Args:
        t: The "root" type.

    Yields:
        :py:class:`TypeNode`

    Notes:
        We will build a graph of types with the given type `t` as the root node,
        then iterate from the outermost leaves back to the root using BFS.
    """
    if isinstance(t, (str, refs.ForwardRef)):  # pragma: no cover
        ref = refs.forwardref(t) if isinstance(t, str) else t
        t = refs.evaluate(ref)

    graph = get_type_graph(t)  # type: ignore[arg-type]
    yield from graph.static_order()


def get_type_graph(t: type) -> graphlib.TopologicalSorter[TypeNode]:
    """Get a directed graph of the type(s) this annotation represents,

    Args:
        t: A type annotation.

    Returns:
        :py:class:`graphlib.TopologicalSorter`
    """
    graph: graphlib.TopologicalSorter = graphlib.TopologicalSorter()
    root = TypeNode(t)
    stack = collections.deque([root])
    visited = {root.type}
    while stack:
        parent = stack.popleft()
        predecessors = []
        for var, child in _level(parent.type):
            # If no type was provided, there's no reason to do further processing.
            if child in (constants.empty, typing.Any):
                continue

            # Only subscripted generics or non-stdlib types can be cyclic.
            #   i.e., we may get `str` or `datetime` any number of times,
            #   that's not cyclic, so we can just add it to the graph.
            is_visited = child in visited
            is_subscripted = inspection.issubscriptedgeneric(child)
            is_stdlib = inspection.isstdlibtype(child)
            can_be_cyclic = is_subscripted or is_stdlib is False
            # We detected a cyclic type,
            #   wrap in a ForwardRef and don't add it to the stack
            #   This will terminate this edge to prevent infinite cycles.
            if is_visited and can_be_cyclic:
                refname = inspection.get_qualname(child)
                is_argument = var is not None
                module = getattr(child, "__module__", None)
                is_class = inspect.isclass(child)
                ref = refs.forwardref(
                    refname, is_argument=is_argument, module=module, is_class=is_class
                )
                node = TypeNode(ref, var=var, cyclic=True)
            # Otherwise, add the type to the stack and track that it's been seen.
            else:
                node = TypeNode(type=child, var=var)
                visited.add(node.type)
                stack.append(node)
            # Flag the type as a "predecessor" of the parent type.
            #   This lets us resolve child types first when we iterate over the graph.
            predecessors.append(node)
        # Add the parent type and its predecessors to the graph.
        graph.add(parent, *predecessors)

    return graph


@classes.slotted(dict=False, weakref=True)
@dataclasses.dataclass
class TypeNode:
    type: typing.Any
    var: str | None = None
    cyclic: bool = False

    def __hash__(self):
        return hash(self.type)


def _level(t: typing.Any) -> typing.Iterable[tuple[str | None, type]]:
    args = inspection.get_args(t)
    # Only pull annotations from the signature if this is a user-defined type.
    is_structured = inspection.isstructuredtype(t)
    members = inspection.get_type_hints(t, exhaustive=is_structured)
    return [*((None, t) for t in args), *(members.items())]  # type: ignore
