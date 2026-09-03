from typing import List, Dict, Any, Optional
import httpx
from loguru import logger
import asyncio

from app.api.schemas import Project
from app.automation.session_manager import load_storage_state
from app.automation.components.project_parser import parse_project_json
from app.automation.antiban import antiban


class WorkanaAPIClient:
    """
    Client for accessing Workana internal API endpoints using user session.
    """

    BASE_URL = "https://www.workana.com"

    @staticmethod
    async def _get_client(user_id: str) -> Optional[httpx.AsyncClient]:
        """Creates an httpx client with the user's cookies and standard headers."""
        storage_state = await load_storage_state(user_id)
        if not storage_state or not storage_state.get("cookies"):
            logger.warning(f"No valid session found for user {user_id}")
            return None

        # Convert to httpx cookies
        cookies = {}
        for cookie in storage_state.get("cookies", []):
            cookies[cookie["name"]] = cookie["value"]

        headers = {
            "Accept": "application/json",
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": antiban.get_random_user_agent(),
        }

        return httpx.AsyncClient(
            base_url=WorkanaAPIClient.BASE_URL,
            cookies=cookies,
            headers=headers,
            timeout=15.0,
            follow_redirects=True,
        )

    async def get_recommended_projects(self, user_id: str) -> List[Project]:
        """Fetches recommended projects for the user."""
        client = await self._get_client(user_id)
        if not client:
            return []

        try:
            async with client:
                response = await client.get("/dashboard/recommended_projects")

                if response.status_code == 403 or response.status_code == 401:
                    logger.warning(
                        f"Session expired or blocked (status {response.status_code}) for user {user_id}"
                    )
                    return []

                response.raise_for_status()
                data = response.json()

                projects_data = data.get("projects", [])
                parsed_projects = []

                for p_data in projects_data:
                    project = await parse_project_json(p_data, self.BASE_URL)
                    if project:
                        parsed_projects.append(project)

                return parsed_projects
        except Exception as e:
            logger.error(f"Failed to fetch recommended projects: {e}")
            return []

    async def get_saved_searches(self, user_id: str) -> List[Dict[str, Any]]:
        """Fetches the user's saved searches."""
        client = await self._get_client(user_id)
        if not client:
            return []

        try:
            async with client:
                response = await client.get("/saved_searches/1")

                if response.status_code in (401, 403):
                    logger.warning(
                        f"Session expired or blocked (status {response.status_code}) for user {user_id}"
                    )
                    return []

                response.raise_for_status()
                data = response.json()

                return data.get("savedSearches", [])
        except Exception as e:
            logger.error(f"Failed to fetch saved searches: {e}")
            return []

    async def get_inbox_threads(self, user_id: str) -> List[Dict[str, Any]]:
        """Fetches all chat/inbox threads."""
        client = await self._get_client(user_id)
        if not client:
            return []

        try:
            async with client:
                response = await client.get("/chat/friends")

                if response.status_code in (401, 403):
                    logger.warning(
                        f"Session expired or blocked (status {response.status_code}) for user {user_id}"
                    )
                    return []

                response.raise_for_status()
                data = response.json()

                if isinstance(data, list):
                    return data
                return []
        except Exception as e:
            logger.error(f"Failed to fetch inbox threads: {e}")
            return []

    async def check_proposal_responses(self, user_id: str) -> List[Dict[str, Any]]:
        """Checks inbox for unread messages."""
        threads = await self.get_inbox_threads(user_id)
        unread_projects = []

        for project_chat in threads:
            for thread in project_chat.get("threads", []):
                if thread.get("has_unread"):
                    unread_projects.append(project_chat)
                    break  # Found unread in this project chat

        return unread_projects


workana_api_client = WorkanaAPIClient()
