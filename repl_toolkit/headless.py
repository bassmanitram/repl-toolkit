"""
Headless interface for repl_toolkit.

Provides non-interactive input processing suitable for scripted usage,
piped input, and automation scenarios.
"""

import sys
from typing import Optional

from loguru import logger

from .types import HeadlessBackend


async def run_headless_mode(
    backend: HeadlessBackend,
    initial_message: Optional[str] = None,
    input_stream=None
) -> bool:
    """
    Run in headless mode for non-interactive input processing.
    
    Processes input from stdin (or provided stream) line by line,
    with support for explicit message boundaries using {{send}} commands.
    
    Args:
        backend: Backend to process the input
        initial_message: Optional initial message to process first
        input_stream: Optional input stream (defaults to sys.stdin)
        
    Returns:
        bool: True if all processing was successful, False otherwise
    """
    if input_stream is None:
        input_stream = sys.stdin
        
    success = True
    
    # Process initial message if provided
    if initial_message:
        logger.debug(f"Processing initial message: {initial_message}")
        try:
            result = await backend.handle_input(initial_message)
            if not result:
                logger.warning("Initial message processing failed")
                success = False
        except Exception as e:
            logger.error(f"Error processing initial message: {e}")
            success = False
    
    # Process input from stream
    buffer = []
    
    try:
        for line in input_stream:
            line = line.rstrip('\n\r')
            
            # Check for explicit send command
            if line.strip() == "{{send}}":
                if buffer:
                    message = '\n'.join(buffer).strip()
                    if message:  # Skip empty messages
                        logger.debug(f"Processing buffered message: {message}")
                        try:
                            result = await backend.handle_input(message)
                            if not result:
                                logger.warning("Message processing failed")
                                success = False
                        except Exception as e:
                            logger.error(f"Error processing message: {e}")
                            success = False
                    buffer = []
            else:
                buffer.append(line)
        
        # Process any remaining buffered content at EOF
        if buffer:
            message = '\n'.join(buffer).strip()
            if message:  # Skip empty messages
                logger.debug(f"Processing final buffered message: {message}")
                try:
                    result = await backend.handle_input(message)
                    if not result:
                        logger.warning("Final message processing failed")
                        success = False
                except Exception as e:
                    logger.error(f"Error processing final message: {e}")
                    success = False
                    
    except KeyboardInterrupt:
        logger.info("Headless mode interrupted by user")
        success = False
    except Exception as e:
        logger.error(f"Error in headless mode: {e}")
        success = False
    
    return success