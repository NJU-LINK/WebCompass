/**
 * Luxury Beauty Products - Product Filter Application
 * Modern ES6+ JavaScript with clean architecture
 */

// Product Data
const products = [
    {
        id: 1,
        name: "Revitalizing Night Serum",
        brand: "Estée Lauder",
        description: "Advanced anti-aging night serum with retinol",
        price: 89,
        category: "Skincare",
        image: "https://images.unsplash.com/photo-1620916566398-39f1143ab7be?w=400&h=400&fit=crop"
    },
    {
        id: 2,
        name: "Luxury Foundation",
        brand: "Chanel",
        description: "Full coverage foundation with SPF 30",
        price: 68,
        category: "Makeup",
        image: "https://images.unsplash.com/photo-1586495777744-4413f21062fa?w=400&h=400&fit=crop"
    },
    {
        id: 3,
        name: "Signature Fragrance",
        brand: "Dior",
        description: "Elegant floral fragrance with lasting power",
        price: 125,
        category: "Fragrance",
        image: "https://images.unsplash.com/photo-1541643600914-78b084683601?w=400&h=400&fit=crop"
    },
    {
        id: 4,
        name: "Hydrating Face Cream",
        brand: "Estée Lauder",
        description: "Rich moisturizing cream for dry skin",
        price: 75,
        category: "Skincare",
        image: "https://images.unsplash.com/photo-1620916566398-39f1143ab7be?w=400&h=400&fit=crop"
    },
    {
        id: 5,
        name: "Premium Lipstick",
        brand: "Tom Ford",
        description: "Long-lasting matte lipstick in bold colors",
        price: 58,
        category: "Makeup",
        image: "https://images.unsplash.com/photo-1586495777744-4413f21062fa?w=400&h=400&fit=crop"
    },
    {
        id: 6,
        name: "Eye Cream",
        brand: "La Mer",
        description: "Anti-aging eye cream with marine extracts",
        price: 195,
        category: "Skincare",
        image: "https://images.unsplash.com/photo-1620916566398-39f1143ab7be?w=400&h=400&fit=crop"
    },
    {
        id: 7,
        name: "Rouge Intense",
        brand: "Chanel",
        description: "Classic red lipstick with satin finish",
        price: 45,
        category: "Makeup",
        image: "https://images.unsplash.com/photo-1586495777744-4413f21062fa?w=400&h=400&fit=crop"
    },
    {
        id: 8,
        name: "Midnight Eau de Parfum",
        brand: "Tom Ford",
        description: "Mysterious and seductive evening fragrance",
        price: 180,
        category: "Fragrance",
        image: "https://images.unsplash.com/photo-1541643600914-78b084683601?w=400&h=400&fit=crop"
    },
    {
        id: 9,
        name: "Vitamin C Serum",
        brand: "Estée Lauder",
        description: "Brightening serum for radiant complexion",
        price: 92,
        category: "Skincare",
        image: "https://images.unsplash.com/photo-1620916566398-39f1143ab7be?w=400&h=400&fit=crop"
    },
    {
        id: 10,
        name: "Cleansing Miracle",
        brand: "La Mer",
        description: "Gentle cleansing foam with sea minerals",
        price: 85,
        category: "Skincare",
        image: "https://images.unsplash.com/photo-1620916566398-39f1143ab7be?w=400&h=400&fit=crop"
    },
    {
        id: 11,
        name: "Classic Perfume",
        brand: "Dior",
        description: "Timeless floral bouquet with warm undertones",
        price: 145,
        category: "Fragrance",
        image: "https://images.unsplash.com/photo-1541643600914-78b084683601?w=400&h=400&fit=crop"
    },
    {
        id: 12,
        name: "Concealer Pro",
        brand: "Tom Ford",
        description: "Full coverage concealer for flawless skin",
        price: 52,
        category: "Makeup",
        image: "https://images.unsplash.com/photo-1586495777744-4413f21062fa?w=400&h=400&fit=crop"
    },
    {
        id: 13,
        name: "Brightening Mask",
        brand: "Estée Lauder",
        description: "Weekly treatment mask for glowing complexion",
        price: 65,
        category: "Skincare",
        image: "https://images.unsplash.com/photo-1620916566398-39f1143ab7be?w=400&h=400&fit=crop"
    },
    {
        id: 14,
        name: "Mascara Volume",
        brand: "Chanel",
        description: "Volumizing mascara for dramatic lashes",
        price: 38,
        category: "Makeup",
        image: "https://images.unsplash.com/photo-1586495777744-4413f21062fa?w=400&h=400&fit=crop"
    },
    {
        id: 15,
        name: "Body Lotion Luxury",
        brand: "La Mer",
        description: "Nourishing body lotion with marine ingredients",
        price: 155,
        category: "Skincare",
        image: "https://images.unsplash.com/photo-1620916566398-39f1143ab7be?w=400&h=400&fit=crop"
    }
];

