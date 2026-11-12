const $ = (selector) => document.querySelector(selector);
let latestRunId = null;
let configuredProviderMode = "mock";
let latestEvaluationCases = [];
let toolAvailability = {};

async function request(path, options = {}) {
  const token = sessionStorage.getItem("aaos-api-token");
  const response = await fetch(path, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers || {}),
    },
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed (${response.status})`);
  }
  return response;
}

function showNotice(message, isError = false) {
  $("#notice").textContent = message;
  $("#notice").style.color = isError ? "#ff9d9d" : "";
}

async function refreshDashboard() {
  const response = await request("/dashboard/summary");
  const data = await response.json();
  $("#total-runs").textContent = data.total_runs;
  $("#completed-runs").textContent = data.completed_runs;
  $("#failed-runs").textContent = data.failed_runs;
  $("#average-score").textContent = data.average_score == null
    ? "—"
    : `${(data.average_score * 100).toFixed(1)}%`;
  $("#history").innerHTML = data.recent_runs.length
    ? data.recent_runs.map((run) => `
      <div class="run-row">
        <span>Run #${run.id} · version ${run.agent_version_id}</span>
        <strong>${escapeHtml(run.status)}</strong>
        <button class="text-button" type="button" data-run-id="${run.id}">Inspect</button>
      </div>`).join("")
    : '<p class="empty">No runs yet. Start a local evaluation above.</p>';
  $("#history").querySelectorAll("[data-run-id]").forEach((button) => {
    button.addEventListener("click", () => loadRun(Number(button.dataset.runId)));
  });
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[char]);
}

function showEvaluation(result, summary) {
  const row = (label, value) => `<div class="result-line"><span>${label}</span><strong>${value}</strong></div>`;
  $("#result").innerHTML = [
    row("Run", `#${result.test_run_id}`),
    row("Cases evaluated", result.total_cases),
    row("Run status", escapeHtml(result.status)),
    row("Completed / failed cases", `${result.completed_cases} / ${result.failed_cases}`),
    row("Average score", result.average_score == null
      ? "Unavailable"
      : `${(result.average_score * 100).toFixed(1)}%`),
    row("Passed cases (score ≥ 80%)", summary.pass_count ?? "—"),
    row("Provider", "mock"),
  ].join("");
  latestRunId = result.test_run_id;
  $("#report-button").disabled = false;
  $("#adaptive-button").disabled = configuredProviderMode !== "mock"
    || !result.completed_cases;
  $("#deepeval-button").disabled = !toolAvailability.deepeval
    || configuredProviderMode !== "mock" || !result.completed_cases;
  $("#garak-button").disabled = !toolAvailability.garak
    || configuredProviderMode !== "mock" || !result.completed_cases;
}

