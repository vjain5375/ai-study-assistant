"""LLM utility functions for interacting with AI models"""
import json
import os
from typing import Dict, List, Any, Optional
from langchain_core.messages import HumanMessage, SystemMessage
import config


def get_llm(provider: str = "gemini", model_name: str = None, temperature: float = 0.7):
    """
    Get LLM instance based on provider.
    
    Args:
        provider: Provider name ("gemini", "groq", "deepseek", "openai")
        model_name: Name of the model to use (overrides default)
        temperature: Temperature for generation
        
    Returns:
        LLM instance or provider marker string
    """
    if config.USE_LOCAL_MODEL:
        # For local models (Ollama, etc.)
        from langchain_community.llms import Ollama
        return Ollama(
            base_url=config.OLLAMA_BASE_URL,
            model=model_name or "llama2",
            temperature=temperature
        )
    
    provider = provider.lower()
    
    # Gemini Provider (for Reader agent)
    if provider == "gemini":
        if not config.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not set. Please set it in .env file")
        try:
            import google.generativeai as genai
            genai.configure(api_key=config.GEMINI_API_KEY)
            return "gemini_direct"
        except ImportError:
            from langchain_google_genai import ChatGoogleGenerativeAI
            return ChatGoogleGenerativeAI(
                model=model_name or config.GEMINI_MODEL,
                temperature=temperature,
                google_api_key=config.GEMINI_API_KEY
            )
    
    # Groq Provider (for Flashcard & Planner agents)
    elif provider == "groq":
        if not config.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY not set. Please set it in .env file")
        try:
            from langchain_groq import ChatGroq
            
            # Try different Groq models in order (llama-3.1-70b is decommissioned, use 8b-instant first)
            models_to_try = [
                "llama-3.1-8b-instant",     # Fast and available
                "llama-3.3-70b-versatile",  # Newer version (if available)
                "mixtral-8x7b-32768",       # Alternative
                "llama-3.1-70b-versatile",  # May be decommissioned
                model_name or config.GROQ_MODEL  # User specified
            ]
            # Remove duplicates while preserving order
            models_to_try = list(dict.fromkeys(models_to_try))
            
            last_error = None
            for model_attempt in models_to_try:
                try:
                    llm = ChatGroq(
                        model=model_attempt,
                        temperature=temperature,
                        groq_api_key=config.GROQ_API_KEY
                    )
                    # Test if it works by trying to create it
                    return llm
                except Exception as e:
                    error_str = str(e)
                    last_error = e
                    # If it's a 404 or model not found, try next model
                    if "404" in error_str or "not found" in error_str.lower() or "model" in error_str.lower():
                        continue
                    else:
                        # Other error (might be API key, quota, etc.) - try this model anyway
                        try:
                            return ChatGroq(
                                model=model_attempt,
                                temperature=temperature,
                                groq_api_key=config.GROQ_API_KEY
                            )
                        except:
                            continue
            
            # If all failed, raise error with helpful message
            raise Exception(f"Failed to initialize Groq. Tried models: {models_to_try}. Last error: {str(last_error)}. Please check your GROQ_API_KEY in Streamlit Cloud Secrets or .env file.")
        except ImportError:
            raise ImportError("langchain-groq not installed. Run: pip install langchain-groq")
    
    # DeepSeek Provider (for Quiz & Chat agents)
    elif provider == "deepseek":
        if not config.DEEPSEEK_API_KEY:
            raise ValueError("DEEPSEEK_API_KEY not set. Please set it in Streamlit Cloud Secrets or .env file")
        try:
            # DeepSeek uses OpenAI-compatible API
            from langchain_openai import ChatOpenAI
            
            # Try different DeepSeek models
            models_to_try = [
                model_name or config.DEEPSEEK_MODEL,
                "DeepSeek-R1-distill-LLaMA",  # R1 distill model
                "deepseek-chat",
                "deepseek-reasoner"
            ]
            models_to_try = list(dict.fromkeys(models_to_try))
            
            last_error = None
            for model_attempt in models_to_try:
                try:
                    llm = ChatOpenAI(
                        model=model_attempt,
                        temperature=temperature,
                        openai_api_key=config.DEEPSEEK_API_KEY,
                        base_url="https://api.deepseek.com/v1"
                    )
                    return llm
                except Exception as e:
                    error_str = str(e)
                    last_error = e
                    if "404" in error_str or "not found" in error_str.lower():
                        continue
                    else:
                        # Try with the model anyway
                        try:
                            return ChatOpenAI(
                                model=model_attempt,
                                temperature=temperature,
                                openai_api_key=config.DEEPSEEK_API_KEY,
                                base_url="https://api.deepseek.com/v1"
                            )
                        except:
                            continue
            
            # If all failed
            raise Exception(f"Failed to initialize DeepSeek. Tried: {models_to_try}. Last error: {str(last_error)}. Please check your DEEPSEEK_API_KEY in Streamlit Cloud Secrets or .env file.")
        except ImportError:
            raise ImportError("langchain-openai not installed. Run: pip install langchain-openai")
    
    # OpenAI Provider (fallback)
    elif provider == "openai":
        if not config.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not set. Please set it in .env file")
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model_name=model_name or "gpt-3.5-turbo",
            temperature=temperature,
            openai_api_key=config.OPENAI_API_KEY
        )
    
    else:
        raise ValueError(f"Unknown provider: {provider}. Use 'gemini', 'groq', 'deepseek', or 'openai'")


