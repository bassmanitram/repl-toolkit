"""
Headless mode for repl_toolkit v2.

Provides non-interactive execution for automated scenarios, batch processing,
and integration testing.
"""

from typing import Optional
from loguru import logger

from .ptypes import HeadlessBackend


async def run_headless_mode(
    backend: HeadlessBackend,
    initial_message: Optional[str] = None
) -> bool:
    """
    Run the backend in headless mode.
    
    Processes a single message through the backend without any interactive
    UI components. This is useful for automated testing, batch processing,
    or integration with other systems.
    
    Args:
        backend: Backend that implements HeadlessBackend protocol
        initial_message: Message to process (optional)
        
    Returns:
        bool: True if processing was successful, False otherwise
        
    Example:
        success = await run_headless_mode(
            backend=my_backend,
            initial_message="Process this message"
        )
        
        if success:
            print("Processing completed successfully")
        else:
            print("Processing failed")
    """
    logger.trace("run_headless_mode() entry")
    
    if not initial_message:
        logger.warning("No initial message provided for headless mode")
        logger.trace("run_headless_mode() exit - no message")
        return False
    
    logger.info(f"Running headless mode with message: {initial_message}")
    
    try:
        success = await backend.handle_input(initial_message)
        
        if success:
            logger.info("Headless mode completed successfully")
        else:
            logger.warning("Headless mode completed with backend reporting failure")
        
        logger.trace("run_headless_mode() exit - success")
        return success
        
    except Exception as e:
        logger.error(f"Error in headless mode: {e}")
        logger.trace("run_headless_mode() exit - exception")
        return False