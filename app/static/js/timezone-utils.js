/**
 * Timezone-aware timestamp formatting utilities
 * Converts server timestamps to user's local timezone
 */

// Global timezone utilities
window.TimezoneUtils = {
  
  /**
   * Format a timestamp to user's local timezone
   * @param {string|Date} timestamp - ISO timestamp string or Date object
   * @param {string} format - Format type: 'full', 'date', 'time', 'relative', 'chat'
   * @returns {string} Formatted timestamp string
   */
  formatTimestamp: function(timestamp, format = 'full') {
    if (!timestamp) return '';
    
    // Handle timestamps that don't have timezone info (assume UTC)
    let timestampStr = timestamp.toString();
    if (!timestampStr.includes('Z') && !timestampStr.includes('+') && !timestampStr.includes('-', 10)) {
      // If no timezone info, assume it's UTC and add 'Z'
      timestampStr = timestampStr + 'Z';
    }
    
    const date = new Date(timestampStr);
    if (isNaN(date.getTime())) return '';
    
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    switch (format) {
      case 'relative':
        if (diffMins < 1) return 'just now';
        if (diffMins < 60) return `${diffMins} minute${diffMins !== 1 ? 's' : ''} ago`;
        if (diffHours < 24) return `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`;
        if (diffDays < 7) return `${diffDays} day${diffDays !== 1 ? 's' : ''} ago`;
        return date.toLocaleDateString();
        
      case 'chat':
        if (diffMins < 1) return 'now';
        if (diffMins < 60) return `${diffMins}m`;
        if (diffHours < 24) return `${diffHours}h`;
        if (diffDays < 7) return `${diffDays}d`;
        return date.toLocaleDateString();
        
      case 'date':
        return date.toLocaleDateString('en-US', {
          year: 'numeric',
          month: 'long',
          day: 'numeric'
        });
        
      case 'time':
        return date.toLocaleTimeString('en-US', {
          hour: 'numeric',
          minute: '2-digit',
          hour12: true
        });
        
      case 'full':
      default:
        return date.toLocaleString('en-US', {
          year: 'numeric',
          month: 'long',
          day: 'numeric',
          hour: 'numeric',
          minute: '2-digit',
          hour12: true
        });
    }
  },
  
  /**
   * Convert all timestamps on the page to user's timezone
   * Looks for elements with data-timestamp attribute
   */
  convertPageTimestamps: function() {
    const timestampElements = document.querySelectorAll('[data-timestamp]');
    
    timestampElements.forEach(element => {
      const timestamp = element.getAttribute('data-timestamp');
      const format = element.getAttribute('data-format') || 'full';
      const converted = this.formatTimestamp(timestamp, format);
      
      if (converted) {
        element.textContent = converted;
        element.classList.add('timezone-converted');
      }
    });
  },
  
  /**
   * Initialize timezone conversion for the page
   */
  init: function() {
    // Convert timestamps on page load
    this.convertPageTimestamps();
    
    // Set up periodic updates for relative timestamps
    setInterval(() => {
      const relativeElements = document.querySelectorAll('[data-format="relative"], [data-format="chat"]');
      relativeElements.forEach(element => {
        const timestamp = element.getAttribute('data-timestamp');
        const format = element.getAttribute('data-format');
        const converted = this.formatTimestamp(timestamp, format);
        
        if (converted && element.textContent !== converted) {
          element.textContent = converted;
        }
      });
    }, 60000); // Update every minute
  }
};

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
  TimezoneUtils.init();
});

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
  module.exports = TimezoneUtils;
}
