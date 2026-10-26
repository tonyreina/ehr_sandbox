# Reference

## Oracle Health (Cerner) R4 endpoints

Tenant `ec2458f2-1e24-41c8-b71b-0e701af7583d` is the public sandbox.

| Purpose | URL |
|---|---|
| Open sandbox (no auth, read-only) | `https://fhir-open.cerner.com/r4/<tenant>` |
| Secured sandbox (SMART, EHR launch) | `https://fhir-ehr-code.cerner.com/r4/<tenant>` |
| Patient access (standalone Patient apps) | `https://fhir-myrecord.cerner.com/r4/<tenant>` |
| SMART discovery | `<base>/.well-known/smart-configuration` |

Cerner requires a `category` or `code` on Observation searches. Condition, Immunization and Procedure searches can be slow on large test charts.

## Epic FHIR base URL

```
https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/R4
```

## Token endpoint

```
https://fhir.epic.com/interconnect-fhir-oauth/oauth2/token
```

## Observation categories

| Category | Description |
|---|---|
| `laboratory` | Lab results (CBC, metabolic panel, etc.) |
| `vital-signs` | Blood pressure, heart rate, weight, etc. |
| `imaging` | Radiology and imaging results |
| `procedure` | Procedure notes |

## Common LOINC codes

| Code | Description |
|---|---|
| `4548-4` | Hemoglobin A1C |
| `2345-7` | Glucose |
| `718-7` | Hemoglobin |
| `20570-8` | Hematocrit |
| `777-3` | Platelets |
| `85354-9` | Blood pressure panel |
| `8480-6` / `8462-4` | Systolic / diastolic blood pressure |
| `8867-4` / `69000-8` | Heart rate / pulse (sitting) |
| `8310-5` | Body temperature |
| `2708-6` | Oxygen saturation |
| `9279-1` | Respiratory rate |
| `29463-7` | Body weight |
| `11727-5` | Estimated fetal weight percentile |
| `11979-2` | Abdominal circumference |

## Useful links

- [Epic on FHIR documentation](https://fhir.epic.com/Documentation)
- [Oracle Health FHIR R4 APIs](https://docs.oracle.com/en/industries/health/millennium-platform-apis/mfrap/rest-endpoints.html)
- [Oracle Health: build SMART on FHIR apps](https://docs.oracle.com/en/industries/health/millennium-platform-apis/build-smart-on-fhir-apps/)
- [Oracle Health authorization framework](https://docs.oracle.com/en/industries/health/millennium-platform-apis/fhir-authorization-framework/)
- [code Console](https://code-console.cerner.com/)
- [FHIR R4 specification](https://hl7.org/fhir/R4/)
- [SMART backend services spec](https://hl7.org/fhir/uv/bulkdata/authorization/)