def call_llm(prompt: str, system_message: str = None, provider: str = "gemini", 
              model_name: str = None, temperature: float = 0.7, timeout: int = 60) -> str:
    """
    Call LLM with a prompt and return the response.
    
    Args:
        prompt: User prompt
        system_message: Optional system message
        provider: Provider name ("gemini", "groq", "deepseek", "openai")
        model_name: Model to use (overrides provider default)
        temperature: Temperature for generation
        timeout: Timeout in seconds (default: 60)
        
    Returns:
        LLM response text
    """
    try:
        # Reload config to get latest API key
        import importlib
        importlib.reload(config)
        
        llm = get_llm(provider=provider, model_name=model_name, temperature=temperature)
        
        # If using direct Gemini API
        if llm == "gemini_direct":
            import google.generativeai as genai
            genai.configure(api_key=config.GEMINI_API_KEY)
            
            # Combine system message and prompt
            full_prompt = prompt
            if system_message:
                full_prompt = f"{system_message}\n\n{prompt}"
            
            # Try models - some API keys may have access to different models
            models_to_try = [
                model_name or config.GEMINI_MODEL,
                "gemini-1.5-flash",
                "gemini-1.5-pro",
                "gemini-pro"
            ]
            # Remove duplicates while preserving order
            models_to_try = list(dict.fromkeys(models_to_try))
            
            last_error = None
            for model_name_attempt in models_to_try:
                try:
                    model = genai.GenerativeModel(model_name_attempt)
                    response = model.generate_content(
                        full_prompt,
                        generation_config=genai.types.GenerationConfig(
                            temperature=temperature
                        )
                    )
                    if response and hasattr(response, 'text') and response.text:
                        return response.text
                    elif response and hasattr(response, 'candidates') and response.candidates:
                        # Handle different response formats
                        candidate = response.candidates[0]
                        if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                            return candidate.content.parts[0].text
                except Exception as e:
                    error_str = str(e)
                    # If it's a 404, try next model
                    if "404" in error_str or "not found" in error_str.lower():
                        last_error = e
                        continue
                    else:
                        # Other error, might be quota or permission - raise it
                        raise
            
            # If all models failed with 404, the API key might not have access
            raise Exception(f"Gemini API: No available models found. Tried: {models_to_try}. Error: {str(last_error)}")
        
        # Use langchain LLM
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
            raise ValueError(f"API Error: {error_msg}. Please check your {provider.upper()} API key configuration.")
        elif "empty" in error_msg.lower():
            raise ValueError(error_msg)
        else:
            raise Exception(f"Error calling LLM ({provider}): {error_msg}")


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
