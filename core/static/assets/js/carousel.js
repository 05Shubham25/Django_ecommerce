document.addEventListener("DOMContentLoaded", function() {
  // Make sure elements exist before initializing
  if (!document.querySelector("#cCarousel")) {
    console.log("Carousel elements not found");
    return;
  }
  const prev = document.querySelector("#prev");
  const next = document.querySelector("#next");

  let carouselVp = document.querySelector("#carousel-vp");
  let cCarouselInner = document.querySelector("#cCarousel-inner");
  let carouselInnerWidth = cCarouselInner.getBoundingClientRect().width;
  
  let leftValue = 0;
  let autoSlideInterval;
  let isHovering = false;

  // Variable used to set the carousel movement value (card's width + gap)
  const totalMovementSize =
    parseFloat(
      document.querySelector(".cCarousel-item").getBoundingClientRect().width,
      10
    ) +
    parseFloat(
      window.getComputedStyle(cCarouselInner).getPropertyValue("gap"),
      10
    );
    
  // Function to move to previous slide with infinite loop
  function movePrev() {
    if (!leftValue == 0) {
      leftValue -= -totalMovementSize;
      cCarouselInner.style.left = leftValue + "px";
    } else {
      // We're at the first slide, need to loop to the last slide smoothly
      const itemCount = document.querySelectorAll('.cCarousel-item').length;
      
      // First remove transition
      cCarouselInner.style.transition = 'none';
      
      // Jump to the position before the last item
      leftValue = -(totalMovementSize * (itemCount - 1));
      cCarouselInner.style.left = leftValue + "px";
      
      // Force reflow
      void cCarouselInner.offsetWidth;
      
      // Restore transition
      cCarouselInner.style.transition = '0.2s ease-in-out';
      
      // Then animate to the last item
      leftValue -= -totalMovementSize;
      cCarouselInner.style.left = leftValue + "px";
    }
  }
  
  // Function to move to next slide with infinite loop
  function moveNext() {
    const carouselVpWidth = carouselVp.getBoundingClientRect().width;
    const itemCount = document.querySelectorAll('.cCarousel-item').length;
    
    // Calculate if we're at the last visible item
    const isLastItem = (carouselInnerWidth - Math.abs(leftValue) - totalMovementSize) <= carouselVpWidth;
    
    if (!isLastItem) {
      leftValue -= totalMovementSize;
      cCarouselInner.style.left = leftValue + "px";
    } else {
      // Animate to the last item
      leftValue -= totalMovementSize;
      cCarouselInner.style.left = leftValue + "px";
      
      // After animation completes, instantly jump to the first item
      setTimeout(() => {
        // Remove transition for instant jump
        cCarouselInner.style.transition = 'none';
        leftValue = 0;
        cCarouselInner.style.left = leftValue + "px";
        
        // Force reflow to make the transition removal take effect
        void cCarouselInner.offsetWidth;
        
        // Restore transition
        cCarouselInner.style.transition = '0.2s ease-in-out';
      }, 200); // Match this to your transition time
    }
  }

  // Set up click event listeners
  prev.addEventListener("click", () => {
    movePrev();
    resetAutoSlide();
  });

  next.addEventListener("click", () => {
    moveNext();
    resetAutoSlide();
  });

  // Set up auto-sliding
  function startAutoSlide() {
    autoSlideInterval = setInterval(() => {
      if (!isHovering) {
        moveNext();
      }
    }, 3000); // Slide every 3 seconds
  }
  
  function resetAutoSlide() {
    clearInterval(autoSlideInterval);
    startAutoSlide();
  }
  
  // Pause auto-sliding when hovering over carousel
  document.querySelector("#cCarousel").addEventListener("mouseenter", () => {
    isHovering = true;
  });
  
  document.querySelector("#cCarousel").addEventListener("mouseleave", () => {
    isHovering = false;
  });
  
  // Start auto-sliding
  startAutoSlide();

  // Handle responsive behavior
  const mediaQuery576 = window.matchMedia("(max-width: 576px)");
  const mediaQuery992 = window.matchMedia("(max-width: 992px)");

  mediaQuery576.addEventListener("change", mediaManagement);
  mediaQuery992.addEventListener("change", mediaManagement);

  let oldViewportWidth = window.innerWidth;

  function mediaManagement() {
    const newViewportWidth = window.innerWidth;
    // Recalculate carousel width on screen size change
    carouselInnerWidth = cCarouselInner.getBoundingClientRect().width;
    
    if (leftValue <= -totalMovementSize && oldViewportWidth < newViewportWidth) {
      leftValue += totalMovementSize;
      cCarouselInner.style.left = leftValue + "px";
      oldViewportWidth = newViewportWidth;
    } else if (
      leftValue <= -totalMovementSize &&
      oldViewportWidth > newViewportWidth
    ) {
      leftValue -= totalMovementSize;
      cCarouselInner.style.left = leftValue + "px";
      oldViewportWidth = newViewportWidth;
    }
  }
  
  // Touch swipe support for mobile
  let touchStartX = 0;
  let touchEndX = 0;
  
  carouselVp.addEventListener("touchstart", function(e) {
    touchStartX = e.touches[0].clientX;
    isHovering = true; // Pause auto-sliding during touch
  });
  
  carouselVp.addEventListener("touchend", function(e) {
    touchEndX = e.changedTouches[0].clientX;
    handleSwipe();
    isHovering = false; // Resume auto-sliding after touch
    resetAutoSlide();
  });
  
  function handleSwipe() {
    const swipeThreshold = 50;
    const swipeDistance = touchStartX - touchEndX;
    
    if (Math.abs(swipeDistance) > swipeThreshold) {
      if (swipeDistance > 0) {
        // Swipe left - go to next
        moveNext();
      } else {
        // Swipe right - go to previous
        movePrev();
      }
    }
  }
});
