import logging
import os
import time

from pythonanywhereapiclient import console, webapp

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

logger = logging.getLogger(__name__)

WORKING_DIRECTORY = os.getenv("PYTHONANYWHERE_WORKING_DIRECTORY")
DOMAIN_NAME = os.getenv("PYTHONANYWHERE_DOMAIN_NAME")


def validate_env_vars():
    """Required environment variables validation."""

    required_vars = ["PYTHONANYWHERE_API_CLIENT_USER", "PYTHONANYWHERE_API_CLIENT_TOKEN", "PYTHONANYWHERE_API_CLIENT_HOST", "PYTHONANYWHERE_WORKING_DIRECTORY", "PYTHONANYWHERE_DOMAIN_NAME"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        raise OSError(f"Missing environment variables: {', '.join(missing_vars)}")


def get_or_create_console():
    """Get existing console or create a new one."""
    try:
        consoles = console.list()
        return consoles[0] if consoles else console.create(executable="bash", working_directory=WORKING_DIRECTORY)
    except Exception as e:
        logger.error(f"Failed to get or create console: {str(e)}")
        raise


def execute_command(console_id, command, timeout=300):
    """Execute a command in the console with timeout."""
    try:
        logger.info(f"Executing: {command.strip()}")
        console.send_input(console_id, command + "\n")
        start_time = time.time()
        while time.time() - start_time < timeout:
            output = console.get_latest_output(console_id)
            if output.get("output"):
                logger.info(f"Command output: {output['output']}")
                return output
            time.sleep(1)
        raise TimeoutError(f"Command timed out: {command}")
    except Exception as e:
        logger.error(f"Error executing command '{command.strip()}': {str(e)}")
        raise


def main():
    """Main deployment function."""
    try:
        validate_env_vars()

        WORKING_DIRECTORY = "/home/spiskauz/spiskauz-python-backend/"
        DOMAIN_NAME = "spiskauz.pythonanywhere.com"

        cl = get_or_create_console()
        console_id = cl["id"]

        commands = [
            (f"cd {WORKING_DIRECTORY}", "Changing to working directory"),
            ("git pull origin main", "Pulling latest changes from git"),
            ("pip install --no-cache-dir -r requirements.txt", "Installing requirements"),
            ("python manage.py migrate", "Applying database migrations"),
        ]

        for command, description in commands:
            logger.info(description)
            execute_command(console_id, command)

        logger.info("Reloading web application")
        webapp.reload(DOMAIN_NAME)
        logger.info("Deployment completed successfully")

    except Exception as e:
        logger.error(f"Deployment failed: {str(e)}")
        raise


if __name__ == "__main__":
    main()
