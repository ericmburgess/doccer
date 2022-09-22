from abc import abstractmethod
import os

import tomli


class ProjectReader:
    @property
    @abstractmethod
    def project_name(self) -> str:
        ...


class PyprojectReader(ProjectReader):
    def __init__(self, pyproject_path: os.PathLike):
        with open(pyproject_path, "rb") as f:
            self.toml = tomli.load(f)
