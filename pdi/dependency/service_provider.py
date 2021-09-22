import os

from multiprocessing.process import current_process
from typing import TypeVar, Type

from flask import Flask
from flask_injector import FlaskInjector, request
from flask_restx import Api
from injector import singleton, Injector, threadlocal, Binder
from sqlalchemy import MetaData
from sqlalchemy.ext.declarative import declarative_base
from werkzeug.utils import redirect

from .scopes import ISingleton, IScoped
from ..api.base import ResourceBase
from ..configuration.models import ApiConfig, ApplicationConfig, DatabaseConfig
from ..configuration import ConfigManager
from ..logging.console_logger import ConsoleLogger
from ..utils import ModuleFinder

T = TypeVar('T')


class ServiceProvider:
    Base = declarative_base(metadata=MetaData(schema='Common'))

    def __init__(self, root_directory: str) -> None:
        self.app: Flask = None
        self.api: Api = None
        self.config_manager: ConfigManager = None
        self.module_finder: ModuleFinder = None
        self.injector: Injector = None
        self.binder: Injector = None
        self.logger = ConsoleLogger()
        self.logger.info(f"Application initialize started")
        self.root_directory = root_directory
        self.configure_startup(self.root_directory)
        self.process_info()

    def get(self, instance_type: Type[T]) -> T:
        return self.injector.get(instance_type)

    def import_controllers(self):
        self.module_finder.import_modules(included_modules=['controllers'])

    def initialize_injection(self):
        FlaskInjector(app=self.app, modules=[self.configure], injector=self.injector)

    def initialize_flask(self):

        application_config: ApplicationConfig = self.config_manager.get(ApplicationConfig)
        api_config: ApiConfig = self.config_manager.get(ApiConfig)
        application_name = ''
        if application_config is not None and application_config.name is not None:
            application_name = application_config.name
        self.app = Flask(application_name)

        @self.app.route('/')
        def home_redirect():
            # Redirect from here, replace your custom site url "www.google.com"
            return redirect("/documentation", code=302, Response=None)

        self.api = Api(self.app,
                       title='Python Data Integrator API',
                       version='v0.1',
                       doc='/documentation',
                       base_url='/')

    def configure_startup(self, root_directory):
        # Importing all modules for dependency
        application_config = ApplicationConfig(root_directory=root_directory)
        self.module_finder = ModuleFinder(root_directory=root_directory)
        self.module_finder.import_modules(excluded_modules=['controllers', 'tests'])

        # Configuration initialize
        self.config_manager = ConfigManager(root_directory=root_directory, module_finder=self.module_finder)
        self.set_database_application_name()

        self.initialize_flask()

        self.injector = Injector()

    def set_database_application_name(self):
        application_config = self.config_manager.get(ApplicationConfig)
        database_config: DatabaseConfig = self.config_manager.get(DatabaseConfig)
        if database_config is not None and database_config.application_name is None:
            process_info = self.get_process_info()
            hostname = os.getenv('HOSTNAME', '')
            self.config_manager.set(ApplicationConfig, "hostname", hostname)
            self.config_manager.set(DatabaseConfig, "application_name", f"{application_config.name}-({process_info})")

    def configure(self, binder: Binder):
        self.binder = binder
        binder.bind(
            Flask,
            to=self.app
        )
        binder.bind(
            Api,
            to=self.api
        )
        for config in self.config_manager.get_all():
            binder.bind(
                config.get("type"),
                to=config.get("instance"),
                scope=singleton,
            )

        for singletonScope in ISingleton.__subclasses__():
            binder.bind(
                singletonScope,
                to=singletonScope,
                scope=singleton,
            )

        for scoped in IScoped.__subclasses__():
            binder.bind(
                scoped,
                to=scoped,
                scope=threadlocal,
            )

    def configure_controller(self):
        for controller in ResourceBase.__subclasses__():
            self.binder.bind(
                controller,
                to=controller,
                scope=request,
            )

    def get_process_info(self):
        return f"{current_process().name} ({os.getpid()},{os.getppid()})"

    def process_info(self):
        logger = ConsoleLogger()
        application_config: ApplicationConfig = self.config_manager.get(ApplicationConfig)
        if application_config is not None:
            hostname = f'-{application_config.hostname}' if (
                    application_config.hostname is not None and application_config.hostname != '') else ''
            logger.info(f"Application : {application_config.name}{hostname}")
