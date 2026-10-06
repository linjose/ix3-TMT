(function () {
  function getCookie(name) {
    const cookies = document.cookie ? document.cookie.split(';') : [];
    for (const raw of cookies) {
      const cookie = raw.trim();
      if (cookie.startsWith(name + '=')) return decodeURIComponent(cookie.slice(name.length + 1));
    }
    return '';
  }

  async function toggleStar(button) {
    if (button.dataset.loading === '1') return;
    button.dataset.loading = '1';
    try {
      const response = await fetch(button.dataset.starUrl, {
        method: 'POST',
        headers: {'X-CSRFToken': getCookie('csrftoken'), 'X-Requested-With': 'XMLHttpRequest'},
        credentials: 'same-origin'
      });
      if (!response.ok) throw new Error('HTTP ' + response.status);
      const data = await response.json();
      button.classList.toggle('active', !!data.active);
      const count = button.querySelector('[data-star-count]');
      if (count) count.textContent = data.count;
    } catch (err) {
      console.error(err);
      alert('Star 操作失敗，請重新整理後再試。');
    } finally {
      delete button.dataset.loading;
    }
  }

  document.addEventListener('click', function (event) {
    const button = event.target.closest('[data-star-url]');
    if (!button) return;
    event.preventDefault();
    toggleStar(button);
  });

  const fileInput = document.querySelector('input[type="file"][name="original_file"]');
  if (fileInput) {
    fileInput.setAttribute('accept', '.ppt,.pptx,application/vnd.ms-powerpoint,application/vnd.openxmlformats-officedocument.presentationml.presentation');
    const titleInput = document.querySelector('input[name="title"]');
    const dropField = fileInput.closest('.drop-field');
    const showFile = () => {
      if (!fileInput.files || !fileInput.files[0]) return;
      const f = fileInput.files[0];
      if (titleInput && !titleInput.value.trim()) titleInput.value = f.name.replace(/\.(pptx?|PPTX?)$/, '');
      let label = dropField && dropField.querySelector('.selected-file');
      if (dropField && !label) { label = document.createElement('div'); label.className = 'selected-file'; dropField.appendChild(label); }
      if (label) label.textContent = `已選擇：${f.name} · ${(f.size / 1024 / 1024).toFixed(1)} MB`;
    };
    fileInput.addEventListener('change', showFile);
    if (dropField) {
      ['dragenter','dragover'].forEach(type => dropField.addEventListener(type, e => { e.preventDefault(); dropField.classList.add('dragover'); }));
      ['dragleave','drop'].forEach(type => dropField.addEventListener(type, e => { e.preventDefault(); dropField.classList.remove('dragover'); }));
      dropField.addEventListener('drop', e => {
        if (e.dataTransfer.files.length) { fileInput.files = e.dataTransfer.files; showFile(); }
      });
    }
  }

  if (document.querySelector('[data-processing-refresh]')) {
    window.setTimeout(() => window.location.reload(), 10000);
  }
})();
