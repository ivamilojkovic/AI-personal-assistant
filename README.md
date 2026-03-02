<div align="center">
  <h1>AI Personal Assistant</h1>
  <p>A modular AI assistant that manages emails and bookings using natural language.</p>
  <p>
    <img src="https://img.shields.io/badge/Python-3.13+-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
    <img src="https://img.shields.io/badge/Status-Active-00C851?style=for-the-badge"/>
  </p>
  <p>
    <img src="https://img.shields.io/badge/Email_Agent-✅_Ready-00C851?style=flat-square"/>
    <img src="https://img.shields.io/badge/Booking_Agent-🚧_Coming_Soon-FFA500?style=flat-square"/>
    <img src="https://img.shields.io/badge/Calendar_Agent-📋_Planned-lightgrey?style=flat-square"/>
  </p>
</div>

<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#overview">Overview</a>
      <ul>
        <li><a href="#built-with">Built With</a></li>
        <li><a href="#example-flow">Example Flow</a></li>
        <li><a href="#architecture">Architecture Layers</a></li>
      </ul>
    </li>
    <li><a href="#protocols">Protocols Deep Dive</a></li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
  </ol>
</details>

## Overview

A modular AI personal assistant system that uses natural language to manage your emails, bookings, and more. Built with agent orchestration technologies including Model Context Protocol (MCP), Agent-to-Agent (A2A) protocol, and LangGraph workflows. The AI Personal Assistant coordinates specialized AI assistants to help you:

  * Email Management - Draft, send, and classify emails with AI
  * Booking Management (coming soon) - Manage accommodations and reservations
  * Smart Orchestration - Intelligent routing to the right assistant
  * Seamless Integration - All agents work together via A2A protocol

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Example Flow

```
User: "Write a professional email to client@example.com about the project update"
  ↓
Orchestrator: 
  - Parses intent → "write_email"
  - Extracts parameters → {to, subject, tone, text}
  - Routes to Email Agent
  ↓
Email Agent:
  - Generates professional email using AI
  - Returns draft
  ↓
User: Receives AI-generated email draft ✅
```
<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Architecture Layers

#### Layer 1: User Interface
The entry point where users express their needs in natural language. No special syntax or commands required, just natural conversation like "Write an email to client@example.com about the project update." 
<div align="center">
  <img src="./images/ui_landing_page.png" alt="AI Personal Assistant UI" width="80%"/>
  <br/><br/>
</div>

#### Layer 2: Orchestrator (Coordination Layer)
The intelligent coordination hub that processes user requests and delegates to the appropriate specialist. Built using LangGraph for stateful workflow orchestration.
Components:

* Intent Parser
    Understands natural language using OpenAI GPT-4
    Extracts structured parameters from unstructured text
    Determines confidence level for the interpretation
    Example: "Write an email to client@example.com" → {intent: "write_email", to: "client@example.com"}

* Agent Router
    Maps intents to the appropriate specialized agent
    Validates that all required parameters are present
    Handles missing information by requesting clarification
    Maintains conversation context for multi-turn interactions

* Agent Client (Generic A2A)
    Implements A2A protocol for agent-to-agent communication
    Discovers agent capabilities via agent cards
    Calls appropriate skills on target agents
    Handles responses and error conditions

#### Layer 3: Specialized Assistants (Execution Layer)
Domain-specific AI agents that perform actual work using their specialized knowledge and tools.

<div align="center">
  <a href="./images/architecture.png">
    <img src="./images/architecture.png" alt="architecture image" width="60%"/>
  </a>
  <br/>
  <em>Figure 1 — System architecture overview</em>
</div>

#### Email Assistant 

* Connected via A2A protocol for communication with orchestrator
* Uses MCP for Gmail integration (compose, send, search, label)
* Implements two LangGraph workflows:

    1. Email writing workflow (draft generation vs. direct send)
    2. Email classification workflow (single vs. batch processing)

        Key Features:
        * Parallel Processing: Batch mode classifies multiple emails concurrently
        * MCP Integration: Direct Gmail API access via MCP tools
        * AI Classification: LLM analyzes email content for categorization

---

### Protocols Deep Dive

This project is built on two emerging open standards for AI agent systems: **A2A** for agent-to-agent communication, and **MCP** for agent-to-tool communication. Together they form the backbone of the entire assistant architecture.

---

#### Agent-to-Agent Protocol (A2A)

##### What is A2A?

