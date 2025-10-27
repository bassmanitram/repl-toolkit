import os
import subprocess

from loguru import logger

from .action import ActionContext

def shell_command(context: ActionContext) -> None:  # pragma: no cover
    """Built-in shell command handler."""
    logger.trace("shell_command() entry")
    
    if not context.args:
        # No arguments - drop to interactive shell
        logger.debug("Dropping to interactive shell. Type 'exit' to return to REPL.")
        shell = os.environ.get('SHELL', '/bin/sh' if os.name != 'nt' else 'cmd')
        subprocess.run(shell, check=False)
        logger.debug("Returned from shell.")
    else:
        # Execute shell command and add output to input buffer
        command_args = context.args
        command_str = ' '.join(command_args)
        
        logger.debug(f"Executing: {command_str}")
        try:
            result = subprocess.run(
                command_args,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.stdout:
                # Add output directly to prompt_toolkit input buffer
                from prompt_toolkit.application import get_app
                app = get_app()
                current_buffer = app.current_buffer
                
                logger.debug(f"Current buffer before adding output: {current_buffer.text!r}")
                
                output_text = result.stdout.strip()
                logger.debug(f"Output_text: {output_text!r}")
                current_buffer.insert_text(f"{output_text}")
                
                # Force the application to redraw to show the inserted text
                app.invalidate()
                
                logger.debug(f"Output added to input buffer and display invalidated")
            
            if result.stderr:
                print("Error output:", result.stderr)
                
            if result.returncode != 0:
                logger.warning(f"Command exited with code: {result.returncode}")
                
        except subprocess.TimeoutExpired:
            logger.warning("Command timed out after 30 seconds.")
        except FileNotFoundError:
            logger.warning(f"Command not found: {command_args[0]}")
        except Exception as e:
            logger.warning(f"Error executing command: {e}")
    
    logger.trace("shell_command() exit")
