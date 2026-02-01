# Frontend Integration Guide

## Google AI Studio Integration

This guide shows how to integrate the BOOM Wizard Engine with your Google AI Studio frontend.

## Architecture Overview

```
┌─────────────────────┐         ┌──────────────────────┐
│  Google AI Studio   │         │   Wizard Engine      │
│  (Frontend/UI)      │ ◄─────► │   (Backend/API)      │
└─────────────────────┘         └──────────────────────┘
         │                               │
         │                               │
         ▼                               ▼
   Renders UI                      Manages State
   Components                      Flow Control
   (chips, forms,                  Validation
    buttons)                       LLM Calls
```

## Backend Endpoint

**Base URL**: `http://localhost:8000` (or your deployed URL)

All requests require headers:
- `X-Tenant-Id`: Your tenant ID (e.g., "boom")
- `X-Api-Key`: Your API key

## Integration Flow

### 1. Initialize Session

When user starts the wizard:

```javascript
const response = await fetch('http://localhost:8000/v1/sessions/start', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-Tenant-Id': 'boom',
    'X-Api-Key': 'API_KEY_123'
  },
  body: JSON.stringify({
    context: {
      page_url: window.location.href,
      utm_source: 'google_ai_studio'
    },
    consent: {
      gdpr: true,
      profiling: true
    }
  })
});

const { session_id, wizard } = await response.json();
// Store session_id for subsequent requests
```

### 2. Render UI Components

The `wizard.ui` object tells you what to render:

```javascript
function renderUI(ui) {
  switch(ui.type) {
    case 'single_select':
      return renderSingleSelect(ui);
    case 'multi_select':
      return renderMultiSelect(ui);
    case 'short_text':
      return renderShortText(ui);
    case 'long_text':
      return renderLongText(ui);
    case 'confirmation':
      return renderConfirmation(ui);
  }
}

function renderSingleSelect(ui) {
  // Render as chips or radio buttons
  return `
    <div class="wizard-field">
      <label>${ui.label}</label>
      <div class="options">
        ${ui.options.map(opt => `
          <button class="chip" data-value="${opt.id}">
            ${opt.label}
          </button>
        `).join('')}
      </div>
    </div>
  `;
}

function renderMultiSelect(ui) {
  // Render as checkboxes
  const { min, max } = ui.constraints || {};
  return `
    <div class="wizard-field">
      <label>${ui.label}</label>
      <p>Seleziona da ${min} a ${max} opzioni</p>
      <div class="options">
        ${ui.options.map(opt => `
          <label>
            <input type="checkbox" value="${opt.id}">
            ${opt.label}
          </label>
        `).join('')}
      </div>
    </div>
  `;
}
```

### 3. Send User Input

When user selects/types something:

```javascript
async function sendTurn(sessionId, field, value, eventType) {
  const response = await fetch('http://localhost:8000/v1/wizard/turn', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Tenant-Id': 'boom',
      'X-Api-Key': 'API_KEY_123'
    },
    body: JSON.stringify({
      session_id: sessionId,
      event_id: generateEventId(), // UUID for idempotency
      ui_event: {
        type: eventType, // 'selected_option', 'multi_selected', 'text_submitted'
        field: field,
        value: value
      }
    })
  });

  const { assistant_message, wizard } = await response.json();
  
  // Update UI with new wizard state
  updateWizard(wizard);
  showMessage(assistant_message);
}

// Example: User clicks "E-commerce" option
button.addEventListener('click', () => {
  sendTurn(sessionId, 'industry', 'ecommerce', 'selected_option');
});

// Example: User selects multiple channels
const selectedChannels = ['paid_search', 'email', 'seo'];
sendTurn(sessionId, 'channels', selectedChannels, 'multi_selected');

// Example: User types text
textarea.addEventListener('blur', () => {
  sendTurn(sessionId, 'key_problem', textarea.value, 'text_submitted');
});
```

### 4. Display Progress

```javascript
function updateProgress(wizard) {
  const progressBar = document.querySelector('.progress-bar');
  progressBar.style.width = wizard.progress + '%';
  
  // Show current step
  const stepLabel = document.querySelector('.step-label');
  stepLabel.textContent = formatStep(wizard.current_step);
}

function formatStep(step) {
  const labels = {
    context: '1. Contesto',
    objective: '2. Obiettivo',
    target_market: '3. Target',
    value_prop: '4. Value Proposition',
    channels_assets: '5. Canali',
    constraints: '6. Vincoli',
    review: '7. Revisione'
  };
  return labels[step] || step;
}
```

### 5. Show Blueprint Panel

Display the collected data in real-time:

```javascript
function renderBlueprint(blueprint) {
  return `
    <div class="blueprint-panel">
      <h3>Riepilogo</h3>
      
      ${blueprint.context.status === 'confirmed' ? `
        <div class="section confirmed">
          <h4>Contesto ✓</h4>
          <p>Settore: ${blueprint.context.value.industry}</p>
          <p>Business Model: ${blueprint.context.value.business_model}</p>
        </div>
      ` : ''}
      
      ${blueprint.objective.value ? `
        <div class="section">
          <h4>Obiettivo</h4>
          <p>Goal: ${blueprint.objective.value.primary_goal}</p>
        </div>
      ` : ''}
      
      <!-- Repeat for other sections -->
    </div>
  `;
}
```

### 6. Review & Confirm

At the review step:

