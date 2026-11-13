from fastapi import HTTPException, status

from serum.repos.v1.cash_shifts import CashShiftsRepository
from serum.repos.v1.users import (
    CreateUser,
    DuplicateUserError,
    LastAdminError,
    ProtectedUserError,
    SelfUserOperationError,
    UpdateUser,
    UserInDb,
    UsersRepository,
)
from responses.v1 import ListResponse


def _without_password(user: UserInDb) -> UserInDb:
    """Evita exponer el hash de contraseña en las respuestas HTTP."""
    return user.model_copy(update={"password": ""})


class UsersController:
    def __init__(
        self,
        users_repo: UsersRepository,
        cash_shifts_repo: CashShiftsRepository,
    ) -> None:
        self.users_repo = users_repo
        self.cash_shifts_repo = cash_shifts_repo

    async def create_user(self, body: CreateUser) -> UserInDb:
        try:
            created_user = await self.users_repo.create_user(body)
            return _without_password(created_user)
        except DuplicateUserError as e:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e),
            )

    async def get_all_users(self) -> ListResponse[UserInDb]:
        users = await self.users_repo.get_all_users()
        public_users = [_without_password(user) for user in users]
        return ListResponse(count=len(public_users), data=public_users)

    async def get_user_by_id(self, user_id: str) -> UserInDb:
        user = await self.users_repo.get_user_by_id(user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        return _without_password(user)

    async def update_user_by_id(
        self,
        user_id: str,
        body: UpdateUser,
        actor: UserInDb | None = None,
    ) -> UserInDb:
        if actor is not None and body.isActive is False:
            active_shifts = await self.cash_shifts_repo.get_all_cash_shifts(
                user_id=user_id,
                status="OPEN",
            )
            if active_shifts:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        "No se puede desactivar un usuario con un turno "
                        "de caja abierto"
                    ),
                )

        try:
            updated_user = await self.users_repo.update_user_by_id(
                user_id,
                body,
                actor_id=actor.id if actor is not None else None,
            )
        except DuplicateUserError as e:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e),
            )
        except (ProtectedUserError, SelfUserOperationError) as e:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e),
            )
        except LastAdminError as e:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e),
            )

        if updated_user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        return _without_password(updated_user)

    async def delete_user_by_id(
        self,
        user_id: str,
        actor: UserInDb | None = None,
    ) -> UserInDb:
        try:
            deleted_user = await self.users_repo.delete_user_by_id(
                user_id,
                actor_id=actor.id if actor is not None else None,
            )
        except (ProtectedUserError, SelfUserOperationError) as e:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e),
            )
        except LastAdminError as e:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e),
            )

        if deleted_user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        return _without_password(deleted_user)


users_controller = UsersController(
    users_repo=UsersRepository.get_instance(),
    cash_shifts_repo=CashShiftsRepository.get_instance(),
)
