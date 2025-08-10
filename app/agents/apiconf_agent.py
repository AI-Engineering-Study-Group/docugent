"""
API Conference AI Agent using Google ADK.
"""

import logging
import hashlib
from typing import Dict, Any, Optional
from google.adk.agents import LlmAgent
from google.adk.runners import Runner

from app.config.settings import settings
from app.services.tool_manager import ToolManager
from app.services.session_manager import SessionManager
from app.services.message_processor import MessageProcessor
from app.services.response_processor import ResponseProcessor
from app.services.agent_config import AgentConfig
from app.services.redis_service import RedisService

logger = logging.getLogger(__name__)

class APIConfAgent:
    """AI Agent for API Conference Lagos 2025."""
    
    def __init__(self):
        """Initialize the API Conference agent."""
        # Initialize services
        self.tool_manager = ToolManager()
        self.session_manager = SessionManager()
        self.redis_service = RedisService.get_instance()
        
        # Create the agent using LlmAgent
        self.agent = LlmAgent(
            model=settings.google_model_name,
            name=AgentConfig.get_agent_name(),
            description=AgentConfig.get_agent_description(),
            instruction=AgentConfig.get_system_instruction(),
            tools=self.tool_manager.get_tools(),
            before_tool_callback=self.tool_manager.before_tool_callback
        )
        
        # Set up runner
        self.runner = Runner(
            agent=self.agent,
            app_name=AgentConfig.get_app_name(),
            session_service=self.session_manager.get_session_service()
        )
        
        logger.info("API Conference Agent initialized successfully")
    
    def _extract_text_from_event(self, event: Any) -> Optional[str]:
        """Safely extract the first *text* part from an ADK event."""
        if not event or not hasattr(event, "content") or not event.content.parts:
            return None
        return event.content.parts[0].text

    async def chat(self, message: str, user_id: str = None, session_id: str = None, 
                  timestamp: int = None, timezone_offset: int = None) -> Dict[str, Any]:
        """Process a chat message and return a response."""
        try:
            # Create a cache key for the message
            cache_key = f"chat:{hashlib.md5(message.encode()).hexdigest()}"
            
            # Check cache first
            cached_response = self.redis_service.get(cache_key)
            if cached_response:
                logger.info(f"Returning cached response for message: {message}")
                return cached_response

            # Set defaults
            user_id = user_id or "default_user"
            session_id = session_id or f"session_{user_id}"
            
            # Get or create session
            await self.session_manager.get_or_create_session(user_id, session_id)
            
            # Process message
            content = MessageProcessor.process_message(message, user_id, timestamp, timezone_offset)
            
            # Initialize response tracking
            final_response = None
            tool_outputs = []
            executed_tool_names = []
            
            # Use the runner to handle the conversation
            async for event in self.runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=content
            ):
                if hasattr(event, 'tool_response') and event.tool_response:
                    tool_outputs.append(event.tool_response)
                
                if hasattr(event, 'tool_code') and event.tool_code:
                    executed_tool_names.append(event.tool_code.name)

                if event.is_final_response():
                    final_response = self._extract_text_from_event(event)
            
            # Process tool outputs for custom formatting
            if tool_outputs:
                formatted_response = ResponseProcessor.process_tool_outputs(tool_outputs)
                if formatted_response:
                    final_response = formatted_response

            if final_response is None:
                final_response = "I apologize, but I couldn't generate a response. Please try again."
            
            response = {
                "success": True,
                "response": final_response,
                "user_id": user_id,
                "session_id": session_id
            }
            
            # Cache the response
            self.redis_service.set(cache_key, response, ttl=3600)
            
            return response
        except Exception as e:
            logger.error(f"Error in chat: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "response": "I apologize, but I'm experiencing technical difficulties. Please try again or contact the support team for assistance.",
                "support_contact": settings.support_phone
            }

    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the agent."""
        return {
            "status": "active",
            "venue": "The Zone, Plot 9, Gbagada Industrial Scheme, Lagos, Nigeria",
            "dates": "July 18-19, 2025",
            "speakers_announced": True,
            "total_speakers": 44
        }
