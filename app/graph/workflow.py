from typing import TypedDict, List, Annotated
from langgraph.graph import StateGraph, END

from app.core.models import AgentState
from app.graph.nodes import scrape_jobs,tailor_application,filter_jobs,apply_to_job, generate_report


def create_workflow():
    workflow = StateGraph(AgentState)
    
    #Add the nodes
    workflow.add_node("scrape",scrape_jobs)
    workflow.add_node("match",filter_jobs)
    workflow.add_node("tailor",tailor_application)
    workflow.add_node("apply", apply_to_job)
    workflow.add_node("report", generate_report)
    #Define the edges
    workflow.set_entry_point("scrape")
    workflow.add_edge("scrape","match")
    workflow.add_edge("match","tailor")
    workflow.add_edge("tailor","apply")
    workflow.add_edge("apply","report")
    workflow.add_edge("report",END)
    
    #Compile the workflow
    app_workflow = workflow.compile()
    return app_workflow

app = create_workflow()
