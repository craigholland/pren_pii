import atexit
import signal
import grpc
from api.api_main import app
from services.grpc.grpc_main import add_grpc_services
from services.kafka.kafka_main import get_producer, consume_messages
from svc_logger import logger
from config import config
from concurrent import futures

# Configuration

def serve_grpc(cfg, is_internal=False, server_credentials=None):
    server = grpc.server()
    add_grpc_services(server)
    logger_msg = f"'{cfg.service_name}' gRPC server started on port "
    grpc_port = cfg.internal_grpc_port if is_internal else cfg.grpc_port
    grpc_port_str = f'[::]:{grpc_port}'
    logger_msg = "Internal " + logger_msg if is_internal else logger_msg
    logger_msg += f' {grpc_port}'
    if server_credentials:
        server.add_secure_port(grpc_port_str, server_credentials)
        logger_msg += " with SSL"
    else:
        server.add_insecure_port(grpc_port_str)
    logger.info(logger_msg)
    server.start()
    server.wait_for_termination()


def shutdown_handler(signal_received, frame):
    logger.info("Shutting down services")
    producer.close()
    exit(0)


# Start Services
if __name__ == "__main__":
    producer = get_producer(config.kafka_topic)

    with futures.ThreadPoolExecutor(max_workers=10) as executor:
        # Start Kafka Consumer
        future_kafka = executor.submit(consume_messages, config, logger)

        # Start gRPC Servers
        future_grpc = executor.submit(serve_grpc, config)
        future_internal_grpc = executor.submit(serve_grpc, config, True)

        # Start REST API
        future_api = executor.submit(
            app.run, host="0.0.0.0", port=int(config.http_port))

        # Register shutdown handler
        signal.signal(signal.SIGINT, shutdown_handler)
        signal.signal(signal.SIGTERM, shutdown_handler)

        future_kafka.result()
        future_grpc.result()
        future_internal_grpc.result()
        future_api.result()

    atexit.register(lambda: producer.close())