async function loadRun(runId) {
  try {
    const [summaryResponse, resultsResponse, assuranceResponse, tracesResponse, certificatesResponse, attacksResponse] = await Promise.all([
      request(`/run-summary/${runId}`),
      request(`/evaluation-results?test_run_id=${runId}`),
      request(`/assurance/runs/by-test-run/${runId}`),
      request(`/traces?test_run_id=${runId}`),
      request("/certificates"),
      request(`/attacks?test_run_id=${runId}`),
    ]);
    const summary = await summaryResponse.json();
    const results = await resultsResponse.json();
    const assuranceRuns = await assuranceResponse.json();
    const traces = await tracesResponse.json();
    const certificates = (await certificatesResponse.json())
      .filter((certificate) => certificate.test_run_id === runId);
    const attacks = await attacksResponse.json();
    latestRunId = runId;
    latestEvaluationCases = results
      .filter((item) => item.status === "COMPLETED")
      .map((item) => ({
      input: item.prompt,
      actual_output: item.actual_response,
      expected_output: item.expected_response,
      }));
    $("#result").innerHTML = results.length
      ? results.map((item) => `
        <article class="evidence-card">
          <strong>Case #${escapeHtml(item.evaluation_case_id)} · ${escapeHtml(item.provider)} · ${escapeHtml(item.status)}</strong>
          <p>Prompt: ${escapeHtml(item.prompt)}</p>
          <p>Expected: ${escapeHtml(item.expected_response)}</p>
          ${item.status === "COMPLETED"
            ? `<p>Actual: ${escapeHtml(item.actual_response)}</p>
              <p>Exact: ${escapeHtml(item.exact_match_score)} · Similarity: ${escapeHtml(item.similarity_score)} · Score: ${escapeHtml(item.score)}</p>`
            : `<p>${escapeHtml(item.error_message || "Evaluation failed.")} (${escapeHtml(item.error_type || "Error")})</p>`}
        </article>`).join("")
      : '<p class="empty">No persisted result rows for this run.</p>';
    $("#run-evidence").innerHTML = `
      <h3>Run evidence</h3>
      <p class="hint">Run status: ${escapeHtml(summary.status)} · traces: ${traces.length}</p>
      ${traces.map((trace) => `
        <article class="evidence-card">
          <strong>Trace #${escapeHtml(trace.id)} · ${escapeHtml(trace.provider || "unknown provider")}</strong>
          <p>Latency: ${escapeHtml(trace.latency_ms)} ms · tokens: ${escapeHtml(trace.tokens_used)}</p>
          ${trace.error ? `<p>${escapeHtml(trace.error)}</p>` : ""}
        </article>`).join("")}
      <h3>Built-in mock probes</h3>
      ${attacks.length
        ? attacks.map((attack) => `
          <article class="evidence-card">
            <strong>${escapeHtml(attack.attack_name)} · ${escapeHtml(attack.risk)}</strong>
            <p>${escapeHtml(attack.status)} · ${escapeHtml(attack.reason || "No additional details")}</p>
          </article>`).join("")
        : '<p class="hint">No built-in probes have been run for this test.</p>'}
      <h3>Internal assessment</h3>
      ${certificates.length
        ? certificates.map((certificate) => `
          <article class="evidence-card">
            <strong>${escapeHtml(certificate.assessment_type)} · ${escapeHtml(certificate.status)}</strong>
            <p>Assessment #${escapeHtml(certificate.id)} · run #${escapeHtml(certificate.test_run_id)} · score ${(certificate.score * 100).toFixed(1)}%</p>
            <p>Reference: ${escapeHtml(certificate.certificate_no)}</p>
          </article>`).join("")
        : '<p class="hint">No eligible assessment is stored for this run.</p>'}`;
    if (assuranceRuns.length) {
      const latestAssuranceResponse = await request(
        `/assurance/runs/${assuranceRuns[0].assurance_run_id}`,
      );
      const latestAssurance = await latestAssuranceResponse.json();
      renderAdaptive({
        ...latestAssurance.summary,
        status: latestAssurance.status,
        assurance_run_id: latestAssurance.assurance_run_id,
      });
    } else {
      $("#adaptive-result").innerHTML = '<p class="hint">Select Run EGAA to inspect adaptive evidence for this run.</p>';
      $("#adaptive-history").innerHTML = "";
    }
    $("#report-button").disabled = false;
    $("#adaptive-button").disabled = configuredProviderMode !== "mock"
      || !latestEvaluationCases.length;
    $("#deepeval-button").disabled = !toolAvailability.deepeval
      || configuredProviderMode !== "mock" || !latestEvaluationCases.length;
    $("#garak-button").disabled = !toolAvailability.garak
      || configuredProviderMode !== "mock" || !latestEvaluationCases.length;
    await refreshToolHistory(runId);
    showNotice(`Loaded stored results for run #${runId} (${summary.total_cases} cases).`);
  } catch (error) {
    showNotice(error.message, true);
  }
}

function configureProviderMode(mode) {
  configuredProviderMode = mode;
  const mockMode = mode === "mock";
  $("#run-button").disabled = !mockMode;
  $("#attack-button").disabled = !mockMode;
}

async function loadApplicationState() {
  const auth = await (await request("/auth/status")).json();
  const storedToken = sessionStorage.getItem("aaos-api-token");
  if (auth.token_required && !storedToken) {
    $("#auth-form").hidden = false;
    $("#run-button").disabled = true;
    $("#attack-button").disabled = true;
    $("#connection").textContent = "API token required";
    showNotice("Enter the server-configured token to use protected AAOS APIs.", true);
    return;
  }
  const health = await (await request("/health")).json();
  $("#auth-form").hidden = true;
  $("#connection").textContent = `Backend online · ${health.provider_mode} mode`;
  if (health.provider_mode === "mock") {
    $("#connection").classList.add("safe");
  } else {
    showNotice(
      "Live provider mode is configured. The local demo is disabled to prevent unexpected external calls or charges.",
      true,
    );
  }
  configureProviderMode(health.provider_mode);
  await refreshDashboard();
  await refreshAssuranceTools();
}

