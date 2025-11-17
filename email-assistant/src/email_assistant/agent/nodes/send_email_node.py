from email_assistant.core.schemas import EmailState
from fastmcp import Client

async def send_email_node(state: EmailState) -> dict:
    """
    Async node: send email using MCP async client.
    """
    try:
        body = state.generated_body or state.text

        # Get MCP client from state
        client = state.mcp

        async with client:
            # Debug: list tools
            tools = await client.list_tools()
            print("Tools:", tools)

            # Call your MCP tool (name must match server-side tool)
            result = await client.call_tool("send_email", {
                "to": state.to,
                "subject": state.subject,
                "body": body,
                "cc": state.cc,
                "bcc": state.bcc,
            })

            print("send_email tool result:", result)

        return {
            **state.model_dump(),
            "status": "sent_successfully",
            "mcp_result": result
        }

    except Exception as e:
        return {
            **state.model_dump(),
            "status": "error",
            "error": f"Failed to send email: {e}"
        }
