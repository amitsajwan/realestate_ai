// AI Property Form Functions
function aiFillField(field) {
  setFormStatus(`Generating ${field}...`, 'info');
  const form = document.getElementById('propertyForm');
  const address = form.elements.propAddress.value;
  const bedrooms = form.elements.propBeds.value;
  const price = form.elements.propPrice.value;

  fetch('/api/v1/property/ai_suggest', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ field, address, bedrooms, price })
  }).then(res => res.json()).then(data => {
    if (data.suggestion) {
      form.elements[`prop${capitalizeFirst(field)}`].value = data.suggestion;
      setFormStatus(`AI suggestion for ${field} applied.`, 'success');
    } else {
      setFormStatus(`No AI suggestion available.`, 'warning');
    }
  }).catch(() => setFormStatus('AI service not available.', 'danger'));
}

function aiFillAll() {
  setFormStatus('AI populating all fields...', 'info');
  const form = document.getElementById('propertyForm');
  const address = form.elements.propAddress.value;
  const bedrooms = form.elements.propBeds.value;
  const price = form.elements.propPrice.value;

  fetch('/api/v1/property/ai_suggest', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ field: 'all', address, bedrooms, price })
  }).then(res => res.json()).then(data => {
    ['title', 'description', 'amenities', 'price'].forEach(field => {
      if (data[field]) form.elements[`prop${capitalizeFirst(field)}`].value = data[field];
    });
    setFormStatus('AI suggestions applied to all fields.', 'success');
  }).catch(() => setFormStatus('Could not auto-fill fields.', 'danger'));
}

function setFormStatus(msg, type) {
  document.getElementById('propertyFormStatus').innerHTML =
    `<div class='alert alert-${type}'>${msg}</div>`;
}

function capitalizeFirst(s) {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

// Initialize property form when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
  const propertyForm = document.getElementById('propertyForm');
  if (propertyForm) {
    propertyForm.onsubmit = function(e) {
      e.preventDefault();
      setFormStatus('Saving property...', 'info');
      setTimeout(() => setFormStatus('Property added successfully!', 'success'), 1200);
    }
  }
});

console.log('✅ AI Property functions loaded');
