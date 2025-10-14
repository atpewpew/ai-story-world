import { motion } from 'framer-motion';
import { Brain, Network, Database, Zap } from 'lucide-react';

export default function Features() {
  const features = [
    {
      icon: <Brain size={32} />,
      title: "AI-Powered Storytelling",
      description: "Advanced language models create dynamic, engaging narratives that adapt to your choices and actions."
    },
    {
      icon: <Network size={32} />,
      title: "Knowledge Graph Memory",
      description: "The AI remembers characters, items, and locations through an intelligent knowledge graph system."
    },
    {
      icon: <Database size={32} />,
      title: "Persistent World State",
      description: "Your story world evolves and persists across sessions, building rich, interconnected narratives."
    },
    {
      icon: <Zap size={32} />,
      title: "Real-time Interaction",
      description: "Get instant responses with A/B/C choice options and seamless story progression."
    }
  ];

  return (
    <section id="features" className="features">
      <motion.h2
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        viewport={{ once: true }}
      >
        Powerful Features
      </motion.h2>
      
      <div className="features-grid">
        {features.map((feature, index) => (
          <motion.div
            key={index}
            className="feature-card"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: index * 0.1 }}
            viewport={{ once: true }}
          >
            <div className="feature-icon">
              {feature.icon}
            </div>
            <h3>{feature.title}</h3>
            <p>{feature.description}</p>
          </motion.div>
        ))}
      </div>
    </section>
  );
}
