from openapi_schema_pydantic import Contact  # type: ignore
from starlite import OpenAPIConfig

from pyspa import __version__

config = OpenAPIConfig(
    title="pyspa",
    version=__version__,
    contact=Contact(name="Cody Fincher", email="cody@fincher.cloud"),
    description="Simple Single Page Application",
)