// State Management
const state = {
    minPrice: 0,
    maxPrice: 300,
    selectedBrands: [],
    activeQuickSelect: null
};

// DOM Elements
const elements = {
    minPriceInput: document.getElementById('minPrice'),
    maxPriceInput: document.getElementById('maxPrice'),
    minPriceLabel: document.getElementById('minPriceLabel'),
    maxPriceLabel: document.getElementById('maxPriceLabel'),
    sliderFill: document.getElementById('sliderFill'),
    productsGrid: document.getElementById('productsGrid'),
    productCount: document.getElementById('productCount'),
    emptyState: document.getElementById('emptyState'),
    resetFilters: document.getElementById('resetFilters'),
    quickSelectBtns: document.querySelectorAll('.quick-select__btn'),
    brandFilters: document.querySelectorAll('.brand-filter__input')
};

// Utility Functions
const debounce = (func, wait) => {
    let timeout;
    return (...args) => {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), wait);
    };
};

const formatPrice = (price) => `$${price}`;

// Slider Functions
const updateSliderFill = () => {
    const min = parseInt(elements.minPriceInput.value);
    const max = parseInt(elements.maxPriceInput.value);
    const totalRange = 300;
    
    const minPercent = (min / totalRange) * 100;
    const maxPercent = (max / totalRange) * 100;
    
    elements.sliderFill.style.left = `${minPercent}%`;
    elements.sliderFill.style.width = `${maxPercent - minPercent}%`;
};

const updatePriceLabels = () => {
    elements.minPriceLabel.textContent = formatPrice(state.minPrice);
    elements.maxPriceLabel.textContent = formatPrice(state.maxPrice);
};

const handleMinPriceChange = (e) => {
    const value = parseInt(e.target.value);
    if (value <= state.maxPrice) {
        state.minPrice = value;
        updateSliderFill();
        updatePriceLabels();
        updateQuickSelectState();
        filterProducts();
    } else {
        e.target.value = state.maxPrice;
    }
};

const handleMaxPriceChange = (e) => {
    const value = parseInt(e.target.value);
    if (value >= state.minPrice) {
        state.maxPrice = value;
        updateSliderFill();
        updatePriceLabels();
        updateQuickSelectState();
        filterProducts();
    } else {
        e.target.value = state.minPrice;
    }
};

// Quick Select Functions
const updateQuickSelectState = () => {
    elements.quickSelectBtns.forEach(btn => {
        const min = parseInt(btn.dataset.min);
        const max = parseInt(btn.dataset.max);
        const isActive = state.minPrice === min && state.maxPrice === max;
        btn.setAttribute('aria-pressed', isActive.toString());
        state.activeQuickSelect = isActive ? btn : null;
    });
};

const handleQuickSelect = (e) => {
    const btn = e.target;
    const min = parseInt(btn.dataset.min);
    const max = parseInt(btn.dataset.max);
    
    state.minPrice = min;
    state.maxPrice = max;
    
    elements.minPriceInput.value = min;
    elements.maxPriceInput.value = max;
    
    updateSliderFill();
    updatePriceLabels();
    updateQuickSelectState();
    filterProducts();
};

// Brand Filter Functions
const handleBrandFilter = (e) => {
    const brand = e.target.value;
    const isChecked = e.target.checked;
    
    if (isChecked) {
        if (!state.selectedBrands.includes(brand)) {
            state.selectedBrands.push(brand);
        }
    } else {
        state.selectedBrands = state.selectedBrands.filter(b => b !== brand);
    }
    
    filterProducts();
};

// Brand Count Functions
const updateBrandCounts = (filteredByPrice) => {
    const brandCounts = {
        'Estée Lauder': 0,
        'Chanel': 0,
        'Dior': 0,
        'Tom Ford': 0,
        'La Mer': 0
    };
    
    filteredByPrice.forEach(product => {
        if (brandCounts.hasOwnProperty(product.brand)) {
            brandCounts[product.brand]++;
        }
    });
    
    document.getElementById('estee-count').textContent = brandCounts['Estée Lauder'];
    document.getElementById('chanel-count').textContent = brandCounts['Chanel'];
    document.getElementById('dior-count').textContent = brandCounts['Dior'];
    document.getElementById('tomford-count').textContent = brandCounts['Tom Ford'];
    document.getElementById('lamer-count').textContent = brandCounts['La Mer'];
};

