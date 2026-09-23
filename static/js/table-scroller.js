/**
 * Table Scroller - Horizontal scroll controls for premium tables
 * Automatically detects table overflow and provides navigation controls
 */

(function() {
    'use strict';

    // Configuration
    const SCROLL_AMOUNT = 300;
    const SCROLL_THRESHOLD = 10;

    /**
     * Initialize table scroller for a wrapper element
     */
    function initTableScroller(wrapper) {
        const table = wrapper.querySelector('.premium-table table');
        if (!table) return;

        // Skip creating navigation controls - only enable horizontal scrolling
        // Navigation buttons are hidden per user request

        // Check overflow and update button states
        function updateScrollerState() {
            const hasOverflow = table.scrollWidth > wrapper.clientWidth + SCROLL_THRESHOLD;

            // Dynamically enable horizontal scrolling when overflow exists
            if (hasOverflow) {
                wrapper.style.overflowX = 'auto';
                wrapper.style.overflowY = 'hidden';
            } else {
                wrapper.style.overflowX = 'hidden';
                wrapper.style.overflowY = 'hidden';
            }

            wrapper.classList.toggle('overflow-active', hasOverflow);
        }

        // Initial check
        updateScrollerState();

        // Watch for resize events using ResizeObserver
        const resizeObserver = new ResizeObserver(() => {
            updateScrollerState();
        });
        resizeObserver.observe(wrapper);
        resizeObserver.observe(table);

        // Watch for window resize
        window.addEventListener('resize', updateScrollerState);
    }

    /**
     * Initialize all table scrollers on the page
     */
    function initAllTableScrollers() {
        const wrappers = document.querySelectorAll('.premium-table-wrapper');
        wrappers.forEach(initTableScroller);
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initAllTableScrollers);
    } else {
        initAllTableScrollers();
    }

    // Also initialize after any dynamic content loads
    window.addEventListener('load', initAllTableScrollers);

})();
