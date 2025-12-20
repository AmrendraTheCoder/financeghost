"""
Base Agent
Abstract base class for all FinanceGhost agents
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime

from ..services.llm_service import LLMService, get_llm_service

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Abstract base class for FinanceGhost agents
    
    All agents follow a common pattern:
    1. Receive input data
    2. Process using LLM or local logic
    3. Return structured output
    4. Log actions for audit trail
    """
    
    # Agent identification
    agent_name: str = "base_agent"
    agent_version: str = "1.0.0"
    
    def __init__(self, llm_service: Optional[LLMService] = None):
        """
        Initialize agent with optional LLM service
        
        Args:
            llm_service: Optional LLM service for AI operations
        """
        self.llm = llm_service or get_llm_service()
        self.logs: List[str] = []
    
    def log(self, message: str, level: str = "info"):
        """Add to agent log for audit trail"""
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] [{self.agent_name}] [{level.upper()}] {message}"
        self.logs.append(log_entry)
        
        # Add to global orchestrator log for UI streaming
        try:
            from .orchestrator import AgentOrchestrator
            AgentOrchestrator.add_global_log(self.agent_name, message, level)
        except ImportError:
            pass  # Avoid circular import issues if any
        
        if level == "error":
            logger.error(log_entry)
        elif level == "warning":
            logger.warning(log_entry)
        else:
            logger.info(log_entry)
    
    def clear_logs(self):
        """Clear agent logs"""
        self.logs = []
    
    def get_logs(self) -> List[str]:
        """Get all logged messages"""
        return self.logs.copy()
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """
        Get the system prompt for this agent
        
        Returns:
            System prompt string for LLM context
        """
        pass
    
    @abstractmethod
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process input data and return results
        
        Args:
            input_data: Input data dictionary
            
        Returns:
            Processing results dictionary
        """
        pass
    
    def validate_input(self, input_data: Dict[str, Any], required_fields: List[str]) -> bool:
        """
        Validate that required fields are present in input
        
        Args:
            input_data: Input data to validate
            required_fields: List of required field names
            
        Returns:
            True if valid, raises ValueError if not
        """
        missing = [f for f in required_fields if f not in input_data]
        if missing:
            raise ValueError(f"Missing required fields: {missing}")
        return True
    
    def safe_process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Safely process with error handling
        
        Args:
            input_data: Input data
            
        Returns:
            Results with success status
        """
        try:
            self.log(f"Starting processing")
            result = self.process(input_data)
            self.log(f"Processing complete")
            return {
                "success": True,
                "data": result,
                "logs": self.get_logs()
            }
        except Exception as e:
            self.log(f"Processing failed: {str(e)}", level="error")
            return {
                "success": False,
                "error": str(e),
                "logs": self.get_logs()
            }
