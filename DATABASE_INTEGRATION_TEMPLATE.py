"""
Database Integration Template for VoiceLink Security

This file provides templates for integrating the security system with a real database.
Replace the TODO sections in api/security.py with implementations based on this template.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class UserDatabaseInterface:
    """Template interface for user database operations"""
    
    def __init__(self, db_connection):
        """Initialize with your database connection"""
        self.db = db_connection
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Get user by email address
        
        Returns user data in format:
        {
            "user_id": "unique_user_id",
            "email": "user@example.com",
            "role": "admin|analytics_viewer|meeting_owner|participant",
            "api_key": "user_api_key",
            "meetings_access": ["meeting_id1", "meeting_id2"] or ["*"] for all,
            "created_at": datetime,
            "is_active": bool
        }
        """
        try:
            # Example SQL query - adapt to your database
            query = "SELECT * FROM users WHERE email = ? AND is_active = 1"
            result = self.db.execute(query, (email,)).fetchone()
            
            if not result:
                return None
            
            return {
                "user_id": result["user_id"],
                "email": result["email"],
                "role": result["role"],
                "api_key": result["api_key"],
                "meetings_access": self._get_user_meeting_access(result["user_id"]),
                "created_at": result["created_at"],
                "is_active": result["is_active"]
            }
        except Exception as e:
            logger.error(f"Error fetching user by email {email}: {e}")
            return None
    
    def get_user_by_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Get user by API key"""
        try:
            # Example SQL query - adapt to your database
            query = """
                SELECT u.*, ak.api_key 
                FROM users u 
                JOIN api_keys ak ON u.user_id = ak.user_id 
                WHERE ak.api_key = ? AND u.is_active = 1 AND ak.is_active = 1
            """
            result = self.db.execute(query, (api_key,)).fetchone()
            
            if not result:
                return None
            
            return {
                "user_id": result["user_id"],
                "email": result["email"],
                "role": result["role"],
                "api_key": result["api_key"],
                "meetings_access": self._get_user_meeting_access(result["user_id"]),
                "created_at": result["created_at"],
                "is_active": result["is_active"]
            }
        except Exception as e:
            logger.error(f"Error fetching user by API key: {e}")
            return None
    
    def create_user(self, email: str, role: str, password_hash: str = None) -> Optional[str]:
        """Create new user and return user_id"""
        try:
            user_id = f"user_{int(datetime.utcnow().timestamp())}"
            query = """
                INSERT INTO users (user_id, email, role, password_hash, created_at, is_active)
                VALUES (?, ?, ?, ?, ?, 1)
            """
            self.db.execute(query, (user_id, email, role, password_hash, datetime.utcnow()))
            self.db.commit()
            return user_id
        except Exception as e:
            logger.error(f"Error creating user {email}: {e}")
            return None
    
    def create_api_key(self, user_id: str, api_key: str) -> bool:
        """Create API key for user"""
        try:
            query = """
                INSERT INTO api_keys (user_id, api_key, created_at, is_active)
                VALUES (?, ?, ?, 1)
            """
            self.db.execute(query, (user_id, api_key, datetime.utcnow()))
            self.db.commit()
            return True
        except Exception as e:
            logger.error(f"Error creating API key for user {user_id}: {e}")
            return False
    
    def _get_user_meeting_access(self, user_id: str) -> List[str]:
        """Get list of meetings user can access"""
        try:
            query = """
                SELECT meeting_id FROM user_meeting_access 
                WHERE user_id = ? AND is_active = 1
            """
            results = self.db.execute(query, (user_id,)).fetchall()
            
            meeting_ids = [row["meeting_id"] for row in results]
            
            # Check if user has global access
            if "*" in meeting_ids:
                return ["*"]
            
            return meeting_ids
        except Exception as e:
            logger.error(f"Error fetching meeting access for user {user_id}: {e}")
            return []

# Example database schema (SQLite/PostgreSQL compatible)
DATABASE_SCHEMA = """
-- Users table
CREATE TABLE users (
    user_id VARCHAR(255) PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    role VARCHAR(50) NOT NULL CHECK (role IN ('admin', 'analytics_viewer', 'meeting_owner', 'participant')),
    password_hash VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT 1
);

-- API Keys table
CREATE TABLE api_keys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id VARCHAR(255) NOT NULL,
    api_key VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT 1,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- User meeting access table
CREATE TABLE user_meeting_access (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id VARCHAR(255) NOT NULL,
    meeting_id VARCHAR(255) NOT NULL,
    access_level VARCHAR(50) DEFAULT 'read',
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT 1,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Indexes for performance
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_api_keys_key ON api_keys(api_key);
CREATE INDEX idx_user_meeting_access_user ON user_meeting_access(user_id);
CREATE INDEX idx_user_meeting_access_meeting ON user_meeting_access(meeting_id);
"""

# Example integration code for api/security.py
INTEGRATION_EXAMPLE = '''
# In api/security.py, replace the TODO sections with:

# At the top of the file, add:
from database.user_service import UserDatabaseInterface
from persistence.database_service import get_database_service

# Initialize database interface
db_service = get_database_service()
user_db = UserDatabaseInterface(db_service.get_connection())

# In APIKeyManager.validate_api_key():
@staticmethod
def validate_api_key(api_key: str) -> Optional[Dict[str, Any]]:
    """Validate API key and return user data"""
    return user_db.get_user_by_api_key(api_key)

# In get_current_user_from_token():
user_email = payload.get("email")
user_data = user_db.get_user_by_email(user_email)

# In AuthUtils.create_user_session():
user_data = user_db.get_user_by_email(user_email)
'''

print("Database integration template created!")
print("See INTEGRATION_EXAMPLE for specific code to use in api/security.py")