$("#auth-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const token = new FormData(event.currentTarget).get("token");
  sessionStorage.setItem("aaos-api-token", token);
  try {
    await loadApplicationState();
    showNotice("AAOS API access enabled for this browser tab.");
  } catch (error) {
    sessionStorage.removeItem("aaos-api-token");
    $("#auth-form").hidden = false;
    $("#run-button").disabled = true;
    $("#attack-button").disabled = true;
    showNotice(error.message, true);
  }
});

$("#auth-form input[name='token']").addEventListener("input", () => {
  sessionStorage.removeItem("aaos-api-token");
});

$("#evaluation-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = $("#run-button");
  button.disabled = true;
  showNotice("Running local mock evaluation…");
  try {
    const values = new FormData(event.currentTarget);
    const agent = await (await request("/agents", {
      method: "POST",
      body: JSON.stringify({
        name: values.get("agent"),
        owner: "local-user",
        description: "Created from the AAOS local demo",
      }),
    })).json();
    const version = await (await request(`/agents/${agent.id}/versions`, {
      method: "POST",
      body: JSON.stringify({ version: "1.0", model_name: "mock" }),
    })).json();
    let run;
    if (values.get("use_dataset")) {
      const dataset = await (await request("/datasets", {
        method: "POST",
        body: JSON.stringify({
          name: `${values.get("agent")} demo ${new Date().toISOString()}`,
          description: "Dataset created by the AAOS local demonstration",
        }),
      })).json();
      await request(`/datasets/${dataset.id}/cases`, {
        method: "POST",
        body: JSON.stringify({
          name: "Local demo case",
          prompt: values.get("prompt"),
          expected_response: values.get("expected"),
          category: "DEMO",
        }),
      });
      run = await (await request(
        `/datasets/${dataset.id}/versions/${version.id}/runs`,
        { method: "POST" },
      )).json();
    } else {
      run = await (await request(`/versions/${version.id}/runs`, {
        method: "POST",
        body: JSON.stringify({}),
      })).json();
      await request("/evaluation-cases", {
        method: "POST",
        body: JSON.stringify({
          name: "Local demo case",
          prompt: values.get("prompt"),
          expected_response: values.get("expected"),
          category: "DEMO",
          test_run_id: run.id,
        }),
      });
    }
    latestEvaluationCases = [{
      input: values.get("prompt"),
      actual_output: "Mock response.",
      expected_output: values.get("expected"),
    }];
    const execution = await (await request(`/evaluation-execution/${run.id}`, {
      method: "POST",
    })).json();
    const summary = await (await request(`/run-summary/${run.id}`)).json();
    showEvaluation(execution, summary);
    await loadRun(run.id);
    await refreshDashboard();
    await refreshAssuranceTools();
    showNotice(
      execution.status === "COMPLETED"
        ? "Evaluation completed using the deterministic mock provider."
        : `Evaluation failed for ${execution.failed_cases} case(s); no assessment was issued.`,
      execution.status !== "COMPLETED",
    );
  } catch (error) {
    showNotice(error.message, true);
  } finally {
    button.disabled = false;
  }
});

$("#hallucination-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const button = $("#hallucination-button");
  button.disabled = true;
  showNotice("Evaluating claims using offline reference checks…");
  try {
    const values = new FormData(form);
    const rawContext = String(values.get("reference_context") || "").trim();
    const result = await (await request("/evaluation/hallucination", {
      method: "POST",
      body: JSON.stringify({
        prompt: values.get("prompt"),
        response: values.get("response"),
        reference_context: rawContext || null,
      }),
    })).json();
    const score = result.overall_hallucination_score == null
      ? "Unavailable (claims are unverifiable)"
      : `${result.overall_hallucination_score.toFixed(1)}%`;
    const categoryRows = Object.entries(result.category_scores).map(([name, item]) => `
      <div class="result-line">
        <span>${escapeHtml(name.replaceAll("_", " "))} · ${escapeHtml(item.status)}</span>
        <strong>${item.score == null ? "N/A" : `${item.score.toFixed(1)}%`}</strong>
      </div>`).join("");
    const findings = result.claims.map((item) => `
      <article class="evidence-card">
        <strong>${escapeHtml(item.status)} · ${escapeHtml(item.category)} · ${escapeHtml(item.severity)}</strong>
        <p>${escapeHtml(item.claim)}</p>
        <p>${escapeHtml(item.explanation)}</p>
        <p>Evidence: ${escapeHtml(item.evidence || "None")}</p>
      </article>`).join("");
    $("#hallucination-result").innerHTML = `
      <div class="result-line"><span>Hallucination reliability score</span><strong>${escapeHtml(score)}</strong></div>
      <div class="result-line"><span>Claims / supported / contradicted</span><strong>${result.claim_count} / ${result.supported} / ${result.contradicted}</strong></div>
      <div class="result-line"><span>Unsupported / unverifiable</span><strong>${result.unsupported} / ${result.unverifiable}</strong></div>
      <div class="result-line"><span>Risk severity</span><strong>${escapeHtml(result.risk?.severity || "UNVERIFIABLE")}</strong></div>
      <h3>Category scorecard</h3>${categoryRows}
      <h3>Claim findings</h3>${findings || '<p class="empty">No claims were extracted.</p>'}
      <p class="hint">${escapeHtml(result.scoring.formula)} No paid or external model was used.</p>
      <p class="hint">${result.limitations.map(escapeHtml).join(" ")}</p>`;
    showNotice("Offline hallucination evaluation completed; see category coverage and limitations.");
  } catch (error) {
    showNotice(error.message, true);
  } finally {
    button.disabled = false;
  }
});

