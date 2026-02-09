import { useRef, useEffect, Suspense } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { useGLTF, useAnimations } from '@react-three/drei';
import * as THREE from 'three';

interface ModelProps {
  emotion: string;
  isSpeaking: boolean;
}

// Component for GLB model with animations
interface AnimatedGLBModelProps {
  emotion: string;
  isSpeaking: boolean;
}

function GLBModel({ emotion, isSpeaking }: AnimatedGLBModelProps) {
  const group = useRef<THREE.Group>(null);
  const { scene, animations } = useGLTF('/models/wikki.glb');
  const { actions, names } = useAnimations(animations, group);

  useEffect(() => {
    console.log('✅ GLB model loaded successfully!');
    console.log('Available animations:', names);
  }, [names]);

  // Idle animation fallback
  useFrame((state) => {
    if (group.current && names.length === 0) {
      // Subtle breathing if no animations
      const breath = Math.sin(state.clock.elapsedTime * 2) * 0.005;
      group.current.scale.y = 1 + breath;
    }
  });

  // Play animation based on emotion and speaking state
  useEffect(() => {
    if (Object.keys(actions).length === 0) return;

    // Fade out all animations
    Object.values(actions).forEach(action => action?.fadeOut(0.3));

    // Determine which animation to play
    let animationName = 'Idle';
    
    if (isSpeaking) {
      animationName = 'Talk';
    } else {
      // Map emotion to animation
      const emotionMap: Record<string, string> = {
        happy: 'Happy',
        sad: 'Sad',
        surprised: 'Surprised',
        thinking: 'Thinking',
        excited: 'Excited',
        neutral: 'Idle',
      };
      animationName = emotionMap[emotion] || 'Idle';
    }

    // Try to play the animation, fallback to Idle, then to first available
    const action = actions[animationName] || 
                   actions['Idle'] || 
                   actions[names[0]] ||
                   Object.values(actions)[0];
    
    if (action) {
      console.log(`Playing animation: ${animationName}`);
      action.reset().fadeIn(0.3).play();
    }
  }, [emotion, isSpeaking, actions, names]);

  return (
    <group ref={group}>
      <primitive object={scene} scale={2} position={[0, -1, 0]} />
    </group>
  );
}

function FallbackModel({ emotion, isSpeaking }: ModelProps) {
  const groupRef = useRef<THREE.Group>(null);
  const headRef = useRef<THREE.Mesh>(null);
  const bodyRef = useRef<THREE.Mesh>(null);

  useEffect(() => {
    console.log('⚠️ Using fallback geometry (wikki.glb not found)');
  }, []);

  useFrame((state) => {
    if (groupRef.current) {
      // Breathing
      const breath = Math.sin(state.clock.elapsedTime * 2) * 0.01;
      groupRef.current.scale.y = 1 + breath;

      // Subtle swaying
      groupRef.current.rotation.z = Math.sin(state.clock.elapsedTime * 0.5) * 0.02;
    }

    if (headRef.current) {
      // Head movement
      headRef.current.rotation.y = Math.sin(state.clock.elapsedTime * 0.3) * 0.1;
      headRef.current.rotation.x = Math.sin(state.clock.elapsedTime * 0.2) * 0.05;

      // Speaking animation
      if (isSpeaking) {
        headRef.current.position.y = 0.5 + Math.sin(state.clock.elapsedTime * 10) * 0.02;
      } else {
        headRef.current.position.y = 0.5;
      }
    }

    // Emotion-based animations
    if (bodyRef.current) {
      switch (emotion) {
        case 'happy':
          bodyRef.current.rotation.z = Math.sin(state.clock.elapsedTime * 3) * 0.05;
          break;
        case 'excited':
          bodyRef.current.position.y = -0.3 + Math.sin(state.clock.elapsedTime * 5) * 0.05;
          break;
        case 'sad':
          bodyRef.current.rotation.x = -0.1;
          break;
        default:
          bodyRef.current.rotation.x = 0;
          bodyRef.current.position.y = -0.3;
      }
    }
  });

  return (
    <group ref={groupRef}>
      {/* Body */}
      <mesh ref={bodyRef} position={[0, -0.3, 0]}>
        <capsuleGeometry args={[0.3, 0.8, 16, 32]} />
        <meshStandardMaterial color="#ffb6c1" />
      </mesh>

      {/* Head */}
      <mesh ref={headRef} position={[0, 0.5, 0]}>
        <sphereGeometry args={[0.35, 32, 32]} />
        <meshStandardMaterial color="#ffc0cb" />
      </mesh>

      {/* Eyes */}
      <mesh position={[-0.15, 0.55, 0.3]}>
        <sphereGeometry args={[0.05, 16, 16]} />
        <meshStandardMaterial color="#000000" />
      </mesh>
      <mesh position={[0.15, 0.55, 0.3]}>
        <sphereGeometry args={[0.05, 16, 16]} />
        <meshStandardMaterial color="#000000" />
      </mesh>

      {/* Smile */}
      <mesh position={[0, 0.4, 0.32]} rotation={[0, 0, Math.PI]}>
        <torusGeometry args={[0.1, 0.02, 8, 16, Math.PI]} />
        <meshStandardMaterial color="#ff69b4" />
      </mesh>
    </group>
  );
}

interface Avatar3DProps {
  emotion: string;
  isSpeaking: boolean;
}

// Preload the GLB model
useGLTF.preload('/models/wikki.glb');

export function Avatar3D({ emotion, isSpeaking }: Avatar3DProps) {
  return (
    <Canvas
      camera={{ position: [0, 0, 3], fov: 45 }}
      gl={{ alpha: true, antialias: true }}
      style={{ background: 'transparent', width: '100%', height: '100%' }}
    >
      <ambientLight intensity={0.6} />
      <directionalLight position={[5, 5, 5]} intensity={0.8} />
      <pointLight position={[-5, 3, -5]} intensity={0.3} />

      <Suspense fallback={<FallbackModel emotion={emotion} isSpeaking={isSpeaking} />}>
        <GLBModel emotion={emotion} isSpeaking={isSpeaking} />
      </Suspense>
    </Canvas>
  );
}
