"""Manage authentication flow for FastAPI endpoints with no-op auth."""

import logging

import requests
from fastapi import Request

from ols.constants import DEFAULT_USER_NAME, DEFAULT_USER_UID, NO_USER_TOKEN

from .auth_dependency_interface import AuthDependencyInterface

logger = logging.getLogger(__name__)


# TODO: PoC - This is a copy of the Noop one , but just reading the X-DAB-JW-TOKEN header as well.

class AuthDependency(AuthDependencyInterface):
    """Create an AuthDependency Class that allows customizing the acces Scope path to check."""

    def __init__(self, virtual_path: str = "/ols-access") -> None:
        logger.error("ROGER :: INIT AAP AuthDependency")
        """Initialize the required allowed paths for authorization checks."""
        self.virtual_path = virtual_path
        # skip user_id suid check if noop auth to allow consumers provide user_id
        self.skip_userid_check = True

    async def __call__(self, request: Request) -> tuple[str, str, bool, str]:
        user_token = NO_USER_TOKEN  # no-op auth yield no token

        aap_jwt = request.headers.get("X-DAB-JW-TOKEN")
        # TODO: PoC.
        if aap_jwt is not None:
            response = requests.get(
                url="https://localhost/api/controller/v2/me/",
                headers={"Content-Type": "application/json", "Accept": "application/json", "X-DAB-JW-TOKEN": aap_jwt},
                verify=False,
            )
            logger.debug("ROGER :: Calling ME in AAP CONTROLLER API :: " + str(response.text))


        user_id = request.query_params.get("user_id", DEFAULT_USER_UID)
        logger.info("User ID: %s", user_id)
        return user_id, DEFAULT_USER_NAME, self.skip_userid_check, user_token