$("#attack-button").addEventListener("click", async () => {
  const button = $("#attack-button");
  button.disabled = true;
  showNotice("Running three built-in probes against the local mock provider…");
  try {
    const response = await request(`/attacks/run?test_run_id=${latestRunId}`, {
      method: "POST",
    });
    const results = await response.json();
    await loadRun(latestRunId);
    showNotice(`Finished ${results.length} local probes. Mock results do not prove model security.`);
  } catch (error) {
    showNotice(error.message, true);
  } finally {
    button.disabled = false;
  }
});

$("#report-button").addEventListener("click", async () => {
  if (!latestRunId) return;
  try {
    const response = await request(`/reports/${latestRunId}`, { method: "POST" });
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `aaos_report_${latestRunId}.pdf`;
    link.click();
    URL.revokeObjectURL(url);
    showNotice("PDF report downloaded.");
  } catch (error) {
    showNotice(error.message, true);
  }
});

function renderAdaptive(result) {
  const gaps = Object.entries(result.final_gaps || {});
  const decisions = (result.selection_history || []).map((step) => `
    <article class="evidence-card">
      <strong>${escapeHtml(step.decision.selected_test)}</strong>
      <span class="status-chip">${escapeHtml(step.execution_status)}</span>
      <p>${escapeHtml(step.decision.why)}</p>
      <p>Expected evidence: ${escapeHtml(step.decision.expected_evidence)}</p>
      <p>Gap update: ${escapeHtml(JSON.stringify(step.gaps_before))} → ${escapeHtml(JSON.stringify(step.gaps_after))}</p>
    </article>`).join("");
  const remaining = gaps.filter(([, gap]) => gap.gap_fraction > gap.threshold || gap.failed_evidence);
  $("#adaptive-result").innerHTML = `
    <div class="result-line"><span>Evidence status</span><strong>${escapeHtml(result.status)}</strong></div>
    <div class="result-line"><span>Stop reason</span><strong>${escapeHtml(result.stopped_reason)}</strong></div>
    <div class="result-line"><span>Executed tests / budget</span><strong>${escapeHtml(result.executed_tests)} / ${escapeHtml(result.max_tests)}</strong></div>
    <div class="result-line"><span>Estimated test cost</span><strong>${escapeHtml(result.estimated_cost)}</strong></div>
    <div class="result-line"><span>Unresolved risks</span><strong>${escapeHtml(remaining.map(([id]) => id).join(", ") || "None")}</strong></div>
    <p class="hint">${escapeHtml(result.assurance_claim)}</p>`;
  $("#adaptive-history").innerHTML = decisions || '<p class="empty">No eligible tests were selected.</p>';
}

$("#adaptive-button").addEventListener("click", async () => {
  if (!latestRunId) return;
  const button = $("#adaptive-button");
  button.disabled = true;
  showNotice("Calculating evidence gaps and selecting bounded mock-compatible tests…");
  try {
    const result = await (await request(`/assurance/runs/${latestRunId}`, {
      method: "POST",
      body: JSON.stringify({ max_tests: 4, max_seconds: 45 }),
    })).json();
    renderAdaptive(result);
    showNotice(`Adaptive assurance finished: ${result.status}. Mock evidence is labeled and not a certification.`);
  } catch (error) {
    showNotice(error.message, true);
  } finally {
    button.disabled = configuredProviderMode !== "mock";
  }
});

