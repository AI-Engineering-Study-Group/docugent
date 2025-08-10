"""
CSV-based schedule management tools for the API Conference AI Agent.
Reads directly from the CSV file as the source of truth.
"""

import csv
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from google.adk.tools import FunctionTool

from app.config.logger import Logger
from app.config.settings import settings
from app.services.redis_service import RedisService

logger = Logger.get_logger(__name__)
redis_service = RedisService.get_instance()

def _load_csv_data() -> List[Dict[str, Any]]:
    """Load session and speaker data from CSV file."""
    cache_key = "csv_data"
    cached_data = redis_service.get(cache_key)
    if cached_data:
        logger.info("Returning cached CSV data")
        return cached_data

    try:
        csv_path = Path("data/api-conf-lagos-2025 flattened accepted sessions - exported 2025-07-05 - Accepted sessions and speakers.csv")
        if not csv_path.exists():
            logger.warning("CSV file not found")
            return []
        
        sessions = []
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Clean up the data
                session = {
                    'title': row.get('Title', '').strip(),
                    'description': row.get('Description', '').strip(),
                    'owner': row.get('Owner', '').strip(),
                    'owner_email': row.get('Owner Email', '').strip(),
                    'session_format': row.get('Session format', '').strip(),
                    'room': row.get('Room', '').strip(),
                    'scheduled_at': row.get('Scheduled At', '').strip(),
                    'scheduled_duration': row.get('Scheduled Duration', '').strip(),
                    'speaker_id': row.get('Speaker Id', '').strip(),
                    'first_name': row.get('FirstName', '').strip(),
                    'last_name': row.get('LastName', '').strip(),
                    'email': row.get('Email', '').strip(),
                    'tagline': row.get('TagLine', '').strip(),
                    'bio': row.get('Bio', '').strip(),
                    'twitter': row.get('X (Twitter)', '').strip(),
                    'linkedin': row.get('LinkedIn', '').strip(),
                    'company_website': row.get('Company Website', '').strip(),
                    'profile_picture': row.get('Profile Picture', '').strip()
                }
                sessions.append(session)
        
        logger.info(f"Loaded {len(sessions)} sessions from CSV")
        redis_service.set(cache_key, sessions, ttl=86400)  # Cache for 24 hours
        return sessions
        
    except Exception as e:
        logger.error(f"Error loading CSV data: {e}")
        return []

def search_sessions_csv(query: str, **kwargs) -> Optional[Dict[str, Any]]:
    """
    Search for sessions based on title, description, or speaker name using CSV data.
    
    Args:
        query: Search query
        
    Returns:
        Dictionary with matching sessions
    """
    try:
        sessions = _load_csv_data()
        query_lower = query.lower()
        matching_sessions = []
        
        for session in sessions:
            # Create searchable text from title, description, and speaker names
            searchable_text = (
                f"{session.get('title', '')} "
                f"{session.get('description', '')} "
                f"{session.get('first_name', '')} "
                f"{session.get('last_name', '')} "
                f"{session.get('owner', '')}"
            ).lower()
            
            if query_lower in searchable_text:
                # Format the session data for response
                formatted_session = {
                    'title': session.get('title'),
                    'description': session.get('description'),
                    'speaker_name': f"{session.get('first_name', '')} {session.get('last_name', '')}".strip(),
                    'owner': session.get('owner'),
                    'session_format': session.get('session_format'),
                    'room': session.get('room'),
                    'scheduled_at': session.get('scheduled_at'),
                    'scheduled_duration': session.get('scheduled_duration'),
                    'tagline': session.get('tagline'),
                    'bio': session.get('bio'),
                    'twitter': session.get('twitter'),
                    'linkedin': session.get('linkedin'),
                    'company_website': session.get('company_website'),
                    'profile_picture': session.get('profile_picture')
                }
                matching_sessions.append(formatted_session)
        
        return {
            "success": True,
            "query": query,
            "sessions": matching_sessions,
            "count": len(matching_sessions),
            "support_contact": settings.support_phone
        }
        
    except Exception as e:
        logger.error(f"Error searching sessions from CSV: {e}")
        return {
            "error": True,
            "message": "Unable to search sessions from CSV",
            "support_contact": settings.support_phone
        }

