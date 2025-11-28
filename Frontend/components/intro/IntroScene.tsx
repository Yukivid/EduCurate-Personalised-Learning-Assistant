"use client";

import { Canvas } from "@react-three/fiber";
import { Suspense, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { GridBackgroundDemo } from "@/components/ui/grid";
import { ContactShadows } from "@react-three/drei";
import BookModel from "./BookModel";
import { TextGenerateEffect } from "@/components/ui/text-generate-effect";

export default function IntroScene({ onStart }: { onStart: () => void }) {
  const [leaving, setLeaving] = useState(false);
  const [hovered, setHovered] = useState(false);

  const handleBookClick = () => {
    setLeaving(true);
    setTimeout(() => onStart(), 10);
  };

  const words = `Touch    the    Book    to    see    the    magic`;

  return (
    <AnimatePresence>
      {!leaving && (
        <motion.div
          className="fixed inset-0 flex flex-col items-center justify-center overflow-hidden"
          initial={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 1.2 }}
        >
          {/* 🟨 Grid background */}
          <div className="absolute inset-0 z-0">
            <GridBackgroundDemo />
          </div>

          {/* 🌟 Vertical Light Beam (Behind Everything) */}
          <div className="absolute inset-0 flex justify-center z-[5]">
            {/* Main glowing beam */}
            <motion.div
              animate={{
                opacity: hovered ? [0.9, 1, 0.9] : [0.7, 0.9, 0.7],
                scaleX: hovered ? 1.1 : 1,
                boxShadow: hovered
                  ? [
                      "0 0 120px 40px rgba(255,191,73,1)",
                      "0 0 160px 60px rgba(255,191,73,0.9)",
                      "0 0 120px 40px rgba(255,191,73,1)",
                    ]
                  : [
                      "0 0 60px 20px rgba(255,191,73,0.5)",
                      "0 0 100px 30px rgba(255,191,73,0.8)",
                      "0 0 60px 20px rgba(255,191,73,0.5)",
                    ],
              }}
              transition={{
                duration: 4,
                repeat: Infinity,
                ease: "easeInOut",
              }}
              className="absolute w-[160px] h-full bg-gradient-to-b from-amber-100 via-amber-400 to-amber-700 blur-[80px] rounded-full"
            />

            {/* ✨ Inner shimmer traveling glow */}
            <motion.div
              animate={{
                y: ["-50%", "100%", "-50%"],
                opacity: [0.2, 0.8, 0.2],
              }}
              transition={{
                duration: 5,
                repeat: Infinity,
                ease: "easeInOut",
              }}
              className="absolute w-[200px] h-[250px] bg-amber-300/60 rounded-full blur-[100px]"
            />
          </div>

          {/* 🪶 Animated text (header area) */}
          <div className="absolute top-[10%] left-1/2 -translate-x-1/2 flex flex-col items-center z-20">
            <TextGenerateEffect
              words={words}
              className="text-center text-neutral-900 dark:text-amber-100 text-4xl md:text-5xl font-black tracking-tight leading-relaxed max-w-6xl drop-shadow-[0_3px_12px_rgba(255,200,150,0.6)]"
            />
          </div>

          {/* 📘 3D Scene (book & shadow) */}
          <div className="absolute inset-0 z-20">
            <Canvas shadows camera={{ position: [0, 1.2, 4.8], fov: 43.5 }}>
              {/* Lights */}
              <ambientLight intensity={0.6} />
              <directionalLight
                position={[2, 6, 2]}
                intensity={1.6}
                castShadow
                shadow-mapSize-width={4096}
                shadow-mapSize-height={4096}
              />

              {/* Soft contact shadow */}
              <ContactShadows
                position={[0, -1.1, 0]}
                opacity={0.6}
                scale={6}
                blur={2.8}
                far={4}
                resolution={1024}
                color="#000000"
              />

              {/* Hoverable + Clickable 3D book */}
              <Suspense fallback={null}>
                <group
                  onClick={handleBookClick}
                  onPointerOver={() => setHovered(true)}
                  onPointerOut={() => setHovered(false)}
                  position={[0, -0.4, 0]}
                  scale={[0.9, 0.9, 0.9]}
                >
                  <BookModel />
                </group>
              </Suspense>
            </Canvas>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
