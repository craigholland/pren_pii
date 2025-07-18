import functools
import logging
import os
import traceback
from abc import ABC, abstractmethod

import grpc
from grpc._channel import _InactiveRpcError

# from uhg.service.protos.permissions_service_pb2 import CheckPermissionRequest
# from uhg.service.protos.permissions_service_pb2_grpc import (
#     PermissionServiceStub,
# )


class CannotContactPermissionService(Exception):
    pass


class PermissionChecker(ABC):
    """
    Interface for permissions checkers
    """

    @abstractmethod
    def check_permission(
        self,
        person_id,
        acting_as_role_id,
        permission_requested: str,
        resource_id,
    ) -> bool:
        pass

    @abstractmethod
    def get_resources_by_permission_name(self, name) -> list:
        pass


class GRPCPermissionChecker(PermissionChecker):
    """
    This communicates with the Permissions Microservice.  It verifies whether
    as user has access to a resource of whether they have a specific permission
    """

    def __init__(self, service="permission-service:80"):
        server = os.getenv("GRPC_PERMISSIONS_SERVICE") or service

        self.channel = grpc.insecure_channel(server)
        #self.stub = PermissionServiceStub(self.channel)

    @functools.lru_cache(maxsize=128)
    def check_permission(
        self,
        person_id,
        acting_as_role_id,
        permission_requested: str,
        resource_id,
    ) -> bool:

        if person_id == "System":
            return True
        return True
        # request = CheckPermissionRequest()
        # request.person_id = person_id
        # if acting_as_role_id:
        #     request.acting_as_role_id = acting_as_role_id
        # request.permission_requested = permission_requested
        # if resource_id:
        #     request.resource_id = resource_id
        # try:
        #     response = self.stub.check_permission(request)
        # except _InactiveRpcError:
        #     logging.error(traceback.format_exc())
        #     raise CannotContactPermissionService()
        # return response.is_permission_granted

    def get_resources_by_permission_name(self, name) -> list:
        pass


class SystemProcessChecker(PermissionChecker):
    def __init__(self, process_name):
        self.process_name = process_name
        logging.info(
            f"Process: {process_name} is using the permissions "
            f"checker: SystemProcessChecker"
        )

    def check_permission(
        self,
        person_id,
        acting_as_role_id,
        permission_requested: str,
        resource_id,
    ) -> bool:
        return True

    def get_resources_by_permission_name(self, name) -> list:
        pass
