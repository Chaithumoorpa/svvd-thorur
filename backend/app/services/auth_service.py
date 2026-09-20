from app.repositories.user_repo import UserRepository
from app.schemas.user import UserCreate, UserLogin, PasswordChange
from datetime import datetime
from app.models.user import User
from app.core.security import hash_password, verify_password, create_access_token
import logging

from fastapi import HTTPException


class AuthService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository
        self.logger = logging.getLogger(__name__)

    def authenticate_user(self, data: UserLogin):
        """
        Authenticate user by username and password.
        Returns user if valid, else raises 401.
        """
        user = self.user_repository.get_by_username(data.username)
        if (
            not user
            or not verify_password(data.password, user.hashed_password)
            or not user.is_active
        ):
            # Same message for unknown user, wrong password and deactivated
            # account so the response does not reveal which usernames exist.
            self.logger.warning(f"Authentication failed for username: {data.username}")
            raise HTTPException(
                status_code=401,
                detail="Invalid username or password"
            )

        # Update last login
        user.last_login = datetime.now()
        self.user_repository.update(user)
        
        self.logger.info(f"User authenticated: {user.username} (roles={user.roles})")
        return user

    def create_admin_user(self, data: UserCreate):
        """
        Create a new user with specified roles.
        Raises 400 if username already exists or roles are invalid.
        """
        existing = self.user_repository.get_by_username(data.username)
        if existing:
            self.logger.warning(
                f"User creation failed: username '{data.username}' already exists"
            )
            raise HTTPException(
                status_code=400,
                detail="Username already exists"
            )

        if data.email and self.user_repository.get_by_email(data.email):
            raise HTTPException(status_code=400, detail="Email already registered")

        # Validate roles array is not empty (Pydantic validator should catch this, but double-check)
        if not data.roles or len(data.roles) == 0:
            self.logger.error("User creation failed: roles array is empty")
            raise HTTPException(
                status_code=400,
                detail="User must have at least one role"
            )

        hashed_password = hash_password(data.password)
        
        # Convert Enum list to string list for database
        roles_str = [role.value if hasattr(role, 'value') else str(role) for role in data.roles]
        
        self.logger.info(
            f"Creating new user: username={data.username}, roles={roles_str}"
        )
        
        user = User(
            username=data.username,
            email=data.email,
            phone=data.phone,
            hashed_password=hashed_password,
            roles=roles_str,
            must_change_password=True
        )
        created_user = self.user_repository.create(user)
        
        self.logger.info(
            f"User created successfully: id={created_user.id}, "
            f"username={created_user.username}, roles={created_user.roles}"
        )
        
        return created_user

    def create_general_user(self, data: UserCreate):
        """
        Create a new general user with GENERAL_USER role.
        """
        existing = self.user_repository.get_by_username(data.username)
        if existing:
            raise HTTPException(
                status_code=400,
                detail="Username already exists"
            )

        if data.email and self.user_repository.get_by_email(data.email):
            raise HTTPException(status_code=400, detail="Email already registered")

        hashed_password = hash_password(data.password)
        
        user = User(
            username=data.username,
            email=data.email,
            phone=data.phone,
            hashed_password=hashed_password,
            roles=["GENERAL_USER"],
            must_change_password=False
        )
        return self.user_repository.create(user)

    def list_users(self):
        return self.user_repository.get_all()

    def change_password(self, user: User, data: PasswordChange):
        """
        Change user password.
        Raises 401 if current password is incorrect.
        """
        if not verify_password(data.current_password, user.hashed_password):
            raise HTTPException(
                status_code=401,
                detail="Incorrect current password"
            )
        
        user.hashed_password = hash_password(data.new_password)
        user.must_change_password = False
        self.user_repository.update(user)
        return user

    def create_access_token(self, user: User) -> str:
        """
        Create JWT access token for authenticated user with roles array.
        """
        token_data = {
            "sub": user.username,
            "user_id": user.id,
            "roles": user.roles,  # Now an array of roles
            "is_admin": user.is_admin  # Backward compatibility - uses helper property
        }
        
        self.logger.debug(
            f"Creating JWT token: user_id={user.id}, username={user.username}, "
            f"roles={user.roles}, is_admin={user.is_admin}"
        )
        
        return create_access_token(token_data)
