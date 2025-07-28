from sqlalchemy.orm import Session

from app.crud.base_crud import BaseCRUD
from app.models import User


class UserCRUD(BaseCRUD[User]):
    pass


def get_user_crud(db: Session) -> UserCRUD:
    from app.models import User  # local import to avoid circular

    return UserCRUD(User, db)
