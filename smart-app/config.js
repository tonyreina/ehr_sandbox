// Shared settings. Your client id lives in config.local.js (created by `pixi run smart-setup`).
window.SMART_CONFIG = {
  clientId: "",
  // Must match a Redirect URI registered in code Console exactly.
  redirectUri: new URL("index.html", window.location.href).href,
  // Public, read-only Oracle Health sandbox used when not signed in (no registration needed).
  openBase: "https://fhir-open.cerner.com/r4/ec2458f2-1e24-41c8-b71b-0e701af7583d",
  // Resources requested when signing in via SMART. Each must also be added to the app's scopes in
  // code Console (user/<Resource>.read); sections without a scope show "Not authorized".
  // Extend with e.g. "MedicationRequest", "AllergyIntolerance", "Encounter", "Condition".
  smartResources: ["Patient", "Observation"],
  // The App type chosen in code Console: "provider" or "patient". A client is only accepted
  // by the matching persona (otherwise: error=unauthorized_client, client-persona-mismatch).
  appType: "provider",
  // Standalone launch target for Patient apps (Oracle Health R4 patient-access sandbox).
  // Provider apps can't launch standalone here: start them with Test Sandbox in code Console.
  patientIss: "https://fhir-myrecord.cerner.com/r4/ec2458f2-1e24-41c8-b71b-0e701af7583d",
  // Sandbox test patients offered in the picker (mirrors ehr/patients.py).
  patients: [
    { id: "12724066", label: "Nancy Patchtest" },
    { id: "12724067", label: "Joe Testpatient" },
    { id: "12724065", label: "Wilm Smart" },
    { id: "12742400", label: "Tim Peters" },
  ],
};
