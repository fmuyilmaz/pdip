from injector import inject

from pdi.api.base import ResourceBase
from pdi.api.decorators import controller
from pdi.data import RepositoryProvider
from tests.api.basic_app_db_model.models.dao.User import User


@controller()
class BasicApiDbModelResource(ResourceBase):
    @inject
    def __init__(self,
                 repository_provider: RepositoryProvider,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.repository_provider = repository_provider

    def get(self, name: str) -> str:
        user_repository = self.repository_provider.get(User)
        new_user = User()
        new_user.Name = name
        user_repository.insert(new_user)
        self.repository_provider.commit()
        user = user_repository.filter_by(Name=name).first()
        return "username:" + user.Name