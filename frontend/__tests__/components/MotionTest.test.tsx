import React from 'react';
import { render } from '@testing-library/react';
import { motion, AnimatePresence } from 'framer-motion';

// Test if framer-motion works
const MotionTest = () => {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
    >
      <h1>Motion Test</h1>
      <AnimatePresence>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <p>Animated content</p>
        </motion.div>
      </AnimatePresence>
    </motion.div>
  );
};

describe('Motion Test', () => {
  test('renders with framer-motion', () => {
    const { container } = render(<MotionTest />);
    expect(container.firstChild).toBeInTheDocument();
  });
});