""""""

import datetime

# Pre-load the dependencies into the protobuf registry.
import google.protobuf.any_pb2  # noqa
import google.protobuf.timestamp_pb2  # noqa
from arsmedicatech.fhir_sync_pb2 import Patient

from amt_nano.services.grpc_service import PatientController
from settings import GRPC_URL

controller = PatientController(address=GRPC_URL, secure=True)


def test():
    # Create and send a patient
    p = Patient()
    p.id = "example-id"
    p.gender = "male"
    p.name.family = "Doe"
    p.name.given.append("John")

    mrn = p.identifier.add()
    mrn.system = "http://hospital.smarthealth.org/mrn"
    mrn.value = "MRN-123456"

    p.identifier.add(system="http://hl7.org/fhir/sid/us-ssn", value="123-45-6789")

    birth_date = datetime.datetime(1985, 5, 22)
    p.birth.FromDatetime(birth_date)

    response = controller.update_patient(p)
    print("Created:", response)

    assert response.id == p.id

    # Fetch by ID
    # fetched = controller.get_patient("example-id")
    # print("Fetched:", fetched)

    # Delete
    # controller.delete_patient("example-id")


if __name__ == "__main__":
    test()