def search_speakers_csv(query: str, **kwargs) -> Optional[Dict[str, Any]]:
    """
    Search for speakers by name using CSV data.
    
    Args:
        query: Search query (speaker name)
        
    Returns:
        Dictionary with matching speakers
    """
    try:
        sessions = _load_csv_data()
        query_lower = query.lower()
        matching_speakers = []
        
        for session in sessions:
            first_name = session.get('first_name', '').lower()
            last_name = session.get('last_name', '').lower()
            full_name = f"{first_name} {last_name}".strip()
            
            if (query_lower in first_name or 
                query_lower in last_name or 
                query_lower in full_name):
                
                # Format the speaker data for response
                formatted_speaker = {
                    'name': f"{session.get('first_name', '')} {session.get('last_name', '')}".strip(),
                    'title': session.get('tagline'),
                    'company': session.get('company_website'),
                    'bio': session.get('bio'),
                    'profile_picture': session.get('profile_picture'),
                    'social_links': {
                        'twitter': session.get('twitter'),
                        'linkedin': session.get('linkedin'),
                        'company_website': session.get('company_website')
                    },
                    'sessions': [{
                        'title': session.get('title'),
                        'description': session.get('description'),
                        'session_format': session.get('session_format'),
                        'room': session.get('room'),
                        'scheduled_at': session.get('scheduled_at'),
                        'scheduled_duration': session.get('scheduled_duration')
                    }]
                }
                matching_speakers.append(formatted_speaker)
        
        return {
            "success": True,
            "query": query,
            "speakers": matching_speakers,
            "count": len(matching_speakers),
            "support_contact": settings.support_phone
        }
        
    except Exception as e:
        logger.error(f"Error searching speakers from CSV: {e}")
        return {
            "error": True,
            "message": "Unable to search speakers from CSV",
            "support_contact": settings.support_phone
        }

def get_full_schedule_csv(**kwargs) -> Optional[Dict[str, Any]]:
    """
    Get the complete conference schedule from CSV.
    
    Returns:
        Dictionary with full schedule information
    """
    try:
        sessions = _load_csv_data()
        
        # Group sessions by date
        schedule_by_date = {}
        for session in sessions:
            scheduled_at = session.get('scheduled_at', '')
            if scheduled_at:
                if scheduled_at not in schedule_by_date:
                    schedule_by_date[scheduled_at] = []
                schedule_by_date[scheduled_at].append(session)
        
        return {
            "success": True,
            "schedule": {
                "total_sessions": len(sessions),
                "sessions_by_date": schedule_by_date,
                "all_sessions": sessions
            },
            "support_contact": settings.support_phone
        }
        
    except Exception as e:
        logger.error(f"Error getting full schedule from CSV: {e}")
        return {
            "error": True,
            "message": "Unable to retrieve schedule from CSV",
            "support_contact": settings.support_phone
        }

def get_keynote_speakers_csv(**kwargs) -> Optional[Dict[str, Any]]:
    """
    Get all keynote speakers from the CSV data.
    
    Returns:
        Dictionary with keynote speakers
    """
    try:
        sessions = _load_csv_data()
        keynote_speakers = []
        
        for session in sessions:
            if session.get('session_format', '').lower() == 'keynote':
                # Format the speaker data for response
                formatted_speaker = {
                    'name': f"{session.get('first_name', '')} {session.get('last_name', '')}".strip(),
                    'title': session.get('tagline'),
                    'company': session.get('company_website'),
                    'bio': session.get('bio'),
                    'profile_picture': session.get('profile_picture'),
                    'social_links': {
                        'twitter': session.get('twitter'),
                        'linkedin': session.get('linkedin'),
                        'company_website': session.get('company_website')
                    },
                    'sessions': [{
                        'title': session.get('title'),
                        'description': session.get('description'),
                        'session_format': session.get('session_format'),
                        'room': session.get('room'),
                        'scheduled_at': session.get('scheduled_at'),
                        'scheduled_duration': session.get('scheduled_duration')
                    }]
                }
                keynote_speakers.append(formatted_speaker)
        
        return {
            "success": True,
            "speakers": keynote_speakers,
            "count": len(keynote_speakers),
            "support_contact": settings.support_phone
        }
        
    except Exception as e:
        logger.error(f"Error getting keynote speakers from CSV: {e}")
        return {
            "error": True,
            "message": "Unable to get keynote speakers from CSV",
            "support_contact": settings.support_phone
        }

def get_csv_schedule_tools() -> List[FunctionTool]:
    """Get all CSV-based schedule tools."""
    
    return [
        FunctionTool(search_sessions_csv),
        FunctionTool(search_speakers_csv),
        FunctionTool(get_full_schedule_csv),
        FunctionTool(get_keynote_speakers_csv)
    ]
