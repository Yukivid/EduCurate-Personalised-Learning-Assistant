"use client";

import { useLoader, useFrame } from "@react-three/fiber";
import { TDSLoader } from "three/examples/jsm/loaders/TDSLoader";
import * as THREE from "three";
import { useRef, useEffect, useMemo } from "react";

export default function BookModel() {
  const model = useLoader(TDSLoader, "/models/Book old N051113.3DS");
  const group = useRef<THREE.Group>(null);

  const coverTexture = useMemo(
    () => new THREE.TextureLoader().load("/models/1238619762_old-book-textures6.jpg"),
    []
  );
  const pageTexture = useMemo(
    () => new THREE.TextureLoader().load("/models/paper.jpg"),
    []
  );
  const beltTexture = useMemo(
    () => new THREE.TextureLoader().load("/models/brown.jpg"),
    []
  );

  
  useEffect(() => {
    model.traverse((child: any) => {
      if (child.isMesh) {
        child.castShadow = true;
        child.receiveShadow = true;

        // 🎯 Apply based on mesh name
        const name = child.name?.toLowerCase();

        if (name.includes("3ddd")) {
          // Inner pages
          child.material = new THREE.MeshStandardMaterial({
            map: pageTexture,
            roughness: 0.1,
          });
        } else if (name.includes("object01")) {
          // Outer cover + branding
          child.material = new THREE.MeshStandardMaterial({
            map: coverTexture,
            metalness: 0.9,
            roughness: 0.5,
          });
        } else {
          // fallback (if unnamed)
          child.material = new THREE.MeshStandardMaterial({
            map: beltTexture,
            metalness: 0.5,
            roughness:0.2,
          });
        }
      }
    });
  }, [model, coverTexture, pageTexture]);

  // 🏀 basketball-style spin: rotate around *world* Y axis
  const worldUp = useMemo(() => new THREE.Vector3(0, 1, 0), []);
  const revPerSec = 1 / 4; // one full spin every 4 seconds (tweak to taste)
  const angularSpeed = 2 * Math.PI * revPerSec;

  useFrame((_, delta) => {
    if (!group.current) return;

    // spin around vertical (world Y), regardless of tilt
    group.current.rotateOnWorldAxis(worldUp, angularSpeed * delta);

    // subtle float
    const t = performance.now() * 0.001;
    group.current.position.y = -0.5 + Math.sin(t * 4) * 0.05;
  });

  return (
    <group
      ref={group}
      scale={0.022}                // slightly smaller
      position={[0, -0.5, 0]}      // centered around the button area
      rotation={[0, 0, 0.5]} 
      castShadow      // tiny forward tilt for depth; keep Y=0 so the spin reads clean
    >
      <primitive object={model} />
    </group>
  );
}
