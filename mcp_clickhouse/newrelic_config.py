"""
New Relic agent configuration for mcp-clickhouse.

This module initializes New Relic monitoring if a license key is provided.
The New Relic agent must be initialized before importing other modules.
"""

import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logger for this module
logger = logging.getLogger(__name__)

def initialize_newrelic():
    """Initialize New Relic agent if license key is available."""
    
    # Check if New Relic license key is available
    license_key = os.getenv('NEW_RELIC_LICENSE_KEY')
    
    if not license_key:
        logger.info("ℹ️  New Relic APM monitoring disabled (no license key provided)")
        return None
    
    try:
        import newrelic.agent
        
        # Set environment variables for New Relic configuration
        # These will be picked up by the newrelic.ini configuration file
        if not os.getenv('NEW_RELIC_APP_NAME'):
            os.environ['NEW_RELIC_APP_NAME'] = os.getenv('NEW_RELIC_APP_NAME', 'mcp-clickhouse')
        
        if not os.getenv('NEW_RELIC_LOG_LEVEL'):
            os.environ['NEW_RELIC_LOG_LEVEL'] = os.getenv('NEW_RELIC_LOG_LEVEL', 'info')
            
        if not os.getenv('NEW_RELIC_LOG_FILE'):
            os.environ['NEW_RELIC_LOG_FILE'] = os.getenv('NEW_RELIC_LOG_FILE', '/tmp/newrelic_agent.log')
            
        if not os.getenv('NEW_RELIC_HIGH_SECURITY'):
            os.environ['NEW_RELIC_HIGH_SECURITY'] = os.getenv('NEW_RELIC_HIGH_SECURITY', 'false')
            
        if not os.getenv('NEW_RELIC_ENVIRONMENT'):
            os.environ['NEW_RELIC_ENVIRONMENT'] = os.getenv('NEW_RELIC_ENVIRONMENT', 'production')
        
        # Initialize New Relic agent with configuration
        # Look for newrelic.ini in the project root
        config_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'newrelic.ini')
        if os.path.exists(config_file):
            newrelic.agent.initialize(config_file)
        else:
            newrelic.agent.initialize()
        
        logger.info("✅ New Relic APM monitoring initialized")
        return newrelic.agent
    
    except ImportError:
        logger.warning("⚠️  New Relic package not found. Install 'newrelic' package to enable monitoring")
        return None
    
    except Exception as error:
        logger.warning(f"⚠️  New Relic initialization failed: {error}")
        return None

# Initialize New Relic agent
newrelic_agent = initialize_newrelic()
