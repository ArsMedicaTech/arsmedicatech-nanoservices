""""""

from amt_nano.services.grpc_service import PatientController
from google.fhir.proto.r5.core.resources import patient_pb2

controller = PatientController(
    address="my.grpc.server:443", secure=True, cert_path="path/to/ca.crt"
)

# Create and send a patient
p = patient_pb2.Patient()
p.id.value = "example-id"
# Add name, gender, birthdate, etc.

response = controller.create_patient(p)
print("Created:", response)

# Fetch by ID
fetched = controller.get_patient("example-id")
print("Fetched:", fetched)

# Delete
controller.delete_patient("example-id")

"""
# Create a Patient instance
patient = patient_pb2.Patient()

# Set ID
patient.id.value = "example-patient-123"

# Set name
name = datatypes_pb2.HumanName()
name.given.add().value = "Jane"
name.family.value = "Doe"
patient.name.append(name)

# Set gender using enum value
gender = patient_pb2.Patient.GenderCode()
gender.value = codes_pb2.AdministrativeGenderCode.Value.FEMALE
patient.gender.CopyFrom(gender)

# Set birth date
birth_date = datatypes_pb2.Date()
birth_date.value_us = 19900101  # yyyyMMdd format
patient.birth_date.CopyFrom(birth_date)

# Set telecom (phone)
telecom = datatypes_pb2.ContactPoint()
telecom.system.value = codes_pb2.ContactPointSystemCode.Value.PHONE
telecom.value.value = "+15551234567"
telecom.use.value = codes_pb2.ContactPointUseCode.Value.MOBILE
patient.telecom.append(telecom)

# Optional: Add identifier
identifier = datatypes_pb2.Identifier()
identifier.system.value = "http://hospital.smarthealth.org/mrn"
identifier.value.value = "MRN-123456"
patient.identifier.append(identifier)

# Print the patient as JSON-like text
print("Patient Object:")
print(patient)

# Optional: serialize to bytes (for sending via gRPC, REST, etc.)
serialized = patient.SerializeToString()

# Optional: convert to JSON (requires MessageToJson from google.protobuf)
from google.protobuf.json_format import MessageToJson

print("\nPatient JSON:")
print(MessageToJson(patient))
"""
