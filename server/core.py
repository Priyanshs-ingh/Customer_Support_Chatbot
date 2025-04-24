#!/usr/bin/env python
# coding: utf-8

# ## Key Components
# 1. **State Management**: Using TypedDict to define and manage the state of each customer interaction.
# 2. **Query Categorization**: Classifying customer queries into Technical, Billing, or General categories.
# 3. **Sentiment Analysis**: Determining the emotional tone of customer queries.
# 4. **Response Generation**: Creating appropriate responses based on the query category and sentiment.
# 5. **Escalation Mechanism**: Automatically escalating queries with negative sentiment to human agents.
# 6. **Workflow Graph**: Utilizing LangGraph to create a flexible and extensible workflow.
# 
# ## Method Details
# 1. **Initialization**: Set up the environment and import necessary libraries.
# 2. **State Definition**: Create a structure to hold query information, category, sentiment, and response.
# 3. **Node Functions**: Implement separate functions for categorization, sentiment analysis, and response generation.
# 4. **Graph Construction**: Use StateGraph to define the workflow, adding nodes and edges to represent the support process.
# 5. **Conditional Routing**: Implement logic to route queries based on their category and sentiment.
# 6. **Workflow Compilation**: Compile the graph into an executable application.
# 7. **Execution**: Process customer queries through the workflow and retrieve results.

# In[1]:





# In[2]:


from typing import TypedDict, Dict
from langgraph.graph import StateGraph, END
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables.graph import MermaidDrawMethod
from IPython.display import display , Image


# Define State Structure

# In[3]:


class State(TypedDict):
  query: str
  category: str
  sentiment: str
  response: str


# In[4]:


from langchain_groq import ChatGroq

llm = ChatGroq(
    temperature=0,
    groq_api_key = "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",
    model_name = "llama-3.3-70b-versatile"
)
result = llm.invoke("What is langchain")
result.content


# Define Node Function

# In[5]:


def categorize(state: State) -> State:
  "Technical, Billing, General"
  prompt = ChatPromptTemplate.from_template(
      "Categorize the following customer query into one of these categories: "
      "Technical, Billing, General. Query: {query}"
  )
  chain = prompt | llm
  category = chain.invoke({"query": state["query"]}).content
  return {"category": category}

def analyze_sentiment(state: State) -> State:
  prompt = ChatPromptTemplate.from_template(
      "Analyze the sentiment of the following customer query"
      "Response with either 'Position', 'Neutral' , or 'Negative'. Query: {query}"
  )
  chain = prompt | llm
  sentiment = chain.invoke({"query": state["query"]}).content
  return {"sentiment": sentiment}

def handle_technical(state: State)->State:
  prompt = ChatPromptTemplate.from_template(
      "Provide a technical support response to the following query : {query}"
  )
  chain = prompt | llm
  response = chain.invoke({"query": state["query"]}).content
  return {"response": response}

def handle_billing(state: State)->State:
  prompt = ChatPromptTemplate.from_template(
      "Provide a billing support response to the following query : {query}"
  )
  chain = prompt | llm
  response = chain.invoke({"query": state["query"]}).content
  return {"response": response}

def handle_general(state: State)->State:
  prompt = ChatPromptTemplate.from_template(
      "Provide a general support response to the following query : {query}"
  )
  chain = prompt | llm
  response = chain.invoke({"query": state["query"]}).content
  return {"response": response}

def escalate(state: State)->State:
  return {"response": "This query has been escalate to a human agent due to its negative sentiment"}

def route_query(state: State)->State:
  if state["sentiment"] == "Negative":
    return "escalate"
  elif state["category"] == "Technical":
    return "handle_technical"
  elif state["category"] == "Billing":
    return "handle_billing"
  else:
    return "handle_general"


# Create and configure the graph

# In[6]:


workflow = StateGraph(State)

workflow.add_node("categorize", categorize)
workflow.add_node("analyze_sentiment", analyze_sentiment)
workflow.add_node("handle_technical", handle_technical)
workflow.add_node("handle_billing", handle_billing)
workflow.add_node("handle_general", handle_general)
workflow.add_node("escalate", escalate)

workflow.add_edge("categorize", "analyze_sentiment")
workflow.add_conditional_edges(
    "analyze_sentiment",
    route_query,{
        "handle_technical" : "handle_technical",
        "handle_billing" :  "handle_billing",
        "handle_general" : "handle_general",
        "escalate": "escalate"
    }
)

workflow.add_edge("handle_technical", END)
workflow.add_edge("handle_billing", END)
workflow.add_edge("handle_general", END)
workflow.add_edge("escalate", END)

workflow.set_entry_point("categorize")

app  = workflow.compile()


# Visulize the graph

# In[7]:


display(
    Image(
        app.get_graph().draw_mermaid_png(
            draw_method=MermaidDrawMethod.API
        )
    )
)


# Run customer support function

# In[8]:


def run_customer_support(query: str)->Dict[str, str]:
  results = app.invoke({"query": query})
  return {
      "category":results['category'],
      "sentiment":results['sentiment'],
      "response": results['response']
  }


# In[9]:


query = "My internet connection is gone it's not working, Can you help me?"
result = run_customer_support(query)
print(f"Query: {query}")
print(f"Category: {result['category']}")
print(f"Sentiment: {result['sentiment']}")
print(f"Response: {result['response']}")
print("\n")


# In[10]:


query = "where can i find my receipt"
result = run_customer_support(query)
print(f"Query: {query}")
print(f"Category: {result['category']}")
print(f"Sentiment: {result['sentiment']}")
print(f"Response: {result['response']}")
print("\n")


# In[11]:




# In[ ]:





# In[ ]:




