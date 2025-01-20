from uuid import UUID

from litestar.utils.signature import ParsedSignature

from app.lib.factory import create_filter_dependencies, create_filter_dependencies_by_type

val = create_filter_dependencies_by_type(
    {
        "id_filter": UUID,
        "search": True,
        "pagination_type": "limit_offset",
        "sort_field": "name",
        "sort_order": "asc",
    },
)
deps = create_filter_dependencies({"id_filter": UUID})

if __name__ == "__main__":
    sig = ParsedSignature.from_fn(val["id_filter"], {})
    sig2 = ParsedSignature.from_fn(deps, {})
    print("Hello, World!")
    print(sig)
    print(sig2)
    print(val)
    print(deps)
