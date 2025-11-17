from email_assistant.core.schemas import EmailState
from fastmcp import Client

async def send_email_node(state: EmailState) -> dict:
    """
    Async node: send email using MCP async client.
    """
    try:
        body = state.generated_body or state.text

        config = {
            "mcpServers": {
                "server_name": {
                    "transport": "stdio",
                    # "transport": "http",
                    # "transport": "streamable-http",                    
                    "url": "http://localhost:6277/mcp",
                    # "headers": {"Authorization": "Bearer token"},
                },
            }
        }
        # client = Client(config)

        from fastmcp.client.transports import StdioTransport

        transport = StdioTransport(
            command="sh",
            args=["/Users/ivamilojkovic/Projects/ai-personal-assistant/email-assistant/run_gmail_mcp_server_conda.sh"]
        )
        client = Client(transport)

        # client = Client("http://localhost:6277/mcp", transport="http")
        # client = Client(transport="stdio")

        #########
        # import pdb; pdb.set_trace()
        #########

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
