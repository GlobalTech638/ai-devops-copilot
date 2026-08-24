const modal = document.getElementById('analyzeModal');
const analyzeBtn = document.getElementById('analyzeBtn');
const closeModal = document.getElementById('closeModal');
const startAnalysis = document.getElementById('startAnalysis');
const repoInput = document.getElementById('repoInput');

analyzeBtn.addEventListener('click', () => modal.classList.remove('hidden'));
closeModal.addEventListener('click', () => modal.classList.add('hidden'));
modal.addEventListener('click', (event) => {
  if (event.target === modal) modal.classList.add('hidden');
});

startAnalysis.addEventListener('click', async () => {
  const repository = repoInput.value.trim();
  if (!repository) return;

  startAnalysis.disabled = true;
  startAnalysis.textContent = 'Creating analysis…';

  try {
    const response = await fetch('/api/v1/jobs', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({repository, ref: 'develop'}),
    });
    if (!response.ok) throw new Error('Unable to create analysis job');
    const job = await response.json();
    startAnalysis.textContent = `Analysis queued · ${job.id.slice(0, 8)}`;
    setTimeout(() => modal.classList.add('hidden'), 1100);
  } catch (error) {
    startAnalysis.textContent = 'Try again';
    console.error(error);
  } finally {
    setTimeout(() => {
      startAnalysis.disabled = false;
      startAnalysis.textContent = 'Start analysis ✦';
    }, 1400);
  }
});

document.getElementById('themeBtn').addEventListener('click', () => {
  document.documentElement.classList.toggle('light');
});
