// Subscription Plans Page JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Billing Toggle Functionality
    const billingToggle = document.getElementById('billingToggle');
    const toggleButtons = billingToggle.querySelectorAll('.billing-toggle-btn');
    const priceElements = document.querySelectorAll('.price-amount');
    
    // Discount percentages for each billing period
    const discounts = {
        '1_month': 0,
        '3_months': 10,
        '6_months': 15,
        '12_months': 20
    };
    
    // Base prices for each plan
    const basePrices = {
        'seed': 0,
        'harvest': 499,
        'legacy': 999
    };
    
    // Handle billing toggle clicks
    toggleButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Remove active class from all buttons
            toggleButtons.forEach(btn => btn.classList.remove('active'));
            
            // Add active class to clicked button
            this.classList.add('active');
            
            // Get selected billing period
            const period = this.getAttribute('data-period');
            
            // Update prices based on billing period
            updatePrices(period);
        });
    });
    
    // Function to update prices based on billing period
    function updatePrices(period) {
        // Hide all price groups
        document.querySelectorAll('.pricing-card-price-group').forEach(el => {
            el.style.display = 'none';
        });
        
        // Show the selected price group
        document.querySelectorAll('.pricing-' + period).forEach(el => {
            el.style.display = 'block';
        });
    }
    
    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            if (href !== '#') {
                e.preventDefault();
                const target = document.querySelector(href);
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            }
        });
    });
    
    // Handle Checkout Buttons
    const checkoutButtons = document.querySelectorAll('.checkout-btn');
    checkoutButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const planId = this.getAttribute('data-plan-id');
            const activePeriodBtn = document.querySelector('.billing-toggle-btn.active');
            let cycle = '12M';
            if (activePeriodBtn) {
                cycle = activePeriodBtn.getAttribute('data-period');
            }
            
            const card = this.closest('.pricing-card');
            const priceElement = card ? card.querySelector('.price-amount') : null;
            const priceText = priceElement ? priceElement.textContent.replace(/[^0-9]/g, '') : '';
            const price = priceText ? parseInt(priceText) : 0;
            
            if (price === 0) {
                window.location.href = `/subscriptions/checkout/${planId}/`;
            } else {
                window.location.href = `/subscriptions/checkout/paid/${planId}/?billing_cycle=${cycle}`;
            }
        });
    });
    
    // Add animation on scroll for pricing cards
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);
    
    // Observe pricing cards
    const pricingCards = document.querySelectorAll('.pricing-card');
    pricingCards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(30px)';
        card.style.transition = `all 0.5s ease ${index * 0.1}s`;
        observer.observe(card);
    });
    
    // Observe why choose cards
    const whyChooseCards = document.querySelectorAll('.why-choose-card');
    whyChooseCards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(30px)';
        card.style.transition = `all 0.5s ease ${index * 0.1}s`;
        observer.observe(card);
    });
});
