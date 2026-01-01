'use client';
import Image from 'next/image';
import { useState, useEffect } from 'react';

const slides = [
  {
    id: 0,
    templeNameSub: 'Thorur',
    deityName: 'Sri Varasiddhi Vinayaka',
    mantra: 'ఓం గం గణపతయే నమః',
    description: 'Remover of obstacles and bestower of blessings.',
    image: '/deities/varasiddhi.png',
  },
  {
    id: 1,
    templeNameSub: 'Thorur',
    deityName: 'Sri Dakshinamurthy',
    mantra: 'ఓం నమః ప్రణవార్థాయ శుద్ధజ్ఞానైక మూర్తయే',
    description: 'The universal teacher, silent wisdom incarnate.',
    image: '/deities/dakshinamurthy.png',
  },
  {
    id: 2,
    templeNameSub: 'Thorur',
    deityName: 'Sri Maha Vishnu',
    mantra: 'ఓం నమో నారాయణాయ',
    description: 'Preserver of the universe, divine protector.',
    image: '/deities/vishnu.png',
  },
  {
    id: 3,
    templeNameSub: 'Thorur',
    deityName: 'Durga Devi',
    mantra: 'ఓం దుం దుర్గాయై నమః',
    description: 'Mighty mother goddess, destroyer of ego and darkness.',
    image: '/deities/durga.png',
  },
];

export default function DeityCarousel() {
  const [current, setCurrent] = useState(0);
  const [isAutoplay, setIsAutoplay] = useState(true);

  useEffect(() => {
    if (!isAutoplay) return;

    const interval = setInterval(() => {
      setCurrent((prev) => (prev + 1) % slides.length);
    }, 6000);

    return () => clearInterval(interval);
  }, [isAutoplay]);

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'ArrowLeft') goToPrevious();
      if (e.key === 'ArrowRight') goToNext();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  function goToPrevious() {
    setIsAutoplay(false);
    setCurrent((prev) => (prev - 1 + slides.length) % slides.length);
  }

  function goToNext() {
    setIsAutoplay(false);
    setCurrent((prev) => (prev + 1) % slides.length);
  }

  function goToSlide(index: number) {
    setIsAutoplay(false);
    setCurrent(index);
  }

  return (
    <div className="w-full bg-templeWhite">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div
          className="relative w-full bg-templeWhite rounded-lg overflow-hidden shadow-md"
          style={{ height: 'clamp(350px, 60vh, 550px)' }}
          onMouseEnter={() => setIsAutoplay(false)}
          onMouseLeave={() => setIsAutoplay(true)}
          tabIndex={0}
          role="region"
          aria-label="Deity Carousel"
        >
          {/* Slides Container */}
          <div className="relative w-full h-full flex">
            {slides.map((slide, index) => (
              <div
                key={slide.id}
                className={`absolute inset-0 transition-opacity duration-700 ease-out flex flex-col md:flex-row items-center justify-between px-8 sm:px-12 py-8 ${index === current ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'
                  }`}
              >
                {/* Left Section: Text */}
                <div className="flex flex-col justify-center w-full md:w-1/2 pr-0 md:pr-4 text-center md:text-left">
                  <h1 className="text-3xl sm:text-4xl lg:text-5xl font-serif font-bold text-templeDark leading-tight">
                    Sri Varasiddhi
                    <br />
                    Vinayaka Swamy Temple
                  </h1>
                  <p className="text-md text-gray-600 mt-1 uppercase tracking-widest">{slide.templeNameSub}</p>

                  <div className="mt-6 md:mt-8">
                    <h2 className="text-2xl font-serif font-semibold text-templeGold">
                      {slide.deityName}
                    </h2>
                    <p className="text-xl text-red-800 font-serif my-2 italic">
                      {slide.mantra}
                    </p>
                    <p className="text-gray-700 mt-2 text-md lg:text-lg leading-relaxed max-w-md mx-auto md:mx-0">
                      {slide.description}
                    </p>
                  </div>
                </div>

                {/* Right Section: Image */}
                <div className="flex items-center justify-center md:justify-end w-full md:w-1/2 mt-6 md:mt-0">
                  <div className="relative w-40 h-40 sm:w-60 sm:h-60 lg:w-72 lg:h-72">
                    <Image
                      src={slide.image}
                      alt={slide.deityName}
                      fill
                      className="object-contain drop-shadow-xl"
                      priority={index === 0}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Previous Button */}
          <button
            aria-label="Previous slide"
            onClick={goToPrevious}
            className="absolute left-4 top-1/2 -translate-y-1/2 z-10 bg-white/80 hover:bg-templeGold text-templeDark hover:text-white rounded-full p-2 sm:p-3 transition shadow-md"
          >
            <span className="text-2xl leading-none">‹</span>
          </button>

          {/* Next Button */}
          <button
            aria-label="Next slide"
            onClick={goToNext}
            className="absolute right-4 top-1/2 -translate-y-1/2 z-10 bg-white/80 hover:bg-templeGold text-templeDark hover:text-white rounded-full p-2 sm:p-3 transition shadow-md"
          >
            <span className="text-2xl leading-none">›</span>
          </button>

          {/* Dot Indicators */}
          <div className="absolute bottom-6 left-1/2 -translate-x-1/2 z-10 flex gap-3">
            {slides.map((_, index) => (
              <button
                key={index}
                aria-label={`Go to slide ${index + 1}`}
                onClick={() => goToSlide(index)}
                className={`w-2.5 h-2.5 rounded-full transition ${index === current ? 'bg-templeGold scale-125' : 'bg-gray-300'
                  }`}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
