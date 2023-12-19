import React from "react";
import ReactDOM from "react-dom/client";
import App from "@/App.tsx";
import "@/main.css";
import { BrowserRouter } from "react-router-dom";
import AuthProvider from "@/contexts/AuthProvider.tsx";
import { Toaster } from "@/components/ui/toaster.tsx";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <App />
        <Toaster />
      </AuthProvider>
    </BrowserRouter>
  </React.StrictMode>,
);
