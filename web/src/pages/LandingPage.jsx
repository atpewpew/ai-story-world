import Hero from '../components/landing/Hero';
import Features from '../components/landing/Features';
import HowItWorks from '../components/landing/HowItWorks';

export default function LandingPage() {
  return (
    <div className="landing-page">
      <Hero />
      <Features />
      <HowItWorks />
    </div>
  );
}
