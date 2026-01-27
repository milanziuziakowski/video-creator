"""
Architecture Diagram Generator for Video Creator Project

This script generates an architecture diagram of the video_creator project
using the diagrams library and the Diagrams MCP Server.

Usage:
    Ask Claude/AI Assistant: "Create an architecture diagram for my project in src/"
"""

from diagrams import Diagram, Cluster, Edge
from diagrams.programming.language import Python
from diagrams.onprem.queue import Kafka
from diagrams.onprem.compute import Server
from diagrams.onprem.database import PostgreSQL, MongoDB
from diagrams.onprem.inmemory import Redis
from diagrams.custom import Custom
import os


def create_video_creator_architecture():
    """Generate architecture diagram for the video_creator application."""
    
    with Diagram("Video Creator Architecture", show=False, direction="TB", outformat="png"):
        
        # Entry point
        user = Custom("User/API Client", "icons/user.png")
        
        with Cluster("Core Application (src/)"):
            with Cluster("Orchestration Layer"):
                orchestrator = Python("Orchestrator")
            
            with Cluster("Core Components"):
                config = Python("Config")
                models = Python("Models")
            
            with Cluster("Business Logic"):
                segment_model = Python("Segment Model")
                video_plan = Python("Video Plan")
        
        with Cluster("Agents Layer"):
            agents = Python("Agents")
        
        with Cluster("Storage Layer"):
            storage = Python("Storage Utils")
        
        with Cluster("External Services"):
            with Cluster("MCP Servers"):
                fl2v = Custom("FL2V MCP", "icons/api.png")
                mediaops = Custom("MediaOps MCP", "icons/api.png")
                minimax = Custom("MiniMax MCP", "icons/api.png")
        
        with Cluster("Data Layer"):
            db = PostgreSQL("Database")
            cache = Redis("Cache")
        
        # Connections
        user >> orchestrator
        orchestrator >> [config, models, segment_model, video_plan]
        orchestrator >> agents
        orchestrator >> storage
        
        # MCP Server connections
        agents >> [fl2v, mediaops, minimax]
        
        # Data layer
        orchestrator >> db
        orchestrator >> cache
        
        return "Architecture diagram created: video_creator_architecture.png"


if __name__ == "__main__":
    print(create_video_creator_architecture())
