const modal = document.getElementById('analyzeModal');
const analyzeBtn = document.getElementById('analyzeBtn');
const closeModal = document.getElementById('closeModal');
const startAnalysis = document.getElementById('startAnalysis');
const repoInput = document.getElementById('repoInput');
const branchInput = document.getElementById('branchInput');
const modalError = document.getElementById('modalError');

analyzeBtn.addEventListener('click', () => modal.classList.remove('hidden'));
closeModal.addEventListener('click', () => modal.classList.add('hidden'));
modal.addEventListener('click', (event) => { if (event.target === modal) modal.classList.add('hidden'); });

document.getElementById('themeBtn').addEventListener('click', () => document.documentElement.classList.toggle('light'));

function renderFindings(findings) {
  const list = document.getElementById('findingsList');
  if (!findings?.length) {
    list.innerHTML = '<div class="empty-state">No findings returned. That is a good signal.</div>';
    return;
  }
  list.innerHTML = findings.map((finding) => {
    const severity = finding.severity || 'info';
    const confidence = Math.round((finding.confidence ?? 0) * 100);
    return `<div class="finding"><span class="severity-dot ${severity}-dot"></span><div><strong>${escapeHtml(finding.title)}</strong><p>${escapeHtml(finding.evidence || '')}</p><p class="recommendation">Fix: ${escapeHtml(finding.recommendation || '')}</p></div><span class="confidence">${confidence}%</span></div>`;
  }).join('');
}

function escapeHtml(value) {
  return String(value).replace(/[&<>'"]/g, (char) => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[char]));
}

async function pollJob(jobId) {
  for (let attempt = 0; attempt < 60; attempt += 1) {
    const response = await fetch(`/api/v1/jobs/${jobId}`);
    if (!response.ok) throw new Error('Unable to read analysis job');
    const job = await response.json();
    document.getElementById('repoStatus').textContent = `${job.ref} · ${job.status} · ${job.progress}%`;
    if (job.status === 'completed') {
      if (job.result) {
        document.getElementById('healthValue').innerHTML = `${job.result.health_score}<small>/100</small>`;
        document.getElementById('findingCount').textContent = job.result.findings?.length ?? 0;
        renderFindings(job.result.findings);
      }
      return job;
    }
    if (job.status === 'failed') throw new Error(job.error || 'Analysis failed');
    await new Promise((resolve) => setTimeout(resolve, 1500));
  }
  throw new Error('Analysis timed out');
}

startAnalysis.addEventListener('click', async () => {
  const repository = repoInput.value.trim();
  const ref = branchInput.value.trim() || 'main';
  if (!repository) return;
  startAnalysis.disabled = true;
  modalError.textContent = '';
  startAnalysis.textContent = 'Creating analysis…';
  try {
    const response = await fetch('/api/v1/jobs', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({repository, ref})});
    if (!response.ok) throw new Error('Unable to create analysis job');
    const job = await response.json();
    modal.classList.add('hidden');
    document.getElementById('repoName').textContent = repository;
    await pollJob(job.id);
  } catch (error) {
    modal.classList.remove('hidden');
    modalError.textContent = error.message;
  } finally {
    startAnalysis.disabled = false;
    startAnalysis.textContent = 'Start analysis ✦';
  }
});
