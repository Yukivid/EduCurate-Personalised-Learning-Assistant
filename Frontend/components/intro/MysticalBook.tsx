"use client";
import { Float } from "@react-three/drei";
import { useRef, useMemo } from "react";
import * as THREE from "three";
import { useFrame } from "@react-three/fiber";

export default function MysticalBook({ progress }: { progress: number }) {
  const group = useRef<THREE.Group>(null);

  useFrame((_, dt) => {
    if (group.current) group.current.rotation.y += dt * 0.6;
  });

  const gold = useMemo(() => new THREE.MeshStandardMaterial({
    color: new THREE.Color("#f6c453"),
    emissive: new THREE.Color("#f6c453"),
    emissiveIntensity: 1.2,
    metalness: 1,
    roughness: 0.3,
  }), []);

  const cover = useMemo(() => new THREE.MeshStandardMaterial({
    color: new THREE.Color("#472a78"),
    metalness: 0.3,
    roughness: 0.8,
  }), []);

  const pages = useMemo(() => new THREE.MeshStandardMaterial({
    color: new THREE.Color("#fff5db"),
    roughness: 1.0,
  }), []);

  return (
    <Float speed={1.5} rotationIntensity={0.7} floatIntensity={0.6}>
      <group ref={group}>
        <mesh position={[0, 0, 0]}>
          <boxGeometry args={[2, 0.5, 1.5]} />
          <primitive object={cover} attach="material" />
        </mesh>
        <mesh position={[0, 0.05, 0]}>
          <boxGeometry args={[1.8, 0.4, 1.3]} />
          <primitive object={pages} attach="material" />
        </mesh>
        <mesh position={[1.05, 0, 0]}>
          <boxGeometry args={[0.1, 0.5, 1.5]} />
          <primitive object={gold} attach="material" />
        </mesh>
        <mesh position={[-1.05, 0, 0]}>
          <boxGeometry args={[0.1, 0.5, 1.5]} />
          <primitive object={gold} attach="material" />
        </mesh>
        <mesh position={[0, 0.3, 0]} rotation={[0, 0, Math.PI / 4]}>
          <boxGeometry args={[0.3, 0.01, 0.3]} />
          <primitive object={gold} attach="material" />
        </mesh>
      </group>
    </Float>
  );
}
