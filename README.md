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
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#acknowledgments">Acknowledgments</a></li>
  </ol>
</details>

## Overview

A modular AI personal assistant system that uses natural language to manage your emails, bookings, and more. Built with cutting-edge agent orchestration technologies including Model Context Protocol (MCP), Agent-to-Agent (A2A) protocol, and LangGraph workflows. The AI Personal Assistant coordinates specialized AI assistants to help you:

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
The entry point where users express their needs in natural language. No special syntax or commands required—just natural conversation like "Write an email to client@example.com about the project update."

#### Layer 2: Orchestrator (Coordination Layer)
The intelligent coordination hub that processes user requests and delegates to the appropriate specialist. Built using LangGraph for stateful workflow orchestration.
Components:

* Intent Parser
    Understands natural language using OpenAI GPT-4
    Extracts structured parameters from unstructured text
    Determines confidence level for the interpretation
    Example: "Write an email to alice@example.com" → {intent: "write_email", to: "alice@example.com"}

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

_Below is an example of how you can instruct your audience on installing and setting up your app. This template doesn't rely on any external dependencies or services._

1. Get a free API Key at [https://example.com](https://example.com)
2. Clone the repo
   ```sh
   git clone https://github.com/github_username/repo_name.git
   ```
3. Install NPM packages
   ```sh
   npm install
   ```
4. Enter your API in `config.js`
   ```js
   const API_KEY = 'ENTER YOUR API';
   ```
5. Change git remote url to avoid accidental pushes to base project
   ```sh
   git remote set-url origin github_username/repo_name
   git remote -v # confirm the changes
   ```

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- USAGE EXAMPLES -->
## Usage

Use this space to show useful examples of how a project can be used. Additional screenshots, code examples and demos work well in this space. You may also link to more resources.

_For more examples, please refer to the [Documentation](https://example.com)_

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- ACKNOWLEDGMENTS -->
## Acknowledgments

Use this space to list resources you find helpful and would like to give credit to. I've included a few of my favorites to kick things off!

* [Choose an Open Source License](https://choosealicense.com)
* [GitHub Emoji Cheat Sheet](https://www.webpagefx.com/tools/emoji-cheat-sheet)
* [Malven's Flexbox Cheatsheet](https://flexbox.malven.co/)
* [Malven's Grid Cheatsheet](https://grid.malven.co/)
* [Img Shields](https://shields.io)
* [GitHub Pages](https://pages.github.com)
* [Font Awesome](https://fontawesome.com)
* [React Icons](https://react-icons.github.io/react-icons/search)

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
