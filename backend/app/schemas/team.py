from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    AGENT = "agent"
    ASSISTANT = "assistant"
    VIEWER = "viewer"

class TeamStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"

class Permission(str, Enum):
    # Lead permissions
    VIEW_LEADS = "view_leads"
    CREATE_LEADS = "create_leads"
    EDIT_LEADS = "edit_leads"
    DELETE_LEADS = "delete_leads"
    ASSIGN_LEADS = "assign_leads"
    
    # Property permissions
    VIEW_PROPERTIES = "view_properties"
    CREATE_PROPERTIES = "create_properties"
    EDIT_PROPERTIES = "edit_properties"
    DELETE_PROPERTIES = "delete_properties"
    PUBLISH_PROPERTIES = "publish_properties"
    
    # Team permissions
    VIEW_TEAM = "view_team"
    MANAGE_TEAM = "manage_team"
    INVITE_MEMBERS = "invite_members"
    REMOVE_MEMBERS = "remove_members"
    
    # Analytics permissions
    VIEW_ANALYTICS = "view_analytics"
    VIEW_ALL_ANALYTICS = "view_all_analytics"
    EXPORT_DATA = "export_data"
    
    # Settings permissions
    VIEW_SETTINGS = "view_settings"
    EDIT_SETTINGS = "edit_settings"
    MANAGE_INTEGRATIONS = "manage_integrations"

class TeamBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    industry: Optional[str] = Field(None, max_length=50)
    size: Optional[str] = Field(None, max_length=20)
    website: Optional[str] = Field(None, max_length=200)
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = Field(None, max_length=200)
    timezone: str = Field(default="UTC", max_length=50)

class TeamCreate(TeamBase):
    pass

class TeamUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    industry: Optional[str] = Field(None, max_length=50)
    size: Optional[str] = Field(None, max_length=20)
    website: Optional[str] = Field(None, max_length=200)
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = Field(None, max_length=200)
    timezone: Optional[str] = Field(None, max_length=50)
    status: Optional[TeamStatus] = None

class TeamMember(BaseModel):
    user_id: str
    email: str
    first_name: str
    last_name: str
    role: UserRole
    permissions: List[Permission] = Field(default_factory=list)
    joined_at: datetime
    last_active: Optional[datetime] = None
    is_active: bool = True
    invited_by: Optional[str] = None

class TeamResponse(TeamBase):
    id: str
    owner_id: str
    status: TeamStatus
    members: List[TeamMember] = Field(default_factory=list)
    member_count: int = 0
    created_at: datetime
    updated_at: datetime
    settings: Dict[str, Any] = Field(default_factory=dict)

class TeamInvitation(BaseModel):
    email: EmailStr
    role: UserRole
    permissions: List[Permission] = Field(default_factory=list)
    message: Optional[str] = Field(None, max_length=500)
    expires_at: Optional[datetime] = None

class TeamInvitationResponse(BaseModel):
    id: str
    team_id: str
    email: str
    role: UserRole
    permissions: List[Permission]
    message: Optional[str]
    status: str = "pending"
    invited_by: str
    invited_at: datetime
    expires_at: Optional[datetime]
    accepted_at: Optional[datetime] = None

class TeamStats(BaseModel):
    total_members: int
    active_members: int
    pending_invitations: int
    total_leads: int
    total_properties: int
    conversion_rate: float
    team_performance: Dict[str, Any] = Field(default_factory=dict)

class AuditLog(BaseModel):
    id: str
    team_id: str
    user_id: str
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    description: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: datetime

class TeamSettings(BaseModel):
    lead_auto_assignment: bool = False
    lead_auto_assignment_rules: Dict[str, Any] = Field(default_factory=dict)
    notification_preferences: Dict[str, bool] = Field(default_factory=dict)
    data_retention_days: int = 365
    require_approval_for_publishing: bool = False
    allow_public_profiles: bool = True
    custom_fields: Dict[str, Any] = Field(default_factory=dict)

class RolePermissions(BaseModel):
    role: UserRole
    permissions: List[Permission]
    description: str
    is_system_role: bool = False

# Default role permissions
DEFAULT_ROLE_PERMISSIONS = {
    UserRole.SUPER_ADMIN: [
        Permission.VIEW_LEADS, Permission.CREATE_LEADS, Permission.EDIT_LEADS, Permission.DELETE_LEADS, Permission.ASSIGN_LEADS,
        Permission.VIEW_PROPERTIES, Permission.CREATE_PROPERTIES, Permission.EDIT_PROPERTIES, Permission.DELETE_PROPERTIES, Permission.PUBLISH_PROPERTIES,
        Permission.VIEW_TEAM, Permission.MANAGE_TEAM, Permission.INVITE_MEMBERS, Permission.REMOVE_MEMBERS,
        Permission.VIEW_ANALYTICS, Permission.VIEW_ALL_ANALYTICS, Permission.EXPORT_DATA,
        Permission.VIEW_SETTINGS, Permission.EDIT_SETTINGS, Permission.MANAGE_INTEGRATIONS
    ],
    UserRole.ADMIN: [
        Permission.VIEW_LEADS, Permission.CREATE_LEADS, Permission.EDIT_LEADS, Permission.DELETE_LEADS, Permission.ASSIGN_LEADS,
        Permission.VIEW_PROPERTIES, Permission.CREATE_PROPERTIES, Permission.EDIT_PROPERTIES, Permission.DELETE_PROPERTIES, Permission.PUBLISH_PROPERTIES,
        Permission.VIEW_TEAM, Permission.MANAGE_TEAM, Permission.INVITE_MEMBERS, Permission.REMOVE_MEMBERS,
        Permission.VIEW_ANALYTICS, Permission.VIEW_ALL_ANALYTICS, Permission.EXPORT_DATA,
        Permission.VIEW_SETTINGS, Permission.EDIT_SETTINGS
    ],
    UserRole.AGENT: [
        Permission.VIEW_LEADS, Permission.CREATE_LEADS, Permission.EDIT_LEADS, Permission.ASSIGN_LEADS,
        Permission.VIEW_PROPERTIES, Permission.CREATE_PROPERTIES, Permission.EDIT_PROPERTIES, Permission.PUBLISH_PROPERTIES,
        Permission.VIEW_TEAM, Permission.VIEW_ANALYTICS, Permission.VIEW_SETTINGS
    ],
    UserRole.ASSISTANT: [
        Permission.VIEW_LEADS, Permission.CREATE_LEADS, Permission.EDIT_LEADS,
        Permission.VIEW_PROPERTIES, Permission.CREATE_PROPERTIES, Permission.EDIT_PROPERTIES,
        Permission.VIEW_TEAM, Permission.VIEW_ANALYTICS
    ],
    UserRole.VIEWER: [
        Permission.VIEW_LEADS, Permission.VIEW_PROPERTIES, Permission.VIEW_TEAM, Permission.VIEW_ANALYTICS
    ]
}