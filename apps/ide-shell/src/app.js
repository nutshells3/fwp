import { ProtocolDriver } from "./driver.js";

const driver = new ProtocolDriver();

function stepResult(transcript, methodName) {
  return transcript.steps.find((step) => step.kind === "response" && step.forMethod === methodName)?.message?.result;
}

function renderFixtureList(fixtures) {
  const list = document.querySelector("#fixture-list");
  list.innerHTML = "";
  for (const fixture of fixtures) {
    const button = document.createElement("button");
    button.textContent = `${fixture.title} (${fixture.backend})`;
    button.addEventListener("click", async () => renderFixture(fixture));
    list.appendChild(button);
  }
}

async function renderFixture(fixture) {
  const transcript = await driver.loadTranscript(fixture.transcript);
  const goals = stepResult(transcript, "query/goals");
  const diagnostics = stepResult(transcript, "query/diagnostics");
  const build = stepResult(transcript, "build/run");
  const probe = stepResult(transcript, "probe/run");
  const audit = stepResult(transcript, "audit/run");

  document.querySelector("#fixture-title").textContent = fixture.title;
  document.querySelector("#backend-name").textContent = fixture.backend;
  document.querySelector("#goals-panel").textContent = JSON.stringify(goals ?? {}, null, 2);
  document.querySelector("#diagnostics-panel").textContent = JSON.stringify(diagnostics ?? {}, null, 2);
  document.querySelector("#build-panel").textContent = JSON.stringify(build ?? {}, null, 2);
  document.querySelector("#probe-panel").textContent = JSON.stringify(probe ?? {}, null, 2);
  document.querySelector("#audit-panel").textContent = JSON.stringify(audit ?? {}, null, 2);
}

async function boot() {
  const fixtures = await driver.loadFixtures();
  renderFixtureList(fixtures.fixtures);
  if (fixtures.fixtures.length > 0) {
    await renderFixture(fixtures.fixtures[0]);
  }
}

boot();