async function refreshAssuranceTools() {
  const [toolsResponse, providersResponse] = await Promise.all([
    request("/assurance-tools"),
    request("/llm/providers"),
  ]);
  const data = await toolsResponse.json();
  const providers = await providersResponse.json();
  toolAvailability = Object.fromEntries(
    data.tools.map((tool) => [tool.tool, tool.status === "AVAILABLE"]),
  );
  $("#tool-status").innerHTML = data.tools.map((tool) => `
    <div class="result-line">
      <span>${escapeHtml(tool.tool)} · ${escapeHtml(tool.version || "version unavailable")}</span>
      <strong>${escapeHtml(tool.status)}</strong>
    </div>`).join("");
  $("#provider-status").innerHTML = providers.map((provider) => `
    <div class="result-line">
      <span>${escapeHtml(provider.provider)}</span>
      <strong>${provider.available ? "Configured" : "Not configured"} · live health unverified</strong>
    </div>`).join("");
  $("#garak-button").disabled = !toolAvailability.garak || !latestRunId || configuredProviderMode !== "mock";
  $("#deepeval-button").disabled = !toolAvailability.deepeval || !latestRunId || !latestEvaluationCases.length || configuredProviderMode !== "mock";
}

async function runTool(path, payload) {
  const result = await (await request(path, {
    method: "POST",
    body: JSON.stringify(payload),
  })).json();
  await refreshToolHistory(latestRunId);
  showNotice(`${result.tool} execution persisted as ${result.status}.`);
}

async function refreshToolHistory(runId) {
  const response = await request(`/assurance-tools/runs/${runId}`);
  const executions = await response.json();
  $("#tool-results").innerHTML = executions.length
    ? executions.map((result) => `
      <article class="evidence-card">
        <strong>${escapeHtml(result.tool)} · ${escapeHtml(result.status)}</strong>
        <p>Version: ${escapeHtml(result.version || "unavailable")} · ID: ${escapeHtml(result.execution_id)}</p>
        ${result.error ? `<p>${escapeHtml(result.error)}</p>` : ""}
        ${(result.findings || []).map((finding) => `
          <p>Finding: ${escapeHtml(finding.probe || finding.metric || "result")} · ${escapeHtml(finding.outcome || finding.status || "")} ${escapeHtml(finding.details || finding.reason || "")}</p>`).join("")}
        ${(result.metrics || []).map((metric) => `
          <p>Metric: ${escapeHtml(metric.metric || "result")} · ${escapeHtml(metric.status || "")} · score ${escapeHtml(metric.score ?? "N/A")}${metric.error ? ` · ${escapeHtml(metric.error)}` : ""}</p>`).join("")}
      </article>`).join("")
    : '<p class="empty">No assurance-tool executions stored for this run.</p>';
}

$("#garak-button").addEventListener("click", async () => {
  if (!latestRunId) return;
  $("#garak-button").disabled = true;
  try {
    await runTool(`/assurance-tools/garak/${latestRunId}`, {
      model_type: "test",
      model_name: "test.Blank",
      probes: ["promptinject.HijackHateHumansMini"],
      authorization_confirmed: true,
      external_target_confirmed: false,
      timeout_seconds: 90,
    });
  } catch (error) {
    showNotice(error.message, true);
  } finally {
    $("#garak-button").disabled = !toolAvailability.garak;
  }
});

$("#deepeval-button").addEventListener("click", async () => {
  if (!latestRunId) return;
  $("#deepeval-button").disabled = true;
  try {
    await runTool(`/assurance-tools/deepeval/${latestRunId}`, {
      cases: latestEvaluationCases,
      metrics: ["exact_match"],
      threshold: 1,
      confirm_external_judge: false,
    });
  } catch (error) {
    showNotice(error.message, true);
  } finally {
    $("#deepeval-button").disabled = !toolAvailability.deepeval;
  }
});

$("#tools-refresh").addEventListener("click", () => {
  refreshAssuranceTools().catch((error) => showNotice(error.message, true));
});

$("#refresh-button").addEventListener("click", () => refreshDashboard().catch((error) => showNotice(error.message, true)));

loadApplicationState().catch((error) => {
  $("#connection").textContent = "Backend unavailable";
  showNotice(error.message, true);
});
