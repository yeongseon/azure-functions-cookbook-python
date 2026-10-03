# OpenAPI Return-Type Inference Opt-Out

> **Trigger**: HTTP | **State**: stateless | **Guarantee**: request-response | **Difficulty**: intermediate

## Overview

This recipe demonstrates how `infer_return_types=False` prevents
`azure-functions-openapi` from turning a handler's return annotation into an
OpenAPI `200` response schema. The two handlers in
`examples/apis-and-ingress/openapi_inference_opt_out/` use the same Pydantic
return type so the generated-spec difference is visible.

## When to Use

- Your handler annotation describes an internal or transport type that should stay private.
- You want to write the public response contract explicitly with `responses=`.
- You need a per-handler exception to the default return-type inference behavior.

## When NOT to Use

- The return annotation is already the correct public `200` response model.
- You only need to override inference with an explicit `responses=` contract; explicit metadata already wins.
- You expect the flag to change runtime serialization; it changes OpenAPI metadata only.

## Architecture

```mermaid
flowchart LR
    annotation[GreetingResponse annotation] --> default[Default @openapi]
    annotation --> optout[@openapi infer_return_types=false]
    default --> schema[OpenAPI 200 schema]
    optout --> omitted[Generic object, no inferred model schema]
```

## Implementation

Inference is enabled by default:

```python
@openapi(
    route="/api/openapi/inference/default",
    method="get",
)
def inferred_greeting(req: func.HttpRequest) -> GreetingResponse:
    ...
```

Set the decorator's public `infer_return_types` parameter to `False` to keep the
same annotation out of the generated response contract:

```python
@openapi(
    route="/api/openapi/inference/opt-out",
    method="get",
    infer_return_types=False,
)
def opted_out_greeting(req: func.HttpRequest) -> GreetingResponse:
    ...
```

With inference enabled, the first operation contains a `200` JSON schema for
`GreetingResponse`. The opted-out operation retains the library's generic
object response, but contains no inferred `GreetingResponse` schema. To document
another schema instead, pass an explicit `responses=` value.

## Run Locally

```bash
cd examples/apis-and-ingress/openapi_inference_opt_out
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp local.settings.json.example local.settings.json
func start
```

```bash
curl "http://localhost:7071/api/openapi/inference/default?name=Ada"
curl "http://localhost:7071/api/openapi/inference/opt-out?name=Ada"
```

## Production Considerations

- Treat annotations as public schema by default; opt out deliberately where that is not appropriate.
- Keep runtime serialization separate from this documentation-only switch.
- Add `responses=` when consumers still need an explicit public response contract.

## Related Links

- [OpenAPI Return-Type Inference](./openapi-inference.md)
- [OpenAPI Validation Supersedes Inference](./openapi-supersedes.md)
- [Recipe source](https://github.com/yeongseon/azure-functions-cookbook-python/tree/main/examples/apis-and-ingress/openapi_inference_opt_out)
