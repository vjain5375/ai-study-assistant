"""LLM utility functions for interacting with AI models"""
import json
import os
from typing import Dict, List, Any
from langchain_core.messages import HumanMessage, SystemMessage
import config


def get_llm(model_name: str = None, temperature: float = 0.7):
    """
    Get LLM instance based on configuration.
    
    Args:
        model_name: Name of the model to use
        temperature: Temperature for generation
        
    Returns:
        LLM instance
    """
    if config.USE_LOCAL_MODEL:
        # For local models (Ollama, etc.)
        from langchain_community.llms import Ollama
        return Ollama(
            base_url=config.OLLAMA_BASE_URL,
            model=model_name or "llama2",
            temperature=temperature
        )
    else:
        # Use Google Gemini (preferred) or fallback to OpenAI
        if config.GEMINI_API_KEY:
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI
                return ChatGoogleGenerativeAI(
                    model=model_name or config.DEFAULT_MODEL,
                    temperature=temperature,
                    google_api_key=config.GEMINI_API_KEY
                )
            except ImportError:
                raise ImportError("langchain-google-genai not installed. Run: pip install langchain-google-genai")
        elif config.OPENAI_API_KEY:
            # Fallback to OpenAI if Gemini not available
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model_name=model_name or "gpt-3.5-turbo",
                temperature=temperature,
                openai_api_key=config.OPENAI_API_KEY
            )
        else:
            raise ValueError("GEMINI_API_KEY or OPENAI_API_KEY not set. Please set it in .env file")


def call_llm(prompt: str, system_message: str = None, model_name: str = None, timeout: int = 60) -> str:
    """
    Call LLM with a prompt and return the response.
    
    Args:
        prompt: User prompt
        system_message: Optional system message
        model_name: Model to use
        timeout: Timeout in seconds (default: 60)
        
    Returns:
        LLM response text
    """
    try:
        # Reload config to get latest API key
        import importlib
        importlib.reload(config)
        
        llm = get_llm(model_name=model_name)
        
        # Set timeout if supported
        if hasattr(llm, 'timeout'):
            llm.timeout = timeout
        
        messages = []
        if system_message:
            messages.append(SystemMessage(content=system_message))
        messages.append(HumanMessage(content=prompt))
        
        response = llm.invoke(messages)
        
        # Handle different response types
        if hasattr(response, 'content'):
            content = response.content
            if content is None or (isinstance(content, str) and len(content.strip()) == 0):
                raise ValueError("Empty response from LLM. The model may have encountered an error.")
            return content
        response_str = str(response)
        if not response_str or len(response_str.strip()) == 0:
            raise ValueError("Empty response from LLM. The model may have encountered an error.")
        return response_str
    except Exception as e:
        error_msg = str(e)
        if "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
            raise TimeoutError(f"LLM request timed out after {timeout} seconds. Try with fewer chunks or smaller text.")
        elif "api" in error_msg.lower() and ("key" in error_msg.lower() or "quota" in error_msg.lower() or "permission" in error_msg.lower()):
            raise ValueError(f"API Error: {error_msg}. Please check your Gemini API key configuration.")
        elif "empty" in error_msg.lower():
            raise ValueError(error_msg)
        else:
            raise Exception(f"Error calling LLM: {error_msg}")


def parse_json_response(response: str) -> Any:
    """
    Parse JSON from LLM response, handling markdown code blocks.
    
    Args:
        response: LLM response string
        
    Returns:
        Parsed JSON object
    """
    # Remove markdown code blocks if present
    response = response.strip()
    if response.startswith("```json"):
        response = response[7:]
    if response.startswith("```"):
        response = response[3:]
    if response.endswith("```"):
        response = response[:-3]
    
    response = response.strip()
    
    try:
        return json.loads(response)
    except json.JSONDecodeError as e:
        # Try to extract JSON from response
        start_idx = response.find('[')
        end_idx = response.rfind(']') + 1
        if start_idx == -1:
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
        
        if start_idx != -1 and end_idx > start_idx:
            try:
                return json.loads(response[start_idx:end_idx])
            except:
                pass
        
        raise ValueError(f"Could not parse JSON from response: {str(e)}")

