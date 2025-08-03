""""""
from typing import Any, Optional, Type

import grpc


class GRPCController:
    def __init__(self, stub_class: Type[Any], address: str, secure: bool = False, cert_path: Optional[str] = None):
        if secure:
            credentials = grpc.ssl_channel_credentials(
                root_certificates=open(cert_path, 'rb').read() if cert_path else None
            )
            self.channel = grpc.secure_channel(address, credentials)
        else:
            self.channel = grpc.insecure_channel(address)

        self.stub = stub_class(self.channel)

    def call(self, method_name: str, request_obj: Any) -> Any:
        method = getattr(self.stub, method_name)
        return method(request_obj)