The [Agent-to-Agent (A2A) protocol](https://a2a-protocol.org/latest/) is an open standard that defines how independent AI agents discover, communicate with, and delegate tasks to each other over HTTP. Before A2A, each project invented its own way for agents to talk. A2A standardizes this layer, much like HTTP standardized web communication.

The core ideas behind A2A are:

- **Agent Cards** — Every A2A-compliant agent publishes a machine-readable JSON descriptor (its "agent card") at a well-known URL (typically `/.well-known/agent.json`). This card declares the agent's name, description, capabilities, supported input/output formats, and the skills it can perform. Any other agent can fetch this card to discover what the agent can do — no hardcoding required.
- **Skills** — Discrete, named capabilities that an agent exposes (e.g., `write_email`, `classify_email`). Each skill has a defined input schema and output schema.
- **Tasks** — The unit of work in A2A. A client agent sends a Task to a server agent, which processes it and responds. Tasks can be synchronous (immediate response) or asynchronous (the client polls or receives a webhook).
- **Transport** — A2A runs over plain HTTP/JSON, making it firewall-friendly and easy to integrate with any infrastructure. Streaming responses are supported via Server-Sent Events (SSE).

```
Agent Card (/.well-known/agent.json)
{
  "name": "Email Assistant",
  "description": "Handles email drafting and classification",
  "skills": [
    {
      "id": "write_email",
      "name": "Write Email",
      "description": "Drafts or sends an email",
      "inputModes": ["text"],
      "outputModes": ["text"]
    },
    {
      "id": "classify_email",
      "name": "Classify Email",
      "description": "Categorizes one or more emails",
      "inputModes": ["text"],
      "outputModes": ["text"]
    }
  ]
}
```

##### How A2A is used here

In this project, A2A is the communication backbone between the **Orchestrator** and every **Specialist Agent**.

```
Orchestrator (A2A Client)                 Email Agent (A2A Server)
       │                                           │
       │  1. GET /.well-known/agent.json           │
       │ ──────────────────────────────────────►   │
       │  ◄──────────────────────────────────────  │
       │       Agent Card (skills, schemas)        │
       │                                           │
       │  2. POST /tasks/send                      │
       │  { skill: "write_email",                  │
       │    params: { to, subject, body, tone } }  │
       │ ──────────────────────────────────────►   │
       │                                           │
       │  3. Response (streamed via SSE)           │
       │  ◄──────────────────────────────────────  │
       │       { draft: "Dear client, ..." }       │
```

Concretely:

- The **Orchestrator** acts as a **generic A2A client**. After parsing user intent, it looks up which agent handles the identified skill, fetches that agent's card if not already cached, and dispatches a Task with the extracted parameters.
- The **Email Agent** acts as an **A2A server**, implemented with the A2A Python SDK. It registers its skills (`write_email`, `classify_email`) and their schemas at startup. When a Task arrives, the SDK routes it to the appropriate LangGraph workflow.
- Because the Orchestrator uses the A2A protocol generically (not hardcoded to the Email Agent), **adding a new specialist agent** (e.g., a Booking Agent) requires only registering its URL — no changes to the Orchestrator code.

---

#### Model Context Protocol (MCP)

##### What is MCP?

The [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) is an open standard that defines how AI models and agents interact with external tools, data sources, and services. Think of it as a universal adapter: instead of every agent writing custom integration code for every service (Gmail API, Slack API, databases, etc.), MCP defines a single interface that any compliant tool server can implement.

MCP operates on a **client-server model**:

- **MCP Server** — A lightweight process that wraps an external service and exposes its capabilities as a list of callable **tools** with defined input/output schemas. For example, an MCP server for Gmail might expose tools like `gmail_send_message`, `gmail_search_messages`, `gmail_create_label`, etc.
- **MCP Client** — The AI agent that connects to one or more MCP servers, discovers their tools, and calls them as needed during task execution.
- **Tool Discovery** — At connection time, the MCP client asks the server to list all available tools. The agent's LLM can then decide which tools to call and with what arguments, just as it would with native function-calling.
- **Transport** — MCP supports two transports: `stdio` (local subprocess, for development) and `SSE` over HTTP (for remote/production servers).

```
MCP Tool Schema Example (Gmail Send)
{
  "name": "gmail_send_message",
  "description": "Sends an email via Gmail",
  "inputSchema": {
    "type": "object",
    "properties": {
      "to":      { "type": "string", "description": "Recipient email" },
      "subject": { "type": "string" },
      "body":    { "type": "string" }
    },
    "required": ["to", "subject", "body"]
  }
}
```

##### How MCP is used here

In this project, MCP is the integration layer between the **Email Agent** and **Gmail**. The Email Agent does not call the Gmail REST API directly — instead it connects to a Gmail MCP server which exposes Gmail capabilities as tools.

```
Email Agent (MCP Client)                  Gmail MCP Server
       │                                         │
       │  1. Connect + list tools                │
       │ ─────────────────────────────────────►  │
       │  ◄───────────────────────────────────── │
       │    [gmail_send, gmail_search, ...]      │
       │                                         │
       │  2. LangGraph workflow runs             │
       │     LLM decides: call gmail_send_message│
       │ ─────────────────────────────────────►  │
       │    { to, subject, body }                │
       │                                         │
       │  3. MCP Server calls Gmail API          │
       │     and returns result                  │
       │  ◄───────────────────────────────────── │
       │    { messageId: "abc123", status: "ok" }│
```

Concretely, the Email Agent's LangGraph workflows use MCP in two places:

| Workflow | MCP Tools Used |
|---|---|
| **Email Writing** | `gmail_send_message` (direct send mode) or returns draft only |
| **Email Classification** | `gmail_search_messages`, `gmail_list_labels`, `gmail_create_label` |

The key benefit: if the project were to support Outlook instead of Gmail in the future, only the MCP server would need to be swapped — the Email Agent's LangGraph logic stays completely unchanged.

---

<br/>
<div align="center">
  <a href="./images/email_graphs.png">
    <img src="./images/email_graphs.png" alt="email graphs image" width="60%"/>
  </a>
  <br/>
  <em>Figure 2 — Email graphs (writing and classifying, respectively)</em>
</div>

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Built With

[![Python][Python]][Python-url]
[![LangChain][LangChain]][LangChain-url]
[![LangGraph][LangGraph]][LangGraph-url]
[![OpenAI][OpenAI]][OpenAI-url]
[![MCP][MCP]][MCP-url]
[![A2A][A2A]][A2A-url]
[![FastAPI][FastAPI]][FastAPI-url]
[![Pydantic][Pydantic]][Pydantic-url]

<table align="center">
  <thead>
    <tr>
      <th>Layer</th>
      <th>Technology</th>
      <th>Purpose</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>Orchestrator</strong></td>
      <td>LangGraph</td>
      <td>Workflow orchestration</td>
    </tr>
    <tr>
      <td></td>
      <td>OpenAI GPT-4</td>
      <td>Intent parsing</td>
    </tr>
    <tr>
      <td></td>
      <td>A2A SDK</td>
      <td>Agent communication</td>
    </tr>
    <tr>
      <td></td>
      <td>FastAPI</td>
      <td>HTTP server</td>
    </tr>
    <tr>
      <td><strong>Email Assistant</strong></td>
      <td>LangGraph</td>
      <td>Workflow orchestration</td>
    </tr>
    <tr>
      <td></td>
      <td>OpenAI GPT-4</td>
      <td>Email generation</td>
    </tr>
    <tr>
      <td></td>
      <td>A2A SDK</td>
      <td>Server implementation</td>
    </tr>
    <tr>
      <td></td>
      <td>MCP</td>
      <td>Gmail tool integration</td>
    </tr>
    <tr>
      <td><strong>Communication</strong></td>
      <td>A2A Protocol</td>
      <td>Inter-agent messaging</td>
    </tr>
    <tr>
      <td></td>
      <td>MCP</td>
      <td>Tool integration</td>
    </tr>
    <tr>
      <td></td>
      <td>HTTP/JSON</td>
      <td>Transport layer</td>
    </tr>
  </tbody>
</table>

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Getting Started

### Prerequisites

* Python 3.13 or higher
* OpenAI API key
* Gmail account (for email features)

### Installation

### Configuration
Copy the example environment file and fill in your credentials:
```
# .env.example

# OpenAI
OPENAI_API_KEY=your_openai_api_key_here

# Gmail / MCP
GMAIL_CLIENT_ID=your_gmail_client_id
GMAIL_CLIENT_SECRET=your_gmail_client_secret
GMAIL_REFRESH_TOKEN=your_gmail_refresh_token

# Agent ports
ORCHESTRATOR_PORT=8000
EMAIL_AGENT_PORT=8001
```
For Gmail credentials, follow the [Gmail OAuth2 setup guide](https://developers.google.com/gmail/api/quickstart/python).

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- MARKDOWN LINKS & IMAGES -->
[Python]: https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white
[Python-url]: https://www.python.org/

[LangChain]: https://img.shields.io/badge/🦜_LangChain-121212?style=for-the-badge
[LangChain-url]: https://github.com/langchain-ai/langchain

[LangGraph]: https://img.shields.io/badge/LangGraph-FF4B4B?style=for-the-badge&logo=graphql&logoColor=white
[LangGraph-url]: https://github.com/langchain-ai/langgraph

[OpenAI]: https://img.shields.io/badge/OpenAI-412991?style=for-the-badge&logo=openai&logoColor=white
[OpenAI-url]: https://openai.com/

[MCP]: https://img.shields.io/badge/MCP-00A67E?style=for-the-badge&logo=modelcontextprotocol&logoColor=white
[MCP-url]: https://modelcontextprotocol.io/

[A2A]: https://img.shields.io/badge/A2A_Protocol-FF6B6B?style=for-the-badge&logoColor=white
[A2A-url]: https://a2a-protocol.org/latest/

[FastAPI]: https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white
[FastAPI-url]: https://fastapi.tiangolo.com/

[Pydantic]: https://img.shields.io/badge/Pydantic-E92063?style=for-the-badge&logo=pydantic&logoColor=white
[Pydantic-url]: https://docs.pydantic.dev/
