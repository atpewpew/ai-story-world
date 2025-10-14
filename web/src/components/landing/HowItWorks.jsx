import { motion } from 'framer-motion';
import { Play, MessageSquare, Network } from 'lucide-react';

export default function HowItWorks() {
  const steps = [
    {
      number: 1,
      icon: <Play size={24} />,
      title: "Start Your Adventure",
      description: "Create a new story session or load an existing one. Choose from fantasy, sci-fi, mystery, or create your own world."
    },
    {
      number: 2,
      icon: <MessageSquare size={24} />,
      title: "Interact & Choose",
      description: "Type your actions or click A/B/C options. The AI responds with rich narrative and suggests next steps."
    },
    {
      number: 3,
      icon: <Network size={24} />,
      title: "Watch Your World Grow",
      description: "See characters, items, and locations evolve in real-time through our interactive knowledge graph."
    }
  ];

  return (
    <section className="how-it-works">
      <motion.h2
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        viewport={{ once: true }}
      >
        How It Works
      </motion.h2>
      
      <div className="steps">
        {steps.map((step, index) => (
          <motion.div
            key={index}
            className="step"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: index * 0.2 }}
            viewport={{ once: true }}
          >
            <div className="step-number">
              {step.number}
            </div>
            <div className="step-icon">
              {step.icon}
            </div>
            <h3>{step.title}</h3>
            <p>{step.description}</p>
          </motion.div>
        ))}
      </div>
    </section>
  );
}
