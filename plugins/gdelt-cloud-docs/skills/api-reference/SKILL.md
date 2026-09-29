---
name: gdelt-cloud-api-reference
description: Find the documented GDELT Cloud endpoint, parameter schema, enum or response contract while designing or debugging an integration. Works without an account; does not retrieve live customer data.
---

# Answer contract questions from the reference

Discover the documentation MCP's current tools. Search for the exact endpoint or error code,
then read its reference or the relevant OpenAPI path. Prefer a precise schema excerpt over
loading the whole specification. If the docs connection is unavailable, use
https://docs.gdeltcloud.com/llms.txt to locate the relevant public page.

For an integration answer, identify the HTTP method/path, auth requirement, required parameters,
accepted types/enums, identifier spaces, time basis, pagination and expected response/error shape.
Distinguish closed enums from observed vocabulary. Keep examples small and use placeholders or
environment variables for keys. Do not request a production key just to explain a schema.

Do not present documentation examples as measured live results. This plugin has documentation
access only. A live query requires a separate authenticated data connector or a user-configured
REST client. If only some contract details are documented, state the uncertainty rather than
inventing fields, response counts or a successful deployment.

For MCP implementations, inspect the data server's live `_tool_get` schema when connected;
REST parameters and JSON bodies can differ from MCP arguments. Progressive execution uses
`<category>_tool_call(tool_name="...", tool_arguments={...})`, and authorized workspace writes
use the declared write wrapper. Discover the operation first; never invent an MCP equivalent
for an endpoint that has none.

Use a source link next to the answer so a builder can verify the contract. If documentation is
contradictory, report both specifics. Prepare feedback if useful; do not send a message to the
provider unless the user authorizes it.
