from grpc_registry.generic_service.service_pb2_grpc import (add_GenericServiceServicer_to_server)
from services.grpc.services import GenericGRPCService

def add_grpc_services(server):
    add_GenericServiceServicer_to_server(GenericGRPCService(), server)


