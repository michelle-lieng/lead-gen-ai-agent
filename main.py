from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain.chat_models import init_chat_model
from dotenv import load_dotenv
from langchain_tavily import TavilySearch
from langgraph.prebuilt import ToolNode, tools_condition

# load variables
load_dotenv()

# define the state/memory between agents
class State(TypedDict):
    messages: Annotated[list, add_messages]

graph_builder = StateGraph(State)

# let's define the tools
tool = TavilySearch(max_results=2)
tools = [tool]
# test to see tool output 
#print(tool.invoke("What's a 'node' in LangGraph?"))
llm = init_chat_model("openai:gpt-4.1")
llm_with_tools = llm.bind_tools(tools)
tool_node = ToolNode(tools=[tool])

# let's define all the nodes 
def chatbot(state: State):
    return {"messages": [llm_with_tools.invoke(state["messages"])]}

graph_builder.add_node("chatbot", chatbot)
graph_builder.add_node("tools", tool_node)

# this is the flow
graph_builder.add_edge(START, "chatbot")
# use prebuilt if tools again then goes back otherwise ends
#don't need chatbot btw end and chatbot anymore
graph_builder.add_conditional_edges("chatbot", tools_condition)
graph_builder.add_edge("tools", "chatbot")

# at the end we compile it
graph = graph_builder.compile()

user_input = "Tell me how much money CBA made this year."
# for x in graph.invoke({"messages": [{"role": "user", "content": user_input}]}):
#     print("\n\n")
#     print(x)

# PRINT FINAL MESSAGE TO USER
state = graph.invoke({"messages": [
    {"role": "system", "content": "The year is 2025."}, 
    {"role": "user", "content": user_input}]})
msg = state["messages"][-1]          # last AI's reply to user
print(msg.content)                    # just the content