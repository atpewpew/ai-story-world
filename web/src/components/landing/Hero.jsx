import { motion } from 'framer-motion';
import { Play, Sparkles } from 'lucide-react';

export default function Hero() {
  return (
    <section className="hero">
      <motion.div 
        className="hero-content"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <h1>
          <span className="gradient-text">AI Story World</span>
          <br />
          Your Story, Your Adventure
        </h1>
        <p>
          Immerse yourself in AI-powered storytelling where every choice shapes your narrative. 
          Create, explore, and experience infinite adventures with intelligent world-building and character development.
        </p>
        
        <div className="hero-actions">
          <button className="btn-primary" onClick={() => window.location.href = '/login'}>
            <Sparkles size={20} />
            Start Your Adventure
          </button>
          <button className="btn-secondary" onClick={() => document.getElementById('features').scrollIntoView({ behavior: 'smooth' })}>
            <Play size={20} />
            Learn More
          </button>
        </div>
      </motion.div>
    </section>
  );
}
