""""""

from typing import Any, Optional, Type

import grpc


class GRPCController:
    def __init__(
        self,
        stub_class: Type[Any],
        address: str,
        secure: bool = False,
        cert_path: Optional[str] = None,
    ):
        if secure:
            credentials = grpc.ssl_channel_credentials(
                root_certificates=open(cert_path, "rb").read() if cert_path else None
            )
            self.channel = grpc.secure_channel(address, credentials)
        else:
            self.channel = grpc.insecure_channel(address)

        self.stub = stub_class(self.channel)

    def call(self, method_name: str, request_obj: Any) -> Any:
        method = getattr(self.stub, method_name)
        return method(request_obj)


from amt_nano.proto.arsmedicatech.fhir_sync_pb2 import Patient, PatientRef
from amt_nano.proto.arsmedicatech.fhir_sync_pb2_grpc import FhirSyncStub
from amt_nano.proto.google.fhir.proto.r5.core.resources import patient_pb2


class PatientController(GRPCController):
    def __init__(
        self,
        address: str = "localhost:50051",
        secure: bool = False,
        cert_path: Optional[str] = None,
    ):
        super().__init__(FhirSyncStub, address, secure, cert_path)

    # def create_patient(self, patient: patient_pb2.Patient):
    #     request = CreatePatientRequest(resource=patient)
    #     return self.call("CreatePatient", request)

    def get_patient(self, patient_id: str):
        request = PatientRef(id=patient_id)
        return self.call("GetPatient", request)

    def update_patient(self, patient: patient_pb2.Patient):
        # Convert from FHIR R5 Patient to our Patient message
        # You'll need to implement this conversion based on your needs
        request = Patient(
            id=patient.id.value,
            # Add other field mappings as needed
        )
        return self.call("UpsertPatient", request)

    # def delete_patient(self, patient_id: str):
    #     request = DeletePatientRequest(id=patient_id)
    #     return self.call("DeletePatient", request)