```javascript
async function confirmWizard(sessionId) {
  const response = await fetch('http://localhost:8000/v1/wizard/confirm', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Tenant-Id': 'boom',
      'X-Api-Key': 'API_KEY_123'
    },
    body: JSON.stringify({
      session_id: sessionId,
      event_id: generateEventId(),
      action: 'confirm', // or 'edit' to go back
      step: 'review'
    })
  });

  const { status, message } = await response.json();
  if (status === 'confirmed') {
    // Proceed to generation
    generateOutput(sessionId);
  }
}
```

### 7. Generate Final Output

```javascript
async function generateOutput(sessionId) {
  showLoading('Generazione in corso...');
  
  const response = await fetch('http://localhost:8000/v1/wizard/generate', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Tenant-Id': 'boom',
      'X-Api-Key': 'API_KEY_123'
    },
    body: JSON.stringify({
      session_id: sessionId,
      event_id: generateEventId(),
      format: 'json'
    })
  });

  const { presentation, report } = await response.json();
  
  hideLoading();
  displayResults(presentation, report);
}

function displayResults(presentation, report) {
  // Render slides
  presentation.slides.forEach(slide => {
    renderSlide(slide.title, slide.bullets);
  });
  
  // Render report
  report.sections.forEach(section => {
    renderSection(section.title, section.content);
  });
}
```

## Complete Example Component

```javascript
class WizardComponent {
  constructor() {
    this.sessionId = null;
    this.currentWizard = null;
  }

  async start() {
    const response = await fetch('http://localhost:8000/v1/sessions/start', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Tenant-Id': 'boom',
        'X-Api-Key': 'API_KEY_123'
      },
      body: JSON.stringify({
        context: { page_url: window.location.href },
        consent: { gdpr: true }
      })
    });

    const { session_id, wizard } = await response.json();
    this.sessionId = session_id;
    this.updateUI(wizard);
  }

  updateUI(wizard) {
    this.currentWizard = wizard;
    
    // Update progress
    document.querySelector('.progress').style.width = wizard.progress + '%';
    
    // Update step indicator
    document.querySelector('.current-step').textContent = wizard.current_step;
    
    // Render UI component
    const container = document.querySelector('.wizard-container');
    container.innerHTML = this.renderUIComponent(wizard.ui);
    
    // Attach event listeners
    this.attachEventListeners(wizard.ui);
    
    // Update blueprint panel
    this.updateBlueprint(wizard.blueprint);
  }

  renderUIComponent(ui) {
    // Implementation based on ui.type
    // ... (see above examples)
  }

  attachEventListeners(ui) {
    const buttons = document.querySelectorAll('.wizard-container button');
    buttons.forEach(btn => {
      btn.addEventListener('click', async () => {
        const value = btn.dataset.value;
        await this.sendTurn(ui.field, value, 'selected_option');
      });
    });
  }

  async sendTurn(field, value, eventType) {
    const response = await fetch('http://localhost:8000/v1/wizard/turn', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Tenant-Id': 'boom',
        'X-Api-Key': 'API_KEY_123'
      },
      body: JSON.stringify({
        session_id: this.sessionId,
        event_id: crypto.randomUUID(),
        ui_event: { type: eventType, field, value }
      })
    });

    const { wizard, assistant_message } = await response.json();
    this.showMessage(assistant_message);
    this.updateUI(wizard);
  }

  updateBlueprint(blueprint) {
    // Render blueprint panel
    // ... (see above example)
  }

  showMessage(message) {
    const msgEl = document.querySelector('.assistant-message');
    msgEl.textContent = message;
    msgEl.classList.add('show');
  }
}

// Initialize
const wizard = new WizardComponent();
wizard.start();
```

## Error Handling

```javascript
async function apiCall(url, options) {
  try {
    const response = await fetch(url, options);
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Request failed');
    }
    
    return await response.json();
  } catch (error) {
    console.error('API Error:', error);
    showError(error.message);
    throw error;
  }
}
```

## Best Practices

1. **Idempotency**: Always use unique `event_id` (UUID) for each turn
2. **Loading States**: Show loading indicators during API calls
3. **Error Handling**: Gracefully handle network errors and validation errors
4. **Session Management**: Store `session_id` in sessionStorage or component state
5. **Real-time Updates**: Update blueprint panel after each turn
6. **Validation**: Show validation errors from `wizard.validation.errors`
7. **Progress Indicator**: Show `wizard.progress` percentage
8. **Assistant Messages**: Display `assistant_message` to guide users

## Styling Tips

```css
.wizard-container {
  max-width: 600px;
  margin: 0 auto;
}

.chip {
  padding: 12px 24px;
  border: 2px solid #e0e0e0;
  border-radius: 24px;
  background: white;
  cursor: pointer;
  transition: all 0.2s;
}

.chip:hover {
  border-color: #2196F3;
  background: #f5f5f5;
}

.chip.selected {
  background: #2196F3;
  color: white;
  border-color: #2196F3;
}

.progress-bar {
  height: 4px;
  background: #2196F3;
  transition: width 0.3s;
}

.blueprint-panel {
  position: fixed;
  right: 0;
  top: 0;
  width: 300px;
  height: 100vh;
  background: #f9f9f9;
  padding: 20px;
  overflow-y: auto;
}

.section.confirmed {
  border-left: 4px solid #4CAF50;
  background: #f1f8f4;
}
```

## Testing

Test your integration with these sample flows:

1. Complete wizard with all required fields
2. Try editing during review
3. Test idempotency (send same event_id twice)
4. Test validation errors (invalid selections)
5. Test session timeout

## Support

For backend issues, check:
- API logs: `docker-compose logs wizard_engine`
- API docs: `http://localhost:8000/docs`
- Health: `http://localhost:8000/health`
