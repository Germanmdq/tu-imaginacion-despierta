import React, { useEffect, useRef, useState } from "react";
import { motion, useScroll, useMotionValueEvent } from "framer-motion";

const FeaturedVideo = ({refForward, ...props }) => {
  const ref = useRef(null);

  const variants = {
    initial: { scale: 1, x: 0, y: 0 },
    animate: { scale: 1.7, x: "60%", y: "100%" },
  };

  const { scrollYProgress } = useScroll({
    target: refForward,
  });

  const [progress, setProgress] = useState(0);
  useMotionValueEvent(scrollYProgress, "change", (value) => {
    setProgress(value);
  });

  return (
    <motion.div
      ref={ref}
      variants={variants}
      initial="initial"
      animate={progress > 0.5 ? "animate" : "initial"}
      transition={{ duration: 1.2, ease: [0.16, 1, 0.3, 1] }}
      className="rounded-3xl w-[40vw] h-[30rem] absolute top-[600px] left-0 flex items-center justify-center overflow-hidden z-30 shadow-2xl bg-black"
      {...props}
    >
      <video
        src="/5e8f8748-a4b6-4082-bd85-391e3c688adf.mp4"
        autoPlay
        loop
        muted
        playsInline
        className="w-full h-full object-cover"
      />
    </motion.div>
  );
};

export default FeaturedVideo;