// Product Filtering
const filterProducts = () => {
    // First filter by price
    const filteredByPrice = products.filter(product => 
        product.price >= state.minPrice && product.price <= state.maxPrice
    );
    
    // Update brand counts based on price-filtered products
    updateBrandCounts(filteredByPrice);
    
    // Then filter by brand (if any brands selected)
    let filteredProducts = filteredByPrice;
    if (state.selectedBrands.length > 0) {
        filteredProducts = filteredByPrice.filter(product => 
            state.selectedBrands.includes(product.brand)
        );
    }
    
    renderProducts(filteredProducts);
};

// Product Rendering
const createProductCard = (product, index) => {
    const card = document.createElement('article');
    card.className = 'product-card';
    card.setAttribute('role', 'listitem');
    card.style.animationDelay = `${index * 50}ms`;
    
    card.innerHTML = `
        <div class="product-card__image-container">
            <img 
                class="product-card__image" 
                src="${product.image}" 
                alt="${product.name} by ${product.brand}"
                loading="lazy"
            />
            <button 
                class="product-card__quick-view" 
                aria-label="Quick view ${product.name}"
            >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M15 3h6v6M9 21H3v-6M21 3l-7 7M3 21l7-7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
            </button>
        </div>
        <div class="product-card__content">
            <span class="product-card__brand">${product.brand}</span>
            <h3 class="product-card__name">${product.name}</h3>
            <p class="product-card__description">${product.description}</p>
            <div class="product-card__footer">
                <span class="product-card__price">${formatPrice(product.price)}</span>
                <span class="product-card__category">${product.category}</span>
            </div>
        </div>
    `;
    
    return card;
};

const renderProducts = (filteredProducts) => {
    const grid = elements.productsGrid;
    const emptyState = elements.emptyState;
    const countElement = elements.productCount;
    
    // Clear existing products
    grid.innerHTML = '';
    
    if (filteredProducts.length === 0) {
        grid.style.display = 'none';
        emptyState.hidden = false;
        countElement.textContent = 'No products found';
    } else {
        grid.style.display = 'grid';
        emptyState.hidden = true;
        
        const productWord = filteredProducts.length === 1 ? 'product' : 'products';
        countElement.textContent = `Showing ${filteredProducts.length} ${productWord}`;
        
        // Use DocumentFragment for better performance
        const fragment = document.createDocumentFragment();
        filteredProducts.forEach((product, index) => {
            fragment.appendChild(createProductCard(product, index));
        });
        grid.appendChild(fragment);
    }
};

// Reset Filters
const resetFilters = () => {
    // Reset state
    state.minPrice = 0;
    state.maxPrice = 300;
    state.selectedBrands = [];
    state.activeQuickSelect = null;
    
    // Reset UI
    elements.minPriceInput.value = 0;
    elements.maxPriceInput.value = 300;
    
    // Reset brand checkboxes
    elements.brandFilters.forEach(checkbox => {
        checkbox.checked = false;
    });
    
    // Reset quick select buttons
    elements.quickSelectBtns.forEach(btn => {
        btn.setAttribute('aria-pressed', 'false');
    });
    
    updateSliderFill();
    updatePriceLabels();
    filterProducts();
};

// Event Listeners
const initEventListeners = () => {
    // Price range sliders
    elements.minPriceInput.addEventListener('input', debounce(handleMinPriceChange, 50));
    elements.maxPriceInput.addEventListener('input', debounce(handleMaxPriceChange, 50));
    
    // Quick select buttons
    elements.quickSelectBtns.forEach(btn => {
        btn.addEventListener('click', handleQuickSelect);
    });
    
    // Brand filters
    elements.brandFilters.forEach(checkbox => {
        checkbox.addEventListener('change', handleBrandFilter);
    });
    
    // Reset filters button
    elements.resetFilters.addEventListener('click', resetFilters);
    
    // Keyboard navigation for quick select
    elements.quickSelectBtns.forEach(btn => {
        btn.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                handleQuickSelect(e);
            }
        });
    });
};

// Initialize Application
const init = () => {
    try {
        updateSliderFill();
        updatePriceLabels();
        initEventListeners();
        filterProducts();
        
        console.log('Luxury Beauty Products app initialized successfully');
    } catch (error) {
        console.error('Error initializing app:', error);
    }
};

// Run on DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}