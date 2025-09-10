#!/usr/bin/env python3
"""
Team Management Service
======================
Handles team collaboration, role-based access control, and permissions
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
import secrets
import hashlib

from app.schemas.team import (
    TeamCreate, TeamUpdate, TeamResponse, TeamMember, TeamInvitation,
    TeamInvitationResponse, TeamStats, AuditLog, TeamSettings,
    UserRole, Permission, DEFAULT_ROLE_PERMISSIONS
)
from app.schemas.user import UserResponse

logger = logging.getLogger(__name__)

class PermissionService:
    """Handles role-based permissions"""
    
    def __init__(self):
        self.role_permissions = DEFAULT_ROLE_PERMISSIONS
    
    def get_permissions_for_role(self, role: UserRole) -> List[Permission]:
        """Get permissions for a role"""
        return self.role_permissions.get(role, [])
    
    def has_permission(self, user_role: UserRole, permission: Permission) -> bool:
        """Check if user role has specific permission"""
        role_permissions = self.get_permissions_for_role(user_role)
        return permission in role_permissions
    
    def can_access_resource(self, user_role: UserRole, resource_type: str, action: str) -> bool:
        """Check if user can access specific resource with action"""
        permission_map = {
            "leads": {
                "view": Permission.VIEW_LEADS,
                "create": Permission.CREATE_LEADS,
                "edit": Permission.EDIT_LEADS,
                "delete": Permission.DELETE_LEADS,
                "assign": Permission.ASSIGN_LEADS
            },
            "properties": {
                "view": Permission.VIEW_PROPERTIES,
                "create": Permission.CREATE_PROPERTIES,
                "edit": Permission.EDIT_PROPERTIES,
                "delete": Permission.DELETE_PROPERTIES,
                "publish": Permission.PUBLISH_PROPERTIES
            },
            "team": {
                "view": Permission.VIEW_TEAM,
                "manage": Permission.MANAGE_TEAM,
                "invite": Permission.INVITE_MEMBERS,
                "remove": Permission.REMOVE_MEMBERS
            },
            "analytics": {
                "view": Permission.VIEW_ANALYTICS,
                "view_all": Permission.VIEW_ALL_ANALYTICS,
                "export": Permission.EXPORT_DATA
            },
            "settings": {
                "view": Permission.VIEW_SETTINGS,
                "edit": Permission.EDIT_SETTINGS,
                "integrations": Permission.MANAGE_INTEGRATIONS
            }
        }
        
        if resource_type not in permission_map:
            return False
        
        if action not in permission_map[resource_type]:
            return False
        
        required_permission = permission_map[resource_type][action]
        return self.has_permission(user_role, required_permission)

class TeamManagementService:
    """Comprehensive team management service"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.teams_collection = db.teams
        self.team_members_collection = db.team_members
        self.team_invitations_collection = db.team_invitations
        self.audit_logs_collection = db.audit_logs
        self.users_collection = db.users
        self.permission_service = PermissionService()
    
    async def create_team(self, team_data: TeamCreate, owner_id: str) -> TeamResponse:
        """Create a new team with owner as super admin"""
        try:
            # Create team document
            team_doc = {
                **team_data.model_dump(),
                "owner_id": owner_id,
                "status": "active",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "settings": {}
            }
            
            result = await self.teams_collection.insert_one(team_doc)
            team_id = str(result.inserted_id)
            
            # Add owner as super admin member
            await self._add_team_member(
                team_id=team_id,
                user_id=owner_id,
                role=UserRole.SUPER_ADMIN,
                invited_by=None
            )
            
            # Log team creation
            await self._log_audit_event(
                team_id=team_id,
                user_id=owner_id,
                action="team_created",
                resource_type="team",
                resource_id=team_id,
                description="Team created"
            )
            
            return await self.get_team(team_id)
            
        except Exception as e:
            logger.error(f"Error creating team: {e}")
            raise
    
    async def get_team(self, team_id: str) -> Optional[TeamResponse]:
        """Get team by ID with members"""
        try:
            team = await self.teams_collection.find_one({"_id": ObjectId(team_id)})
            if not team:
                return None
            
            # Get team members
            members = await self._get_team_members(team_id)
            
            team_doc = {
                "id": str(team["_id"]),
                "name": team["name"],
                "description": team.get("description"),
                "industry": team.get("industry"),
                "size": team.get("size"),
                "website": team.get("website"),
                "phone": team.get("phone"),
                "address": team.get("address"),
                "timezone": team.get("timezone", "UTC"),
                "owner_id": team["owner_id"],
                "status": team["status"],
                "members": members,
                "member_count": len(members),
                "created_at": team["created_at"],
                "updated_at": team["updated_at"],
                "settings": team.get("settings", {})
            }
            
            return TeamResponse(**team_doc)
            
        except Exception as e:
            logger.error(f"Error getting team: {e}")
            raise
    
    async def update_team(self, team_id: str, update_data: TeamUpdate, user_id: str) -> TeamResponse:
        """Update team (requires manage_team permission)"""
        try:
            # Check permissions
            if not await self._check_permission(team_id, user_id, Permission.MANAGE_TEAM):
                raise PermissionError("Insufficient permissions to update team")
            
            # Update team
            update_dict = update_data.model_dump(exclude_unset=True)
            update_dict["updated_at"] = datetime.utcnow()
            
            await self.teams_collection.update_one(
                {"_id": ObjectId(team_id)},
                {"$set": update_dict}
            )
            
            # Log update
            await self._log_audit_event(
                team_id=team_id,
                user_id=user_id,
                action="team_updated",
                resource_type="team",
                resource_id=team_id,
                description="Team updated"
            )
            
            return await self.get_team(team_id)
            
        except Exception as e:
            logger.error(f"Error updating team: {e}")
            raise
    
    async def invite_member(self, team_id: str, invitation: TeamInvitation, invited_by: str) -> TeamInvitationResponse:
        """Invite a new member to the team"""
        try:
            # Check permissions
            if not await self._check_permission(team_id, invited_by, Permission.INVITE_MEMBERS):
                raise PermissionError("Insufficient permissions to invite members")
            
            # Check if user already exists
            existing_user = await self.users_collection.find_one({"email": invitation.email})
            if not existing_user:
                raise ValueError("User with this email does not exist")
            
            # Check if user is already a member
            existing_member = await self.team_members_collection.find_one({
                "team_id": team_id,
                "user_id": str(existing_user["_id"])
            })
            if existing_member:
                raise ValueError("User is already a member of this team")
            
            # Check if invitation already exists
            existing_invitation = await self.team_invitations_collection.find_one({
                "team_id": team_id,
                "email": invitation.email,
                "status": "pending"
            })
            if existing_invitation:
                raise ValueError("Invitation already exists for this email")
            
            # Create invitation
            invitation_doc = {
                "team_id": team_id,
                "email": invitation.email,
                "role": invitation.role.value,
                "permissions": [p.value for p in invitation.permissions],
                "message": invitation.message,
                "status": "pending",
                "invited_by": invited_by,
                "invited_at": datetime.utcnow(),
                "expires_at": invitation.expires_at or (datetime.utcnow() + timedelta(days=7)),
                "token": self._generate_invitation_token()
            }
            
            result = await self.team_invitations_collection.insert_one(invitation_doc)
            
            # Log invitation
            await self._log_audit_event(
                team_id=team_id,
                user_id=invited_by,
                action="member_invited",
                resource_type="team_member",
                resource_id=str(result.inserted_id),
                description=f"Invited {invitation.email} as {invitation.role.value}"
            )
            
            return TeamInvitationResponse(
                id=str(result.inserted_id),
                team_id=team_id,
                email=invitation.email,
                role=invitation.role,
                permissions=invitation.permissions,
                message=invitation.message,
                status="pending",
                invited_by=invited_by,
                invited_at=invitation_doc["invited_at"],
                expires_at=invitation_doc["expires_at"]
            )
            
        except Exception as e:
            logger.error(f"Error inviting member: {e}")
            raise
    
    async def accept_invitation(self, invitation_token: str, user_id: str) -> TeamResponse:
        """Accept team invitation"""
        try:
            # Find invitation
            invitation = await self.team_invitations_collection.find_one({
                "token": invitation_token,
                "status": "pending"
            })
            
            if not invitation:
                raise ValueError("Invalid or expired invitation")
            
            if invitation["expires_at"] < datetime.utcnow():
                raise ValueError("Invitation has expired")
            
            # Verify user email matches invitation
            user = await self.users_collection.find_one({"_id": ObjectId(user_id)})
            if not user or user["email"] != invitation["email"]:
                raise ValueError("User email does not match invitation")
            
            # Add user to team
            await self._add_team_member(
                team_id=invitation["team_id"],
                user_id=user_id,
                role=UserRole(invitation["role"]),
                invited_by=invitation["invited_by"],
                custom_permissions=[Permission(p) for p in invitation["permissions"]]
            )
            
            # Update invitation status
            await self.team_invitations_collection.update_one(
                {"_id": invitation["_id"]},
                {
                    "$set": {
                        "status": "accepted",
                        "accepted_at": datetime.utcnow()
                    }
                }
            )
            
            # Log acceptance
            await self._log_audit_event(
                team_id=invitation["team_id"],
                user_id=user_id,
                action="invitation_accepted",
                resource_type="team_member",
                resource_id=user_id,
                description="Accepted team invitation"
            )
            
            return await self.get_team(invitation["team_id"])
            
        except Exception as e:
            logger.error(f"Error accepting invitation: {e}")
            raise
    
    async def remove_member(self, team_id: str, member_user_id: str, removed_by: str) -> bool:
        """Remove member from team"""
        try:
            # Check permissions
            if not await self._check_permission(team_id, removed_by, Permission.REMOVE_MEMBERS):
                raise PermissionError("Insufficient permissions to remove members")
            
            # Get member info
            member = await self.team_members_collection.find_one({
                "team_id": team_id,
                "user_id": member_user_id
            })
            
            if not member:
                raise ValueError("Member not found")
            
            # Check if trying to remove owner
            team = await self.teams_collection.find_one({"_id": ObjectId(team_id)})
            if team["owner_id"] == member_user_id:
                raise ValueError("Cannot remove team owner")
            
            # Remove member
            await self.team_members_collection.delete_one({
                "team_id": team_id,
                "user_id": member_user_id
            })
            
            # Log removal
            await self._log_audit_event(
                team_id=team_id,
                user_id=removed_by,
                action="member_removed",
                resource_type="team_member",
                resource_id=member_user_id,
                description=f"Removed member {member_user_id}"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error removing member: {e}")
            raise
    
    async def update_member_role(self, team_id: str, member_user_id: str, new_role: UserRole, updated_by: str) -> bool:
        """Update member role"""
        try:
            # Check permissions
            if not await self._check_permission(team_id, updated_by, Permission.MANAGE_TEAM):
                raise PermissionError("Insufficient permissions to update member roles")
            
            # Update member role
            await self.team_members_collection.update_one(
                {
                    "team_id": team_id,
                    "user_id": member_user_id
                },
                {
                    "$set": {
                        "role": new_role.value,
                        "permissions": [p.value for p in self.permission_service.get_permissions_for_role(new_role)],
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            # Log role update
            await self._log_audit_event(
                team_id=team_id,
                user_id=updated_by,
                action="member_role_updated",
                resource_type="team_member",
                resource_id=member_user_id,
                description=f"Updated role to {new_role.value}"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating member role: {e}")
            raise
    
    async def get_team_stats(self, team_id: str) -> TeamStats:
        """Get team statistics"""
        try:
            # Get member counts
            total_members = await self.team_members_collection.count_documents({
                "team_id": team_id
            })
            
            active_members = await self.team_members_collection.count_documents({
                "team_id": team_id,
                "is_active": True
            })
            
            # Get pending invitations
            pending_invitations = await self.team_invitations_collection.count_documents({
                "team_id": team_id,
                "status": "pending"
            })
            
            # Get leads and properties counts (assuming these collections exist)
            total_leads = await self.db.leads.count_documents({"team_id": team_id})
            total_properties = await self.db.properties.count_documents({"team_id": team_id})
            
            # Calculate conversion rate
            converted_leads = await self.db.leads.count_documents({
                "team_id": team_id,
                "status": "converted"
            })
            conversion_rate = (converted_leads / total_leads * 100) if total_leads > 0 else 0
            
            return TeamStats(
                total_members=total_members,
                active_members=active_members,
                pending_invitations=pending_invitations,
                total_leads=total_leads,
                total_properties=total_properties,
                conversion_rate=round(conversion_rate, 2),
                team_performance={}
            )
            
        except Exception as e:
            logger.error(f"Error getting team stats: {e}")
            raise
    
    async def get_audit_logs(self, team_id: str, limit: int = 100, offset: int = 0) -> List[AuditLog]:
        """Get team audit logs"""
        try:
            cursor = self.audit_logs_collection.find(
                {"team_id": team_id}
            ).sort("timestamp", -1).skip(offset).limit(limit)
            
            logs = await cursor.to_list(length=limit)
            
            return [
                AuditLog(
                    id=str(log["_id"]),
                    team_id=log["team_id"],
                    user_id=log["user_id"],
                    action=log["action"],
                    resource_type=log["resource_type"],
                    resource_id=log.get("resource_id"),
                    description=log["description"],
                    metadata=log.get("metadata", {}),
                    ip_address=log.get("ip_address"),
                    user_agent=log.get("user_agent"),
                    timestamp=log["timestamp"]
                )
                for log in logs
            ]
            
        except Exception as e:
            logger.error(f"Error getting audit logs: {e}")
            raise
    
    async def _add_team_member(self, team_id: str, user_id: str, role: UserRole, 
                             invited_by: Optional[str] = None, custom_permissions: Optional[List[Permission]] = None):
        """Add member to team"""
        try:
            # Get user info
            user = await self.users_collection.find_one({"_id": ObjectId(user_id)})
            if not user:
                raise ValueError("User not found")
            
            # Get permissions for role
            permissions = custom_permissions or self.permission_service.get_permissions_for_role(role)
            
            # Create member document
            member_doc = {
                "team_id": team_id,
                "user_id": user_id,
                "email": user["email"],
                "first_name": user.get("first_name", ""),
                "last_name": user.get("last_name", ""),
                "role": role.value,
                "permissions": [p.value for p in permissions],
                "joined_at": datetime.utcnow(),
                "last_active": datetime.utcnow(),
                "is_active": True,
                "invited_by": invited_by
            }
            
            await self.team_members_collection.insert_one(member_doc)
            
        except Exception as e:
            logger.error(f"Error adding team member: {e}")
            raise
    
    async def _get_team_members(self, team_id: str) -> List[TeamMember]:
        """Get team members"""
        try:
            cursor = self.team_members_collection.find({"team_id": team_id})
            members = await cursor.to_list(length=100)
            
            return [
                TeamMember(
                    user_id=member["user_id"],
                    email=member["email"],
                    first_name=member["first_name"],
                    last_name=member["last_name"],
                    role=UserRole(member["role"]),
                    permissions=[Permission(p) for p in member["permissions"]],
                    joined_at=member["joined_at"],
                    last_active=member.get("last_active"),
                    is_active=member["is_active"],
                    invited_by=member.get("invited_by")
                )
                for member in members
            ]
            
        except Exception as e:
            logger.error(f"Error getting team members: {e}")
            return []
    
    async def _check_permission(self, team_id: str, user_id: str, permission: Permission) -> bool:
        """Check if user has permission in team"""
        try:
            member = await self.team_members_collection.find_one({
                "team_id": team_id,
                "user_id": user_id,
                "is_active": True
            })
            
            if not member:
                return False
            
            user_role = UserRole(member["role"])
            return self.permission_service.has_permission(user_role, permission)
            
        except Exception as e:
            logger.error(f"Error checking permission: {e}")
            return False
    
    async def _log_audit_event(self, team_id: str, user_id: str, action: str, 
                             resource_type: str, resource_id: Optional[str], 
                             description: str, metadata: Optional[Dict] = None):
        """Log audit event"""
        try:
            audit_doc = {
                "team_id": team_id,
                "user_id": user_id,
                "action": action,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "description": description,
                "metadata": metadata or {},
                "timestamp": datetime.utcnow()
            }
            
            await self.audit_logs_collection.insert_one(audit_doc)
            
        except Exception as e:
            logger.error(f"Error logging audit event: {e}")
    
    def _generate_invitation_token(self) -> str:
        """Generate secure invitation token"""
        return secrets.token_urlsafe(32)