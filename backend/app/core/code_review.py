"""
Code Review Process Implementation
================================
Automated code review system with quality gates and metrics tracking.
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import json

logger = logging.getLogger(__name__)


class ReviewStatus(Enum):
    """Code review status enumeration."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_CHANGES = "needs_changes"
    MERGED = "merged"


class ReviewSeverity(Enum):
    """Review issue severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ReviewIssue:
    """Code review issue data structure."""
    id: str
    file_path: str
    line_number: int
    severity: ReviewSeverity
    category: str
    description: str
    suggestion: Optional[str] = None
    reviewer: Optional[str] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


@dataclass
class CodeReview:
    """Code review data structure."""
    id: str
    pull_request_id: str
    author: str
    reviewers: List[str]
    status: ReviewStatus
    issues: List[ReviewIssue]
    metrics: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    merged_at: Optional[datetime] = None


class CodeReviewService:
    """
    Service for managing code reviews and quality gates.
    """
    
    def __init__(self):
        self.reviews: Dict[str, CodeReview] = {}
        self.quality_gates = self._initialize_quality_gates()
        logger.info("Initialized CodeReviewService")
    
    def _initialize_quality_gates(self) -> Dict[str, Any]:
        """Initialize quality gate thresholds."""
        return {
            "max_issues_per_review": 10,
            "max_critical_issues": 0,
            "max_high_issues": 2,
            "min_reviewers": 2,
            "max_file_size_mb": 1,
            "min_test_coverage": 90,
            "max_complexity": 10,
            "max_duplication": 5
        }
    
    async def create_review(self, 
                           pull_request_id: str, 
                           author: str, 
                           reviewers: List[str],
                           files_changed: List[str]) -> CodeReview:
        """
        Create a new code review.
        
        Args:
            pull_request_id (str): Pull request ID
            author (str): Author of the changes
            reviewers (List[str]): List of reviewer usernames
            files_changed (List[str]): List of changed files
            
        Returns:
            CodeReview: Created review instance
        """
        try:
            logger.info(f"Creating code review for PR {pull_request_id}")
            
            # Generate review ID
            review_id = f"review_{pull_request_id}_{int(datetime.utcnow().timestamp())}"
            
            # Analyze files for issues
            issues = await self._analyze_files(files_changed)
            
            # Calculate metrics
            metrics = await self._calculate_metrics(files_changed, issues)
            
            # Create review
            review = CodeReview(
                id=review_id,
                pull_request_id=pull_request_id,
                author=author,
                reviewers=reviewers,
                status=ReviewStatus.PENDING,
                issues=issues,
                metrics=metrics,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # Store review
            self.reviews[review_id] = review
            
            # Check quality gates
            await self._check_quality_gates(review)
            
            logger.info(f"Created code review {review_id} with {len(issues)} issues")
            return review
            
        except Exception as e:
            logger.error(f"Failed to create code review: {e}")
            raise Exception(f"Failed to create code review: {str(e)}")
    
    async def _analyze_files(self, files: List[str]) -> List[ReviewIssue]:
        """Analyze files for potential issues."""
        issues = []
        
        for file_path in files:
            try:
                # Basic file analysis
                file_issues = await self._analyze_single_file(file_path)
                issues.extend(file_issues)
                
            except Exception as e:
                logger.warning(f"Failed to analyze file {file_path}: {e}")
                # Add a generic issue for analysis failure
                issues.append(ReviewIssue(
                    id=f"analysis_error_{len(issues)}",
                    file_path=file_path,
                    line_number=0,
                    severity=ReviewSeverity.MEDIUM,
                    category="analysis",
                    description=f"Failed to analyze file: {str(e)}"
                ))
        
        return issues
    
    async def _analyze_single_file(self, file_path: str) -> List[ReviewIssue]:
        """Analyze a single file for issues."""
        issues = []
        
        # File size check
        try:
            import os
            file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
            if file_size > self.quality_gates["max_file_size_mb"]:
                issues.append(ReviewIssue(
                    id=f"file_size_{len(issues)}",
                    file_path=file_path,
                    line_number=0,
                    severity=ReviewSeverity.MEDIUM,
                    category="file_size",
                    description=f"File size ({file_size:.2f}MB) exceeds limit ({self.quality_gates['max_file_size_mb']}MB)",
                    suggestion="Consider splitting the file into smaller modules"
                ))
        except Exception:
            pass
        
        # Basic code quality checks
        if file_path.endswith('.py'):
            issues.extend(await self._analyze_python_file(file_path))
        elif file_path.endswith(('.ts', '.tsx', '.js', '.jsx')):
            issues.extend(await self._analyze_typescript_file(file_path))
        
        return issues
    
    async def _analyze_python_file(self, file_path: str) -> List[ReviewIssue]:
        """Analyze Python file for issues."""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Check for common Python issues
            for i, line in enumerate(lines, 1):
                line = line.strip()
                
                # Long lines
                if len(line) > 120:
                    issues.append(ReviewIssue(
                        id=f"long_line_{i}",
                        file_path=file_path,
                        line_number=i,
                        severity=ReviewSeverity.LOW,
                        category="style",
                        description=f"Line too long ({len(line)} characters)",
                        suggestion="Break into multiple lines"
                    ))
                
                # TODO comments
                if 'TODO' in line.upper():
                    issues.append(ReviewIssue(
                        id=f"todo_{i}",
                        file_path=file_path,
                        line_number=i,
                        severity=ReviewSeverity.LOW,
                        category="maintenance",
                        description="TODO comment found",
                        suggestion="Address TODO before merging"
                    ))
                
                # FIXME comments
                if 'FIXME' in line.upper():
                    issues.append(ReviewIssue(
                        id=f"fixme_{i}",
                        file_path=file_path,
                        line_number=i,
                        severity=ReviewSeverity.MEDIUM,
                        category="maintenance",
                        description="FIXME comment found",
                        suggestion="Address FIXME before merging"
                    ))
                
                # Hardcoded strings
                if 'password' in line.lower() and '=' in line:
                    issues.append(ReviewIssue(
                        id=f"hardcoded_password_{i}",
                        file_path=file_path,
                        line_number=i,
                        severity=ReviewSeverity.HIGH,
                        category="security",
                        description="Potential hardcoded password",
                        suggestion="Use environment variables or secure configuration"
                    ))
        
        except Exception as e:
            logger.warning(f"Failed to analyze Python file {file_path}: {e}")
        
        return issues
    
    async def _analyze_typescript_file(self, file_path: str) -> List[ReviewIssue]:
        """Analyze TypeScript/JavaScript file for issues."""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Check for common TypeScript/JavaScript issues
            for i, line in enumerate(lines, 1):
                line = line.strip()
                
                # Long lines
                if len(line) > 120:
                    issues.append(ReviewIssue(
                        id=f"long_line_{i}",
                        file_path=file_path,
                        line_number=i,
                        severity=ReviewSeverity.LOW,
                        category="style",
                        description=f"Line too long ({len(line)} characters)",
                        suggestion="Break into multiple lines"
                    ))
                
                # Console.log statements
                if 'console.log' in line and not line.startswith('//'):
                    issues.append(ReviewIssue(
                        id=f"console_log_{i}",
                        file_path=file_path,
                        line_number=i,
                        severity=ReviewSeverity.LOW,
                        category="debugging",
                        description="Console.log statement found",
                        suggestion="Remove or replace with proper logging"
                    ))
                
                # TODO comments
                if 'TODO' in line.toUpperCase():
                    issues.append(ReviewIssue(
                        id=f"todo_{i}",
                        file_path=file_path,
                        line_number=i,
                        severity=ReviewSeverity.LOW,
                        category="maintenance",
                        description="TODO comment found",
                        suggestion="Address TODO before merging"
                    ))
        
        except Exception as e:
            logger.warning(f"Failed to analyze TypeScript file {file_path}: {e}")
        
        return issues
    
    async def _calculate_metrics(self, files: List[str], issues: List[ReviewIssue]) -> Dict[str, Any]:
        """Calculate review metrics."""
        metrics = {
            "total_files": len(files),
            "total_issues": len(issues),
            "critical_issues": len([i for i in issues if i.severity == ReviewSeverity.CRITICAL]),
            "high_issues": len([i for i in issues if i.severity == ReviewSeverity.HIGH]),
            "medium_issues": len([i for i in issues if i.severity == ReviewSeverity.MEDIUM]),
            "low_issues": len([i for i in issues if i.severity == ReviewSeverity.LOW]),
            "issues_by_category": {},
            "files_with_issues": len(set(i.file_path for i in issues))
        }
        
        # Group issues by category
        for issue in issues:
            category = issue.category
            if category not in metrics["issues_by_category"]:
                metrics["issues_by_category"][category] = 0
            metrics["issues_by_category"][category] += 1
        
        return metrics
    
    async def _check_quality_gates(self, review: CodeReview) -> bool:
        """Check if review passes quality gates."""
        metrics = review.metrics
        
        # Check critical issues
        if metrics["critical_issues"] > self.quality_gates["max_critical_issues"]:
            logger.warning(f"Review {review.id} failed quality gate: too many critical issues")
            return False
        
        # Check high issues
        if metrics["high_issues"] > self.quality_gates["max_high_issues"]:
            logger.warning(f"Review {review.id} failed quality gate: too many high severity issues")
            return False
        
        # Check total issues
        if metrics["total_issues"] > self.quality_gates["max_issues_per_review"]:
            logger.warning(f"Review {review.id} failed quality gate: too many total issues")
            return False
        
        logger.info(f"Review {review.id} passed all quality gates")
        return True
    
    async def add_review_comment(self, 
                                review_id: str, 
                                issue_id: str, 
                                comment: str, 
                                reviewer: str) -> bool:
        """Add a comment to a review issue."""
        try:
            if review_id not in self.reviews:
                raise ValueError(f"Review {review_id} not found")
            
            review = self.reviews[review_id]
            issue = next((i for i in review.issues if i.id == issue_id), None)
            
            if not issue:
                raise ValueError(f"Issue {issue_id} not found")
            
            # Update issue with reviewer comment
            issue.reviewer = reviewer
            issue.suggestion = comment
            
            # Update review timestamp
            review.updated_at = datetime.utcnow()
            
            logger.info(f"Added comment to issue {issue_id} in review {review_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add review comment: {e}")
            return False
    
    async def approve_review(self, review_id: str, reviewer: str) -> bool:
        """Approve a code review."""
        try:
            if review_id not in self.reviews:
                raise ValueError(f"Review {review_id} not found")
            
            review = self.reviews[review_id]
            
            # Check if reviewer is authorized
            if reviewer not in review.reviewers:
                raise ValueError(f"Reviewer {reviewer} not authorized for this review")
            
            # Update review status
            review.status = ReviewStatus.APPROVED
            review.updated_at = datetime.utcnow()
            
            logger.info(f"Review {review_id} approved by {reviewer}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to approve review: {e}")
            return False
    
    async def reject_review(self, review_id: str, reviewer: str, reason: str) -> bool:
        """Reject a code review."""
        try:
            if review_id not in self.reviews:
                raise ValueError(f"Review {review_id} not found")
            
            review = self.reviews[review_id]
            
            # Check if reviewer is authorized
            if reviewer not in review.reviewers:
                raise ValueError(f"Reviewer {reviewer} not authorized for this review")
            
            # Update review status
            review.status = ReviewStatus.REJECTED
            review.updated_at = datetime.utcnow()
            
            logger.info(f"Review {review_id} rejected by {reviewer}: {reason}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to reject review: {e}")
            return False
    
    async def get_review(self, review_id: str) -> Optional[CodeReview]:
        """Get a code review by ID."""
        return self.reviews.get(review_id)
    
    async def get_reviews_by_author(self, author: str) -> List[CodeReview]:
        """Get all reviews by an author."""
        return [review for review in self.reviews.values() if review.author == author]
    
    async def get_reviews_by_reviewer(self, reviewer: str) -> List[CodeReview]:
        """Get all reviews assigned to a reviewer."""
        return [review for review in self.reviews.values() if reviewer in review.reviewers]
    
    async def get_review_metrics(self) -> Dict[str, Any]:
        """Get overall review metrics."""
        total_reviews = len(self.reviews)
        if total_reviews == 0:
            return {"total_reviews": 0}
        
        approved_reviews = len([r for r in self.reviews.values() if r.status == ReviewStatus.APPROVED])
        rejected_reviews = len([r for r in self.reviews.values() if r.status == ReviewStatus.REJECTED])
        pending_reviews = len([r for r in self.reviews.values() if r.status == ReviewStatus.PENDING])
        
        total_issues = sum(len(r.issues) for r in self.reviews.values())
        avg_issues_per_review = total_issues / total_reviews if total_reviews > 0 else 0
        
        return {
            "total_reviews": total_reviews,
            "approved_reviews": approved_reviews,
            "rejected_reviews": rejected_reviews,
            "pending_reviews": pending_reviews,
            "approval_rate": (approved_reviews / total_reviews) * 100 if total_reviews > 0 else 0,
            "total_issues": total_issues,
            "avg_issues_per_review": round(avg_issues_per_review, 2)
        }