from litestar import post
from litestar.testing import create_test_client
from pydantic import BaseModel


class Foo(BaseModel):
    x: int


@post("", type_decoders=[(lambda x: x is Foo, lambda t, v: Foo(x=42))])
async def webhook(data: Foo) -> Foo:
    return data


with create_test_client([webhook]) as client:
    print(client.post("/", json={"x": 1}).json())
