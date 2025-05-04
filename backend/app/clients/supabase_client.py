from typing import Optional

from supabase import Client, create_client
from supabase.lib.client_options import ClientOptions

from core.config import settings
from logger import get_logger

logger = get_logger()


class SupabaseClient:
    def __init__(self) -> None:
        """
        Initialize the Supabase client.

        Args:
            url (str): Supabase URL.
            key (str): Supabase API key.

        Raises:
            ValueError: If the URL or key is not provided.
        """
        self.url = settings.SUPABASE_URL
        self.key = settings.SUPABASE_SECRET_KEY
        if not self.url or not self.key:
            raise ValueError("Supabase URL and key must be provided.")

        try:
            self.client: Client = create_client(
                self.url,
                self.key,
                options=ClientOptions(
                    auto_refresh_token=False,
                    persist_session=False,
                ),
            )
            logger.info("Supabase client initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            raise RuntimeError("Supabase client initialization failed.") from e

    def create_user(self, email: str, password: str, user_data: dict):
        """
        Create a new user in Supabase Auth with metadata using sign_up.

        Args:
            email (str): User's email
            password (str): User's password
            user_data (dict): User metadata to be stored

        Returns:
            dict: Created user data
        """
        try:
            response = self.client.auth.admin.create_user(
                {"email": email, "password": password, "email_confirm": True,"user_metadata": user_data}
            )
            logger.info(f"User account created successfully for {email}")
            return response
        except Exception as e:
            logger.error(f"Error creating user {email}: {e}")
            raise

    def get_auth_user(self):
        """Return user if present in Auth."""
        try:
            response = self.client.auth.admin.list_users()
            emails = [u.email for u in response if getattr(u, "email", None)]
            logger.info(f"this is the get auth user response {emails}")
            if settings.SUPERADMIN_EMAIL in emails:
                return True
            else:
                return False
        except Exception:
            return None
        
    def sign_in(self, email: str, password: str) -> dict:
        """
        Sign in with email+ password and return a dict containing:
          { "token": str, "user": AuthUser }
        """
        try:
            res = self.client.auth.sign_in_with_password(
                {"email": email, "password": password}
            )
            if not res.session or not res.session.access_token:
                raise ValueError("Supabase did not return an access token")
            logger.info(f"token:{res.session.access_token}")
            return {
                "token": res.session.access_token,
                "user": res.user,
            }

        except Exception as e:
            logger.error(f"Signin failed for {email}: {e}")
            raise

    def ensure_superadmin(self) -> None:
        """
        Create the superadmin account once if it doesn't exist.
        The user receives a confirmation email from Supabase automatically.
        """
        email = settings.SUPERADMIN_EMAIL
        password = settings.SUPERADMIN_PASSWORD
        user = self.get_auth_user()
        logger.info(f"the user is {user}")
        if self.get_auth_user():
            logger.info("✅  Superadmin already exists.")
            return

        user_data = {"role": "superadmin", "name": "SuperAdmin"}
        self.create_user(email, password, user_data)
        logger.warning("🚀  Superadmin seeded — **change the default password ASAP!**")

    def safe_query(self, operation: str, *args, **kwargs) -> Optional[dict]:
        """
        Execute a safe query on the Supabase client with exception handling.

        Args:
            operation (str): The client operation to execute (e.g., "table", "rpc").
            *args: Positional arguments for the operation.
            **kwargs: Keyword arguments for the operation.

        Returns:
            Optional[dict]: The result of the operation or None if it failed.
        """
        try:
            method = getattr(self.client, operation, None)
            if not callable(method):
                raise AttributeError(
                    f"Operation '{operation}' does not exist on the client."
                )

            result = method(*args, **kwargs)
            logger.info(f"Operation '{operation}' executed successfully.")
            return result
        except Exception as e:
            logger.error(f"Error executing operation '{operation}': {e}")
            return None
