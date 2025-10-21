# ArsMedicaTech Nanoservices

## About

TBD.

## Usage

1. Create virtual environment: `python3 -m venv .venv`.
2. Activate virtual environment:
* Windows: `.\.venv\Scripts\activate`.
* Linux: `source .venv/bin/activate`.
3. Install requirements: `pip install -r requirements.txt`.
4. Add generated protos (from `fhir-sync`).
5. Install as editable: `pip install -e .`.

### Example Message Construction

```python
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
```
