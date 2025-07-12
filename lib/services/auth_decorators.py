"""
Authentication decorators for Flask routes.
"""
from functools import wraps
from typing import Any, Callable, Optional, TypeVar, cast

from flask import g, jsonify, request, session

from lib.models.user import UserSession
from lib.services.user_service import UserService
from settings import logger

F = TypeVar('F', bound=Callable[..., Any])


def require_auth(f: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator to require authentication for a route

    This decorator checks for a valid session token in the request headers or session.
    If a valid token is found, it validates the session and adds user information to the request context.
    If no valid token is found, it returns a 401 Unauthorized response.

    :param: f: The function to decorate (Flask route handler).
    :return: The decorated function that checks authentication.
    """
    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        """
        Decorated function that checks for a valid session token and adds user info to request context.
        :param args: Args passed to the decorated function.
        :param kwargs: Keyword args passed to the decorated function.
        :return: Optional[Callable]: The original function if authentication is successful, otherwise a 401 response.
        """
        # Get token from request headers or session
        token = request.headers.get('Authorization')
        if token and token.startswith('Bearer '):
            token = token[7:]  # Remove 'Bearer ' prefix
            logger.debug(f"Got Bearer token: {token[:10]}...")
        
        if not token:
            token = session.get('auth_token') # type: ignore
            token = str(token) if token is not None else None # type: ignore
            logger.debug(f"Got session token: {token[:10] if token else 'None'}...")
        
        if not token:
            logger.debug("No token found")
            return jsonify({"error": "Authentication required"}), 401
        
        # Validate session
        user_service = UserService()
        user_service.connect()
        try:
            logger.debug(f"Validating session token: {token[:10]}...")
            user_session = user_service.validate_session(str(token))
            if not user_session:
                logger.debug("Session validation failed")
                return jsonify({"error": "Invalid or expired session"}), 401
            
            logger.debug(f"Session validated for user: {user_session.username}")
            # Add user info to request context
            g.user_session = user_session
            g.user_id = user_session.user_id
            g.user_role = user_session.role
            
            return f(*args, **kwargs)
        finally:
            user_service.close()
    
    return cast(Callable[..., Any], decorated_function)


def require_role(required_role: str) -> Callable[[F], F]:
    """
    Decorator to require a specific role for a route

    This decorator first checks if the user is authenticated, and then checks if the user has the required role.
    If the user is not authenticated or does not have the required role, it returns a 403 Forbidden response.
    :param required_role: The role that the user must have to access the route.
    :return: The decorated function that checks authentication and role.
    """
    def decorator(f: F) -> F:
        """
        Decorator function that checks for user authentication and required role.
        :param f: The function to decorate (Flask route handler).
        :return: Callable: The decorated function that checks authentication and role.
        """
        @wraps(f)
        def decorated_function(*args: Any, **kwargs: Any) -> Any:
            """
            Decorated function that checks for user authentication and required role.
            :param args: Args passed to the decorated function.
            :param kwargs: Keyword args passed to the decorated function.
            :return: Optional[Callable]: The original function if authentication and role checks pass, otherwise a 403 response.
            """
            # First check authentication
            auth_result = require_auth(lambda: None)()
            if auth_result is not None:
                return auth_result
            
            # Then check role
            user_session = getattr(g, 'user_session', None)
            if not user_session:
                return jsonify({"error": "Authentication required"}), 401
            
            # Check if user has required role
            user_service = UserService()
            user_service.connect()
            try:
                user = user_service.get_user_by_id(user_session.user_id)
                if not user or not user.has_role(required_role):
                    return jsonify({"error": f"Role '{required_role}' required"}), 403
                
                return f(*args, **kwargs)
            finally:
                user_service.close()
        
        return decorated_function  # type: ignore
    return decorator

def require_admin(f: F) -> F:
    """
    Decorator to require admin role

    This decorator checks if the user has the 'admin' role.
    If the user does not have the required role, it returns a 403 Forbidden response.
    :param f: The function to decorate (Flask route handler).
    :return: The decorated function that checks for admin role.
    """
    return require_role('admin')(f)


def require_provider(f: F) -> F:
    """
    Decorator to require provider role

    This decorator checks if the user has the 'provider' role.
    If the user does not have the required role, it returns a 403 Forbidden response.
    :param f: The function to decorate (Flask route handler).
    :return: The decorated function that checks for provider role.
    """
    return require_role('provider')(f)


def require_patient(f: F) -> F:
    """
    Decorator to require patient role

    This decorator checks if the user has the 'patient' role.
    If the user does not have the required role, it returns a 403 Forbidden response.
    :param f: The function to decorate (Flask route handler).
    :return: The decorated function that checks for patient role.
    """
    return require_role('patient')(f)


def optional_auth(f: F) -> F:
    """
    Decorator to optionally authenticate user (doesn't fail if no auth)

    This decorator checks for a valid session token in the request headers or session.
    If a valid token is found, it validates the session and adds user information to the request context.
    If no valid token is found, it simply allows the request to proceed without authentication.
    :param f: The function to decorate (Flask route handler).
    :return: The decorated function that checks for optional authentication.
    """
    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        """
        Decorated function that checks for optional authentication.
        :param args: Args passed to the decorated function.
        :param kwargs: Keyword args passed to the decorated function.
        :return: Any: The original function result, regardless of authentication.
        """
        # Get token from request headers or session
        token = request.headers.get('Authorization')
        if token and token.startswith('Bearer '):
            token = token[7:]  # Remove 'Bearer ' prefix
        
        if not token:
            token = session.get('auth_token') # type: ignore
        
        if token:
            # Try to validate session
            user_service = UserService()
            user_service.connect()
            try:
                user_session = user_service.validate_session(token) # type: ignore
                if user_session:
                    # Add user info to request context
                    g.user_session = user_session
                    g.user_id = user_session.user_id
                    g.user_role = user_session.role
            finally:
                user_service.close()

        return cast(F, decorated_function)

    return cast(F, decorated_function)


def get_current_user() -> Optional[UserSession]:
    """
    Get current authenticated user session

    This function retrieves the current user session from the request context.
    If no user session is found, it returns None.
    :return: Optional[UserSession]: The current user session if available, otherwise None.
    """
    return getattr(g, 'user_session', None)


def get_current_user_id() -> Optional[str]:
    """
    Get current authenticated user ID

    This function retrieves the current user ID from the request context.
    If no user ID is found, it returns None.
    :return: Optional[str]: The current user ID if available, otherwise None.
    """
    return getattr(g, 'user_id', None)


def get_current_user_role() -> Optional[str]:
    """
    Get current authenticated user role

    This function retrieves the current user role from the request context.
    If no user role is found, it returns None.
    :return: Optional[str]: The current user role if available, otherwise None.
    """
    return getattr(g, 'user_role', None)
