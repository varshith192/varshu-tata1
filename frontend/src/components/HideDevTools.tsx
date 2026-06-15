"use client";
import { useEffect } from "react";

export default function HideDevTools() {
  useEffect(() => {
    const remove = () => {
      document.querySelectorAll("nextjs-portal").forEach(el => el.remove());
    };
    remove();
    const observer = new MutationObserver(remove);
    observer.observe(document.body, { childList: true, subtree: false });
    return () => observer.disconnect();
  }, []);
  return null;
}
