# Official Kaggle x Google 5-Day AI Agents Course Patterns

**Extracted from**: `kaggle x google/` folder notebooks  
**Last Updated**: November 24, 2025

---

## 📚 Day 1: From Prompt to Action

### Pattern 1.1: Agent Initialization

**Official Pattern**:
```python
from google.adk.agents import Agent  # or LlmAgent
from google.adk.models.google_llm import Gemini
from google.genai import types

# Create agent
agent = Agent(
    name="AgentName",
    model=Gemini(model_name="gemini-2.0-flash-exp"),  # or gemini-1.5-pro
    instruction="Clear instructions for the agent's behavior"
)
```

**Key Components**:
- Uses `google.adk.agents` module
- `Gemini()` model wrapper from `google.adk.models.google_llm`
- Model names: `gemini-2.0-flash-exp`, `gemini-1.5-pro`
- Instructions define agent behavior

### Pattern 1.2: Running Agents

**Official Pattern**:
```python
from google.adk.runners import InMemoryRunner

runner = InMemoryRunner()
response = runner.run(agent, "User query here")
print(response)
```

---

## 🛠️ Day 2: Agent Tools

### Pattern 2.1: Built-in Tools

**Official Pattern**:
```python
from google.adk.tools import google_search, AgentTool
from google.adk.code_executors import BuiltInCodeExecutor

agent = LlmAgent(
    name="ResearchAgent",
    model=Gemini(model_name="gemini-2.0-flash-exp"),
    tools=[google_search],  # Built-in tools
    instruction="Research topics using Google Search"
)
```

### Pattern 2.2: Custom Tool Definition

**Official Pattern**:
```python
from google.adk.tools import AgentTool, ToolContext

def custom_tool_function(param: str) -> str:
    """Tool description for LLM.
    
    Args:
        param: Description of parameter
        
    Returns:
        Description of return value
    """
    # Implementation
    return result

# Wrap as AgentTool
custom_tool = AgentTool(
    name="custom_tool_name",
    description="Description for the LLM",
    function=custom_tool_function
)

agent = LlmAgent(
    name="ToolUser",
    model=Gemini(model_name="gemini-2.0-flash-exp"),
    tools=[custom_tool],
    instruction="Use custom tools to complete tasks"
)
```

**Note**: The course uses `AgentTool` wrapper, NOT `@tool` decorator. The decorator doesn't exist in the official ADK.

---

## 💾 Day 3: Agent Sessions & Memory

### Pattern 3.1: Session Management

**Official Pattern**:
```python
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner

# Create session service
session_service = InMemorySessionService()

# Create runner with session support
runner = Runner(session_service=session_service)

# Create session
session_id = "unique_session_id"
response = runner.run(
    agent,
    "User message",
    session_id=session_id  # Maintains context
)
```

### Pattern 3.2: Persistent State

**Official Pattern**:
```python
# Sessions automatically persist conversation history
# Access session history
session = session_service.get_session(session_id)
for message in session.history:
    print(f"{message.role}: {message.content}")
```

**Key Features**:
- `InMemorySessionService` for development
- `Runner` (not `InMemoryRunner`) for session support
- Session ID tracks conversation context
- Automatic history persistence

---

## 🔗 Day 5: Agent-to-Agent Communication

### Pattern 5.1: Multi-Agent with Sub-Agents

**Official Pattern**:
```python
from google.adk.agents import LlmAgent

# Create specialist agents
specialist_1 = LlmAgent(
    name="Specialist1",
    model=Gemini(model_name="gemini-2.0-flash-exp"),
    tools=[tool1],
    instruction="Specialist 1 instructions"
)

specialist_2 = LlmAgent(
    name="Specialist2", 
    model=Gemini(model_name="gemini-2.0-flash-exp"),
    tools=[tool2],
    instruction="Specialist 2 instructions"
)

# Create coordinator with sub_agents
coordinator = LlmAgent(
    name="Coordinator",
    model=Gemini(model_name="gemini-1.5-pro"),  # Pro for coordination
    sub_agents=[specialist_1, specialist_2],  # ⭐ KEY PATTERN
    instruction="""
    You are a coordinator that delegates to specialist agents.
    Route user requests to the appropriate specialist.
    """
)
```

**⭐ CRITICAL**: The `sub_agents` parameter is the official pattern for multi-agent coordination!

### Pattern 5.2: Agent-to-Agent Protocol (A2A)

**Official Pattern**:
```python
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from google.adk.a2a.utils.agent_to_a2a import to_a2a

# Expose agent via A2A protocol
a2a_agent = to_a2a(agent)

# Consume remote agent
remote_agent = RemoteA2aAgent(
    name="RemoteAgent",
    description="Description of remote agent",
    url="http://remote-agent-url.com"
)

# Use in coordinator
coordinator = LlmAgent(
    name="MainAgent",
    sub_agents=[local_agent, remote_agent]
)
```

---

## 📊 Summary of Key Patterns

### ✅ What the Course DOES Use:

1. **`google.adk.agents.LlmAgent`** - Main agent class
2. **`google.adk.models.google_llm.Gemini`** - Model wrapper
3. **`sub_agents=[...]`** - Multi-agent coordination parameter
4. **`AgentTool()`** - Custom tool wrapper (NOT @tool decorator)
5. **`InMemorySessionService`** - Session state management
6. **`Runner`** - Execution with session support
7. **Model names**: `gemini-2.0-flash-exp`, `gemini-1.5-pro`

### ❌ What the Course Does NOT Use:

1. **`@tool` decorator** - This doesn't exist in ADK
2. **`Agent` class without "Llm" prefix** - Day 1 uses `Agent`, but Day 2+ uses `LlmAgent`
3. **`google.generativeai`** - This is the older SDK, not ADK
4. **Plain dict for state** - Uses `InMemorySessionService` instead
5. **`.run()` on agent directly** - Always uses `Runner.run(agent, ...)`

---

## 🎯 Model Selection Guidelines

From the course:

- **`gemini-2.0-flash-exp`**: Fast, efficient for specialist agents
- **`gemini-1.5-pro`**: More powerful, used for coordinators and complex reasoning
- **Retry configuration**: Use `types.HttpRetryOptions` for production

---

## 🔑 Key Takeaways for Competition

1. **Use `LlmAgent` consistently** - This is the main agent class
2. **Use `sub_agents` for coordination** - This is THE multi-agent pattern
3. **Wrap tools with `AgentTool()`** - Not decorators
4. **Use `InMemorySessionService` + `Runner`** - For proper session management
5. **Model naming**: Use the exact names from course (`gemini-2.0-flash-exp`, not `gemini-1.5-flash`)
6. **Always use `Runner.run()`** - Don't call agent methods directly

---

## 📖 Course Reference

- **Course**: Kaggle x Google 5-Day AI Agents Intensive
- **URL**: https://www.kaggle.com/learn-guide/5-day-agents
- **Notebooks**: Included in `kaggle x google/` folder
