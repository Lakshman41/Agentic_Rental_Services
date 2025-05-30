import os
from pathlib import Path

# Define the root directory name
PROJECT_NAME = "agentic_rental_platform"

# Define the structure as a list of paths
# Directories are ended with a '/'
# Files do not end with a '/'
# __init__.py files are explicitly listed
structure = [
    # Top-level files and directories
    f"{PROJECT_NAME}/.env.example",
    f"{PROJECT_NAME}/README.md",
    f"{PROJECT_NAME}/docker-compose.yml",
    f"{PROJECT_NAME}/requirements.txt",
    f"{PROJECT_NAME}/docs/",
    f"{PROJECT_NAME}/docker/",
    f"{PROJECT_NAME}/kubernetes/",
    f"{PROJECT_NAME}/migrations/",
    f"{PROJECT_NAME}/scripts/",
    f"{PROJECT_NAME}/tests/",

    # app directory and its direct contents
    f"{PROJECT_NAME}/app/",
    f"{PROJECT_NAME}/app/__init__.py",
    f"{PROJECT_NAME}/app/main.py",

    # app/api
    f"{PROJECT_NAME}/app/api/",
    f"{PROJECT_NAME}/app/api/__init__.py",
    f"{PROJECT_NAME}/app/api/deps.py",
    f"{PROJECT_NAME}/app/api/middleware.py",
    f"{PROJECT_NAME}/app/api/v1/",
    f"{PROJECT_NAME}/app/api/v1/__init__.py",
    f"{PROJECT_NAME}/app/api/v1/router.py",
    f"{PROJECT_NAME}/app/api/v1/endpoints/",
    f"{PROJECT_NAME}/app/api/v1/endpoints/__init__.py",
    f"{PROJECT_NAME}/app/api/v1/endpoints/chat.py",
    f"{PROJECT_NAME}/app/api/v1/endpoints/properties.py",
    f"{PROJECT_NAME}/app/api/v1/endpoints/users.py",
    f"{PROJECT_NAME}/app/api/v1/endpoints/bookings.py",
    f"{PROJECT_NAME}/app/api/v1/endpoints/websocket.py",
    f"{PROJECT_NAME}/app/api/v1/endpoints/health.py",

    # app/agents
    f"{PROJECT_NAME}/app/agents/",
    f"{PROJECT_NAME}/app/agents/__init__.py",
    f"{PROJECT_NAME}/app/agents/orchestrator.py",
    f"{PROJECT_NAME}/app/agents/registry.py",
    f"{PROJECT_NAME}/app/agents/fallback.py",
    f"{PROJECT_NAME}/app/agents/base/",
    f"{PROJECT_NAME}/app/agents/base/__init__.py",
    f"{PROJECT_NAME}/app/agents/base/agent.py",
    f"{PROJECT_NAME}/app/agents/base/message.py",
    f"{PROJECT_NAME}/app/agents/base/state.py",
    f"{PROJECT_NAME}/app/agents/core/", # This 'core' is under 'agents'
    f"{PROJECT_NAME}/app/agents/core/__init__.py",
    f"{PROJECT_NAME}/app/agents/core/conversation_agent.py",
    f"{PROJECT_NAME}/app/agents/core/search_agent.py",
    f"{PROJECT_NAME}/app/agents/core/recommendation_agent.py",
    f"{PROJECT_NAME}/app/agents/core/negotiation_agent.py",
    f"{PROJECT_NAME}/app/agents/core/scheduling_agent.py",
    f"{PROJECT_NAME}/app/agents/core/documentation_agent.py",
    f"{PROJECT_NAME}/app/agents/core/analytics_agent.py",
    f"{PROJECT_NAME}/app/agents/core/compliance_agent.py",
    f"{PROJECT_NAME}/app/agents/core/notification_agent.py", # Added from "Additional Agents"
    f"{PROJECT_NAME}/app/agents/core/mobile_agent.py",       # Added from "Additional Agents"

    # app/core (this 'core' is under 'app')
    f"{PROJECT_NAME}/app/core/",
    f"{PROJECT_NAME}/app/core/__init__.py",
    f"{PROJECT_NAME}/app/core/config.py",
    f"{PROJECT_NAME}/app/core/security.py",
    f"{PROJECT_NAME}/app/core/database.py",
    f"{PROJECT_NAME}/app/core/logging.py",
    f"{PROJECT_NAME}/app/core/events.py",

    # app/models
    f"{PROJECT_NAME}/app/models/",
    f"{PROJECT_NAME}/app/models/__init__.py",
    f"{PROJECT_NAME}/app/models/base.py",
    f"{PROJECT_NAME}/app/models/user.py",
    f"{PROJECT_NAME}/app/models/property.py",
    f"{PROJECT_NAME}/app/models/chat.py",
    f"{PROJECT_NAME}/app/models/booking.py",
    f"{PROJECT_NAME}/app/models/agent.py", # Agent state models
    f"{PROJECT_NAME}/app/models/analytics.py",

    # app/services
    f"{PROJECT_NAME}/app/services/",
    f"{PROJECT_NAME}/app/services/__init__.py",
    f"{PROJECT_NAME}/app/services/base.py",
    f"{PROJECT_NAME}/app/services/chat_service.py",
    f"{PROJECT_NAME}/app/services/property_service.py",
    f"{PROJECT_NAME}/app/services/user_service.py",
    f"{PROJECT_NAME}/app/services/booking_service.py",
    f"{PROJECT_NAME}/app/services/notification_service.py",
    f"{PROJECT_NAME}/app/services/analytics_service.py",
    f"{PROJECT_NAME}/app/services/compliance_service.py",

    # app/external
    f"{PROJECT_NAME}/app/external/",
    f"{PROJECT_NAME}/app/external/__init__.py",
    f"{PROJECT_NAME}/app/external/ai/",
    f"{PROJECT_NAME}/app/external/ai/__init__.py",
    f"{PROJECT_NAME}/app/external/ai/openai_client.py",
    f"{PROJECT_NAME}/app/external/ai/deepseek_client.py",
    f"{PROJECT_NAME}/app/external/ai/huggingface_client.py",
    f"{PROJECT_NAME}/app/external/data/",
    f"{PROJECT_NAME}/app/external/data/__init__.py",
    f"{PROJECT_NAME}/app/external/data/property_apis.py",
    f"{PROJECT_NAME}/app/external/data/maps_client.py",
    f"{PROJECT_NAME}/app/external/data/demographics_client.py",
    f"{PROJECT_NAME}/app/external/communication/",
    f"{PROJECT_NAME}/app/external/communication/__init__.py",
    f"{PROJECT_NAME}/app/external/communication/email_client.py",
    f"{PROJECT_NAME}/app/external/communication/sms_client.py",
    f"{PROJECT_NAME}/app/external/communication/push_client.py",
    f"{PROJECT_NAME}/app/external/payment/",
    f"{PROJECT_NAME}/app/external/payment/__init__.py",
    f"{PROJECT_NAME}/app/external/payment/stripe_client.py",
    f"{PROJECT_NAME}/app/external/payment/blockchain_client.py",

    # app/stores
    f"{PROJECT_NAME}/app/stores/",
    f"{PROJECT_NAME}/app/stores/__init__.py",
    f"{PROJECT_NAME}/app/stores/base.py",
    f"{PROJECT_NAME}/app/stores/conversation_store.py",
    f"{PROJECT_NAME}/app/stores/property_store.py",
    f"{PROJECT_NAME}/app/stores/user_store.py",
    f"{PROJECT_NAME}/app/stores/vector_store.py",
    f"{PROJECT_NAME}/app/stores/cache_store.py",

    # app/utils
    f"{PROJECT_NAME}/app/utils/",
    f"{PROJECT_NAME}/app/utils/__init__.py",
    f"{PROJECT_NAME}/app/utils/helpers.py",
    f"{PROJECT_NAME}/app/utils/validators.py",
    f"{PROJECT_NAME}/app/utils/formatters.py",
    f"{PROJECT_NAME}/app/utils/ml_utils.py",
    f"{PROJECT_NAME}/app/utils/monitoring.py",

    # app/websocket
    f"{PROJECT_NAME}/app/websocket/",
    f"{PROJECT_NAME}/app/websocket/__init__.py",
    f"{PROJECT_NAME}/app/websocket/connection_manager.py",
    f"{PROJECT_NAME}/app/websocket/chat_handler.py",
    f"{PROJECT_NAME}/app/websocket/notifications_handler.py",
]

def create_structure():
    """Creates the project directory structure."""
    base_path = Path(".") # Create in the current directory

    for item_path_str in structure:
        item_path = base_path / item_path_str
        if item_path_str.endswith('/'):
            # This is a directory
            item_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {item_path}")
        else:
            # This is a file
            # Ensure parent directory exists
            item_path.parent.mkdir(parents=True, exist_ok=True)
            # Create the file if it doesn't exist
            item_path.touch(exist_ok=True)
            print(f"Created file: {item_path}")

    print("\nProject structure created successfully!")
    print(f"Root project folder: {base_path / PROJECT_NAME}")

if __name__ == "__main__":
    create_structure()