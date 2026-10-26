// Shared settings. Per-EHR client ids live in config.local.js (created by `pixi run smart-setup`).
window.SMART_CONFIG = {
  // Default EHR profile. Overridden by ?ehr=, the CLI (`smart-app --ehr`, EHR_TYPE) and launches.
  ehr: "cerner",
  // Must match a Redirect URI registered with the EHR exactly.
  redirectUri: new URL("index.html", window.location.href).href,
  // Legacy single client id (maps to Cerner); prefer clientIds in config.local.js.
  clientId: "",

  profiles: {
    cerner: {
      name: "Oracle Health (Cerner)",
      issMatch: "cerner.com",
      // Public, read-only sandbox used when not signed in (no registration needed).
      openBase: "https://fhir-open.cerner.com/r4/ec2458f2-1e24-41c8-b71b-0e701af7583d",
      // Where the app can start the login itself. null for a Provider app, which must be
      // launched from code Console. For a Patient app use:
      // "https://fhir-myrecord.cerner.com/r4/ec2458f2-1e24-41c8-b71b-0e701af7583d"
      standaloneIss: null,
      signedInNote: "For a signed-in SMART session, launch from code Console.",
      launchHint: "Provider apps are launched from code Console: your app, Test Sandbox, pick a patient, Launch.",
      ehrScopePrefix: "user", standaloneScopePrefix: "patient",
      extraScopes: ["openid", "fhirUser", "online_access"],
      // Each resource must also be registered as a scope (user/<Resource>.read) with the EHR.
      // Extend with "MedicationRequest", "AllergyIntolerance", "Encounter", "Condition".
      resources: ["Patient", "Observation"],
      conditionCategory: "problem-list-item",
      patients: [
        { id: "12724066", label: "Nancy Patchtest" },
        { id: "12724067", label: "Joe Testpatient" },
        { id: "12724065", label: "Wilm Smart" },
        { id: "12742400", label: "Tim Peters" },
      ],
    },

    epic: {
      name: "Epic",
      issMatch: "epic.com",
      // Epic has no open endpoint. `pixi run smart-app` serves a read-only proxy that signs in with
      // your Backend Systems app (.env + keys/), so the browser needs no login and holds no secret.
      openBase: null,
      proxy: "proxy/epic",
      standaloneIss: null,
      searchNeedsBirthDate: true,           // Epic's Patient search needs name + birthdate
      launchHint: "Epic is reached through `pixi run smart-app`, which signs in with your backend app (EPIC_* in .env and keys/).",
      conditionCategory: "problem-list-item",
      patients: [
        { id: "erXuFYUfucBZaryVksYEcMg3", label: "Camila Lopez" },
        { id: "eq081-VQEgP8drUUqCWzHfw3", label: "Derrick Lin" },
        { id: "e63wRTbPfr1p8UW81d8Seiw3", label: "Theodore Mychart" },
        { id: "eIXesllypH3M9tAA5WdJftQ3", label: "Linda Ross" },
      ],
    },

    hapi: {
      name: "HAPI FHIR",
      issMatch: null,
      // Public HAPI test server. Use ?base=http://localhost:8080/fhir for a local Docker server.
      openBase: "https://hapi.fhir.org/baseR4",
      launchHint: "HAPI has no login.",
      conditionCategory: null,
      patients: [],                         // empty: the page lists the server's first patients
    },
  },
};
