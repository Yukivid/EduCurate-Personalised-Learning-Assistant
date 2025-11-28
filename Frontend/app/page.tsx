"use client";

import React, { useState } from "react";
import IntroScene from "@/components/intro/IntroScene";
import HomePage from "@/components/HomePage";

const Page = () => {
  const [started, setStarted] = useState(false);

  return (
    <div className="relative min-h-screen">
      {!started && <IntroScene onStart={() => setStarted(true)} />}
      {started && <HomePage />}
    </div>
  );
};

export default Page;
