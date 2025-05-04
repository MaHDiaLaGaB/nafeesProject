from sqlalchemy.orm import Session

from crud.base_crud import BaseCRUD
from models import User

class UserCRUD(BaseCRUD[User]):
    pass

def get_user_crud(db: Session) -> UserCRUD:
    from app.models import User  # local import to avoid circular
    return UserCRUD(User, db)