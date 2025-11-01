/**
 * Validation feedback utility functions
 */

interface ValidationFeedbackOptions {
  duration?: number
  requireScroll?: boolean
  flashEffect?: boolean
}

/**
 * Show validation feedback for a form field error
 */
export const showFieldError = (
  field: string,
  message: string,
  options: ValidationFeedbackOptions = {}
) => {
  const {
    duration = 4000,
    requireScroll = true,
    flashEffect = true
  } = options

  // Add flash effect to error field if enabled
  const fieldElement = document.querySelector(`[name="${field}"]`) as HTMLElement
  if (fieldElement && flashEffect) {
    fieldElement.classList.add('animate-error-flash')
    setTimeout(() => {
      fieldElement.classList.remove('animate-error-flash')
    }, 1000)

    // Add visual feedback for touch devices
    fieldElement.style.boxShadow = '0 0 0 2px #ef4444'
    setTimeout(() => {
      fieldElement.style.boxShadow = ''
    }, duration)
  }

  // Scroll into view on mobile devices if enabled
  if (requireScroll && window.innerWidth < 640 && fieldElement) {
    fieldElement.scrollIntoView({
      behavior: 'smooth',
      block: 'center'
    })
  }

  return {
    duration,
    style: {
      padding: '16px',
      borderRadius: '12px',
      background: '#fee2e2',
      color: '#b91c1c',
      border: '2px solid #ef4444',
      fontSize: window.innerWidth < 640 ? '16px' : '14px'
    }
  }
}