from starlite_users import StarliteUsers, StarliteUsersConfig
from starlite_users.config import AuthHandlerConfig

config = StarliteUsersConfig(user_model=User, user_read_dto=UserReadDTO, auth_handler_config=AuthHandlerConfig())
starlite_users = StarliteUsers(config=config)
